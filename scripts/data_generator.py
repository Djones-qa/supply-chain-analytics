"""
Generates realistic supply chain data for
inventory optimization and demand forecasting.
"""
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import sqlite3
import os

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

CATEGORIES = [
    "Electronics", "Clothing", "Food & Beverage", "Home & Garden",
    "Automotive", "Health & Beauty", "Sports", "Industrial", "Books", "Toys"
]

SUPPLIERS = [
    "Global Supply Co", "FastShip Industries", "Prime Logistics",
    "MegaSource Ltd", "QuickDeliver Inc", "Reliable Parts Co",
    "EcoSupply Group", "TechParts Global", "ValueChain Corp", "SwiftGoods"
]

WAREHOUSES = ["East DC", "West DC", "Central Hub", "South Depot", "North Facility"]

STATUS = ["Active", "Discontinued", "Seasonal", "Backorder"]


def generate_products(num_products: int = 300) -> pd.DataFrame:
    """Generate product catalog with supply chain attributes."""
    records = []
    for i in range(1, num_products + 1):
        category = random.choice(CATEGORIES)
        unit_cost = round(random.uniform(5, 500), 2)
        selling_price = round(unit_cost * random.uniform(1.3, 2.5), 2)
        lead_time = random.randint(3, 45)
        daily_demand = round(random.uniform(1, 50), 1)
        holding_cost_pct = round(random.uniform(0.15, 0.30), 2)
        ordering_cost = round(random.uniform(20, 200), 2)

        # EOQ calculation
        annual_demand = daily_demand * 365
        holding_cost = unit_cost * holding_cost_pct
        eoq = round(np.sqrt((2 * annual_demand * ordering_cost) / holding_cost), 0)

        # Safety stock and reorder point
        demand_std = round(daily_demand * 0.2, 1)
        safety_stock = round(1.65 * demand_std * np.sqrt(lead_time), 0)
        reorder_point = round(daily_demand * lead_time + safety_stock, 0)

        records.append({
            "product_id": f"SKU{i:05d}",
            "product_name": fake.catch_phrase(),
            "category": category,
            "supplier": random.choice(SUPPLIERS),
            "warehouse": random.choice(WAREHOUSES),
            "unit_cost": unit_cost,
            "selling_price": selling_price,
            "lead_time_days": lead_time,
            "daily_demand": daily_demand,
            "demand_std": demand_std,
            "holding_cost_pct": holding_cost_pct,
            "ordering_cost": ordering_cost,
            "eoq": int(eoq),
            "safety_stock": int(safety_stock),
            "reorder_point": int(reorder_point),
            "current_stock": random.randint(0, int(eoq * 2)),
            "status": random.choice(STATUS),
            "abc_class": random.choice(["A", "B", "C"]),
        })
    return pd.DataFrame(records)


def generate_demand_history(products_df: pd.DataFrame,
                             days: int = 365) -> pd.DataFrame:
    """Generate daily demand history for each product."""
    records = []
    base_date = datetime(2024, 1, 1)

    for _, product in products_df.sample(100).iterrows():
        base_demand = product["daily_demand"]
        for day in range(days):
            date = base_date + timedelta(days=day)
            day_of_week = date.weekday()
            month = date.month

            # Seasonality and day-of-week effects
            seasonal_factor = 1.0
            if month in [11, 12]:
                seasonal_factor = 1.4
            elif month in [6, 7]:
                seasonal_factor = 1.2
            elif month in [1, 2]:
                seasonal_factor = 0.8

            dow_factor = 1.2 if day_of_week < 5 else 0.7

            demand = max(0, round(
                np.random.normal(
                    base_demand * seasonal_factor * dow_factor,
                    product["demand_std"]
                ), 0
            ))

            records.append({
                "product_id": product["product_id"],
                "date": date.strftime("%Y-%m-%d"),
                "demand": int(demand),
                "day_of_week": day_of_week,
                "month": month,
                "is_weekend": day_of_week >= 5,
                "is_holiday_season": month in [11, 12],
            })
    return pd.DataFrame(records)


def generate_purchase_orders(products_df: pd.DataFrame,
                              num_orders: int = 500) -> pd.DataFrame:
    """Generate purchase order history."""
    records = []
    base_date = datetime(2024, 1, 1)

    for i in range(1, num_orders + 1):
        product = products_df.sample(1).iloc[0]
        order_date = base_date + timedelta(days=random.randint(0, 300))
        lead_time_days = int(product["lead_time_days"])
        lead_time = lead_time_days + random.randint(-3, 7)
        lead_time = max(1, lead_time)
        expected_delivery = order_date + timedelta(days=lead_time_days)
        actual_delivery = order_date + timedelta(days=lead_time)
        quantity = int(product["eoq"] * random.uniform(0.8, 1.5))
        unit_cost = product["unit_cost"] * random.uniform(0.95, 1.05)

        records.append({
            "po_id": f"PO{i:06d}",
            "product_id": product["product_id"],
            "supplier": product["supplier"],
            "order_date": order_date.strftime("%Y-%m-%d"),
            "expected_delivery": expected_delivery.strftime("%Y-%m-%d"),
            "actual_delivery": actual_delivery.strftime("%Y-%m-%d"),
            "quantity_ordered": quantity,
            "unit_cost": round(unit_cost, 2),
            "total_cost": round(quantity * unit_cost, 2),
            "lead_time_actual": lead_time,
            "lead_time_variance": lead_time - product["lead_time_days"],
            "on_time": actual_delivery <= expected_delivery,
            "status": random.choice(["Delivered", "Pending",
                                     "In Transit", "Cancelled"]),
        })
    return pd.DataFrame(records)


def generate_supplier_performance(products_df: pd.DataFrame) -> pd.DataFrame:
    """Generate supplier performance scorecard."""
    records = []
    for supplier in SUPPLIERS:
        supplier_products = products_df[products_df["supplier"] == supplier]
        records.append({
            "supplier": supplier,
            "total_products": len(supplier_products),
            "on_time_delivery_pct": round(random.uniform(75, 99), 1),
            "quality_rating": round(random.uniform(3, 5), 2),
            "avg_lead_time_days": round(random.uniform(5, 30), 1),
            "lead_time_variability": round(random.uniform(1, 8), 1),
            "defect_rate_pct": round(random.uniform(0.1, 5.0), 2),
            "avg_unit_cost": round(supplier_products["unit_cost"].mean(), 2) if len(supplier_products) > 0 else 0,
            "total_spend": round(random.uniform(50000, 500000), 2),
            "contract_compliance_pct": round(random.uniform(80, 100), 1),
        })
    return pd.DataFrame(records)


def save_to_sqlite(products_df, demand_df, orders_df, suppliers_df,
                   db_path="data/supply_chain.db"):
    """Save all datasets to SQLite."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    products_df.to_sql("products", conn, if_exists="replace", index=False)
    demand_df.to_sql("demand_history", conn, if_exists="replace", index=False)
    orders_df.to_sql("purchase_orders", conn, if_exists="replace", index=False)
    suppliers_df.to_sql("supplier_performance", conn,
                        if_exists="replace", index=False)
    conn.close()
    return db_path


def save_to_csv(products_df, demand_df, orders_df, suppliers_df):
    """Save all datasets to CSV."""
    os.makedirs("data", exist_ok=True)
    products_df.to_csv("data/products.csv", index=False)
    demand_df.to_csv("data/demand_history.csv", index=False)
    orders_df.to_csv("data/purchase_orders.csv", index=False)
    suppliers_df.to_csv("data/supplier_performance.csv", index=False)
    print("CSVs saved!")
