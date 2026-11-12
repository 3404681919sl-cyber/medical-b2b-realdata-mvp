from io import BytesIO

import pandas as pd

from src.exports import build_excel_report


def test_build_excel_report_round_trips_named_sheets():
    """Catches an export that downloads but cannot be opened as a valid workbook."""
    payload = build_excel_report(
        {
            "analysis": pd.DataFrame({"sku_id": ["A"], "revenue": [12.5]}),
            "quality": pd.DataFrame({"issue": ["duplicate"], "count": [2]}),
        }
    )

    workbook = pd.ExcelFile(BytesIO(payload))
    analysis = pd.read_excel(workbook, sheet_name="analysis")

    assert workbook.sheet_names == ["analysis", "quality"]
    assert analysis.iloc[0].to_dict() == {"sku_id": "A", "revenue": 12.5}


def test_build_excel_report_replaces_xml_illegal_control_characters():
    """Catches real source text making the entire evidence export unreadable."""
    payload = build_excel_report(
        {"products": pd.DataFrame({"product_name": ["\x1aoladex 10"]})}
    )

    products = pd.read_excel(BytesIO(payload), sheet_name="products")

    assert products.iloc[0]["product_name"] == "�oladex 10"

