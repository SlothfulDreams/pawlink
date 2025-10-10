"""
Formatting utilities for course search results.

This module contains all presentation logic for formatting course data
into human-readable strings. Separates formatting concerns from business
logic and MCP interface.
"""

import re
import sys
from pathlib import Path
from typing import TypeVar

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.searchneu_types import (
    Section,
    ClassOccurrence,
    FilterOption,
    FilterOptions,
    SearchResults,
    ClassInfo,
)

# Generic type variable for truncate_list function
T = TypeVar("T")


# ============================================================================
# Helper Functions
# ============================================================================


def format_credits(min_credits: int, max_credits: int) -> str:
    """
    Format credit range as readable string.

    Args:
        min_credits: Minimum credit hours
        max_credits: Maximum credit hours

    Returns:
        Formatted string like "3 credits" or "1-4 credits"

    Example:
        >>> format_credits(3, 3)
        "3 credits"
        >>> format_credits(1, 4)
        "1-4 credits"
    """
    if min_credits == max_credits:
        return f"{min_credits} credit{'s' if min_credits != 1 else ''}"
    return f"{min_credits}-{max_credits} credits"


def extract_professors(sections: list[Section]) -> set[str]:
    """
    Extract unique professor names from sections.

    Args:
        sections: List of section dictionaries

    Returns:
        Set of unique professor names

    Example:
        >>> sections = [{"profs": ["Smith", "Jones"]}, {"profs": ["Smith"]}]
        >>> extract_professors(sections)
        {"Smith", "Jones"}
    """
    professors = set()
    for section in sections:
        professors.update(section.get("profs", []))
    return professors


def calculate_total_seats(sections: list[Section]) -> int:
    """
    Calculate total available seats across all sections.

    Args:
        sections: List of section dictionaries

    Returns:
        Sum of seatsRemaining across all sections

    Example:
        >>> sections = [{"seatsRemaining": 5}, {"seatsRemaining": 10}]
        >>> calculate_total_seats(sections)
        15
    """
    return sum(s.get("seatsRemaining", 0) for s in sections)


def strip_html(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text: Text potentially containing HTML tags

    Returns:
        Clean text with HTML tags removed

    Example:
        >>> strip_html("<p>Hello <b>world</b></p>")
        "Hello world"
    """
    return re.sub(r"<[^<]+?>", "", text).strip()


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """
    Return singular or plural form based on count.

    Args:
        count: Number to check
        singular: Singular form of word
        plural: Plural form (defaults to singular + 's')

    Returns:
        Appropriate form with count

    Example:
        >>> pluralize(1, "section")
        "1 section"
        >>> pluralize(5, "section")
        "5 sections"
    """
    if plural is None:
        plural = singular + "s"
    form = singular if count == 1 else plural
    return f"{count} {form}"


def format_header(title: str, width: int = 80, char: str = "=") -> str:
    """
    Create a formatted header with title and separator line.

    Args:
        title: Header title text
        width: Width of separator line
        char: Character to use for separator

    Returns:
        Formatted header string

    Example:
        >>> format_header("My Title")
        "My Title\\n======================================..."
    """
    separator = char * width
    if title:
        return f"{title}\n{separator}"
    return separator


def truncate_list(
    items: list[T], max_items: int, show_count: bool = True
) -> tuple[list[T], str | None]:
    """
    Truncate a list and provide overflow message.

    Args:
        items: List to truncate
        max_items: Maximum number of items to keep
        show_count: Whether to return count message

    Returns:
        Tuple of (truncated list, overflow message or None)

    Example:
        >>> items = [1, 2, 3, 4, 5]
        >>> truncate_list(items, 3)
        ([1, 2, 3], "... and 2 more")
    """
    if len(items) <= max_items:
        return items, None

    truncated = items[:max_items]
    remaining = len(items) - max_items

    if show_count:
        message = f"... and {pluralize(remaining, 'more', 'more')}"
        return truncated, message

    return truncated, None


def format_section_details(
    section: Section, show_professors: bool = True, indent: int = 4
) -> list[str]:
    """
    Format details for a single course section.

    Args:
        section: Section dictionary with CRN, seats, profs, etc.
        show_professors: Whether to include professor names
        indent: Number of spaces to indent

    Returns:
        List of formatted lines for the section

    Example:
        >>> section = {
        ...     "crn": "12345",
        ...     "seatsRemaining": 5,
        ...     "seatsCapacity": 40,
        ...     "campus": "Boston",
        ...     "profs": ["Smith"],
        ...     "classType": "Lecture"
        ... }
        >>> format_section_details(section)
        ["- CRN 12345 (Lecture): 5/40 seats at Boston", "  Prof: Smith"]
    """
    crn = section.get("crn", "N/A")
    seats_remaining = section.get("seatsRemaining", 0)
    seats_capacity = section.get("seatsCapacity", 0)
    campus = section.get("campus", "Unknown")
    profs = section.get("profs", [])
    class_type = section.get("classType", "N/A")

    prefix = " " * indent
    lines = []

    # Main section line
    lines.append(
        f"{prefix}- CRN {crn} ({class_type}): {seats_remaining}/{seats_capacity} seats at {campus}"
    )

    # Professor line (if requested and available)
    if show_professors and profs:
        lines.append(f"{prefix}  Prof: {', '.join(profs)}")

    return lines


# ============================================================================
# Main Formatter Functions
# ============================================================================


def format_search_results(results: SearchResults, max_courses: int) -> str:
    """
    Format raw search results into readable course listing.

    Args:
        results: Raw GraphQL search results dictionary
        max_courses: Maximum number of courses that were requested

    Returns:
        Formatted string with course information including:
        - Course code, name, and credits
        - Number of sections and available seats
        - Professors teaching the course
        - Section details (CRN, seats, campus, professors)

    Example:
        >>> results = {
        ...     "totalCount": 100,
        ...     "nodes": [...]
        ... }
        >>> formatted = format_search_results(results, 10)
    """
    total_count = results.get("totalCount", 0)
    courses = results.get("nodes", [])

    if not courses:
        return f"No courses found matching your search criteria.\nTotal courses in catalog: {total_count}"

    output = []
    output.append(
        f"Found {total_count} total courses. Showing {len(courses)} results:\n"
    )
    output.append("=" * 80)

    for course in courses:
        subject = course.get("subject", "")
        class_id = course.get("classId", "")
        name = course.get("name", "Unknown")
        min_credits = course.get("minCredits", 0)
        max_credits = course.get("maxCredits", 0)
        sections = course.get("sections", [])

        # Format course header
        credits_str = format_credits(min_credits, max_credits)
        total_seats = calculate_total_seats(sections)
        professors = extract_professors(sections)

        output.append(f"\n{subject} {class_id}: {name}")
        output.append(f"  Credits: {credits_str}")
        output.append(
            f"  Sections: {pluralize(len(sections), 'section')} ({total_seats} seats available)"
        )

        if professors:
            output.append(f"  Professors: {', '.join(sorted(professors))}")

        # Show section details (limit to first 5)
        if sections:
            output.append(f"  Section Details:")
            sections_to_show, overflow_msg = truncate_list(sections, 5)

            for section in sections_to_show:
                section_lines = format_section_details(
                    section, show_professors=True, indent=4
                )
                output.extend(section_lines)

            if overflow_msg:
                output.append(f"    {overflow_msg}")

    output.append("\n" + "=" * 80)
    return "\n".join(output)


def format_class_details(class_info: ClassInfo) -> str:
    """
    Format detailed information about a specific class.

    Args:
        class_info: Raw class data from get_class() query

    Returns:
        Formatted string with comprehensive class details including:
        - Full course name and description
        - Credit hours
        - NUPath requirements
        - All sections with full details
        - URL to official course page

    Example:
        >>> class_info = {
        ...     "latestOccurrence": {
        ...         "name": "Fundamentals of CS",
        ...         "desc": "<p>Introduction to...</p>",
        ...         ...
        ...     }
        ... }
        >>> formatted = format_class_details(class_info)
    """
    if not class_info or not class_info.get("latestOccurrence"):
        subject = class_info.get("subject", "Unknown") if class_info else "Unknown"
        class_id = class_info.get("classId", "Unknown") if class_info else "Unknown"
        return f"Class {subject} {class_id} not found in the catalog."

    latest = class_info.get("latestOccurrence")
    if not latest:  # Type guard for LSP
        return f"Class information incomplete - no latest occurrence data."
    subject = latest.get("subject", "")
    class_id = latest.get("classId", "")
    name = latest.get("name", "Unknown")

    output = []
    output.append("=" * 80)
    output.append(f"{subject} {class_id}: {name}")
    output.append("=" * 80)

    # Description
    desc = latest.get("desc", "No description available")
    desc_clean = strip_html(desc)
    output.append(f"\nDescription:\n{desc_clean}\n")

    # Credits
    min_credits = latest.get("minCredits", 0)
    max_credits = latest.get("maxCredits", 0)
    output.append(f"Credits: {format_credits(min_credits, max_credits)}")

    # NUPath requirements
    nupath = latest.get("nupath", [])
    if nupath:
        output.append(f"NUPath: {', '.join(nupath)}")

    # URL
    url = latest.get("url", "")
    if url:
        output.append(f"URL: {url}")

    # Sections
    sections = latest.get("sections", [])
    output.append(f"\nSections ({len(sections)} available):")
    output.append("-" * 80)

    for section in sections:
        crn = section.get("crn", "N/A")
        seats_remaining = section.get("seatsRemaining", 0)
        seats_capacity = section.get("seatsCapacity", 0)
        wait_remaining = section.get("waitRemaining", 0)
        wait_capacity = section.get("waitCapacity", 0)
        campus = section.get("campus", "Unknown")
        profs = section.get("profs", [])
        honors = section.get("honors", False)
        class_type = section.get("classType", "Unknown")

        output.append(f"\nCRN {crn} ({class_type})")
        output.append(f"  Campus: {campus}")
        output.append(f"  Seats: {seats_remaining}/{seats_capacity} available")
        if wait_capacity > 0:
            output.append(f"  Waitlist: {wait_remaining}/{wait_capacity} available")
        if profs:
            output.append(f"  Professors: {', '.join(profs)}")
        if honors:
            output.append(f"  Honors Section")

    output.append("\n" + "=" * 80)
    return "\n".join(output)


def format_professor_courses(
    courses: list[ClassOccurrence], professor_name: str, term_id: str
) -> str:
    """
    Format courses taught by a specific professor.

    Args:
        courses: List of filtered courses taught by the professor
        professor_name: Professor's name
        term_id: Term ID for context

    Returns:
        Formatted string with professor's courses including:
        - Course code and name
        - Section CRNs taught by the professor
        - Seat availability for those sections

    Example:
        >>> courses = [
        ...     {
        ...         "subject": "CS",
        ...         "classId": "2500",
        ...         "name": "Fundamentals",
        ...         "sections": [...]
        ...     }
        ... ]
        >>> formatted = format_professor_courses(courses, "Smith", "202510")
    """
    if not courses:
        return f"No courses found taught by professor matching '{professor_name}' in term {term_id}."

    output = []
    output.append(f"Courses taught by '{professor_name}' in term {term_id}:")
    output.append("=" * 80)

    for course in courses:
        subject_code = course.get("subject", "")
        class_id = course.get("classId", "")
        name = course.get("name", "Unknown")
        sections = course.get("sections", [])

        output.append(f"\n{subject_code} {class_id}: {name}")
        output.append(f"  Sections taught by {professor_name}:")

        for section in sections:
            crn = section.get("crn", "N/A")
            seats_remaining = section.get("seatsRemaining", 0)
            seats_capacity = section.get("seatsCapacity", 0)
            section_profs = section.get("profs", [])
            class_type = section.get("classType", "N/A")

            output.append(
                f"    - CRN {crn} ({class_type}): {seats_remaining}/{seats_capacity} seats"
            )
            output.append(f"      All instructors: {', '.join(section_profs)}")

    output.append("\n" + "=" * 80)
    output.append(f"Total: {pluralize(len(courses), 'course')}")

    return "\n".join(output)


def format_available_courses(
    courses: list[ClassOccurrence],
    min_seats: int,
    subject: list[str] | None = None,
    campus: str | None = None,
) -> str:
    """
    Format courses with available seats.

    Args:
        courses: List of filtered courses with availability
        min_seats: Minimum seat threshold used for filtering
        subject: Optional subject filter applied (for messaging)
        campus: Optional campus filter applied (for messaging)

    Returns:
        Formatted string with available courses including:
        - Course code and name
        - Total seats available across sections
        - Section breakdown with seat counts
        - Professors for each section

    Example:
        >>> courses = [
        ...     {
        ...         "subject": "CS",
        ...         "classId": "2500",
        ...         "sections": [...]
        ...     }
        ... ]
        >>> formatted = format_available_courses(courses, 5, subject=["CS"])
    """
    if not courses:
        campus_str = f" at {campus}" if campus else ""
        subject_str = f" in {', '.join(subject)}" if subject else ""
        seat_str = pluralize(min_seats, "seat")
        return f"No courses found{subject_str}{campus_str} with at least {seat_str} available."

    output = []
    seat_str = pluralize(min_seats, "seat")
    output.append(f"Courses with at least {seat_str} available:")
    output.append("=" * 80)

    for course in courses:
        subject_code = course.get("subject", "")
        class_id = course.get("classId", "")
        name = course.get("name", "Unknown")
        sections = course.get("sections", [])

        # Calculate total seats
        total_seats = calculate_total_seats(sections)

        output.append(f"\n{subject_code} {class_id}: {name}")
        output.append(
            f"  Total seats available: {total_seats} across {pluralize(len(sections), 'section')}"
        )

        # Show sections with availability
        for section in sections:
            section_lines = format_section_details(
                section, show_professors=True, indent=4
            )
            output.extend(section_lines)

    output.append("\n" + "=" * 80)
    output.append(f"Total: {pluralize(len(courses), 'course')} with availability")

    return "\n".join(output)


def format_filter_options(
    filters: FilterOptions, term_id: str, query: str | None = None
) -> str:
    """
    Format available filter options with counts.

    Args:
        filters: Dictionary of filter categories and their values
        term_id: Term ID for context
        query: Optional query that was used (for messaging)

    Returns:
        Formatted string showing:
        - Available subjects with course counts
        - Available campuses with course counts
        - Available class types with course counts
        - Available NUPath requirements with course counts

    Example:
        >>> filters = {
        ...     "subject": [{"value": "CS", "count": 110}, ...],
        ...     "campus": [{"value": "Boston", "count": 500}, ...],
        ...     ...
        ... }
        >>> formatted = format_filter_options(filters, "202510")
    """
    output = []
    query_str = f" for '{query}'" if query else ""
    output.append(f"Available filter options{query_str} in term {term_id}:")
    output.append("=" * 80)

    # Subjects
    subjects = filters.get("subject", [])
    if subjects:
        output.append(f"\nSubjects ({len(subjects)} available):")
        subjects_to_show, overflow_msg = truncate_list(subjects, 20)
        for subj in subjects_to_show:
            output.append(f"  {subj['value']}: {pluralize(subj['count'], 'course')}")
        if overflow_msg:
            output.append(f"  {overflow_msg}")

    # Campuses
    campuses = filters.get("campus", [])
    if campuses:
        output.append(f"\nCampuses ({len(campuses)} available):")
        for campus in campuses:
            output.append(
                f"  {campus['value']}: {pluralize(campus['count'], 'course')}"
            )

    # Class Types
    class_types = filters.get("classType", [])
    if class_types:
        output.append(f"\nClass Types ({len(class_types)} available):")
        for ct in class_types:
            output.append(f"  {ct['value']}: {pluralize(ct['count'], 'course')}")

    # NUPath
    nupath = filters.get("nupath", [])
    if nupath:
        output.append(f"\nNUPath Requirements ({len(nupath)} available):")
        nupath_to_show, overflow_msg = truncate_list(nupath, 15)
        for np in nupath_to_show:
            output.append(f"  {np['value']}: {pluralize(np['count'], 'course')}")
        if overflow_msg:
            output.append(f"  {overflow_msg}")

    output.append("\n" + "=" * 80)
    return "\n".join(output)
