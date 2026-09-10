"""
SQLite Database Connection Manager for JARVIS Memory Subsystem.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional
from jarvis.memory.errors import DatabaseError


class DatabaseManager:
    """Manages thread-safe SQLite connection and execution pragmas."""

    DEFAULT_DB_PATH = Path("data/database/memory.db")

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self._shared_conn: Optional[sqlite3.Connection] = None
        self._ensure_db_dir()

    def _ensure_db_dir(self) -> None:
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        try:
            if str(self.db_path) == ":memory:":
                if self._shared_conn is None:
                    conn = sqlite3.connect(":memory:", timeout=10.0, check_same_thread=False)
                    conn.row_factory = sqlite3.Row
                    conn.execute("PRAGMA foreign_keys=ON;")
                    self._shared_conn = conn
                return self._shared_conn

            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            return conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to SQLite database at {self.db_path}: {e}")

    def execute_script(self, sql_script: str) -> None:
        with self.get_connection() as conn:
            try:
                conn.executescript(sql_script)
                conn.commit()
            except sqlite3.Error as e:
                raise DatabaseError(f"Failed to execute SQL script: {e}")
