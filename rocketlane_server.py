#!/usr/bin/env python3
"""Rocketlane MCP Server - Integrates with Rocketlane project management API."""
import os
import sys
import logging
import json
import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("rocketlane-server")

# Initialize MCP server - NO PROMPT PARAMETER!
mcp = FastMCP("rocketlane")

# Configuration
API_KEY = os.environ.get("ROCKETLANE_API_KEY", "")
BASE_URL = "https://api.rocketlane.com/api/1.0"


def get_headers():
    """Get headers for API requests."""
    return {
        "accept": "application/json",
        "api-key": API_KEY,
        "content-type": "application/json"
    }


def format_task(task):
    """Format a task object for display."""
    lines = [f"Task: {task.get('taskName', 'N/A')}"]
    lines.append(f"  ID: {task.get('taskId', 'N/A')}")
    if task.get('taskDescription'):
        lines.append(f"  Description: {task.get('taskDescription', '')[:100]}")
    status = task.get('status', 'N/A')
    if isinstance(status, dict):
        status = status.get('label', 'N/A')
    lines.append(f"  Status: {status}")
    lines.append(f"  Start Date: {task.get('startDate', 'N/A')}")
    lines.append(f"  Due Date: {task.get('dueDate', 'N/A')}")
    lines.append(f"  Progress: {task.get('progress', 0)}%")
    if task.get('assignees'):
        assignee_names = [a.get('firstName', '') + ' ' + a.get('lastName', '') for a in task.get('assignees', [])]
        lines.append(f"  Assignees: {', '.join(assignee_names)}")
    return '\n'.join(lines)


def format_project(project):
    """Format a project object for display."""
    lines = [f"Project: {project.get('projectName', 'N/A')}"]
    lines.append(f"  ID: {project.get('projectId', 'N/A')}")
    status = project.get('status', 'N/A')
    if isinstance(status, dict):
        status = status.get('label', 'N/A')
    lines.append(f"  Status: {status}")
    lines.append(f"  Start Date: {project.get('startDate', 'N/A')}")
    lines.append(f"  Due Date: {project.get('dueDate', 'N/A')}")
    customer = project.get('customer')
    if customer:
        if isinstance(customer, dict):
            customer = customer.get('companyName', 'N/A')
        lines.append(f"  Customer: {customer}")
    lines.append(f"  Progress: {project.get('progress', 0)}%")
    return '\n'.join(lines)


def format_phase(phase):
    """Format a phase object for display."""
    lines = [f"Phase: {phase.get('phaseName', 'N/A')}"]
    lines.append(f"  ID: {phase.get('phaseId', 'N/A')}")
    status = phase.get('status', 'N/A')
    if isinstance(status, dict):
        status = status.get('label', 'N/A')
    lines.append(f"  Status: {status}")
    lines.append(f"  Start Date: {phase.get('startDate', 'N/A')}")
    lines.append(f"  Due Date: {phase.get('dueDate', 'N/A')}")
    return '\n'.join(lines)


def format_user(user):
    """Format a user object for display."""
    lines = [f"User: {user.get('firstName', '')} {user.get('lastName', '')}"]
    lines.append(f"  ID: {user.get('userId', 'N/A')}")
    lines.append(f"  Email: {user.get('email', 'N/A')}")
    lines.append(f"  Type: {user.get('type', 'N/A')}")
    lines.append(f"  Status: {user.get('status', 'N/A')}")
    return '\n'.join(lines)


def format_space(space):
    """Format a space object for display."""
    lines = [f"Space: {space.get('spaceName', 'N/A')}"]
    lines.append(f"  ID: {space.get('spaceId', 'N/A')}")
    lines.append(f"  Private: {space.get('private', False)}")
    return '\n'.join(lines)


def format_field(field):
    """Format a field object for display."""
    lines = [f"Field: {field.get('label', 'N/A')}"]
    lines.append(f"  ID: {field.get('fieldId', 'N/A')}")
    lines.append(f"  Type: {field.get('type', 'N/A')}")
    if field.get('description'):
        lines.append(f"  Description: {field.get('description', '')}")
    return '\n'.join(lines)


def format_time_entry(entry):
    """Format a time entry object for display."""
    lines = [f"Time Entry: {entry.get('timeEntryId', 'N/A')}"]
    lines.append(f"  Date: {entry.get('date', 'N/A')}")
    lines.append(f"  Minutes: {entry.get('minutes', 0)}")
    lines.append(f"  Billable: {entry.get('billable', False)}")
    if entry.get('notes'):
        lines.append(f"  Notes: {entry.get('notes', '')[:100]}")
    return '\n'.join(lines)


# === TASK TOOLS ===

@mcp.tool()
async def get_task(task_id: str = "") -> str:
    """Get a task by its unique ID from Rocketlane."""
    if not task_id.strip():
        return "Error: task_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Getting task {task_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/tasks/{task_id}",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            task = response.json()
            return f"Task retrieved:\n{format_task(task)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_task(project_id: str = "", task_name: str = "", description: str = "", start_date: str = "", due_date: str = "", effort_minutes: str = "", task_type: str = "", phase_id: str = "", parent_task_id: str = "") -> str:
    """Create a new task or subtask in a Rocketlane project with name, dates, phase, and optional parent."""
    if not project_id.strip():
        return "Error: project_id is required"
    if not task_name.strip():
        return "Error: task_name is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Creating task '{task_name}' in project {project_id}")
    try:
        body = {
            "project": {"projectId": int(project_id)},
            "taskName": task_name
        }
        if description.strip():
            body["taskDescription"] = description
        if start_date.strip():
            body["startDate"] = start_date
        if due_date.strip():
            body["dueDate"] = due_date
        if effort_minutes.strip():
            body["effortInMinutes"] = int(effort_minutes)
        if task_type.strip():
            valid_types = ["TASK", "MILESTONE"]
            task_type_upper = task_type.upper()
            if task_type_upper not in valid_types:
                return f"Error: Invalid task_type '{task_type}'. Valid types are: TASK, MILESTONE (use parent_task_id for subtasks)"
            body["type"] = task_type_upper
        if phase_id.strip():
            body["phase"] = {"phaseId": int(phase_id)}
        if parent_task_id.strip():
            body["parent"] = {"taskId": int(parent_task_id)}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/tasks",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            task = response.json()
            return f"Task created:\n{format_task(task)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def update_task(task_id: str = "", task_name: str = "", description: str = "", start_date: str = "", due_date: str = "", progress: str = "", status_value: str = "", phase_id: str = "") -> str:
    """Update an existing task by ID with new name, dates, phase, progress, or status."""
    if not task_id.strip():
        return "Error: task_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Updating task {task_id}")
    try:
        body = {}
        if task_name.strip():
            body["taskName"] = task_name
        if description.strip():
            body["taskDescription"] = description
        if start_date.strip():
            body["startDate"] = start_date
        if due_date.strip():
            body["dueDate"] = due_date
        if progress.strip():
            body["progress"] = int(progress)
        if status_value.strip():
            body["status"] = {"value": int(status_value)}
        if phase_id.strip():
            body["phase"] = {"phaseId": int(phase_id)}

        if not body:
            return "Error: At least one field to update is required"

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}/tasks/{task_id}",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            task = response.json()
            return f"Task updated:\n{format_task(task)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def delete_task(task_id: str = "") -> str:
    """Delete a task by its unique ID - this action cannot be undone."""
    if not task_id.strip():
        return "Error: task_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Deleting task {task_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{BASE_URL}/tasks/{task_id}",
                headers=get_headers(),
                timeout=30
            )
            if response.status_code == 204:
                return f"Task {task_id} deleted successfully"
            response.raise_for_status()
            return f"Task {task_id} deleted"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_tasks(project_id: str = "", phase_id: str = "", status: str = "", limit: str = "50") -> str:
    """List all tasks with optional filters for project, phase, or status."""
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info("Listing tasks")
    try:
        params = {"pageSize": int(limit) if limit.strip() else 50}
        if project_id.strip():
            params["projectId.eq"] = project_id
        if phase_id.strip():
            params["phaseId.eq"] = phase_id
        if status.strip():
            params["status.eq"] = status

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/tasks",
                headers=get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'errors' in data:
                errors = data.get('errors', [])
                if errors:
                    err = errors[0] if isinstance(errors, list) else errors
                    return f"API Error: {err.get('errorMessage', str(err)) if isinstance(err, dict) else str(err)}"

            tasks = data.get('data', data.get('results', data)) if isinstance(data, dict) else data

            if not tasks or not isinstance(tasks, list):
                return "No tasks found"

            result = [f"Found {len(tasks)} task(s):\n"]
            for task in tasks:
                if isinstance(task, dict):
                    result.append(format_task(task))
                    result.append("")
            return '\n'.join(result)
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def add_task_assignees(task_id: str = "", user_emails: str = "") -> str:
    """Add assignees to a task by providing comma-separated email addresses."""
    if not task_id.strip():
        return "Error: task_id is required"
    if not user_emails.strip():
        return "Error: user_emails is required (comma-separated)"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Adding assignees to task {task_id}")
    try:
        emails = [e.strip() for e in user_emails.split(',') if e.strip()]
        body = {"assignees": [{"emailId": email} for email in emails]}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/tasks/{task_id}/assignees",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return f"Assignees added to task {task_id}: {', '.join(emails)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error adding assignees: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def remove_task_assignees(task_id: str = "", user_emails: str = "") -> str:
    """Remove assignees from a task by providing comma-separated email addresses."""
    if not task_id.strip():
        return "Error: task_id is required"
    if not user_emails.strip():
        return "Error: user_emails is required (comma-separated)"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Removing assignees from task {task_id}")
    try:
        emails = [e.strip() for e in user_emails.split(',') if e.strip()]
        body = {"assignees": [{"emailId": email} for email in emails]}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/tasks/{task_id}/assignees/remove",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return f"Assignees removed from task {task_id}: {', '.join(emails)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error removing assignees: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def add_task_followers(task_id: str = "", user_emails: str = "") -> str:
    """Add followers to a task by providing comma-separated email addresses."""
    if not task_id.strip():
        return "Error: task_id is required"
    if not user_emails.strip():
        return "Error: user_emails is required (comma-separated)"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Adding followers to task {task_id}")
    try:
        emails = [e.strip() for e in user_emails.split(',') if e.strip()]
        body = {"followers": [{"emailId": email} for email in emails]}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/tasks/{task_id}/followers",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return f"Followers added to task {task_id}: {', '.join(emails)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error adding followers: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def add_task_dependencies(task_id: str = "", dependency_task_ids: str = "") -> str:
    """Add dependencies to a task by providing comma-separated task IDs that must complete first."""
    if not task_id.strip():
        return "Error: task_id is required"
    if not dependency_task_ids.strip():
        return "Error: dependency_task_ids is required (comma-separated)"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Adding dependencies to task {task_id}")
    try:
        dep_ids = [d.strip() for d in dependency_task_ids.split(',') if d.strip()]
        body = {"dependencies": [{"taskId": tid} for tid in dep_ids]}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/tasks/{task_id}/dependencies",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return f"Dependencies added to task {task_id}: {', '.join(dep_ids)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error adding dependencies: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def move_task_to_phase(task_id: str = "", phase_id: str = "") -> str:
    """Move a task to a different phase by updating its phase assignment."""
    if not task_id.strip():
        return "Error: task_id is required"
    if not phase_id.strip():
        return "Error: phase_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Moving task {task_id} to phase {phase_id}")
    try:
        body = {"phase": {"phaseId": int(phase_id)}}

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}/tasks/{task_id}",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return f"Task {task_id} moved to phase {phase_id}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error moving task: {e}")
        return f"Error: {str(e)}"


# === PROJECT TOOLS ===

@mcp.tool()
async def get_project(project_id: str = "") -> str:
    """Get a project by its unique ID from Rocketlane."""
    if not project_id.strip():
        return "Error: project_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Getting project {project_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/projects/{project_id}",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            project = response.json()
            return f"Project retrieved:\n{format_project(project)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_project(project_name: str = "", customer_name: str = "", owner_email: str = "", start_date: str = "", due_date: str = "") -> str:
    """Create a new project with name, customer, owner, dates. Customer name must differ from vendor name."""
    if not project_name.strip():
        return "Error: project_name is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Creating project '{project_name}'")
    try:
        body = {"projectName": project_name}
        if customer_name.strip():
            # Note: Customer name cannot match the vendor/organization name in Rocketlane
            # If you get a name conflict error, append " - Customer" to the customer name
            body["customer"] = {"companyName": customer_name}
        if owner_email.strip():
            body["owner"] = {"emailId": owner_email}
        if start_date.strip():
            body["startDate"] = start_date
        if due_date.strip():
            body["dueDate"] = due_date

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/projects",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            project = response.json()
            return f"Project created:\n{format_project(project)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_projects(status: str = "", customer_name: str = "", limit: str = "50") -> str:
    """List all projects with optional filters for status or customer name."""
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info("Listing projects")
    try:
        params = {"pageSize": int(limit) if limit.strip() else 50}
        if status.strip():
            params["status"] = status
        if customer_name.strip():
            params["customerName"] = customer_name

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/projects",
                headers=get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Check for API error response
            if isinstance(data, dict) and 'errors' in data:
                errors = data.get('errors', [])
                if errors:
                    err = errors[0] if isinstance(errors, list) else errors
                    return f"API Error: {err.get('errorMessage', str(err)) if isinstance(err, dict) else str(err)}"

            projects = data.get('data', data.get('results', data)) if isinstance(data, dict) else data

            if not projects or not isinstance(projects, list):
                return "No projects found"

            result = [f"Found {len(projects)} project(s):\n"]
            for project in projects:
                if isinstance(project, dict):
                    result.append(format_project(project))
                    result.append("")
            return '\n'.join(result)
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def archive_project(project_id: str = "") -> str:
    """Archive a project by ID - archived projects can be restored later."""
    if not project_id.strip():
        return "Error: project_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Archiving project {project_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/projects/{project_id}/archive",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return f"Project {project_id} archived successfully"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error archiving project: {e}")
        return f"Error: {str(e)}"


# === PHASE TOOLS ===

@mcp.tool()
async def get_phase(phase_id: str = "") -> str:
    """Get a phase by its unique ID from Rocketlane."""
    if not phase_id.strip():
        return "Error: phase_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Getting phase {phase_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/phases/{phase_id}",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            phase = response.json()
            return f"Phase retrieved:\n{format_phase(phase)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error getting phase: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_phase(project_id: str = "", phase_name: str = "", start_date: str = "", due_date: str = "", is_private: str = "") -> str:
    """Create a new phase in a Rocketlane project with name and dates."""
    if not project_id.strip():
        return "Error: project_id is required"
    if not phase_name.strip():
        return "Error: phase_name is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Creating phase '{phase_name}' in project {project_id}")
    try:
        body = {
            "project": {"projectId": int(project_id)},
            "phaseName": phase_name
        }
        if start_date.strip():
            body["startDate"] = start_date
        if due_date.strip():
            body["dueDate"] = due_date
        if is_private.strip():
            body["private"] = is_private.lower() == "true"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/phases",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            phase = response.json()
            return f"Phase created:\n{format_phase(phase)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error creating phase: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def update_phase(phase_id: str = "", phase_name: str = "", start_date: str = "", due_date: str = "", status_value: str = "") -> str:
    """Update an existing phase by ID with new name, dates, or status."""
    if not phase_id.strip():
        return "Error: phase_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Updating phase {phase_id}")
    try:
        body = {}
        if phase_name.strip():
            body["phaseName"] = phase_name
        if start_date.strip():
            body["startDate"] = start_date
        if due_date.strip():
            body["dueDate"] = due_date
        if status_value.strip():
            body["status"] = {"value": int(status_value)}

        if not body:
            return "Error: At least one field to update is required"

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}/phases/{phase_id}",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            phase = response.json()
            return f"Phase updated:\n{format_phase(phase)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error updating phase: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def delete_phase(phase_id: str = "") -> str:
    """Delete a phase by its unique ID - this action cannot be undone."""
    if not phase_id.strip():
        return "Error: phase_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Deleting phase {phase_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{BASE_URL}/phases/{phase_id}",
                headers=get_headers(),
                timeout=30
            )
            if response.status_code == 204:
                return f"Phase {phase_id} deleted successfully"
            response.raise_for_status()
            return f"Phase {phase_id} deleted"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error deleting phase: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_phases(project_id: str = "", limit: str = "50") -> str:
    """List all phases with optional filter for project ID."""
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info("Listing phases")
    try:
        params = {"pageSize": int(limit) if limit.strip() else 50}
        if project_id.strip():
            params["projectId"] = project_id

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/phases",
                headers=get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'errors' in data:
                errors = data.get('errors', [])
                if errors:
                    err = errors[0] if isinstance(errors, list) else errors
                    return f"API Error: {err.get('errorMessage', str(err)) if isinstance(err, dict) else str(err)}"

            phases = data.get('data', data.get('results', data)) if isinstance(data, dict) else data

            if not phases or not isinstance(phases, list):
                return "No phases found"

            result = [f"Found {len(phases)} phase(s):\n"]
            for phase in phases:
                if isinstance(phase, dict):
                    result.append(format_phase(phase))
                    result.append("")
            return '\n'.join(result)
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error listing phases: {e}")
        return f"Error: {str(e)}"


# === USER TOOLS ===

@mcp.tool()
async def get_user(user_id: str = "") -> str:
    """Get a user by their unique ID from Rocketlane."""
    if not user_id.strip():
        return "Error: user_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Getting user {user_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/users/{user_id}",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            user = response.json()
            return f"User retrieved:\n{format_user(user)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_users(user_type: str = "", status: str = "", limit: str = "50") -> str:
    """List all users with optional filters for type (TEAM_MEMBER, PARTNER, CUSTOMER) or status."""
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info("Listing users")
    try:
        params = {"pageSize": int(limit) if limit.strip() else 50}
        if user_type.strip():
            params["type"] = user_type.upper()
        if status.strip():
            params["status"] = status.upper()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/users",
                headers=get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'errors' in data:
                errors = data.get('errors', [])
                if errors:
                    err = errors[0] if isinstance(errors, list) else errors
                    return f"API Error: {err.get('errorMessage', str(err)) if isinstance(err, dict) else str(err)}"

            users = data.get('data', data.get('results', data)) if isinstance(data, dict) else data

            if not users or not isinstance(users, list):
                return "No users found"

            result = [f"Found {len(users)} user(s):\n"]
            for user in users:
                if isinstance(user, dict):
                    result.append(format_user(user))
                    result.append("")
            return '\n'.join(result)
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return f"Error: {str(e)}"


# === FIELD TOOLS ===

@mcp.tool()
async def get_field(field_id: str = "") -> str:
    """Get a custom field by its unique ID from Rocketlane."""
    if not field_id.strip():
        return "Error: field_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Getting field {field_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/fields/{field_id}",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            field = response.json()
            return f"Field retrieved:\n{format_field(field)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error getting field: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_field(label: str = "", field_type: str = "", description: str = "", entity_type: str = "") -> str:
    """Create a new custom field in Rocketlane with label, type, and optional description."""
    if not label.strip():
        return "Error: label is required"
    if not field_type.strip():
        return "Error: field_type is required (TEXT, NUMBER, DATE, SELECT, etc.)"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Creating field '{label}'")
    try:
        body = {
            "label": label,
            "type": field_type.upper()
        }
        if description.strip():
            body["description"] = description
        if entity_type.strip():
            body["entityType"] = entity_type.upper()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/fields",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            field = response.json()
            return f"Field created:\n{format_field(field)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error creating field: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def update_field(field_id: str = "", label: str = "", description: str = "") -> str:
    """Update an existing custom field by ID with new label or description."""
    if not field_id.strip():
        return "Error: field_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Updating field {field_id}")
    try:
        body = {}
        if label.strip():
            body["label"] = label
        if description.strip():
            body["description"] = description

        if not body:
            return "Error: At least one field to update is required"

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}/fields/{field_id}",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            field = response.json()
            return f"Field updated:\n{format_field(field)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error updating field: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_fields(entity_type: str = "", limit: str = "50") -> str:
    """List all custom fields with optional filter for entity type (TASK, PROJECT, etc.)."""
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info("Listing fields")
    try:
        params = {"pageSize": int(limit) if limit.strip() else 50}
        if entity_type.strip():
            params["entityType"] = entity_type.upper()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/fields",
                headers=get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'errors' in data:
                errors = data.get('errors', [])
                if errors:
                    err = errors[0] if isinstance(errors, list) else errors
                    return f"API Error: {err.get('errorMessage', str(err)) if isinstance(err, dict) else str(err)}"

            fields = data.get('data', data.get('results', data)) if isinstance(data, dict) else data

            if not fields or not isinstance(fields, list):
                return "No fields found"

            result = [f"Found {len(fields)} field(s):\n"]
            for field in fields:
                if isinstance(field, dict):
                    result.append(format_field(field))
                    result.append("")
            return '\n'.join(result)
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error listing fields: {e}")
        return f"Error: {str(e)}"


# === SPACE TOOLS ===

@mcp.tool()
async def get_space(space_id: str = "") -> str:
    """Get a space by its unique ID from Rocketlane."""
    if not space_id.strip():
        return "Error: space_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Getting space {space_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/spaces/{space_id}",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            space = response.json()
            return f"Space retrieved:\n{format_space(space)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error getting space: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_space(project_id: str = "", space_name: str = "", is_private: str = "") -> str:
    """Create a new space in a Rocketlane project for collaboration and documents."""
    if not project_id.strip():
        return "Error: project_id is required"
    if not space_name.strip():
        return "Error: space_name is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Creating space '{space_name}' in project {project_id}")
    try:
        body = {
            "project": {"projectId": int(project_id)},
            "spaceName": space_name
        }
        if is_private.strip():
            body["private"] = is_private.lower() == "true"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/spaces",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            space = response.json()
            return f"Space created:\n{format_space(space)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error creating space: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def update_space(space_id: str = "", space_name: str = "", is_private: str = "") -> str:
    """Update an existing space by ID with new name or privacy setting."""
    if not space_id.strip():
        return "Error: space_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Updating space {space_id}")
    try:
        body = {}
        if space_name.strip():
            body["spaceName"] = space_name
        if is_private.strip():
            body["private"] = is_private.lower() == "true"

        if not body:
            return "Error: At least one field to update is required"

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}/spaces/{space_id}",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            space = response.json()
            return f"Space updated:\n{format_space(space)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error updating space: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_spaces(project_id: str = "", limit: str = "50") -> str:
    """List all spaces with optional filter for project ID."""
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info("Listing spaces")
    try:
        params = {"pageSize": int(limit) if limit.strip() else 50}
        if project_id.strip():
            params["projectId"] = project_id

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/spaces",
                headers=get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'errors' in data:
                errors = data.get('errors', [])
                if errors:
                    err = errors[0] if isinstance(errors, list) else errors
                    return f"API Error: {err.get('errorMessage', str(err)) if isinstance(err, dict) else str(err)}"

            spaces = data.get('data', data.get('results', data)) if isinstance(data, dict) else data

            if not spaces or not isinstance(spaces, list):
                return "No spaces found"

            result = [f"Found {len(spaces)} space(s):\n"]
            for space in spaces:
                if isinstance(space, dict):
                    result.append(format_space(space))
                    result.append("")
            return '\n'.join(result)
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error listing spaces: {e}")
        return f"Error: {str(e)}"


# === TIME ENTRY TOOLS ===

@mcp.tool()
async def get_time_entry(time_entry_id: str = "") -> str:
    """Get a time entry by its unique ID from Rocketlane."""
    if not time_entry_id.strip():
        return "Error: time_entry_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Getting time entry {time_entry_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/time-entries/{time_entry_id}",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            entry = response.json()
            return f"Time entry retrieved:\n{format_time_entry(entry)}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error getting time entry: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def search_time_entries(user_id: str = "", project_id: str = "", date_from: str = "", date_to: str = "", limit: str = "50") -> str:
    """Search time entries with filters for user, project, and date range (YYYY-MM-DD format)."""
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info("Searching time entries")
    try:
        params = {"limit": int(limit) if limit.strip() else 50}
        if user_id.strip():
            params["userId.eq"] = user_id
        if project_id.strip():
            params["projectId.eq"] = project_id
        if date_from.strip():
            params["date.gte"] = date_from
        if date_to.strip():
            params["date.lte"] = date_to

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/time-entries/search",
                headers=get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'errors' in data:
                errors = data.get('errors', [])
                if errors:
                    err = errors[0] if isinstance(errors, list) else errors
                    return f"API Error: {err.get('errorMessage', str(err)) if isinstance(err, dict) else str(err)}"

            entries = data.get('data', data.get('results', data)) if isinstance(data, dict) else data

            if not entries or not isinstance(entries, list):
                return "No time entries found"

            result = [f"Found {len(entries)} time entry(ies):\n"]
            for entry in entries:
                if isinstance(entry, dict):
                    result.append(format_time_entry(entry))
                    result.append("")
            return '\n'.join(result)
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error searching time entries: {e}")
        return f"Error: {str(e)}"


# === TIME-OFF TOOLS ===

@mcp.tool()
async def create_time_off(user_email: str = "", start_date: str = "", end_date: str = "", reason: str = "") -> str:
    """Create a time-off request for a user with start/end dates (YYYY-MM-DD) and optional reason."""
    if not user_email.strip():
        return "Error: user_email is required"
    if not start_date.strip():
        return "Error: start_date is required (YYYY-MM-DD)"
    if not end_date.strip():
        return "Error: end_date is required (YYYY-MM-DD)"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Creating time-off for {user_email}")
    try:
        body = {
            "user": {"emailId": user_email},
            "startDate": start_date,
            "endDate": end_date
        }
        if reason.strip():
            body["reason"] = reason

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/time-offs",
                headers=get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            time_off = response.json()
            return f"Time-off created for {user_email} from {start_date} to {end_date}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error creating time-off: {e}")
        return f"Error: {str(e)}"


# === SPACE DOCUMENT TOOLS ===

@mcp.tool()
async def get_space_document(document_id: str = "") -> str:
    """Get a space document by its unique ID from Rocketlane."""
    if not document_id.strip():
        return "Error: document_id is required"
    if not API_KEY:
        return "Error: ROCKETLANE_API_KEY not configured"

    logger.info(f"Getting space document {document_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/space-documents/{document_id}",
                headers=get_headers(),
                timeout=30
            )
            response.raise_for_status()
            doc = response.json()
            lines = [f"Space Document: {doc.get('documentName', 'N/A')}"]
            lines.append(f"  ID: {doc.get('spaceDocumentId', 'N/A')}")
            lines.append(f"  Space ID: {doc.get('spaceId', 'N/A')}")
            return '\n'.join(lines)
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Error getting space document: {e}")
        return f"Error: {str(e)}"


# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Rocketlane MCP server...")

    if not API_KEY:
        logger.warning("ROCKETLANE_API_KEY not set - API calls will fail")

    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
