"""Run with uv run --with matplotlib feed_items_per_month.py"""

import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DB_PATH = "../../backend/brcrawl.sqlite3"
OUTPUT_FILE = "feed_items_per_month.png"

conn = sqlite3.connect(DB_PATH)

def outlier_analysis(conn):
    min_max_query = """
    SELECT MIN(published_at), MAX(published_at)
    FROM feed_items;
    """

    rows = conn.execute(min_max_query).fetchall()
    res = rows[0]
    print(f"Oldest blog post: {res[0]}")
    print(f"Newest blog post: {res[1]}")

    top_old_query = """
    SELECT DISTINCT published_at
    FROM feed_items
    ORDER BY published_at
    LIMIT 10;
    """

    rows = conn.execute(top_old_query).fetchall()
    print("Top 10 oldest posts")
    for r in rows:
        print(f"    {r[0]}")

    top_new_query = """
    SELECT DISTINCT published_at
    FROM feed_items
    ORDER BY published_at
    DESC
    LIMIT 10;
    """

    print("Top 10 newest posts")
    rows = conn.execute(top_new_query).fetchall()
    for r in rows:
        print(f"    {r[0]}")


outlier_analysis(conn)

query = """
SELECT
    strftime('%Y-%m', published_at) AS year_month,
    COUNT(*) AS item_count
FROM feed_items
WHERE published_at BETWEEN '2000-01-01' AND datetime('now')
GROUP BY year_month
ORDER BY year_month;
"""

rows = conn.execute(query).fetchall()
conn.close()

# Convert query results
months = [datetime.strptime(r[0], "%Y-%m") for r in rows]
counts = [r[1] for r in rows]

fig, ax = plt.subplots()

ax.plot(months, counts, marker="o")

ax.set_xlabel("Year")
ax.set_ylabel("Number of feed items")
ax.set_title("Feed items published per month")

# Format date axis
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))  # minor ticks every 3 months

plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(OUTPUT_FILE, dpi=300)
print(f"Graph saved to {OUTPUT_FILE}")
