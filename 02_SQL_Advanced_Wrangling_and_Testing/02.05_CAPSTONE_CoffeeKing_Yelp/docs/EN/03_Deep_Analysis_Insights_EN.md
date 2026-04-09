
# Deep Analysis and Advanced Insights - CoffeeKing Project

## 1. Deep Dive: Relationships and Correlations
In this phase, we have moved beyond simple descriptive counting to understand the underlying factors of business success by analyzing how different variables interact.

### Key Correlations Discovered:
* **Rating vs. Connectivity (Wi-Fi):** There is a strong positive correlation between offering **Free Wi-Fi** and achieving "Elite" status (Rating > 3.8). Data shows that free Wi-Fi acts as a magnet for the "Professional Power User," leading to higher and more consistent ratings (Average 3.81) compared to venues with paid or no Wi-Fi (Average 3.64).
* **Volume vs. Rating Stability:** A clear relationship is observed where an increase in `review_count` reduces rating volatility. Venues with more than 100 reviews show a narrower rating range (3 instead of 4), confirming that higher data volume provides a more reliable business quality benchmark.

## 2. Moving Beyond: Textual Analysis and Hidden Connections
Understanding the "why" behind the numbers through potential textual patterns and data points that might have been overlooked.

### Textual Analysis Expectations (TF-IDF):
If we were to apply **TF-IDF (Term Frequency – Inverse Document Frequency)** to the reviews of our top-performing venues, we would expect to find high relevance scores for terms such as:
* *"Reliable Wi-Fi"*
* *"Quiet environment"*
* *"Meeting spot"*
* *"Professional atmosphere"*

These terms define the "success theme" for CoffeeKing: the coffee shop as a functional co-working space rather than just a walk-through store.

### The Role of Check-ins:
Although initially ignored, the `checkin` table has become vital. Given the 138% higher activity during weekdays discovered in Milestone 2, analyzing check-in patterns is essential for optimizing staff shifts and table turnover during professional peak hours.

## 3. New Engineering Metrics (KPIs)
To track these deep relationships, I have developed two new custom metrics:

### Metric 1: Professional Engagement Index (PEI)
* **Formula:** `Weekday Reviews / Weekend Reviews`
* **Purpose:** To monitor whether the location is successfully capturing the target "Professional" demographic.
* **Target:** A PEI > 1.5 indicates successful alignment with the professional customer segment.

### Metric 2: Connectivity Premium (CP)
* **Formula:** `Average Rating (Free Wi-Fi) - Global Average Rating`
* **Purpose:** To quantify exactly how much value (in rating stars) the investment in high-speed connectivity adds to the business.
* **Current Value:** Based on current data, the Connectivity Premium is **+0.16 stars**.

## 4. Technical Implementation (SQL)
Below are the queries developed to extract the Phase 03 metrics:

### KPI Calculation (PEI and CP)
```sql
-- 1. Professional Engagement Index (PEI)
-- Weekday vs. weekend activity ratio
SELECT 
    ROUND(
        (SELECT COUNT(*) FROM review WHERE strftime('%w', date) NOT IN ('0', '6')) * 1.0 / 
        (SELECT COUNT(*) FROM review WHERE strftime('%w', date) IN ('0', '6')), 
    2) AS professional_engagement_index;

-- 2. Connectivity Premium (CP)
-- Free Wi-Fi impact compared to the global average
WITH GlobalAvg AS (
    SELECT AVG(stars) AS global_mean FROM business
),
WiFiAvg AS (
    SELECT AVG(stars) AS wifi_mean FROM business WHERE "attributes.WiFi" LIKE '%free%'
)
SELECT 
    ROUND(wifi_mean - global_mean, 2) AS connectivity_premium
FROM WiFiAvg, GlobalAvg;

-- 3. EXPLORATION FOR TF-IDF (Term Frequency)
-- Since SQLite does not have a native TF-IDF function, we prepare the data extraction
-- from "Elite" venues for future processing in Python/Spark.
SELECT 
    b.name,
    r.text
FROM business b
JOIN review r ON b.business_id = r.business_id
WHERE b.stars >= 3.8 AND "attributes.WiFi" LIKE '%free%'
LIMIT 10;