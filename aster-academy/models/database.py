"""Database configuration model shared by the application repositories."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatabaseSettings:
    path: Path
    timeout_seconds: int = 15


def default_settings(base_dir: Path) -> DatabaseSettings:
    return DatabaseSettings(path=base_dir / "aster.sqlite3")
