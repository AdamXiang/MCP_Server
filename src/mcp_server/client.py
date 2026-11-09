"""Call the MCP server from fixed Python code, with no LLM.

Use this script to check that the server works before you add an LLM agent. It
prints the tool names and then creates, updates, and lists tasks.

Start the server in another terminal, and then run::

    uv run python -m mcp_server.client

Each run adds one task with the title ``task_test``. The update step needs the
sample task with the ID ``"1"``, which ``database.py`` creates.

The MCP calls use ``async`` and ``await`` because they wait for network
responses. An ``async def`` function does not run until an event loop runs it,
which is what ``asyncio.run()`` does at the bottom of this file.
"""

import asyncio

from fastmcp import Client

# Creating the Client does not connect to the server. The connection opens when
# the code enters "async with client" and closes when the code leaves that block.
client = Client("http://127.0.0.1:8000/mcp")


async def get_tools_from_server():
    """Ask the server which tools it has, and print each tool name.

    Returns:
        The list of tool definitions from the server. Each definition has a
        name, a description, and an argument schema.
    """
    async with client:
        tools = await client.list_tools()

        for tool in tools:
            print(tool.name)

    return tools


async def create_task_using_mcp():
    """Call the ``create_task`` tool with fixed test values.

    Returns:
        The new task that the server returned.
    """
    async with client:
        # The second argument holds the tool arguments, by name. The server
        # validates them against the tool's schema.
        result = await client.call_tool(
            "create_task",
            {
                "title": "task_test",
                "priority": "high",
                "description": "test again from client",
            },
        )

        # result.data is the tool's return value as a Python object.
        print(result.data)

    return result.data


async def update_task_status_from_mcp():
    """Set the sample task with the ID ``"1"`` to ``"in progress"``.

    Returns:
        The updated task, or a dict with an ``"error"`` key if the task does not
        exist.
    """
    async with client:
        result = await client.call_tool(
            "update_task_status", {"task_id": "1", "status": "in progress"}
        )

        print(result.data)

    return result.data


async def list_tasks_using_mcp():
    """Call the ``list_tasks`` tool and print the result.

    Returns:
        A list with one dict for each task.
    """
    async with client:
        result = await client.call_tool("list_tasks")

        print(result.data)

    return result.data


if __name__ == "__main__":
    # The steps run in order, and the list calls between them show how each
    # change affects the database.
    asyncio.run(get_tools_from_server())
    asyncio.run(list_tasks_using_mcp())
    asyncio.run(create_task_using_mcp())
    asyncio.run(list_tasks_using_mcp())
    asyncio.run(update_task_status_from_mcp())
    asyncio.run(list_tasks_using_mcp())
