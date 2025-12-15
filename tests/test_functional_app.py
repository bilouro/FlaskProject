import unittest
import json
import requests


BASE_URL = "http://127.0.0.1:5000"


class FunctionalHttpTestCase(unittest.TestCase):
    """
    Functional tests that hit the running Flask app via real HTTP calls.

    Requirements:
    - The Flask app MUST be running (python app.py)
    - The PostgreSQL database MUST be up and have the 'books' table.
    """

    def test_health_endpoint(self):
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("database", data)

    def test_full_book_crud_flow(self):
        # 1) List current books
        resp = requests.get(f"{BASE_URL}/books", timeout=5)
        self.assertEqual(resp.status_code, 200)
        initial_books = resp.json()
        initial_count = len(initial_books)

        # 2) Create a new book
        new_book = {
            "title": "Functional Test Book",
            "author": "Test Author",
            "year": 2024,
            "isbn": "FUNC-123456",
        }
        resp = requests.post(
            f"{BASE_URL}/books",
            data=json.dumps(new_book),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        self.assertEqual(resp.status_code, 201)
        created = resp.json()
        self.assertIn("id", created)
        self.assertEqual(created["title"], new_book["title"])
        book_id = created["id"]

        # 3) Get the created book
        resp = requests.get(f"{BASE_URL}/books/{book_id}", timeout=5)
        self.assertEqual(resp.status_code, 200)
        fetched = resp.json()
        self.assertEqual(fetched["id"], book_id)
        self.assertEqual(fetched["isbn"], new_book["isbn"])

        # 4) Replace the book (PUT)
        updated_full = {
            "title": "Functional Test Book - Updated",
            "author": "Updated Author",
            "year": 2025,
            "isbn": "FUNC-654321",
        }
        resp = requests.put(
            f"{BASE_URL}/books/{book_id}",
            data=json.dumps(updated_full),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        self.assertEqual(resp.status_code, 200)
        replaced = resp.json()
        self.assertEqual(replaced["title"], updated_full["title"])
        self.assertEqual(replaced["isbn"], updated_full["isbn"])

        # 5) Partially update the book (PATCH)
        partial_update = {"year": 2030}
        resp = requests.patch(
            f"{BASE_URL}/books/{book_id}",
            data=json.dumps(partial_update),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        self.assertEqual(resp.status_code, 200)
        patched = resp.json()
        self.assertEqual(patched["year"], 2030)

        # 6) Delete the book
        resp = requests.delete(f"{BASE_URL}/books/{book_id}", timeout=5)
        self.assertEqual(resp.status_code, 204)

        # 7) Ensure it was deleted
        resp = requests.get(f"{BASE_URL}/books/{book_id}", timeout=5)
        self.assertEqual(resp.status_code, 404)

        # 8) List again and check count is back to original
        resp = requests.get(f"{BASE_URL}/books", timeout=5)
        self.assertEqual(resp.status_code, 200)
        final_books = resp.json()
        self.assertEqual(len(final_books), initial_count)


if __name__ == "__main__":
    unittest.main()