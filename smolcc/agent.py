import os
from typing import Optional, Any, Dict, List
from dotenv import load_dotenv

from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel, LogLevel

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

class SilentToolAgent(ToolCallingAgent):
    """
    A modified version of ToolCallingAgent that suppresses tool execution output
    from appearing in the console, while maintaining the agent's ability to
    use tool results in its reasoning.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Save the original console
        self._original_console = self.logger.console
        
        # Create a null console for suppressing output
        self._null_console = Console(file=io.StringIO())
        
        # Create a debug log file
        with open("tool_agent_debug.log", "w") as f:
            f.write("SilentToolAgent debug log initialized\n")
    
    def execute_tool_call(self, tool_name, tool_arguments):
        """
        Override execute_tool_call to capture and suppress the tool output.
        """
        # Log that we're executing a tool
        with open("tool_agent_debug.log", "a") as f:
            f.write(f"\n==== EXECUTING TOOL: {tool_name} ====\n")
            f.write(f"Arguments: {tool_arguments}\n")
        
        # Temporarily replace the logger's console with our null console
        self.logger.console = self._null_console
        
        # Capture stdout/stderr during execution
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Execute the tool call
            result = super().execute_tool_call(tool_name, tool_arguments)
        
        # Restore the original console
        self.logger.console = self._original_console
        
        # Log the result (but not to the console)
        with open("tool_agent_debug.log", "a") as f:
            f.write(f"==== TOOL RESULT ====\n")
            f.write(f"Result: {str(result)[:100]}...\n")
            f.write(f"Captured stdout: {stdout_buffer.getvalue()[:100]}...\n")
            f.write(f"Captured stderr: {stderr_buffer.getvalue()[:100]}...\n")
            f.write("==== END TOOL RESULT ====\n")
        
        return result
    
    def run(self, user_input, stream=False):
        """
        Override run method to suppress "Observations:" output.
        """
        # Log the user input
        with open("tool_agent_debug.log", "a") as f:
            f.write(f"\n==== RUNNING QUERY ====\n")
            f.write(f"User input: {user_input}\n")
        
        # Create a stdout capture buffer
        stdout_buffer = io.StringIO()
        
        # Execute with stdout redirected
        with redirect_stdout(stdout_buffer):
            result = super().run(user_input, stream)
            
            # Extract and log the stdout content
            stdout_content = stdout_buffer.getvalue()
            with open("tool_agent_debug.log", "a") as f:
                f.write(f"==== STDOUT CAPTURE ====\n")
                f.write(stdout_content[:500])
                f.write("\n==== END STDOUT CAPTURE ====\n")
            
            # Filter out the "Observations:" lines from stdout
            filtered_lines = []
            for line in stdout_content.splitlines():
                if not line.strip().startswith("Observations:"):
                    filtered_lines.append(line)
            
            # Print the filtered output
            print("\n".join(filtered_lines))
        
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
    
    # Initialize the agent with all tools
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
        model=agent_model
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