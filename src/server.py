"""
FastMCP Server for Campus API

Exposes Northeastern University course search tools to Claude via MCP protocol.
Uses SearchNEU GraphQL API to provide course information, professor details,
and seat availability.

This server acts as a thin MCP interface layer, delegating all business logic
to the SearchNEUClient and all formatting to the utils.formatters module.
"""

from fastmcp import FastMCP
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.searchneu import SearchNEUClient

# Initialize FastMCP server
mcp = FastMCP(name="PawLink", dependencies=["gql[httpx]", "httpx", "python-dotenv"])

# Initialize SearchNEU client
searchneu_client = SearchNEUClient()


@mcp.tool()
def search_courses(
    term_id: str,
    query: str | None = None,
    subject: list[str] | None = None,
    campus: list[str] | None = None,
    class_type: list[str] | None = None,
    honors: bool | None = None,
    max_results: int = 10,
) -> str:
    """
    Search for courses at Northeastern University by keyword and filters.

    Args:
        term_id: Semester term ID (e.g., "202510" for Spring 2025)
        query: Search keyword (course name or code)
        subject: Subject codes to filter by (e.g., ["CS", "MATH"])
        campus: Campus locations (e.g., ["Boston"])
        class_type: Class types (e.g., ["Lecture", "Lab"])
        honors: Filter for honors courses only
        max_results: Maximum courses to return (default: 10, max: 100)

    Returns formatted course listings with sections, professors, and seat availability.
    """
    try:
        max_results = min(max_results, 100)

        results = searchneu_client.search_courses(
            term_id=term_id,
            query=query,
            subject=subject,
            campus=campus,
            class_type=class_type,
            honors=honors,
            first=max_results,
        )

        return searchneu_client.format_search_results(results, max_results)

    except Exception as e:
        return f"Error searching courses: {str(e)}"


@mcp.tool()
def get_class_details(subject: str, class_id: str) -> str:
    """
    Get detailed information about a specific class.

    Args:
        subject: Subject code (e.g., "CS", "MATH")
        class_id: Class ID number (e.g., "2500")

    Returns full course description, prerequisites, NUPath requirements, and all section details.
    """
    try:
        class_info = searchneu_client.get_class(subject, class_id)
        # format_class_details handles None internally, but we check to satisfy type checker
        if class_info is None:
            return f"Class {subject} {class_id} not found in the catalog."
        return searchneu_client.format_class_details(class_info)

    except Exception as e:
        return f"Error getting class details: {str(e)}"


@mcp.tool()
def find_courses_by_professor(
    term_id: str,
    professor_name: str,
    subject: list[str] | None = None,
    max_results: int = 50,
) -> str:
    """
    Find all courses taught by a specific professor.

    Args:
        term_id: Semester term ID (e.g., "202510")
        professor_name: Professor's name (partial match, case-insensitive)
        subject: Optional subject codes to narrow search
        max_results: Maximum courses to search (default: 50)

    Returns courses taught by the professor with section details and seat availability.
    """
    try:
        results = searchneu_client.search_courses(
            term_id=term_id, subject=subject, first=max_results
        )

        prof_courses = searchneu_client.filter_by_professor(results, professor_name)

        return searchneu_client.format_professor_courses(
            prof_courses, professor_name, term_id
        )

    except Exception as e:
        return f"Error finding courses by professor: {str(e)}"


@mcp.tool()
def find_available_courses(
    term_id: str,
    subject: list[str] | None = None,
    min_seats: int = 1,
    campus: str | None = None,
    max_results: int = 50,
) -> str:
    """
    Find courses with available seats.

    Args:
        term_id: Semester term ID (e.g., "202510")
        subject: Optional subject codes to filter
        min_seats: Minimum available seats required (default: 1)
        campus: Optional campus filter (e.g., "Boston")
        max_results: Maximum courses to search (default: 50)

    Returns courses with open seats, showing total availability and section details.
    """
    try:
        results = searchneu_client.search_courses(
            term_id=term_id,
            subject=subject,
            campus=[campus] if campus else None,
            first=max_results,
        )

        available_courses = searchneu_client.filter_by_available_seats(
            results, min_seats
        )

        return searchneu_client.format_available_courses(
            available_courses, min_seats, subject, campus
        )

    except Exception as e:
        return f"Error finding available courses: {str(e)}"


@mcp.tool()
def get_course_filters(term_id: str, query: str | None = None) -> str:
    """
    Get available filter options for course search.

    Args:
        term_id: Semester term ID (e.g., "202510")
        query: Optional search query to scope filters

    Returns available subjects, campuses, class types, and NUPath requirements with counts.
    """
    try:
        filters = searchneu_client.get_filter_options(term_id, query)
        return searchneu_client.format_filter_options(filters, term_id, query)

    except Exception as e:
        return f"Error getting filter options: {str(e)}"


if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
