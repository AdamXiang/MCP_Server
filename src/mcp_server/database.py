import sqlite3
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]

data_dir = project_root / "data"

database_path = data_dir / "tasks.db"


def init_database() -> None:
    data_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(database_path)

    cursor = conn.cursor()

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

        conn.commit()

    finally:
        conn.close()


def save_task(task: dict) -> None:

    conn = sqlite3.connect(database_path)

    cursor = conn.cursor()

    try:
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
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row

    # After row_factory, it must be recreate cursor to effect
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

    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_database()

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
