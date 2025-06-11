"""
BashTool for SmolCC - Bash command execution tool with rich output

This tool executes bash commands in a persistent shell session and returns
rich output objects for better display in the terminal.
"""

import os
import re
import subprocess
import shlex
import time
import threading
import signal
from typing import Optional, Dict, Any, Union, Tuple

from smolagents import Tool
from smolcc.tool_output import ToolOutput, CodeOutput, TextOutput

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
    Executes bash commands in a persistent shell session with rich output.
    """
    
    name = "Bash"
    description = "Runs a supplied bash command inside a persistent shell session, with an optional timeout, while applying the required safety practices.\n\nBefore you launch the command, complete these steps:\n\n1. Parent Directory Confirmation:\n - If the command will create new folders or files, first employ the LS tool to ensure the parent directory already exists and is the intended location.\n - Example: prior to executing \"mkdir foo/bar\", call LS to verify that \"foo\" exists and is truly the correct parent directory.\n\n2. Safety Screening:\n - To reduce the risk of prompt-injection attacks, some commands are restricted or banned. If you attempt to run a blocked command, you will receive an error message explaining the limitation—pass that explanation along to the User.\n - Confirm that the command is not one of these prohibited commands: alias, curl, curlie, wget, axel, aria2c, nc, telnet, lynx, w3m, links, httpie, xh, http-prompt, chrome, firefox, safari.\n\n3. Perform the Command:\n - Once proper quoting is verified, execute the command.\n - Capture the command's output.\n\nOperational notes:\n - Supplying the command argument is mandatory.\n - A timeout in milliseconds may be provided (up to 600000 ms / 10 minutes). If omitted, the default timeout is 30 minutes.\n - If the output exceeds 30000 characters, it will be truncated before being returned.\n - VERY IMPORTANT: You MUST avoid search utilities like find and grep; instead, rely on GrepTool, GlobTool, or dispatch_agent. Likewise, avoid using cat, head, tail, and ls for reading—use View and LS.\n - When sending several commands, combine them with ';' or '&&' rather than newlines (newlines are acceptable only inside quoted strings).\n - IMPORTANT: All commands run within the same shell session. Environment variables, virtual environments, the current directory, and other state persist between commands. For instance, any environment variable you set will remain in subsequent commands.\n - Try to keep the working directory unchanged by using absolute paths and avoiding cd, unless the User explicitly instructs otherwise."
    inputs = {
        "command": {"type": "string", "description": "The command to execute"},
        "timeout": {"type": "number", "description": "Optional timeout in milliseconds (max 600000)", "nullable": True}
    }
    output_type = "string"
    
    def __init__(self):
        """Initialize the EnhancedBashTool with a persistent shell process."""
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
    
    def forward(self, command: str, timeout: Optional[int] = None) -> Union[ToolOutput, str]:
        """
        Execute a bash command in a persistent shell session with rich output.
        
        Args:
            command: The bash command to execute
            timeout: Optional timeout in milliseconds (max 600000)
            
        Returns:
            A ToolOutput object for rich display
        """
        # Check if shell process is alive, restart if needed
        if self.shell_process is None or self.shell_process.poll() is not None:
            self._initialize_shell()
        
        # Security check for banned commands
        if self._is_banned_command(command):
            return TextOutput(f"Error: Command contains one or more banned commands: {', '.join(BANNED_COMMANDS)}. Please use alternative tools for these operations.")
        
        # Set timeout
        if timeout is None:
            timeout_ms = DEFAULT_TIMEOUT
        else:
            timeout_ms = min(int(timeout), MAX_TIMEOUT)
        timeout_sec = timeout_ms / 1000
        
        try:
            # Execute command with timeout
            output, is_error = self._execute_command_with_timeout(command, timeout_sec)
            
            # Determine if the output is code based on the command
            if self._is_code_command(command):
                language = self._guess_language_from_command(command)
                return CodeOutput(output, language=language)
            elif is_error:
                return TextOutput(output)
            else:
                return TextOutput(output)
        except Exception as e:
            return TextOutput(f"Error executing command: {str(e)}")
    
    def _execute_command_with_timeout(self, command: str, timeout_sec: float) -> Tuple[str, bool]:
        """
        Execute a command with a timeout in the persistent shell.
        
        Args:
            command: The command to execute
            timeout_sec: Timeout in seconds
            
        Returns:
            Tuple of (command output, is_error)
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
                return f"Command timed out after {timeout_sec} seconds", True
            
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
            return self._format_result_with_stderr(stdout, stderr), True
            
        return stdout, False
    
    def _read_line_nonblocking_with_source(self) -> Tuple[Optional[str], bool]:
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
        try:
            tokens = shlex.split(command)
            
            # Check each token against the banned commands list
            for token in tokens:
                if token in BANNED_COMMANDS:
                    return True
                
                # Also check for commands with paths
                cmd_name = os.path.basename(token)
                if cmd_name in BANNED_COMMANDS:
                    return True
        except Exception:
            # If we can't parse the command, be conservative and allow it
            # (the shell will fail if it's invalid syntax anyway)
            pass
        
        return False
    
    def _is_code_command(self, command: str) -> bool:
        """
        Determine if a command likely produces code output.
        
        Args:
            command: The command to check
            
        Returns:
            True if the command likely produces code output, False otherwise
        """
        # Commands that often produce code-like output
        code_commands = [
            # File listing commands (that show source code)
            "cat", "head", "tail", "less", "more", "type",
            # Programming language commands
            "python", "python3", "node", "npm", "npx", "ruby", "perl", "php", 
            "go", "rust", "cargo", "java", "javac", "scala", "clang", "gcc",
            # Build/Config commands
            "cmake", "make", "bazel", "gradle", "maven", "ant", "pip", 
            # Source control
            "git diff", "git show", "svn diff",
            # File operations on code
            "diff", "patch"
        ]
        
        try:
            # Check if the command starts with any of the code commands
            for code_cmd in code_commands:
                if command.startswith(code_cmd + " ") or command == code_cmd:
                    return True
                
            # Check for shell script syntax that might indicate code
            if re.search(r'\bfor\b.*\bin\b.*\bdo\b', command) or \
               re.search(r'\bwhile\b.*\bdo\b', command) or \
               re.search(r'\bif\b.*\bthen\b', command) or \
               re.search(r'\bcase\b.*\bin\b', command):
                return True
                
        except Exception:
            # If we can't parse the command, assume it's not code
            pass
        
        return False
    
    def _guess_language_from_command(self, command: str) -> str:
        """
        Guess the programming language based on the command.
        
        Args:
            command: The command to analyze
            
        Returns:
            Language name for syntax highlighting
        """
        # Map commands to languages
        command_language_map = {
            "python": "python",
            "python3": "python",
            "node": "javascript",
            "npm": "javascript",
            "npx": "javascript",
            "ruby": "ruby",
            "perl": "perl",
            "php": "php",
            "go": "go",
            "rust": "rust",
            "cargo": "rust",
            "java": "java",
            "javac": "java",
            "scala": "scala",
            "clang": "c",
            "gcc": "c"
        }
        
        # Check command start for language hints
        for cmd, lang in command_language_map.items():
            if command.startswith(cmd + " ") or command == cmd:
                return lang
        
        # Check if it's a git diff or git show command
        if command.startswith("git diff") or command.startswith("git show"):
            return "diff"
        
        # Check for shell script syntax
        if re.search(r'\bfor\b.*\bin\b.*\bdo\b', command) or \
           re.search(r'\bwhile\b.*\bdo\b', command) or \
           re.search(r'\bif\b.*\bthen\b', command) or \
           re.search(r'\bcase\b.*\bin\b', command):
            return "bash"
        
        # Default to bash for most commands
        return "bash"
        
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
enhanced_bash_tool = bash_tool  # Alias for backward compatibility