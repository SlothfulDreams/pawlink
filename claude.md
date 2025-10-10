# MCP Campus API Server

A Model Context Protocol (MCP) server that provides Claude with access to multiple campus/educational APIs through a unified interface.

## Purpose

This project enables Claude to:
- Search for courses and class information
- Check room availability and make bookings
- Query course data from multiple institutional systems

By exposing these capabilities as MCP tools, Claude can help students and staff interact with campus systems naturally during conversations.

## Tech Stack

| Technology | Purpose | Why We Use It |
|-----------|---------|---------------|
| **Python** | Programming language | Foundation for the entire server |
| **FastMCP** | MCP server framework | Turns functions into tools Claude can call |
| **httpx** | HTTP client | Handles REST API calls (Canvas, Room Booking) |
| **gql** | GraphQL client | Queries SearchNEU GraphQL endpoint |
| **python-dotenv** | Environment variables | Securely manages API credentials |
| **uv** | Package manager | Fast dependency management and virtual environments |

## Architecture

```
┌──────────────────────────────────────────────┐
│           Claude (MCP Client)                 │
└──────────────────────────────────────────────┘
                    ↕ MCP Protocol
┌──────────────────────────────────────────────┐
│         MCP Campus API Server                 │
│  ┌────────────────────────────────────────┐  │
│  │  Tools (server.py)                     │  │
│  │  - search_courses()                    │  │
│  │  - search_classes()                    │  │
│  │  - check_room_availability()           │  │
│  │  - book_room()                         │  │
│  └────────────────────────────────────────┘  │
│                    ↕                          │
│  ┌────────────────────────────────────────┐  │
│  │  Clients (clients/)                    │  │
│  │  - SearchNEUClient (GraphQL)           │  │
│  │  - CanvasClient (REST)                 │  │
│  │  - RoomBookingClient (REST + Cookies)  │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
                    ↕ HTTP/GraphQL
┌──────────────────────────────────────────────┐
│          External APIs                        │
│  - SearchNEU (GraphQL)                        │
│  - Infrastructure Canvas (REST)               │
│  - Room Booking System (REST + Auth)          │
└──────────────────────────────────────────────┘
```

### Key Concepts

**Tools vs Clients:**
- **Tools** = List of actions Claude can perform (the interface)
- **Clients** = How those actions actually work (the implementation)

Tools are what Claude sees and calls. Clients are the internal code that handles API communication.

## Project Structure

```
mcp-campus-api/
├── pyproject.toml         # UV project configuration
├── uv.lock               # Dependency lockfile
├── .env                  # Credentials (DO NOT COMMIT)
├── .gitignore
├── README.md
├── claude.md             # This file
├── src/
│   ├── __init__.py
│   ├── server.py         # MCP server with tool definitions
│   └── clients/
│       ├── __init__.py
│       ├── canvas.py     # Infrastructure Canvas API client
│       ├── searchneu.py  # SearchNEU GraphQL client
│       └── rooms.py      # Room booking client (cookie auth)
└── tests/                # Tests (optional)
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- UV package manager installed ([installation guide](https://docs.astral.sh/uv/))

### 2. Initialize Project

```bash
# Clone or create the project
mkdir mcp-campus-api
cd mcp-campus-api

# Initialize with UV
uv init

# Add dependencies
uv add fastmcp
uv add "gql[httpx]"
uv add httpx
uv add python-dotenv
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# .env
ROOM_BOOKING_URL=https://your-room-booking-system.edu
ROOM_BOOKING_USERNAME=your_username
ROOM_BOOKING_PASSWORD=your_password

CANVAS_BASE_URL=https://infrastructure-canvas.edu/api
CANVAS_API_KEY=your_api_key_if_needed

SEARCHNEU_URL=https://api.searchneu.com/api/
```

**⚠️ IMPORTANT:** Add `.env` to your `.gitignore` to avoid committing secrets!

### 4. Run the Server

```bash
# UV automatically manages the virtual environment
uv run python src/server.py
```

## Available Tools

### 1. `search_courses`
**Purpose:** Search for courses using SearchNEU GraphQL API

**Parameters:**
- `query` (string): Search term (course code, title, or keyword)

**Example:**
```
User: "Find all data structures courses"
Claude: [calls search_courses("data structures")]
```

### 2. `search_classes`
**Purpose:** Search for classes in Infrastructure Canvas

**Parameters:**
- `search_term` (string): Class name, code, or keyword

**Example:**
```
User: "What CS classes are available?"
Claude: [calls search_classes("CS")]
```

### 3. `check_room_availability`
**Purpose:** Check available rooms for a specific time slot

**Parameters:**
- `date` (string): Date in YYYY-MM-DD format
- `start_time` (string): Start time in HH:MM format
- `end_time` (string): End time in HH:MM format

**Example:**
```
User: "Are there any rooms available tomorrow at 2pm?"
Claude: [calls check_room_availability("2024-03-15", "14:00", "15:00")]
```

### 4. `book_room`
**Purpose:** Reserve a room for a specific time

**Parameters:**
- `room_id` (string): Room identifier
- `date` (string): Date in YYYY-MM-DD format
- `start_time` (string): Start time in HH:MM format
- `end_time` (string): End time in HH:MM format

**Example:**
```
User: "Book room 301 for tomorrow 2-3pm"
Claude: [calls book_room("301", "2024-03-15", "14:00", "15:00")]
```

## API Clients

### SearchNEUClient (GraphQL)

**File:** `src/clients/searchneu.py`

**Responsibilities:**
- Connect to SearchNEU GraphQL endpoint
- Execute course search queries
- Parse and return course data

**Key Methods:**
- `search_courses(query: str)` - Search for courses by keyword

**Authentication:** None (public API)

### CanvasClient (REST)

**File:** `src/clients/canvas.py`

**Responsibilities:**
- Query Infrastructure Canvas REST API
- Retrieve class information
- Handle API key authentication (if required)

**Key Methods:**
- `get_classes(search_term: str)` - Search for classes

**Authentication:** API key (if required)

### RoomBookingClient (REST + Cookies)

**File:** `src/clients/rooms.py`

**Responsibilities:**
- Authenticate with room booking system
- Maintain session cookies
- Query room availability
- Make room reservations

**Key Methods:**
- `login(username: str, password: str)` - Authenticate and create session
- `get_available_rooms(date, start_time, end_time)` - Check availability
- `book_room(room_id, date, start_time, end_time)` - Reserve a room

**Authentication:** Cookie-based session (username/password login)

**Special Notes:**
- Uses `httpx.Client()` to automatically manage cookies
- Authenticates once on server startup
- Maintains session across requests

## Development Notes

### Adding New Tools

To add a new tool:

1. **Create or update a client** (if needed):
```python
# src/clients/new_api.py
class NewAPIClient:
    def some_action(self, param):
        # Implementation
        pass
```

2. **Add the tool to server.py**:
```python
# src/server.py
from clients.new_api import NewAPIClient

new_api = NewAPIClient()

@mcp.tool()
def do_something(param: str) -> dict:
    """Description that Claude will see"""
    return new_api.some_action(param)
```

### Testing API Clients

Test clients independently before integrating:

```python
# test_script.py
from dotenv import load_dotenv
import os
from clients.searchneu import SearchNEUClient

load_dotenv()

client = SearchNEUClient()
result = client.search_courses("algorithms")
print(result)
```

Run with: `uv run python test_script.py`

### Error Handling Best Practices

1. **Handle authentication failures:**
```python
try:
    room_client.login(username, password)
except Exception as e:
    print(f"Login failed: {e}")
```

2. **Validate responses:**
```python
response = httpx.get(url)
if response.status_code != 200:
    raise Exception(f"API error: {response.status_code}")
```

3. **Provide helpful error messages:**
```python
@mcp.tool()
def search_courses(query: str) -> dict:
    try:
        return client.search_courses(query)
    except Exception as e:
        return {"error": f"Failed to search courses: {str(e)}"}
```

### Caching (Optional)

For frequently requested data that doesn't change often:

```python
from functools import lru_cache
from datetime import datetime, timedelta

cache = {}
CACHE_TTL = timedelta(minutes=5)

def get_with_cache(key, fetch_func):
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now() - timestamp < CACHE_TTL:
            return data

    data = fetch_func()
    cache[key] = (data, datetime.now())
    return data
```

## Security Considerations

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use environment variables** for all credentials
3. **Validate user inputs** before passing to APIs
4. **Handle authentication errors gracefully** - Don't expose credentials in error messages
5. **Consider rate limiting** to avoid overwhelming external APIs

## Deployment

### Local Development
```bash
uv run python src/server.py
```

### Production Considerations
- Use a process manager (systemd, supervisor, PM2)
- Set up proper logging
- Monitor API rate limits
- Implement retry logic for transient failures
- Consider using a secrets manager instead of `.env` files

## Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
# Ensure dependencies are installed
uv sync
```

**Authentication failures:**
- Check `.env` file exists and has correct credentials
- Verify credentials work manually in the web interface
- Check for session timeout (re-login may be needed)

**GraphQL query errors:**
- Verify the SearchNEU schema matches your queries
- Use GraphQL introspection to explore available fields
- Check for API version changes

**Cookie authentication issues:**
- Ensure `httpx.Client()` is used (not `httpx` directly)
- Check if the login endpoint has changed
- Verify cookies are being sent in subsequent requests

## Future Enhancements

- [ ] Add caching layer for frequently requested data
- [ ] Implement retry logic for failed API calls
- [ ] Add more sophisticated error handling
- [ ] Create comprehensive test suite
- [ ] Add logging for debugging
- [ ] Support multiple authentication methods
- [ ] Add tools for more campus services (dining, events, etc.)
- [ ] Implement rate limiting protection

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [UV Package Manager Docs](https://docs.astral.sh/uv/)
- [httpx Documentation](https://www.python-httpx.org/)
- [gql Documentation](https://gql.readthedocs.io/)

## License

[Your chosen license]

## Contributing

[Your contribution guidelines]

---

**Questions or issues?** [Contact information or issue tracker]
