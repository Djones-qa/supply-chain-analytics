"""
Tests for supply chain analytics calculations.
"""
import pytest
import pandas as pd
import sys, os
sys.path.insert(0, os.path.abspath("."))
from scripts.data_generator import (
    generate_products, generate_demand_history,
    generate_purchase_orders, generate_supplier_performance,
    save_to_sqlite
)
from scripts.analytics import (
    classify_abc, detect_stockouts, forecast_demand,
    calculate_inventory_metrics, analyze_supplier_performance,
    calculate_order_cycle_metrics, run_sql_queries
)


@pytest.fixture(scope="module")
def products():
    return generate_products(300)


@pytest.fixture(scope="module")
def demand(products):
    return generate_demand_history(products, days=365)


@pytest.fixture(scope="module")
def orders(products):
    return generate_purchase_orders(products, 500)


@pytest.fixture(scope="module")
def suppliers(products):
    return generate_supplier_performance(products)


@pytest.fixture(scope="module")
def db(products, demand, orders, suppliers):
    save_to_sqlite(products, demand, orders, suppliers)
    return "data/supply_chain.db"


class TestABCClassification:

    def test_returns_dataframe(self, products):
        result = classify_abc(products)
        assert isinstance(result, pd.DataFrame)

    def test_has_abc_column(self, products):
        result = classify_abc(products)
        assert "calculated_abc" in result.columns

    def test_abc_values_valid(self, products):
        result = classify_abc(products)
        valid = {"A", "B", "C"}
        assert set(result["calculated_abc"].unique()).issubset(valid)

    def test_has_annual_value(self, products):
        result = classify_abc(products)
        assert "annual_value" in result.columns
        assert (result["annual_value"] > 0).all()

    def test_sorted_by_value_descending(self, products):
        result = classify_abc(products)
        values = result["annual_value"].tolist()
        assert values == sorted(values, reverse=True)


class TestStockoutDetection:

    def test_returns_dataframe(self, products):
        result = detect_stockouts(products)
        assert isinstance(result, pd.DataFrame)

    def test_has_stock_status(self, products):
        result = detect_stockouts(products)
        assert "stock_status" in result.columns

    def test_status_values_valid(self, products):
        result = detect_stockouts(products)
        valid = {"Stockout Risk", "Overstock", "Optimal"}
        assert set(result["stock_status"].unique()).issubset(valid)

    def test_days_of_stock_positive(self, products):
        result = detect_stockouts(products)
        assert (result["days_of_stock"] >= 0).all()

    def test_stockout_flag_correct(self, products):
        result = detect_stockouts(products)
        stockout = result[result["stockout_risk"] == True]
        assert (stockout["current_stock"] <=
                stockout["reorder_point"]).all()


class TestDemandForecast:

    def test_returns_dataframe(self, demand, products):
        product_id = products["product_id"].iloc[0]
        if product_id in demand["product_id"].values:
            result = forecast_demand(demand, product_id)
            assert isinstance(result, pd.DataFrame)

    def test_has_moving_average(self, demand, products):
        pid = demand["product_id"].iloc[0]
        result = forecast_demand(demand, pid)
        assert "ma_7" in result.columns
        assert "ma_30" in result.columns


class TestInventoryMetrics:

    def test_returns_dict(self, products):
        result = calculate_inventory_metrics(products)
        assert isinstance(result, dict)

    def test_has_required_keys(self, products):
        result = calculate_inventory_metrics(products)
        required = ["total_inventory_value", "total_skus",
                    "stockout_risk_count", "overstock_count",
                    "avg_days_of_stock"]
        for key in required:
            assert key in result

    def test_total_skus_correct(self, products):
        result = calculate_inventory_metrics(products)
        assert result["total_skus"] == len(products)

    def test_inventory_value_positive(self, products):
        result = calculate_inventory_metrics(products)
        assert result["total_inventory_value"] > 0

    def test_stockout_pct_within_range(self, products):
        result = calculate_inventory_metrics(products)
        assert 0 <= result["stockout_risk_pct"] <= 100


class TestSupplierAnalysis:

    def test_returns_dataframe(self, suppliers):
        result = analyze_supplier_performance(suppliers)
        assert isinstance(result, pd.DataFrame)

    def test_has_performance_score(self, suppliers):
        result = analyze_supplier_performance(suppliers)
        assert "performance_score" in result.columns

    def test_score_within_range(self, suppliers):
        result = analyze_supplier_performance(suppliers)
        assert result["performance_score"].between(0, 1).all()

    def test_tier_values_valid(self, suppliers):
        result = analyze_supplier_performance(suppliers)
        valid = {"Tier 1", "Tier 2", "Tier 3"}
        actual = set(result["supplier_tier"].dropna().astype(str).unique())
        assert actual.issubset(valid)

    def test_sorted_by_score_descending(self, suppliers):
        result = analyze_supplier_performance(suppliers)
        scores = result["performance_score"].tolist()
        assert scores == sorted(scores, reverse=True)


class TestOrderCycleMetrics:

    def test_returns_dict(self, orders):
        result = calculate_order_cycle_metrics(orders)
        assert isinstance(result, dict)

    def test_on_time_rate_within_range(self, orders):
        result = calculate_order_cycle_metrics(orders)
        assert 0 <= result["on_time_delivery_rate"] <= 100

    def test_total_spend_positive(self, orders):
        result = calculate_order_cycle_metrics(orders)
        assert result["total_spend"] > 0


class TestSQLQueries:

    def test_all_queries_return_results(self, db):
        results = run_sql_queries(db)
        expected = ["stockout_risk_products", "inventory_by_category",
                    "supplier_spend", "overstock_products",
                    "abc_summary", "late_deliveries"]
        for key in expected:
            assert key in results

    def test_abc_summary_has_3_classes(self, db):
        results = run_sql_queries(db)
        assert len(results["abc_summary"]) == 3

    def test_inventory_by_category_has_all_cats(self, db):
        results = run_sql_queries(db)
        assert len(results["inventory_by_category"]) == 10
