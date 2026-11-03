# E-commerce Sales Analytics Dashboard

An interactive analytics dashboard built with Python, Pandas, Streamlit, Plotly and optional MySQL.

## Features
- Revenue, profit, orders and profit-margin KPIs
- Monthly revenue trend
- Product and regional analysis
- Category profitability
- Product, region and date filters
- CSV upload and filtered CSV export
- Optional MySQL data source

## Run on macOS

Open Terminal in this project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python data_generator.py
python -m streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Optional MySQL setup

1. Run `mysql -u root -p < schema.sql` if MySQL is installed and running.
2. Copy `.env.example` to `.env` and enter your local MySQL credentials.
3. Run `python import_to_mysql.py`.
4. Select **MySQL** in the dashboard sidebar.

Sample data is synthetic and intended for learning, not real business reporting.
