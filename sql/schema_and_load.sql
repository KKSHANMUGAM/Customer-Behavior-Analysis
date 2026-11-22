-- =====================================================================
-- DATABASE SCHEMA: Customer Analytics Data Warehouse
-- Dialect: SQLite / ANSI SQL-92 Standard
-- =====================================================================

-- Table 1: Dimension Customers
CREATE TABLE IF NOT EXISTS customers (
    Customer_ID VARCHAR(20) PRIMARY KEY,
    Age INTEGER,
    Gender VARCHAR(15),
    City VARCHAR(50),
    Income_Bracket VARCHAR(20),
    Join_Date DATE,
    Preferred_Category VARCHAR(50),
    Membership_Level VARCHAR(20),
    Satisfaction_Score FLOAT,
    App_Usage_Hours_Month FLOAT
);

-- Table 2: Fact Transactions
CREATE TABLE IF NOT EXISTS transactions (
    Transaction_ID VARCHAR(20) PRIMARY KEY,
    Customer_ID VARCHAR(20),
    Transaction_Date DATE,
    Product_Category VARCHAR(50),
    Purchase_Amount DECIMAL(10, 2),
    Items_Count INTEGER,
    Payment_Type VARCHAR(30),
    Channel VARCHAR(30),
    FOREIGN KEY (Customer_ID) REFERENCES customers(Customer_ID)
);

-- Table 3: Customer RFM Aggregated View / Table
CREATE TABLE IF NOT EXISTS customer_rfm_summary (
    Customer_ID VARCHAR(20) PRIMARY KEY,
    Age INTEGER,
    Gender VARCHAR(15),
    City VARCHAR(50),
    Income_Bracket VARCHAR(20),
    Join_Date DATE,
    Preferred_Category VARCHAR(50),
    Membership_Level VARCHAR(20),
    Satisfaction_Score FLOAT,
    App_Usage_Hours_Month FLOAT,
    Total_Spend DECIMAL(12, 2),
    Total_Orders INTEGER,
    Total_Items INTEGER,
    Last_Order_Date DATE,
    First_Order_Date DATE,
    Recency_Days INTEGER,
    Average_Order_Value DECIMAL(10, 2),
    Tenure_Days INTEGER
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_trans_cust ON transactions(Customer_ID);
CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(Transaction_Date);
CREATE INDEX IF NOT EXISTS idx_cust_city ON customers(City);
