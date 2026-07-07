import sqlite3

def normalize_date(date_str):
    if not date_str:
        return None
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            return f"{year}-{int(month):02d}-{int(day):02d}"
    except:
        pass
    return None

conn = sqlite3.connect('IchingDB.db')
conn.create_function("normalize_date", 1, normalize_date)

# Test non-standard date formats specifically
print("=== 测试非标准日期格式 ===")
cur = conn.execute("""
    SELECT DISTINCT mydatetime, normalize_date(mydatetime) as normalized 
    FROM ichinglist 
    WHERE mydatetime GLOB '*-[0-9]-*' 
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"原始: {row[0]:20} -> 标准化: {row[1]}")

conn.close()
