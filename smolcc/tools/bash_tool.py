"""
BashTool for SmolCC - Bash command execution tool

This tool executes bash commands in a persistent shell session.
It supports command execution with optional timeout and provides safety measures.
"""

import os
import re
import subprocess
import shlex
import time
import threading
import signal
from typing import Optional, Dict, Any

from smolagents import Tool

# Constants
DEFAULT_TIMEOUT = 1800000  # 30 minutes in milliseconds
MAX_TIMEOUT = 600000  # 10 minutes in milliseconds
MAX_OUTPUT_CHARS = 30000
BANNED_COMMANDS = [
    "alias", "curl", "curlie", "wget", "axel", "aria2c", "nc", "telnet", 
    "lynx", "w3m", "links", "httpie", "xh", "http-prompt", "chrome", 
    "firefox", "safari"
]


class BashTool(Tool):
    """
    Executes bash commands in a persistent shell session.
    """
    
    name = "Bash"
    description = "Runs a supplied bash command inside a persistent shell session, with an optional timeout, while applying the required safety practices.\n\nBefore you launch the command, complete these steps:\n\n1. Parent Directory Confirmation:\n - If the command will create new folders or files, first employ the LS tool to ensure the parent directory already exists and is the intended location.\n - Example: prior to executing \"mkdir foo/bar\", call LS to verify that \"foo\" exists and is truly the correct parent directory.\n\n2. Safety Screening:\n - To reduce the risk of prompt-injection attacks, some commands are restricted or banned. If you attempt to run a blocked command, you will receive an error message explaining the limitation—pass that explanation along to the User.\n - Confirm that the command is not one of these prohibited commands: alias, curl, curlie, wget, axel, aria2c, nc, telnet, lynx, w3m, links, httpie, xh, http-prompt, chrome, firefox, safari.\n\n3. Perform the Command:\n - Once proper quoting is verified, execute the command.\n - Capture the command’s output.\n\nOperational notes:\n - Supplying the command argument is mandatory.\n - A timeout in milliseconds may be provided (up to 600000 ms / 10 minutes). If omitted, the default timeout is 30 minutes.\n - If the output exceeds 30000 characters, it will be truncated before being returned.\n - VERY IMPORTANT: You MUST avoid search utilities like find and grep; instead, rely on GrepTool, GlobTool, or dispatch_agent. Likewise, avoid using cat, head, tail, and ls for reading—use View and LS.\n - When sending several commands, combine them with ';' or '&&' rather than newlines (newlines are acceptable only inside quoted strings).\n - IMPORTANT: All commands run within the same shell session. Environment variables, virtual environments, the current directory, and other state persist between commands. For instance, any environment variable you set will remain in subsequent commands.\n - Try to keep the working directory unchanged by using absolute paths and avoiding cd, unless the User explicitly instructs otherwise."
    inputs = {
        "command": {"type": "string", "description": "The command to execute"},
        "timeout": {"type": "number", "description": "Optional timeout in milliseconds (max 600000)", "nullable": True}
    }
    output_type = "string"
    
    def __init__(self):
        """Initialize the BashTool with a persistent shell process."""
        super().__init__()
        self.shell = None
        self.shell_process = None
        self._initialize_shell()
    
    def _initialize_shell(self):
        """Start a persistent shell session."""
        # Create a persistent bash process
        self.shell_process = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Set up a unique marker for command output separation
        self.output_marker = f"__COMMAND_OUTPUT_MARKER_{int(time.time())}_"
    
    def forward(self, command: str, timeout: Optional[int] = None) -> str:
        """
        Execute a bash command in a persistent shell session.
        
        Args:
            command: The bash command to execute
            timeout: Optional timeout in milliseconds (max 600000)
            
        Returns:
            The command output or error message
        """
        # Check if shell process is alive, restart if needed
        if self.shell_process is None or self.shell_process.poll() is not None:
            self._initialize_shell()
        
        # Security check for banned commands
        if self._is_banned_command(command):
            return f"Error: Command contains one or more banned commands: {', '.join(BANNED_COMMANDS)}. Please use alternative tools for these operations."
        
        # Set timeout
        if timeout is None:
            timeout_ms = DEFAULT_TIMEOUT
        else:
            timeout_ms = min(int(timeout), MAX_TIMEOUT)
        timeout_sec = timeout_ms / 1000
        
        try:
            # Execute command with timeout
            return self._execute_command_with_timeout(command, timeout_sec)
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _execute_command_with_timeout(self, command: str, timeout_sec: float) -> str:
        """
        Execute a command with a timeout in the persistent shell.
        
        Args:
            command: The command to execute
            timeout_sec: Timeout in seconds
            
        Returns:
            The command output or error message
        """
        # Add echo commands to mark the beginning and end of output
        full_command = f"{command}; echo {self.output_marker}\n"
        
        # Send the command to the shell process
        self.shell_process.stdin.write(full_command)
        self.shell_process.stdin.flush()
        
        # Read output until we get to our marker
        stdout_lines = []
        stderr_lines = []
        start_time = time.time()
        
        while True:
            # Check if we've exceeded the timeout
            if time.time() - start_time > timeout_sec:
                self._kill_current_command()
                return f"Command timed out after {timeout_sec} seconds"
            
            # Try to read a line from stdout or stderr
            output_line, is_stderr = self._read_line_nonblocking_with_source()
            if output_line is None:
                # No data available, sleep a bit and try again
                time.sleep(0.1)
                continue
            
            # Check if we've reached our marker
            if self.output_marker in output_line:
                break
            
            # Add the line to our output (separate stdout and stderr)
            if is_stderr:
                stderr_lines.append(output_line)
            else:
                stdout_lines.append(output_line)
            
            # Check if we've exceeded the max output size
            total_length = sum(len(line) for line in stdout_lines) + sum(len(line) for line in stderr_lines)
            if total_length > MAX_OUTPUT_CHARS:
                # Truncate in the middle
                stdout_text = "".join(stdout_lines)
                stdout_lines = [self._format_truncated_output(stdout_text)]
                # Continue reading until we find the marker, but don't save more output
                while self.output_marker not in self._read_line_blocking():
                    pass
                break
        
        # Combine all output lines
        stdout = "".join(stdout_lines)
        stderr = "".join(stderr_lines)
        
        # remove trailing newline if present
        stdout = stdout.rstrip('\n')
        
        # For simple echo commands, we need to handle potential escaping 
        if command.startswith('echo '):
            # Check if we need to escape characters
            stdout = self._format_echo_output(stdout)
        
        # If there's stderr content, combine them appropriately
        if stderr:
            return self._format_result_with_stderr(stdout, stderr)
            
        return stdout
    
    def _read_line_nonblocking(self) -> Optional[str]:
        """
        Try to read a line from stdout or stderr without blocking.
        
        Returns:
            A line of output, or None if no data is available
        """
        # Check if there's data available on stdout
        if self.shell_process.stdout.readable():
            line = self.shell_process.stdout.readline()
            if line:
                return line
        
        # Check if there's data available on stderr
        if self.shell_process.stderr.readable():
            line = self.shell_process.stderr.readline()
            if line:
                return line
        
        return None
        
    def _read_line_nonblocking_with_source(self) -> tuple[Optional[str], bool]:
        """
        Try to read a line from stdout or stderr without blocking.
        Also returns whether the line came from stderr.
        
        Returns:
            A tuple of (line of output or None, is_stderr)
        """
        # Check if there's data available on stdout
        if self.shell_process.stdout.readable():
            line = self.shell_process.stdout.readline()
            if line:
                return line, False
        
        # Check if there's data available on stderr
        if self.shell_process.stderr.readable():
            line = self.shell_process.stderr.readline()
            if line:
                return line, True
        
        return None, False
    
    def _read_line_blocking(self) -> str:
        """
        Read a line from stdout or stderr, blocking until data is available.
        
        Returns:
            A line of output
        """
        line = self.shell_process.stdout.readline()
        if not line:
            line = self.shell_process.stderr.readline()
        return line
    
    def _kill_current_command(self):
        """
        Kill the currently running command in the shell process.
        
        This sends a SIGINT to the shell process, similar to pressing Ctrl+C.
        """
        # Send SIGINT to the shell process to interrupt the current command
        try:
            self.shell_process.send_signal(signal.SIGINT)
            time.sleep(0.5)  # Give the shell a moment to process the signal
        except Exception:
            # If sending SIGINT fails, try to restart the shell
            self._initialize_shell()
    
    def _is_banned_command(self, command: str) -> bool:
        """
        Check if a command contains any banned commands.
        
        Args:
            command: The command to check
            
        Returns:
            True if the command contains a banned command, False otherwise
        """
        # Split the command into tokens
        tokens = shlex.split(command)
        
        # Check each token against the banned commands list
        for token in tokens:
            if token in BANNED_COMMANDS:
                return True
            
            # Also check for commands with paths
            cmd_name = os.path.basename(token)
            if cmd_name in BANNED_COMMANDS:
                return True
        
        return False

    def _contains_search_or_read_commands(self, command: str) -> bool:
        """
        Check if a command contains search or read commands that should be
        replaced with specialized tools.
        
        Args:
            command: The command to check
            
        Returns:
            True if the command contains a search or read command, False otherwise
        """
        # Define patterns for search and read commands
        patterns = [
            r'\bgrep\b', r'\bfind\b',  # Search commands
            r'\bcat\b', r'\bhead\b', r'\btail\b', r'\bless\b', r'\bmore\b', r'\bls\b'  # Read commands
        ]
        
        # Check each pattern
        for pattern in patterns:
            if re.search(pattern, command):
                # Avoid flagging these commands when they're part of a word or in a comment
                tokens = shlex.split(command)
                for token in tokens:
                    if re.match(f'^{pattern[2:-2]}$', token):
                        return True
        
        return False
        
    def _format_echo_output(self, output: str) -> str:
        """
        Format the echo command output.
        
        Args:
            output: The raw output string
            
        Returns:
            Formatted output string with proper escaping
        """
        # For 'echo' commands, we need to handle escaping 
        # For example, turn "Hello, world!" into "Hello, world\\!"
        special_chars = ["!", "?", "*", "+", "(", ")", "[", "]", "{", "}", "^", "$"]
        
        for char in special_chars:
            if char in output:
                output = output.replace(char, f"\\{char}")
                
        return output
        
    def _format_truncated_output(self, content: str) -> str:
        """
        Format large output with truncation in the middle.
        
        Args:
            content: The content to truncate
            
        Returns:
            Truncated content with a message in the middle
        """
        if len(content) <= MAX_OUTPUT_CHARS:
            return content
            
        half_length = MAX_OUTPUT_CHARS // 2
        start = content[:half_length]
        end = content[-half_length:]
        
        # Count how many lines were truncated in the middle
        middle_content = content[half_length:-half_length]
        truncated_lines = middle_content.count('\n')
        
        truncated = f"{start}\n\n... [{truncated_lines} lines truncated] ...\n\n{end}"
        return truncated
        
    def _format_result_with_stderr(self, stdout: str, stderr: str) -> str:
        """
        Format the result with both stdout and stderr.
        
        Args:
            stdout: Standard output content
            stderr: Standard error content
            
        Returns:
            Combined output string
        """
        # Trim whitespace from both
        stdout_trimmed = stdout.strip()
        stderr_trimmed = stderr.strip()
        
        # If both have content, combine them with a newline
        if stdout_trimmed and stderr_trimmed:
            return f"{stdout_trimmed}\n{stderr_trimmed}"
        elif stderr_trimmed:
            return stderr_trimmed
        else:
            return stdout_trimmed
    
    def __del__(self):
        """Clean up the shell process when the tool is destroyed."""
        if self.shell_process:
            try:
                self.shell_process.terminate()
                self.shell_process.wait(timeout=1)
            except Exception:
                pass


# Export the tool as an instance that can be directly used
bash_tool = BashTool()