import time
import sqlite3
from datetime import datetime
from pynput import mouse, keyboard
import os
import sys
import atexit

# Windows-specific imports for app tracking
import win32gui
import win32process
import psutil

# ================= CONFIG =================
IDLE_THRESHOLD = 15 * 60  # 15 minutes
LOG_INTERVAL = 10  # seconds
DB_FILE = "activity.db"
LOCK_FILE = "tracker.lock"

# ================= SINGLE INSTANCE LOCK =================
if os.path.exists(LOCK_FILE):
    sys.exit()

open(LOCK_FILE, "w").close()

def cleanup():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

atexit.register(cleanup)

# ================= DB SETUP =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    status TEXT,
    idle_seconds REAL,
    app_name TEXT,
    window_title TEXT,
    event TEXT
)
""")
conn.commit()

# ================= GLOBALS =================
last_activity_time = time.time()
prev_time = time.time()
already_flagged = False

# ================= INPUT LISTENERS =================
def on_input(event=None):
    global last_activity_time
    last_activity_time = time.time()

mouse.Listener(on_move=on_input, on_click=on_input).start()
keyboard.Listener(on_press=on_input).start()

# ================= ACTIVE WINDOW TRACKING =================
def get_active_window_info():
    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        app_name = process.name()

        return app_name, window_title
    except Exception:
        return "Unknown", "Unknown"

# ================= LOG FUNCTION =================
def log_event(status=None, idle_seconds=None, app_name=None, window_title=None, event=None):
    cursor.execute("""
        INSERT INTO activity_log (timestamp, status, idle_seconds, app_name, window_title, event)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), status, idle_seconds, app_name, window_title, event))
    conn.commit()

# ================= MAIN LOOP =================
try:
    while True:
        current_time = time.time()
        idle_time = current_time - last_activity_time

        # Get active app info
        app_name, window_title = get_active_window_info()

        # Detect Sleep (time jump)
        if current_time - prev_time > 60:
            log_event(event="System Sleep Detected")

        # Status logic
        if idle_time > IDLE_THRESHOLD:
            status = "Idle-Long"

            if not already_flagged:
                log_event(event="Idle > 15 min")
                already_flagged = True
        else:
            status = "Active"
            already_flagged = False

        # Log activity
        log_event(
            status=status,
            idle_seconds=idle_time,
            app_name=app_name,
            window_title=window_title
        )

        prev_time = current_time
        time.sleep(LOG_INTERVAL)

except Exception as e:
    log_event(event=f"Crash: {str(e)}")

finally:
    conn.close()