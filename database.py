
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "credit_risk.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_age REAL NOT NULL,
                person_income REAL NOT NULL,
                loan_amnt REAL NOT NULL,
                loan_int_rate REAL NOT NULL,
                probability REAL NOT NULL,
                threshold REAL NOT NULL,
                prediction TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully: {DB_PATH}")
