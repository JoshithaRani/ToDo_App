import streamlit as st
import pandas as pd
import datetime
import sqlite3



conn = sqlite3.connect("tasks.db")  # SQLite file-based DB
cursor = conn.cursor()
#Table creation
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taskname TEXT,
    status TEXT,
    tags TEXT,
    priority TEXT,
    selected_date DATE,
    created_date DATE,
    pending_days INTEGER,
    information TEXT
)
""")
conn.commit()




# ────────── FUNCTIONS ────────── #
def get_tasks(filter_status=None):
    if filter_status and filter_status != "All":
        cursor.execute("""SELECT id, taskname, status, tags, priority, pending_days FROM tasks WHERE priority = ?""", (filter_status,))
    else:
        cursor.execute("SELECT id, taskname, status, tags, priority, pending_days FROM tasks")
    return cursor.fetchall()


def inserttask(tn, stt, stag, pr, duedate, doe, nodl, info):
    tn = tn.title()
    stt = stt.title()
    stag = stag.title()
    pr = pr.title()
    info = info.title()
    
    if stt in ["Pending", "In Progress", "Completed"]:
        cursor.execute("""
            INSERT INTO tasks(taskname, status, tags, priority, selected_date, created_date, pending_days, information)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tn, stt, stag, pr, duedate, doe, nodl, info))
        conn.commit()
        st.success("✅ Task added!")
    else:
        st.error("❌ Status must be 'Completed', 'Pending', or 'In Progress'.")

def tags():
    predefined_tags = ["Work", "Personal", "College", "Shopping"]
    selected_tag = st.selectbox("Choose a tag", predefined_tags + ["Add Custom Tag"])
    if selected_tag == "Add Custom Tag":
        custom_tag = st.text_input("Enter your custom tag")
        return custom_tag.title()
    else:
        return selected_tag

def update_status(task_id, new_value, column_type):
    if column_type == "Status":
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_value, task_id))
    elif column_type == "Priority":
        cursor.execute("UPDATE tasks SET priority = ? WHERE id = ?", (new_value, task_id))
    elif column_type == "Tags":
        cursor.execute("UPDATE tasks SET tags = ? WHERE id = ?", (new_value, task_id))
    elif column_type == "Due Date":
        cursor.execute("UPDATE tasks SET selected_date = ? WHERE id = ?", (new_value, task_id))
        today = datetime.date.today()
        pend = (new_value - today).days
        cursor.execute("UPDATE tasks SET pending_days =? WHERE id = ?", (pend, task_id))
    else:
        cursor.execute("UPDATE tasks SET information = ? WHERE id = ?", (new_value, task_id))
    conn.commit()
    st.success("✅ Task updated!")

def search_task(by, value):
    if by == "Status":
        cursor.execute("SELECT * FROM tasks WHERE status = ?", (value,))
    elif by == "Tags":
        cursor.execute("SELECT * FROM tasks WHERE tags = ?", (value,))
    else:  # ID
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (value,))
    return cursor.fetchall()

def delete_task(del_type, task_id=None):
    if del_type == "All":
        cursor.execute("DELETE FROM tasks")
    elif del_type == "ID" and task_id:
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    st.success("🗑️ Deleted successfully!")

def moreinfo(tid):
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (tid,))
    record = cursor.fetchone()
    if record:
        df = pd.DataFrame([record], columns=[
            "ID", "Task Name", "Status", "Tags", "Priority",
            "Due Date", "Date of Entry", "Pending Days", "Information"
        ])
        st.table(df)
    else:
        st.warning("⚠️ No task found with the given ID.")

# ────────── SIDEBAR ────────── #
tab = st.sidebar.radio(
    "📌 Choose Action",
    ["📋 View Tasks", "➕ Add Task", "🔄 Update", "🔍 Search Task", "🗑️ Delete Task", "ℹ️ More Information"]
)

st.title("📝 My To-Do List")

# ────────── VIEW TASKS ────────── #
if tab == "📋 View Tasks":
    st.subheader("📊 Filter & View Tasks")
    status_filter = st.radio("Filter by Priority", ["All", "High", "Medium", "Low"])
    tasks = get_tasks(status_filter)
    if tasks:
        # Prepare updated table with Overdue/Upcoming info
        enhanced_data = []
        for task in tasks:
            task_id, name, status, tags, priority, pending_days = task
            if pending_days < 0:
                deadline_status = f"❌ Overdue ({abs(pending_days)} days ago)"
            elif pending_days == 0:
                deadline_status = "⚠️ Due Today"
            else:
                deadline_status = f"✅ {pending_days} days left"
            enhanced_data.append([task_id, name, status, tags, priority, deadline_status])

        df = pd.DataFrame(enhanced_data, columns=["ID", "Task Name", "Status", "Tags", "Priority", "Deadline Status"])
        st.table(df)
    else:
        
        st.info("No tasks found.")

# ────────── ADD TASK ────────── #
elif tab == "➕ Add Task":
    st.subheader("Add a New Task")
    task_name = st.text_input("Task Name")
    tag = tags()
    due = st.date_input("Select Due Date")
    today = datetime.date.today()
    pending_days = (due - today).days
    task_info = st.text_input("Task Information")
    status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])

    if st.button("Add Task"):
        if task_name:
            inserttask(task_name, status, tag, priority, due, today, pending_days, task_info)
        else:
            st.warning("⚠️ Please enter a task name.")

# ────────── UPDATE TASK ────────── #
elif tab == "🔄 Update":
    st.subheader("Update Task")
    task_id = st.number_input("Task ID", step=1, min_value=1)
    column = st.radio("Update:", ["Status", "Priority", "Tags","Due Date","Information"])

    if column == "Status":
        new_val = st.selectbox("New Status", ["Pending", "In Progress", "Completed"])
    elif column == "Priority":
        new_val = st.selectbox("New Priority", ["High", "Medium", "Low"])
    elif column == "Tags":
        new_val = tags()
    elif column == "Due Date":
        new_val = st.date_input("Select Due Date")
    else:
        new_val = st.text_input("Task Information")
        

    if st.button("Update"):
        update_status(task_id, new_val, column)

# ────────── SEARCH TASK ────────── #
elif tab == "🔍 Search Task":
    st.subheader("Search for a Task")
    search_by = st.radio("Search by", ["Status", "ID", "Tags"])

    if search_by == "Status":
        value = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
    elif search_by == "Tags":
        value = st.text_input("Enter tag value")
    else:
        value = st.number_input("Enter Task ID to Search", step=1, min_value=1)

    if st.button("Search"):
        results = search_task(search_by, value)
        if results:
            df = pd.DataFrame(results, columns=["ID", "Task Name", "Status", "Tags", "Priority","Due Date", "Date of Entry", "Pending Days", "Information"
        ])
            st.table(df)
        else:
            st.warning("No results found.")

# ────────── DELETE TASK ────────── #
elif tab == "🗑️ Delete Task":
    st.subheader("Delete Tasks")
    del_type = st.radio("Delete Type", ["ID", "All"])
    if del_type == "All":
        if st.button("Delete All Tasks"):
            delete_task("All")
    else:
        task_id = st.number_input("Enter Task ID to Delete", step=1, min_value=1)
        if st.button("Delete Task"):
            delete_task("ID", task_id)

# ────────── MORE INFORMATION ────────── #
elif tab == "ℹ️ More Information":
    st.subheader("More Information")
    tid = st.number_input("Enter Task ID", step=1, min_value=1)
    if st.button("Get Info"):
        moreinfo(tid)
