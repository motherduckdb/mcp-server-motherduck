from typing import Any
from dataclasses import dataclass
import logging
import os

# Version for consolidated server
SERVER_VERSION = "1.0.0"
SERVER_NAME = "mcp-unified-server"
SERVER_LOCALHOST = "127.0.0.1"

@dataclass
class ServerConfig:
    """Configuration for the MCP server"""
    name: str = SERVER_NAME
    version: str = SERVER_VERSION
    host: str = SERVER_LOCALHOST
    log_level: str = "INFO"
    motherduck_token: str = ""
    db_config: dict = None
    
    def __post_init__(self):
        # Get MotherDuck token from environment
        self.motherduck_token = os.getenv("MOTHERDUCK_TOKEN", "")
        
        # Default database configuration
        if self.db_config is None:
            self.db_config = DEFAULT_DB_CONFIG.copy()
        
        # Convert log level string to logging constant
        if isinstance(self.log_level, str):
            self.log_level = getattr(logging, self.log_level.upper(), logging.INFO)

def get_configs() -> ServerConfig:
    """Get server configuration"""
    return ServerConfig()

# Legacy function for backward compatibility
def get_config() -> ServerConfig:
    """Legacy function - use get_configs() instead"""
    return get_configs()

# Production logging configuration (from motherduck)
UVICORN_LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter", 
            "fmt": "[mcp-server] %(levelname)s - %(message)s",
            "use_colors": None,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler", 
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {"level": "INFO"},
    },
}

# Default database configurations
DEFAULT_DB_CONFIG = {
    "read_only": True,
    "max_rows": 1000,
    "query_timeout": 30,
}
