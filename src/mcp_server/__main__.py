"""
Command Line Interface for MCP Unified Server
Consolidates professional CLI from motherduck server with unified server
"""

import asyncio
import logging
import mcp.server.stdio
import mcp.server.sse
import click
import uvicorn
from mcp.server.models import InitializationOptions

from .server import MCPUnifiedServer
from .core.configs import get_configs

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--transport', 
              type=click.Choice(['stdio', 'sse', 'stream']), 
              default='stdio',
              help='Transport mechanism to use')
@click.option('--host', default='127.0.0.1', help='Host to bind to (for sse/stream)')
@click.option('--port', default=8000, type=int, help='Port to bind to (for sse/stream)')
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              default='INFO',
              help='Logging level')
def main(ctx, transport, host, port, log_level):
    """MCP Unified Server with DuckDB/MotherDuck support and plugin architecture"""
    
    if ctx.invoked_subcommand is None:
        # Default behavior: run server
        asyncio.run(run_server(transport, host, port, log_level))

@main.command()
@click.option('--transport', 
              type=click.Choice(['stdio', 'sse', 'stream']), 
              default='stdio',
              help='Transport mechanism to use')
@click.option('--host', default='127.0.0.1', help='Host to bind to (for sse/stream)')
@click.option('--port', default=8000, type=int, help='Port to bind to (for sse/stream)')
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              default='INFO',
              help='Logging level')
def serve(transport, host, port, log_level):
    """Start the MCP server"""
    asyncio.run(run_server(transport, host, port, log_level))

@main.command()
def info():
    """Show server information"""
    config = get_configs()
    click.echo(f"""
MCP Unified Server Information:
==============================
Name: {config.name}
Version: {config.version}
Host: {config.host}
Log Level: {config.log_level}

Available Transports:
- stdio: Standard input/output (default, for MCP clients)
- sse: Server-Sent Events over HTTP
- stream: HTTP streaming protocol

Plugin Support:
- Modular dataset architecture
- Auto-discovery of dataset plugins
- Specialized tools per dataset

Supported Databases:
- Local DuckDB files
- MotherDuck cloud databases
- Enhanced safety features and query validation
    """)

@main.command()
def plugins():
    """List available plugins"""
    from .plugins import get_plugin_registry
    
    registry = get_plugin_registry()
    click.echo("Available Dataset Plugins:")
    click.echo("=" * 40)
    
    if not registry:
        click.echo("No plugins found.")
        return
    
    for name, plugin_class in registry.items():
        plugin_instance = plugin_class()
        click.echo(f"• {name}: {plugin_instance.description}")

async def run_server(transport: str, host: str, port: int, log_level: str):
    """Run the MCP server with specified transport"""
    
    # Set up logging
    logging.basicConfig(level=getattr(logging, log_level))
    logger = logging.getLogger(__name__)
    
    # Create server instance
    server = MCPUnifiedServer()
    await server.initialize()
    
    config = get_configs()
    
    try:
        if transport == 'stdio':
            logger.info(f"Starting {config.name} with stdio transport")
            await server.run_stdio()
            
        elif transport == 'sse':
            logger.info(f"Starting {config.name} with SSE transport on {host}:{port}")
            
            async with mcp.server.sse.sse_server() as sse:
                from fastapi import FastAPI
                from fastapi.responses import JSONResponse
                
                app = FastAPI(title=config.name, version=config.version)
                
                @app.get("/")
                async def root():
                    return JSONResponse({
                        "name": config.name,
                        "version": config.version,
                        "transport": "sse",
                        "status": "running"
                    })
                
                app.mount("/sse", sse)
                
                uvicorn_config = uvicorn.Config(
                    app=app,
                    host=host,
                    port=port,
                    log_level=log_level.lower()
                )
                
                server_instance = uvicorn.Server(uvicorn_config)
                
                await sse.run(
                    server.server,
                    InitializationOptions(
                        server_name=config.name,
                        server_version=config.version,
                        capabilities=server.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities={}
                        ),
                    ),
                )
                
                await server_instance.serve()
                
        elif transport == 'stream':
            logger.info(f"Starting {config.name} with stream transport on {host}:{port}")
            
            from fastapi import FastAPI
            from fastapi.responses import JSONResponse
            
            app = FastAPI(title=config.name, version=config.version)
            
            @app.get("/")
            async def root():
                return JSONResponse({
                    "name": config.name,
                    "version": config.version,
                    "transport": "stream",
                    "status": "running"
                })
            
            @app.post("/mcp")
            async def mcp_endpoint():
                # Basic HTTP endpoint for MCP protocol
                return JSONResponse({"message": "MCP stream endpoint - not yet implemented"})
            
            uvicorn_config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level=log_level.lower()
            )
            
            server_instance = uvicorn.Server(uvicorn_config)
            await server_instance.serve()
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()
