"""Tool implementations for SmolCC.

This package contains the implementations of tools that can be used by SmolCC.
"""

# Original tools
from .bash_tool import BashTool
from .edit_tool import FileEditTool as EditTool
from .glob_tool import GlobTool
from .grep_tool import GrepTool
from .ls_tool import LSTool
from .replace_tool import WriteTool as ReplaceTool
from .view_tool import ViewTool

# Enhanced tools with rich output
from .enhanced_ls_tool import enhanced_ls_tool as EnhancedLSTool
from .enhanced_view_tool import enhanced_view_tool as EnhancedViewTool
from .enhanced_glob_tool import enhanced_glob_tool as EnhancedGlobTool
from .enhanced_grep_tool import enhanced_grep_tool as EnhancedGrepTool
from .enhanced_bash_tool import enhanced_bash_tool as EnhancedBashTool

__all__ = [
    # Original tools
    "BashTool",
    "EditTool",
    "GlobTool",
    "GrepTool",
    "LSTool",
    "ReplaceTool",
    "ViewTool",
    
    # Enhanced tools
    "EnhancedLSTool",
    "EnhancedViewTool",
    "EnhancedGlobTool",
    "EnhancedGrepTool",
    "EnhancedBashTool",
]