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