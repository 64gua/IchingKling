import sqlite3
conn = sqlite3.connect('IchingDB.db')
cur = conn.execute("SELECT DISTINCT mydatetime FROM ichinglist")
dates = [row[0] for row in cur.fetchall()]
print("Total unique dates:", len(dates))
print("Sample dates:", dates[:10])

# Check for non-standard formats
non_standard = [d for d in dates if d and (len(d) != 10 or d[4] != '-' or d[7] != '-')]
print("Non-standard format dates:", non_standard[:20])

# Check for NULL or empty
null_empty = [d for d in dates if not d]
print("NULL/Empty dates:", len(null_empty))
conn.close()
