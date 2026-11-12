"""Readable workbook exports."""

from __future__ import annotations

import re
from io import BytesIO

import pandas as pd


XML_ILLEGAL_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")


def build_excel_report(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Serialize named DataFrames into a valid XLSX workbook."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            sanitized = frame.copy()
            for column in sanitized.select_dtypes(include=["object", "string"]).columns:
                sanitized[column] = sanitized[column].map(_sanitize_excel_text)
            sanitized.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()


def _sanitize_excel_text(value: object) -> object:
    if not isinstance(value, str):
        return value
    return XML_ILLEGAL_CONTROL_CHARACTERS.sub("�", value)

