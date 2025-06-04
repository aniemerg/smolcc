"""Tool implementations for SmolCC.

This package contains the implementations of tools that can be used by SmolCC.
"""

import platform

# Import platform-independent tools
from .cd_tool import ChangeDirectoryTool
from .edit_tool import FileEditTool as EditTool
from .glob_tool import GlobTool
from .grep_tool import GrepTool
from .ls_tool import LSTool
from .replace_tool import WriteTool as ReplaceTool
from .view_tool import ViewTool

# Import platform-specific shell tools
__all__ = [
    "ChangeDirectoryTool",
    "EditTool",
    "GlobTool", 
    "GrepTool",
    "LSTool",
    "ReplaceTool",
    "ViewTool",
]

if platform.system() == 'Windows':
    try:
        from .powershell_tool import PowerShellTool
        __all__.append("PowerShellTool")
    except ImportError:
        pass
else:
    try:
        from .bash_tool import BashTool
        __all__.append("BashTool")
    except ImportError:
        pass