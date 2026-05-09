"""
Seed the PostgreSQL database from the logistics CSV file.

Usage:
  python -m db.seed                  # seed (idempotent — safe to re-run)
  python -m db.seed --truncate       # force truncate before seeding
"""
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from dotenv import load_dotenv

from db.connection import engine
from db.models import Order

load_dotenv()

# Resolve CSV path: Docker volume mount takes priority, then fall back to repo layout
_docker_path = Path("/product/mock_logistics_data.csv")
_repo_path = Path(__file__).parent.parent.parent / "product" / "mock_logistics_data.csv"
CSV_PATH = _docker_path if _docker_path.exists() else _repo_path

# Columns that map directly from the CSV to the DB (matches Order model fields)
DB_COLUMNS = [
    "order_id", "client_id", "order_date", "delivery_date",
    "carrier", "origin_city", "destination_city", "status",
    "sku", "product_category", "quantity",
    "unit_price_usd", "order_value_usd",
    "is_promo", "promo_discount_pct",
    "region", "warehouse",
]


def _load_csv() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip().lower() for c in df.columns]

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce").dt.date
    df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce").dt.date
    # Convert NaT → None so SQLAlchemy stores NULL
    df["delivery_date"] = df["delivery_date"].where(df["delivery_date"].notna(), other=None)

    df["is_promo"] = df["is_promo"].astype(bool)
    df["promo_discount_pct"] = df["promo_discount_pct"].fillna(0).astype(int)
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price_usd"] = df["unit_price_usd"].astype(float)
    df["order_value_usd"] = df["order_value_usd"].astype(float)

    return df[DB_COLUMNS]


def seed(truncate: bool = False) -> None:
    """
    Seed the orders table from mock_logistics_data.csv.

    Args:
        truncate: If True, truncate the table before inserting.
                  If False (default), uses INSERT ... ON CONFLICT DO NOTHING
                  so existing rows are preserved and the function is safely re-runnable.
    """
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

    df = _load_csv()
    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        if truncate:
            conn.execute(text("TRUNCATE TABLE orders RESTART IDENTITY CASCADE"))
            print("Truncated orders table.")

        # Bulk insert — ON CONFLICT DO NOTHING makes this idempotent
        insert_stmt = pg_insert(Order.__table__).on_conflict_do_nothing(
            index_elements=["order_id"]
        )
        conn.execute(insert_stmt, records)

    print(f"Seeded {len(records)} rows from {CSV_PATH.name} into the orders table.")


if __name__ == "__main__":
    force_truncate = "--truncate" in sys.argv
    seed(truncate=force_truncate)
