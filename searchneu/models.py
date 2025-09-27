"""Pydantic models for SearchNEU data structures."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field


class MeetingTime(BaseModel):
    """Meeting time information for a section."""

    days_pattern: str = Field(..., description="Days of the week (e.g., 'MWF')")
    start_time: str | None = Field(None, description="Start time")
    end_time: str | None = Field(None, description="End time")
    location: str | None = Field(None, description="Meeting location")
    start_date: str | None = Field(None, description="Start date")
    end_date: str | None = Field(None, description="End date")


class Instructor(BaseModel):
    """Instructor information."""

    name: str | None = Field(None, description="Instructor name")
    email: str | None = Field(None, description="Instructor email")


class Section(BaseModel):
    """Course section information."""

    hash: str = Field(..., description="Section hash identifier")
    crn: str = Field(..., description="Course Reference Number")
    class_nbr: str = Field(..., description="Class number")
    capacity: int = Field(..., description="Total capacity")
    remaining: int = Field(..., description="Remaining seats")
    waitlisted: int | None = Field(None, description="Number of waitlisted students")
    instructor: Instructor | None = Field(None, description="Section instructor")
    meetings: list[MeetingTime] = Field(
        default_factory=list, description="Meeting times"
    )

    @property
    def is_full(self) -> bool:
        """Check if section is full."""
        return self.remaining <= 0

    @property
    def enrollment_percentage(self) -> float:
        """Calculate enrollment percentage."""
        if self.capacity == 0:
            return 0.0
        return ((self.capacity - self.remaining) / self.capacity) * 100


class Course(BaseModel):
    """Course information."""

    name: str = Field(..., description="Course name")
    subject: str = Field(..., description="Course subject code")
    class_id: str = Field(..., description="Course number")
    term_id: str = Field(..., description="Term identifier")
    max_credits: float = Field(..., description="Maximum credits")
    min_credits: float = Field(..., description="Minimum credits")
    description: str | None = Field(None, description="Course description")
    class_url: str | None = Field(None, description="Course URL")
    prerequisites: list[str] = Field(default_factory=list, description="Prerequisites")
    corequisites: list[str] = Field(default_factory=list, description="Corequisites")
    nupath: list[str] = Field(default_factory=list, description="NU Path requirements")
    sections: list[Section] = Field(default_factory=list, description="Course sections")

    @property
    def credits(self) -> float:
        """Get course credits (using max credits)."""
        return self.max_credits

    @property
    def total_sections(self) -> int:
        """Get total number of sections."""
        return len(self.sections)

    @property
    def total_capacity(self) -> int:
        """Get total capacity across all sections."""
        return sum(section.capacity for section in self.sections)

    @property
    def total_enrolled(self) -> int:
        """Get total enrolled students across all sections."""
        return sum(section.capacity - section.remaining for section in self.sections)

    @property
    def total_remaining_seats(self) -> int:
        """Get total remaining seats across all sections."""
        return sum(section.remaining for section in self.sections)


class SearchResult(BaseModel):
    """Search result from SearchNEU API."""

    nodes: list[dict[str, Any]] = Field(
        default_factory=list, description="Search result nodes"
    )


class TermInfo(BaseModel):
    """Academic term information."""

    term_id: str = Field(..., description="Term identifier")
    sub_college: str = Field(..., description="Sub-college code")
    text: str = Field(..., description="Term description")


class ClassOccurrence(BaseModel):
    """Class occurrence in a specific term."""

    name: str = Field(..., description="Course name")
    subject: str = Field(..., description="Course subject")
    class_id: str = Field(..., description="Course number")
    term_id: str = Field(..., description="Term identifier")
    max_credits: float = Field(..., description="Maximum credits")
    min_credits: float = Field(..., description="Minimum credits")
    description: str | None = Field(None, description="Course description")
    class_url: str | None = Field(None, description="Course URL")


def parse_prerequisites(prereqs_data: Any) -> list[str]:
    """Parse prerequisites from API response."""
    if isinstance(prereqs_data, str):
        return [prereqs_data]
    elif isinstance(prereqs_data, list):
        return [str(prereq) for prereq in prereqs_data]
    elif isinstance(prereqs_data, Mapping):
        # Handle complex prerequisite structure
        return [str(prereqs_data)]
    return []


def parse_meeting_times(meetings_data: list[dict[str, Any]]) -> list[MeetingTime]:
    """Parse meeting times from API response."""
    meeting_times = []
    for meeting in meetings_data:
        meeting_times.append(
            MeetingTime(
                days_pattern=meeting.get("daysPattern", ""),
                start_time=meeting.get("startTime"),
                end_time=meeting.get("endTime"),
                location=meeting.get("location"),
                start_date=meeting.get("startDate"),
                end_date=meeting.get("endDate"),
            )
        )
    return meeting_times


def parse_instructor(instructor_data: dict[str, Any] | None) -> Instructor | None:
    """Parse instructor from API response."""
    if instructor_data:
        return Instructor(
            name=instructor_data.get("name"), email=instructor_data.get("email")
        )
    return None
