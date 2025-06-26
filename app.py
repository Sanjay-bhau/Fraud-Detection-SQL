# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from fraud import (
    get_transaction_data,
    get_outliers_std,
    get_outliers_iqr,
    assign_risk_score
)

# --- DATABASE CONFIG ---
DB_URI = "postgresql://fraud_detection_99dp_user:UvlgVzIc44opPE60guodiLy6ywZ1XYLa@dpg-d1e3k1p5pdvs73f5pq7g-a.oregon-postgres.render.com/fraud_detection_99dp"
engine = create_engine(DB_URI)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Credit Card Fraud Detection Dashboard", layout="wide")
st.title("💳 Credit Card Fraud Detection Dashboard")

# --- SIDEBAR ---
st.sidebar.header("🔍 Filters")
cardholder_id = st.sidebar.selectbox("Select Cardholder ID", options=["All"] + list(range(1, 26)))
method = st.sidebar.radio("Outlier Detection Method", ["Standard Deviation", "IQR"])

# --- LOAD DATA ---
st.info("Loading transactions from database...")
try:
    df = get_transaction_data(engine, cardholder_id)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])

# --- DATE FILTER ---
start_date = st.sidebar.date_input("Start Date", df['date'].min().date())
end_date = st.sidebar.date_input("End Date", df['date'].max().date())
df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]

# --- OUTLIER DETECTION ---
if method == "Standard Deviation":
    df = get_outliers_std(df)  # This adds 'outlier_std' column to df
    df['outlier'] = df['outlier_std']  # unify column name
else:
    df = get_outliers_iqr(df)  # This adds 'outlier_iqr' column to df
    df['outlier'] = df['outlier_iqr']  # unify column name

outliers_df = df[df['outlier']]


# --- RISK SCORING ---
df = assign_risk_score(df)
outliers_df = df[df['outlier']] if 'outlier' in df.columns else pd.DataFrame()

# --- DASHBOARD TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🚩 Outliers", "📋 Raw Data"])

with tab1:
    st.metric("Total Transactions", len(df))
    st.metric("Outliers Detected", len(outliers_df))
    st.metric("Total Suspicious ₹", int(outliers_df['amount'].sum()))
    st.plotly_chart(px.histogram(df, x='amount', nbins=50, title='Transaction Amount Distribution'), use_container_width=True)

with tab2:
    if not outliers_df.empty and 'date' in df.columns:
        st.plotly_chart(
            px.scatter(outliers_df, x='date', y='amount', color='risk_score', hover_data=['name', 'category'],
                       title='Outlier Transactions by Risk Score'), use_container_width=True)
    else:
        st.warning("No outlier data available for plotting.")

    st.subheader("🕒 Early Hour Transactions (7–9 AM)")
    df['time'] = df['date'].dt.time
    early_df = df[df['time'].between(pd.to_datetime("07:00:00").time(), pd.to_datetime("09:00:00").time())]
    st.plotly_chart(px.scatter(early_df, x='date', y='amount', color='category', size='amount', title='Early Hour Transactions'), use_container_width=True)

with tab3:
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

# --- DOWNLOAD ---
if not outliers_df.empty:
    st.sidebar.download_button("Download Suspicious Transactions (CSV)", outliers_df.to_csv(index=False), file_name="suspicious_transactions.csv")
