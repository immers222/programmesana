import sqlite3
import hashlib
import threading
import time
from flask import Flask, request, jsonify
import tkinter as tk
from tkinter import ttk, messagebox
import requests

DB_NAME = "expenses.db"
API_URL = "http://127.0.0.1:5000"


# =========================
# DATABASE
# =========================
def create_database():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            date TEXT,
            description TEXT
        )
    """)

    # Ja vecā datubāzē nav user_id kolonnas, pievieno
    cur.execute("PRAGMA table_info(expenses)")
    columns = [c[1] for c in cur.fetchall()]

    if "user_id" not in columns:
        cur.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER")

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =========================
# API
# =========================
app = Flask(__name__)


@app.route("/register", methods=["POST"])
def register():
    data = request.json

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (data["username"], hash_password(data["password"]))
        )
        conn.commit()
        return jsonify({"status": "ok"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "User already exists"})
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE username=? AND password=?",
        (data["username"], hash_password(data["password"]))
    )

    user = cur.fetchone()
    conn.close()

    if user:
        return jsonify({"status": "ok", "user_id": user[0]})

    return jsonify({"status": "error", "message": "Wrong username or password"})


@app.route("/expenses", methods=["GET"])
def get_expenses():
    user_id = int(request.args.get("user_id"))

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, amount, category, date, description
        FROM expenses
        WHERE user_id=?
        ORDER BY date DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return jsonify(rows)


@app.route("/expenses", methods=["POST"])
def add_expense():
    data = request.json

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["user_id"],
        data["amount"],
        data["category"],
        data["date"],
        data["description"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("DELETE FROM expenses WHERE id=?", (expense_id,))

    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


@app.route("/summary", methods=["GET"])
def summary():
    user_id = int(request.args.get("user_id"))
    month = request.args.get("month")  # piemērs: 2026-04

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=? AND substr(date, 1, 7)=?
        GROUP BY category
    """, (user_id, month))

    data = cur.fetchall()
    conn.close()

    return jsonify(data)


# =========================
# UI
# =========================
class ExpenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("850x600")

        self.user_id = None

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        self.show_login()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # =========================
    # LOGIN
    # =========================
    def show_login(self):
        self.clear_frame()

        login_frame = tk.LabelFrame(self.main_frame, text="Login", padx=20, pady=20)
        login_frame.pack(pady=50)

        tk.Label(login_frame, text="Username").grid(row=0, column=0, sticky="w")
        self.username_entry = tk.Entry(login_frame, width=30)
        self.username_entry.grid(row=1, column=0, pady=5)

        tk.Label(login_frame, text="Password").grid(row=2, column=0, sticky="w")
        self.password_entry = tk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=3, column=0, pady=5)

        tk.Button(login_frame, text="Login", width=15, command=self.login).grid(row=4, column=0, pady=5)
        tk.Button(login_frame, text="Register", width=15, command=self.register).grid(row=5, column=0, pady=5)

    def login(self):
        response = requests.post(API_URL + "/login", json={
            "username": self.username_entry.get(),
            "password": self.password_entry.get()
        }).json()

        if response["status"] == "ok":
            self.user_id = response["user_id"]
            self.show_main()
        else:
            messagebox.showerror("Login failed", response["message"])

    def register(self):
        response = requests.post(API_URL + "/register", json={
            "username": self.username_entry.get(),
            "password": self.password_entry.get()
        }).json()

        if response["status"] == "ok":
            messagebox.showinfo("Success", "User registered successfully")
        else:
            messagebox.showerror("Error", response["message"])

    # =========================
    # MAIN SCREEN
    # =========================
    def show_main(self):
        self.clear_frame()

        # ---------- Add expense ----------
        add_frame = tk.LabelFrame(self.main_frame, text="Add Expense", padx=10, pady=10)
        add_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(add_frame, text="Amount").grid(row=0, column=0, sticky="w")
        self.amount_entry = tk.Entry(add_frame, width=15)
        self.amount_entry.grid(row=1, column=0, padx=5)

        tk.Label(add_frame, text="Category").grid(row=0, column=1, sticky="w")
        self.category_entry = tk.Entry(add_frame, width=20)
        self.category_entry.grid(row=1, column=1, padx=5)

        tk.Label(add_frame, text="Date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w")
        self.date_entry = tk.Entry(add_frame, width=15)
        self.date_entry.grid(row=1, column=2, padx=5)

        tk.Label(add_frame, text="Description").grid(row=0, column=3, sticky="w")
        self.description_entry = tk.Entry(add_frame, width=30)
        self.description_entry.grid(row=1, column=3, padx=5)

        tk.Button(add_frame, text="Add Expense", command=self.add_expense).grid(row=1, column=4, padx=10)

        # ---------- Table ----------
        table_frame = tk.LabelFrame(self.main_frame, text="Expenses")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "amount", "category", "date", "description"),
            show="headings"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("category", text="Category")
        self.tree.heading("date", text="Date")
        self.tree.heading("description", text="Description")

        self.tree.column("id", width=50)
        self.tree.column("amount", width=100)
        self.tree.column("category", width=150)
        self.tree.column("date", width=120)
        self.tree.column("description", width=300)

        self.tree.pack(fill="both", expand=True)

        # ---------- Bottom actions ----------
        bottom_frame = tk.Frame(self.main_frame)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="Delete Selected", command=self.delete_expense).pack(side="left", padx=5)

        tk.Label(bottom_frame, text="Month (YYYY-MM)").pack(side="left", padx=5)
        self.month_entry = tk.Entry(bottom_frame, width=10)
        self.month_entry.pack(side="left")

        tk.Button(bottom_frame, text="Show Monthly Summary", command=self.show_summary).pack(side="left", padx=5)

        self.load_expenses()

    # =========================
    # FUNCTIONS
    # =========================
    def load_expenses(self):
        data = requests.get(API_URL + "/expenses", params={
            "user_id": self.user_id
        }).json()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in data:
            self.tree.insert("", "end", values=row)

    def clear_inputs(self):
        self.amount_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)

    def add_expense(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number")
            return

        response = requests.post(API_URL + "/expenses", json={
            "user_id": self.user_id,
            "amount": amount,
            "category": self.category_entry.get(),
            "date": self.date_entry.get(),
            "description": self.description_entry.get()
        }).json()

        if response["status"] == "ok":
            self.clear_inputs()
            self.load_expenses()

    def delete_expense(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Select an expense first")
            return

        expense_id = self.tree.item(selected[0])["values"][0]

        requests.delete(API_URL + f"/expenses/{expense_id}")
        self.load_expenses()

    def show_summary(self):
        month = self.month_entry.get()

        if not month:
            messagebox.showwarning("Warning", "Enter month in format YYYY-MM")
            return

        data = requests.get(API_URL + "/summary", params={
            "user_id": self.user_id,
            "month": month
        }).json()

        summary_window = tk.Toplevel(self.root)
        summary_window.title(f"Summary for {month}")
        summary_window.geometry("300x250")

        tk.Label(
            summary_window,
            text=f"Monthly Summary: {month}",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        if not data:
            tk.Label(summary_window, text="No expenses for this month").pack()
            return

        for category, total in data:
            tk.Label(
                summary_window,
                text=f"{category}: {total:.2f}"
            ).pack(anchor="w", padx=20)

        total_sum = sum(item[1] for item in data)

        tk.Label(
            summary_window,
            text=f"\nTotal: {total_sum:.2f}",
            font=("Arial", 12, "bold")
        ).pack(pady=10)


# =========================
# RUN
# =========================
def start_api():
    create_database()
    app.run(use_reloader=False)


if __name__ == "__main__":
    threading.Thread(target=start_api, daemon=True).start()
    time.sleep(1)

    root = tk.Tk()
    ExpenseApp(root)
    root.mainloop()