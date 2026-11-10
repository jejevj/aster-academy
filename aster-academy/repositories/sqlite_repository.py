"""SQLite connection repository; schema ownership remains with schema modules."""
import sqlite3
from pathlib import Path


class SQLiteRepository:
    def __init__(self, path: Path, timeout_seconds: int = 15):
        self.path = Path(path)
        self.timeout_seconds = timeout_seconds

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout_seconds)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection
