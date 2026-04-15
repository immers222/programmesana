import unittest
import requests
import sqlite3
import time
import threading

# IMPORTĒ TAVU APP FAILU
import app   # ⚠️ failam jābūt app.py

API_URL = "http://127.0.0.1:5000"
DB_NAME = "expenses.db"


class TestExpenseApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 🔥 START SERVER AUTOMĀTISKI
        def run_server():
            app.create_database()
            app.app.run(use_reloader=False)

        cls.server_thread = threading.Thread(target=run_server, daemon=True)
        cls.server_thread.start()

        # pagaidām līdz serveris startē
        time.sleep(2)

        # notīra DB
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM users")
        cur.execute("DELETE FROM expenses")
        conn.commit()
        conn.close()

        # izveido user
        requests.post(API_URL + "/register", json={
            "username": "testuser",
            "password": "1234"
        })

        r = requests.post(API_URL + "/login", json={
            "username": "testuser",
            "password": "1234"
        }).json()

        cls.user_id = r["user_id"]

    def test_add_expense(self):
        r = requests.post(API_URL + "/expenses", json={
            "user_id": self.__class__.user_id,
            "amount": 10,
            "category": "food",
            "date": "2026-04-10",
            "description": "test"
        }).json()

        self.assertEqual(r["status"], "ok")

    def test_get_expenses(self):
        r = requests.get(API_URL + "/expenses", params={
            "user_id": self.__class__.user_id
        }).json()

        self.assertTrue(len(r) > 0)

    def test_summary(self):
        r = requests.get(API_URL + "/summary", params={
            "user_id": self.__class__.user_id,
            "month": "2026-04"
        }).json()

        self.assertTrue(isinstance(r, list))

    def test_delete(self):
        r = requests.get(API_URL + "/expenses", params={
            "user_id": self.__class__.user_id
        }).json()

        if r:
            eid = r[0][0]
            d = requests.delete(API_URL + f"/expenses/{eid}").json()
            self.assertEqual(d["status"], "deleted")


if __name__ == "__main__":
    unittest.main()