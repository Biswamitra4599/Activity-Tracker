import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ================= CONFIG =================
DB_FILE = "activity.db"
LOG_INTERVAL = 10  # must match tracker

st.set_page_config(page_title="Activity Dashboard", layout="wide")

st.title("📊 Activity Tracker Dashboard")

# ================= LOAD DATA =================
conn = sqlite3.connect(DB_FILE)
df = pd.read_sql_query("SELECT * FROM activity_log", conn)

if df.empty:
    st.warning("No data available yet.")
    st.stop()

# ================= PREPROCESS =================
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date

# Count entries per day
summary = df.groupby(["date", "status"]).size().unstack(fill_value=0)

# Convert to hours
summary["Active_hours"] = summary.get("Active", 0) * LOG_INTERVAL / 3600
summary["Idle_hours"] = summary.get("Idle-Long", 0) * LOG_INTERVAL / 3600

# ================= DISPLAY TABLE =================
st.subheader("📅 Daily Summary")
st.dataframe(summary)

# ================= BAR CHART =================
st.subheader("📊 Active vs Idle Hours")

fig, ax = plt.subplots()
summary[["Active_hours", "Idle_hours"]].plot(kind="bar", ax=ax)

ax.set_ylabel("Hours")
ax.set_xlabel("Date")
ax.set_title("Daily Activity Breakdown")

st.pyplot(fig)

# ================= LINE CHART =================
st.subheader("📈 Active Hours Trend")

fig2, ax2 = plt.subplots()
summary["Active_hours"].plot(marker="o", ax=ax2)

ax2.set_ylabel("Active Hours")
ax2.set_xlabel("Date")
ax2.set_title("Active Hours Over Time")

st.pyplot(fig2)

# ================= EVENT ANALYSIS =================
st.subheader("🚨 Events")

events = df[df["event"].notna()]

if not events.empty:
    event_counts = events.groupby(["date", "event"]).size().unstack(fill_value=0)
    st.dataframe(event_counts)
else:
    st.info("No events recorded.")