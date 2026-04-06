import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_FILE = "activity.db"
OUTPUT_DIR = "reports"

os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_FILE)

# Load data
df = pd.read_sql_query("SELECT * FROM activity_log", conn)

if df.empty:
    print("No data found.")
    exit()

# Convert timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date

# ================= SUMMARY =================
summary = df.groupby(["date", "status"]).size().unstack(fill_value=0)

# Convert counts → hours
summary["Active_hours"] = summary.get("Active", 0) * 10 / 3600
summary["Idle_hours"] = summary.get("Idle-Long", 0) * 10 / 3600

# Event counts
events = df[df["event"].notna()]
event_counts = events.groupby(["date", "event"]).size().unstack(fill_value=0)

# ================= EXPORT =================
filename = os.path.join(OUTPUT_DIR, f"activity_report_{datetime.now().date()}.xlsx")

with pd.ExcelWriter(filename) as writer:
    df.to_excel(writer, sheet_name="Raw Logs", index=False)
    summary.to_excel(writer, sheet_name="Summary")
    event_counts.to_excel(writer, sheet_name="Events")

print(f"Report saved: {filename}")