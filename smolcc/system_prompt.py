import os
import datetime
import platform
import json
import subprocess
from pathlib import Path


def get_directory_structure(start_path, ignore_patterns=None):
    """Generate a nested directory structure as a string."""
    if ignore_patterns is None:
        # Add more patterns to ignore:
        # - Hidden directories (.*)
        # - Virtual environment directories (venv, env, site-packages)
        # - Build and dist directories
        # - Cache directories
        # - Common dependency locations
        ignore_patterns = [
            '.git', '__pycache__', '*.pyc', 
            '.*',  # All hidden directories 
            'venv', 'env', '.venv', '.env',
            'dist', 'build', 'node_modules',
            '*.egg-info', '*.dist-info',
            'site-packages', 'lib', 'include',
            'bin', '.cache', 'tmp', 'temp',
            'typings', 'stubs', 'vendored',
            '.pytest_cache', '.coverage',
            '.vscode', '.idea', '.atom',
            'vendor', 'third_party', 'external',
            'htmlcov', 'coverage', 'benchmark'
        ]
    
    # Get the working directory path
    cwd = Path(start_path).resolve()
    
    # Create formatted string
    structure = f"- {cwd}/\n"
    
    # We'll use a list to store the structure
    dir_structure = []
    max_files = 100  # Limit total number of files to avoid cluttering
    file_count = 0
    
    for root, dirs, files in os.walk(cwd, topdown=True):
        # Skip ignored directories - both exact matches and pattern matches
        dirs[:] = [d for d in dirs if not any(
            d == pattern or 
            (pattern.startswith('*') and d.endswith(pattern[1:])) or
            (pattern == '.*' and d.startswith('.'))
            for pattern in ignore_patterns
        )]
        
        # Skip if we've reached max files
        if file_count >= max_files:
            # Add a note that we've limited output
            if len(dir_structure) > 0 and not dir_structure[-1].endswith("(truncated)"):
                dir_structure.append("  ... (truncated for brevity)")
            break
        
        level = root.replace(str(cwd), '').count(os.sep)
        indent = '  ' * (level + 1)
        rel_path = os.path.relpath(root, start_path)
        
        # Skip if this path contains any ignored pattern components
        if any(pattern in rel_path.split(os.sep) for pattern in ignore_patterns if not pattern.startswith('*')):
            continue
        
        if rel_path != '.':
            path_parts = rel_path.split(os.sep)
            dir_name = path_parts[-1]
            dir_structure.append(f"{indent}- {dir_name}/")
        
        # Limit files per directory to avoid cluttering
        max_files_per_dir = 10
        dir_files = []
        
        sub_indent = '  ' * (level + 2)
        for file in sorted(files):
            # Skip ignored files
            if any(
                file == pattern or 
                (pattern.startswith('*') and file.endswith(pattern[1:])) or
                (pattern == '.*' and file.startswith('.'))
                for pattern in ignore_patterns
            ):
                continue
                
            # Skip lock files and other large generated files
            if file.endswith(('.lock', '.sum', '.mod', '.bin', '.whl')):
                continue
                
            dir_files.append(f"{sub_indent}- {file}")
            file_count += 1
            
            # Stop if we've reached max files
            if file_count >= max_files:
                break
                
        # Add directory files (limited)
        if len(dir_files) > max_files_per_dir:
            dir_structure.extend(dir_files[:max_files_per_dir])
            dir_structure.append(f"{sub_indent}  ... ({len(dir_files) - max_files_per_dir} more files)")
        else:
            dir_structure.extend(dir_files)
    
    # If we reached the max files, add a note
    if file_count >= max_files:
        dir_structure.append("  ... (truncated for brevity)")
    
    return "".join([structure] + [f"{line}\n" for line in dir_structure])


def is_git_repo(path):
    """Check if the given path is a git repository."""
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except Exception:
        return False


def get_system_prompt(cwd=None):
    """Generate the system prompt with dynamic values filled in."""
    if cwd is None:
        cwd = os.getcwd()
    
    # The system message template is now in the same directory as this file
    template_path = os.path.join(os.path.dirname(__file__), 'system_message.txt')
    
    try:
        with open(template_path, 'r') as f:
            system_message = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find system_message.txt at {template_path}")
    
    # Get current date in format M/D/YYYY
    today = datetime.datetime.now().strftime("%-m/%-d/%Y")
    
    # Check if directory is a git repo
    is_repo = is_git_repo(cwd)
    
    # Get directory structure
    dir_structure = get_directory_structure(cwd)
    
    # Replace placeholders in the template with actual values
    system_message = system_message.replace("{working_directory}", cwd)
    system_message = system_message.replace("{is_git_repo}", "Yes" if is_repo else "No")
    system_message = system_message.replace("{platform}", platform.system().lower())
    system_message = system_message.replace("{date}", today)
    system_message = system_message.replace("{model}", "claude-3-7-sonnet-20250219")
    
    # Replace the directory structure placeholder
    system_message = system_message.replace("{directory_structure}", dir_structure)
    
    # Add git status if it's a git repository
    if is_repo:
        git_status = get_git_status(cwd)
        system_message = system_message + f"\n<context name=\"gitStatus\">{git_status}</context>\n"
    
    return system_message


def get_git_status(cwd):
    """Get git status information for the context."""
    try:
        # Get current branch
        branch_cmd = ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"]
        branch = subprocess.run(branch_cmd, capture_output=True, text=True, check=False).stdout.strip()
        
        # Get remote main branch
        main_branch_cmd = ["git", "-C", cwd, "remote", "show", "origin"]
        main_output = subprocess.run(main_branch_cmd, capture_output=True, text=True, check=False).stdout
        main_branch = "main"  # Default
        for line in main_output.splitlines():
            if "HEAD branch" in line:
                main_branch = line.split(":")[-1].strip()
        
        # Get status
        status_cmd = ["git", "-C", cwd, "status", "--porcelain"]
        status_output = subprocess.run(status_cmd, capture_output=True, text=True, check=False).stdout
        
        if status_output.strip():
            status_lines = status_output.strip().split("\n")
            status = "\n".join(status_lines)
        else:
            status = "(clean)"
        
        # Get recent commits
        log_cmd = ["git", "-C", cwd, "log", "--oneline", "--max-count=5"]
        log_output = subprocess.run(log_cmd, capture_output=True, text=True, check=False).stdout.strip()
        
        git_status_text = f"""This is the git status at the start of the conversation. Note that this status is a snapshot in time, and will not update during the conversation.
Current branch: {branch}

Main branch (you will usually use this for PRs): {main_branch}

Status:
{status}

Recent commits:
{log_output}"""
        return git_status_text
    except Exception as e:
        return f"Error getting git status: {str(e)}"