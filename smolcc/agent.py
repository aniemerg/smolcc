"""
Tool Agent for SmolCC with improved output formatting.

This module provides an agent implementation that uses Rich for
better terminal output, including spinners for long-running operations
and formatted tool outputs.
"""
import os
import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from smolagents import ToolCallingAgent, Tool, LogLevel, AgentLogger
from smolcc.utils import strip_quotes

from smolcc.tool_output import ToolOutput, ToolCallOutput, AssistantOutput, convert_to_tool_output


class RichConsoleLogger(AgentLogger):
    """
    Custom logger that suppresses default AgentLogger output but provides
    a Rich console for enhanced display.
    """
    def __init__(self, level: LogLevel = LogLevel.INFO, log_file: Optional[str] = None):
        # Create the Rich console for output
        self.console = Console()
        super().__init__(level=level)
        
        # Set up file logging if requested
        self.log_file = log_file
        if log_file:
            # Create or truncate the log file
            with open(log_file, "w") as f:
                f.write("RichConsoleLogger initialized\n")
    
    def log(self, *args, level: int = LogLevel.INFO, **kwargs) -> None:
        """
        Override to suppress default AgentLogger output.
        
        We'll handle our own logging through the Rich console elsewhere.
        """
        if self.log_file and level <= self.level:
            with open(self.log_file, "a") as f:
                f.write(f"LOG: {args}\n")
    
    def log_error(self, error_message: str) -> None:
        """Display errors prominently."""
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(f"ERROR: {error_message}\n")
        
        self.console.print(f"[bold red]Error:[/bold red] {error_message}")
    
    def log_task(self, content: str, subtitle: str, title: str = None, level: LogLevel = LogLevel.INFO) -> None:
        """Suppress task headers."""
        if self.log_file and level <= self.level:
            with open(self.log_file, "a") as f:
                f.write(f"TASK: {content}\nSubtitle: {subtitle}\nTitle: {title}\n")
    
    def log_rule(self, title: str, level: int = LogLevel.INFO) -> None:
        """Suppress rule dividers."""
        if self.log_file and level <= self.level:
            with open(self.log_file, "a") as f:
                f.write(f"RULE: {title}\n")
    
    def log_markdown(self, content: str, title: str = None, level=LogLevel.INFO, style=None) -> None:
        """Suppress markdown output."""
        if self.log_file and level <= self.level:
            with open(self.log_file, "a") as f:
                f.write(f"MARKDOWN: {title}\n{content}\n")


class ToolAgent(ToolCallingAgent):
    """
    Tool Agent with improved terminal output.
    
    This agent extends the ToolCallingAgent with better terminal output,
    including spinners for long-running operations and formatted tool outputs.
    """
    def __init__(self, *args, **kwargs):
        # Extract log file if provided
        log_file = kwargs.pop("log_file", None)
        
        # Create our custom logger
        if 'logger' not in kwargs:
            kwargs['logger'] = RichConsoleLogger(level=LogLevel.INFO, log_file=log_file)
        
        # Initialize the parent class
        super().__init__(*args, **kwargs)
        
        # Get the console from the logger
        self.console = self.logger.console
    
    def execute_tool_call(self, tool_name: str, tool_arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool call with visual feedback.
        
        Args:
            tool_name: Name of the tool to execute
            tool_arguments: Arguments to pass to the tool
            
        Returns:
            The result of the tool execution
        """
        # Display the tool call
        tool_call_output = ToolCallOutput(tool_name, tool_arguments)
        tool_call_output.display(self.console)
        
        # Get the tool instance
        try:
            tool = self.get_tool(tool_name)
        except ValueError as e:
            self.logger.log_error(f"Tool not found: {tool_name}")
            return f"Error: {str(e)}"
        
        # Execute the tool without a spinner
        try:
            start_time = time.time()
            result = tool(**tool_arguments)
            execution_time = time.time() - start_time
        except Exception as e:
            self.logger.log_error(f"Error executing tool {tool_name}: {str(e)}")
            return f"Error: {str(e)}"
        
        # Convert the result to a ToolOutput if it's not already
        output = convert_to_tool_output(result)
        
        # Display the output
        output.display(self.console)
        
        # Log the execution time if it was slow
        if execution_time > 1.0:
            self.console.print(f"  ⏱️ {execution_time:.2f}s", style="bright_black")
        
        # Add a blank line after each tool output for better readability
        self.console.print()
        
        # Return the raw result for the agent to use
        return result
    
    def run(self, user_input: str, stream: bool = False) -> str:
        """
        Run the agent with visual feedback.
        
        Args:
            user_input: The user's input query
            stream: Whether to stream the response
            
        Returns:
            The agent's response
        """
        # Show the user's query in a darker gray
        self.console.print(f"> {user_input}", style="dim")
        self.console.print()  # Add blank line after user input
        
        # Run the agent without a spinner - leave LLM spinners to _format_messages_for_llm
        try:
            # Run the agent
            result = super().run(user_input, stream=stream)
        except Exception as e:
            self.logger.log_error(f"Error running agent: {str(e)}")
            return f"Error: {str(e)}"
        
        # Add blank line before final answer
        self.console.print()
        
        # Display the result as an assistant message
        assistant_output = AssistantOutput(result)
        assistant_output.display(self.console)
        
        # Add blank line after the response
        self.console.print()
        
        return result
        
    def format_messages_for_llm(self, prompt: str) -> List[Dict[str, str]]:
        """
        Override to provide visual feedback when preparing messages for the LLM.
        
        Args:
            prompt: The user's prompt
            
        Returns:
            The formatted messages for the LLM
        """
        # Show a thinking spinner during LLM formatting (this is a long operation)
        with Progress(
            SpinnerColumn(),
            TextColumn("[yellow]Thinking...[/yellow]"),
            console=self.console,
            transient=True,
        ) as progress:
            progress.add_task("Thinking...", total=None)
            # Call parent method
            messages = super().format_messages_for_llm(prompt)
            
        return messages
    
    def get_tool(self, tool_name: str) -> Tool:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool to get
            
        Returns:
            The tool instance
            
        Raises:
            ValueError: If the tool is not found
        """
        # In ToolCallingAgent, self.tools is a dictionary with tool names as keys
        if tool_name in self.tools:
            return self.tools[tool_name]
                
        # If we didn't find it, raise an error
        raise ValueError(f"Tool not found: {tool_name}")


def create_agent(cwd: Optional[str] = None, log_file: Optional[str] = "tool_agent.log") -> ToolAgent:
    """
    Create a tool agent with all available tools.
    
    Args:
        cwd: Current working directory (defaults to os.getcwd())
        log_file: Path to log file or None to disable logging
        
    Returns:
        A ToolAgent instance
    """
    from dotenv import load_dotenv
    from smolagents import LiteLLMModel

    # Import tool modules
    from smolcc.tools import (
        BashTool,
        EditTool,
        GlobTool, 
        GrepTool,
        LSTool, 
        ReplaceTool,
        ViewTool,
        UserInputTool
    )
    
    # Import system prompt utilities
    from smolcc.system_prompt import get_system_prompt
    
    # Initialize environment variables
    load_dotenv()
    
    # Use the provided working directory or current one
    if cwd is None:
        cwd = os.getcwd()
    
    # Get the dynamic system prompt
    system_prompt = get_system_prompt(cwd)
    
    # Create a model with the system prompt
    agent_model = LiteLLMModel(
        model_id="claude-3-7-sonnet-20250219",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        system=system_prompt
    )
    
    # Create instances for tools if needed
    from smolagents import Tool
    
    # Create instances for all tools
    tool_instances = [
        BashTool if isinstance(BashTool, Tool) else BashTool(),
        EditTool() if not isinstance(EditTool, Tool) else EditTool,
        GlobTool if isinstance(GlobTool, Tool) else GlobTool(),
        GrepTool if isinstance(GrepTool, Tool) else GrepTool(),
        LSTool if isinstance(LSTool, Tool) else LSTool(),
        ReplaceTool() if not isinstance(ReplaceTool, Tool) else ReplaceTool,
        ViewTool if isinstance(ViewTool, Tool) else ViewTool(),
        UserInputTool
    ]
    
    # Initialize the agent with all tools
    agent = ToolAgent(
        tools=tool_instances,
        model=agent_model,
        log_file=log_file
    )
    
    return agent


def main():
    """
    Run the EnhancedToolAgent with a sample query.
    """
    # Example query
    query = "What files are in the current directory?"
    
    # Create the agent
    agent = create_enhanced_agent()
    
    # Run the query
    agent.run(query)


if __name__ == "__main__":
    main()