import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ================= CONFIG =================
DB_FILE = "activity.db"
LOG_INTERVAL = 10  # seconds
import os
import sqlite3

conn = sqlite3.connect(r"C:\Users\Black Parrot\OneDrive\Desktop\Activity Tracker\v_2.0\activity.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

st.set_page_config(page_title="Activity Dashboard", layout="wide")
st.title("📊 Productivity Analytics Dashboard")

# ================= LOAD DATA =================
conn = sqlite3.connect(DB_FILE)
df = pd.read_sql_query("SELECT * FROM activity_log", conn)

if df.empty:
    st.warning("No data available yet.")
    st.stop()

# ================= PREPROCESS =================
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour

# ================= TIME CONVERSION =================
df["seconds"] = LOG_INTERVAL
df["hours"] = df["seconds"] / 3600

# ================= FILTER =================
st.sidebar.header("Filters")
selected_dates = st.sidebar.date_input(
    "Select Date Range",
    [df["date"].min(), df["date"].max()]
)

df = df[(df["date"] >= selected_dates[0]) & (df["date"] <= selected_dates[1])]

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

# ================= DAILY SUMMARY =================
st.subheader("📅 Daily Trends")

daily = df.groupby(["date", "category"])["hours"].sum().unstack(fill_value=0)

fig, ax = plt.subplots()
daily.plot(ax=ax)
ax.set_ylabel("Hours")
ax.set_title("Daily Activity Breakdown")
st.pyplot(fig)



st.subheader("📦 Sessions")

session_df = pd.read_csv("sessions.csv")

st.dataframe(session_df.head(50))
# ================= WEEKLY TRENDS =================
st.subheader("📆 Weekly Trends")

df["week"] = df["timestamp"].dt.isocalendar().week

weekly = df.groupby(["week", "category"])["hours"].sum().unstack(fill_value=0)

fig2, ax2 = plt.subplots()
weekly.plot(ax=ax2)
ax2.set_ylabel("Hours")
ax2.set_title("Weekly Productivity Trends")
st.pyplot(fig2)

# ================= HEATMAP =================
st.subheader("⏱️ Hour-wise Productivity Heatmap")

heatmap_data = df[df["category"] == "Productive"].groupby(["date", "hour"])["hours"].sum().unstack(fill_value=0)

fig3, ax3 = plt.subplots()
cax = ax3.imshow(heatmap_data, aspect='auto')

ax3.set_title("Productive Hours Heatmap")
ax3.set_xlabel("Hour of Day")
ax3.set_ylabel("Date")

fig3.colorbar(cax)
st.pyplot(fig3)

# ================= APP USAGE =================
st.subheader("🔥 Top Applications")

app_usage = df[df["status"] == "Active"].groupby("app_name")["hours"].sum().sort_values(ascending=False).head(10)
st.bar_chart(app_usage)

# ================= CATEGORY DISTRIBUTION =================
st.subheader("📊 Category Distribution")

cat_dist = df.groupby("category")["hours"].sum()
st.bar_chart(cat_dist)

# ================= FOCUS ANALYSIS =================
st.subheader("🧠 Focus Analysis")

focus_sessions = df[df["category"] == "Productive"].groupby("date")["hours"].sum()

fig4, ax4 = plt.subplots()
focus_sessions.plot(marker='o', ax=ax4)
ax4.set_title("Daily Focus Time")
ax4.set_ylabel("Hours")
st.pyplot(fig4)

# ================= EVENT ANALYSIS =================
st.subheader("🚨 Events")

events = df[df["event"].notna()]

if not events.empty:
    event_counts = events.groupby(["date", "event"]).size().unstack(fill_value=0)
    st.dataframe(event_counts)
else:
    st.info("No events recorded.")