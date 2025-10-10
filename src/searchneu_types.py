"""
Type definitions for SearchNEU GraphQL API structures.

This module contains TypedDict definitions for GraphQL response structures,
separated to avoid circular imports between searchneu.py and formatters.py.
"""

from typing import TypedDict


class Section(TypedDict, total=False):
    """Course section information."""

    crn: str
    seatsCapacity: int
    seatsRemaining: int
    waitCapacity: int
    waitRemaining: int
    campus: str
    honors: bool
    url: str
    profs: list[str]
    meetings: dict[str, str | int | list[str]]  # JSON field
    classType: str
    termId: str
    subject: str
    classId: str
    host: str
    lastUpdateTime: float


class ClassOccurrence(TypedDict, total=False):
    """Course class occurrence with all details."""

    name: str
    subject: str
    classId: str
    termId: str
    desc: str
    minCredits: int
    maxCredits: int
    classAttributes: list[str]
    nupath: list[str]
    url: str
    prettyUrl: str
    host: str
    sections: list[Section]
    prereqs: dict[str, str | list[str]]  # JSON field
    coreqs: dict[str, str | list[str]]  # JSON field
    prereqsFor: dict[str, str | list[str]]  # JSON field
    optPrereqsFor: dict[str, str | list[str]]  # JSON field
    feeAmount: int
    feeDescription: str
    lastUpdateTime: float


class FilterOption(TypedDict):
    """Filter option with value and count."""

    value: str
    count: int


class FilterOptions(TypedDict, total=False):
    """Available filter options."""

    nupath: list[FilterOption]
    subject: list[FilterOption]
    classType: list[FilterOption]
    campus: list[FilterOption]
    honors: list[FilterOption]


class PageInfo(TypedDict):
    """Pagination information."""

    hasNextPage: bool


class SearchResults(TypedDict):
    """Search results from GraphQL query."""

    totalCount: int
    pageInfo: PageInfo
    nodes: list[ClassOccurrence]
    filterOptions: FilterOptions


class ClassInfo(TypedDict, total=False):
    """Class information wrapper."""

    name: str
    subject: str
    classId: str
    latestOccurrence: ClassOccurrence
