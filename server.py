"""Core MCP server implementation for Pawlink."""

import json
import logging
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from searchneu.client import SearchNEUClient
from searchneu.models import parse_prerequisites

logger = logging.getLogger(__name__)


class PawlinkServer:
    """Main MCP Server implementation for Pawlink."""

    def __init__(self) -> None:
        self.server = Server("pawlink")
        self.searchneu_client = SearchNEUClient()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="search_courses",
                    description="Search Northeastern University courses by keyword",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search keyword or phrase",
                            },
                            "term_id": {
                                "type": "string",
                                "description": "Term ID (e.g., '202610' for Fall 2025)",
                            },
                            "first": {
                                "type": "integer",
                                "description": "Number of results to return (default: 10)",
                                "default": 10,
                            },
                        },
                        "required": ["query", "term_id"],
                    },
                ),
                types.Tool(
                    name="get_course_details",
                    description="Get detailed information about a specific course",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "Course subject code (e.g., 'CS', 'MATH')",
                            },
                            "class_id": {
                                "type": "string",
                                "description": "Course number (e.g., '2500')",
                            },
                        },
                        "required": ["subject", "class_id"],
                    },
                ),
                types.Tool(
                    name="get_course_by_hash",
                    description="Get course information by hash with all sections",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "class_hash": {
                                "type": "string",
                                "description": "Class occurrence hash",
                            }
                        },
                        "required": ["class_hash"],
                    },
                ),
                types.Tool(
                    name="get_section_details",
                    description="Get detailed information about a specific section",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "section_hash": {
                                "type": "string",
                                "description": "Section hash identifier",
                            }
                        },
                        "required": ["section_hash"],
                    },
                ),
                types.Tool(
                    name="get_available_terms",
                    description="Get available academic terms",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sub_college": {
                                "type": "string",
                                "description": "Sub-college code (default: 'NEU')",
                                "default": "NEU",
                            }
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent]:
            """Call a tool with the given arguments."""
            if arguments is None:
                arguments = {}

            try:
                if name == "search_courses":
                    result = await self._search_courses(arguments)
                elif name == "get_course_details":
                    result = await self._get_course_details(arguments)
                elif name == "get_course_by_hash":
                    result = await self._get_course_by_hash(arguments)
                elif name == "get_section_details":
                    result = await self._get_section_details(arguments)
                elif name == "get_available_terms":
                    result = await self._get_available_terms(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [types.TextContent(type="text", text=result)]

            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        @self.server.list_resources()
        async def list_resources() -> list[types.Resource]:
            """List available resources."""
            return [
                types.Resource(
                    uri="pawlink://info",
                    name="Server Information",
                    description="Information about the Pawlink MCP server",
                    mimeType="application/json",
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource by URI."""
            if uri == "pawlink://info":
                return json.dumps(
                    {
                        "name": "Pawlink MCP Server",
                        "version": "0.1.0",
                        "description": "MCP Server for SearchNEU API integration",
                        "tools": [
                            "search_courses",
                            "get_course_details",
                            "get_course_by_hash",
                            "get_section_details",
                            "get_available_terms",
                        ],
                        "resources": ["pawlink://info"],
                        "api": "SearchNEU GraphQL API",
                    },
                    indent=2,
                )
            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def _search_courses(self, args: dict[str, Any]) -> str:
        """Search for courses."""
        query = args.get("query", "")
        term_id = args.get("term_id", "")
        first = args.get("first", 10)

        result = await self.searchneu_client.search_courses(query, term_id, first)

        if not result.get("search", {}).get("nodes"):
            return f"No courses found for query: '{query}' in term {term_id}"

        courses = []
        for node in result["search"]["nodes"]:
            if node.get("__typename") == "ClassOccurrence":
                courses.append(
                    {
                        "name": node.get("name"),
                        "subject": node.get("subject"),
                        "class_id": node.get("classId"),
                        "term_id": node.get("termId"),
                        "credits": f"{node.get('minCredits', 0)}-{node.get('maxCredits', 0)}",
                        "description": node.get("desc", "")[:200] + "..."
                        if len(node.get("desc", "")) > 200
                        else node.get("desc", ""),
                    }
                )

        return json.dumps(courses, indent=2)

    async def _get_course_details(self, args: dict[str, Any]) -> str:
        """Get detailed course information."""
        subject = args.get("subject", "")
        class_id = args.get("class_id", "")

        result = await self.searchneu_client.get_class(subject, class_id)

        if not result.get("class"):
            return f"Course not found: {subject} {class_id}"

        class_data = result["class"]
        latest_occurrence = class_data.get("latestOccurrence", {})

        course_info = {
            "name": class_data.get("name"),
            "subject": class_data.get("subject"),
            "class_id": class_data.get("classId"),
            "credits": f"{latest_occurrence.get('minCredits', 0)}-{latest_occurrence.get('maxCredits', 0)}",
            "description": latest_occurrence.get("desc"),
            "prerequisites": parse_prerequisites(latest_occurrence.get("prereqs", [])),
            "corequisites": parse_prerequisites(latest_occurrence.get("coreqs", [])),
            "nupath": latest_occurrence.get("nupath", []),
            "term_id": latest_occurrence.get("termId"),
            "url": None,  # classUrl field doesn't exist in the schema,
        }

        return json.dumps(course_info, indent=2)

    async def _get_course_by_hash(self, args: dict[str, Any]) -> str:
        """Get course by hash with sections."""
        class_hash = args.get("class_hash", "")

        result = await self.searchneu_client.get_class_by_hash(class_hash)

        if not result.get("classByHash"):
            return f"Class not found for hash: {class_hash}"

        class_data = result["classByHash"]

        # Parse sections
        sections = []
        for section_data in class_data.get("sections", []):
            section = {
                "hash": section_data.get("hash"),
                "crn": section_data.get("crn"),
                "class_nbr": section_data.get("classNbr"),
                "capacity": section_data.get("capacity"),
                "remaining": section_data.get("remaining"),
                "instructor": section_data.get("instructor", {}).get("name"),
                "meetings": [],
            }

            for meeting in section_data.get("meetings", []):
                section["meetings"].append(
                    {
                        "days": meeting.get("daysPattern"),
                        "time": f"{meeting.get('startTime', '')} - {meeting.get('endTime', '')}",
                        "location": meeting.get("location"),
                    }
                )

            sections.append(section)

        course_info = {
            "name": class_data.get("name"),
            "subject": class_data.get("subject"),
            "class_id": class_data.get("classId"),
            "term_id": class_data.get("termId"),
            "credits": f"{class_data.get('minCredits', 0)}-{class_data.get('maxCredits', 0)}",
            "description": class_data.get("desc"),
            "prerequisites": parse_prerequisites(class_data.get("prereqs", [])),
            "corequisites": parse_prerequisites(class_data.get("coreqs", [])),
            "nupath": class_data.get("nupath", []),
            "sections": sections,
        }

        return json.dumps(course_info, indent=2)

    async def _get_section_details(self, args: dict[str, Any]) -> str:
        """Get section details by hash."""
        section_hash = args.get("section_hash", "")

        result = await self.searchneu_client.get_section_by_hash(section_hash)

        if not result.get("sectionByHash"):
            return f"Section not found for hash: {section_hash}"

        section_data = result["sectionByHash"]

        meetings = []
        for meeting in section_data.get("meetings", []):
            meetings.append(
                {
                    "days": meeting.get("daysPattern"),
                    "time": f"{meeting.get('startTime', '')} - {meeting.get('endTime', '')}",
                    "location": meeting.get("location"),
                    "dates": f"{meeting.get('startDate', '')} to {meeting.get('endDate', '')}",
                }
            )

        section_info = {
            "crn": section_data.get("crn"),
            "class_nbr": section_data.get("classNbr"),
            "capacity": section_data.get("capacity"),
            "remaining": section_data.get("remaining"),
            "waitlisted": section_data.get("waitlisted"),
            "instructor": section_data.get("instructor", {}).get("name"),
            "instructor_email": section_data.get("instructor", {}).get("email"),
            "meetings": meetings,
            "enrollment_status": f"{section_data.get('capacity', 0) - section_data.get('remaining', 0)}/{section_data.get('capacity', 0)} enrolled",
        }

        return json.dumps(section_info, indent=2)

    async def _get_available_terms(self, args: dict[str, Any]) -> str:
        """Get available terms."""
        sub_college = args.get("sub_college", "NEU")

        result = await self.searchneu_client.get_term_infos(sub_college)

        terms = []
        for term_data in result.get("termInfos", []):
            terms.append(
                {
                    "term_id": term_data.get("termId"),
                    "sub_college": term_data.get("subCollege"),
                    "description": term_data.get("text"),
                }
            )

        return json.dumps(terms, indent=2)

    async def run_stdio(self) -> None:
        """Run the server using stdio transport."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="pawlink",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
