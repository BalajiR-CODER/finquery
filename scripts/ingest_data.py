import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from backend.database import init_db, get_engine

NSE_STOCKS = {
    "RELIANCE.NS":   {"name": "Reliance Industries",  "sector": "Oil & Gas",   "market_cap": "largecap",  "index": "NIFTY50"},
    "INFY.NS":       {"name": "Infosys",              "sector": "IT",          "market_cap": "largecap",  "index": "NIFTY50"},
    "TCS.NS":        {"name": "TCS",                  "sector": "IT",          "market_cap": "largecap",  "index": "NIFTY50"},
    "HDFCBANK.NS":   {"name": "HDFC Bank",            "sector": "Banking",     "market_cap": "largecap",  "index": "NIFTY50"},
    "ICICIBANK.NS":  {"name": "ICICI Bank",           "sector": "Banking",     "market_cap": "largecap",  "index": "NIFTY50"},
    "BEL.NS":        {"name": "Bharat Electronics",   "sector": "Defence",     "market_cap": "largecap",  "index": "NIFTY50"},
    "HAL.NS":        {"name": "Hindustan Aeronautics","sector": "Defence",     "market_cap": "largecap",  "index": "NIFTY50"},
    "POLYCAB.NS":    {"name": "Polycab India",        "sector": "Cables",      "market_cap": "midcap",    "index": "NIFTY500"},
    "DIXON.NS":      {"name": "Dixon Technologies",   "sector": "Electronics", "market_cap": "midcap",    "index": "NIFTY500"},
    "ZENTEC.NS":     {"name": "Zen Technologies",     "sector": "Defence",     "market_cap": "smallcap",  "index": "NIFTY500"},
    "DATAPATTNS.NS": {"name": "Data Patterns",        "sector": "Defence",     "market_cap": "smallcap",  "index": "NIFTY500"},
    "LT.NS":         {"name": "Larsen & Toubro",      "sector": "Infra",       "market_cap": "largecap",  "index": "NIFTY50"},
    "TITAN.NS":      {"name": "Titan",                "sector": "Consumer",    "market_cap": "largecap",  "index": "NIFTY50"},
    "ASIANPAINT.NS": {"name": "Asian Paints",         "sector": "Consumer",    "market_cap": "largecap",  "index": "NIFTY50"},
    "MARUTI.NS":     {"name": "Maruti Suzuki",        "sector": "Auto",        "market_cap": "largecap",  "index": "NIFTY50"},
    "BAJFINANCE.NS": {"name": "Bajaj Finance",        "sector": "Finance",     "market_cap": "largecap",  "index": "NIFTY50"},
    "SBIN.NS":       {"name": "State Bank of India",  "sector": "Banking",     "market_cap": "largecap",  "index": "NIFTY50"},
    "ITC.NS":        {"name": "ITC",                  "sector": "FMCG",        "market_cap": "largecap",  "index": "NIFTY50"},
    "SUNPHARMA.NS":  {"name": "Sun Pharma",           "sector": "Pharma",      "market_cap": "largecap",  "index": "NIFTY50"},
    "BHARTIARTL.NS": {"name": "Bharti Airtel",        "sector": "Telecom",     "market_cap": "largecap",  "index": "NIFTY50"},
}

def download_and_store():
    init_db()
    engine = get_engine()

    end_date = datetime.today()
    start_date = end_date - timedelta(days=730)

    price_rows = []
    company_rows = []
    metrics_rows = []

    for yticker, info in NSE_STOCKS.items():
        ticker_clean = yticker.replace(".NS", "")
        company_rows.append({
            "ticker": ticker_clean,
            "name": info["name"],
            "sector": info["sector"],
            "market_cap": info["market_cap"],
            "index_name": info["index"]
        })

        try:
            df = yf.download(
                yticker,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True
            )

            if df.empty:
                print(f"No data for {yticker}")
                continue

            # Flatten MultiIndex columns (yfinance v0.2+)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Reset index, lowercase, rename 'index' -> 'date'
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            df = df.rename(columns={"index": "date"})

            df["ticker"] = ticker_clean
            df["sector"] = info["sector"]

            price_rows.append(df[["date", "ticker", "open", "high", "low", "close", "volume", "sector"]])
            print(f"✅ {ticker_clean}: {len(df)} rows")

            # Weekly metrics
            df["date"] = pd.to_datetime(df["date"])
            weekly = df.set_index("date").resample("W-FRI").agg(
                avg_volume=("volume", "mean"),
                close_first=("close", "first"),
                close_last=("close", "last"),
                volatility=("close", "std")
            ).reset_index()

            weekly["price_change_pct"] = (
                (weekly["close_last"] - weekly["close_first"]) / weekly["close_first"] * 100
            )
            weekly["rsi_14"] = 0
            weekly["ticker"] = ticker_clean

            for _, row in weekly.iterrows():
                metrics_rows.append({
                    "ticker": row["ticker"],
                    "week_ending": row["date"].strftime("%Y-%m-%d"),
                    "avg_volume": int(row["avg_volume"]) if not pd.isna(row["avg_volume"]) else 0,
                    "price_change_pct": round(row["price_change_pct"], 2) if not pd.isna(row["price_change_pct"]) else 0.0,
                    "volatility": round(row["volatility"], 2) if not pd.isna(row["volatility"]) else 0.0,
                    "rsi_14": 0
                })

        except Exception as e:
            print(f"❌ Failed to download {yticker}: {e}")

    # Save to DB
    if price_rows:
        price_df = pd.concat(price_rows, ignore_index=True)
        price_df.to_sql("stock_prices", engine, if_exists="replace", index=False)
        print(f"\n✅ stock_prices: {len(price_df)} total rows saved")

    comp_df = pd.DataFrame(company_rows)
    comp_df.to_sql("companies", engine, if_exists="replace", index=False)
    print(f"✅ companies: {len(comp_df)} rows saved")

    if metrics_rows:
        met_df = pd.DataFrame(metrics_rows)
        met_df.to_sql("stock_metrics", engine, if_exists="replace", index=False)
        print(f"✅ stock_metrics: {len(met_df)} rows saved")

    print("\n🎉 Data ingestion complete.")

if __name__ == "__main__":
    download_and_store()