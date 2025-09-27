"""SearchNEU GraphQL client implementation."""

import logging
from typing import Any, NotRequired, TypedDict  # type: ignore

import httpx

logger = logging.getLogger(__name__)


class ClassResponse(TypedDict):
    """Type for class response from SearchNEU API."""

    class_: NotRequired[dict[str, Any]]


class SearchResponse(TypedDict):
    """Type for search response from SearchNEU API."""

    search: dict[str, Any]


class ClassByHashResponse(TypedDict):
    """Type for class by hash response from SearchNEU API."""

    classByHash: NotRequired[dict[str, Any]]


class SectionByHashResponse(TypedDict):
    """Type for section by hash response from SearchNEU API."""

    sectionByHash: NotRequired[dict[str, Any]]


class TermInfosResponse(TypedDict):
    """Type for term infos response from SearchNEU API."""

    termInfos: list[dict[str, Any]]


class SearchNEUClient:
    """Client for interacting with the SearchNEU GraphQL API."""

    def __init__(self, api_url: str = "https://api.searchneu.com/api/") -> None:
        self.api_url: str = api_url

    async def execute_query(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a GraphQL query."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload: dict[str, Any] = {"query": query}  # type: ignore
                if variables:
                    payload["variables"] = variables

                response = await client.post(
                    self.api_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                _ = response.raise_for_status()
                result = response.json()

                if "errors" in result:
                    logger.error(f"GraphQL errors: {result['errors']}")
                    raise Exception(f"GraphQL query failed: {result['errors']}")

                return result.get("data", {})  # type: ignore

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API request failed: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise

    async def get_class(self, subject: str, class_id: str) -> dict[str, Any]:
        """Get class information by subject and class ID."""
        query = """
        query GetClass($subject: String!, $classId: String!) {
            class(subject: $subject, classId: $classId) {
                name
                subject
                classId
                latestOccurrence {
                    termId
                    desc
                    maxCredits
                    minCredits
                    prereqs
                    coreqs
                    nupath
                }
            }
        }
        """
        variables = {"subject": subject, "classId": class_id}
        return await self.execute_query(query, variables)

    async def search_courses(
        self, query: str, term_id: str, first: int = 10
    ) -> dict[str, Any]:
        """Search for courses using the search functionality."""
        search_query = """
        query SearchCourses($query: String!, $termId: String!, $first: Int) {
            search(query: $query, termId: $termId, first: $first) {
                nodes {
                    __typename
                    ... on ClassOccurrence {
                        name
                        subject
                        classId
                        termId
                        maxCredits
                        minCredits
                        desc
                    }
                }
            }
        }
        """
        variables = {"query": query, "termId": term_id, "first": first}
        return await self.execute_query(search_query, variables)

    async def get_term_infos(self, sub_college: str = "NEU") -> dict[str, Any]:
        """Get available term information."""
        query = """
        query GetTermInfos($subCollege: String!) {
            termInfos(subCollege: $subCollege) {
                termId
                subCollege
                text
            }
        }
        """
        variables = {"subCollege": sub_college}
        return await self.execute_query(query, variables)

    async def get_class_by_hash(self, class_hash: str) -> dict[str, Any]:
        """Get class occurrence by hash."""
        query = """
        query GetClassByHash($hash: String!) {
            classByHash(hash: $hash) {
                name
                subject
                classId
                termId
                maxCredits
                minCredits
                desc
                prereqs
                coreqs
                nupath
                sections {
                    host
                    crn
                    classId
                    waitCapacity
                    waitRemaining
                    meetings
                }
            }
        }
        """
        variables = {"hash": class_hash}
        return await self.execute_query(query, variables)

    async def get_section_by_hash(self, section_hash: str) -> dict[str, Any]:
        """Get section information by hash."""
        query = """
        query GetSectionByHash($hash: String!) {
            sectionByHash(hash: $hash) {
                host
                crn
                classId
                waitCapacity
                waitRemaining
                meetings
            }
        }
        """
        variables = {"hash": section_hash}
        return await self.execute_query(query, variables)
