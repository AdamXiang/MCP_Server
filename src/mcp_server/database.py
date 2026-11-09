"""Store tasks in a local SQLite database.

This module is the only place in the project that contains SQL. The MCP server
in ``server.py`` calls these functions and does not know how tasks are stored.

Each function opens its own connection and closes that connection before it
returns. A SQLite connection is cheap to open, and this pattern means that no
connection stays open between tool calls.

Each task is a plain ``dict`` with these string keys:

- ``task_id``: the unique ID of the task.
- ``title``: the short name of the task.
- ``description``: the details of the task. This value can be an empty string.
- ``priority``: the importance of the task, such as ``"medium"``.
- ``status``: the progress of the task, such as ``"in progress"``.

Run this module once to create the database and one sample task::

    uv run python -m mcp_server.database
"""

import sqlite3
from pathlib import Path

# __file__ is src/mcp_server/database.py, so parents[0] is src/mcp_server,
# parents[1] is src, and parents[2] is the project root. Building the path from
# __file__ gives the same database from any working directory.
project_root = Path(__file__).resolve().parents[2]

data_dir = project_root / "data"

database_path = data_dir / "tasks.db"


def init_database() -> None:
    """Create the ``data`` directory and the ``tasks`` table if they are missing.

    You can call this function many times. ``exist_ok=True`` and
    ``CREATE TABLE IF NOT EXISTS`` make a repeated call do nothing, and existing
    tasks stay in the table.

    The server does not call this function when it starts. Call it, or run this
    module, before the first tool call.
    """
    data_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(database_path)

    cursor = conn.cursor()

    # try/finally closes the connection even if the SQL statement fails.
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks(
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'todo'
            )

        """)

        # SQLite keeps changes in a transaction until commit() saves them.
        conn.commit()

    finally:
        conn.close()


def save_task(task: dict) -> None:
    """Insert one new task into the database.

    Args:
        task: The task to insert. It must contain all the keys that the module
            docstring lists.

    Raises:
        KeyError: A required key is missing from ``task``.
        sqlite3.IntegrityError: A task with the same ``task_id`` already exists.
        sqlite3.OperationalError: The database or the ``tasks`` table does not
            exist. Call ``init_database`` first.
    """

    conn = sqlite3.connect(database_path)

    cursor = conn.cursor()

    try:
        # Each ? is a placeholder that SQLite fills with a value from the tuple.
        # Never build SQL with an f-string: placeholders stop text from a user
        # or an LLM from running as SQL (SQL injection).
        cursor.execute(
            """
            INSERT INTO tasks(
                task_id, title, description, priority, status
            )
            VALUES(?, ?, ?, ?, ?)
        """,
            (
                task["task_id"],
                task["title"],
                task["description"],
                task["priority"],
                task["status"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def update_task_status_in_db(task_id: str, status: str) -> dict:
    """Change the status of one task and return the updated task.

    Args:
        task_id: The ID of the task to update.
        status: The new status. This function does not validate the value. The
            MCP tool in ``server.py`` limits the values that callers can send.

    Returns:
        The updated task. If no task has this ID, the function returns
        ``{"error": "The task_id <id> doesn't exist"}`` and does not raise an
        exception. The MCP caller receives this dict as a normal tool result,
        so check for the ``"error"`` key.

    Raises:
        sqlite3.OperationalError: The database or the ``tasks`` table does not
            exist. Call ``init_database`` first.
    """
    conn = sqlite3.connect(database_path)
    # sqlite3.Row lets the code read a column by name and convert a row to a
    # dict. The default row type is a plain tuple, which has no column names.
    conn.row_factory = sqlite3.Row

    # A cursor copies row_factory when it is created, so create the cursor after
    # you set row_factory.
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE tasks
            SET status = ?
            WHERE task_id = ?
        """,
            (status, task_id),
        )
        conn.commit()

        # UPDATE does not return the row, so read the row back. If the ID does
        # not exist, UPDATE changes zero rows and fetchone() returns None.
        record = cursor.execute(
            """
                SELECT *
                FROM tasks
                WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
    finally:
        conn.close()

    if record is None:
        return {"error": f"The task_id {task_id} doesn't exist"}

    return dict(record)  # Convert into standard dictionary


def get_all_tasks() -> list[dict]:
    """Return every task in the database.

    Returns:
        A list with one dict for each task. The list is empty if the table has
        no tasks.

    Raises:
        sqlite3.OperationalError: The database or the ``tasks`` table does not
            exist. Call ``init_database`` first.
    """
    conn = sqlite3.connect(database_path)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM tasks;
        """)

        rows = cursor.fetchall()
    finally:
        conn.close()

    # sqlite3.Row objects cannot be sent as JSON, but plain dicts can. MCP sends
    # tool results as JSON.
    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_database()

    # This fixed ID is the task that update_task_status_from_mcp() in client.py
    # updates. Because task_id is the primary key, a second run of this module
    # fails with sqlite3.IntegrityError. The table and its tasks stay unchanged.
    save_task(
        {
            "task_id": "1",
            "title": "new task",
            "description": "test",
            "priority": "low",
            "status": "todo",
        }
    )

    print(get_all_tasks())
