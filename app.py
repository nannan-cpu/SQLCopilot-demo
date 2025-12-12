# app.py
# SQLense: AI Copilot for SQL & Reporting (Credit Card Center Demo)

import os
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---- 基本页面配置 ----
st.set_page_config(
    page_title="SQLense: AI Copilot for SQL & Reporting",
    layout="wide"
)

st.title("🧠 SQLense: AI Copilot for SQL & Reporting")
st.caption("Prototype for a JPMorgan-style credit card analytics copilot")

# ---- 载入环境变量 & OpenAI client ----
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY not found. Please add it to your .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

DB_PATH = "card_transactions.db"

# ---- 提示 LLM 了解数据库结构 ----
SCHEMA_PROMPT = """
You are an expert SQL assistant for a credit card analytics team.

You ONLY output SQL code, no explanation, no markdown, no backticks.

The database is a SQLite database with one main table:

card_transactions(
    transaction_id    INTEGER PRIMARY KEY,
    customer_id       INTEGER,
    state             TEXT,      -- US state code, e.g. NY, CA
    card_type         TEXT,      -- Platinum, Gold, Silver, Freedom, Basic
    channel           TEXT,      -- Online, Branch, Mobile, ATM, POS
    transaction_date  TEXT,      -- 'YYYY-MM-DD'
    amount            REAL,      -- transaction amount in USD
    is_fraud          INTEGER,   -- 0 or 1
    merchant_cat      TEXT,      -- Grocery, Travel, Dining, Fuel, Shopping, etc.
    product_version   TEXT       -- 'A' or 'B' for A/B test
)

Rules:
- Use only this table.
- Use standard SQLite syntax.
- If the question mentions time like "last 30 days", "last 3 months", or "Q3",
  convert it into a filter on transaction_date.
- If the question asks for aggregated metrics, include GROUP BY as needed.
- If the question doesn't specify a limit, add LIMIT 50.
- If the question is ambiguous, make a reasonable assumption.
Return ONLY the final SQL query.
"""

def generate_sql_from_question(question: str) -> str:
    """Call OpenAI to generate SQL from natural language question."""
    messages = [
        {"role": "system", "content": SCHEMA_PROMPT},
        {"role": "user", "content": question}
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 如果你账号不支持可以改成其他可用模型
        messages=messages,
        temperature=0.1,
    )
    sql = response.choices[0].message.content.strip()

    # 清理可能的 ```sql 包裹
    if "```" in sql:
        parts = sql.split("```")
        # 通常 SQL 在中间那段
        for part in parts:
            if "SELECT" in part.upper():
                sql = part
                break
        sql = sql.replace("sql", "").strip()

    return sql

def run_sql(sql: str) -> pd.DataFrame:
    """Run SQL on local SQLite DB and return result as DataFrame."""
    conn = sqlite3.connect("card_transactions.db")
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df

# ---------- Auto validation on query result ----------
def basic_result_validation(df: pd.DataFrame) -> dict:
    """
    Very simple data quality / sanity checks on the query result.
    Returns a dict with a 'summary' list of human-readable messages.
    """
    checks = []

    if df.empty:
        checks.append("⚠️ Query returned 0 rows. Please double-check filters or logic.")
        return {"summary": checks}

    checks.append(f"✅ Query returned {len(df)} rows and {len(df.columns)} columns.")

    # Amount sanity check
    if "amount" in df.columns:
        total = df["amount"].sum()
        checks.append(f"💰 Total amount in result set: ${total:,.2f}")

        if total < 0:
            checks.append("⚠️ Total amount is negative. This may indicate refunds/chargebacks.")
        elif total == 0:
            checks.append("⚠️ Total amount is zero. Check if the query filter is too strict.")

    # Fraud rate sanity check
    if "is_fraud" in df.columns:
        rate = float(df["is_fraud"].mean() * 100)
        checks.append(f"🕵️ Estimated fraud rate in this result: {rate:.2f}%")
        if rate > 10:
            checks.append("🚨 Fraud rate seems unusually high. Consider deeper investigation.")
        elif rate < 0.1:
            checks.append("ℹ️ Fraud rate is very low in this slice. Check if sample size is sufficient.")

    return {"summary": checks}


# ---------- AI analysis & recommendations ----------
def generate_ai_report(question: str, sql: str, df: pd.DataFrame) -> str:
    """
    Ask the LLM to summarize the result and provide business recommendations
    for a credit card analytics / risk team.
    """
    # Use only a small preview to control token usage
    preview = df.head(10).to_markdown(index=False)

    prompt = f"""
You are a senior data analyst in a credit card center (JPMorgan-style).

User business question:
{question}

Executed SQL:
{sql}

Result preview (first 10 rows in markdown table format):
{preview}

Please provide a short English report with the following structure:

1. **What this query is analyzing** (1–2 sentences).
2. **Key insights from the result** (bullet points, focusing on patterns, anomalies, high-risk segments).
3. **Actionable recommendations** for risk management / portfolio strategy
   (e.g., which segments to monitor, potential campaigns, further drill-down analysis).

Keep the tone professional but concise.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


# ---- 页面主体 ----

st.markdown("### Step 1 · Ask a business question")

st.info(
    "This demo uses a synthetic credit card transactions dataset stored in a local SQLite database.\n\n"
    "Try questions like:\n"
    "- What is total transaction volume by state?\n"
    "- Show Platinum card volume by channel.\n"
    "- What is fraud rate by state in the last 30 days?\n"
    "- Compare transaction volume by card_type and merchant_cat.\n"
)

user_question = st.text_input(
    "Type a business question (English only):",
    placeholder="e.g. What is total transaction volume by state in the last 90 days?"
)

generate_button = st.button("Generate & Run SQL")

if generate_button:
    if not user_question.strip():
        st.warning("Please enter a question first.")
        st.stop()

    # Step 2: 调用 OpenAI 生成 SQL
    with st.spinner("Calling AI to generate SQL..."):
        try:
            generated_sql = generate_sql_from_question(user_question)
        except Exception as e:
            st.error(f"Error calling OpenAI API: {e}")
            st.stop()

    # Step 3: 执行 SQL 并展示结果
    with st.spinner("Running SQL on local SQLite database..."):
        try:
            df = run_sql(generated_sql)
        except Exception as e:
            st.error(f"Error running SQL: {e}")
            st.stop()

    
    st.session_state["last_question"] = user_question
    st.session_state["last_sql"] = generated_sql
    st.session_state["last_df"] = df

# ---- Show last result (if exists) ----
if "last_df" in st.session_state:
    df = st.session_state["last_df"]
    generated_sql = st.session_state["last_sql"]
    last_question = st.session_state["last_question"]

    st.markdown("### Step 2 · Generated SQL")
    st.code(generated_sql, language="sql")

    st.markdown("### Step 3 · Query Result")
    st.write(f"Returned **{len(df)}** rows.")
    st.dataframe(df, use_container_width=True)

    # --- Auto validation (data sanity check) ---
    with st.expander("✅ Auto validation on query result"):
        result_check = basic_result_validation(df)
        for line in result_check["summary"]:
            st.write("- ", line)

    # --- Optional AI reporting / recommendations ---
    if not df.empty:
        if st.checkbox("📄 Generate AI analysis & recommendations"):
            with st.spinner("Calling AI to generate analysis / recommendations..."):
                try:
                    report_text = generate_ai_report(
                        question=last_question,
                        sql=generated_sql,
                        df=df,
                    )
                    st.markdown("### Step 4 · AI-generated analysis & recommendations")
                    st.markdown(report_text)
                except Exception as e:
                    st.error(f"Error calling OpenAI for report: {e}")

