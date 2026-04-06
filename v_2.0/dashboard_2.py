import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os

# ================= CONFIG =================
DB_FILE = r"C:\Users\Black Parrot\OneDrive\Desktop\Activity Tracker\v_2.0\activity.db"
LOG_INTERVAL = 10  # seconds

st.set_page_config(page_title="Activity Dashboard", layout="wide")
st.title("📊 Productivity Analytics Dashboard")

# ================= DB CONNECTION =================
if not os.path.exists(DB_FILE):
    st.error("❌ Database file not found.")
    st.stop()

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Check table exists
cursor.execute("""
SELECT name FROM sqlite_master 
WHERE type='table' AND name='activity_log';
""")

if not cursor.fetchone():
    st.error("❌ Table 'activity_log' not found. Run tracker.py first.")
    st.stop()

# ================= LOAD DATA =================
df = pd.read_sql_query("SELECT * FROM activity_log", conn)

if df.empty:
    st.warning("⚠️ No data available yet.")
    st.stop()

# ================= PREPROCESS =================
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour

df["seconds"] = LOG_INTERVAL
df["hours"] = df["seconds"] / 3600

# ================= FILTER =================
st.sidebar.header("Filters")
selected_dates = st.sidebar.date_input(
    "Select Date Range",
    [df["date"].min(), df["date"].max()]
)

df = df[(df["date"] >= selected_dates[0]) & (df["date"] <= selected_dates[1])]

# ================= EMPTY CHECK AFTER FILTER =================
if df.empty:
    st.warning("⚠️ No data for selected date range.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟢 Productive Hours", "0.00")
    col2.metric("🔴 Distracting Hours", "0.00")
    col3.metric("⚫ Idle Hours", "0.00")
    col4.metric("🎯 Productivity Score", "0.00%")

    st.info("Try selecting a different date range.")
    st.stop()

# ================= KPI METRICS =================
st.subheader("🎯 Key Metrics")

total_active = df[df["category"] == "Productive"]["hours"].sum()
total_distracting = df[df["category"] == "Distracting"]["hours"].sum()
total_idle = df[df["category"] == "Idle"]["hours"].sum()

total_time = total_active + total_distracting + total_idle
productivity_score = (total_active / total_time) * 100 if total_time > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("🟢 Productive Hours", f"{total_active:.2f}")
col2.metric("🔴 Distracting Hours", f"{total_distracting:.2f}")
col3.metric("⚫ Idle Hours", f"{total_idle:.2f}")
col4.metric("🎯 Productivity Score", f"{productivity_score:.2f}%")

# ================= DAILY TRENDS =================
st.subheader("📅 Daily Trends")

daily = df.groupby(["date", "category"])["hours"].sum().unstack(fill_value=0)

if not daily.empty:
    fig, ax = plt.subplots()
    daily.plot(ax=ax)
    ax.set_ylabel("Hours")
    ax.set_title("Daily Activity Breakdown")
    st.pyplot(fig)
else:
    st.info("📭 No data for Daily Trends")

# ================= SESSION BUILDING =================
st.subheader("📦 Sessions")

df_sorted = df.sort_values("timestamp")
df_sorted = df_sorted[df_sorted["status"].notna()]

sessions = []

if not df_sorted.empty:
    start_time = df_sorted.iloc[0]["timestamp"]
    prev_row = df_sorted.iloc[0]

    for i in range(1, len(df_sorted)):
        curr = df_sorted.iloc[i]

        if (
            curr["app_name"] != prev_row["app_name"] or
            curr["category"] != prev_row["category"] or
            curr["status"] != prev_row["status"]
        ):
            end_time = prev_row["timestamp"]
            duration = (end_time - start_time).total_seconds()

            if duration > 30:
                sessions.append({
                    "Start": start_time,
                    "End": end_time,
                    "Duration (min)": round(duration / 60, 2),
                    "App": prev_row["app_name"],
                    "Category": prev_row["category"],
                    "Status": prev_row["status"]
                })

            start_time = curr["timestamp"]

        prev_row = curr

    # Last session
    end_time = prev_row["timestamp"]
    duration = (end_time - start_time).total_seconds()

    if duration > 30:
        sessions.append({
            "Start": start_time,
            "End": end_time,
            "Duration (min)": round(duration / 60, 2),
            "App": prev_row["app_name"],
            "Category": prev_row["category"],
            "Status": prev_row["status"]
        })

session_df = pd.DataFrame(sessions)

if not session_df.empty:
    st.dataframe(session_df.head(50))
else:
    st.info("📭 No sessions detected yet.")

# ================= WEEKLY TRENDS =================
st.subheader("📆 Weekly Trends")

df["week"] = df["timestamp"].dt.isocalendar().week
weekly = df.groupby(["week", "category"])["hours"].sum().unstack(fill_value=0)

if not weekly.empty:
    fig, ax = plt.subplots()
    weekly.plot(ax=ax)
    ax.set_ylabel("Hours")
    st.pyplot(fig)
else:
    st.info("📭 No weekly data")

# ================= HEATMAP =================
st.subheader("⏱️ Hour-wise Productivity Heatmap")

heatmap_data = df[df["category"] == "Productive"].groupby(["date", "hour"])["hours"].sum().unstack(fill_value=0)

if not heatmap_data.empty:
    fig, ax = plt.subplots()
    cax = ax.imshow(heatmap_data, aspect='auto')
    fig.colorbar(cax)
    st.pyplot(fig)
else:
    st.info("📭 No heatmap data")

# ================= APP USAGE =================
st.subheader("🔥 Top Applications")

app_usage = df[df["status"] == "Active"].groupby("app_name")["hours"].sum().sort_values(ascending=False).head(10)

if not app_usage.empty:
    st.bar_chart(app_usage)
else:
    st.info("📭 No app usage data")

# ================= CATEGORY DISTRIBUTION =================
st.subheader("📊 Category Distribution")

cat_dist = df.groupby("category")["hours"].sum()

if not cat_dist.empty:
    st.bar_chart(cat_dist)
else:
    st.info("📭 No category data")

# ================= FOCUS ANALYSIS =================
st.subheader("🧠 Focus Analysis")

focus_sessions = df[df["category"] == "Productive"].groupby("date")["hours"].sum()

if not focus_sessions.empty:
    fig, ax = plt.subplots()
    focus_sessions.plot(marker='o', ax=ax)
    st.pyplot(fig)
else:
    st.info("📭 No focus data")

# ================= EVENTS =================
st.subheader("🚨 Events")

events = df[df["event"].notna()]

if not events.empty:
    event_counts = events.groupby(["date", "event"]).size().unstack(fill_value=0)
    st.dataframe(event_counts)
else:
    st.info("No events recorded.")