"""
Module: data_preprocessing.py
Project: Customer Behavior Analysis
Author: Portfolio Project
Description: Data cleaning, missing value imputation, text standardization, 
             RFM feature engineering, and SQLite database storage.
"""

import os
import sqlite3
import pandas as pd
import numpy as np

def preprocess_customer_data(cust_csv: str, trans_csv: str, db_path: str, clean_cust_out: str):
    print("=" * 65)
    print("STEP 1: PREPROCESSING CUSTOMER & TRANSACTION DATA")
    print("=" * 65)

    df_cust = pd.read_csv(cust_csv)
    df_trans = pd.read_csv(trans_csv)
    print(f"Loaded Raw Customers: {len(df_cust)} rows")
    print(f"Loaded Raw Transactions: {len(df_trans)} rows")

    # 1. Deduplication
    cust_dups = df_cust.duplicated(subset=["Customer_ID"]).sum()
    trans_dups = df_trans.duplicated(subset=["Transaction_ID"]).sum()
    print(f"\nDuplicates found: Customers={cust_dups}, Transactions={trans_dups}")
    
    df_cust = df_cust.drop_duplicates(subset=["Customer_ID"], keep="first").copy()
    df_trans = df_trans.drop_duplicates(subset=["Transaction_ID"], keep="first").copy()

    # 2. String Standardization
    # Standardize Gender ('m' -> 'Male', 'f' -> 'Female', casing)
    gender_map = {
        "m": "Male", "male": "Male", "Male": "Male",
        "f": "Female", "female": "Female", "Female": "Female",
        "other": "Other", "Other": "Other"
    }
    df_cust["Gender"] = df_cust["Gender"].astype(str).str.strip().map(lambda x: gender_map.get(x, "Other"))
    
    # Clean text columns
    for col in ["City", "Income_Bracket", "Preferred_Category", "Membership_Level"]:
        df_cust[col] = df_cust[col].astype(str).str.strip()

    # 3. Missing Value Imputation
    # Age: impute with median
    median_age = int(df_cust["Age"].dropna().median())
    df_cust["Age"] = df_cust["Age"].fillna(median_age).astype(int)

    # Income_Bracket: impute with mode
    mode_inc = df_cust["Income_Bracket"].replace("nan", np.nan).mode()[0]
    df_cust["Income_Bracket"] = df_cust["Income_Bracket"].replace("nan", np.nan).fillna(mode_inc)

    # Satisfaction_Score: impute with median
    median_sat = round(float(df_cust["Satisfaction_Score"].dropna().median()), 1)
    df_cust["Satisfaction_Score"] = df_cust["Satisfaction_Score"].fillna(median_sat)

    # Channel in Transactions: impute with mode
    mode_chan = df_trans["Channel"].dropna().mode()[0]
    df_trans["Channel"] = df_trans["Channel"].fillna(mode_chan)

    # 4. Dates
    df_cust["Join_Date"] = pd.to_datetime(df_cust["Join_Date"])
    df_trans["Transaction_Date"] = pd.to_datetime(df_trans["Transaction_Date"])

    # 5. Compute RFM metrics per Customer
    # Benchmark date for recency calculation
    benchmark_date = pd.Timestamp("2025-11-01")
    
    rfm_agg = df_trans.groupby("Customer_ID").agg(
        Total_Spend=("Purchase_Amount", "sum"),
        Total_Orders=("Transaction_ID", "count"),
        Total_Items=("Items_Count", "sum"),
        Last_Order_Date=("Transaction_Date", "max"),
        First_Order_Date=("Transaction_Date", "min")
    ).reset_index()

    rfm_agg["Recency_Days"] = (benchmark_date - rfm_agg["Last_Order_Date"]).dt.days
    rfm_agg["Average_Order_Value"] = (rfm_agg["Total_Spend"] / rfm_agg["Total_Orders"]).round(2)
    rfm_agg["Total_Spend"] = rfm_agg["Total_Spend"].round(2)

    # Merge customer profile with RFM metrics
    df_master = pd.merge(df_cust, rfm_agg, on="Customer_ID", how="left")
    
    # Handle any customers with 0 transactions
    df_master["Total_Spend"] = df_master["Total_Spend"].fillna(0.0)
    df_master["Total_Orders"] = df_master["Total_Orders"].fillna(0).astype(int)
    df_master["Total_Items"] = df_master["Total_Items"].fillna(0).astype(int)
    df_master["Average_Order_Value"] = df_master["Average_Order_Value"].fillna(0.0)
    df_master["Recency_Days"] = df_master["Recency_Days"].fillna(999).astype(int)

    # Calculate Customer Tenure in Days
    df_master["Tenure_Days"] = (benchmark_date - df_master["Join_Date"]).dt.days

    # 6. Save Cleaned Customer Dataset
    os.makedirs(os.path.dirname(clean_cust_out), exist_ok=True)
    df_master.to_csv(clean_cust_out, index=False)
    print(f"\nSaved Cleaned Master Customer Dataset: {clean_cust_out}")

    # 7. Load into SQLite Database for SQL Analysis
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    
    # Save tables into SQLite
    df_cust.to_sql("customers", conn, if_exists="replace", index=False)
    # Convert dates to ISO string for SQLite
    df_trans_sql = df_trans.copy()
    df_trans_sql["Transaction_Date"] = df_trans_sql["Transaction_Date"].dt.strftime("%Y-%m-%d")
    df_trans_sql.to_sql("transactions", conn, if_exists="replace", index=False)
    
    df_master_sql = df_master.copy()
    df_master_sql["Join_Date"] = df_master_sql["Join_Date"].dt.strftime("%Y-%m-%d")
    if "Last_Order_Date" in df_master_sql.columns:
        df_master_sql["Last_Order_Date"] = df_master_sql["Last_Order_Date"].dt.strftime("%Y-%m-%d")
    if "First_Order_Date" in df_master_sql.columns:
        df_master_sql["First_Order_Date"] = df_master_sql["First_Order_Date"].dt.strftime("%Y-%m-%d")
    df_master_sql.to_sql("customer_rfm_summary", conn, if_exists="replace", index=False)

    # Create indexes for fast querying
    cur = conn.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trans_cust ON transactions(Customer_ID);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(Transaction_Date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cust_id ON customers(Customer_ID);")
    conn.commit()
    conn.close()

    print(f"Successfully populated SQLite Database: {db_path}")
    print(f"Tables created: 'customers', 'transactions', 'customer_rfm_summary'")
    print("=" * 65)
    return df_master

if __name__ == "__main__":
    c_csv = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\data\raw_customer_data.csv")
    t_csv = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\data\raw_transactions_data.csv")
    db_p = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\data\customer_analytics.db")
    c_out = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\data\cleaned_customer_data.csv")
    preprocess_customer_data(c_csv, t_csv, db_p, c_out)
