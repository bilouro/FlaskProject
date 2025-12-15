import unittest
import json

from app import app, BOOKS  # import Flask app and in-memory "database"


class BookApiTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test client for the application
        self.app = app.test_client()

        # Ensure a known state for the in-memory structure
        BOOKS.clear()
        BOOKS.update({
            1: {"id": 1, "title": "Book 1", "author": "Author 1", "year": 2001, "isbn": "111"},
            2: {"id": 2, "title": "Book 2", "author": "Author 2", "year": 2002, "isbn": "222"},
        })

    # ---------- GET /health ----------
    def test_health(self):
        resp = self.app.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")

    # ---------- GET /books ----------
    def test_list_books(self):
        resp = self.app.get("/books")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data), 2)

    # ---------- GET /books/<id> ----------
    def test_get_book_success(self):
        resp = self.app.get("/books/1")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Book 1")

    def test_get_book_not_found(self):
        resp = self.app.get("/books/999")
        self.assertEqual(resp.status_code, 404)

    # ---------- POST /books ----------
    def test_create_book_success(self):
        new_book = {
            "title": "New Book",
            "author": "New Author",
            "year": 2023,
            "isbn": "333",
        }
        resp = self.app.post(
            "/books",
            data=json.dumps(new_book),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "New Book")

    def test_create_book_missing_field(self):
        # Missing the "author" field
        new_book = {
            "title": "Invalid Book",
            "year": 2023,
            "isbn": "999",
        }
        resp = self.app.post(
            "/books",
            data=json.dumps(new_book),
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
        resp = self.app.put(
            "/books/1",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["title"], "Updated Book 1")

    def test_replace_book_not_found(self):
        payload = {
            "title": "Does Not Exist",
            "author": "X",
            "year": 2000,
            "isbn": "000",
        }
        resp = self.app.put(
            "/books/999",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    # ---------- PATCH /books/<id> ----------
    def test_update_book_success(self):
        payload = {"year": 2020}
        resp = self.app.patch(
            "/books/1",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["year"], 2020)

    def test_update_book_not_found(self):
        payload = {"year": 2020}
        resp = self.app.patch(
            "/books/999",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    # ---------- DELETE /books/<id> ----------
    def test_delete_book_success(self):
        resp = self.app.delete("/books/1")
        self.assertEqual(resp.status_code, 204)
        # Ensure it was removed from the in-memory structure
        self.assertNotIn(1, BOOKS)

    def test_delete_book_not_found(self):
        resp = self.app.delete("/books/999")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()