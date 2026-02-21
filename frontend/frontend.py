import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, date, time, timedelta


API_URL = os.getenv("API_URL", "http://backend:8000")
OFFSET_HOURS = 4  # Tasks reset at 4 AM

def get_effective_date(dt: datetime = None):
    if dt is None:
        dt = datetime.now()
    return (dt - timedelta(hours=OFFSET_HOURS)).date()

def get_effective_range(d: date):
    start = datetime.combine(d, time(OFFSET_HOURS, 0))
    end = start + timedelta(days=1)
    return start, end

# "Today" relative to the reset hour
effective_today = get_effective_date()
effective_start, effective_end = get_effective_range(effective_today)

st.set_page_config(page_title="Daily Focus", page_icon="🎯", layout="wide")

st.markdown("""
<style>
/* ── Global page dark background ───────────────────────────── */
.stApp { background-color: #0f1117; color: #e2e8f0; }

/* ── Calendar iframe wrapper ────────────────────────────────── */
iframe[title="streamlit_calendar.calendar"] {
    border-radius: 14px;
    background: #161b27;
    border: none !important;
    box-shadow: 0 4px 32px rgba(0,0,0,0.5);
}

/* ── Hide scrollbar globally ─────────────────────────────────── */
::-webkit-scrollbar { width: 0px; background: transparent; }
* { scrollbar-width: none; -ms-overflow-style: none; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Daily Focus Dashboard")

# --- API Helper Functions ---

def get_categories():
    try:
        res = requests.get(f"{API_URL}/categories/")
        return res.json() if res.status_code == 200 else []
    except:
        return []

def get_tasks():
    try:
        res = requests.get(f"{API_URL}/tasks/")
        return res.json() if res.status_code == 200 else []
    except:
        return []

# --- Sidebar: Data Entry ---

today_str = effective_today.strftime("%A, %b %d, %Y")

categories = get_categories()
cat_options = {c["name"]: c["id"] for c in categories}
global_color_map = {c["name"]: c["color_hex"] for c in categories}

with st.sidebar:
    st.header(f"📅 {effective_today.strftime('%A, %b %d')}")
    st.divider()
    
    # --- 1. New Task ---
    with st.form("new_task_form", clear_on_submit=True):
        st.subheader("Add Task")
        task_title = st.text_input("Task Title")
        selected_cat = st.selectbox("Category", options=list(cat_options.keys()) if categories else ["None"])
        
        if st.form_submit_button("Add to Today"):
            if categories and task_title.strip():
                requests.post(f"{API_URL}/tasks/", json={"title": task_title, "category_id": cat_options[selected_cat]})
                st.rerun()

    # --- 2. Add / Edit Categories ---
    with st.expander("⚙️ Manage Categories"):
        # Add New (With Uniqueness Check)
        new_c_name = st.text_input("New Category Name")
        new_c_color = st.color_picker("New Color", "#FFFFFF")
        if st.button("Create Category"):
            existing_names = [c["name"].lower() for c in categories]
            existing_colors = [c["color_hex"].upper() for c in categories]
            
            if new_c_name.lower() in existing_names:
                st.error("Name already exists!")
            elif new_c_color.upper() in existing_colors:
                st.error("Color already used! Pick a unique one.")
            else:
                requests.post(f"{API_URL}/categories/", json={"name": new_c_name, "color_hex": new_c_color})
                st.rerun()
                
        st.divider()
        # Edit Existing
        if categories:
            edit_cat = st.selectbox("Edit Existing", options=list(cat_options.keys()))
            current_color = global_color_map.get(edit_cat, "#000000")
            updated_color = st.color_picker("Update Color", current_color, key="edit_color")
            if st.button("Save Color Update"):
                cat_id = cat_options[edit_cat]
                requests.put(f"{API_URL}/categories/{cat_id}", json={"name": edit_cat, "color_hex": updated_color})
                st.rerun()

# ==========================================
# MODULE 2: MAIN TABS
# ==========================================
# Fetch tasks once at top level so every tab can use them safely
all_tasks = get_tasks()
todays_tasks = [t for t in all_tasks if get_effective_date(datetime.fromisoformat(t["created_at"])) == effective_today]

tab1, tab2, tab3 = st.tabs(["📝 Today's List", "⏱️ Log Time", "📊 Analytics"])

# --- TAB 1: TO-DO LIST (Filtered for Today) ---
with tab1:
    st.header("Today's Focus")
    
    if not todays_tasks:
        st.info("Your list is clear for today!")
    else:
        sorted_tasks = sorted(todays_tasks, key=lambda x: x["is_completed"])
        for task in sorted_tasks:
            # Added a 3rd column for the delete button
            col1, col2, col3 = st.columns([0.05, 0.85, 0.1])
            is_done = col1.checkbox("", value=task["is_completed"], key=f"chk_{task['id']}")
            
            title_text = f"~~{task['title']}~~" if is_done else task['title']
            col2.markdown(title_text)
            
            # DELETE BUTTON
            if col3.button("❌", key=f"del_{task['id']}"):
                requests.delete(f"{API_URL}/tasks/{task['id']}")
                st.rerun()

            if is_done != task["is_completed"]:
                requests.put(f"{API_URL}/tasks/{task['id']}", json={"is_completed": is_done})
                st.rerun()

# --- TAB 2: LOG TIME ---
with tab2:
    st.header("⏱️ Log Session")

    # ── Fetch today's blocks ──────────────────────────────────────────
    start_of_day = effective_start.isoformat()
    end_of_day   = effective_end.isoformat()
    try:
        blocks_res  = requests.get(f"{API_URL}/calendar/blocks",
                                   params={"start": start_of_day, "end": end_of_day},
                                   timeout=5)
        blocks_data = blocks_res.json() if blocks_res.status_code == 200 else []
    except Exception:
        blocks_data = []

    # ── Log Session Form ─────────────────────────────────────────────
    with st.form("log_session_form", clear_on_submit=True):
        st.subheader("Add a Session")
        if todays_tasks:
            form_col1, form_col2, form_col3 = st.columns([2, 1, 1])
            log_task  = form_col1.selectbox("Task", options=[t["title"] for t in todays_tasks])
            start_t   = form_col2.time_input("Start", value=time(9, 0))
            end_t     = form_col3.time_input("End",   value=time(10, 0))

            submitted = st.form_submit_button("➕ Add Session")
            if submitted:
                task_id  = next(t["id"] for t in todays_tasks if t["title"] == log_task)
                
                # Logic: If time is before OFFSET_HOURS, it belongs to the "next" calendar day
                # but stays within the "effective" yesterday.
                def to_dt(t_val):
                    dt = datetime.combine(effective_today, t_val)
                    if t_val.hour < OFFSET_HOURS:
                        dt += timedelta(days=1)
                    # Edge case: if it's 23:00 but offset is 4 AM, it's correct.
                    # if it's 01:00 and offset is 4 AM, it's next calendar day.
                    return dt

                start_dt_obj = to_dt(start_t)
                end_dt_obj = to_dt(end_t)
                
                # If end time is objectively before start time (e.g. 11 PM to 1 AM)
                if end_dt_obj <= start_dt_obj:
                    end_dt_obj += timedelta(days=1)

                res = requests.post(f"{API_URL}/calendar/block",
                                    json={"task_id": task_id,
                                          "start_time": start_dt_obj.isoformat(),
                                          "end_time": end_dt_obj.isoformat()})
                if res.status_code == 200:
                    st.success("Session added!")
                    st.rerun()
                else:
                    st.error(f"❌ {res.json().get('detail', 'Unknown error')}")
        else:
            st.warning("Add a task to today's list first!")
            st.form_submit_button("➕ Add Session", disabled=True)

    st.divider()

    # ── 24-Hour Plotly Timeline ───────────────────────────────────────
    st.subheader("Today's Timeline")

    today_str = date.today().isoformat()

    if not blocks_data:
        st.info("No sessions logged yet today. Add one above.")
    else:
        chart_rows = []
        for b in blocks_data:
            task_info = next((t for t in all_tasks if t["id"] == b["task_id"]), None)
            task_name = task_info["title"] if task_info else "Unknown"
            cat_color = global_color_map.get(
                next((c["name"] for c in categories if c["id"] == task_info.get("category_id")), ""),
                "#3788d8"
            ) if task_info else "#3788d8"
            s = datetime.fromisoformat(b["start_time"])
            e = datetime.fromisoformat(b["end_time"])
            chart_rows.append({
                "Task":  task_name,
                "Start": s,
                "End":   e,
                "Color": cat_color,
            })

        df_timeline = pd.DataFrame(chart_rows)
        fig = px.timeline(
            df_timeline,
            x_start="Start",
            x_end="End",
            y="Task",
            color="Task",
            color_discrete_sequence=df_timeline["Color"].tolist(),
        )
        fig.update_xaxes(
            range=[effective_start, effective_end],
            tickformat="%H:%M",
            title="Time",
            showgrid=True,
            gridcolor="#334155",
            dtick=3600000, # 1 hour in ms
        )
        fig.update_yaxes(
            title="",
            showgrid=True,
            gridcolor="#334155",
        )
        fig.update_layout(
            paper_bgcolor="#0f1117",
            plot_bgcolor="#161b27",
            font_color="#e2e8f0",
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=max(120, 60 * len(chart_rows)),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Logged Blocks List with Delete ───────────────────────────────
    st.subheader("Logged Sessions")
    if not blocks_data:
        st.info("Nothing logged yet.")
    else:
        for b in blocks_data:
            task_info = next((t for t in all_tasks if t["id"] == b["task_id"]), None)
            task_name = task_info["title"] if task_info else "Unknown Task"
            s_time    = datetime.fromisoformat(b["start_time"]).strftime("%H:%M")
            e_time    = datetime.fromisoformat(b["end_time"]).strftime("%H:%M")

            c1, c2, c3 = st.columns([0.55, 0.35, 0.1])
            c1.write(f"**{task_name}**")
            c2.write(f"{s_time} → {e_time}")
            if c3.button("❌", key=f"del_block_{b['id']}"):
                del_res = requests.delete(f"{API_URL}/calendar/block/{b['id']}")
                if del_res.status_code == 200:
                    st.rerun()
                else:
                    st.error("Failed to delete.")



with tab3:
    st.header("📊 Analytics Dashboard")

    # ── Date Range ───────────────────────────────────────────────────
    today = effective_today
    d_col1, d_col2 = st.columns(2)
    report_start = d_col1.date_input("Start Date", value=today)
    report_end   = d_col2.date_input("End Date",   value=today)

    # Validation
    if report_start > report_end:
        st.error("⚠️ Start date cannot be after end date.")
        st.stop()

    label = "Today" if report_start == report_end == today else f"{report_start} → {report_end}"
    st.caption(f"Showing stats for: **{label}**")

    report_start_dt, _ = get_effective_range(report_start)
    _, report_end_dt   = get_effective_range(report_end)
    start_iso = report_start_dt.isoformat()
    end_iso   = report_end_dt.isoformat()

    # ── Fetch Data ───────────────────────────────────────────────────
    try:
        res = requests.get(
            f"{API_URL}/analytics/dashboard",
            params={"start_date": start_iso, "end_date": end_iso},
            timeout=5
        )
    except Exception:
        st.error("Cannot connect to the backend.")
        st.stop()

    if res.status_code != 200:
        st.error("Backend returned an error loading analytics.")
        st.stop()

    data = res.json()
    cat_color_map = {item["name"]: item["color"] for item in data.get("pie_chart", [])}

    # ── Hero Metric ──────────────────────────────────────────────────
    hours   = data["total_minutes"] // 60
    minutes = data["total_minutes"] % 60
    st.metric("⏱️ Total Tracked Time", f"{hours}h {minutes}m" if hours else f"{minutes} min")
    st.divider()

    if not data["pie_chart"]:
        st.info("No sessions logged for this period.")
    else:
        # ── Row 1: Pie + Task Bar ────────────────────────────────────
        col_pie, col_bar = st.columns(2)

        # Donut pie — time by category
        with col_pie:
            st.subheader("🍩 Time by Category")
            df_pie = pd.DataFrame(data["pie_chart"])
            fig_pie = px.pie(
                df_pie,
                values="value",
                names="name",
                color="name",
                color_discrete_map=cat_color_map,
                hole=0.45,
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>%{value} min<extra></extra>",
            )
            fig_pie.update_layout(
                paper_bgcolor="#0f1117",
                font_color="#e2e8f0",
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Horizontal bar — time per task (sorted descending)
        with col_bar:
            st.subheader("📋 Time by Task")
            if data["task_breakdown"]:
                df_task = pd.DataFrame(data["task_breakdown"])
                fig_task = px.bar(
                    df_task,
                    x="minutes",
                    y="task",
                    orientation="h",
                    color="task",
                    color_discrete_sequence=df_task["color"].tolist(),
                    text="minutes",
                )
                fig_task.update_traces(
                    texttemplate="%{text} min",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x} min<extra></extra>",
                )
                fig_task.update_layout(
                    paper_bgcolor="#0f1117",
                    plot_bgcolor="#161b27",
                    font_color="#e2e8f0",
                    showlegend=False,
                    xaxis_title="Minutes",
                    yaxis_title="",
                    margin=dict(l=0, r=40, t=10, b=0),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_task, use_container_width=True)
            else:
                st.info("No task data.")


        st.divider()

        # ── Row 3: Category vs Total Time — Horizontal Bar ───────────
        st.subheader("🗂️ Total Time by Category")
        if data["pie_chart"]:
            df_cat = pd.DataFrame(data["pie_chart"]).sort_values("value", ascending=True)
            fig_cat = px.bar(
                df_cat,
                x="value",
                y="name",
                orientation="h",
                color="name",
                color_discrete_map=cat_color_map,
                text="value",
            )
            fig_cat.update_traces(
                texttemplate="%{text} min",
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x} min<extra></extra>",
            )
            fig_cat.update_layout(
                paper_bgcolor="#0f1117",
                plot_bgcolor="#161b27",
                font_color="#e2e8f0",
                showlegend=False,
                xaxis_title="Minutes",
                yaxis_title="",
                margin=dict(l=0, r=60, t=10, b=0),
            )
            st.plotly_chart(fig_cat, use_container_width=True)


    st.divider()

    # ── 365-Day Streak Dot Tracker ────────────────────────────────────
    st.subheader("🔥 365-Day Streak Tracker")
    st.caption("Each dot = 1 day. Fill all 365 to earn a Mega Year 🏆. Any break resets the dots.")

    all_tasks_for_streak = get_tasks()
    if all_tasks_for_streak:
        task_options = {t["title"]: t["id"] for t in all_tasks_for_streak}
        streak_task  = st.selectbox(
            "Select Task", options=list(task_options.keys()), key="streak_select", label_visibility="collapsed"
        )
        streak_res = requests.get(f"{API_URL}/analytics/streak/{task_options[streak_task]}")

        if streak_res.status_code == 200:
            import plotly.graph_objects as go
            sd = streak_res.json()
            current_days = sd["current_streak_days"]

            years_done = current_days // 365
            dot_fill   = current_days % 365
            if dot_fill == 0 and current_days > 0:
                dot_fill = 365

            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🔥 Current Streak", f"{current_days} days")
            m2.metric("🏆 Mega Years",     years_done)
            m3.metric("📆 Days Tracked",   sd["tracked_days_count"])
            m4.metric("⏱️ Total Time",     f"{sd['total_time_spent_minutes']} min")

            if years_done > 0:
                trophies = " ".join(["🏆"] * min(years_done, 10))
                suffix   = f" + {years_done - 10} more" if years_done > 10 else ""
                st.success(f"**{years_done} Mega Year{'s' if years_done > 1 else ''} Complete!**  {trophies}{suffix}")

            # 365 dot grid: 73 cols × 5 rows
            COLS, ROWS = 73, 5
            x_vals, y_vals, colors, hover_texts = [], [], [], []

            for i in range(365):
                filled = i < dot_fill
                if filled:
                    p = i / max(dot_fill - 1, 1)
                    color = "#0e4429" if p < 0.33 else "#006d32" if p < 0.66 else "#26a641" if p < 0.9 else "#39d353"
                else:
                    color = "#1e2433"
                x_vals.append(i % COLS)
                y_vals.append(i // COLS)
                colors.append(color)
                hover_texts.append(f"Day {i + 1} {'✅' if filled else '○'}")

            fig_dots = go.Figure(go.Scatter(
                x=x_vals, y=y_vals,
                mode="markers",
                marker=dict(color=colors, size=9, symbol="circle", line=dict(width=0)),
                text=hover_texts,
                hoverinfo="text",
            ))
            fig_dots.update_layout(
                paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[-0.5, COLS - 0.5]),
                yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, autorange="reversed", range=[-0.5, ROWS - 0.5]),
                margin=dict(l=0, r=0, t=5, b=0),
                height=150, showlegend=False,
            )
            st.plotly_chart(fig_dots, use_container_width=True)
            st.caption(f"**{dot_fill} / 365** days complete — {365 - dot_fill} days to go until Mega Year {years_done + 1}")
    else:
        st.info("No tasks yet.")

