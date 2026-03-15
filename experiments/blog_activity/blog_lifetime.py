"""Run with `uv run --with matplotlib blog_lifetime.py`"""

import sqlite3
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DB_PATH = "../../backend/brcrawl.sqlite3"


conn = sqlite3.connect(DB_PATH)
output_file = "blog_lifetime.png"


query = """
SELECT
    feed_id,
    MIN(published_at) AS first_post,
    MAX(published_at) AS last_post,
    julianday(MAX(published_at)) - julianday(MIN(published_at)) AS lifetime_days
FROM feed_items
WHERE published_at BETWEEN '2000-01-01' AND datetime('now')
GROUP BY feed_id;
"""

rows = conn.execute(query).fetchall()
conn.close()
lifetime_days = [round(row[3]) for row in rows]
lifetime_months = [round(d / 30) for d in lifetime_days]

print(f"Analyzing {len(lifetime_days)} blogs")

monthly_distribution = dict()
for num_months in sorted(lifetime_months):
    if num_months in monthly_distribution:
        monthly_distribution[num_months] += 1
    else:
        monthly_distribution[num_months] = 1

zero_years = monthly_distribution.get(0)
print(f"- {zero_years} blogs have a single post (0 months lifetime)")

up_to_one_year = 0
for i in range(1, 13):
    up_to_one_year += monthly_distribution.get(i, 0)

print(f"- {up_to_one_year} blogs lived from 1 month to 1 year")

one_to_three_years = 0
for i in range(13, 37):
    one_to_three_years += monthly_distribution.get(i, 0)

print(f"- {one_to_three_years} blogs lived from 1 year to 3 years")

three_to_five_years = 0
for i in range(37, 61):
    three_to_five_years += monthly_distribution.get(i, 0)

print(f"- {three_to_five_years} blogs lived from 3 to 5 years")

five_to_ten = 0
for i in range(61, 121):
    five_to_ten += monthly_distribution.get(i, 0)

print(f"- {five_to_ten} blogs lived from 5 to 10 years")

more_than_ten = 0
for i in range(121, 281):
    more_than_ten += monthly_distribution.get(i, 0)

print(f"- {more_than_ten} blogs lived more than 10 years")

print(f"Analyzed {zero_years + up_to_one_year + one_to_three_years + three_to_five_years + five_to_ten + more_than_ten} blogs")
print(monthly_distribution)

sys.exit(0)


plt.figure()
plt.hist(lifetime_months, bins=250)
plt.xlabel("Blog lifetime (months)")
plt.ylabel("Number of blogs")
plt.title("Distribution of blog lifetimes")
plt.tight_layout()

plt.savefig(output_file, dpi=300)

print(f"Saved graph to {output_file}")
