"""Run with `uv run --with matplotlib new_blogs_per_month.py`"""

import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DB_PATH = "../../backend/brcrawl.sqlite3"
OUTPUT_FILE = "new_blogs_per_month.png"

conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    strftime('%Y-%m', first_post) AS year_month,
    COUNT(*) AS new_blogs
FROM (
    SELECT
        feed_id,
        MIN(published_at) AS first_post
    FROM feed_items
    WHERE published_at BETWEEN '2000-01-01' AND datetime('now')
    GROUP BY feed_id
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
ax.set_ylabel("New blogs")
ax.set_title("New blogs appearing per month")

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))

plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(OUTPUT_FILE, dpi=300)

print(f"Saved graph to {OUTPUT_FILE}")
