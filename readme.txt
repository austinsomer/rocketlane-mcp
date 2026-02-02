# Rocketlane MCP Server

A Model Context Protocol (MCP) server that integrates with the Rocketlane project management API, enabling AI assistants to manage tasks, projects, phases, users, and more through natural language.

## Purpose

This MCP server provides a secure interface for AI assistants to interact with your Rocketlane instance. It supports comprehensive project management operations including task management, project tracking, phase organization, user management, time tracking, and collaboration spaces.

## Features

### Task Management
- `get_task` - Get a task by ID
- `create_task` - Create a new task in a project
- `update_task` - Update an existing task
- `delete_task` - Delete a task
- `list_tasks` - List all tasks with filters
- `add_task_assignees` - Add assignees to a task
- `remove_task_assignees` - Remove assignees from a task
- `add_task_followers` - Add followers to a task
- `add_task_dependencies` - Add task dependencies
- `move_task_to_phase` - Move a task to a different phase

### Project Management
- `get_project` - Get a project by ID
- `create_project` - Create a new project
- `list_projects` - List all projects with filters
- `archive_project` - Archive a project

### Phase Management
- `get_phase` - Get a phase by ID
- `create_phase` - Create a new phase
- `update_phase` - Update a phase
- `delete_phase` - Delete a phase
- `list_phases` - List all phases

### User Management
- `get_user` - Get a user by ID
- `list_users` - List all users with filters

### Custom Fields
- `get_field` - Get a field by ID
- `create_field` - Create a custom field
- `update_field` - Update a field
- `list_fields` - List all fields

### Spaces & Documents
- `get_space` - Get a space by ID
- `create_space` - Create a new space
- `update_space` - Update a space
- `list_spaces` - List all spaces
- `get_space_document` - Get a space document

### Time Management
- `get_time_entry` - Get a time entry by ID
- `search_time_entries` - Search time entries with filters
- `create_time_off` - Create a time-off request

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- Rocketlane account with API access
- Rocketlane API key (generated from Settings > API)

## Installation

See the installation steps provided with this server or refer to the CLAUDE.md file for detailed setup instructions.

## Usage Examples

In Claude Desktop or any MCP-compatible client, you can use natural language:

### Task Operations
- "List all tasks in my Rocketlane projects"
- "Create a task called 'Review proposal' in project abc123 with a due date of 2025-02-15"
- "Update task xyz789 to set progress to 50%"
- "Add john@company.com as an assignee to task abc456"
- "Move task def123 to phase ghi789"

### Project Operations
- "Show me all my Rocketlane projects"
- "Create a new project called 'Customer Onboarding' for customer 'Acme Inc'"
- "Get details for project proj123"
- "Archive the old project proj456"

### Phase Operations
- "List all phases in project proj123"
- "Create a phase called 'Implementation' in project proj123"
- "Update phase pha123 to extend the due date to 2025-03-01"

### User Operations
- "List all team members in Rocketlane"
- "Show me all active users"
- "Get details for user usr123"

### Time Tracking
- "Search time entries for user john@company.com from 2025-01-01 to 2025-01-31"
- "Create a time-off request for jane@company.com from 2025-02-10 to 2025-02-14"

## Architecture

```
Claude Desktop --> MCP Gateway --> Rocketlane MCP Server --> Rocketlane API
                                          |
                                   Docker Desktop Secrets
                                   (ROCKETLANE_API_KEY)
```

## Development

### Local Testing

```bash
# Set environment variable for testing
set ROCKETLANE_API_KEY=your-api-key-here

# Run directly
python rocketlane_server.py

# Test MCP protocol
echo {"jsonrpc":"2.0","method":"tools/list","id":1} | python rocketlane_server.py
```

### Adding New Tools

1. Add the function to `rocketlane_server.py`
2. Decorate with `@mcp.tool()`
3. Use SINGLE-LINE docstrings only
4. Use empty string defaults for parameters
5. Return formatted strings
6. Update the catalog entry with the new tool name
7. Rebuild the Docker image

## Troubleshooting

### Tools Not Appearing
- Verify Docker image built successfully: `docker images | findstr rocketlane`
- Check catalog and registry files are properly configured
- Ensure Claude Desktop config includes custom catalog
- Restart Claude Desktop

### Authentication Errors
- Verify secret is set: `docker mcp secret list`
- Ensure secret name matches in code and catalog (ROCKETLANE_API_KEY)
- Check API key is valid and not expired in Rocketlane

### API Errors
- Check Rocketlane API status
- Verify your API key has appropriate permissions
- Review error messages for specific issues

## Security Considerations

- API key stored securely in Docker Desktop secrets
- Never hardcode credentials in code
- Running as non-root user in container
- Sensitive data never logged
- API key permissions match the creating user's permissions

## API Reference

Base URL: https://api.rocketlane.com/api/1.0
Authentication: Header `api-key: <your-api-key>`
Documentation: https://developer.rocketlane.com/reference

## License

MIT License
