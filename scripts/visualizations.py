"""
Supply chain analytics visualizations.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

sns.set_theme(style="darkgrid")
os.makedirs("visuals", exist_ok=True)

COLORS = {
    "blue": "#1B4F8A",
    "green": "#2ECC71",
    "red": "#E74C3C",
    "orange": "#F39C12",
    "purple": "#9B59B6",
    "teal": "#1ABC9C",
    "gray": "#95A5A6",
}


def save(fig, name):
    path = f"visuals/{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_stock_status(products_df):
    """Pie chart — inventory stock status distribution."""
    from scripts.analytics import detect_stockouts
    status_df = detect_stockouts(products_df)
    status_counts = status_df["stock_status"].value_counts()
    colors = [COLORS["red"] if s == "Stockout Risk" else
              COLORS["orange"] if s == "Overstock" else
              COLORS["green"] for s in status_counts.index]
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.pie(status_counts.values, labels=status_counts.index,
           colors=colors, autopct="%1.1f%%", startangle=90,
           wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax.set_title("Inventory Stock Status Distribution",
                 fontsize=14, fontweight="bold", pad=20)
    return save(fig, "01_stock_status")


def plot_abc_classification(products_df):
    """Bar chart — ABC inventory classification."""
    from scripts.analytics import classify_abc
    abc_df = classify_abc(products_df)
    abc_summary = abc_df.groupby("calculated_abc").agg(
        count=("product_id", "count"),
        value=("annual_value", "sum")
    ).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    colors = [COLORS["red"], COLORS["orange"], COLORS["blue"]]
    axes[0].bar(abc_summary["calculated_abc"], abc_summary["count"],
                color=colors, alpha=0.85)
    axes[0].set_title("ABC Classification — SKU Count",
                      fontsize=12, fontweight="bold")
    axes[0].set_xlabel("ABC Class")
    axes[0].set_ylabel("Number of SKUs")
    axes[1].bar(abc_summary["calculated_abc"],
                abc_summary["value"] / 1e6,
                color=colors, alpha=0.85)
    axes[1].set_title("ABC Classification — Annual Value ($M)",
                      fontsize=12, fontweight="bold")
    axes[1].set_xlabel("ABC Class")
    axes[1].set_ylabel("Annual Value ($M)")
    fig.suptitle("ABC Inventory Classification",
                 fontsize=14, fontweight="bold", y=1.02)
    return save(fig, "02_abc_classification")


def plot_demand_forecast(demand_df, product_id):
    """Line chart — demand history and moving average forecast."""
    from scripts.analytics import forecast_demand
    forecast = forecast_demand(demand_df, product_id, window=7)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(forecast["date"], forecast["demand"],
            alpha=0.4, color=COLORS["gray"], linewidth=1, label="Daily Demand")
    ax.plot(forecast["date"], forecast["ma_7"],
            color=COLORS["blue"], linewidth=2.5, label="7-Day MA")
    ax.plot(forecast["date"], forecast["ma_30"],
            color=COLORS["red"], linewidth=2.5,
            linestyle="--", label="30-Day MA")
    ax.set_title(f"Demand Forecast — {product_id}",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Date")
    ax.set_ylabel("Units Demanded")
    ax.legend()
    plt.xticks(rotation=30, ha="right")
    return save(fig, "03_demand_forecast")


def plot_inventory_by_category(products_df):
    """Bar chart — inventory value by category."""
    cat_value = (
        products_df.groupby("category").apply(
            lambda x: (x["current_stock"] * x["unit_cost"]).sum()
        ).sort_values(ascending=True)
    )
    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(cat_value.index, cat_value.values / 1000,
                   color=COLORS["blue"], alpha=0.85)
    for bar, val in zip(bars, cat_value.values / 1000):
        ax.text(val + 1, bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}K", va="center", fontsize=9, fontweight="bold")
    ax.set_title("Inventory Value by Category ($K)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Inventory Value ($K)")
    return save(fig, "04_inventory_by_category")


def plot_supplier_performance(suppliers_df):
    """Scatter — supplier on-time delivery vs quality rating."""
    from scripts.analytics import analyze_supplier_performance
    ranked = analyze_supplier_performance(suppliers_df)
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = [COLORS["green"] if t == "Tier 1" else
              COLORS["orange"] if t == "Tier 2" else
              COLORS["red"] for t in ranked["supplier_tier"].astype(str)]
    scatter = ax.scatter(ranked["on_time_delivery_pct"],
                         ranked["quality_rating"],
                         s=ranked["total_spend"] / 2000,
                         c=colors, alpha=0.8)
    for _, row in ranked.iterrows():
        ax.annotate(row["supplier"][:12],
                    (row["on_time_delivery_pct"], row["quality_rating"]),
                    textcoords="offset points", xytext=(5, 5), fontsize=8)
    ax.axvline(x=90, color=COLORS["gray"], linestyle="--",
               linewidth=1.5, label="90% on-time target")
    ax.axhline(y=4.0, color=COLORS["gray"], linestyle=":",
               linewidth=1.5, label="4.0 quality target")
    ax.set_title("Supplier Performance — On-Time vs Quality\n(bubble = spend)",
                 fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("On-Time Delivery (%)")
    ax.set_ylabel("Quality Rating (1-5)")
    ax.legend()
    return save(fig, "05_supplier_performance")


def plot_lead_time_distribution(orders_df):
    """Histogram — lead time distribution by supplier."""
    delivered = orders_df[orders_df["status"] == "Delivered"]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(delivered[delivered["on_time"] == True]["lead_time_actual"],
            bins=20, alpha=0.7, color=COLORS["green"], label="On-Time")
    ax.hist(delivered[delivered["on_time"] == False]["lead_time_actual"],
            bins=20, alpha=0.7, color=COLORS["red"], label="Late")
    ax.axvline(delivered["lead_time_actual"].mean(),
               color=COLORS["blue"], linestyle="--",
               linewidth=2, label=f"Mean: {delivered['lead_time_actual'].mean():.1f} days")
    ax.set_title("Lead Time Distribution — On-Time vs Late Deliveries",
                 fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("Lead Time (Days)")
    ax.set_ylabel("Number of Orders")
    ax.legend()
    return save(fig, "06_lead_time_distribution")


def plot_eoq_vs_current_stock(products_df):
    """Scatter — EOQ vs current stock levels."""
    fig, ax = plt.subplots(figsize=(11, 7))
    colors = [COLORS["red"] if r <= rp else
              COLORS["orange"] if c > e * 2 else
              COLORS["green"]
              for r, rp, c, e in zip(
                  products_df["current_stock"],
                  products_df["reorder_point"],
                  products_df["current_stock"],
                  products_df["eoq"])]
    ax.scatter(products_df["eoq"], products_df["current_stock"],
               c=colors, alpha=0.6, s=40)
    max_val = max(products_df["eoq"].max(),
                  products_df["current_stock"].max())
    ax.plot([0, max_val], [0, max_val], "--",
            color=COLORS["gray"], linewidth=1.5, label="EOQ = Stock")
    ax.set_title("EOQ vs Current Stock Level",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Economic Order Quantity (EOQ)")
    ax.set_ylabel("Current Stock Level")
    from matplotlib.patches import Patch
    legend = [Patch(color=COLORS["green"], label="Optimal"),
              Patch(color=COLORS["red"], label="Stockout Risk"),
              Patch(color=COLORS["orange"], label="Overstock")]
    ax.legend(handles=legend)
    return save(fig, "07_eoq_vs_stock")


def plot_monthly_order_spend(orders_df):
    """Line chart — monthly purchase order spend."""
    orders = orders_df.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    monthly = orders.groupby(
        orders["order_date"].dt.to_period("M")
    )["total_cost"].sum().reset_index()
    monthly["order_date"] = monthly["order_date"].astype(str)
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(range(len(monthly)), monthly["total_cost"] / 1000,
            color=COLORS["blue"], linewidth=2.5, marker="o", markersize=5)
    ax.fill_between(range(len(monthly)), monthly["total_cost"] / 1000,
                    alpha=0.15, color=COLORS["blue"])
    ax.set_title("Monthly Purchase Order Spend ($K)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Spend ($K)")
    ax.set_xticks(range(len(monthly)))
    ax.set_xticklabels(monthly["order_date"], rotation=45, ha="right")
    return save(fig, "08_monthly_order_spend")
