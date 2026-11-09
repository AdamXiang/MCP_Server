"""Publish the task database as MCP tools.

An MCP server tells its clients which tools exist, what each tool does, and which
arguments each tool takes. A client, which can be a script or an LLM agent, then
asks the server to run a tool. FastMCP handles the protocol. This file only
declares the tools.

Start the server from the project root::

    uv run python -m mcp_server.server

The server listens at ``http://127.0.0.1:8000/mcp`` until you press Ctrl+C.
"""

from typing import Literal
from uuid import uuid4

from fastmcp import FastMCP

from mcp_server.database import get_all_tasks, save_task, update_task_status_in_db

# This object holds the tool list and runs the server. MCP clients see the name
# "MCP Server ACL" when they connect.
mcp = FastMCP("MCP Server ACL")


# @mcp.tool registers the function as an MCP tool. FastMCP builds the tool's
# argument schema from the type hints and the default values. Clients and LLMs
# see the description= text, not the docstring, because description= takes
# priority. To change what an LLM reads, edit description=.
@mcp.tool(name="create_task", description="This tool is created to create new tasks")
def create_task(title: str, priority: str = "medium", description: str = "") -> dict:
    """Create a task with a generated ID and save it in the database.

    Args:
        title: The short name of the task.
        priority: The importance of the task. Any string is accepted because
            this argument has no ``Literal`` type.
        description: The details of the task.

    Returns:
        The saved task, including the generated ``task_id``.
    """

    # A UUID is random, so the server can create an ID without asking the
    # database. Convert it to str because the column type is TEXT.
    task_id = str(uuid4())

    # NOTE: This value is "to do" with a space. update_task_status accepts
    # "todo" without a space, and the database default is also "todo". A caller
    # cannot set a task back to the value that it started with.
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
    """Return every task in the database.

    Returns:
        A list with one dict for each task.
    """
    return get_all_tasks()


@mcp.tool(
    name="update_task_status",
    description="This tool will update a task status based on its ID",
)
def update_task_status(
    task_id: str, status: Literal["todo", "in progress", "done"]
) -> dict:
    """Change the status of one task.

    Args:
        task_id: The ID of the task to update.
        status: The new status. FastMCP turns the ``Literal`` type into a list
            of allowed values and rejects any other value before this function
            runs.

    Returns:
        The updated task, or a dict with an ``"error"`` key if the ID does not
        exist.
    """
    return update_task_status_in_db(task_id=task_id, status=status)


if __name__ == "__main__":
    # mcp.run() blocks: Python stays on this line while the server is running.
    # The "http" transport lets clients in other processes connect over the
    # network. The default path is /mcp.
    mcp.run(transport="http", port=8000)
    # NOTE: This line runs only after the server stops, so each Ctrl+C adds a
    # task with the title "second task" to the database. It looks like leftover
    # test code.
    create_task(title="second task", description="test again")
