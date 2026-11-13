import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/trades.db")


def log_trade(**fields: str | int | float) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trade_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                rationale TEXT,
                order_id TEXT,
                status TEXT NOT NULL
            )
            """
        )

        fields["timestamp"] = datetime.now(timezone.utc).isoformat()
        columns = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)

        conn.execute(
            f"INSERT INTO trade_journal ({columns}) VALUES ({placeholders})",
            list(fields.values()),
        )
