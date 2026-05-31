import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from backend.config import DB_PATH

def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}")

def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            date TEXT,
            ticker TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            sector TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            market_cap TEXT,
            index_name TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_metrics (
            ticker TEXT,
            week_ending TEXT,
            avg_volume INTEGER,
            price_change_pct REAL,
            volatility REAL,
            rsi_14 REAL
        )
    """)

    conn.commit()
    conn.close()