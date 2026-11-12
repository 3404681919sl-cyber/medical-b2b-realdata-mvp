"""Streaming helpers for the published MariaDB dump."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator


def parse_values_line(line: str) -> list[str | None]:
    """Parse one single-line SQL VALUES tuple without splitting quoted commas."""
    text = line.strip().rstrip(",;")
    if not (text.startswith("(") and text.endswith(")")):
        raise ValueError("Expected one parenthesized SQL values row")
    values = next(
        csv.reader(
            [text[1:-1]],
            delimiter=",",
            quotechar="'",
            escapechar="\\",
            doublequote=True,
            skipinitialspace=True,
        )
    )
    return [None if value.strip().upper() == "NULL" else value.strip() for value in values]


def iter_table_rows(
    lines: Iterable[str], table_name: str
) -> Iterator[list[str | None]]:
    """Yield parsed rows from every INSERT block for one table."""
    insert_prefix = f"INSERT INTO `{table_name}` "
    active = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("INSERT INTO `"):
            active = stripped.startswith(insert_prefix)
            continue
        if not active or not stripped.startswith("("):
            continue
        yield parse_values_line(stripped)
        if stripped.endswith(";"):
            active = False

