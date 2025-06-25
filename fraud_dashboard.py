import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# ----------------------------
# 1. MySQL Connection Details
# ----------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",       # ← change this
    password="sanjay123",   # ← change this
    database="fraud_detection"        # ← use your DB name
)

def run_query(query):
    return pd.read_sql(query, conn)

# ----------------------------
# 2. Streamlit Dashboard Setup
# ----------------------------
st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")
st.title("💳 Fraud Detection Dashboard")

# ----------------------------
# 3. Micro Transactions < ₹2
# ----------------------------
st.header("🔍 Micro-Transactions (Less than ₹2)")

df_micro = run_query("""
    SELECT t.id, t.amount, t.date, ch.name AS card_holder
    FROM transaction_table t
    JOIN credit_card cc ON t.card = cc.card
    JOIN card_holder ch ON cc.id_card_holder = ch.id
    WHERE t.amount < 2
""")

st.dataframe(df_micro)

# ----------------------------
# 4. Early Morning Transactions
# ----------------------------
st.header("⏰ Early Morning Transactions (7AM to 9AM)")

df_morning = run_query("""
    SELECT t.id, t.amount, t.date, ch.name AS card_holder
    FROM transaction_table t
    JOIN credit_card cc ON t.card = cc.card
    JOIN card_holder ch ON cc.id_card_holder = ch.id
    WHERE HOUR(t.date) BETWEEN 7 AND 9
""")

st.dataframe(df_morning)

# ----------------------------
# 5. Suspicious Merchants Chart
# ----------------------------
st.header("⚠️ Top Suspicious Merchants (Most Micro-Transactions)")

df_merchants = run_query("""
    SELECT m.name AS merchant_name, COUNT(*) AS count
    FROM transaction_table t
    JOIN merchant m ON t.id_merchant = m.id
    WHERE t.amount < 2
    GROUP BY m.name
    ORDER BY count DESC
    LIMIT 5
""")

fig = px.bar(df_merchants, x='merchant_name', y='count', title="Top Suspicious Merchants")
st.plotly_chart(fig)
