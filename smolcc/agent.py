import os
import platform
import importlib.util
from typing import Optional
from dotenv import load_dotenv

from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel

# Import system prompt utilities
from smolcc.system_prompt import get_system_prompt

# Initialize environment variables
load_dotenv()

def import_tool_safely(module_path, tool_name):
    """Safely import a tool from a specific file path."""
    try:
        spec = importlib.util.spec_from_file_location(f"smolcc.tools.{tool_name}", module_path)
        if spec is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, tool_name, None)
    except Exception as e:
        print(f"Warning: Could not import {tool_name} from {module_path}: {e}")
        return None

def get_available_tools():
    """Get all available tools for the current platform."""
    tools = []
    
    # Get the tools directory path
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")
    
    # List of tools to try importing (filename, tool_instance_name)
    tool_configs = [
        ("edit_tool.py", "file_edit_tool"),
        ("glob_tool.py", "glob_tool"),
        ("grep_tool.py", "grep_tool"),
        ("ls_tool.py", "ls_tool"),
        ("replace_tool.py", "write_tool"),
        ("view_tool.py", "view_tool"),
        ("user_input_tool.py", "user_input_tool"),
    ]
    
    # Add platform-specific shell tools
    if platform.system() == 'Windows':
        # On Windows, use PowerShell tool
        tool_configs.append(("powershell_tool.py", "powershell_tool"))
        print("Note: Using PowerShell tool on Windows")
    else:
        # On Unix-like systems, use bash tool
        tool_configs.append(("bash_tool.py", "bash_tool"))
        print("Note: Using Bash tool on Unix-like system")
    
    for filename, tool_name in tool_configs:
        tool_path = os.path.join(tools_dir, filename)
        if os.path.exists(tool_path):
            tool = import_tool_safely(tool_path, tool_name)
            if tool is not None:
                tools.append(tool)
                print(f"✓ Loaded {tool_name}")
            else:
                print(f"✗ Failed to load {tool_name}")
        else:
            print(f"✗ Tool file not found: {tool_path}")
    
    return tools

def create_agent(cwd=None):
    """Create a tool-calling agent with the system prompt."""
    if cwd is None:
        cwd = os.getcwd()
    
    # Get the dynamic system prompt
    system_prompt = get_system_prompt(cwd)
    
    # Create a new model with the system prompt
    agent_model = LiteLLMModel(
        model_id="deepseek/deepseek-chat",  # LiteLLM format for DeepSeek
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        system=system_prompt
    )
    
    # Get available tools for this platform
    tools = get_available_tools()
    
    if not tools:
        raise RuntimeError("No tools available! Check your tool imports.")
    
    print(f"\nLoaded {len(tools)} tools successfully")
    
    agent = ToolCallingAgent(
        tools=tools,
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