import importlib
import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class CoffeeShopApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend_dir = Path(__file__).resolve().parent
        self.menu_file = self.backend_dir / "_test_menu.json"
        self.reservations_file = self.backend_dir / "_test_reservations.json"
        source_menu_file = self.backend_dir / "menu.json"

        self.menu_file.write_text(source_menu_file.read_text(encoding="utf-8"), encoding="utf-8")
        self.reservations_file.write_text("[]\n", encoding="utf-8")

        import main as backend_main

        self.backend_main = importlib.reload(backend_main)
        self.backend_main.MENU_FILE = self.menu_file
        self.backend_main.RESERVATIONS_FILE = self.reservations_file

        self.client_context = TestClient(self.backend_main.app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        if self.menu_file.exists():
            self.menu_file.unlink()
        if self.reservations_file.exists():
            self.reservations_file.unlink()

    def test_status_returns_counts(self) -> None:
        response = self.client.get("/api/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["menu_count"], 8)
        self.assertEqual(response.json()["reservation_count"], 0)

    def test_get_menu_returns_all_items(self) -> None:
        response = self.client.get("/api/menu")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 8)

    def test_get_menu_filters_by_category_case_insensitively(self) -> None:
        response = self.client.get("/api/menu", params={"category": "coffee"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)
        self.assertTrue(all(item["category"] == "Coffee" for item in response.json()))

    def test_get_menu_item_returns_single_item(self) -> None:
        response = self.client.get("/api/menu/3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Latte")

    def test_get_menu_item_returns_404_for_missing_item(self) -> None:
        response = self.client.get("/api/menu/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Menu item not found.")

    def test_post_reservation_returns_201_and_persists_to_disk(self) -> None:
        payload = {
            "contact_name": "Jane Doe",
            "contact_email": "jane@example.com",
            "date": "2026-06-15",
            "time": "14:30",
            "guest_count": 4,
            "special_requests": "Window seat, please.",
        }

        response = self.client.post("/api/reservations", json=payload)

        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertEqual(response_data["id"], 1)
        self.assertEqual(response_data["contact_name"], payload["contact_name"])

        saved_reservations = json.loads(self.reservations_file.read_text(encoding="utf-8"))
        self.assertEqual(len(saved_reservations), 1)
        self.assertEqual(saved_reservations[0]["contact_email"], payload["contact_email"])

    def test_post_reservation_rejects_invalid_guest_count(self) -> None:
        payload = {
            "contact_name": "Jane Doe",
            "contact_email": "jane@example.com",
            "date": "2026-06-15",
            "time": "14:30",
            "guest_count": 0,
            "special_requests": None,
        }

        response = self.client.post("/api/reservations", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_post_reservation_rejects_invalid_email(self) -> None:
        payload = {
            "contact_name": "Jane Doe",
            "contact_email": "not-an-email",
            "date": "2026-06-15",
            "time": "14:30",
            "guest_count": 4,
            "special_requests": None,
        }

        response = self.client.post("/api/reservations", json=payload)

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
