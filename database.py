import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "ecommerce_analytics"),
        connection_timeout=5,
    )


def fetch_sales():
    connection = get_connection()
    try:
        query = """
            SELECT Order_ID, Date, Product, Category,
                   Region, Customer, Quantity, Sales, Cost
            FROM sales
            ORDER BY Date DESC
        """
        return pd.read_sql(query, connection)
    finally:
        connection.close()


def insert_sales(df):
    if df.empty:
        return 0
    columns = [
        "Order_ID", "Date", "Product", "Category", "Region",
        "Customer", "Quantity", "Sales", "Cost"
    ]
    data = df[columns].copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="raise").dt.date
    records = [tuple(row) for row in data.itertuples(index=False, name=None)]
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO sales (
                Order_ID, Date, Product, Category, Region,
                Customer, Quantity, Sales, Cost
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                Date=VALUES(Date), Product=VALUES(Product),
                Category=VALUES(Category), Region=VALUES(Region),
                Customer=VALUES(Customer), Quantity=VALUES(Quantity),
                Sales=VALUES(Sales), Cost=VALUES(Cost)
        """
        cursor.executemany(query, records)
        connection.commit()
        return len(records)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
