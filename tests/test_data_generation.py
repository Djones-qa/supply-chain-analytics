"""
Tests for supply chain data generation.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.abspath("."))
from scripts.data_generator import (
    generate_products, generate_demand_history,
    generate_purchase_orders, generate_supplier_performance,
    save_to_sqlite, save_to_csv, SUPPLIERS, CATEGORIES
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


class TestProductGeneration:

    def test_correct_product_count(self, products):
        assert len(products) == 300

    def test_product_ids_unique(self, products):
        assert products["product_id"].nunique() == 300

    def test_unit_cost_positive(self, products):
        assert (products["unit_cost"] > 0).all()

    def test_selling_price_above_cost(self, products):
        assert (products["selling_price"] > products["unit_cost"]).all()

    def test_lead_time_positive(self, products):
        assert (products["lead_time_days"] >= 3).all()

    def test_eoq_positive(self, products):
        assert (products["eoq"] > 0).all()

    def test_safety_stock_non_negative(self, products):
        assert (products["safety_stock"] >= 0).all()

    def test_reorder_point_positive(self, products):
        assert (products["reorder_point"] > 0).all()

    def test_abc_class_valid(self, products):
        valid = {"A", "B", "C"}
        assert set(products["abc_class"].unique()).issubset(valid)

    def test_category_values_valid(self, products):
        assert set(products["category"].unique()).issubset(set(CATEGORIES))

    def test_supplier_values_valid(self, products):
        assert set(products["supplier"].unique()).issubset(set(SUPPLIERS))

    def test_no_null_critical_fields(self, products):
        critical = ["product_id", "unit_cost", "eoq",
                    "reorder_point", "current_stock"]
        for col in critical:
            assert products[col].isnull().sum() == 0


class TestDemandHistory:

    def test_demand_generated(self, demand):
        assert len(demand) > 0

    def test_demand_non_negative(self, demand):
        assert (demand["demand"] >= 0).all()

    def test_month_within_range(self, demand):
        assert demand["month"].between(1, 12).all()

    def test_day_of_week_within_range(self, demand):
        assert demand["day_of_week"].between(0, 6).all()

    def test_is_weekend_is_boolean(self, demand):
        assert demand["is_weekend"].dtype == bool


class TestPurchaseOrders:

    def test_correct_order_count(self, orders):
        assert len(orders) == 500

    def test_order_ids_unique(self, orders):
        assert orders["po_id"].nunique() == 500

    def test_quantity_positive(self, orders):
        assert (orders["quantity_ordered"] > 0).all()

    def test_total_cost_positive(self, orders):
        assert (orders["total_cost"] > 0).all()

    def test_on_time_is_boolean(self, orders):
        assert orders["on_time"].dtype == bool

    def test_status_values_valid(self, orders):
        valid = {"Delivered", "Pending", "In Transit", "Cancelled"}
        assert set(orders["status"].unique()).issubset(valid)

    def test_lead_time_variance_calculated(self, orders):
        assert "lead_time_variance" in orders.columns


class TestSupplierPerformance:

    def test_all_suppliers_present(self, suppliers):
        assert len(suppliers) == len(SUPPLIERS)

    def test_on_time_pct_within_range(self, suppliers):
        assert suppliers["on_time_delivery_pct"].between(0, 100).all()

    def test_quality_rating_within_range(self, suppliers):
        assert suppliers["quality_rating"].between(1, 5).all()

    def test_defect_rate_positive(self, suppliers):
        assert (suppliers["defect_rate_pct"] >= 0).all()


class TestDataPersistence:

    def test_save_to_csv(self, products, demand, orders, suppliers):
        save_to_csv(products, demand, orders, suppliers)
        assert os.path.exists("data/products.csv")
        assert os.path.exists("data/demand_history.csv")
        assert os.path.exists("data/purchase_orders.csv")
        assert os.path.exists("data/supplier_performance.csv")

    def test_save_to_sqlite(self, products, demand, orders, suppliers):
        path = save_to_sqlite(products, demand, orders, suppliers)
        assert os.path.exists(path)
