"""
Module: rfm_segmentation.py
Project: Customer Behavior Analysis
Author: Portfolio Project
Description: Conducts RFM scoring, segments customers into actionable behavioral cohorts,
             and produces publication-quality charts in visualizations/.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10

def perform_rfm_analysis(clean_cust_csv: str, viz_dir: str):
    print("=" * 65)
    print("CUSTOMER BEHAVIOR & RFM SEGMENTATION PIPELINE")
    print("=" * 65)
    
    df = pd.read_csv(clean_cust_csv)
    os.makedirs(viz_dir, exist_ok=True)

    # Filter out customers with 0 orders for RFM scoring
    active_mask = df["Total_Orders"] > 0
    active_df = df[active_mask].copy()

    # RFM Scoring using quantiles (1 to 4)
    # Recency: Lower days = higher score (inverted)
    active_df["R_Score"] = pd.qcut(active_df["Recency_Days"], q=4, labels=[4, 3, 2, 1]).astype(int)
    # Frequency: higher = higher score
    active_df["F_Score"] = pd.qcut(active_df["Total_Orders"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
    # Monetary: higher = higher score
    active_df["M_Score"] = pd.qcut(active_df["Total_Spend"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)

    def assign_segment(row):
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 3 and f >= 3:
            return "Loyal Customers"
        elif r >= 3 and f < 3:
            return "Potential Loyalists"
        elif r <= 2 and f >= 3:
            return "At Risk / Slipping"
        elif r <= 2 and f <= 2 and m >= 3:
            return "Hibernating"
        else:
            return "Lost / Inactive"

    active_df["RFM_Segment"] = active_df.apply(assign_segment, axis=1)

    # Aggregate by Segment
    seg_summary = active_df.groupby("RFM_Segment").agg(
        Customers=("Customer_ID", "count"),
        Total_Revenue=("Total_Spend", "sum"),
        Avg_Spend=("Total_Spend", "mean"),
        Avg_Orders=("Total_Orders", "mean"),
        Avg_Recency=("Recency_Days", "mean")
    ).reset_index()

    seg_summary["Customer_Pct"] = (seg_summary["Customers"] / len(active_df)) * 100
    seg_summary["Revenue_Pct"] = (seg_summary["Total_Revenue"] / active_df["Total_Spend"].sum()) * 100
    seg_summary = seg_summary.sort_values(by="Total_Revenue", ascending=False)

    print("\n--- RFM SEGMENT METRICS SUMMARY ---")
    print(seg_summary.to_string(index=False))

    # -------------------------------------------------------------
    # CHART 1: Customer Segment Distribution (Customers vs Revenue)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 6))
    y_pos = np.arange(len(seg_summary))
    height = 0.35

    b1 = ax.barh(y_pos - height/2, seg_summary["Customer_Pct"], height, label="% of Customers", color="#3b82f6")
    b2 = ax.barh(y_pos + height/2, seg_summary["Revenue_Pct"], height, label="% of Revenue", color="#10b981")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(seg_summary["RFM_Segment"], weight="bold", fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Percentage (%)", weight="bold", labelpad=10)
    ax.set_title("Customer Base Share vs. Revenue Contribution by RFM Segment", fontsize=14, weight="bold", pad=15)
    ax.legend(frameon=True, loc="lower right")

    for b in b1:
        w = b.get_width()
        ax.text(w + 0.6, b.get_y() + b.get_height()/2, f"{w:.1f}%", va="center", ha="left", fontsize=9, color="#1e3a8a", weight="bold")
    for b in b2:
        w = b.get_width()
        ax.text(w + 0.6, b.get_y() + b.get_height()/2, f"{w:.1f}%", va="center", ha="left", fontsize=9, color="#065f46", weight="bold")

    ax.set_xlim(0, max(seg_summary["Customer_Pct"].max(), seg_summary["Revenue_Pct"].max()) * 1.20)
    plt.tight_layout()
    c1 = os.path.join(viz_dir, "01_customer_segment_distribution.png")
    plt.savefig(c1, dpi=300)
    plt.close()
    print(f"Saved: {c1}")

    # -------------------------------------------------------------
    # CHART 2: Spending by Income Bracket
    # -------------------------------------------------------------
    income_order = ["Low", "Medium", "High", "Very High"]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(x="Income_Bracket", y="Total_Spend", data=active_df, order=income_order,
                palette="Blues", ax=ax, showmeans=True,
                meanprops={"marker":"D", "markerfacecolor":"red", "markeredgecolor":"red"})
    ax.set_title("Customer Total Spend Distribution Across Income Brackets", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel("Household Income Bracket", weight="bold", labelpad=10)
    ax.set_ylabel("Total Lifetime Spend in USD ($)", weight="bold", labelpad=10)
    ax.yaxis.set_major_formatter("${x:,.0f}")
    
    # Annotate median values
    for i, inc in enumerate(income_order):
        median_val = active_df[active_df["Income_Bracket"] == inc]["Total_Spend"].median()
        ax.text(i, median_val + 20, f"Med: ${median_val:,.0f}", ha="center", weight="bold", color="#1f2937", fontsize=9)

    plt.tight_layout()
    c2 = os.path.join(viz_dir, "02_spending_by_income_bracket.png")
    plt.savefig(c2, dpi=300)
    plt.close()
    print(f"Saved: {c2}")

    # -------------------------------------------------------------
    # CHART 3: Purchase Frequency Distribution
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.5))
    freq_counts = active_df["Total_Orders"].value_counts().sort_index()
    bars = ax.bar(freq_counts.index, freq_counts.values, color="#6366f1", edgecolor="#374151", width=0.6)
    ax.set_title("Customer Purchase Frequency Distribution (Order Count per Customer)", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel("Number of Completed Transactions", weight="bold", labelpad=10)
    ax.set_ylabel("Number of Customers", weight="bold", labelpad=10)
    ax.set_xticks(freq_counts.index)

    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + 3, f"{h}", ha="center", va="bottom", weight="bold", fontsize=9)

    ax.set_ylim(0, max(freq_counts.values) * 1.15)
    plt.tight_layout()
    c3 = os.path.join(viz_dir, "03_purchase_frequency_distribution.png")
    plt.savefig(c3, dpi=300)
    plt.close()
    print(f"Saved: {c3}")

    # -------------------------------------------------------------
    # CHART 4: RFM Revenue Contribution Breakdown
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    colors_pie = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#6b7280"]
    wedges, texts, autotexts = ax.pie(
        seg_summary["Total_Revenue"],
        labels=seg_summary["RFM_Segment"],
        autopct="%1.1f%%",
        startangle=140,
        colors=colors_pie[:len(seg_summary)],
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
        textprops=dict(weight="bold", fontsize=10)
    )
    for at in autotexts:
        at.set_color("white")
    ax.set_title("Share of Aggregate Revenue by RFM Behavioral Segment", fontsize=14, weight="bold", pad=15)
    plt.tight_layout()
    c4 = os.path.join(viz_dir, "04_rfm_revenue_contribution.png")
    plt.savefig(c4, dpi=300)
    plt.close()
    print(f"Saved: {c4}")

    # -------------------------------------------------------------
    # CHART 5: Customer Tenure vs. Total Spend by Membership Level
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 6))
    tier_palette = {"Bronze": "#cd7f32", "Silver": "#94a3b8", "Gold": "#eab308", "Platinum": "#6366f1"}
    sns.scatterplot(
        data=active_df,
        x="Tenure_Days",
        y="Total_Spend",
        hue="Membership_Level",
        palette=tier_palette,
        style="Membership_Level",
        s=60,
        alpha=0.75,
        ax=ax
    )
    ax.set_title("Customer Account Tenure vs. Lifetime Spend by Loyalty Tier", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel("Account Tenure (Days Since Registration)", weight="bold", labelpad=10)
    ax.set_ylabel("Total Spend in USD ($)", weight="bold", labelpad=10)
    ax.yaxis.set_major_formatter("${x:,.0f}")
    ax.legend(title="Membership Level", frameon=True, loc="upper left")

    plt.tight_layout()
    c5 = os.path.join(viz_dir, "05_loyalty_tenure_vs_spend.png")
    plt.savefig(c5, dpi=300)
    plt.close()
    print(f"Saved: {c5}")
    print("=" * 65)

if __name__ == "__main__":
    c_csv = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\data\cleaned_customer_data.csv")
    v_dir = os.path.abspath(r"C:\Users\saic7\.gemini\antigravity\scratch\Customer-Behavior-Analysis\visualizations")
    perform_rfm_analysis(c_csv, v_dir)
