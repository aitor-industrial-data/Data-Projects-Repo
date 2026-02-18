# 🧹 The Great Cleaner: SQL Data Wrangling & Profiling Pipeline

![SQL](https://img.shields.io/badge/SQL-SQLite-blue)
![Data Engineering](https://img.shields.io/badge/Data_Engineering-Wrangling-orange)
![Architecture](https://img.shields.io/badge/Architecture-Medallion-success)

## 📌 Project Overview
This project is a comprehensive **SQL Data Wrangling and Profiling pipeline** built on top of the Chinook relational database. It simulates a real-world Data Engineering scenario where raw, inconsistent data (Bronze Layer) needs to be cleaned, standardized (Silver Layer), and finally aggregated into Business-Ready views (Gold Layer) for downstream Analytics and BI teams.



## 🎯 Business Problem
The raw Chinook database contains several data quality issues:
- Inconsistent string formats in CRM data (e.g., phone numbers with brackets, hyphens, and spaces).
- Null values in critical categorical fields.
- Corrupted or anomalous numerical records in the product inventory (e.g., tracks with impossible durations).
- Lack of clear segmentation for B2B vs. B2C customers.

**The goal of this pipeline is to establish a robust Data Quality framework and deliver a clean Data Mart.**

## 🏗️ Architecture & Workflow

The project is structured into three sequential phases, applying the **Medallion Architecture** principles:

### Phase 1: Customer Data Standardization (`01_Silver_Customer_Cleansing.sql`)
**Layer:** Silver 🥈
- **Data Cleansing:** Deep string manipulation using nested `REPLACE` functions to normalize phone numbers for API integration.
- **Handling Nulls:** Strategic use of `COALESCE` to prevent missing values from breaking downstream systems.
- **Business Logic:** Applied `CASE` statements to segment users into `B2C Customer` or `B2B Customer` based on company metadata.

### Phase 2: Inventory Audit & Profiling (`02_Silver_Track_Audit.sql`)
**Layer:** Silver 🥈
- **Data Profiling:** Audited track durations (Milliseconds) to identify outliers (< 10s or > 1h) and flagged them as `Corrupted` to prevent skewed aggregations.
- **Window Functions:** Utilized `COUNT() OVER(PARTITION BY ...)` to dynamically categorize albums into 'EP' or 'LP' without collapsing the dataset.
- **Referential Integrity:** Used `LEFT JOIN` to identify orphan tracks without losing data, assigning default values to missing dimensions.

### Phase 3: Business Intelligence Ready (`03_Gold_Sales_Master.sql`)
**Layer:** Gold 🥇
- **Data Mart Creation:** Joined the clean dimensions (`V_Silver_Clean_Customer_Roster` & `V_Silver_Track_Inventory_Audit`) with transactional fact tables (`Invoice` & `InvoiceLine`).
- **KPI Generation:** Calculated `Line_Revenue` and exposed quality flags (`Track_Quality_Flag`) directly to the presentation layer.
- **Outcome:** A highly optimized view ready to be ingested by tools like Power BI or Tableau.

## 🛠️ Tech Stack
- **Database Engine:** SQLite (Chinook DB - Singular Columns Version)
- **Tools:** DB Browser for SQLite / DBeaver / Visual Studio Code
- **Techniques Used:** CTEs, Window Functions, String Parsing, Data Profiling, View Creation, Medallion Architecture.

## 🚀 How to Run
1. Connect to the Chinook SQLite database using your preferred IDE (e.g., DB Browser or DBeaver).
2. Execute the scripts in sequential order:
    - `01_Silver_Customer_Cleansing.sql`
   - `02_Silver_Track_Audit.sql`
   - `03_Gold_Sales_Master.sql`
3. Query the final Gold view to see the results:
   ```sql
   SELECT * FROM V_Gold_Sales_Analytics LIMIT 100;