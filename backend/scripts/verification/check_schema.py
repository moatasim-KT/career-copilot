import sqlite3

conn = sqlite3.connect('data/career_copilot.db')
cursor = conn.cursor()

print("=== Users Table Schema ===")
cursor.execute("PRAGMA table_info(users)")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print("\n=== Jobs Table Schema ===")
cursor.execute("PRAGMA table_info(jobs)")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print("\n=== Applications Table Schema ===")
cursor.execute("PRAGMA table_info(applications)")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print("\n=== Indexes ===")
cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
for row in cursor.fetchall():
    print(f"  {row[0]} on {row[1]}")

conn.close()
