"""
Tests for supply chain visualizations.
"""
import pytest
import os
import sys
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, os.path.abspath("."))
from scripts.data_generator import (
    generate_products, generate_demand_history,
    generate_purchase_orders, generate_supplier_performance
)
from scripts.visualizations import (
    plot_stock_status, plot_abc_classification,
    plot_demand_forecast, plot_inventory_by_category,
    plot_supplier_performance, plot_lead_time_distribution,
    plot_eoq_vs_current_stock, plot_monthly_order_spend
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


class TestVisualizations:

    def test_stock_status_chart_created(self, products):
        path = plot_stock_status(products)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_abc_classification_chart_created(self, products):
        path = plot_abc_classification(products)
        assert os.path.exists(path)

    def test_demand_forecast_chart_created(self, demand):
        product_id = demand["product_id"].iloc[0]
        path = plot_demand_forecast(demand, product_id)
        assert os.path.exists(path)

    def test_inventory_by_category_chart_created(self, products):
        path = plot_inventory_by_category(products)
        assert os.path.exists(path)

    def test_supplier_performance_chart_created(self, suppliers):
        path = plot_supplier_performance(suppliers)
        assert os.path.exists(path)

    def test_lead_time_distribution_chart_created(self, orders):
        path = plot_lead_time_distribution(orders)
        assert os.path.exists(path)

    def test_eoq_vs_stock_chart_created(self, products):
        path = plot_eoq_vs_current_stock(products)
        assert os.path.exists(path)

    def test_monthly_spend_chart_created(self, orders):
        path = plot_monthly_order_spend(orders)
        assert os.path.exists(path)

    def test_all_charts_are_png(self):
        charts = [f for f in os.listdir("visuals") if f.endswith(".png")]
        assert len(charts) >= 8

    def test_all_charts_non_empty(self):
        for f in os.listdir("visuals"):
            if f.endswith(".png"):
                assert os.path.getsize(f"visuals/{f}") > 0
