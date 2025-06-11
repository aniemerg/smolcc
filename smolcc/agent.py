import os
from typing import Optional, Any, Dict, List
from dotenv import load_dotenv

from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel, LogLevel, AgentLogger

# Import tool modules to get their instances
from smolcc.tools.bash_tool import bash_tool
from smolcc.tools.edit_tool import file_edit_tool
from smolcc.tools.glob_tool import glob_tool
from smolcc.tools.grep_tool import grep_tool
from smolcc.tools.ls_tool import ls_tool
from smolcc.tools.replace_tool import write_tool
from smolcc.tools.view_tool import view_tool
from smolcc.tools.user_input_tool import user_input_tool

# Import system prompt utilities
from smolcc.system_prompt import get_system_prompt

# Initialize environment variables
load_dotenv()

# Initialize the model
model = LiteLLMModel(
    model_id="claude-3-7-sonnet-20250219",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

import io
from contextlib import redirect_stdout, redirect_stderr
from rich.console import Console

class SilentAgentLogger(AgentLogger):
    """
    A custom logger that silences most AgentLogger output but still allows tool results
    to be displayed. It writes all log events to a file for debugging purposes.
    """
    def __init__(self, level: LogLevel = LogLevel.INFO, log_file: str = "tool_agent_debug.log"):
        # Create a null console that suppresses output
        self.null_console = Console(file=io.StringIO())
        # But maintain a real console for when we want to show things
        self.real_console = Console()
        
        # Initialize with the null console to suppress default output
        super().__init__(level=level, console=self.null_console)
        
        self.log_file = log_file
        # Create/truncate the log file
        with open(self.log_file, "w") as f:
            f.write("SilentAgentLogger initialized\n")
    
    def log(self, *args, level: int = LogLevel.INFO, **kwargs) -> None:
        """Capture all logs to file but only show some to console"""
        if level <= self.level:
            # Always capture to log file
            string_io = io.StringIO()
            temp_console = Console(file=string_io)
            temp_console.print(*args, **kwargs)
            captured_output = string_io.getvalue()
            
            # Write to log file
            with open(self.log_file, "a") as f:
                f.write(captured_output + "\n")
            
            # Check if this is a tool result/observation that should be displayed
            # This is a bit of a hack but works for the common case
            display_to_console = False
            content = str(args[0]) if args else ""
            
            # We want to show actual tool results but not the scaffolding
            if "Observations:" in content and not content.startswith("Observations:"):
                # Use the real console to display only tool results
                self.real_console.print(*args, **kwargs)
    
    def log_error(self, error_message: str) -> None:
        """Always show errors to the console"""
        # Write to log file
        with open(self.log_file, "a") as f:
            f.write(f"ERROR: {error_message}\n")
        # And display to user
        self.real_console.print(error_message, style="bold red")
    
    def log_task(self, content: str, subtitle: str, title: str = None, level: LogLevel = LogLevel.INFO) -> None:
        """Suppress task headers"""
        # Write to log file only
        with open(self.log_file, "a") as f:
            f.write(f"TASK: {content}\nSubtitle: {subtitle}\nTitle: {title}\n")
    
    def log_rule(self, title: str, level: int = LogLevel.INFO) -> None:
        """Suppress step rules/separators"""
        # Write to log file only
        with open(self.log_file, "a") as f:
            f.write(f"RULE: {title}\n")
    
    def log_markdown(self, content: str, title: str = None, level=LogLevel.INFO, style=None) -> None:
        """Suppress markdown output (usually model reasoning)"""
        # Write to log file only
        with open(self.log_file, "a") as f:
            f.write(f"MARKDOWN: {title}\n{content}\n")

class SilentToolAgent(ToolCallingAgent):
    """
    A modified version of ToolCallingAgent that suppresses default agent logger output
    from appearing in the console, while showing our custom logging information.
    """
    def __init__(self, *args, **kwargs):
        # Use our custom silent logger to suppress default agent output
        if 'logger' not in kwargs:
            kwargs['logger'] = SilentAgentLogger(level=LogLevel.INFO)
        
        super().__init__(*args, **kwargs)
        
        # Real console for our custom output
        self.console = Console()
        
        # Create a debug log file
        with open("tool_agent_debug.log", "w") as f:
            f.write("SilentToolAgent debug log initialized\n")
        
        # Print initialization message to screen
        self.console.print("SilentToolAgent debug log initialized")
    
    def execute_tool_call(self, tool_name, tool_arguments):
        """
        Override execute_tool_call to capture and log the tool output.
        """
        # Log message for tool execution
        log_message = f"\n==== EXECUTING TOOL: {tool_name} ====\n"
        log_message += f"Arguments: {tool_arguments}\n"
        
        # Write to log file and display to screen
        with open("tool_agent_debug.log", "a") as f:
            f.write(log_message)
        self.console.print(log_message)
        
        # Execute the tool call with original functionality (don't suppress console)
        result = super().execute_tool_call(tool_name, tool_arguments)
        
        # Log the result to the file and display
        result_log = f"==== TOOL RESULT ====\n"
        result_log += f"Result: {str(result)[:100]}...\n"
        result_log += "==== END TOOL RESULT ====\n"
        
        # Write to log file and display to screen
        with open("tool_agent_debug.log", "a") as f:
            f.write(result_log)
        self.console.print(result_log)
        
        return result
    
    def run(self, user_input, stream=False):
        """
        Override run method to suppress "Observations:" output.
        """
        # Log message for query
        log_message = f"\n==== RUNNING QUERY ====\n"
        log_message += f"User input: {user_input}\n"
        
        # Write to log file and display to screen
        with open("tool_agent_debug.log", "a") as f:
            f.write(log_message)
        self.console.print(log_message)
        
        # Let the original run method execute normally
        result = super().run(user_input, stream)
        
        # Log the result to the file and display to screen
        result_log = f"==== QUERY RESULT ====\n"
        result_log += f"Result: {str(result)[:500]}...\n"
        result_log += "==== END QUERY RESULT ====\n"
        
        with open("tool_agent_debug.log", "a") as f:
            f.write(result_log)
        self.console.print(result_log)
        
        return result

def create_agent(cwd=None):
    """Create a silent tool-calling agent with the system prompt."""
    if cwd is None:
        cwd = os.getcwd()
    
    # Get the dynamic system prompt
    system_prompt = get_system_prompt(cwd)
    
    # Create a new model with the system prompt
    agent_model = LiteLLMModel(
        model_id="claude-3-7-sonnet-20250219",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        system=system_prompt
    )
    
    # Create our silent logger that suppresses default agent output
    silent_logger = SilentAgentLogger(level=LogLevel.INFO)
    
    # Initialize the agent with all tools and our silent logger
    agent = SilentToolAgent(
        tools=[
            bash_tool,
            file_edit_tool,
            glob_tool,
            grep_tool,
            ls_tool,
            write_tool,
            view_tool,
            user_input_tool,
        ],
        model=agent_model,
        logger=silent_logger
    )
    
    return agent

def main():
    """Run the SmolCC agent with a sample query."""
    # Example query - can be changed as needed
    query = "What files are in the current directory?"
    
    # Create the agent with the current working directory
    agent = create_agent()
    
    print(f"\nQuery: {query}\n")
    answer = agent.run(query)
    print(f"\nAnswer: {answer}")

if __name__ == "__main__":
    main()