"""
Module: sql_analytics.py
Project: Customer Behavior Analysis
Author: Portfolio Project
Description: Executes analytical SQL queries on the customer SQLite database
             and converts query results into structured pandas DataFrames.
"""

import os
import sqlite3
import pandas as pd

def run_sql_queries(db_path: str):
    print("=" * 65)
    print("EXECUTING ADVANCED SQL ANALYTICAL QUERIES ON SQLITE DATABASE")
    print("=" * 65)
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")

    conn = sqlite3.connect(db_path)

    # 1. Top 10 VIP Customers
    q1 = """
    SELECT 
        c.Customer_ID,
        c.City,
        c.Membership_Level,
        c.Income_Bracket,
        COUNT(t.Transaction_ID) AS Total_Orders,
        SUM(t.Items_Count) AS Total_Units_Bought,
        ROUND(SUM(t.Purchase_Amount), 2) AS Lifetime_Spend,
        ROUND(AVG(t.Purchase_Amount), 2) AS Average_Order_Value
    FROM customers c
    INNER JOIN transactions t ON c.Customer_ID = t.Customer_ID
    GROUP BY c.Customer_ID, c.City, c.Membership_Level, c.Income_Bracket
    ORDER BY Lifetime_Spend DESC
    LIMIT 10;
    """
    df1 = pd.read_sql_query(q1, conn)
    print("\n--- QUERY 1: TOP 10 VIP CUSTOMERS BY LIFETIME SPEND ---")
    print(df1.to_string(index=False))

    # 2. Spending Behavior by Income Bracket
    q2 = """
    SELECT 
        c.Income_Bracket,
        COUNT(DISTINCT c.Customer_ID) AS Customer_Count,
        COUNT(t.Transaction_ID) AS Total_Transactions,
        ROUND(SUM(t.Purchase_Amount), 2) AS Aggregate_Revenue,
        ROUND(AVG(t.Purchase_Amount), 2) AS Avg_Transaction_Value,
        ROUND(SUM(t.Purchase_Amount) / COUNT(DISTINCT c.Customer_ID), 2) AS Revenue_Per_Customer
    FROM customers c
    LEFT JOIN transactions t ON c.Customer_ID = t.Customer_ID
    GROUP BY c.Income_Bracket
    ORDER BY Aggregate_Revenue DESC;
    """
    df2 = pd.read_sql_query(q2, conn)
    print("\n--- QUERY 2: PURCHASING METRICS ACROSS INCOME BRACKETS ---")
    print(df2.to_string(index=False))

    # 3. Channel Distribution
    q3 = """
    SELECT 
        t.Channel,
        COUNT(t.Transaction_ID) AS Transaction_Count,
        ROUND(COUNT(t.Transaction_ID) * 100.0 / (SELECT COUNT(*) FROM transactions), 2) AS Transaction_Pct,
        ROUND(SUM(t.Purchase_Amount), 2) AS Total_Revenue,
        ROUND(SUM(t.Purchase_Amount) * 100.0 / (SELECT SUM(Purchase_Amount) FROM transactions), 2) AS Revenue_Pct,
        ROUND(AVG(t.Purchase_Amount), 2) AS Avg_Order_Size
    FROM transactions t
    GROUP BY t.Channel
    ORDER BY Total_Revenue DESC;
    """
    df3 = pd.read_sql_query(q3, conn)
    print("\n--- QUERY 3: TRANSACTION CHANNEL DISTRIBUTION ---")
    print(df3.to_string(index=False))

    # 4. RFM Segmentation via SQL Window Functions
    q4 = """
    WITH Customer_RFM_Raw AS (
        SELECT 
            c.Customer_ID,
            c.City,
            c.Membership_Level,
            CAST(JULIANDAY('2025-11-01') - JULIANDAY(MAX(t.Transaction_Date)) AS INTEGER) AS Recency_Days,
            COUNT(t.Transaction_ID) AS Frequency,
            ROUND(SUM(t.Purchase_Amount), 2) AS Monetary
        FROM customers c
        INNER JOIN transactions t ON c.Customer_ID = t.Customer_ID
        GROUP BY c.Customer_ID, c.City, c.Membership_Level
    ),
    Customer_RFM_Scores AS (
        SELECT 
            Customer_ID,
            City,
            Membership_Level,
            Recency_Days,
            Frequency,
            Monetary,
            NTILE(4) OVER (ORDER BY Recency_Days DESC) AS R_Score,
            NTILE(4) OVER (ORDER BY Frequency ASC) AS F_Score,
            NTILE(4) OVER (ORDER BY Monetary ASC) AS M_Score
        FROM Customer_RFM_Raw
    ),
    Customer_Segmented AS (
        SELECT 
            Customer_ID,
            City,
            Membership_Level,
            Recency_Days,
            Frequency,
            Monetary,
            R_Score,
            F_Score,
            M_Score,
            CASE 
                WHEN R_Score >= 4 AND F_Score >= 4 AND M_Score >= 4 THEN 'Champions'
                WHEN R_Score >= 3 AND F_Score >= 3 THEN 'Loyal Customers'
                WHEN R_Score >= 3 AND F_Score < 3 THEN 'Potential Loyalists'
                WHEN R_Score <= 2 AND F_Score >= 3 THEN 'At Risk / Slipping'
                WHEN R_Score <= 2 AND F_Score <= 2 AND M_Score >= 3 THEN 'Hibernating'
                ELSE 'Lost / Inactive'
            END AS RFM_Segment
        FROM Customer_RFM_Scores
    )
    SELECT 
        RFM_Segment,
        COUNT(Customer_ID) AS Customer_Count,
        ROUND(COUNT(Customer_ID) * 100.0 / (SELECT COUNT(*) FROM Customer_Segmented), 2) AS Customer_Pct,
        ROUND(SUM(Monetary), 2) AS Segment_Revenue,
        ROUND(SUM(Monetary) * 100.0 / (SELECT SUM(Monetary) FROM Customer_Segmented), 2) AS Revenue_Pct,
        ROUND(AVG(Monetary), 2) AS Avg_Spend_Per_Customer,
        ROUND(AVG(Recency_Days), 1) AS Avg_Recency_Days,
        ROUND(AVG(Frequency), 1) AS Avg_Frequency
    FROM Customer_Segmented
    GROUP BY RFM_Segment
    ORDER BY Segment_Revenue DESC;
    """
    df4 = pd.read_sql_query(q4, conn)
    print("\n--- QUERY 4: RFM SEGMENTATION BREAKDOWN (SQL NTILE CTE) ---")
    print(df4.to_string(index=False))

    conn.close()
    print("=" * 65)
    return {"vip": df1, "income": df2, "channel": df3, "rfm": df4}

if __name__ == "__main__":
    db = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\data\customer_analytics.db")
    run_sql_queries(db)
