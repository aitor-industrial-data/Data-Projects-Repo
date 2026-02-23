# CoffeeKing Analytics: Coffee Shop Investment Optimization (Yelp Dataset)
[Versión en Español](README.md)

## 📌 1. Project Structure and Methodology
This project follows a modular engineering approach to ensure traceability between business requirements and code:

* **[PHASE 01] Project Proposal:** Problem definition, dataset selection, and hypothesis formulation.

    [See: 01_CoffeeKing_Project_Proposal_EN.pdf](/02_SQL_Advanced_Wrangling_and_Testing/02.05_CAPSTONE_CoffeeKing_Yelp/docs/EN/01_CoffeeKing_Project_Proposal_EN.pdf).
* **[PHASE 02] Hypothesis Analysis:** Technical validation through advanced SQL and descriptive statistics.

    [See: /scripts/02a_H1_Rating_Stability.sql](/02_SQL_Advanced_Wrangling_and_Testing/02.05_CAPSTONE_CoffeeKing_Yelp/scripts/02a_H1_Rating_Stability.sql)

    [See: /scripts/02b_H2_Temporal_Behavior.sql](/02_SQL_Advanced_Wrangling_and_Testing/02.05_CAPSTONE_CoffeeKing_Yelp/scripts/02b_H2_Temporal_Behavior.sql)

    [See: /scripts/02c_H3_Analysis.sql](/02_SQL_Advanced_Wrangling_and_Testing/02.05_CAPSTONE_CoffeeKing_Yelp/scripts/02c_H3_Analysis.sql.sql)
* **[PHASE 03] Advanced Analysis & Metrics:** Correlation identification, KPI implementation (PEI/CP), and text processing preparation.

    [See: /docs/EN/03_Deep_Analysis_Insights_EN.md](/02_SQL_Advanced_Wrangling_and_Testing/02.05_CAPSTONE_CoffeeKing_Yelp/docs/EN/03_Deep_Analysis_Insights_EN.md)

    [See: /scripts/03_New_Metrics_Implementation.sql](/02_SQL_Advanced_Wrangling_and_Testing/02.05_CAPSTONE_CoffeeKing_Yelp/scripts/03_New_Metrics_Implementation.sql)
* **[PHASE 04] Final Executive Report:** Consolidation of strategic findings, final KPI validation (PEI/CP), and management recommendations. Completion of the relational engineering cycle.

    [See: 04_Executive_Report_CoffeeKing_EN.md](/02_SQL_Advanced_Wrangling_and_Testing/02.05_CAPSTONE_CoffeeKing_Yelp/docs/EN/04_Presentation_Executive_Report_EN.md).

## 🛠️ 2. Tech Stack
* **Database:** SQLite (`CoffeeKing_Yelp.db`).
* **SQL Management:** DBeaver & DB Browser for SQLite.
* **File Processing:** Git-Bash (JSON to CSV sampling).
* **Documentation Environment:** Visual Studio Code.

## 📁 3. File Structure
* `/scripts/`: SQL Scripts (`02a_H1_Rating_Stability.sql`, `02b_H2_Temporal_Behavior.sql`, etc.)
* `/docs/`: Detailed reports and project proposals.
* `/data/`: (Not uploaded to GitHub) Local database `CoffeeKing_Yelp.db`.
* `/images/`: Data model diagrams and visual documentation. <details style="display:inline"><summary><b>View Entity-Relationship Diagram (ERD)</b></summary><br><img src="./images/01_CoffeeKing_Yelp_Diagram.png" alt="Database Schema" width="800"></details>

## 📊 4. Critical Findings and Hypothesis Validation
After completing the descriptive analysis and attribute correlation using advanced SQL, the initial hypotheses were tested with the following results:

### Hypothesis 1 (H1): Maturity Threshold and Stability
* **Statement:** Businesses with more than 100 reviews reach reputational maturity, converging at **4.0 stars**.
* **Result:** ❌ **REFUTED**.
* **Evidence:** Established venues show an actual average of **3.81 stars**. While data volume provides stability, the market is more demanding than expected.
* **Impact:** The **Elite Benchmark is redefined to 3.8 stars** to adjust success KPIs.

### Hypothesis 2 (H2): Temporal Behavior (Professional Profile)
* **Statement:** Determine if there is a predominantly professional customer profile by analyzing interaction volume on weekdays.
* **Result:** ✅ **CONFIRMED**.
* **Evidence:** Date processing reveals a clear dominance of professional workflow:
    * **Weekdays (M-F):** **70.5%** of activity (705 reviews).
    * **Weekends (S-S):** **29.5%** of activity (295 reviews).
* **Impact:** Business volume is **138% higher** during the week, validating the focus on remote workers.

### Hypothesis 3 (H3): Impact of Services (Wi-Fi vs. Outdoor Seating)
* **Statement:** Identify the determining rating factor: digital infrastructure (Wi-Fi) or physical assets (Outdoor Seating).
* **Result:** ✅ **CONFIRMED (Tech Priority)**.
* **Evidence:** * **Free Wi-Fi:** Average rating of **3.81 stars**, with a net impact of **+0.16 stars** over the global average.
    * **Outdoor Seating:** Marginal reputation improvement (3.69 vs 3.67).
* **Impact:** Priority is recommended for investment in **high-speed connectivity** over outdoor furniture.

## 🔍 5. New Engineering Metrics (KPIs)
To transcend basic descriptive analysis, I have designed and implemented two Key Performance Indicators (KPIs) to quantify "Work-Friendly" business success and tech ROI.

### 1. Professional Engagement Index (PEI)
This index measures a venue's specialization in the professional segment. It is calculated as the ratio between weekday activity versus weekends.
* **Formula:** `PEI = (Total Reviews Weekdays) / (Total Reviews Weekends)`
* **Result:** **2.39**
* **Technical Interpretation:** A value of 2.39 indicates that for every weekend review, nearly 2.4 are generated during the workweek. This confirms a **139% dominance of professional activity**, validating the dataset's suitability for CoffeeKing's target.

### 2. Connectivity Premium (CP)
The CP is a quality differential metric that isolates the impact of free Wi-Fi on the business's perceived reputation.
* **Formula:** `CP = (Avg Rating WiFi-Free Venues) - (Global Market Avg Rating)`
* **Result:** **+0.16 stars**
* **Technical Interpretation:** This value quantifies the "digital competitive advantage." Venues offering free connectivity outperform the market average by 0.16 stars. On a 1-5 scale, this differential is statistically significant for algorithmic recommendation positioning.

---

## 💻 6. Technical Implementation (SQL)
To ensure reproducibility and avoid ambiguity, a unified query was implemented using **CTEs (Common Table Expressions)** to process strategic KPIs in a single disk read:

```sql
/* Strategic KPI Computation (CP and PEI)
   This block unifies business logic to ensure data integrity.
*/
WITH Metrics_Computation AS (
    SELECT 
        -- Average rating for venues with connectivity (Free Wi-Fi)
        AVG(CASE WHEN b."attributes.WiFi" LIKE '%free%' THEN b.stars END) as wifi_rating,
        -- Global market average rating
        AVG(b.stars) as global_rating,
        -- Activity ratio: Weekdays vs Weekends
        -- The * 1.0 factor ensures division is not treated as an integer.
        COUNT(CASE WHEN strftime('%w', r.date) NOT IN ('0', '6') THEN 1 END) * 1.0 as weekday_count,
        COUNT(CASE WHEN strftime('%w', r.date) IN ('0', '6') THEN 1 END) as weekend_count
    FROM business b
    JOIN review r ON b.business_id = r.business_id
)
SELECT 
    -- Star differential provided by connectivity
    ROUND(wifi_rating - global_rating, 2) AS connectivity_premium,
    -- Professional Engagement Index (Targeting)
    ROUND(weekday_count / weekend_count, 2) AS professional_index
FROM Metrics_Computation;
```

## 🚀 7. Engineering Roadmap and Future Vision

While the current scope of the CoffeeKing project concludes with SQL validation, I have designed a technical roadmap for system scalability. This roadmap represents the natural evolution toward advanced data architectures:

### Distributed Processing (Big Data)
* **Migration to Apache Spark:** Transitioning business logic from local environments to distributed processing to handle the full Yelp dataset (millions of records), overcoming SQLite's memory limitations.
* **Shuffling Optimization:** Implementation of efficient partitioning and data distribution for large-scale computations.

### Data Enrichment (NLP)
* **Advanced Text Mining:** Implementation of Natural Language Processing (NLP) models to break down the specific sentiment behind the "Connectivity Premium."
* **Entity Extraction:** Automated identification of critical terms such as *"high-speed Wi-Fi"*, *"power outlets"*, or *"quiet environment"*.

### Automation and Cloud (ETL Pipeline)
* **Python ETL Robot:** Development of an automated pipeline for recurring Data Extraction, Transformation, and Loading (ETL).
* **Cloud Orchestration:** Deployment of workflows on AWS/Azure using **Apache Airflow** to ensure a 100% remote, robust, and professional data engineering system.



