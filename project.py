# ==============================
# Pcs Distribution Converter (MySQL → NoSQL)
# ==============================

# Run this in MySQL first (if not already done):
# CREATE DATABASE pc_data;
# USE pc_data;
# CREATE TABLE calculations (
#    id INT AUTO_INCREMENT PRIMARY KEY,
#    date DATETIME,
#    pcs INT,
#    a_values TEXT,
#    results TEXT,
#    nc_values TEXT,
#    dechet_values TEXT
# );
# ==============================# ==============================
# Pcs Distribution Converter (MySQL → NoSQL)
# ==============================

import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime
from pymongo import MongoClient

# ---------- DATABASE SETUP ----------
mysql_conn = None
mysql_cursor = None

try:
    mysql_conn = mysql.connector.connect(
        host="localhost",
        user="root",               # change to your MySQL username
        password="your_password",  # change to your MySQL password
        database="pc_data"
    )
    mysql_cursor = mysql_conn.cursor()
except mysql.connector.Error as e:
    messagebox.showerror("Database Error", f"MySQL Connection Error:\n{e}")

# MongoDB setup
try:
    mongo_client = MongoClient("mongodb://localhost:27017/")
    mongo_db = mongo_client["pc_data"]
    mongo_collection = mongo_db["calculations_nosql"]
except Exception as e:
    messagebox.showerror("Database Error", f"MongoDB Connection Error:\n{e}")

# ---------- APP SETTINGS ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ---------- FUNCTIONS ----------


def save_to_mysql(Pcs, A, Pc_final, NC, Dechet, time_divider):
    if not mysql_conn:
        messagebox.showerror("Database Error", "MySQL not connected.")
        return
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    a_values = ",".join(map(str, A))
    results = ",".join([f"{v:.2f}" for v in Pc_final])
    nc_values = ",".join(map(str, NC))
    dechet_values = ",".join(map(str, Dechet))
    mysql_cursor.execute(
        "INSERT INTO calculations (date, pcs, a_values, results, nc_values, dechet_values, time_divider) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (date, Pcs, a_values, results, nc_values, dechet_values, time_divider)
    )
    mysql_conn.commit()


def calculate():
    try:
        Pcs = int(entry_pcs.get())
        A = [int(entry.get() or 0) for entry in A_entries]
        NC = [int(entry.get() or 0) for entry in NC_entries]
        Dechet = [int(entry.get() or 0) for entry in Dechet_entries]
        time_divider = float(entry_time.get() or 15)

        S = 16 * 60 / time_divider
        Pc = [(60 - a) * S if a > 0 else 0 for a in A]
        z = sum(Pc)
        Pc0_total = Pcs - z
        NA = [1 if a == 0 else 0 for a in A]
        y = sum(NA)
        Pc0_each = Pc0_total // y if y > 0 else 0
        Pc_final = [round(pc + (Pc0_each if na == 1 else 0), 2)
                    for pc, na in zip(Pc, NA)]

        for row in table.get_children():
            table.delete(row)

        for i, (a, nc, de, pc_final_value) in enumerate(zip(A, NC, Dechet, Pc_final), start=1):
            table.insert("", "end", values=(
                f"A{i}", a, nc, de, f"{pc_final_value:.2f}"))

        total_label.configure(text=f"Total = {Pcs}")
        save_to_mysql(Pcs, A, Pc_final, NC, Dechet, time_divider)

    except ValueError:
        messagebox.showerror(
            "Input Error", "Please enter valid numeric values.")
    except mysql.connector.Error as e:
        messagebox.showerror("MySQL Error", str(e))


def clear_all():
    entry_pcs.delete(0, "end")
    entry_time.delete(0, "end")
    entry_time.insert(0, "15")
    for entry_list in [A_entries, NC_entries, Dechet_entries]:
        for entry in entry_list:
            entry.delete(0, "end")
            entry.insert(0, "0")
    for row in table.get_children():
        table.delete(row)
    total_label.configure(text="Total = 0")


def view_data():
    if not mysql_conn:
        messagebox.showerror("Database Error", "MySQL not connected.")
        return

    view_win = ctk.CTkToplevel(app)
    view_win.title("📊 Saved Calculations (MySQL)")
    view_win.geometry("1000x450")

    cols = ("ID", "Date", "Pcs", "Stop Time", "Results",
            "NC Values", "Déchet Values", "Time Divider")
    view_table = ttk.Treeview(view_win, columns=cols,
                              show="headings", height=15)
    for col in cols:
        view_table.heading(col, text=col)
        view_table.column(col, anchor="center", width=120)

    scrollbar = ttk.Scrollbar(
        view_win, orient="vertical", command=view_table.yview)
    view_table.configure(yscroll=scrollbar.set)
    view_table.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    mysql_cursor.execute("SELECT * FROM calculations ORDER BY id DESC")
    for row in mysql_cursor.fetchall():
        view_table.insert("", "end", values=row)


def convert_to_nosql():
    try:
        if not mysql_conn:
            messagebox.showerror("Database Error", "MySQL not connected.")
            return

        mysql_cursor.execute("SELECT * FROM calculations")
        records = mysql_cursor.fetchall()

        if not records:
            messagebox.showinfo(
                "Info", "No records found in MySQL to convert.")
            return

        mongo_collection.delete_many({})

        for row in records:
            doc = {
                "_id": row[0],
                "date": row[1].strftime("%Y-%m-%d %H:%M:%S"),
                "pcs": row[2],
                "a_values": row[3].split(","),
                "results": row[4].split(","),
                "nc_values": row[5].split(","),
                "dechet_values": row[6].split(","),
                "time_divider": row[7]
            }
            mongo_collection.replace_one({"_id": row[0]}, doc, upsert=True)

        messagebox.showinfo(
            "Success", f"✅ {len(records)} records exported to MongoDB.")
    except Exception as e:
        messagebox.showerror("Conversion Error", str(e))


def on_close():
    try:
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
        if mongo_client:
            mongo_client.close()
    except:
        pass
    app.destroy()


# ---------- UI SETUP ----------
app = ctk.CTk()
app.title("Pcs Distribution Converter (MySQL → NoSQL)")
app.geometry("900x740")
app.protocol("WM_DELETE_WINDOW", on_close)

main_frame = ctk.CTkFrame(app, corner_radius=15)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# --- Title ---
ctk.CTkLabel(
    main_frame,
    text="Pcs Distribution Calculator",
    font=("Segoe UI", 24, "bold"),
    justify="center"
).pack(pady=(5, 15))

input_frame = ctk.CTkFrame(main_frame)
input_frame.pack(pady=10)

# --- Top Inputs: Pcs + Time Divider ---
ctk.CTkLabel(input_frame, text="Enter Pcs:", font=("Segoe UI", 13)
             ).grid(row=0, column=0, padx=10, pady=6, sticky="e")
entry_pcs = ctk.CTkEntry(input_frame, width=100)
entry_pcs.grid(row=0, column=1, padx=10, pady=6)

ctk.CTkLabel(input_frame, text="Time Divider:", font=("Segoe UI", 13)).grid(
    row=0, column=2, padx=10, pady=6, sticky="e")
entry_time = ctk.CTkEntry(input_frame, width=100)
entry_time.insert(0, "15")
entry_time.grid(row=0, column=3, padx=10, pady=6)

# ---------- ALIGNED INPUT SECTIONS ----------
A_entries = []
Dechet_entries = []
NC_entries = []

# Safe container to use pack without grid conflict
section_container = ctk.CTkFrame(input_frame, fg_color="transparent")
section_container.grid(row=1, column=0, columnspan=4, pady=10)


def create_grid_section(parent, title, prefix, entries_list):
    """Create 4-column aligned input sections"""
    section = ctk.CTkFrame(parent, fg_color="transparent")
    section.pack(pady=10)

    ctk.CTkLabel(section, text=title, font=(
        "Segoe UI", 14, "bold")).pack(pady=(5, 5))

    grid_frame = ctk.CTkFrame(section, fg_color="transparent")
    grid_frame.pack()

    for i in range(8):
        row = i // 4
        col = (i % 4)
        cell = ctk.CTkFrame(grid_frame, fg_color="transparent")
        cell.grid(row=row, column=col, padx=8, pady=4)

        ctk.CTkLabel(cell, text=f"{prefix}{i+1}:",
                     font=("Segoe UI", 12)).pack(side="left", padx=(0, 4))
        entry = ctk.CTkEntry(cell, width=70)
        entry.insert(0, "0")
        entry.pack(side="right")
        entries_list.append(entry)


# --- Create Sections ---
create_grid_section(section_container, "Stop Time", "A", A_entries)
create_grid_section(section_container, "DÉCHET", "D", Dechet_entries)
create_grid_section(section_container, "NC", "N", NC_entries)

# ---------- BUTTONS ----------
btn_frame = ctk.CTkFrame(main_frame)
btn_frame.pack(pady=15)

ctk.CTkButton(btn_frame, text="Calculate", command=calculate,
              width=130).grid(row=0, column=0, padx=10)
ctk.CTkButton(btn_frame, text="Clear All", command=clear_all, fg_color="#444",
              hover_color="#666", width=130).grid(row=0, column=1, padx=10)
ctk.CTkButton(btn_frame, text="View SQL Data", command=view_data, fg_color="#225",
              hover_color="#338", width=160).grid(row=0, column=2, padx=10)
ctk.CTkButton(btn_frame, text="Convert SQL → NoSQL", command=convert_to_nosql,
              fg_color="#065f46", hover_color="#047857", width=200).grid(row=0, column=3, padx=10)

# ---------- TABLE ----------
table_frame = ctk.CTkFrame(main_frame)
table_frame.pack(pady=10)

columns = ("Index", "Stop Time", "NC", "Déchet", "Pc (final)")
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background="#1e1e1e", foreground="white",
                fieldbackground="#1e1e1e", rowheight=28, font=("Segoe UI", 11))
style.map("Treeview", background=[("selected", "#007acc")])

table = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
for col in columns:
    table.heading(col, text=col)
    table.column(col, anchor="center", width=120)

scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
table.configure(yscroll=scrollbar.set)
table.grid(row=0, column=0)
scrollbar.grid(row=0, column=1, sticky="ns")

total_label = ctk.CTkLabel(
    main_frame, text="Total = 0", font=("Segoe UI", 16, "bold"))
total_label.pack(pady=15)

ctk.CTkLabel(main_frame, text="Developed by Abdeladim", font=(
    "Segoe UI", 10, "italic"), text_color="#888").pack(side="bottom", pady=10)

app.mainloop()
