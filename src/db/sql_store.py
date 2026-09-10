import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = "data/database/enterprise.db"
SCHEMA_PATH = "data/database/schema.sql"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(conn: sqlite3.Connection, schema_path: str = SCHEMA_PATH) -> None:
    schema_sql = Path(schema_path).read_text()
    conn.executescript(schema_sql)
    conn.commit()


def run_query(conn: sqlite3.Connection, query: str) -> list[dict]:
    cursor = conn.execute(query)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
