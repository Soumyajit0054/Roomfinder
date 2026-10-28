"""API tests with the database layer mocked (no MySQL needed).

Run:  python -m unittest discover tests
"""
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash

import app as app_module
from routes import api

USER = {
    "id": 1, "name": "Tia", "email": "tia@example.com", "phone": "123",
    "role": "tenant", "password": generate_password_hash("secret123"),
}
PROP = {
    "id": 5, "title": "Cozy room", "description": "d", "location": "Dhaka",
    "address": "a", "rent": 5000, "room_type": "Single", "furnished": "Yes",
    "food_available": "No", "gender_preference": "Any", "available": 1,
    "owner_name": "Omar", "owner_email": "o@example.com", "owner_phone": "999",
    "image": "p.jpg", "created_at": datetime(2026, 1, 1),
}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def token(self, role="tenant"):
        with app_module.app.app_context():
            return api.make_token(1, role)

    def auth(self, role="tenant"):
        return {"Authorization": f"Bearer {self.token(role)}"}

    def test_web_routes_still_redirect_but_api_does_not(self):
        self.assertEqual(self.client.get("/favorites").status_code, 302)
        self.assertEqual(self.client.get("/api/v1/favorites").status_code, 401)

    def test_pwa_files_are_public(self):
        self.assertEqual(self.client.get("/sw.js").status_code, 200)
        self.assertEqual(self.client.get("/offline").status_code, 200)
        self.assertEqual(self.client.get("/static/manifest.webmanifest").status_code, 200)

    @patch("routes.api.query_one", return_value=USER)
    def test_login_ok(self, _):
        r = self.client.post("/api/v1/auth/login", json={"email": "tia@example.com", "password": "secret123"})
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertTrue(body["token"])
        self.assertEqual(body["user"]["role"], "tenant")
        self.assertNotIn("password", body["user"])

    @patch("routes.api.query_one", return_value=USER)
    def test_login_bad_password(self, _):
        r = self.client.post("/api/v1/auth/login", json={"email": "tia@example.com", "password": "nope"})
        self.assertEqual(r.status_code, 401)

    @patch("routes.api.query_one", return_value=None)
    def test_login_unknown_user(self, _):
        r = self.client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "x"})
        self.assertEqual(r.status_code, 401)

    def test_tampered_token_rejected(self):
        r = self.client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + self.token() + "x"})
        self.assertEqual(r.status_code, 401)

    @patch("routes.api.query_one", return_value=USER)
    def test_me(self, _):
        r = self.client.get("/api/v1/auth/me", headers=self.auth())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["user"]["email"], "tia@example.com")

    @patch("routes.api.query_all", return_value=[PROP])
    def test_list_properties_with_filters(self, qa):
        r = self.client.get("/api/v1/properties?location=Dhaka&max_rent=6000&limit=5")
        self.assertEqual(r.status_code, 200)
        p = r.get_json()["properties"][0]
        self.assertEqual(p["rent"], 5000.0)
        self.assertTrue(p["image"].endswith("/static/uploads/p.jpg"))
        self.assertNotIn("owner_email", p)
        sql, params = qa.call_args[0]
        self.assertIn("p.rent <=", sql)
        self.assertEqual(params[-2:], [5, 0])

    def test_bad_filter(self):
        self.assertEqual(self.client.get("/api/v1/properties?min_rent=abc").status_code, 400)

    @patch("routes.api.query_all", return_value=[{"image": "a.jpg"}, {"image": "b.jpg"}])
    @patch("routes.api.query_one", return_value=PROP)
    def test_detail_hides_contact_when_anonymous(self, *_):
        anon = self.client.get("/api/v1/properties/5").get_json()["property"]
        self.assertNotIn("owner_phone", anon)
        self.assertEqual(len(anon["images"]), 2)
        authed = self.client.get("/api/v1/properties/5", headers=self.auth()).get_json()["property"]
        self.assertEqual(authed["owner_phone"], "999")

    @patch("routes.api.query_one", return_value=None)
    def test_detail_404(self, _):
        self.assertEqual(self.client.get("/api/v1/properties/99").status_code, 404)

    @patch("routes.api.query_one", return_value=USER)
    def test_owner_cannot_use_tenant_endpoints(self, _):
        r = self.client.get("/api/v1/favorites", headers=self.auth("owner"))
        self.assertEqual(r.status_code, 403)

    @patch("routes.api.execute_query")
    @patch("routes.api.query_one", side_effect=[USER, {"id": 5}, None])
    def test_add_favorite(self, _, ex):
        r = self.client.put("/api/v1/favorites/5", headers=self.auth())
        self.assertEqual(r.get_json(), {"favorite": True})
        ex.assert_called_once()

    @patch("routes.api.execute_query")
    @patch("routes.api.query_one", side_effect=[USER, {"id": 5, "available": 1}, {"status": "pending"}])
    def test_duplicate_request_conflict(self, _, ex):
        r = self.client.post("/api/v1/properties/5/request", headers=self.auth(), json={"message": "hi"})
        self.assertEqual(r.status_code, 409)
        ex.assert_not_called()

    @patch("routes.api.execute_query")
    @patch("routes.api.query_one", side_effect=[USER, {"id": 5, "available": 1}, None])
    def test_create_request(self, _, ex):
        r = self.client.post("/api/v1/properties/5/request", headers=self.auth(), json={"message": "hi"})
        self.assertEqual(r.status_code, 201)
        ex.assert_called_once()

    @patch("routes.api.query_one", return_value=USER)
    def test_message_too_long(self, _):
        r = self.client.post("/api/v1/properties/5/request", headers=self.auth(), json={"message": "x" * 1001})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
