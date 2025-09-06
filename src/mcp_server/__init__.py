"""
Main entry point for MCP Unified Server
Provides backward compatibility with existing scripts
"""

from .core.configs import get_configs

# Avoid importing main from __main__ to prevent circular import warnings
def main():
    """Main entry point that imports and runs the CLI"""
    from .__main__ import main as cli_main
    return cli_main()

# For backward compatibility
def main_motherduck():
    """Legacy entry point for motherduck server"""
    return main()

def main_tariffs():
    """Legacy entry point for tariffs server"""  
    return main()

if __name__ == "__main__":
    main()
