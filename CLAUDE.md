# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Docker-based MCP (Model Context Protocol) server that integrates with the Rocketlane project management API. It provides 30+ tools for managing tasks, projects, phases, users, time entries, spaces, and custom fields.

## Key Files

- `Dockerfile` - Container configuration using Python 3.11-slim
- `requirements.txt` - Python dependencies (mcp[cli], httpx)
- `rocketlane_server.py` - Main MCP server with all tool implementations
- `readme.txt` - User documentation and usage examples

## Architecture

```
Claude Desktop --> MCP Gateway --> This Server (Docker) --> Rocketlane API
```

## API Details

- **Base URL**: `https://api.rocketlane.com/api/1.0`
- **Auth Header**: `api-key: <key>`
- **Environment Variable**: `ROCKETLANE_API_KEY`

## Code Conventions

When modifying this server, follow these critical rules:

1. **NO `@mcp.prompt()` decorators** - They break Claude Desktop
2. **NO `prompt` parameter to FastMCP()** - It breaks Claude Desktop
3. **SINGLE-LINE DOCSTRINGS ONLY** - Multi-line docstrings cause gateway panic errors
4. **DEFAULT TO EMPTY STRINGS** - Use `param: str = ""` never `param: str = None`
5. **NO complex type hints** - No `Optional`, `Union`, `List[str]`, etc.
6. **ALWAYS return strings** - All tools must return formatted strings
7. **Log to stderr** - Use the logging configuration provided
8. **Handle errors gracefully** - Return user-friendly error messages

## API Response Handling

The Rocketlane API returns data in `{"data": [...]}` format. Always:

1. **Check for error responses first** - API errors come as `{"errors": [{"errorCode": "...", "errorMessage": "..."}]}`
2. **Validate list data** - Before iterating, confirm the data is actually a list with `isinstance(items, list)`
3. **Type-check items** - Before calling `.get()` on items, verify they are dicts with `isinstance(item, dict)`

```python
data = response.json()

# Check for API errors
if isinstance(data, dict) and 'errors' in data:
    errors = data.get('errors', [])
    if errors:
        err = errors[0] if isinstance(errors, list) else errors
        return f"API Error: {err.get('errorMessage', str(err)) if isinstance(err, dict) else str(err)}"

# Extract list data
items = data.get('data', data.get('results', data)) if isinstance(data, dict) else data

if not items or not isinstance(items, list):
    return "No items found"

for item in items:
    if isinstance(item, dict):
        # Process item
```

## API Request Body Format

When creating resources that belong to a project (tasks, phases, spaces), the Rocketlane API expects project IDs in a **nested format**:

```python
# CORRECT - nested project object
body = {
    "project": {"projectId": int(project_id)},
    "taskName": task_name
}

# WRONG - flat structure causes "Project id is missing" errors
body = {
    "projectId": int(project_id),
    "taskName": task_name
}
```

This applies to: `create_task`, `create_phase`, `create_space`

## Creating Projects

When creating a project, the **customer name cannot match the vendor/organization name**. Use a suffix to differentiate:

```python
# CORRECT - customer name differs from vendor
customer_name = "SomerVentures - Customer"

# WRONG - causes API error if vendor is also named "SomerVentures"
customer_name = "SomerVentures"
```

## Assigning Tasks to Phases

Tasks can be assigned to phases using the `phase` parameter in `create_task` or `update_task`:

```python
# When creating a task with a phase
body = {
    "project": {"projectId": int(project_id)},
    "taskName": task_name,
    "phase": {"phaseId": int(phase_id)}  # Assigns task to phase
}

# When updating a task to move it to a phase
body = {
    "taskName": task_name,  # Include at least one other field
    "phase": {"phaseId": int(phase_id)}
}
```

**Note:** The `move_task_to_phase` tool uses a `/tasks/{id}/move` endpoint that returns 404. Use `update_task` with `phase_id` instead.

## Creating Subtasks

Subtasks are created by specifying a parent task. Use the `parent` parameter:

```python
body = {
    "project": {"projectId": int(project_id)},
    "taskName": subtask_name,
    "parent": {"taskId": int(parent_task_id)},  # Makes this a subtask
    "phase": {"phaseId": int(phase_id)}  # Optional: assign to phase
}
```

**Important:** The task `type` field only accepts `"TASK"` or `"MILESTONE"`. There is no `"SUBTASK"` type - subtasks are just tasks with a parent.

## Adding New Tools

```python
@mcp.tool()
async def new_tool(param1: str = "", param2: str = "") -> str:
    """Single-line description of what this tool does."""
    if not param1.strip():
        return "Error: param1 is required"

    try:
        # Implementation
        return "Success: result"
    except Exception as e:
        return f"Error: {str(e)}"
```

## Building and Testing

```powershell
# Build Docker image
docker build -t rocketlane-mcp-server .

# Set secret
docker mcp secret set ROCKETLANE_API_KEY="your-key"

# Verify server is registered
docker mcp server ls

# Local testing (without Docker)
$env:ROCKETLANE_API_KEY="your-key"
python rocketlane_server.py

# Test container directly via MCP protocol
(echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"0.1.0","clientInfo":{"name":"test","version":"1.0"},"capabilities":{}},"id":1}' && sleep 1 && echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_projects","arguments":{"limit":"3"}},"id":2}' && sleep 3) | docker run -i --rm -e "ROCKETLANE_API_KEY=your-key" rocketlane-mcp-server:latest
```

**Important:** After rebuilding the Docker image, you must restart Claude Code for the MCP gateway to pick up the new container.

## Tool Categories

| Category | Tools |
|----------|-------|
| Tasks | get_task, create_task, update_task, delete_task, list_tasks, add_task_assignees, remove_task_assignees, add_task_followers, add_task_dependencies, move_task_to_phase |
| Projects | get_project, create_project, list_projects, archive_project |
| Phases | get_phase, create_phase, update_phase, delete_phase, list_phases |
| Users | get_user, list_users |
| Fields | get_field, create_field, update_field, list_fields |
| Spaces | get_space, create_space, update_space, list_spaces, get_space_document |
| Time | get_time_entry, search_time_entries, create_time_off |
