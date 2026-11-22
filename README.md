# Indian Ecommerce AI Analytics

An end-to-end data analytics and machine learning project that explores synthetic Indian ecommerce data to identify business trends, understand customer behaviour, evaluate product profitability, and monitor operational performance.

## Project Overview

This project transforms raw ecommerce data into meaningful business insights using Python, SQL, DuckDB, Streamlit, and Machine Learning.

It includes an interactive multi-page dashboard with sales analysis, customer segmentation, product performance, operational analytics, automated business insights, and downloadable reports.

**Dataset disclosure:** This project uses a synthetic Indian ecommerce dataset. It does not contain actual transaction data from Amazon, Flipkart, Meesho, or any other ecommerce company.

## Business Objectives

- Analyse sales trends and revenue performance.
- Identify valuable and repeat customers.
- Understand customer purchasing behaviour.
- Evaluate product and category profitability.
- Identify product return patterns.
- Monitor payment success and delivery performance.
- Apply machine learning to customer segmentation.
- Generate actionable business recommendations.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data analysis and application development |
| Pandas | Data cleaning and transformation |
| NumPy | Numerical operations |
| SQL | Business queries and analysis |
| DuckDB | Analytical database |
| Scikit-learn | K-Means customer segmentation |
| Streamlit | Interactive dashboard |
| Plotly | Interactive charts |
| OpenPyXL | Excel report generation |
| Git and GitHub | Version control and project sharing |

## Project Features

### 1. Business Overview
- Delivered orders
- Delivered order value
- Average order value
- Unique customers
- Product profit
- Date-range filtering

### 2. Sales Analysis
- Monthly sales trends
- Monthly order volume
- Category-wise revenue
- Category-wise profit
- State-wise sales performance

### 3. Customer Analysis
- One-time and repeat customers
- Repeat purchase rate
- Customer purchase frequency
- Monthly active customers
- Top customers by order value
- State-wise customer distribution

### 4. Product Analysis
- Product revenue and profit
- Category profitability
- Top 10 products by revenue
- Lowest-profit products
- Category-level product return rates

### 5. Operations Analysis
- Payment method performance
- Payment success and failure rates
- Return reasons and refund status
- Delivery delay analysis
- Shipping method performance
- Warehouse performance

### 6. AI Business Insights
- K-Means customer segmentation
- Recency, Frequency and Monetary analysis
- Customer group comparisons
- Automated business observations
- Data-driven recommendations

The machine learning component uses K-Means clustering. Business recommendations are generated through transparent metric-based rules rather than a generative AI model.

### 7. Downloadable Reports
- Executive summary
- Monthly sales report
- Category performance report
- State performance report
- Customer performance report
- Payment method report
- Return reasons report
- Delivery performance report
- Metric definitions

Reports can be downloaded in Excel and CSV formats.

## Dataset Information

The project uses nine main business tables:

| Dataset | Records |
|---|---:|
| Customers | 25,000 |
| Customer Reviews | 77,530 |
| Marketing Campaigns | 151 |
| Orders | 100,000 |
| Order Items | 254,331 |
| Payments | 100,000 |
| Products | 550 |
| Returns | 12,075 |
| Shipments | 89,681 |

The dataset also includes a data dictionary and validation report.

## Selected Business Findings

The following findings were identified during analysis of the full synthetic dataset:

- Delivered order value was approximately ₹208.43 crore.
- Delivered product revenue was approximately ₹198.49 crore.
- Product profit was approximately ₹15.86 crore.
- Overall product profit margin was approximately 7.99%.
- Electronics generated the highest category revenue but had a very low product profit margin.
- Fashion recorded a relatively high product profit margin.
- Footwear had the highest category-level product-line return rate in the analysis.
- Standard shipping had a higher delivery delay rate than Next-Day shipping.

These findings describe the synthetic dataset, not the actual Indian ecommerce market.

## Project Structure

```text
Indian_Ecommerce_AI_Analytics/
│
├── data/
│   ├── raw/
│   └── cleaned/
│
├── database/
│   └── ecommerce_analytics.duckdb
│
├── notebooks/
│
├── src/
│   ├── create_database.py
│   ├── inspect_data.py
│   ├── clean_data.py
│   ├── validate_relationships.py
│   ├── validate_financials.py
│   ├── build_kpi_analysis.py
│   ├── customer_rfm_analysis.py
│   ├── customer_cohort_analysis.py
│   ├── payment_analysis.py
│   ├── return_analysis.py
│   └── delivery_analysis.py
│
├── dashboards/
│   ├── app.py
│   └── pages/
│       ├── 1_Sales_Analysis.py
│       ├── 2_Customer_Analysis.py
│       ├── 3_Product_Analysis.py
│       ├── 4_Operations_Analysis.py
│       ├── 5_AI_Business_Insights.py
│       └── 6_Download_Reports.py
│
├── reports/
├── requirements.txt
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.13 or newer
- Visual Studio Code
- Git
- The project dataset

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Open the project folder

```bash
cd Indian_Ecommerce_AI_Analytics
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Start the dashboard

```bash
python -m streamlit run dashboards/app.py
```

The dashboard will open in your browser.

**Note:** The DuckDB database and source dataset must be available in their expected project folders. If the database is not included in the repository, follow the database creation steps in the project source code.

## Key Business Metric Definitions

- **Delivered Order Value:** Sum of final order amounts for delivered orders, including shipping and tax.
- **Product Revenue:** Sum of item revenue for delivered order items.
- **Product Profit:** Product revenue minus product cost.
- **Product Profit Margin:** Product profit divided by product revenue, multiplied by 100.
- **Repeat Purchase Rate:** Customers with more than one delivered order divided by customers with delivered orders in the selected period.
- **Customer Value:** Sum of delivered order final amounts for a customer.
- **Return Rate:** Distinct returned order-product lines divided by eligible delivered and returned order-product lines, where specified.

Metric definitions may differ between individual analyses. Refer to the relevant dashboard page for its calculation scope.

## Future Improvements

- Add sales forecasting using machine learning.
- Develop a product demand prediction model.
- Add customer churn prediction.
- Improve dashboard navigation and user experience.
- Add more interactive filters.
- Deploy the dashboard using a suitable hosting platform.
- Add automated report scheduling.

## Author

Developed as a portfolio project to demonstrate practical skills in data analytics, SQL, Python, dashboard development, and machine learning.

**Project:** Indian Ecommerce AI Analytics  
**Category:** Data Analytics | Business Intelligence | Machine Learning  
**Tools:** Python, SQL, DuckDB, Pandas, Plotly, Streamlit, Scikit-learn