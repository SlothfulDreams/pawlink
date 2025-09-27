import asyncio
import logging
import sys

from mcp.server.fastmcp import FastMCP

from tools.searchneu.client import (
    ClassByHashResponse,
    ClassResponse,
    SearchNEUClient,
    SearchResponse,
    SectionByHashResponse,
    TermInfosResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Pawlink")

# Initialize SearchNEU client
searchneu_client = SearchNEUClient()


@mcp.tool(
    name="search_courses",
    description="Search for Northeastern University courses by keyword and academic term",
)
async def search_courses(keyword: str, term_id: str) -> SearchResponse:
    """
    Search for courses by keyword and term.

    Args:
        keyword: Search term for course names, descriptions, etc.
        term_id: Academic term ID (e.g., "202410" for Fall 2024)

    Returns:
        Search results with matching courses
    """
    try:
        results = await searchneu_client.search_courses(keyword, term_id)
        return {"search": results.get("search", {})}
    except Exception as e:
        logger.error(f"Error searching courses: {e}")
        return {"search": {}}


@mcp.tool(
    name="get_course_details",
    description="Get detailed information about a specific Northeastern University course including prerequisites, credits, and NUPath requirements",
)
async def get_course_details(
    subject: str, class_id: str, term_id: str
) -> ClassResponse:
    """
    Get detailed information about a specific course.

    Args:
        subject: Course subject code (e.g., "CS")
        class_id: Course number (e.g., "2500")
        term_id: Academic term ID (unused in current implementation)

    Returns:
        Detailed course information including description, prerequisites, etc.
    """
    try:
        course_data = await searchneu_client.get_class(subject, class_id)
        return {"class_": course_data.get("class", {})}
    except Exception as e:
        logger.error(f"Error getting course details: {e}")
        return {"class_": {}}


@mcp.tool(
    name="get_course_by_hash",
    description="Get complete course information including all available sections by using a course hash identifier",
)
async def get_course_by_hash(course_hash: str) -> ClassByHashResponse:
    """
    Get course information and sections by course hash.

    Args:
        course_hash: Unique hash identifier for the course

    Returns:
        Course information with all sections
    """
    try:
        course_data = await searchneu_client.get_class_by_hash(course_hash)
        return {"classByHash": course_data.get("classByHash", {})}
    except Exception as e:
        logger.error(f"Error getting course by hash: {e}")
        return {"classByHash": {}}


@mcp.tool(
    name="get_section_details",
    description="Get detailed section information including meeting times, instructor details, enrollment capacity, and availability",
)
async def get_section_details(section_hash: str) -> SectionByHashResponse:
    """
    Get detailed information about a specific section.

    Args:
        section_hash: Unique hash identifier for the section

    Returns:
        Section details including meeting times, instructor, availability
    """
    try:
        section_data = await searchneu_client.get_section_by_hash(section_hash)
        return {"sectionByHash": section_data.get("sectionByHash", {})}
    except Exception as e:
        logger.error(f"Error getting section details: {e}")
        return {"sectionByHash": {}}


@mcp.tool(
    name="get_available_terms",
    description="Get all available academic terms for Northeastern University to use with other course search tools",
)
async def get_available_terms() -> TermInfosResponse:
    """
    Get list of available academic terms.

    Returns:
        List of available terms with IDs and names
    """
    try:
        terms_data = await searchneu_client.get_term_infos()
        return {"termInfos": terms_data.get("termInfos", [])}
    except Exception as e:
        logger.error(f"Error getting available terms: {e}")
        return {"termInfos": []}


async def test_api_connection() -> bool:
    """Test connection to SearchNEU API."""
    try:
        terms = await searchneu_client.get_term_infos()
        term_infos = terms.get("termInfos", [])
        if isinstance(term_infos, list):
            logger.info(
                f"Successfully connected to SearchNEU API. Found {len(term_infos)} terms."
            )
        else:
            logger.info("Successfully connected to SearchNEU API. Found 0 terms.")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to SearchNEU API: {e}")
        return False


async def run_server_async(
    transport: str = "stdio",
    _host: str = "127.0.0.1",
    _port: int = 8000,
    log_level: str = "INFO",
) -> None:
    """
    Run the FastMCP server asynchronously.

    Args:
        transport: Transport protocol ('stdio', 'http', 'sse', 'streamable-http')
        _host: Host to bind to (for HTTP/SSE transports)
        _port: Port to bind to (for HTTP/SSE transports)
        log_level: Logging level
    """
    # Set log level
    log_level_value = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level_value)

    logger.info(f"Starting Pawlink MCP Server (FastMCP) with {transport} transport")

    # Test API connection
    if not await test_api_connection():
        logger.warning("API connection test failed, but server will continue to run")

    # Configure transport-specific settings
    if transport == "stdio":
        await mcp.run_stdio_async()
    elif transport == "http":
        # HTTP transport not supported by FastMCP, fall back to stdio
        logger.warning("HTTP transport not supported by FastMCP, falling back to stdio")
        await mcp.run_stdio_async()
    elif transport == "sse":
        # For SSE transport, use the synchronous method
        mcp.run(transport="sse")
    elif transport == "streamable-http":
        # For streamable HTTP transport, use the synchronous method
        mcp.run(transport="streamable-http")
    else:
        logger.error(f"Unsupported transport: {transport}")
        raise ValueError(f"Unsupported transport: {transport}")


def run_server(
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: str = "INFO",
) -> None:
    """
    Run the FastMCP server (synchronous wrapper).

    Args:
        transport: Transport protocol ('stdio', 'http', 'sse', 'streamable-http')
        host: Host to bind to (for HTTP/SSE transports)
        port: Port to bind to (for HTTP/SSE transports)
        log_level: Logging level
    """
    asyncio.run(run_server_async(transport, host, port, log_level))


def main():
    """Main entry point for the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Pawlink MCP Server")
    _ = parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    _ = parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    _ = parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    _ = parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    try:
        run_server(
            transport=str(args.transport),
            host=str(args.host),
            port=int(args.port),
            log_level=str(args.log_level),
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
