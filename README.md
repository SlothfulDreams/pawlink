# Pawlink

Model Context Protocol (MCP) server that provides integration with the SearchNEU API for Northeastern University course information.

## Features

- Course search by keyword and academic term
- Detailed course information retrieval
- Section information and availability
- Available academic terms listing

## Installation

```bash
uv sync
```

## Usage

### Basic Usage

```bash
uv run python server.py
```

### With Custom Settings

```bash
uv run python server.py --transport stdio --log-level INFO
```

### Available Tools

- `search_courses` - Search courses by keyword and term
- `get_course_details` - Get detailed course information
- `get_course_by_hash` - Get course with sections by hash
- `get_section_details` - Get section details by hash
- `get_available_terms` - List available academic terms

## Development

### Running Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run mypy .
```

### Linting

```bash
uv run ruff check .
```

## Dependencies

- `fastmcp>=2.12.4` - MCP server framework
- `pydantic>=2.0.0` - Data validation
- `httpx>=0.27.0` - HTTP client
- `gql>=3.5.0` - GraphQL client

## License

MIT