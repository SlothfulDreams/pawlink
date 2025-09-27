#!/usr/bin/env python3
"""Main entry point for Pawlink MCP Server."""

import asyncio
import logging
import sys

from server import PawlinkServer


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main():
    """Main entry point for the MCP server."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Pawlink MCP Server for SearchNEU API...")

    try:
        server = PawlinkServer()
        await server.run_stdio()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
