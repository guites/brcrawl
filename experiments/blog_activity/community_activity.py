"""Run with uv run --with matplotlib community_activity.py"""

import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DB_PATH = "../../backend/brcrawl.sqlite3"
OUTPUT_FILE = "active_feeds_per_month.png"

conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    year_month,
    COUNT(*) AS active_feeds
FROM (
    SELECT DISTINCT
        feed_id,
        strftime('%Y-%m', published_at) AS year_month
    FROM feed_items
    WHERE published_at BETWEEN '2000-01-01' AND datetime('now')
)
GROUP BY year_month
ORDER BY year_month;
"""

rows = conn.execute(query).fetchall()
conn.close()

months = [datetime.strptime(r[0], "%Y-%m") for r in rows]
counts = [r[1] for r in rows]

fig, ax = plt.subplots()

ax.plot(months, counts, marker="o")

ax.set_xlabel("Month")
ax.set_ylabel("Active feeds")
ax.set_title("Active feeds per month")

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))

plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(OUTPUT_FILE, dpi=300)

print(f"Saved graph to {OUTPUT_FILE}")
