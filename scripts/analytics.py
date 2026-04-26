"""
Supply chain analytics engine —
inventory optimization, demand forecasting, and supplier analysis.
"""
import pandas as pd
import numpy as np
import sqlite3


def classify_abc(products_df: pd.DataFrame) -> pd.DataFrame:
    """
    ABC inventory classification based on annual value.
    A = top 20% products = 80% of value
    B = next 30% products = 15% of value
    C = bottom 50% products = 5% of value
    """
    df = products_df.copy()
    df["annual_value"] = df["daily_demand"] * 365 * df["unit_cost"]
    df = df.sort_values("annual_value", ascending=False)
    df["cumulative_value"] = df["annual_value"].cumsum()
    total_value = df["annual_value"].sum()
    df["cumulative_pct"] = df["cumulative_value"] / total_value * 100

    def get_abc(pct):
        if pct <= 80:
            return "A"
        elif pct <= 95:
            return "B"
        else:
            return "C"

    df["calculated_abc"] = df["cumulative_pct"].apply(get_abc)
    return df


def detect_stockouts(products_df: pd.DataFrame) -> pd.DataFrame:
    """Detect products at risk of stockout."""
    df = products_df.copy()
    df["days_of_stock"] = (df["current_stock"] / df["daily_demand"]).round(1)
    df["stockout_risk"] = df["current_stock"] <= df["reorder_point"]
    df["overstock"] = df["current_stock"] > df["eoq"] * 2
    df["stock_status"] = df.apply(
        lambda r: "Stockout Risk" if r["stockout_risk"] else
                  "Overstock" if r["overstock"] else "Optimal", axis=1
    )
    return df[["product_id", "product_name", "category", "current_stock",
               "reorder_point", "eoq", "days_of_stock",
               "stockout_risk", "overstock", "stock_status"]].sort_values(
        "days_of_stock")


def forecast_demand(demand_df: pd.DataFrame,
                    product_id: str,
                    window: int = 7) -> pd.DataFrame:
    """Simple moving average demand forecast."""
    product_demand = demand_df[demand_df["product_id"] == product_id].copy()
    product_demand["date"] = pd.to_datetime(product_demand["date"])
    product_demand = product_demand.sort_values("date")
    product_demand[f"ma_{window}"] = product_demand["demand"].rolling(
        window=window).mean().round(2)
    product_demand["ma_30"] = product_demand["demand"].rolling(
        window=30).mean().round(2)
    product_demand["demand_trend"] = product_demand["demand"].diff().rolling(
        window=7).mean().round(2)
    return product_demand


def calculate_inventory_metrics(products_df: pd.DataFrame) -> dict:
    """Calculate key inventory KPIs."""
    total_inventory_value = (
        products_df["current_stock"] * products_df["unit_cost"]
    ).sum()
    stockout_count = (
        products_df["current_stock"] <= products_df["reorder_point"]
    ).sum()
    overstock_count = (
        products_df["current_stock"] > products_df["eoq"] * 2
    ).sum()
    avg_days_stock = (
        products_df["current_stock"] / products_df["daily_demand"]
    ).mean()

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "total_skus": len(products_df),
        "stockout_risk_count": int(stockout_count),
        "overstock_count": int(overstock_count),
        "optimal_count": int(
            len(products_df) - stockout_count - overstock_count),
        "avg_days_of_stock": round(avg_days_stock, 1),
        "stockout_risk_pct": round(stockout_count / len(products_df) * 100, 2),
        "overstock_pct": round(overstock_count / len(products_df) * 100, 2),
    }


def analyze_supplier_performance(suppliers_df: pd.DataFrame) -> pd.DataFrame:
    """Rank suppliers by composite performance score."""
    df = suppliers_df.copy()
    df["performance_score"] = (
        (df["on_time_delivery_pct"] / 100) * 0.35 +
        (df["quality_rating"] / 5) * 0.30 +
        (1 - df["defect_rate_pct"] / 5) * 0.20 +
        (df["contract_compliance_pct"] / 100) * 0.15
    ).round(3)
    df["supplier_tier"] = pd.cut(
        df["performance_score"],
        bins=[-0.01, 0.70, 0.85, 1.01],
        labels=["Tier 3", "Tier 2", "Tier 1"]
    )
    return df.sort_values("performance_score", ascending=False)


def calculate_order_cycle_metrics(orders_df: pd.DataFrame) -> dict:
    """Calculate purchase order performance metrics."""
    delivered = orders_df[orders_df["status"] == "Delivered"]
    on_time_rate = delivered["on_time"].mean() * 100
    avg_lead_time = delivered["lead_time_actual"].mean()
    avg_variance = delivered["lead_time_variance"].mean()
    total_spend = orders_df["total_cost"].sum()

    return {
        "total_orders": len(orders_df),
        "delivered_orders": len(delivered),
        "on_time_delivery_rate": round(on_time_rate, 2),
        "avg_actual_lead_time": round(avg_lead_time, 1),
        "avg_lead_time_variance": round(avg_variance, 1),
        "total_spend": round(total_spend, 2),
        "avg_order_value": round(orders_df["total_cost"].mean(), 2),
    }


def run_sql_queries(db_path: str = "data/supply_chain.db") -> dict:
    """Run supply chain SQL investigation queries."""
    conn = sqlite3.connect(db_path)
    queries = {
        "stockout_risk_products": """
            SELECT product_id, category, supplier,
                   current_stock, reorder_point, daily_demand,
                   ROUND(CAST(current_stock AS FLOAT) / daily_demand, 1)
                   as days_of_stock
            FROM products
            WHERE current_stock <= reorder_point
            ORDER BY days_of_stock ASC
            LIMIT 15
        """,
        "inventory_by_category": """
            SELECT category,
                   COUNT(*) as sku_count,
                   ROUND(SUM(current_stock * unit_cost), 2) as inventory_value,
                   ROUND(AVG(daily_demand), 2) as avg_daily_demand,
                   ROUND(AVG(lead_time_days), 1) as avg_lead_time
            FROM products
            GROUP BY category
            ORDER BY inventory_value DESC
        """,
        "supplier_spend": """
            SELECT supplier,
                   COUNT(*) as orders,
                   ROUND(SUM(total_cost), 2) as total_spend,
                   ROUND(AVG(total_cost), 2) as avg_order_value,
                   ROUND(100.0 * SUM(on_time) / COUNT(*), 2) as on_time_pct
            FROM purchase_orders
            WHERE status = 'Delivered'
            GROUP BY supplier
            ORDER BY total_spend DESC
        """,
        "overstock_products": """
            SELECT product_id, category, warehouse,
                   current_stock, eoq,
                   ROUND(current_stock - (eoq * 2), 0) as excess_units,
                   ROUND((current_stock - eoq * 2) * unit_cost, 2)
                   as excess_value
            FROM products
            WHERE current_stock > eoq * 2
            ORDER BY excess_value DESC
            LIMIT 15
        """,
        "abc_summary": """
            SELECT abc_class,
                   COUNT(*) as sku_count,
                   ROUND(SUM(current_stock * unit_cost), 2) as inventory_value,
                   ROUND(AVG(daily_demand), 2) as avg_demand,
                   ROUND(AVG(lead_time_days), 1) as avg_lead_time
            FROM products
            GROUP BY abc_class
            ORDER BY abc_class
        """,
        "late_deliveries": """
            SELECT supplier,
                   COUNT(*) as total_orders,
                   SUM(CASE WHEN on_time = 0 THEN 1 ELSE 0 END) as late_orders,
                   ROUND(AVG(lead_time_variance), 1) as avg_variance_days,
                   ROUND(100.0 * SUM(CASE WHEN on_time = 0 THEN 1 ELSE 0 END)
                   / COUNT(*), 2) as late_rate_pct
            FROM purchase_orders
            WHERE status = 'Delivered'
            GROUP BY supplier
            ORDER BY late_rate_pct DESC
        """,
    }
    results = {}
    for name, query in queries.items():
        results[name] = pd.read_sql_query(query, conn)
    conn.close()
    return results
