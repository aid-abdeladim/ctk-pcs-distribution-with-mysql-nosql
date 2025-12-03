import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector.cursor import MySQLCursor

# =====================================
#  DATABASE SETUP
# =====================================
mysql_conn = None
mysql_cursor: MySQLCursor | None = None

try:
    mysql_conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="pc_data"
    )

    mysql_cursor = mysql_conn.cursor()

    mysql_cursor.execute("""
        CREATE TABLE IF NOT EXISTS calculations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pcs INT,
            time_divider FLOAT,
            a_values VARCHAR(255),
            nc_values VARCHAR(255),
            dechet_values VARCHAR(255),
            pcc_values VARCHAR(255),
            r_value INT
        )
    """)
    mysql_conn.commit()

except mysql.connector.Error as e:
    messagebox.showerror("Database Error", f"MySQL Connection Error:\n{e}")

# =====================================================
#  SAVE RESULTS TO MYSQL
# =====================================================


def save_to_mysql(Pcs, time_divider, A, Pc_final, NC, Dechet, PCC, r):
    if not mysql_conn or not mysql_cursor or not mysql_conn.is_connected():
        messagebox.showerror("Database Error", "MySQL not connected.")
        return

    try:
        a_values = ",".join(map(str, A))
        nc_values = ",".join(map(str, NC))
        dechet_values = ",".join(map(str, Dechet))
        pcc_values = ",".join(map(str, PCC))

        mysql_cursor.execute(
            """
            INSERT INTO calculations 
                (pcs, time_divider, a_values, nc_values, dechet_values, pcc_values, r_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (Pcs, time_divider, a_values, nc_values, dechet_values, pcc_values, r)
        )
        mysql_conn.commit()

        display_results_table(A, NC, Dechet, PCC, r)

    except mysql.connector.Error as e:
        messagebox.showerror("MySQL Save Error", str(e))


#  RESULTS DISPLAY WINDOW
def display_results_table(A, NC, Dechet, PCC, r):
    win = ctk.CTkToplevel()
    win.title("Calculation Results - NC, Dechet, A & PCC")
    win.geometry("650x450")
    win.configure(fg_color=GLOBAL_BG)
    win.attributes("-topmost", True)

    ctk.CTkLabel(
        win, text="Results (A, NC, Dechet, PCC)",
        font=("Segoe UI", 20, "bold")
    ).pack(pady=10)

    # r display
    r_frame = ctk.CTkFrame(win, fg_color=GLOBAL_BG)
    r_frame.pack(pady=(0, 10))

    ctk.CTkLabel(r_frame, text="Remaining r value:", font=(
        "Segoe UI", 14)).pack(side="left", padx=5)
    ctk.CTkLabel(
        r_frame,
        text=f"{r}",
        font=("Segoe UI", 14, "bold"),
        text_color="#FF6B6B" if r != 0 else "#4ECDC4"
    ).pack(side="left")

    # Table frame
    frame = ctk.CTkFrame(win, fg_color=GLOBAL_BG)
    frame.pack(padx=10, pady=10, fill="both", expand=True)

    cols = ("Index", "A", "NC", "Dechet", "PCC")
    table = ttk.Treeview(frame, columns=cols, show="headings")

    for col in cols:
        table.heading(col, text=col)
        table.column(col, anchor="center", width=120 if col != "Index" else 80)

    table.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    for i in range(len(A)):
        table.insert("", "end", values=(i + 1, A[i], NC[i], Dechet[i], PCC[i]))


#  CALCULATION LOGIC
def calculate():
    try:
        Pcs = int(entry_pcs.get())
        A = [int(x.get() or 0) for x in A_entries]
        NC = [int(x.get() or 0) for x in NC_entries]
        Dechet = [int(x.get() or 0) for x in Dechet_entries]
        time_divider = float(entry_time.get() or 15)

        S = 16 * 60 / time_divider
        Pcanc = [(60 - a) * S if a > 0 else 0 for a in A]
        Pcac = [round(x - y, 2) for x, y in zip(Pcanc, NC)]
        z = sum(Pcac)
        Pc0_total = Pcs - z
        NA = [1 if a == 0 else 0 for a in A]
        y = sum(NA)

        Pc0_each = Pc0_total // y if y > 0 else 0

        Pc_final = [round(pc + (Pc0_each if na == 1 else 0), 2)
                    for pc, na in zip(Pcanc, NA)]

        PCC = [int(round(pf - nc, 2)) for pf, nc in zip(Pc_final, NC)]

        k = sum(PCC)
        r = Pcs - k
        r_distributed = 0

        if r != 0 and y > 0:
            idxs = [i for i, a in enumerate(A) if a == 0]
            r_per = r // len(idxs)
            r_rem = r % len(idxs)

            for i in idxs:
                PCC[i] += r_per
                r_distributed += r_per

            for i in idxs:
                if r_rem == 0:
                    break
                PCC[i] += 1 if r > 0 else -1
                r_rem -= 1
                r_distributed += 1 if r > 0 else -1

        k_final = sum(PCC)
        r_final = Pcs - k_final

        save_to_mysql(Pcs, time_divider, A, Pc_final, NC, Dechet, PCC, r_final)

    except Exception as e:
        messagebox.showerror("Error", str(e))


#  MYSQL HISTORY WINDOW
def open_mysql_window():
    if not mysql_conn or not mysql_cursor or not mysql_conn.is_connected():
        messagebox.showerror("MySQL Error", "MySQL not connected.")
        return

    win = ctk.CTkToplevel()
    win.title("MySQL Saved Calculations")
    win.geometry("1100x500")
    win.configure(fg_color=GLOBAL_BG)
    win.attributes("-topmost", True)

    ctk.CTkLabel(win, text="MySQL History", font=(
        "Segoe UI", 20, "bold")).pack(pady=10)

    frame = ctk.CTkFrame(win, fg_color=GLOBAL_BG)
    frame.pack(fill="both", expand=True)

    cols = ("ID", "PCS", "Time Divider", "A", "NC", "Dechet", "PCC", "r")
    table = ttk.Treeview(frame, columns=cols, show="headings")

    for col in cols:
        table.heading(col, text=col)
        table.column(col, width=150, anchor="center")

    table.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(frame, command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    def load():
        table.delete(*table.get_children())
        mysql_cursor.execute(
            "SELECT id, pcs, time_divider, a_values, nc_values, dechet_values, pcc_values, r_value FROM calculations ORDER BY id DESC LIMIT 200")
        for row in mysql_cursor.fetchall():
            table.insert("", "end", values=row)

    load()
    ctk.CTkButton(win, text="Refresh", command=load).pack(pady=10)


#  CLOSE APP
def on_close():
    try:
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
    except:
        pass
    app.destroy()


# UI BLOCK


# APP THEME
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

GLOBAL_BG = "#1a1a1a"
app = ctk.CTk()
app.title("PCS Distribution Calculator")
app.geometry("900x620")
app.configure(fg_color=GLOBAL_BG)
app.protocol("WM_DELETE_WINDOW", on_close)

main_frame = ctk.CTkFrame(app, fg_color=GLOBAL_BG)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

ctk.CTkLabel(
    main_frame,
    text="Pcs Distribution Calculator",
    font=("Segoe UI", 24, "bold")
).pack(pady=10)

# Input Containers
input_frame = ctk.CTkFrame(main_frame, fg_color=GLOBAL_BG)
input_frame.pack(pady=10)

ctk.CTkLabel(input_frame, text="Enter Pcs:", font=(
    "Segoe UI", 13)).grid(row=0, column=0, padx=10)
entry_pcs = ctk.CTkEntry(input_frame, width=100)
entry_pcs.grid(row=0, column=1, padx=10)

ctk.CTkLabel(input_frame, text="Time Divider:", font=(
    "Segoe UI", 13)).grid(row=0, column=2, padx=10)
entry_time = ctk.CTkEntry(input_frame, width=100)
entry_time.insert(0, "15")
entry_time.grid(row=0, column=3, padx=10)

A_entries, Dechet_entries, NC_entries = [], [], []

section_container = ctk.CTkFrame(input_frame, fg_color=GLOBAL_BG)
section_container.grid(row=1, column=0, columnspan=4, pady=10)


def create_section(parent, title, prefix, store_list):
    sec = ctk.CTkFrame(parent, fg_color=GLOBAL_BG)
    ctk.CTkLabel(sec, text=title, font=("Segoe UI", 14, "bold")).pack()
    inner = ctk.CTkFrame(sec, fg_color=GLOBAL_BG)
    inner.pack()

    for i in range(8):
        row = ctk.CTkFrame(inner, fg_color=GLOBAL_BG)
        row.grid(row=i, column=0, pady=4)

        ctk.CTkLabel(row, text=f"{prefix}{i+1}:",
                     font=("Segoe UI", 12)).pack(side="left")
        entry = ctk.CTkEntry(row, width=70)
        entry.insert(0, "0")
        entry.pack(side="right")

        store_list.append(entry)

    return sec


create_section(section_container, "Stop Time (A)", "A",
               A_entries).grid(row=0, column=0, padx=20)
create_section(section_container, "Waste (D)", "D",
               Dechet_entries).grid(row=0, column=1, padx=20)
create_section(section_container, "NC", "N",
               NC_entries).grid(row=0, column=2, padx=20)

# Buttons
btn_frame = ctk.CTkFrame(main_frame, fg_color=GLOBAL_BG)
btn_frame.pack(pady=20)

ctk.CTkButton(btn_frame, text="Calculate", command=calculate,
              width=180).grid(row=0, column=0, padx=10)
ctk.CTkButton(btn_frame, text="MySQL History",
              command=open_mysql_window, width=180).grid(row=0, column=1, padx=10)

ctk.CTkLabel(main_frame, text="Developed by Abdeladim", font=(
    "Segoe UI", 10), text_color="#888").pack(side="bottom", pady=10)

app.mainloop()
