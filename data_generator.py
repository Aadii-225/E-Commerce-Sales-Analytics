from pathlib import Path
import numpy as np
import pandas as pd

OUTPUT = Path("data/sales.csv")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def generate_sales(n=1000, seed=42):
    rng = np.random.default_rng(seed)
    products = {
        "Laptop": ("Electronics", 55000, 0.75),
        "Mobile": ("Electronics", 22000, 0.78),
        "Tablet": ("Electronics", 18000, 0.76),
        "Headphones": ("Accessories", 2500, 0.60),
        "Keyboard": ("Accessories", 1500, 0.55),
    }
    names = list(products)
    selected = rng.choice(names, n)
    start = pd.Timestamp("2025-01-01").value // 10**9
    end = pd.Timestamp("2026-10-01").value // 10**9
    dates = pd.to_datetime(rng.integers(start, end, n), unit="s").normalize()
    rows = []
    for i, product in enumerate(selected):
        category, price, cost_ratio = products[product]
        quantity = int(rng.integers(1, 5))
        unit_price = price * float(rng.uniform(0.90, 1.10))
        sales = round(unit_price * quantity, 2)
        cost = round(sales * cost_ratio * float(rng.uniform(0.90, 1.10)), 2)
        rows.append({
            "Order_ID": f"ORD-{i + 1:05d}",
            "Date": dates[i].strftime("%Y-%m-%d"),
            "Product": product,
            "Category": category,
            "Region": str(rng.choice(["North", "South", "East", "West"])),
            "Customer": f"CUST-{int(rng.integers(1, 251)):04d}",
            "Quantity": quantity,
            "Sales": sales,
            "Cost": cost,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sales()
    df.to_csv(OUTPUT, index=False)
    print(f"Created {len(df)} sample orders: {OUTPUT}")
