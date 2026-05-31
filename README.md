# 📈 FinQuery

**Natural Language Analytics for Indian Stocks**

Ask questions about NSE-listed stocks in plain English. FinQuery translates them into SQL queries, executes them against a real market database, and returns answers with auto-generated charts.

> *"Which sector had the highest volatility last month?"*
> *"Compare BEL vs HAL price trend over 6 months"*
> *"Top 5 stocks by average volume this week"*

---

## 🧠 What This Demonstrates

This project is a production-style **Text-to-SQL AI agent** — one of the most in-demand AI Engineer deliverables across fintech, SaaS, and enterprise data teams.

| Skill | Implementation |
|---|---|
| LLM tool use / ReAct loop | LangGraph `create_react_agent` with SQL toolkit |
| Structured data + LLMs | SQLite DB with real NSE OHLCV data |
| Agentic error recovery | Agent retries on bad SQL, fixes column names |
| Full pipeline to UI | NL → SQL → DataFrame → Plotly chart → Streamlit |
| Session memory | Per-session message history across multi-turn queries |

---

## 🏗️ Architecture

```
User (Streamlit UI)
        │
        ▼
FastAPI Backend (/query endpoint)
        │
        ▼
LangGraph ReAct Agent
        │
   ┌────┴────┐
   │         │
SQL Tools   Qwen2.5-7B (HuggingFace)
   │
   ▼
SQLite Database
├── stock_prices     (date, ticker, OHLCV, sector)
├── companies        (ticker, name, sector, market_cap, index)
└── stock_metrics    (ticker, week_ending, avg_volume, volatility, RSI)
        │
        ▼
Plotly Chart (auto-generated from query result)
```

---

## 🗂️ Project Structure

```
finquery/
├── backend/
│   ├── agent.py          # LangGraph ReAct agent + session memory
│   ├── app.py            # FastAPI endpoints (/query, /schema)
│   ├── config.py         # Environment config (API keys, DB path)
│   ├── database.py       # SQLite schema creation
│   └── tools.py          # Plotly chart auto-generator
├── frontend/
│   └── streamlit_app.py  # Chat UI with SQL expander + charts
├── scripts/
│   └── ingest_data.py    # yfinance → SQLite pipeline (20 NSE stocks, 2yr)
├── data/
│   └── finquery.db       # SQLite database (auto-generated)
├── .env                  # API keys (not committed)
└── requirements.txt
```

---

## 🚀 Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/yourusername/finquery.git
cd finquery
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file at the project root:

```env
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
```

Get your free token at: https://huggingface.co/settings/tokens

### 4. Ingest market data

Downloads 2 years of daily OHLCV data for 20 NSE stocks via yfinance:

```bash
python scripts/ingest_data.py
```

### 5. Start the backend

```bash
uvicorn backend.app:app --reload
```

### 6. Start the frontend (new terminal)

```bash
streamlit run frontend/streamlit_app.py
```

Open http://localhost:8501

---

## 📊 Database

20 NSE stocks across 10 sectors:

| Sector | Stocks |
|---|---|
| IT | TCS, Infosys |
| Banking | HDFC Bank, ICICI Bank, SBI |
| Defence | BEL, HAL, Zen Technologies, Data Patterns |
| Energy | Reliance Industries |
| Consumer | Titan, Asian Paints |
| Auto | Maruti Suzuki |
| Finance | Bajaj Finance |
| Telecom | Bharti Airtel |
| FMCG | ITC |
| Pharma | Sun Pharma |

---

## 💬 Sample Queries

```
Compare volatility of largecap vs midcap stocks
Show me price trend of BEL vs HAL for last 6 months
Which sector had the best average returns in 2024?
Top 5 stocks by average volume this month
What was POLYCAB's highest closing price this year?
Show all defence sector stocks ranked by return
Which stocks have RSI above 60 this week?
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Qwen2.5-7B-Instruct (HuggingFace Inference API) |
| Agent Framework | LangGraph + LangChain |
| SQL Toolkit | LangChain SQLDatabaseToolkit |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Charts | Plotly |
| Database | SQLite |
| Data Source | yfinance (Yahoo Finance) |

---

## 📸 Demo

![FinQuery Demo](assets/demo.png)

*Volatility comparison across NSE sectors — query answered in natural language, chart auto-generated*

---

## 🔧 How the Agent Works

1. User sends a natural language question via Streamlit
2. FastAPI receives the request and calls `process_query()`
3. LangGraph's ReAct agent receives the question + conversation history
4. The agent uses `sql_db_query` and `sql_db_schema` tools to explore the DB
5. Qwen2.5 generates SQL, the toolkit executes it, results come back
6. If SQL errors, the agent self-corrects and retries (up to 8 iterations)
7. Final answer is returned with the SQL tagged as `[SQL_QUERY]...[/SQL_QUERY]`
8. Backend strips tags, executes SQL independently to get a DataFrame
9. DataFrame is passed to `generate_chart()` which auto-selects chart type
10. Streamlit renders answer + SQL expander + Plotly chart

---

## 📝 Notes

- RSI values in `stock_metrics` are simplified approximations (weekly window)
- `market_cap` field uses lowercase strings: `largecap`, `midcap`, `smallcap`
- Free HuggingFace Inference API has rate limits; for production use a paid tier or self-host
- The agent prompt explicitly encodes domain knowledge (index membership, cap categories) to improve SQL accuracy

---

## 👤 Author

Built by **Balaji R** — AI Engineer  
[LinkedIn](https://linkedin.com/in/balaji-r-06b68b289) · [GitHub](https://github.com/BalajiR-CODER)
