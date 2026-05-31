import re
import pandas as pd
import sqlite3
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from backend.config import HUGGINGFACE_API_TOKEN, DB_PATH
from backend.tools import generate_chart
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert financial data analyst for Indian stock market data.
Translate natural language questions into SQL queries and answer clearly.

Database tables:
- stock_prices (date, ticker, open, high, low, close, volume, sector)
- companies (ticker, name, sector, market_cap, index_name)
  NOTE: market_cap values are lowercase strings: 'largecap', 'midcap', 'smallcap'
- stock_metrics (ticker, week_ending, avg_volume, price_change_pct, volatility, rsi_14)

Rules:
- Always use LIMIT to avoid huge results unless user asks for full data.
- Write clean, efficient SQL.
- If a query errors, fix and retry.
- market_cap column uses lowercase: 'largecap', 'midcap', 'smallcap' — never use 'LargeCap' or 'MidCap'.
- In your final answer, wrap the SQL used like this:
  [SQL_QUERY]SELECT ... FROM ...[/SQL_QUERY]
"""

# Per-session message history store
_session_histories: dict = {}
from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY

def get_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=GROQ_API_KEY,
        temperature=0,
    )

def run_sql(sql: str) -> pd.DataFrame:
    """Execute SQL directly against the SQLite DB and return a DataFrame."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return pd.DataFrame()

def clean_answer(answer: str) -> str:
    """Strip [SQL_QUERY]...[/SQL_QUERY] tags from displayed answer."""
    return re.sub(r'\[SQL_QUERY\].*?\[/SQL_QUERY\]', '', answer, flags=re.DOTALL).strip()

def extract_sql(answer: str) -> str:
    """Extract SQL from tagged block in answer."""
    match = re.search(r'\[SQL_QUERY\](.*?)\[/SQL_QUERY\]', answer, re.DOTALL)
    return match.group(1).strip() if match else ""

def process_query(user_input: str, session_id: str = "default") -> dict:
    """Main function: takes user input, returns answer, SQL, and chart JSON."""

    if session_id not in _session_histories:
        _session_histories[session_id] = []

    history = _session_histories[session_id]

    try:
        llm = get_llm()
        db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = toolkit.get_tools()

        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=SYSTEM_PROMPT
        )

        messages = history + [HumanMessage(content=user_input)]
        result = agent.invoke({"messages": messages})

        # Extract final AI answer
        raw_answer = ""
        for msg in reversed(result["messages"]):
            if msg.__class__.__name__ == "AIMessage" and msg.content:
                content = msg.content
                if isinstance(content, str):
                    raw_answer = content
                elif isinstance(content, list):
                    raw_answer = " ".join(
                        block.get("text", "") if isinstance(block, dict) else str(block)
                        for block in content
                    ).strip()
                if raw_answer:
                    break

        # Update history
        _session_histories[session_id] = result["messages"][-20:]

        # Extract SQL and clean answer
        sql_query = extract_sql(raw_answer)
        display_answer = clean_answer(raw_answer)

        # Generate chart if we have SQL
        chart_json = None
        if sql_query:
            df = run_sql(sql_query)
            if not df.empty:
                chart_json = generate_chart(df, user_input)

        return {
            "answer": display_answer,
            "sql": sql_query,
            "chart_json": chart_json,
            "error": None
        }

    except Exception as e:
        logger.error(f"Agent error: {e}")
        return {
            "answer": f"Sorry, I couldn't process that. Error: {str(e)}",
            "sql": "",
            "chart_json": None,
            "error": str(e)
        }