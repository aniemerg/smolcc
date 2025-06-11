#!/usr/bin/env python3
"""
SmolCC - A lightweight code assistant with rich terminal UI.

This script provides a command line interface to the SmolCC agent
with improved terminal output using Rich.
"""
import sys
import os
import argparse
from smolcc.agent import create_agent


def main():
    """
    Main entry point for SmolCC.
    Handles command line arguments and runs the agent.
    """
    parser = argparse.ArgumentParser(
        description="SmolCC - A lightweight code assistant with rich terminal UI"
    )
    parser.add_argument(
        "query", nargs="*", help="Query to send to Claude"
    )
    parser.add_argument(
        "-i", "--interactive", action="store_true", 
        help="Run in interactive mode (prompt for queries)"
    )
    parser.add_argument(
        "--cwd", help="Set the working directory for the agent"
    )
    parser.add_argument(
        "--no-log", action="store_true",
        help="Disable logging to file"
    )
    parser.add_argument(
        "--log-file", default="tool_agent.log",
        help="Path to log file (default: tool_agent.log)"
    )
    
    args = parser.parse_args()
    
    # Set the working directory if provided
    working_dir = args.cwd if args.cwd else os.getcwd()
    
    # Configure logging
    log_file = None if args.no_log else args.log_file
    
    # Create the agent
    agent = create_agent(working_dir, log_file)
    
    # Handle the query based on arguments
    if args.interactive:
        run_interactive_mode(agent)
    elif args.query:
        query = " ".join(args.query)
        agent.run(query)
    else:
        parser.print_help()
        sys.exit(1)


def run_interactive_mode(agent):
    """
    Run SmolCC in interactive mode with enhanced UI.
    
    Args:
        agent: The EnhancedToolAgent instance
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    
    console = Console()
    
    # Display welcome header
    welcome_text = Text()
    welcome_text.append("SmolCC Interactive Mode", style="bold cyan")
    welcome_text.append("\nEnter your queries (type 'exit' or 'quit' to end)")
    console.print(Panel(welcome_text, expand=False))
    
    while True:
        try:
            # Use Rich's prompt
            query = console.input("[cyan bold]>[/cyan bold] ")
            
            if query.lower() in ("exit", "quit"):
                console.print("[yellow]Exiting SmolCC...[/yellow]")
                break
            
            if not query.strip():
                continue
            
            # The agent will handle displaying the result
            agent.run(query)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    main()