import sys
import os
import argparse
from smolcc import create_agent

def main():
    """
    Main entry point for SmolCC.
    Handles command line arguments and runs the agent.
    """
    parser = argparse.ArgumentParser(description="SmolCC - A lightweight code assistant with tools")
    parser.add_argument("query", nargs="*", help="Query to send to Claude")
    parser.add_argument("-i", "--interactive", action="store_true", 
                        help="Run in interactive mode (prompt for queries)")
    parser.add_argument("--cwd", help="Set the working directory for the agent")
    
    args = parser.parse_args()
    
    # Set the working directory if provided
    working_dir = args.cwd if args.cwd else os.getcwd()
    
    # Create the agent with the appropriate working directory
    agent = create_agent(working_dir)
    
    # Handle the query based on arguments
    if args.interactive:
        run_interactive_mode(agent)
    elif args.query:
        query = " ".join(args.query)
        result = agent.run(query)
        print(result)
    else:
        parser.print_help()
        sys.exit(1)

def run_interactive_mode(agent):
    """Run SmolCC in interactive mode, prompting for queries."""
    print("SmolCC Interactive Mode")
    print("Enter your queries (type 'exit' or 'quit' to end):")
    
    while True:
        try:
            query = input("\n> ")
            if query.lower() in ("exit", "quit"):
                break
            
            if not query.strip():
                continue
                
            result = agent.run(query)
            print(result)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
