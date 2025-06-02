import os
from typing import Optional
from dotenv import load_dotenv

from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel

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

def create_agent(cwd=None):
    """Create a tool-calling agent with the system prompt."""
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
    agent = ToolCallingAgent(
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