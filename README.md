# 🧮 CTk PC Distribution Converter (MySQL → NoSQL)

A modern **Python GUI application** built with **CustomTkinter**, designed to calculate and manage production performance data.  
It allows users to input, compute, and distribute PC (performance count) values for each hour while tracking **NC (Not Conform)** and **Déchet (Waste)** per hour.  
All results are stored in **MySQL** and can be exported to **MongoDB** (NoSQL) with one click.

---

## 🚀 Features

✅ **Real-Time Calculation**
- Input production values (`A1–A8`) and calculate PC distribution automatically.  
- Adjust the *time divider* dynamically to control calculations.

✅ **Data Management**
- Automatically saves results in a local **MySQL** database.  
- Instantly exports or synchronizes data to **MongoDB (NoSQL)**.

✅ **Modern User Interface**
- Built with **CustomTkinter** (dark mode, responsive design).  
- Clean layout: 4 columns for inputs, compact view, and summary table.

✅ **Additional Metrics**
- Includes **NC (Not OK)** and **Déchet (Waste)** tracking for each hour.  
- Displays final PC values for each time slot.

---

## 🧠 How It Works

1. **Enter Total Pcs** – total number of parts produced or processed.  
2. **Set Time Divider** – default is `15`, but you can modify it.  
3. **Input Values**
   - `A1–A8`: hourly production counts.
   - `N1–N8`: non-conform (NC) counts.
   - `D1–D8`: waste (Déchet) counts.
4. Click **Calculate** → results are instantly displayed and saved to MySQL.
5. Click **Convert SQL → NoSQL** → exports data to MongoDB automatically.

---

## 🗄️ Database Structure

### **MySQL Table: `calculations`**
| Column | Type | Description |
|---------|------|-------------|
| id | INT | Auto Increment Primary Key |
| date | DATETIME | Timestamp of record |
| pcs | INT | Total pieces |
| a_values | TEXT | A1–A8 values |
| results | TEXT | Final PC results |
| nc_values | TEXT | NC1–NC8 values |
| dechet_values | TEXT | D1–D8 values |
| time_divider | FLOAT | Custom divider used |

### **MongoDB Collection: `calculations_nosql`**
Stores the same data structure in a document-oriented format.

---

## ⚙️ Installation

### Prerequisites
Make sure you have:
- Python 3.10 or newer  
- MySQL and MongoDB installed and running locally

### Install dependencies:
```bash
pip install customtkinter mysql-connector-python pymongo
