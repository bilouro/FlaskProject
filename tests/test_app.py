import json
import unittest

from app import create_app
from config import TestConfig
from db import get_connection


class BookApiTestCase(unittest.TestCase):
    """
    API-level tests using Flask's test client (no real HTTP, but full routing, JSON, etc.).
    Tests hit the real PostgreSQL database configured for the app.
    """

    @classmethod
    def setUpClass(cls):
        """
        Create a Flask app instance configured for tests
        and a shared test client.
        """
        cls.app = create_app(TestConfig)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the application context after all tests.
        """
        cls.app_context.pop()

    def setUp(self):
        """
        Ensure a known state for the database before each test.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Clear table and reset ids (dev/test friendly)
                cur.execute("TRUNCATE TABLE books RESTART IDENTITY CASCADE;")

                # Insert two known records
                cur.execute(
                    """
                    INSERT INTO books (title, author, year, isbn)
                    VALUES
                        (%s, %s, %s, %s),
                        (%s, %s, %s, %s)
                    """,
                    (
                        "Book 1", "Author 1", 2001, "111",
                        "Book 2", "Author 2", 2002, "222",
                    ),
                )
            conn.commit()

    # ---------- GET /health ----------
    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("database", data)

    # ---------- GET /books/ ----------
    def test_list_books(self):
        # NOTE: use "/books/" (with trailing slash) to avoid 308 redirect
        resp = self.client.get("/books/")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Book 1")
        self.assertEqual(data[1]["title"], "Book 2")

    # ---------- GET /books/<id> ----------
    def test_get_book_success(self):
        resp = self.client.get("/books/1")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Book 1")

    def test_get_book_not_found(self):
        resp = self.client.get("/books/999")
        self.assertEqual(resp.status_code, 404)

    # ---------- POST /books/ ----------
    def test_create_book_success(self):
        new_book = {
            "title": "New Book",
            "author": "New Author",
            "year": 2023,
            "isbn": "333",
        }
        # NOTE: use "/books/" to avoid 308 redirect
        resp = self.client.post(
            "/books/",
            data=json.dumps(new_book),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)

        data = resp.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "New Book")

        # Check it was really inserted into DB
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books WHERE isbn = %s", ("333",))
                count = cur.fetchone()[0]
        self.assertEqual(count, 1)

    def test_create_book_missing_field(self):
        # Missing the "author" field
        invalid_book = {
            "title": "Invalid Book",
            "year": 2023,
            "isbn": "999",
        }
        resp = self.client.post(
            "/books/",
            data=json.dumps(invalid_book),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    # ---------- PUT /books/<id> ----------
    def test_replace_book_success(self):
        payload = {
            "title": "Updated Book 1",
            "author": "Updated Author",
            "year": 2010,
            "isbn": "111-updated",
        }
        resp = self.client.put(
            "/books/1",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data["title"], "Updated Book 1")
        self.assertEqual(data["isbn"], "111-updated")

    def test_replace_book_not_found(self):
        payload = {
            "title": "Does Not Exist",
            "author": "X",
            "year": 2000,
            "isbn": "000",
        }
        resp = self.client.put(
            "/books/999",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    # ---------- PATCH /books/<id> ----------
    def test_update_book_success(self):
        payload = {"year": 2020}
        resp = self.client.patch(
            "/books/1",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data["year"], 2020)

    def test_update_book_not_found(self):
        payload = {"year": 2020}
        resp = self.client.patch(
            "/books/999",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    # ---------- DELETE /books/<id> ----------
    def test_delete_book_success(self):
        resp = self.client.delete("/books/1")
        self.assertEqual(resp.status_code, 204)

        # Ensure it was removed from the database
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books WHERE id = %s", (1,))
                count = cur.fetchone()[0]
        self.assertEqual(count, 0)

    def test_delete_book_not_found(self):
        resp = self.client.delete("/books/999")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()