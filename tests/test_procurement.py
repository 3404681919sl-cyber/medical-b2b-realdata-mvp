import pandas as pd
import pytest

from src.procurement import calculate_procurement_plan


def test_procurement_plan_uses_stock_transit_safety_and_minimum_order():
    """Catches recommendations that ignore stock position or minimum order size."""
    inputs = pd.DataFrame(
        {
            "sku_id": ["A", "B"],
            "forecast_demand": [20.0, 10.0],
            "safety_stock_units": [5.0, 2.0],
            "current_stock": [8.0, 20.0],
            "in_transit": [2.0, 0.0],
            "minimum_order_qty": [10.0, 5.0],
            "unit_cost": [3.0, 4.0],
        }
    )

    result = calculate_procurement_plan(inputs).set_index("sku_id")

    assert result.loc["A", "raw_reorder_qty"] == 15.0
    assert result.loc["A", "recommended_order_qty"] == 20.0
    assert result.loc["A", "recommended_order_cost"] == 60.0
    assert result.loc["B", "recommended_order_qty"] == 0.0


def test_procurement_plan_rejects_missing_real_inventory_input():
    """Catches the product fabricating a recommendation when stock is unknown."""
    incomplete = pd.DataFrame(
        {
            "sku_id": ["A"],
            "forecast_demand": [20.0],
            "safety_stock_units": [5.0],
            "in_transit": [2.0],
            "minimum_order_qty": [10.0],
            "unit_cost": [3.0],
        }
    )

    with pytest.raises(ValueError, match="current_stock"):
        calculate_procurement_plan(incomplete)

