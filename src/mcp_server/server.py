from typing import Literal
from uuid import uuid4

from fastmcp import FastMCP

from mcp_server.database import get_all_tasks, save_task, update_task_status_in_db

mcp = FastMCP("MCP Server ACL")


@mcp.tool(name="create_task", description="This tool is created to create new tasks")
def create_task(title: str, priority: str = "medium", description: str = "") -> dict:
    """
    This function creates new tasks in our database
    """

    task_id = str(uuid4())

    status = "to do"

    task = {
        "task_id": task_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": status,
    }

    save_task(task)

    return task


@mcp.tool(
    name="list_tasks",
    description="This tool provides all the list of tasks in our database",
)
def list_tasks() -> list[dict]:
    """
    This function returns all the tasks in our database
    """
    return get_all_tasks()


@mcp.tool(
    name="update_task_status",
    description="This tool will update a task status based on its ID",
)
def update_task_status(
    task_id: str, status: Literal["todo", "in progress", "done"]
) -> dict:
    """
    This function will update the status of a specific task based on its ID
    """
    return update_task_status_in_db(task_id=task_id, status=status)


if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
    create_task(title="second task", description="test again")
