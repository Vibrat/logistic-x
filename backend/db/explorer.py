"""
db/explorer.py — Safe data exploration queries for the AI agentic loop.

Allows the AI to discover real dimension values (SKUs, carriers, regions, etc.)
from the database before committing to a final analytics or forecast query.

Security: column names are validated against an explicit allowlist — never
interpolated from raw user or AI input.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

_EXPLORABLE_COLUMNS = frozenset({
    "sku",
    "product_category",
    "carrier",
    "region",
    "warehouse",
    "status",
    "origin_city",
    "destination_city",
})


def explore_column(column: str, search: str | None, db: Session) -> list[str]:
    """
    Return up to 20 distinct values for *column* in the orders table.
    If *search* is provided, only values containing that string (case-insensitive)
    are returned.

    Raises ValueError for unknown column names.
    """
    if column not in _EXPLORABLE_COLUMNS:
        raise ValueError(
            f"Column '{column}' is not explorable. "
            f"Valid columns: {sorted(_EXPLORABLE_COLUMNS)}"
        )

    # Column name is safe — validated against the allowlist above
    sql = f"SELECT DISTINCT {column} FROM orders"  # noqa: S608
    params: dict = {}

    if search and search.strip():
        sql += f" WHERE {column} ILIKE :search"
        params["search"] = f"%{search.strip()}%"

    sql += f" ORDER BY {column} LIMIT 20"

    rows = db.execute(text(sql), params).fetchall()
    return [str(row[0]) for row in rows if row[0] is not None]
