# 🏆 Master SQL Guide: Engineering Portfolio

This guide documents the technical decisions and advanced logic applied during my SQL training.

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