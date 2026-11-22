-- =====================================================================
-- SCRIPT: customer_behavior_queries.sql
-- PROJECT: Customer Behavior Analysis
-- DESCRIPTION: Production-grade analytical SQL queries evaluating customer lifetime spend,
--              RFM segmentation, cohort retention, channel preferences, and 80/20 Pareto distribution.
-- =====================================================================

-- ---------------------------------------------------------------------
-- QUERY 1: Top 10 High-Value VIP Customers
-- Business Question: Who are our top spending customers, what is their average order size,
--                    and what membership tier do they hold?
-- ---------------------------------------------------------------------
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


-- ---------------------------------------------------------------------
-- QUERY 2: Spending Behavior Across Income Brackets
-- Business Question: How does purchasing power vary across customer income brackets,
--                    and which tier delivers the highest aggregate revenue?
-- ---------------------------------------------------------------------
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


-- ---------------------------------------------------------------------
-- QUERY 3: Preferred Sales Channel & Multi-Channel Penetration
-- Business Question: What share of transactions and revenue flows through Mobile App,
--                    Web, and In-Store channels?
-- ---------------------------------------------------------------------
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


-- ---------------------------------------------------------------------
-- QUERY 4: RFM Scoring and Behavioral Customer Segmentation
-- Business Question: Segment customers into Champions, Loyalists, At Risk,
--                    and Lost using NTILE(4) quartile ranking over Recency, Frequency, and Monetary metrics.
-- ---------------------------------------------------------------------
WITH Customer_RFM_Raw AS (
    SELECT 
        c.Customer_ID,
        c.City,
        c.Membership_Level,
        -- Recency: Days since last transaction relative to benchmark 2025-11-01
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
        -- Recency: Lower days = higher score (Quartile 4 is most recent)
        NTILE(4) OVER (ORDER BY Recency_Days DESC) AS R_Score,
        -- Frequency: Higher count = higher score
        NTILE(4) OVER (ORDER BY Frequency ASC) AS F_Score,
        -- Monetary: Higher spend = higher score
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
        (R_Score + F_Score + M_Score) AS RFM_Total,
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


-- ---------------------------------------------------------------------
-- QUERY 5: Churn Risk Identification & Intervention Target List
-- Business Question: Find high-spending customers (top 20%) who have not purchased in over 180 days.
-- ---------------------------------------------------------------------
WITH Customer_Recency_Rank AS (
    SELECT 
        c.Customer_ID,
        c.City,
        c.Membership_Level,
        CAST(JULIANDAY('2025-11-01') - JULIANDAY(MAX(t.Transaction_Date)) AS INTEGER) AS Days_Since_Last_Purchase,
        COUNT(t.Transaction_ID) AS Total_Transactions,
        ROUND(SUM(t.Purchase_Amount), 2) AS Total_Spend,
        PERCENT_RANK() OVER (ORDER BY SUM(t.Purchase_Amount) ASC) AS Spend_Percentile
    FROM customers c
    INNER JOIN transactions t ON c.Customer_ID = t.Customer_ID
    GROUP BY c.Customer_ID, c.City, c.Membership_Level
)
SELECT 
    Customer_ID,
    City,
    Membership_Level,
    Days_Since_Last_Purchase,
    Total_Transactions,
    Total_Spend,
    ROUND(Spend_Percentile * 100, 1) AS Spend_Percentile_Rank
FROM Customer_Recency_Rank
WHERE Spend_Percentile >= 0.80 AND Days_Since_Last_Purchase > 180
ORDER BY Total_Spend DESC
LIMIT 15;


-- ---------------------------------------------------------------------
-- QUERY 6: Pareto 80/20 Revenue Contribution
-- Business Question: What percentage of total revenue is generated by each cumulative decile of customers?
-- ---------------------------------------------------------------------
WITH Customer_Totals AS (
    SELECT 
        Customer_ID,
        ROUND(SUM(Purchase_Amount), 2) AS Spend
    FROM transactions
    GROUP BY Customer_ID
),
Deciles AS (
    SELECT 
        Customer_ID,
        Spend,
        NTILE(10) OVER (ORDER BY Spend DESC) AS Decile
    FROM Customer_Totals
)
SELECT 
    Decile,
    COUNT(Customer_ID) AS Customers_In_Decile,
    ROUND(SUM(Spend), 2) AS Decile_Revenue,
    ROUND(SUM(Spend) * 100.0 / (SELECT SUM(Spend) FROM Customer_Totals), 2) AS Decile_Revenue_Pct,
    ROUND(SUM(SUM(Spend)) OVER (ORDER BY Decile ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 / (SELECT SUM(Spend) FROM Customer_Totals), 2) AS Cumulative_Revenue_Pct
FROM Deciles
GROUP BY Decile
ORDER BY Decile ASC;
