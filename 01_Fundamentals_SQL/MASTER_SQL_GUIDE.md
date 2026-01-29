# Module 01: SQL Fundamentals & Data Architecture
**Status:** Completed ✅ | **Role:** Data Engineer | **Environment:** Remote / Agile

## 🚀 Featured Projects & Exercises

### 1. Advanced Client Analysis (Brazil VIP Project)
* **Goal:** Identify customers in Brazil with spending above the global average.
* **Technical Skill:** Subqueries and filtering by country-specific metrics.
* *See code in:* `advanced-exercises/brazil_vip_project.sql`

### 2. Business Intelligence (Chinook Case Studies)
* **Customer ROI:** Top 5 spenders analysis.
* **Sales Attribution:** Linking Employees to Invoices via `SupportRepId`.
* *See code in:* `advanced-exercises/business_analysis.sql`

## 🛠️ Performance & Optimization Mindset
As a Data Engineer, I prioritize efficiency:
1. **Explain Plan:** Using `EXPLAIN QUERY PLAN` to avoid full table scans.
2. **Indexing:** Understanding when the engine uses `SEARCH` instead of `SCAN`.
3. **Clean Code:** Avoiding `SELECT *` to reduce I/O overhead.

---
## 🏗️ Day 15: Data Architecture & Strategy

A true Data Engineer knows that the tool depends on the data's nature.

### SQL vs NoSQL: The Industrial Case
* **Time-Series Data (e.g., Voltage Sensors):** Best handled by **NoSQL**. High-velocity ingestion and horizontal scaling are priority.
* **Relational Data (e.g., Client Contracts):** Best handled by **SQL**. ACID compliance and data integrity are non-negotiable.

### Analytical Flow (The Big Picture)
1.  **OLTP (SQL):** Where the business happens (Transactions).
2.  **ETL Process:** The bridge where I extract, clean, and optimize data.
3.  **OLAP (Data Warehouse):** Where decisions happen (Analysis).


### Day 16: Data Architecture & Star Schema Design

Today I transformed the **Chinook** relational database into an **OLAP (Analytical)** structure to optimize business queries.

#### Key Achievements:
* **Star Schema Implementation:** Designed and created a central Fact Table and a flattened Dimension Table.
* **Dimension Table (`Dim_Track`):** Denormalized `Track`, `Album`, `Artist`, and `Genre` tables into a single wide table for faster lookups.
* **Fact Table (`Fact_Sales`):** Built a high-granularity fact table by joining `InvoiceLine` and `Invoice` to track sales metrics.
* **Performance Optimization:** Reduced query complexity from 5+ JOINS to a single JOIN between Fact and Dimension.

#### Sample Analytics Query:
I calculated the **Top Artists by Revenue** using the new architecture:
```sql
SELECT dt.ArtistName, sum(fs.unitprice * fs.Quantity) as Revenue
FROM Dim_Track dt
JOIN Fact_Sales fs ON dt.TrackId = fs.TrackId
GROUP BY dt.ArtistName
ORDER BY Revenue DESC;



## Day 18: 📋 Project Overview (Jira Task: CHK-01)
Transformation of the Chinook Relational Database into a Star Schema optimized for Business Intelligence and Analytical queries.

### 🛠️ Tech Stack & Tools
* **SQL IDE:** VS Code / DBeaver.
* **Database:** SQLite (Chinook).
* **Version Control:** Git & GitHub.
* **Communication:** Slack (Mock-up reporting).

### 🚀 Key Deliverables
1. **ERD Analysis:** Identified N:M relationships and resolved them using bridge tables (`InvoiceLine`).
2. **Star Schema Implementation:** - Created `Fact_Sales` for granular transaction tracking.
   - Designed `Dim_Track` to centralize track metadata.
3. **Architecture Optimization:** Denormalized specific fields (Country, Genre) to reduce JOIN overhead.

## 📡 Remote Work Communication (Slack Snippet)
*Daily Update - 2026-01-28:*
> "Hi team, I've completed the architectural migration of the Chinook dataset. The scripts are now available in `/Scripts`. This new Star Schema reduces query complexity for the BI team. Ready for the Data Wrangling phase."

---
*Developed by Aitor - Data Engineering Roadmap 2026*

