"""
Utility functions for SmolCC.
"""


def strip_quotes(s: str) -> str:
    """
    Remove quotes from a string if present.
    
    Args:
        s: The string to strip quotes from
        
    Returns:
        The string with quotes removed
    """
    if isinstance(s, str) and len(s) >= 2:
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
    return s