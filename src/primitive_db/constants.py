"""Общие константы файловой базы данных."""

from pathlib import Path

METADATA_FILE = "db_meta.json"
DATA_DIR = Path("data")

NAME_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"

ALLOWED_TYPES = {
    "int": int,
    "str": str,
    "bool": bool,
}

VALUE_TYPES = tuple(ALLOWED_TYPES.values())
