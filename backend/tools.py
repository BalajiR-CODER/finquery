import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def generate_chart(df: pd.DataFrame, user_question: str) -> dict:
    """
    Returns a Plotly chart as JSON.
    Auto-detects the best chart type from the dataframe.
    """
    if df.empty:
        return None

    # Heuristic: if only one row, make a bar chart
    if len(df) == 1:
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df.columns)),
            cells=dict(values=[df[col] for col in df.columns])
        )])
        fig.update_layout(title="Result")
        return fig.to_json()

    # Detect columns
    cols = df.columns.tolist()
    # If we have a date-like column + numeric, use line chart
    date_col = None
    numeric_cols = []
    for col in cols:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_col = col
        elif pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)

    # If there's a ticker column and multiple tickers, maybe multi-line
    if "ticker" in cols and date_col and numeric_cols:
        # Group by ticker over time -> line chart
        fig = px.line(df, x=date_col, y=numeric_cols[0], color="ticker",
                      title=f"{numeric_cols[0]} over time by stock")
        return fig.to_json()

    if date_col and numeric_cols:
        fig = px.line(df, x=date_col, y=numeric_cols[0], title=f"{numeric_cols[0]} trend")
        return fig.to_json()

    # If ranking or categorical + numeric -> bar chart
    if len(df) <= 20 and len(numeric_cols) >= 1:
        cat_col = None
        if cols and not pd.api.types.is_numeric_dtype(df[cols[0]]):
            cat_col = cols[0]
        elif len(cols) > 1 and not pd.api.types.is_numeric_dtype(df[cols[1]]):
            cat_col = cols[1]
        if cat_col:
            fig = px.bar(df, x=cat_col, y=numeric_cols[0], title=f"{numeric_cols[0]} by {cat_col}")
            return fig.to_json()

    # Fallback: table
    fig = go.Figure(data=[go.Table(
        header=dict(values=cols),
        cells=dict(values=[df[col] for col in cols])
    )])
    return fig.to_json()