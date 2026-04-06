import sqlite3
import pandas as pd

# ================= CONFIG =================
DB_FILE = "activity.db"
LOG_INTERVAL = 10  # seconds

# ================= LOAD DATA =================
conn = sqlite3.connect(DB_FILE)

df = pd.read_sql_query("SELECT * FROM activity_log ORDER BY timestamp", conn)

if df.empty:
    print("No data found.")
    exit()

# ================= PREPROCESS =================
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Only consider Active + Idle-Long rows (ignore pure event rows)
df = df[df["status"].notna()]

# ================= SESSION BUILDING =================
sessions = []

start_time = df.iloc[0]["timestamp"]
prev_row = df.iloc[0]

for i in range(1, len(df)):
    curr = df.iloc[i]

    # Check if session should break
    if (
        curr["app_name"] != prev_row["app_name"] or
        curr["category"] != prev_row["category"] or
        curr["status"] != prev_row["status"]
    ):
        end_time = prev_row["timestamp"]

        duration = (end_time - start_time).total_seconds()

        sessions.append({
            "start_time": start_time,
            "end_time": end_time,
            "duration_sec": duration,
            "duration_hr": duration / 3600,
            "app_name": prev_row["app_name"],
            "category": prev_row["category"],
            "status": prev_row["status"]
        })

        # Start new session
        start_time = curr["timestamp"]

    prev_row = curr

# Add last session
end_time = prev_row["timestamp"]
duration = (end_time - start_time).total_seconds()

sessions.append({
    "start_time": start_time,
    "end_time": end_time,
    "duration_sec": duration,
    "duration_hr": duration / 3600,
    "app_name": prev_row["app_name"],
    "category": prev_row["category"],
    "status": prev_row["status"]
})

# ================= OUTPUT =================
session_df = pd.DataFrame(sessions)

# Save
session_df.to_csv("sessions.csv", index=False)

print("✅ Sessions saved to sessions.csv")