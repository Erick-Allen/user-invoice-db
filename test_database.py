import unittest
import sqlite3
import database


TEST_NAME_1 = "John Doe"
TEST_EMAIL_1 = "johndoe@gmail.com"
TEST_NAME_2 = "Alice"
TEST_EMAIL_2 = "alice@yahoo.org"

class TestDatabaseCRUD(unittest.TestCase):

    def setUp(self):
        self.connect = sqlite3.connect(":memory:")
        self.connect.row_factory = sqlite3.Row
        self.cursor = self.connect.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

        database.create_user_schema(self.cursor)
        database.create_invoice_schema(self.cursor)
        self.connect.commit()

    def tearDown(self):
        self.connect.close()

    # User CRUD tests
    def test_create_user(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.connect.commit()
        row = self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['name'], TEST_NAME_1)
        self.assertEqual(row['email'], TEST_EMAIL_1)

    def test_get_user_by_id(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.connect.commit()
        row = database.get_user_by_id(self.cursor, user_id)
        self.assertEqual(row['id'], user_id)

    def test_get_user_by_email(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.connect.commit()
        row = database.get_user_by_email(self.cursor, TEST_EMAIL_1)
        self.assertIsNotNone(row)
        self.assertEqual(row['name'], TEST_NAME_1)
        self.assertEqual(row['email'], TEST_EMAIL_1)

    def test_get_user_id_by_email(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.connect.commit()
        got_id = database.get_user_id_by_email(self.cursor, TEST_EMAIL_1)
        self.assertEqual(got_id, user_id)

    def test_get_users(self):
        user_id_1 = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        user_id_2 = database.create_user(self.cursor, TEST_NAME_2, TEST_EMAIL_2)
        self.connect.commit()
        rows = database.get_users(self.cursor)

        self.assertEqual(len(rows), 2)

        user_1 = next((u for u in rows if u['id'] == user_id_1), None)
        user_2 = next((u for u in rows if u['id'] == user_id_2), None)

        self.assertIsNotNone(user_1)
        self.assertIsNotNone(user_2)
        self.assertEqual(user_1['name'], TEST_NAME_1)
        self.assertEqual(user_1['email'], TEST_EMAIL_1)
        self.assertEqual(user_2['name'], TEST_NAME_2)
        self.assertEqual(user_2['email'], TEST_EMAIL_2)

    def test_update_user_name_only(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.connect.commit()

        updated_name = "Timmy"
        user_was_updated = database.update_user(self.cursor, user_id, name=updated_name)
        updated_user = database.get_user_by_id(self.cursor, user_id)

        self.assertTrue(user_was_updated)
        self.assertEqual(updated_user['name'], updated_name)
        self.assertEqual(updated_user['email'], TEST_EMAIL_1)

    def test_update_user_email_only(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.connect.commit()

        updated_email = "paul@gmail.com"
        user_was_updated = database.update_user(self.cursor, user_id, email=updated_email)
        updated_user = database.get_user_by_id(self.cursor, user_id)
        
        self.assertTrue(user_was_updated)
        self.assertEqual(updated_user['name'], TEST_NAME_1)
        self.assertEqual(updated_user['email'], updated_email)

    def test_update_user_name_and_email_only(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.connect.commit()

        updated_name = "Melissa"
        updated_email = "melissa@test.co"
        user_was_updated = database.update_user(self.cursor, user_id, name=updated_name, email=updated_email)
        updated_user = database.get_user_by_id(self.cursor, user_id)

        self.assertTrue(user_was_updated)
        self.assertEqual(updated_user['name'], updated_name)
        self.assertEqual(updated_user['email'], updated_email)

    def test_update_user_nothing_returns_false(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.assertFalse(database.update_user(self.cursor, user_id))

    def test_delete_user(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.connect.commit()

        user_was_deleted = database.delete_user(self.cursor, user_id)
        row = database.get_user_by_id(self.cursor, user_id)
        
        self.assertTrue(user_was_deleted)
        self.assertIsNone(row)

    # Invoice CRUD TESTS
    def test_add_invoice_to_user(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        self.connect.commit()
        row = self.cursor.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row['invoice_id'], invoice_id)
        self.assertEqual(row['user_id'], user_id)
        self.assertEqual(row['date_issued'], "2025-01-20")
        self.assertEqual(row['total'], 30025)
        self.assertIsNone(row["due_date"])

    def test_get_invoice_by_id(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        self.connect.commit()
        row = database.get_invoice_by_id(self.cursor, invoice_id)

        self.assertEqual(row['invoice_id'], invoice_id)

    def test_get_invoices_by_email(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        invoice_id_2 = database.add_invoice_to_user(self.cursor, user_id, "2/17/2025", 100)
        self.connect.commit()
        rows = database.get_invoices_by_email(self.cursor, TEST_EMAIL_1)

        self.assertEqual(len(rows), 2)

        invoice_1 = next((i for i in rows if i['invoice_id'] == invoice_id_1), None)
        invoice_2 = next((i for i in rows if i['invoice_id'] == invoice_id_2), None)
        
        self.assertIsNotNone(invoice_1)
        self.assertIsNotNone(invoice_2)
        self.assertEqual(invoice_1["user_id"], user_id)
        self.assertEqual(invoice_2["user_id"], user_id)
        self.assertEqual(invoice_1["invoice_id"], invoice_id_1)
        self.assertEqual(invoice_2["invoice_id"], invoice_id_2)

    def test_get_invoices_by_user_id(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        invoice_id_2 = database.add_invoice_to_user(self.cursor, user_id, "2/17/2025", 100)
        self.connect.commit()
        rows = database.get_invoices_by_user_id(self.cursor, user_id)

        self.assertEqual(len(rows), 2)

        user_ids = {r["user_id"] for r in rows}
        self.assertEqual(user_ids, {user_id})

    def test_get_invoices_by_user_and_range(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        invoice_id_2 = database.add_invoice_to_user(self.cursor, user_id, "2/17/2025", 100)
        invoice_id_3 = database.add_invoice_to_user(self.cursor, user_id, "6/5/2025", 1000.01)
        self.connect.commit()

        start_date = "2/17/2025"
        end_date = "6/5/2025"
        rows = database.get_invoices_by_user_and_range(self.cursor, user_id, start_date, end_date)

        self.assertEqual(len(rows), 2)

        invoice_1 = next((i for i in rows if i['invoice_id'] == invoice_id_1), None)
        invoice_2 = next((i for i in rows if i['invoice_id'] == invoice_id_2), None)
        invoice_3 = next((i for i in rows if i['invoice_id'] == invoice_id_3), None)

        
        self.assertIsNone(invoice_1)
        self.assertIsNotNone(invoice_2)
        self.assertIsNotNone(invoice_3)
        self.assertEqual(invoice_2["user_id"], user_id)
        self.assertEqual(invoice_3["user_id"], user_id)
        self.assertEqual(invoice_2["invoice_id"], invoice_id_2)
        self.assertEqual(invoice_3["invoice_id"], invoice_id_3)

    def test_count_invoices(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        invoice_id_2 = database.add_invoice_to_user(self.cursor, user_id, "2/17/2025", 100)
        invoice_id_3 = database.add_invoice_to_user(self.cursor, user_id, "6/5/2025", 1000.01)
        self.connect.commit()

        invoice_count = database.count_invoices(self.cursor)

        self.assertEqual(invoice_count, 3)

    def test_update_invoice_one_argument(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        invoice_id_2 = database.add_invoice_to_user(self.cursor, user_id, "2/17/2025", 100)

        new_date_issued = "2025-03-08"
        updated = database.update_invoice(self.cursor, invoice_id_1, date_issued=new_date_issued)
        self.assertTrue(updated)

        row_1 = database.get_invoice_by_id(self.cursor, invoice_id_1)
        row_2 = database.get_invoice_by_id(self.cursor, invoice_id_2)

        self.assertEqual(row_1["date_issued"], new_date_issued)
        self.assertNotEqual(row_2["date_issued"], new_date_issued)

    def test_update_invoice_two_arguments(self):
        user_id_1 = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        user_id_2 = database.create_user(self.cursor, TEST_NAME_2, TEST_EMAIL_2)
        invoice_id_1 = database.add_invoice_to_user(self.cursor, user_id_1, "1/20/2025", 300.25)
        invoice_id_2 = database.add_invoice_to_user(self.cursor, user_id_1, "2/17/2025", 100)

        new_total = 1500.90
        updated = database.update_invoice(self.cursor, invoice_id_2, total=new_total, user_id=user_id_2)
        self.assertTrue(updated)

        row_1 = database.get_invoice_by_id(self.cursor, invoice_id_1)
        row_2 = database.get_invoice_by_id(self.cursor, invoice_id_2)

        self.assertEqual(row_2["total"], database.to_cents(new_total))
        self.assertEqual(row_2["user_id"], user_id_2)
        self.assertNotEqual(row_1["total"], database.to_cents(new_total))
        self.assertEqual(row_1["user_id"], user_id_1)

    def test_update_invoice_no_arguments(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        invoice_id_2 = database.add_invoice_to_user(self.cursor, user_id, "2/17/2025", 100)

        updated = database.update_invoice(self.cursor, invoice_id_1)
        self.assertFalse(updated)

    def test_delete_invoice(self):
        user_id = database.create_user(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = database.add_invoice_to_user(self.cursor, user_id, "1/20/2025", 300.25)
        invoice_id_2 = database.add_invoice_to_user(self.cursor, user_id, "2/17/2025", 100)

        deleted = database.delete_invoice(self.cursor, invoice_id_1)
        self.assertTrue(deleted)

        remaining = database.get_invoices_by_user_id(self.cursor, user_id)
        remaining_ids = {r["invoice_id"] for r in remaining}
        self.assertNotIn(invoice_id_1, remaining_ids)
        self.assertIn(invoice_id_2, remaining_ids)

if __name__ == '__main__':
    unittest.main()
    