import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px



DB_PATH = "battery_logs.sqlite"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def run_sql(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"SQL error: {e}")
        return pd.DataFrame()   # <-- always return a DataFrame
    finally:
        conn.close()

def execute_sql(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()

def ensure_settings_row():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, interval INTEGER DEFAULT 20, allowed_networks TEXT DEFAULT '', manual_override INTEGER DEFAULT 0)")
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM settings")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("INSERT INTO settings (interval, allowed_networks, manual_override) VALUES (20, '', 0)")
        conn.commit()
    conn.close()

def get_settings():
    ensure_settings_row()
    df = run_sql("SELECT * FROM settings LIMIT 1")
    return df.iloc[0].to_dict()

def save_settings(interval=None, allowed_networks=None, manual_override=None):
    settings = get_settings()
    if interval is None:
        interval = settings["interval"]
    if allowed_networks is None:
        allowed_networks = settings["allowed_networks"]
    if manual_override is None:
        manual_override = settings["manual_override"]

    execute_sql(
        "UPDATE settings SET interval = ?, allowed_networks = ?, manual_override = ? WHERE id = 1",
        (interval, allowed_networks, manual_override),
    )

def get_all_devices():
    df = run_sql("SELECT DISTINCT device_id FROM battery_logs ORDER BY device_id")
    if df is None or df.empty:
        return []
    return df["device_id"].dropna().tolist()

def get_all_networks():
    df = run_sql("SELECT DISTINCT localisation FROM battery_logs WHERE localisation IS NOT NULL ORDER BY localisation")
    return df["localisation"].tolist()

def page_event_explorer():
    st.header("Event Explorer")

    devices = ["All"] + get_all_devices()
    selected_device = st.selectbox("Device", devices)

    event_filter = st.selectbox(
        "Event filter",
        ["All", "Only events (event_type NOT NULL)", "Only plugged_in/unplugged"],
    )

    default_start = datetime.now() - timedelta(days=0)
    default_end = datetime.now()
    start_date, end_date = st.date_input(
        "Date range", [default_start, default_end]
    )
    hours = [f"{h:02d}:00" for h in range(9, 18)]
    col1, col2 = st.columns(2)
    with col1:
        start_hour = st.selectbox("Starting from", hours, index=0)
    with col2:
        end_hour = st.selectbox("Ending at", hours, index=len(hours)-1)

    query = "SELECT * FROM battery_logs WHERE 1=1"
    params = []

    if selected_device != "All":
        query += " AND device_id = ?"
        params.append(selected_device)

    if event_filter == "Only events (event_type NOT NULL)":
        query += " AND event_type IS NOT NULL"
    elif event_filter == "Only plugged_in/unplugged":
        query += " AND event_type IN ('PLUGGED_IN', 'UNPLUGGED')"

    start_ts = f"{start_date} {start_hour}:00"
    end_ts   = f"{end_date} {end_hour}:59"

    query += " AND timestamp BETWEEN ? AND ?"
    params.append(start_ts)
    params.append(end_ts)

    df = pd.DataFrame()

    if st.button("Run query"):
        df = run_sql(query, params)
        st.write(f"{len(df)} rows")
        st.dataframe(df)

    """if not df.empty:
        st.subheader("Heatmap: Event's by Hour")

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["hour"] = df["timestamp"].dt.hour

        heatmap_data = df.pivot_table(
            index="hour",
            columns="event_type",
            values="device_id",
            aggfunc="count",
            fill_value=0
        )

        heatmap_data = heatmap_data.reset_index().melt(id_vars="hour")

        fig = px.density_heatmap(
            heatmap_data,
            x="event_type",
            y="hour",
            z="value",
            color_continuous_scale="Viridis",
            labels={"value": "Count"},
            height=500,
        )

        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for heatmap")"""

def page_device_comparison():
    st.header("Device Comparison")

    devices = get_all_devices()
    if not devices:
        st.info("No devices found in logs yet")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        device_a = st.selectbox("Device A", devices, key="device_a")
    with col2:
        device_b = st.selectbox("Device B", devices, key="device_b")

    default_start = datetime.now() - timedelta(days=0)
    default_end = datetime.now()
    start_date, end_date = st.date_input(
        "Date range", [default_start, default_end], key="cmp_dates"
    )

    if st.button("Compare devices"):
        q = """
        SELECT device_id, event_type, timestamp, level, localisation
        FROM battery_logs
        WHERE device_id IN (?, ?)
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp DESC
        """
        df = run_sql(q, (device_a, device_b, start_date, end_date))
        st.dataframe(df)

        st.subheader("Counts by device and event_type")
        if not df.empty:
            counts = df.groupby(["device_id", "event_type"]).size().reset_index(name="count")
            st.dataframe(counts)
        else:
            st.write("No data for this range/devices.")

def page_network_settings():
    st.header("Network Settings")

    settings = get_settings()
    all_networks = get_all_networks()
    current_allowed = (
        settings["allowed_networks"].split(",")
        if settings["allowed_networks"]
        else[]
    )

    selected_networks = st.multiselect(
        "Networks allowing logging",
        all_networks,
        default=current_allowed,
    )

    if st.button("Save network settings"):
        allowed_str = ",".join(selected_networks)
        save_settings(allowed_networks=allowed_str)
        st.success("Network settings saved.")

    st.write("Current allowed networks:", selected_networks)

def page_tracker_settings():
    st.header("Tracker Settings")

    settings = get_settings()
    st.write(f"Current interval: {settings['interval']} seconds")

    interval = st.slider(
        "Tracker interval (seconds)",
        5,
        300,
        int(settings["interval"]),
    )

    if st.button("Save interval"):
        save_settings(interval=interval)
        st.success(f"Interval updated to {interval} seconds.")

def page_tracker_control():
    st.header("Tracker Control")

    settings = get_settings()
    manual_override = settings["manual_override"]

    st.write("This uses a *soft* control flag in SQLite.")
    st.write("Your tracker should read `manual_override` and skip logging when it is 1.")

    st.write(f"Current manual_override value: {manual_override}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Pause tracker (set manual_override = 1)"):
            save_settings(manual_override=1)
            st.success("Tracker paused (manual_override = 1).")
    with col2:
        if st.button("Resume tracker (set manual_override = 0)"):
            save_settings(manual_override=0)
            st.success("Tracker resumed (manual_override = 0).")

    st.info(
        "In your tracker loop, check this flag and skip work when manual_override == 1.\n"
        "This avoids clashing with systemd timers and keeps control in the DB."
    )

# -----------------------------
# Main app
# -----------------------------
def main():
    st.set_page_config(page_title="Battery Tracker Dashboard", layout="wide")

    st.sidebar.title("🔋 Battery Tracker")
    page = st.sidebar.radio(
        "Navigate",
        [
            "Event Explorer",
            "Device Comparison",
            "Network Settings",
            "Tracker Settings",
            "Tracker Control",
        ],
    )

    if page == "Event Explorer":
        page_event_explorer()
    elif page == "Device Comparison":
        page_device_comparison()
    elif page == "Network Settings":
        page_network_settings()
    elif page == "Tracker Settings":
        page_tracker_settings()
    elif page == "Tracker Control":
        page_tracker_control()

if __name__ == "__main__":
    main()
