"""
SearchNEU GraphQL API Client

Provides access to Northeastern University's course search API.
Supports searching courses, filtering by various criteria, and extracting
professor information and seat availability.
"""

import os
from typing import cast
from gql import gql, Client
from gql.transport.httpx import HTTPXTransport
from dotenv import load_dotenv

# Import type definitions from separate module to avoid circular imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.searchneu_types import (
    Section,
    ClassOccurrence,
    FilterOption,
    FilterOptions,
    PageInfo,
    SearchResults,
    ClassInfo,
)
from src.utils import formatters


class SearchNEUClient:
    """Client for interacting with the SearchNEU GraphQL API."""

    def __init__(self, api_url: str | None = None):
        """
        Initialize the SearchNEU client.

        Args:
            api_url: GraphQL API endpoint URL. If not provided, loads from
                    SEARCHNEU_API_URL environment variable.
        """
        # Load environment variables
        load_dotenv()

        # Get API URL from parameter or environment
        self.api_url: str = (
            api_url
            or os.getenv("SEARCHNEU_API_URL", "https://api.searchneu.com/api/")
            or "https://api.searchneu.com/api/"
        )

        # Initialize GraphQL client with httpx transport
        transport = HTTPXTransport(url=self.api_url)
        self.client = Client(transport=transport, fetch_schema_from_transport=False)

    def search_courses(
        self,
        term_id: str,
        query: str | None = None,
        subject: list[str] | None = None,
        nupath: list[str] | None = None,
        campus: list[str] | None = None,
        class_type: list[str] | None = None,
        honors: bool | None = None,
        offset: int = 0,
        first: int = 10,
    ) -> SearchResults:
        """
        Search for courses using the SearchNEU GraphQL API.

        Args:
            term_id: Term/semester ID (e.g., "202510" for Spring 2025)
            query: Search text (course name, code, or keyword)
            subject: List of subject codes to filter by (e.g., ["CS", "MATH"])
            nupath: List of NUPath requirements to filter by
            campus: List of campuses to filter by (e.g., ["Boston"])
            class_type: List of class types (e.g., ["Lecture", "Lab"])
            honors: Filter for honors courses only
            offset: Pagination offset (default: 0)
            first: Number of results to return (default: 10)

        Returns:
            Dictionary containing search results with the following structure:
            {
                "totalCount": int,
                "nodes": List[ClassOccurrence],
                "filterOptions": FilterOptions
            }

        Example:
            >>> client = SearchNEUClient()
            >>> results = client.search_courses(
            ...     term_id="202510",
            ...     query="algorithms",
            ...     subject=["CS"],
            ...     first=5
            ... )
        """
        # Build the GraphQL query
        search_query = gql(
            """
            query SearchCourses(
                $termId: String!
                $query: String
                $subject: [String!]
                $nupath: [String!]
                $campus: [String!]
                $classType: [String!]
                $honors: Boolean
                $offset: Int
                $first: Int
            ) {
                search(
                    termId: $termId
                    query: $query
                    subject: $subject
                    nupath: $nupath
                    campus: $campus
                    classType: $classType
                    honors: $honors
                    offset: $offset
                    first: $first
                ) {
                    totalCount
                    pageInfo {
                        hasNextPage
                    }
                    nodes {
                        ... on ClassOccurrence {
                            name
                            subject
                            classId
                            termId
                            desc
                            minCredits
                            maxCredits
                            classAttributes
                            nupath
                            url
                            prettyUrl
                            host
                            sections {
                                crn
                                seatsCapacity
                                seatsRemaining
                                waitCapacity
                                waitRemaining
                                campus
                                honors
                                url
                                profs
                                meetings
                                classType
                            }
                        }
                    }
                    filterOptions {
                        nupath {
                            value
                            count
                        }
                        subject {
                            value
                            count
                        }
                        classType {
                            value
                            count
                        }
                        campus {
                            value
                            count
                        }
                        honors {
                            value
                            count
                        }
                    }
                }
            }
        """
        )

        # Prepare variables
        variables = {
            "termId": term_id,
            "query": query,
            "subject": subject,
            "nupath": nupath,
            "campus": campus,
            "classType": class_type,
            "honors": honors,
            "offset": offset,
            "first": first,
        }

        # Execute query
        try:
            result = self.client.execute(search_query, variable_values=variables)
            return cast(SearchResults, result["search"])
        except Exception as e:
            raise Exception(f"Failed to search courses: {str(e)}")

    def get_class(self, subject: str, class_id: str) -> ClassInfo | None:
        """
        Get details for a specific class by subject and class ID.

        Args:
            subject: Subject code (e.g., "CS")
            class_id: Class ID (e.g., "2500")

        Returns:
            Dictionary containing class details, or None if not found.

        Example:
            >>> client = SearchNEUClient()
            >>> class_info = client.get_class("CS", "2500")
        """
        class_query = gql(
            """
            query GetClass($subject: String!, $classId: String!) {
                class(subject: $subject, classId: $classId) {
                    name
                    subject
                    classId
                    latestOccurrence {
                        name
                        subject
                        classId
                        termId
                        desc
                        minCredits
                        maxCredits
                        classAttributes
                        nupath
                        url
                        prettyUrl
                        sections {
                            crn
                            seatsCapacity
                            seatsRemaining
                            waitCapacity
                            waitRemaining
                            campus
                            honors
                            url
                            profs
                            meetings
                            classType
                        }
                    }
                }
            }
        """
        )

        variables = {"subject": subject, "classId": class_id}

        try:
            result = self.client.execute(class_query, variable_values=variables)
            return result.get("class")
        except Exception as e:
            raise Exception(f"Failed to get class {subject} {class_id}: {str(e)}")

    def get_filter_options(
        self, term_id: str, query: str | None = None
    ) -> FilterOptions:
        """
        Get available filter options with counts for a search query.

        This is useful for building dynamic filter UIs or understanding
        what filters are available for a given search.

        Args:
            term_id: Term/semester ID (e.g., "202510")
            query: Optional search query to scope the filters

        Returns:
            Dictionary with filter categories (nupath, subject, classType, etc.)
            and their available values with counts.

        Example:
            >>> client = SearchNEUClient()
            >>> filters = client.get_filter_options("202510", "CS")
            >>> print(filters["subject"])  # Shows all subjects with count
        """
        result = self.search_courses(term_id=term_id, query=query, first=1)
        return result.get("filterOptions", {})

    # Helper Methods for Filtering Results

    def filter_by_professor(
        self, search_results: SearchResults, professor_name: str
    ) -> list[ClassOccurrence]:
        """
        Filter search results to only include classes taught by a specific professor.

        Args:
            search_results: Results from search_courses()
            professor_name: Professor's name (case-insensitive partial match)

        Returns:
            List of classes that have at least one section taught by the professor.

        Example:
            >>> results = client.search_courses("202510", subject=["CS"])
            >>> smith_classes = client.filter_by_professor(results, "Smith")
        """
        filtered_classes = []
        professor_name_lower = professor_name.lower()

        for course in search_results.get("nodes", []):
            # Check if any section has this professor
            matching_sections = [
                section
                for section in course.get("sections", [])
                if any(
                    professor_name_lower in prof.lower()
                    for prof in section.get("profs", [])
                )
            ]

            if matching_sections:
                # Create a copy of the course with only matching sections
                filtered_course = course.copy()
                filtered_course["sections"] = matching_sections
                filtered_classes.append(filtered_course)

        return filtered_classes

    def filter_by_available_seats(
        self, search_results: SearchResults, min_seats: int = 1
    ) -> list[ClassOccurrence]:
        """
        Filter search results to only include classes with available seats.

        Args:
            search_results: Results from search_courses()
            min_seats: Minimum number of seats required (default: 1)

        Returns:
            List of classes that have at least one section with available seats.

        Example:
            >>> results = client.search_courses("202510", subject=["CS"])
            >>> available = client.filter_by_available_seats(results, min_seats=5)
        """
        filtered_classes = []

        for course in search_results.get("nodes", []):
            # Check if any section has enough seats
            available_sections = [
                section
                for section in course.get("sections", [])
                if section.get("seatsRemaining", 0) >= min_seats
            ]

            if available_sections:
                filtered_course = course.copy()
                filtered_course["sections"] = available_sections
                filtered_classes.append(filtered_course)

        return filtered_classes

    def filter_by_campus(
        self, search_results: SearchResults, campus: str
    ) -> list[ClassOccurrence]:
        """
        Filter search results to only include classes at a specific campus.

        Args:
            search_results: Results from search_courses()
            campus: Campus name (e.g., "Boston", "Seattle, WA")

        Returns:
            List of classes with sections at the specified campus.

        Example:
            >>> results = client.search_courses("202510", subject=["CS"])
            >>> boston_only = client.filter_by_campus(results, "Boston")
        """
        filtered_classes = []
        campus_lower = campus.lower()

        for course in search_results.get("nodes", []):
            campus_sections = [
                section
                for section in course.get("sections", [])
                if campus_lower in section.get("campus", "").lower()
            ]

            if campus_sections:
                filtered_course = course.copy()
                filtered_course["sections"] = campus_sections
                filtered_classes.append(filtered_course)

        return filtered_classes

    def get_all_professors(self, search_results: SearchResults) -> list[str]:
        """
        Extract a unique list of all professors from search results.

        Args:
            search_results: Results from search_courses()

        Returns:
            Sorted list of unique professor names.

        Example:
            >>> results = client.search_courses("202510", subject=["CS"])
            >>> profs = client.get_all_professors(results)
            >>> print(f"Found {len(profs)} unique professors")
        """
        professors = set()

        for course in search_results.get("nodes", []):
            for section in course.get("sections", []):
                professors.update(section.get("profs", []))

        return sorted(list(professors))

    # ========================================================================
    # Formatter Wrapper Methods
    # ========================================================================
    # These methods delegate to the utils.formatters module for presentation
    # logic, maintaining clean separation between data access and formatting.

    def format_search_results(self, results: SearchResults, max_courses: int) -> str:
        """
        Format search results for display.

        Args:
            results: Raw search results from search_courses()
            max_courses: Maximum number of courses requested

        Returns:
            Formatted string with course listing
        """
        return formatters.format_search_results(results, max_courses)

    def format_class_details(self, class_info: ClassInfo) -> str:
        """
        Format class details for display.

        Args:
            class_info: Raw class info from get_class()

        Returns:
            Formatted string with detailed class information
        """
        return formatters.format_class_details(class_info)

    def format_professor_courses(
        self, courses: list[ClassOccurrence], professor_name: str, term_id: str
    ) -> str:
        """
        Format courses taught by professor for display.

        Args:
            courses: Filtered list of courses
            professor_name: Professor's name
            term_id: Term ID

        Returns:
            Formatted string with professor's courses
        """
        return formatters.format_professor_courses(courses, professor_name, term_id)

    def format_available_courses(
        self,
        courses: list[ClassOccurrence],
        min_seats: int,
        subject: list[str] | None = None,
        campus: str | None = None,
    ) -> str:
        """
        Format available courses for display.

        Args:
            courses: Filtered list of courses with availability
            min_seats: Minimum seat threshold
            subject: Optional subject filter
            campus: Optional campus filter

        Returns:
            Formatted string with available courses
        """
        return formatters.format_available_courses(courses, min_seats, subject, campus)

    def format_filter_options(
        self,
        filters: FilterOptions,
        term_id: str,
        query: str | None = None,
    ) -> str:
        """
        Format filter options for display.

        Args:
            filters: Filter options dictionary
            term_id: Term ID
            query: Optional query used

        Returns:
            Formatted string with filter options
        """
        return formatters.format_filter_options(filters, term_id, query)

    # Deprecated: Old formatting method - keeping for backward compatibility
    def format_class_summary(self, class_data: ClassOccurrence) -> str:
        """
        Format class information into a human-readable summary.

        Args:
            class_data: A single class node from search results

        Returns:
            Formatted string with class details.

        Example:
            >>> results = client.search_courses("202510", query="algorithms", first=1)
            >>> for course in results["nodes"]:
            ...     print(client.format_class_summary(course))
        """
        name = class_data.get("name", "Unknown")
        subject = class_data.get("subject", "")
        class_id = class_data.get("classId", "")
        min_credits = class_data.get("minCredits", 0)
        max_credits = class_data.get("maxCredits", 0)

        # Format credits
        if min_credits == max_credits:
            credits_str = f"{min_credits} credit{'s' if min_credits != 1 else ''}"
        else:
            credits_str = f"{min_credits}-{max_credits} credits"

        # Get section info
        sections = class_data.get("sections", [])
        total_seats = sum(s.get("seatsRemaining", 0) for s in sections)
        professors = set()
        for section in sections:
            professors.update(section.get("profs", []))

        # Build summary
        summary = f"{subject} {class_id}: {name}\n"
        summary += f"Credits: {credits_str}\n"
        summary += f"Sections: {len(sections)} ({total_seats} seats available)\n"

        if professors:
            summary += f"Professors: {', '.join(sorted(professors))}\n"

        return summary
