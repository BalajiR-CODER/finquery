"""
FinQuery Evaluation Script
==========================
Tests the agent against 20 ground-truth questions.
Measures: correctness, SQL validity, response time, chart generation.

Usage:
    python backend/eval.py                  # run all tests
    python backend/eval.py --verbose        # show full answers
    python backend/eval.py --category sql   # run only SQL tests
"""

import sys
import os
import time
import json
import argparse
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agent import process_query
from backend.config import DB_PATH


# ─────────────────────────────────────────────
# EVAL TEST CASES
# ─────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "T01",
        "category": "retrieval",
        "question": "How many companies are in the database?",
        "must_contain": ["20"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "companies" in sql.lower(),
    },
    {
        "id": "T02",
        "category": "retrieval",
        "question": "List all sectors available in the database",
        "must_contain": ["IT", "Banking", "Defence"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "sector" in sql.lower(),
    },
    {
        "id": "T03",
        "category": "retrieval",
        "question": "Which stocks are classified as smallcap?",
        "must_contain": ["smallcap"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "smallcap" in sql.lower() or "market_cap" in sql.lower(),
    },
    {
        "id": "T04",
        "category": "aggregation",
        "question": "What is the average closing price of TCS?",
        "must_contain": ["TCS"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "tcs" in sql.lower() and ("avg" in sql.lower() or "average" in sql.lower()),
    },
    {
        "id": "T05",
        "category": "aggregation",
        "question": "Which stock has the highest average volume?",
        "must_contain": [],
        "must_have_sql": True,
        "must_have_chart": True,
        "sql_check": lambda sql: "volume" in sql.lower() and "avg" in sql.lower(),
    },
    {
        "id": "T06",
        "category": "aggregation",
        "question": "What is the total trading volume for the Banking sector?",
        "must_contain": ["Banking"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "banking" in sql.lower() and "volume" in sql.lower(),
    },
    {
        "id": "T07",
        "category": "ranking",
        "question": "Top 5 stocks by market cap",
        "must_contain": [],
        "must_have_sql": True,
        "must_have_chart": True,
        "sql_check": lambda sql: "market_cap" in sql.lower() and "limit" in sql.lower(),
    },
    {
        "id": "T08",
        "category": "ranking",
        "question": "Which 3 stocks had the highest price change percentage last week?",
        "must_contain": [],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "price_change_pct" in sql.lower() and "limit" in sql.lower(),
    },
    {
        "id": "T09",
        "category": "ranking",
        "question": "Show all defence sector stocks ranked by volatility",
        "must_contain": ["Defence"],
        "must_have_sql": True,
        "must_have_chart": True,
        "sql_check": lambda sql: "defence" in sql.lower() and "volatility" in sql.lower(),
    },
    {
        "id": "T10",
        "category": "comparison",
        "question": "Compare average volatility of largecap vs midcap stocks",
        "must_contain": ["largecap", "midcap"],
        "must_have_sql": True,
        "must_have_chart": True,
        "sql_check": lambda sql: "market_cap" in sql.lower() and "volatility" in sql.lower(),
    },
    {
        "id": "T11",
        "category": "comparison",
        "question": "Which has higher average RSI — IT sector or Banking sector?",
        "must_contain": ["IT", "Banking"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "rsi" in sql.lower() and "sector" in sql.lower(),
    },
    {
        "id": "T12",
        "category": "comparison",
        "question": "Compare the average closing price of BEL and HAL",
        "must_contain": ["BEL", "HAL"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "bel" in sql.lower() and "hal" in sql.lower(),
    },
    {
        "id": "T13",
        "category": "filtering",
        "question": "Show me all NIFTY50 stocks in the database",
        "must_contain": ["NIFTY50"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "nifty50" in sql.lower() or "nifty 50" in sql.lower() or "index_name" in sql.lower(),
    },
    {
        "id": "T14",
        "category": "filtering",
        "question": "Which stocks had a positive price change last week?",
        "must_contain": [],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "price_change_pct" in sql.lower() and ">" in sql,
    },
    {
        "id": "T15",
        "category": "filtering",
        "question": "Show stocks where RSI is above 60",
        "must_contain": [],
        "must_have_sql": True,
        "must_have_chart": True,
        "sql_check": lambda sql: "rsi" in sql.lower() and "60" in sql,
    },
    {
        "id": "T16",
        "category": "time",
        "question": "What was Reliance's closing price on the most recent trading day?",
        "must_contain": ["RELIANCE"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "reliance" in sql.lower() and "close" in sql.lower(),
    },
    {
        "id": "T17",
        "category": "time",
        "question": "Show me the highest closing price of INFY in the last 30 days",
        "must_contain": ["INFY"],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "infy" in sql.lower() and ("max" in sql.lower() or "high" in sql.lower()),
    },
    {
        "id": "T18",
        "category": "join",
        "question": "Show average volatility by sector using stock metrics",
        "must_contain": [],
        "must_have_sql": True,
        "must_have_chart": True,
        "sql_check": lambda sql: "join" in sql.lower() and "sector" in sql.lower(),
    },
    {
        "id": "T19",
        "category": "join",
        "question": "Which company name has the highest RSI this week?",
        "must_contain": [],
        "must_have_sql": True,
        "must_have_chart": False,
        "sql_check": lambda sql: "join" in sql.lower() and "rsi" in sql.lower(),
    },
    {
        "id": "T20",
        "category": "edge",
        "question": "What is the schema of the stock_prices table?",
        "must_contain": ["date", "ticker", "close"],
        "must_have_sql": False,
        "must_have_chart": False,
        "sql_check": None,
    },
]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def is_valid_sql(sql: str) -> bool:
    if not sql:
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(sql)
        conn.close()
        return True
    except Exception:
        return False


def run_test(test: dict, verbose: bool = False) -> dict:
    start = time.time()
    result = process_query(test["question"], session_id=f"eval_{test['id']}")
    elapsed = round(time.time() - start, 2)

    answer = result.get("answer", "").lower()
    sql = result.get("sql", "")
    chart = result.get("chart_json")
    error = result.get("error")

    failures = []

    for keyword in test["must_contain"]:
        if keyword.lower() not in answer:
            failures.append(f"missing keyword '{keyword}' in answer")

    if test["must_have_sql"] and not sql:
        failures.append("no SQL extracted")

    if sql and not is_valid_sql(sql):
        failures.append("SQL is invalid (execution error)")

    if test["sql_check"] and sql:
        try:
            if not test["sql_check"](sql):
                failures.append("SQL failed logic check")
        except Exception:
            failures.append("SQL check threw exception")

    if test["must_have_chart"] and not chart:
        failures.append("no chart generated")

    if error:
        failures.append(f"agent error: {error[:80]}")

    passed = len(failures) == 0

    if verbose:
        print(f"\n{'='*60}")
        print(f"[{test['id']}] {test['question']}")
        print(f"Answer: {result.get('answer', '')[:300]}")
        print(f"SQL: {sql[:200] if sql else 'None'}")
        print(f"Chart: {'✅' if chart else '❌'}")
        print(f"Time: {elapsed}s")
        if failures:
            print(f"FAILURES: {failures}")

    return {
        "id": test["id"],
        "category": test["category"],
        "question": test["question"],
        "passed": passed,
        "failures": failures,
        "elapsed": elapsed,
        "has_sql": bool(sql),
        "has_chart": bool(chart),
        "sql_valid": is_valid_sql(sql) if sql else None,
    }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Show full answers")
    parser.add_argument("--category", type=str, default=None, help="Filter by category")
    parser.add_argument("--output", type=str, default=None, help="Save results to JSON file")
    args = parser.parse_args()

    tests = TEST_CASES
    if args.category:
        tests = [t for t in tests if t["category"] == args.category]

    print(f"\n🧪 FinQuery Eval — {len(tests)} tests")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'─'*60}")

    results = []
    passed = 0

    for i, test in enumerate(tests):
        print(f"[{i+1}/{len(tests)}] {test['id']} — {test['question'][:55]}...", end=" ", flush=True)
        res = run_test(test, verbose=args.verbose)
        results.append(res)

        if res["passed"]:
            passed += 1
            print(f"✅ ({res['elapsed']}s)")
        else:
            print(f"❌ ({res['elapsed']}s) → {', '.join(res['failures'])}")

    total = len(tests)
    pct = round(passed / total * 100, 1)

    print(f"\n{'='*60}")
    print(f"📊 RESULTS: {passed}/{total} passed ({pct}%)")
    print(f"{'─'*60}")

    categories = sorted(set(t["category"] for t in tests))
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_passed = sum(1 for r in cat_results if r["passed"])
        print(f"  {cat:<15} {cat_passed}/{len(cat_results)}")

    avg_time = round(sum(r["elapsed"] for r in results) / len(results), 2)
    sql_rate = round(sum(1 for r in results if r["has_sql"]) / total * 100, 1)
    chart_rate = round(sum(1 for r in results if r["has_chart"]) / total * 100, 1)
    valid_sql_rate = round(
        sum(1 for r in results if r["sql_valid"] is True) /
        max(sum(1 for r in results if r["sql_valid"] is not None), 1) * 100, 1
    )

    print(f"\n  Avg response time : {avg_time}s")
    print(f"  SQL extraction    : {sql_rate}%")
    print(f"  Valid SQL         : {valid_sql_rate}%")
    print(f"  Chart generation  : {chart_rate}%")

    if pct >= 85:
        grade = "🟢 PRODUCTION READY"
    elif pct >= 70:
        grade = "🟡 GOOD — minor fixes needed"
    elif pct >= 50:
        grade = "🟠 FAIR — needs improvement"
    else:
        grade = "🔴 NEEDS WORK"

    print(f"\n  Grade: {grade}")
    print(f"{'='*60}\n")

    if args.output:
        with open(args.output, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "passed": passed,
                "total": total,
                "score_pct": pct,
                "avg_time": avg_time,
                "results": results
            }, f, indent=2)
        print(f"Results saved to {args.output}")

    return pct


if __name__ == "__main__":
    main()