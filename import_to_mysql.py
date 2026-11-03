from pathlib import Path
import pandas as pd
from database import insert_sales

file_path = Path("data/sales.csv")
if not file_path.exists():
    raise FileNotFoundError("CSV missing. Run python data_generator.py first.")

df = pd.read_csv(file_path)
count = insert_sales(df)
print(f"Imported or updated {count} sales records.")
