from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_app_starts_with_verified_public_dataset():
    """Catches startup failures in the default real-data path."""
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=30).run()

    assert not app.exception
    assert app.title[0].value == "药采智析"


def test_forecast_pages_expose_manual_selection_and_bad_case_analysis():
    """Catches the forecast decision trail disappearing from the product UI."""
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=30).run()

    assert "BadCase分析" in app.sidebar.radio[0].options
    assert "智能问数" in app.sidebar.radio[0].options

    app.sidebar.radio[0].set_value("需求回测").run()
    assert not app.exception
    assert any(item.label == "人工选择策略" for item in app.selectbox)
    assert any(
        item.label == "下载策略决策记录（JSON）" for item in app.download_button
    )

    app.sidebar.radio[0].set_value("BadCase分析").run()
    assert not app.exception
    assert app.header[0].value == "BadCase分析"

    app.sidebar.radio[0].set_value("智能问数").run()
    assert not app.exception
    assert app.header[0].value == "智能问数"

