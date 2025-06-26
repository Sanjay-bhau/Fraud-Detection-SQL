import pandas as pd
import numpy as np
from numpy import mean, std, percentile

# Load transaction data for specific or all cardholders
def get_transaction_data(engine, cardholder_id="All"):
    query = '''
        SELECT a.id, a.name, b.card, c.date, c.amount, e.name as "category"
        FROM public.card_holder a
        JOIN public.credit_card b ON a.id = b.id_card_holder
        JOIN public.transaction c ON b.card = c.card
        JOIN public.merchant d ON c.id_merchant = d.id
        JOIN public.merchant_category e ON d.id_merchant_category = e.id
    '''
    if cardholder_id != "All":
        query += f' WHERE a.id = {cardholder_id}'

    df = pd.read_sql(query, engine, parse_dates=["date"])
    df['time'] = df['date'].dt.time
    return df


# Outlier detection using Standard Deviation
def get_outliers_std(df):
    data_mean, data_std = mean(df['amount']), std(df['amount'])
    cut_off = data_std * 3
    lower, upper = data_mean - cut_off, data_mean + cut_off
    df['outlier_std'] = (df['amount'] < lower) | (df['amount'] > upper)
    return df

def get_outliers_iqr(df):
    q25, q75 = percentile(df['amount'], 25), percentile(df['amount'], 75)
    iqr = q75 - q25
    cut_off = iqr * 1.5
    lower, upper = q25 - cut_off, q75 + cut_off
    df['outlier_iqr'] = (df['amount'] < lower) | (df['amount'] > upper)
    return df



# Detect micro-transactions (used to test stolen cards)
def fraud_transactions(df, threshold=2.0):
    df['micro_fraud'] = df['amount'] < threshold
    return df[df['micro_fraud']]


# Detect early morning transactions (7–9 AM)
def get_early_hour_transactions(df):
    start_time = pd.to_datetime("07:00:00").time()
    end_time = pd.to_datetime("09:00:00").time()
    early_df = df[(df['time'] >= start_time) & (df['time'] <= end_time)]
    return early_df


# Assign risk score (0 to 100) based on amount and time
def assign_risk_score(df):
    def score(row):
        base = 50
        if row['amount'] > 1000:
            base += 25
        if row['amount'] > 5000:
            base += 50
        if pd.to_datetime("00:00:00").time() <= row['time'] <= pd.to_datetime("06:00:00").time():
            base += 20
        if row.get('micro_fraud', False):
            base += 15
        if row.get('outlier_std', False) or row.get('outlier_iqr', False):
            base += 10
        return min(base, 100)

    df['risk_score'] = df.apply(score, axis=1)
    return df
