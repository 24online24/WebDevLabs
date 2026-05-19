import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import main as backend_main


class CoffeeShopApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend_dir = BACKEND_DIR
        self.menu_file = self.backend_dir / "_test_menu.json"
        self.database_file = self.backend_dir / "_test_coffee_shop.db"
        source_menu_file = self.backend_dir / "menu.json"

        self.menu_file.write_text(source_menu_file.read_text(encoding="utf-8"), encoding="utf-8")
        if self.database_file.exists():
            self.database_file.unlink()

        self.backend_main = backend_main
        self.backend_main.MENU_FILE = self.menu_file
        self.backend_main.database.configure_engine(self.database_file)

        self.client_context = TestClient(self.backend_main.app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.backend_main.database.engine.dispose()
        if self.menu_file.exists():
            self.menu_file.unlink()
        if self.database_file.exists():
            self.database_file.unlink()

    def login_as(self, email: str, password: str) -> dict[str, object]:
        response = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

        self.assertEqual(response.status_code, 200)
        return response.json()

    def build_session_headers(self, session_token: str) -> dict[str, str]:
        return {self.backend_main.SESSION_HEADER_NAME: session_token}

    def create_reservation(self, **overrides: object) -> dict[str, object]:
        payload = {
            "contact_name": "Jane Doe",
            "contact_email": "jane@example.com",
            "date": "2026-06-15",
            "time": "14:30",
            "guest_count": 4,
            "special_requests": "Window seat, please.",
        }
        payload.update(overrides)

        response = self.client.post("/api/reservations", json=payload)
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_startup_seeds_menu_items_into_database(self) -> None:
        with Session(self.backend_main.database.engine) as session:
            menu_items = session.exec(select(self.backend_main.MenuItem)).all()

        self.assertEqual(len(menu_items), 8)

    def test_startup_seeds_staff_users_into_database(self) -> None:
        with Session(self.backend_main.database.engine) as session:
            staff_users = session.exec(select(self.backend_main.User).order_by(self.backend_main.User.id)).all()

        self.assertEqual(len(staff_users), 2)
        self.assertEqual(staff_users[0].role, self.backend_main.UserRole.admin)
        self.assertEqual(staff_users[1].role, self.backend_main.UserRole.manager)

    def test_status_returns_counts(self) -> None:
        response = self.client.get("/api/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["menu_count"], 8)
        self.assertEqual(response.json()["reservation_count"], 0)
        self.assertEqual(response.json()["staff_user_count"], 2)

    def test_login_returns_session_token_and_user_summary(self) -> None:
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": self.backend_main.INITIAL_ADMIN_EMAIL,
                "password": self.backend_main.INITIAL_ADMIN_PASSWORD,
            },
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("session_token", response_data)
        self.assertEqual(response_data["user"]["email"], self.backend_main.INITIAL_ADMIN_EMAIL)
        self.assertEqual(response_data["user"]["role"], self.backend_main.UserRole.admin.value)

    def test_login_rejects_invalid_credentials(self) -> None:
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": self.backend_main.INITIAL_ADMIN_EMAIL,
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], self.backend_main.INVALID_CREDENTIALS_DETAIL)

    def test_get_current_user_requires_session_token(self) -> None:
        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], self.backend_main.AUTH_REQUIRED_DETAIL)

    def test_get_current_user_returns_authenticated_staff_user(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_MANAGER_EMAIL,
            self.backend_main.INITIAL_MANAGER_PASSWORD,
        )

        response = self.client.get(
            "/api/auth/me",
            headers=self.build_session_headers(str(login_data["session_token"])),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], self.backend_main.INITIAL_MANAGER_EMAIL)
        self.assertEqual(response.json()["role"], self.backend_main.UserRole.manager.value)

    def test_logout_revokes_the_current_session(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_MANAGER_EMAIL,
            self.backend_main.INITIAL_MANAGER_PASSWORD,
        )
        headers = self.build_session_headers(str(login_data["session_token"]))

        logout_response = self.client.post("/api/auth/logout", headers=headers)
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(logout_response.json()["status"], "logged_out")

        me_response = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_response.status_code, 401)
        self.assertEqual(me_response.json()["detail"], self.backend_main.INVALID_SESSION_DETAIL)

    def test_get_menu_returns_all_items(self) -> None:
        response = self.client.get("/api/menu")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 8)

    def test_cors_allows_svelte_dev_server_origin(self) -> None:
        response = self.client.options(
            "/api/menu",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )

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

    def test_manager_cannot_create_menu_item(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_MANAGER_EMAIL,
            self.backend_main.INITIAL_MANAGER_PASSWORD,
        )

        response = self.client.post(
            "/api/menu",
            headers=self.build_session_headers(str(login_data["session_token"])),
            json={
                "name": "Flat White",
                "category": "Coffee",
                "price": 4.75,
                "description": "Velvety espresso with steamed milk.",
                "image": "https://example.com/flat-white.jpg",
                "alt": "Flat white coffee",
                "isFeatured": False,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], self.backend_main.FORBIDDEN_DETAIL)

    def test_admin_can_create_and_delete_menu_item(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_ADMIN_EMAIL,
            self.backend_main.INITIAL_ADMIN_PASSWORD,
        )
        headers = self.build_session_headers(str(login_data["session_token"]))

        create_response = self.client.post(
            "/api/menu",
            headers=headers,
            json={
                "name": "Flat White",
                "category": "Coffee",
                "price": 4.75,
                "description": "Velvety espresso with steamed milk.",
                "image": "https://example.com/flat-white.jpg",
                "alt": "Flat white coffee",
                "isFeatured": True,
            },
        )

        self.assertEqual(create_response.status_code, 201)
        menu_item_id = create_response.json()["id"]

        delete_response = self.client.delete(f"/api/menu/{menu_item_id}", headers=headers)
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["status"], "deleted")

        fetch_response = self.client.get(f"/api/menu/{menu_item_id}")
        self.assertEqual(fetch_response.status_code, 404)

    def test_admin_cannot_create_menu_item_with_invalid_price(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_ADMIN_EMAIL,
            self.backend_main.INITIAL_ADMIN_PASSWORD,
        )

        response = self.client.post(
            "/api/menu",
            headers=self.build_session_headers(str(login_data["session_token"])),
            json={
                "name": "Flat White",
                "category": "Coffee",
                "price": 0,
                "description": "Velvety espresso with steamed milk.",
                "image": "https://example.com/flat-white.jpg",
                "alt": "Flat white coffee",
                "isFeatured": False,
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_admin_cannot_update_menu_item_with_blank_name(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_ADMIN_EMAIL,
            self.backend_main.INITIAL_ADMIN_PASSWORD,
        )

        response = self.client.put(
            "/api/menu/1",
            headers=self.build_session_headers(str(login_data["session_token"])),
            json={
                "name": "   ",
                "category": "Coffee",
                "price": 4.25,
                "description": "Updated espresso-based drink.",
                "image": "https://example.com/espresso.jpg",
                "alt": "Espresso beverage",
                "isFeatured": True,
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_admin_can_create_staff_user(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_ADMIN_EMAIL,
            self.backend_main.INITIAL_ADMIN_PASSWORD,
        )

        response = self.client.post(
            "/api/staff/users",
            headers=self.build_session_headers(str(login_data["session_token"])),
            json={
                "email": "shiftlead@example.com",
                "display_name": "Shift Lead",
                "password": "shiftlead123",
                "role": self.backend_main.UserRole.manager.value,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "shiftlead@example.com")
        self.assertEqual(response.json()["role"], self.backend_main.UserRole.manager.value)

    def test_admin_can_update_staff_user_role_and_active_state(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_ADMIN_EMAIL,
            self.backend_main.INITIAL_ADMIN_PASSWORD,
        )
        headers = self.build_session_headers(str(login_data["session_token"]))

        create_response = self.client.post(
            "/api/staff/users",
            headers=headers,
            json={
                "email": "host@example.com",
                "display_name": "Host",
                "password": "hostpass123",
                "role": self.backend_main.UserRole.manager.value,
            },
        )
        self.assertEqual(create_response.status_code, 201)
        created_user_id = create_response.json()["id"]

        update_response = self.client.patch(
            f"/api/staff/users/{created_user_id}",
            headers=headers,
            json={
                "display_name": "Lead Host",
                "role": self.backend_main.UserRole.admin.value,
                "is_active": False,
            },
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["display_name"], "Lead Host")
        self.assertEqual(update_response.json()["role"], self.backend_main.UserRole.admin.value)
        self.assertFalse(update_response.json()["is_active"])

    def test_manager_cannot_update_staff_user(self) -> None:
        admin_login = self.login_as(
            self.backend_main.INITIAL_ADMIN_EMAIL,
            self.backend_main.INITIAL_ADMIN_PASSWORD,
        )
        admin_headers = self.build_session_headers(str(admin_login["session_token"]))

        create_response = self.client.post(
            "/api/staff/users",
            headers=admin_headers,
            json={
                "email": "host@example.com",
                "display_name": "Host",
                "password": "hostpass123",
                "role": self.backend_main.UserRole.manager.value,
            },
        )
        self.assertEqual(create_response.status_code, 201)
        created_user_id = create_response.json()["id"]

        manager_login = self.login_as(
            self.backend_main.INITIAL_MANAGER_EMAIL,
            self.backend_main.INITIAL_MANAGER_PASSWORD,
        )

        response = self.client.patch(
            f"/api/staff/users/{created_user_id}",
            headers=self.build_session_headers(str(manager_login["session_token"])),
            json={"is_active": False},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], self.backend_main.FORBIDDEN_DETAIL)

    def test_admin_cannot_deactivate_their_own_account(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_ADMIN_EMAIL,
            self.backend_main.INITIAL_ADMIN_PASSWORD,
        )
        headers = self.build_session_headers(str(login_data["session_token"]))

        response = self.client.patch(
            "/api/staff/users/1",
            headers=headers,
            json={"is_active": False},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "You cannot deactivate your own account.",
        )

    def test_manager_cannot_list_staff_users(self) -> None:
        login_data = self.login_as(
            self.backend_main.INITIAL_MANAGER_EMAIL,
            self.backend_main.INITIAL_MANAGER_PASSWORD,
        )

        response = self.client.get(
            "/api/staff/users",
            headers=self.build_session_headers(str(login_data["session_token"])),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], self.backend_main.FORBIDDEN_DETAIL)

    def test_post_reservation_returns_201_and_persists_to_database(self) -> None:
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
        self.assertEqual(
            response_data["status"],
            self.backend_main.ReservationStatus.pending.value,
        )
        self.assertIsNone(response_data["internal_notes"])

        with Session(self.backend_main.database.engine) as session:
            saved_reservations = session.exec(select(self.backend_main.Reservation)).all()

        self.assertEqual(len(saved_reservations), 1)
        self.assertEqual(saved_reservations[0].contact_email, payload["contact_email"])
        self.assertEqual(
            saved_reservations[0].status,
            self.backend_main.ReservationStatus.pending,
        )

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

    def test_manager_can_list_reservations(self) -> None:
        reservation = self.create_reservation()

        login_data = self.login_as(
            self.backend_main.INITIAL_MANAGER_EMAIL,
            self.backend_main.INITIAL_MANAGER_PASSWORD,
        )

        response = self.client.get(
            "/api/reservations",
            headers=self.build_session_headers(str(login_data["session_token"])),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["contact_email"], reservation["contact_email"])

    def test_manager_can_update_reservation_status_and_notes(self) -> None:
        reservation = self.create_reservation()
        login_data = self.login_as(
            self.backend_main.INITIAL_MANAGER_EMAIL,
            self.backend_main.INITIAL_MANAGER_PASSWORD,
        )

        response = self.client.patch(
            f"/api/reservations/{reservation['id']}",
            headers=self.build_session_headers(str(login_data["session_token"])),
            json={
                "status": self.backend_main.ReservationStatus.confirmed.value,
                "internal_notes": "VIP guest, hold the corner table.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status"],
            self.backend_main.ReservationStatus.confirmed.value,
        )
        self.assertEqual(
            response.json()["internal_notes"],
            "VIP guest, hold the corner table.",
        )

        with Session(self.backend_main.database.engine) as session:
            saved_reservation = session.get(
                self.backend_main.Reservation,
                int(reservation["id"]),
            )

        self.assertIsNotNone(saved_reservation)
        assert saved_reservation is not None
        self.assertEqual(
            saved_reservation.status,
            self.backend_main.ReservationStatus.confirmed,
        )
        self.assertEqual(
            saved_reservation.internal_notes,
            "VIP guest, hold the corner table.",
        )

    def test_reservation_list_filters_by_status(self) -> None:
        first_reservation = self.create_reservation(contact_email="pending@example.com")
        second_reservation = self.create_reservation(
            contact_name="Sam Guest",
            contact_email="confirmed@example.com",
            time="16:00",
        )
        login_data = self.login_as(
            self.backend_main.INITIAL_MANAGER_EMAIL,
            self.backend_main.INITIAL_MANAGER_PASSWORD,
        )
        headers = self.build_session_headers(str(login_data["session_token"]))

        update_response = self.client.patch(
            f"/api/reservations/{second_reservation['id']}",
            headers=headers,
            json={"status": self.backend_main.ReservationStatus.confirmed.value},
        )
        self.assertEqual(update_response.status_code, 200)

        filtered_response = self.client.get(
            "/api/reservations",
            headers=headers,
            params={"status": self.backend_main.ReservationStatus.confirmed.value},
        )

        self.assertEqual(filtered_response.status_code, 200)
        self.assertEqual(len(filtered_response.json()), 1)
        self.assertEqual(filtered_response.json()[0]["id"], second_reservation["id"])
        self.assertNotEqual(filtered_response.json()[0]["id"], first_reservation["id"])

    def test_reservation_update_requires_session_token(self) -> None:
        reservation = self.create_reservation()

        response = self.client.patch(
            f"/api/reservations/{reservation['id']}",
            json={"status": self.backend_main.ReservationStatus.cancelled.value},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], self.backend_main.AUTH_REQUIRED_DETAIL)

    def test_reservation_list_requires_session_token(self) -> None:
        response = self.client.get("/api/reservations")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], self.backend_main.AUTH_REQUIRED_DETAIL)

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
