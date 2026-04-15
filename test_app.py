import unittest
from app import add_expense, get_expenses, delete_expense, monthly_summary, create_database


class TestExpenseTracker(unittest.TestCase):

    def setUp(self):
        create_database()

    def test_add_expense(self):
        add_expense(10, "Food", "2026-04-10", "Lunch")
        expenses = get_expenses()
        self.assertTrue(len(expenses) > 0)

    def test_delete_expense(self):
        add_expense(5, "Test", "2026-04-10", "Delete")
        expense_id = get_expenses()[-1][0]
        delete_expense(expense_id)
        ids = [e[0] for e in get_expenses()]
        self.assertNotIn(expense_id, ids)

    def test_monthly_summary(self):
        add_expense(20, "Test", "2026-04-01", "Test")
        total = monthly_summary("2026-04")
        self.assertTrue(total >= 20)


if __name__ == "__main__":
    unittest.main()