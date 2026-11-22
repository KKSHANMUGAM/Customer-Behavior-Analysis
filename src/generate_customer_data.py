"""
Script: generate_customer_data.py
Project: Customer Behavior Analysis
Author: Portfolio Project
Description: Synthesizes a realistic e-commerce customer demographic and multi-order transaction 
             dataset with intentional anomalies and dirty records for analytics and SQL querying.
"""

import os
import random
import numpy as np
import pandas as pd

def generate_customer_datasets(cust_out: str, trans_out: str, seed: int = 101, num_customers: int = 1200, num_transactions: int = 4200):
    np.random.seed(seed)
    random.seed(seed)

    # 1. Generate Customers
    customer_ids = [f"CUST-{1000 + i}" for i in range(1, num_customers + 1)]
    genders = ["Male", "Female", "Other"]
    incomes = ["Low", "Medium", "High", "Very High"]
    categories = ["Electronics", "Fashion", "Home & Living", "Beauty & Health", "Sports & Outdoors"]
    membership_levels = ["Bronze", "Silver", "Gold", "Platinum"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Seattle", "Austin", "Denver"]

    cust_rows = []
    start_date = pd.Timestamp("2022-01-01")
    end_date = pd.Timestamp("2024-12-31")
    days_span = (end_date - start_date).days

    for cid in customer_ids:
        age = int(np.random.normal(loc=36, scale=12))
        age = max(18, min(75, age))
        
        gender = random.choice(genders)
        # Introduce casing/format anomalies
        if random.random() < 0.05:
            gender = gender.lower()
        elif random.random() < 0.03:
            gender = gender[0] # 'M' or 'F'
            
        income = np.random.choice(incomes, p=[0.25, 0.40, 0.25, 0.10])
        pref_cat = random.choice(categories)
        mem_lvl = np.random.choice(membership_levels, p=[0.45, 0.30, 0.18, 0.07])
        city = random.choice(cities)
        
        signup_date = start_date + pd.Timedelta(days=random.randint(0, days_span))
        satisfaction = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.10, 0.25, 0.38, 0.22])
        app_hours = round(max(0.5, np.random.gamma(shape=2.5, scale=3.0)), 1)

        cust_rows.append({
            "Customer_ID": cid,
            "Age": age,
            "Gender": gender,
            "City": city,
            "Income_Bracket": income,
            "Join_Date": signup_date.strftime("%Y-%m-%d"),
            "Preferred_Category": pref_cat,
            "Membership_Level": mem_lvl,
            "Satisfaction_Score": satisfaction,
            "App_Usage_Hours_Month": app_hours
        })

    df_cust = pd.DataFrame(cust_rows)

    # Introduce duplicates
    dup_cust = df_cust.sample(n=20, random_state=seed)
    df_cust = pd.concat([df_cust, dup_cust], ignore_index=True)

    # Introduce missing values
    miss_age = np.random.choice(df_cust.index, size=30, replace=False)
    df_cust.loc[miss_age, "Age"] = np.nan

    miss_inc = np.random.choice(df_cust.index, size=35, replace=False)
    df_cust.loc[miss_inc, "Income_Bracket"] = np.nan

    miss_sat = np.random.choice(df_cust.index, size=25, replace=False)
    df_cust.loc[miss_sat, "Satisfaction_Score"] = np.nan

    df_cust = df_cust.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    # 2. Generate Transactions linked to Customers
    trans_rows = []
    t_start = pd.Timestamp("2023-01-01")
    t_end = pd.Timestamp("2025-10-31")
    t_span = (t_end - t_start).days
    
    pay_types = ["Credit Card", "Debit Card", "Digital Wallet", "BNPL (Buy Now Pay Later)"]
    channels = ["Mobile App", "Web", "In-Store"]

    for t_idx in range(1, num_transactions + 1):
        tid = f"TXN-{100000 + t_idx}"
        cid = random.choice(customer_ids)
        t_date = t_start + pd.Timedelta(days=random.randint(0, t_span))
        cat = random.choice(categories)
        
        # Spend follows lognormal distribution
        base_amt = np.random.lognormal(mean=4.2, sigma=0.8)
        amt = round(max(10.0, min(2200.0, base_amt)), 2)
        
        pay = random.choice(pay_types)
        chan = np.random.choice(channels, p=[0.55, 0.35, 0.10])
        
        # Items bought
        items_count = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.45, 0.25, 0.15, 0.08, 0.04, 0.03])

        trans_rows.append({
            "Transaction_ID": tid,
            "Customer_ID": cid,
            "Transaction_Date": t_date.strftime("%Y-%m-%d"),
            "Product_Category": cat,
            "Purchase_Amount": amt,
            "Items_Count": items_count,
            "Payment_Type": pay,
            "Channel": chan
        })

    df_trans = pd.DataFrame(trans_rows)

    # Introduce duplicate transactions
    dup_trans = df_trans.sample(n=35, random_state=seed)
    df_trans = pd.concat([df_trans, dup_trans], ignore_index=True)

    # Introduce missing Channel
    miss_chan = np.random.choice(df_trans.index, size=40, replace=False)
    df_trans.loc[miss_chan, "Channel"] = np.nan

    df_trans = df_trans.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    os.makedirs(os.path.dirname(cust_out), exist_ok=True)
    os.makedirs(os.path.dirname(trans_out), exist_ok=True)

    df_cust.to_csv(cust_out, index=False)
    df_trans.to_csv(trans_out, index=False)
    print(f"Exported raw customer dataset ({len(df_cust)} rows) -> {cust_out}")
    print(f"Exported raw transactions dataset ({len(df_trans)} rows) -> {trans_out}")

if __name__ == "__main__":
    c_out = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\data\raw_customer_data.csv")
    t_out = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\data\raw_transactions_data.csv")
    generate_customer_datasets(c_out, t_out)
