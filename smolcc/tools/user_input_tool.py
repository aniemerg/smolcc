"""
UserInputTool for SmolCC - Tool to request input from users

This tool allows agents to request information from users during execution,
creating a simple human-in-the-loop mechanism.
"""

from smolagents import Tool

class UserInputTool(Tool):
    """
    Tool to request input from users during agent execution.
    """
    
    name = "UserInput"
    description = "Ask the user a question and get their response. Use this when you need information from the user to proceed."
    inputs = {
        "question": {"type": "string", "description": "The question to ask the user"}
    }
    output_type = "string"
    
    def forward(self, question: str) -> str:
        """
        Ask the user a question and return their response.
        
        Args:
            question: The question to ask the user
            
        Returns:
            The user's response as a string
        """
        user_input = input(f"\n[USER INPUT REQUESTED] {question}\n> ")
        return user_input


# Export the tool as an instance that can be directly used
user_input_tool = UserInputTool()