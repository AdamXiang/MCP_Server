"""A task manager that AI agents can use through the Model Context Protocol (MCP).

MCP is an open standard that lets an AI application discover and call tools
that another program provides. This package has three layers:

- ``database``: reads and writes tasks in a SQLite file.
- ``server``: publishes the database operations as MCP tools.
- ``client`` and ``langchain_client``: two programs that call the MCP tools.
  ``client`` calls them from fixed Python code. ``langchain_client`` lets a
  Claude model decide which tool to call.

A request always moves in one direction::

    client or agent --(MCP over HTTP)--> server --> database --> data/tasks.db

Start reading with ``database.py``, then ``server.py``, then ``client.py``, and
finish with ``langchain_client.py``. The README has the setup steps.
"""


def main() -> None:
    """Print a greeting. This is the target of the ``mcp-server`` command.

    This function is a placeholder from the project template. It does not start
    the MCP server. To start the server, run
    ``uv run python -m mcp_server.server``.
    """
    print("Hello from mcp-server!")
