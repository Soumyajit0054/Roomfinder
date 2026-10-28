"""Owner/admin API tests with the database layer mocked.

Run:  python -m unittest discover tests
"""
import io
import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from routes import api

USER = {"id": 7, "name": "Omar", "email": "o@example.com", "phone": "1", "role": "owner"}
PROP = {
    "id": 5, "owner_id": 7, "title": "Room", "description": "d", "location": "Dhaka",
    "address": "a", "rent": 5000, "room_type": "Single", "furnished": "Yes",
    "food_available": "No", "gender_preference": "Any", "available": 1,
    "created_at": datetime(2026, 1, 1),
}
FORM = {"title": "New room", "location": "Dhaka", "rent": "4500"}


def auth_patch(user=USER):
    return patch("routes.api.query_one", return_value=user)


class ManageTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        self.tmp = tempfile.TemporaryDirectory()
        app_module.app.config["UPLOAD_FOLDER"] = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def h(self, role="owner"):
        with app_module.app.app_context():
            return {"Authorization": f"Bearer {api.make_token(7, role)}"}

    # ---------- role gates ----------
    def test_tenant_blocked_from_owner_and_admin(self):
        with auth_patch():
            self.assertEqual(self.client.get("/api/v1/owner/dashboard", headers=self.h("tenant")).status_code, 403)
            self.assertEqual(self.client.get("/api/v1/admin/users", headers=self.h("tenant")).status_code, 403)
            self.assertEqual(self.client.get("/api/v1/admin/users", headers=self.h("owner")).status_code, 403)

    def test_anonymous_gets_401(self):
        self.assertEqual(self.client.get("/api/v1/owner/properties").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/admin/dashboard").status_code, 401)

    # ---------- owner: create ----------
    @patch("routes.api_manage.query_all", return_value=[])
    @patch("routes.api_manage.query_one", return_value=PROP)
    @patch("routes.api_manage.execute_query", return_value=5)
    def test_add_property_with_images(self, ex, *_):
        data = {**FORM, "images": [(io.BytesIO(b"x"), "a.jpg"), (io.BytesIO(b"x"), "evil.svg"), (io.BytesIO(b"x"), "n.txt")]}
        with auth_patch():
            r = self.client.post("/api/v1/owner/properties", headers=self.h(), data=data,
                                 content_type="multipart/form-data")
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["images_saved"], 1)
        self.assertEqual(sorted(body["images_rejected"]), ["evil.svg", "n.txt"])
        self.assertEqual(len(os.listdir(self.tmp.name)), 1)
        self.assertEqual(ex.call_count, 2)  # property insert + one image row

    def test_add_property_validation(self):
        with auth_patch():
            for bad, msg in (({**FORM, "title": ""}, "title"), ({**FORM, "rent": "abc"}, "valid rent"),
                             ({**FORM, "rent": "0"}, "greater than 0"), ({**FORM, "location": " "}, "location")):
                r = self.client.post("/api/v1/owner/properties", headers=self.h(), data=bad)
                self.assertEqual(r.status_code, 400, bad)
                self.assertIn(msg, r.get_json()["error"])

    # ---------- owner: edit / delete ----------
    @patch("routes.api_manage.query_one", return_value=None)
    def test_cannot_touch_someone_elses_property(self, _):
        with auth_patch():
            self.assertEqual(self.client.put("/api/v1/owner/properties/5", headers=self.h(), data=FORM).status_code, 404)
            self.assertEqual(self.client.delete("/api/v1/owner/properties/5", headers=self.h()).status_code, 404)

    @patch("routes.api_manage.query_all", return_value=[])
    @patch("routes.api_manage.execute_query")
    @patch("routes.api_manage.query_one")
    def test_update_keeps_omitted_fields_and_removes_image(self, qone, ex, _):
        qone.side_effect = [PROP, {"id": 3, "image": "old.jpg"}, PROP]
        open(os.path.join(self.tmp.name, "old.jpg"), "w").close()
        with auth_patch():
            r = self.client.put("/api/v1/owner/properties/5", headers=self.h(),
                                data={"rent": "6000", "available": "0", "delete_image_ids": ["3", "x"]})
        self.assertEqual(r.status_code, 200)
        update_args = ex.call_args_list[0][0][1]
        self.assertEqual(update_args[0], "Room")      # title kept
        self.assertEqual(update_args[4], 6000.0)      # rent changed
        self.assertEqual(update_args[9], 0)           # unavailable
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "old.jpg")))

    @patch("routes.api_manage.query_all", return_value=[{"image": "p.jpg"}])
    @patch("routes.api_manage.execute_query")
    @patch("routes.api_manage.query_one", return_value=PROP)
    def test_delete_property_removes_files(self, _q, ex, _a):
        open(os.path.join(self.tmp.name, "p.jpg"), "w").close()
        with auth_patch():
            r = self.client.delete("/api/v1/owner/properties/5", headers=self.h())
        self.assertEqual(r.get_json(), {"deleted": True})
        self.assertEqual(os.listdir(self.tmp.name), [])
        ex.assert_called_once()

    # ---------- owner: requests ----------
    @patch("routes.api_manage.execute_query")
    @patch("routes.api_manage.query_one", return_value={"id": 1, "property_id": 5})
    def test_accept_marks_property_unavailable(self, _, ex):
        with auth_patch():
            r = self.client.post("/api/v1/owner/requests/1", headers=self.h(), json={"status": "accepted"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ex.call_count, 2)
        self.assertIn("available = 0", ex.call_args_list[1][0][0])

    @patch("routes.api_manage.execute_query")
    @patch("routes.api_manage.query_one", return_value={"id": 1, "property_id": 5})
    def test_reject_leaves_property_alone(self, _, ex):
        with auth_patch():
            self.client.post("/api/v1/owner/requests/1", headers=self.h(), json={"status": "rejected"})
        self.assertEqual(ex.call_count, 1)

    def test_invalid_decision(self):
        with auth_patch():
            r = self.client.post("/api/v1/owner/requests/1", headers=self.h(), json={"status": "maybe"})
        self.assertEqual(r.status_code, 400)

    @patch("routes.api_manage.query_one", return_value=None)
    def test_decide_other_owners_request(self, _):
        with auth_patch():
            r = self.client.post("/api/v1/owner/requests/1", headers=self.h(), json={"status": "accepted"})
        self.assertEqual(r.status_code, 404)

    # ---------- admin ----------
    def test_admin_cannot_delete_self(self):
        with auth_patch({**USER, "role": "admin"}):
            r = self.client.delete("/api/v1/admin/users/7", headers=self.h("admin"))
        self.assertEqual(r.status_code, 400)

    @patch("routes.api_manage.execute_query")
    @patch("routes.api_manage.query_one", return_value={"id": 9})
    def test_admin_deletes_user(self, _, ex):
        with auth_patch({**USER, "role": "admin"}):
            r = self.client.delete("/api/v1/admin/users/9", headers=self.h("admin"))
        self.assertEqual(r.status_code, 200)
        ex.assert_called_once()

    @patch("routes.api_manage.query_one", return_value={"total": 3})
    def test_admin_dashboard(self, _):
        with auth_patch({**USER, "role": "admin"}):
            r = self.client.get("/api/v1/admin/dashboard", headers=self.h("admin"))
        self.assertEqual(r.get_json()["users"], 3)


if __name__ == "__main__":
    unittest.main()
