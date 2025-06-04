"""
PowerShellTool for SmolCC - PowerShell command execution tool

This tool executes PowerShell commands in a persistent PowerShell session.
It supports command execution with optional timeout and provides safety measures.
"""

import os
import re
import subprocess
import time
import threading
import signal
import platform
from typing import Optional, Dict, Any

from smolagents import Tool

# Constants
DEFAULT_TIMEOUT = 1800000  # 30 minutes in milliseconds
MAX_TIMEOUT = 600000  # 10 minutes in milliseconds
MAX_OUTPUT_CHARS = 30000
BANNED_COMMANDS = [
    "Invoke-WebRequest", "wget", "curl", "Invoke-RestMethod", "Start-Process",
    "iwr", "irm", "chrome", "firefox", "msedge", "iexplore"
]


class PowerShellTool(Tool):
    """
    Executes PowerShell commands in a persistent PowerShell session.
    """
    
    name = "PowerShell"
    description = "Runs a supplied PowerShell command inside a persistent PowerShell session, with an optional timeout, while applying the required safety practices.\n\nBefore you launch the command, complete these steps:\n\n1. Parent Directory Confirmation:\n - If the command will create new folders or files, first employ the LS tool to ensure the parent directory already exists and is the intended location.\n - Example: prior to executing \"New-Item -ItemType Directory foo/bar\", call LS to verify that \"foo\" exists and is truly the correct parent directory.\n\n2. Safety Screening:\n - To reduce the risk of prompt-injection attacks, some commands are restricted or banned. If you attempt to run a blocked command, you will receive an error message explaining the limitation—pass that explanation along to the User.\n - Confirm that the command is not one of these prohibited commands: Invoke-WebRequest, wget, curl, Invoke-RestMethod, Start-Process, iwr, irm, chrome, firefox, msedge, iexplore.\n\n3. Perform the Command:\n - Once proper syntax is verified, execute the command.\n - Capture the command's output.\n\nOperational notes:\n - Supplying the command argument is mandatory.\n - A timeout in milliseconds may be provided (up to 600000 ms / 10 minutes). If omitted, the default timeout is 30 minutes.\n - If the output exceeds 30000 characters, it will be truncated before being returned.\n - VERY IMPORTANT: You MUST avoid search utilities like Select-String for file content search; instead, rely on GrepTool, GlobTool, or dispatch_agent. Likewise, avoid using Get-Content, Get-ChildItem for reading—use View and LS.\n - When sending several commands, combine them with ';' rather than newlines (newlines are acceptable only inside quoted strings).\n - IMPORTANT: All commands run within the same PowerShell session. Environment variables, modules, the current directory, and other state persist between commands. For instance, any variable you set will remain in subsequent commands.\n - Try to keep the working directory unchanged by using absolute paths and avoiding Set-Location, unless the User explicitly instructs otherwise."
    inputs = {
        "command": {"type": "string", "description": "The PowerShell command to execute"},
        "timeout": {"type": "number", "description": "Optional timeout in milliseconds (max 600000)", "nullable": True}
    }
    output_type = "string"
    
    def __init__(self):
        """Initialize the PowerShellTool with a persistent PowerShell process."""
        super().__init__()
        self.shell = None
        self.shell_process = None
        self._initialize_shell()
    
    def _initialize_shell(self):
        """Start a persistent PowerShell session."""
        # Create a persistent PowerShell process
        if platform.system() == "Windows":
            powershell_cmd = ["powershell.exe", "-NoProfile", "-NoLogo", "-NonInteractive"]
        else:
            # For cross-platform PowerShell (PowerShell Core)
            powershell_cmd = ["pwsh", "-NoProfile", "-NoLogo", "-NonInteractive"]
        
        try:
            self.shell_process = subprocess.Popen(
                powershell_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
        except FileNotFoundError:
            raise RuntimeError("PowerShell not found. Please ensure PowerShell is installed and available in PATH.")
        
        # Set up a unique marker for command output separation
        self.output_marker = f"__COMMAND_OUTPUT_MARKER_{int(time.time())}_"
    
    def forward(self, command: str, timeout: Optional[int] = None) -> str:
        """
        Execute a PowerShell command in a persistent PowerShell session.
        
        Args:
            command: The PowerShell command to execute
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
        Execute a command with a timeout in the persistent PowerShell session.
        
        Args:
            command: The command to execute
            timeout_sec: Timeout in seconds
            
        Returns:
            The command output or error message
        """
        # Add Write-Host commands to mark the beginning and end of output
        full_command = f"{command}; Write-Host '{self.output_marker}'\n"
        
        # Send the command to the PowerShell process
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
        stdout = stdout.rstrip('\n\r')
        
        # For simple Write-Host commands, we need to handle potential escaping 
        if command.strip().startswith('Write-Host '):
            # Check if we need to escape characters
            stdout = self._format_write_host_output(stdout)
        
        # If there's stderr content, combine them appropriately
        if stderr:
            return self._format_result_with_stderr(stdout, stderr)
            
        return stdout
    
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
        Kill the currently running command in the PowerShell process.
        
        This sends a SIGTERM to the PowerShell process on Unix or terminates on Windows.
        """
        try:
            if platform.system() == "Windows":
                # On Windows, send Ctrl+C signal
                self.shell_process.send_signal(signal.CTRL_C_EVENT)
            else:
                # On Unix-like systems, send SIGTERM
                self.shell_process.terminate()
            time.sleep(0.5)  # Give the shell a moment to process the signal
        except Exception:
            # If sending signal fails, try to restart the shell
            self._initialize_shell()
    
    def _is_banned_command(self, command: str) -> bool:
        """
        Check if a command contains any banned commands.
        
        Args:
            command: The command to check
            
        Returns:
            True if the command contains a banned command, False otherwise
        """
        # PowerShell commands are case-insensitive
        command_lower = command.lower()
        
        # Check each banned command
        for banned_cmd in BANNED_COMMANDS:
            if banned_cmd.lower() in command_lower:
                return True
        
        return False

    def _format_write_host_output(self, output: str) -> str:
        """
        Format the Write-Host command output.
        
        Args:
            output: The raw output string
            
        Returns:
            Formatted output string
        """
        # PowerShell Write-Host doesn't typically need special escaping
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
        """Clean up the PowerShell process when the tool is destroyed."""
        if self.shell_process:
            try:
                self.shell_process.terminate()
                self.shell_process.wait(timeout=1)
            except Exception:
                pass


# Export the tool as an instance that can be directly used
powershell_tool = PowerShellTool()