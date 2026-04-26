# Supply Chain Analytics

![CI](https://github.com/Djones-qa/supply-chain-analytics/actions/workflows/supply-chain-tests.yml/badge.svg?branch=my-feature-branch)

Comprehensive supply chain analytics framework using Python, Pandas, Scikit-learn, Matplotlib, and SQLite. Covers inventory optimization with EOQ and safety stock calculations, ABC classification, stockout and overstock detection, demand forecasting, supplier performance analysis, and SQL supply chain queries.

## Why Supply Chain Analytics Matters
Supply chain inefficiencies cost businesses billions annually:
- Stockouts lose sales and damage customer trust
- Overstock ties up capital and increases holding costs
- Poor supplier performance disrupts operations
- Inaccurate demand forecasting leads to waste
- ABC analysis focuses resources on highest-value items

## Tech Stack
- Python 3.x
- Pandas — data manipulation and supply chain analysis
- NumPy — EOQ, safety stock, and statistical calculations
- Matplotlib + Seaborn — supply chain visualizations
- Scikit-learn — demand forecasting
- SQLite — SQL supply chain investigation queries
- Pytest — test execution and fixtures
- GitHub Actions CI

## Project Structure
`
supply-chain-analytics/
├── scripts/
│   ├── data_generator.py    # Products, demand, orders, supplier data
│   ├── analytics.py         # EOQ, ABC, stockout, supplier analysis
│   └── visualizations.py    # Supply chain dashboard charts
├── tests/
│   ├── test_data_generation.py  # Data quality tests
│   ├── test_analytics.py        # Analytics accuracy tests
│   └── test_visualizations.py   # Chart generation tests
├── data/                    # Generated CSV and SQLite datasets
├── visuals/                 # Generated PNG dashboard charts
├── conftest.py
├── pytest.ini
├── requirements.txt
└── .github/workflows/
    └── supply-chain-tests.yml
`

## Analytics Covered

### Inventory Optimization
- Economic Order Quantity (EOQ) calculation
- Safety stock using service level and demand variability
- Reorder point — lead time demand plus safety stock
- Stockout risk detection — stock below reorder point
- Overstock detection — stock above 2x EOQ
- Days of stock remaining per SKU

### ABC Inventory Classification
- Annual value calculation per SKU
- Cumulative value percentage
- A class — top 80% of value
- B class — next 15% of value
- C class — bottom 5% of value

### Demand Forecasting
- Daily demand history with seasonality
- 7-day moving average forecast
- 30-day moving average trend
- Demand trend analysis
- Holiday season and day-of-week factors

### Supplier Performance
- Composite performance score
- On-time delivery rate weighted 35%
- Quality rating weighted 30%
- Defect rate weighted 20%
- Contract compliance weighted 15%
- Supplier tier classification — Tier 1, 2, 3

### Purchase Order Analysis
- On-time delivery rate
- Lead time variance tracking
- Monthly spend trend
- Late delivery analysis by supplier

## SQL Investigation Queries
- Stockout risk products with days of stock remaining
- Inventory value by category
- Supplier spend and on-time delivery rate
- Overstock products with excess value
- ABC classification summary
- Late delivery rate by supplier

## Charts Generated
1. Inventory Stock Status Distribution
2. ABC Classification — SKU count and annual value
3. Demand Forecast with Moving Averages
4. Inventory Value by Category
5. Supplier Performance — On-Time vs Quality
6. Lead Time Distribution — On-Time vs Late
7. EOQ vs Current Stock Level
8. Monthly Purchase Order Spend

## Run Tests
`ash
pip install -r requirements.txt
python -m pytest tests/ -v
`

## Author
Darrius Jones - github.com/Djones-qa