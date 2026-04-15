import sqlite3
import hashlib
from getpass import getpass

DB_NAME = "expenses.db"


# =========================
# DATABASE
# =========================
def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT
        )
    ''')

    conn.commit()
    conn.close()


# =========================
# AUTH (hashlib)
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(password, stored_hash):
    return hash_password(password) == stored_hash


def register():
    username = input("Lietotājvārds: ")
    password = getpass("Parole: ")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        print("✔ Reģistrācija veiksmīga")
    except sqlite3.IntegrityError:
        print("❌ Lietotājs jau eksistē")

    conn.close()


def login():
    username = input("Lietotājvārds: ")
    password = getpass("Parole: ")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, password FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    if user and check_password(password, user[1]):
        print("✔ Ielogots!")
        return user[0]
    else:
        print("❌ Nepareizi dati")
        return None


# =========================
# EXPENSES
# =========================
def add_expense(user_id):
    try:
        amount = float(input("Summa: "))
        category = input("Kategorija: ")
        date = input("Datums (YYYY-MM-DD): ")
        desc = input("Apraksts: ")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, desc)
        )

        conn.commit()
        conn.close()

        print("✔ Pievienots!")

    except ValueError:
        print("❌ Summai jābūt skaitlim")


def view_expenses(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, amount, category, date, description FROM expenses WHERE user_id=?",
        (user_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    if rows:
        for row in rows:
            print(row)
    else:
        print("Nav izdevumu")


def delete_expense(user_id):
    try:
        expense_id = int(input("ID: "))

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM expenses WHERE id=? AND user_id=?",
            (expense_id, user_id)
        )

        conn.commit()
        conn.close()

        print("✔ Dzēsts")

    except ValueError:
        print("❌ ID jābūt skaitlim")


def monthly_summary(user_id):
    month = input("Mēnesis (YYYY-MM): ")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=? AND date LIKE ?",
        (user_id, month + "%")
    )

    total = cursor.fetchone()[0]
    conn.close()

    print("Kopā:", total or 0, "EUR")


# =========================
# MAIN
# =========================
def run_app():
    create_database()

    user_id = None

    # LOGIN / REGISTER
    while not user_id:
        print("\n1. Login")
        print("2. Register")

        choice = input("Izvēle: ")

        if choice == "1":
            user_id = login()
        elif choice == "2":
            register()
        else:
            print("Nepareiza izvēle")

    # APP
    while True:
        print("\n==== ExpenseTracker ====")
        print("1. Pievienot izdevumu")
        print("2. Skatīt izdevumus")
        print("3. Dzēst izdevumu")
        print("4. Mēneša pārskats")
        print("5. Iziet")

        choice = input("Izvēlieties darbību: ")

        if choice == "1":
            add_expense(user_id)
        elif choice == "2":
            view_expenses(user_id)
        elif choice == "3":
            delete_expense(user_id)
        elif choice == "4":
            monthly_summary(user_id)
        elif choice == "5":
            print("Programma beidz darbu.")
            break
        else:
            print("Nepareiza izvēle")


if __name__ == "__main__":
    run_app()