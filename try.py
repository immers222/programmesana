from flask import Flask, request, jsonify, render_template_string
import sqlite3
import hashlib

app = Flask(__name__)
DB_NAME = "expenses.db"


def init_db():
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
        user_id INTEGER,
        amount REAL,
        category TEXT,
        date TEXT,
        description TEXT
    )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def validate_credentials(username, password):
    if len(username) < 4:
        return "Username must contain at least 4 characters"

    if " " in username:
        return "Username cannot contain spaces"

    if len(password) < 8:
        return "Password must contain at least 8 characters"

    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number"

    return None


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Expense Tracker</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }

        body {
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            padding: 40px 20px;
        }

        .container {
            max-width: 1200px;
            margin: auto;
        }

        #login-card {
            max-width: 420px;
            margin: 60px auto;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 24px;
            padding: 36px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.35);
        }

        #app {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 24px;
        }

        .sidebar {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 24px;
            padding: 28px;
            height: fit-content;
            position: sticky;
            top: 20px;
        }

        .main-content {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        h1 {
            font-size: 34px;
            margin-bottom: 8px;
            color: #f8fafc;
        }

        h2 {
            font-size: 22px;
            margin-bottom: 18px;
            color: #f8fafc;
        }

        .subtitle {
            color: #94a3b8;
            margin-bottom: 28px;
            line-height: 1.5;
        }

        label {
            display: block;
            margin-bottom: 8px;
            margin-top: 16px;
            color: #cbd5e1;
            font-size: 14px;
        }

        input {
            width: 100%;
            background: #0f172a;
            border: 1px solid #475569;
            color: #f8fafc;
            border-radius: 14px;
            padding: 14px;
            font-size: 14px;
            transition: 0.2s;
        }

        input:focus {
            outline: none;
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px rgba(56,189,248,0.2);
        }

        .password-wrapper {
            display: flex;
            gap: 10px;
        }

        .password-wrapper input {
            flex: 1;
        }

        button {
            border: none;
            border-radius: 14px;
            padding: 14px 18px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
        }

        .primary-btn {
            background: linear-gradient(135deg, #2563eb, #38bdf8);
            color: white;
        }

        .primary-btn:hover {
            transform: translateY(-2px);
        }

        .secondary-btn {
            background: #334155;
            color: #f8fafc;
        }

        .secondary-btn:hover {
            background: #475569;
        }

        .danger-btn {
            background: #7f1d1d;
            color: white;
        }

        .danger-btn:hover {
            background: #991b1b;
        }

        .actions {
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            overflow: hidden;
        }

        th {
            text-align: left;
            padding: 16px;
            background: #0f172a;
            color: #93c5fd;
            font-size: 13px;
            letter-spacing: 0.5px;
        }

        td {
            padding: 16px;
            border-top: 1px solid #334155;
            color: #e2e8f0;
        }

        tr:hover {
            background: rgba(255,255,255,0.03);
        }

        .summary-item {
            display: flex;
            justify-content: space-between;
            padding: 14px 16px;
            margin-top: 10px;
            background: #0f172a;
            border-radius: 14px;
            border: 1px solid #334155;
        }

        .total-box {
            margin-top: 16px;
            padding: 18px;
            border-radius: 16px;
            background: linear-gradient(135deg, #1d4ed8, #0ea5e9);
            color: white;
            font-size: 18px;
            font-weight: bold;
            text-align: center;
        }

        #login-message {
            margin-top: 18px;
            color: #fca5a5;
        }

        @media (max-width: 900px) {
            #app {
                grid-template-columns: 1fr;
            }

            .sidebar {
                position: static;
            }
        }
    </style>
</head>
<body>
    <div class="container">

        <div id="login-screen">
    <div id="login-card" class="card">
            <h1>Expense Tracker</h1>
            <div class="subtitle">Track your expenses, manage categories and view monthly summaries.</div>
            <h2>Login / Register</h2>

            <input id="username" placeholder="Username">
            <div class="password-wrapper">
                <input id="password" type="password" placeholder="Password">
                <button type="button" class="toggle-btn" onclick="togglePassword()">Show</button>
            </div>
            <br>
            <div class="actions">
                <button class="secondary" onclick="register()">Register</button>
                <button onclick="login()">Login</button>
            </div>
            <p id="login-message"></p>
        </div>

            </div>
</div>

<div id="app" class="hidden">
            <div class="sidebar">
                <h2>Add Expense</h2>

                <label>Amount *</label>
                <input id="amount" type="number" step="0.01" placeholder="Example: 12.50">

                <label>Category *</label>
                <input id="category" placeholder="Food, Transport, Bills...">

                <label>Date *</label>
                <input id="date" type="date">

                <label>Description</label>
                <input id="description" placeholder="Optional note">

                <div class="actions">
                    <button class="primary-btn" onclick="addExpense()">Add Expense</button>
                </div>
            </div>

            <div class="main-content">
                <div class="card">
                    <h2>Saved Expenses</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Amount</th>
                                <th>Category</th>
                                <th>Date</th>
                                <th>Description</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody id="expense-table"></tbody>
                    </table>
                </div>

                <div class="card">
                    <h2>Monthly Summary</h2>
                    <div style="display:flex; gap:12px; margin-bottom:18px; flex-wrap:wrap;">
                        <input id="month" placeholder="YYYY-MM" style="max-width:180px;">
                        <button class="primary-btn" onclick="loadSummary()">Generate Summary</button>
                    </div>
                    <div id="summary"></div>
                </div>
            </div>
        </div>
    </div>
        </div>
    </div>

<script>
let currentUserId = null;

async function register() {
    const response = await fetch('/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        })
    });

    const data = await response.json();
    document.getElementById('login-message').innerText =
        data.status === 'ok' ? 'User registered successfully' : data.message;
}

async function login() {
    const response = await fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        })
    });

    const data = await response.json();

    if (data.status === 'ok') {
        currentUserId = data.user_id;

        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('app').classList.remove('hidden');

        loadExpenses();
    } else {
        document.getElementById('login-message').innerText = data.message;
    }
}

async function addExpense() {
    const amount = document.getElementById('amount').value.trim();
    const category = document.getElementById('category').value.trim();
    const date = document.getElementById('date').value.trim();
    const description = document.getElementById('description').value.trim();

    if (!amount || !category || !date) {
        alert('Amount, Category and Date are required fields.');
        return;
    }

    await fetch('/expenses', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: currentUserId,
            amount: amount,
            category: category,
            date: date,
            description: description
        })
    });

    document.getElementById('amount').value = '';
    document.getElementById('category').value = '';
    document.getElementById('date').value = '';
    document.getElementById('description').value = '';

    loadExpenses();
}

async function loadExpenses() {
    const response = await fetch(`/expenses?user_id=${currentUserId}`);
    const expenses = await response.json();

    const table = document.getElementById('expense-table');
    table.innerHTML = '';

    expenses.forEach(expense => {
        table.innerHTML += `
            <tr>
                <td>${expense[0]}</td>
                <td>${expense[1]} €</td>
                <td>${expense[2]}</td>
                <td>${expense[3]}</td>
                <td>${expense[4]}</td>
                <td><button class="delete-btn" onclick="deleteExpense(${expense[0]})">Delete</button></td>
            </tr>
        `;
    });
}

async function deleteExpense(id) {
    await fetch(`/expenses/${id}`, {method: 'DELETE'});
    loadExpenses();
}

async function loadSummary() {
    const month = document.getElementById('month').value;

    const response = await fetch(`/summary?user_id=${currentUserId}&month=${month}`);
    const summary = await response.json();

    const div = document.getElementById('summary');
    div.innerHTML = '';

    if (summary.length === 0) {
        div.innerHTML = '<p>No expenses for this month.</p>';
        return;
    }

    let total = 0;

    summary.forEach(item => {
        total += item[1];
        div.innerHTML += `<div class="summary-item"><b>${item[0]}</b>: ${item[1].toFixed(2)} €</div>`;
    });

    div.innerHTML += `<hr><h3>Total: ${total.toFixed(2)} €</h3>`;
}
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const button = document.querySelector('.toggle-btn');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        button.innerText = 'Hide';
    } else {
        passwordInput.type = 'password';
        button.innerText = 'Show';
    }
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/register", methods=["POST"])
def register():
    data = request.json

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    validation_error = validate_credentials(data["username"], data["password"])

    if validation_error:
        conn.close()
        return jsonify({"status": "error", "message": validation_error})

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (data["username"], hash_password(data["password"]))
        )
        conn.commit()
        return jsonify({"status": "ok"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Username already exists"})
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

    return jsonify({"status": "error", "message": "Invalid username or password"})


@app.route("/expenses", methods=["GET"])
def get_expenses():
    user_id = request.args.get("user_id")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, amount, category, date, description FROM expenses WHERE user_id=? ORDER BY date DESC",
        (user_id,)
    )

    expenses = cur.fetchall()
    conn.close()

    return jsonify(expenses)


@app.route("/expenses", methods=["POST"])
def add_expense():
    data = request.json

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (data["user_id"], data["amount"], data["category"], data["date"], data["description"])
    )

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
    user_id = request.args.get("user_id")
    month = request.args.get("month")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=? AND substr(date, 1, 7)=?
        GROUP BY category
        """,
        (user_id, month)
    )

    result = cur.fetchall()
    conn.close()

    return jsonify(result)


if __name__ == "__main__":
    import threading
    import webbrowser
    import time

    init_db()

    def open_browser():
        time.sleep(1)
        webbrowser.open("http://127.0.0.1:5000")

    threading.Thread(target=open_browser, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
