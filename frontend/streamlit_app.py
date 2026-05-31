import streamlit as st
import requests
import plotly.graph_objects as go
import json

API_URL = "http://localhost:8000"

st.set_page_config(page_title="FinQuery", layout="wide")
st.title("📊 FinQuery – Natural Language Analytics for Indian Stocks")

# Session state for chat and session id
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_session"

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg and msg["sql"]:
            with st.expander("🔍 SQL Query"):
                st.code(msg["sql"], language="sql")
        if "chart_json" in msg and msg["chart_json"]:
            fig = go.Figure(json.loads(msg["chart_json"]))
            st.plotly_chart(fig, use_container_width=True)

# Quick example buttons
examples = [
    "What are the top 5 stocks by average volume this month?",
    "Show me price trend of BEL vs HAL for last 6 months",
    "Which sector had the best average returns in 2024?",
    "Compare volatility of largecap vs midcap stocks",
    "What was POLYCAB's highest closing price this year?",
    "Show me all defence sector stocks ranked by 2024 return"
]

cols = st.columns(3)
for i, ex in enumerate(examples):
    if cols[i % 3].button(ex, key=f"ex_{i}"):
        user_input = ex
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Send to backend
        with st.spinner("FinQuery is analyzing..."):
            try:
                resp = requests.post(f"{API_URL}/query", json={
                    "question": user_input,
                    "session_id": st.session_state.session_id
                })
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data.get("answer", "No answer")
                    sql = data.get("sql", "")
                    chart_json = data.get("chart_json")
                    error = data.get("error")
                    if error:
                        answer = f"⚠️ {error}"
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sql": sql,
                        "chart_json": chart_json
                    })
                    st.rerun()
                else:
                    st.error(f"Backend error: {resp.status_code}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# Chat input
if prompt := st.chat_input("Ask a question about Indian stocks..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("FinQuery is analyzing..."):
        try:
            resp = requests.post(f"{API_URL}/query", json={
                "question": prompt,
                "session_id": st.session_state.session_id
            })
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer", "No answer")
                sql = data.get("sql", "")
                chart_json = data.get("chart_json")
                error = data.get("error")
                if error:
                    answer = f"⚠️ {error}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sql": sql,
                    "chart_json": chart_json
                })
                st.rerun()
            else:
                st.error(f"Backend error: {resp.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {e}")