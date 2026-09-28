from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from brands.models import Brand


class AuthenticationApiTests(APITestCase):
    def test_registration_returns_token_for_valid_credentials(self):
        response = self.client.post(
            "/api/ai/register/",
            {"username": "newfounder", "password": "SafePassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["username"], "newfounder")
        self.assertTrue(response.data["token"])
        self.assertTrue(User.objects.filter(username="newfounder").exists())

    def test_registration_rejects_weak_password_and_duplicate_username(self):
        User.objects.create_user("founder", password="SafePassword123!")

        weak_password = self.client.post(
            "/api/ai/register/",
            {"username": "another", "password": "short"},
            format="json",
        )
        duplicate = self.client.post(
            "/api/ai/register/",
            {"username": "founder", "password": "SafePassword123!"},
            format="json",
        )

        self.assertEqual(weak_password.status_code, 400)
        self.assertIn("password", weak_password.data)
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("username", duplicate.data)

    def test_login_rejects_bad_credentials_and_returns_existing_token(self):
        user = User.objects.create_user("founder", password="SafePassword123!")
        token = Token.objects.create(user=user)

        failed = self.client.post(
            "/api/ai/login/",
            {"username": "founder", "password": "wrong-password"},
            format="json",
        )
        successful = self.client.post(
            "/api/ai/login/",
            {"username": "founder", "password": "SafePassword123!"},
            format="json",
        )

        self.assertEqual(failed.status_code, 401)
        self.assertEqual(successful.status_code, 200)
        self.assertEqual(successful.data["token"], token.key)

    def test_me_and_logout_require_and_revoke_token(self):
        user = User.objects.create_user("founder", password="SafePassword123!")
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        self.assertEqual(self.client.get("/api/ai/me/").data, {"username": "founder"})
        logout = self.client.post("/api/ai/logout/")
        self.assertEqual(logout.status_code, 204)
        self.assertFalse(Token.objects.filter(key=token.key).exists())
        self.assertEqual(self.client.get("/api/ai/me/").status_code, 401)


@override_settings(AI_MODE="mock")
class MockAiWorkflowTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("founder", password="SafePassword123!")
        self.other_user = User.objects.create_user("otherfounder", password="SafePassword123!")
        self.owner_token = Token.objects.create(user=self.owner)
        self.other_token = Token.objects.create(user=self.other_user)
        self.brand = Brand.objects.create(
            owner=self.owner,
            name="Kindred Glow",
            industry="Skincare",
            description="Refillable skincare for busy young professionals.",
        )

    def authenticate_as(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_mock_interview_and_report_work_offline(self):
        self.authenticate_as(self.owner_token)
        first = self.client.post("/api/ai/start/", {"brand_id": self.brand.id}, format="json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["mode"], "mock")
        self.assertEqual(first.data["progress"], {"completed": 0, "total": 6})
        self.assertIn("problem", first.data["question"].lower())

        resumed = self.client.post("/api/ai/start/", {"brand_id": self.brand.id}, format="json")
        self.assertEqual(resumed.status_code, 200)
        self.assertEqual(resumed.data["question"], first.data["question"])
        self.assertEqual(len(resumed.data["history"]), 1)

        answers = [
            "It makes refills simple.",
            "Busy young professionals.",
            "Refill packs reduce waste.",
            "Calm and capable.",
            "Instagram and referrals.",
            "One hundred repeat customers.",
        ]
        last = first
        for answer in answers:
            last = self.client.post(
                "/api/ai/start/",
                {"brand_id": self.brand.id, "answer": answer},
                format="json",
            )
            self.assertEqual(last.status_code, 200)

        self.assertTrue(last.data["complete"])
        self.assertIsNone(last.data["question"])
        self.assertEqual(last.data["progress"], {"completed": 6, "total": 6})

        report = self.client.post("/api/ai/report/", {"brand_id": self.brand.id}, format="json")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data["mode"], "mock")
        self.assertIn("DEMO / MOCK AI OUTPUT", report.data["report"])
        self.assertIn("positioning", report.data["strategy_data"])
        self.assertEqual(len(report.data["strategy_data"]["taglines"]), 3)

        saved = self.client.get(f"/api/ai/report/{self.brand.id}/")
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.data["mode"], "mock")

    def test_report_requires_started_interview(self):
        self.authenticate_as(self.owner_token)
        response = self.client.post("/api/ai/report/", {"brand_id": self.brand.id}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_other_user_cannot_access_interview_or_saved_report(self):
        self.authenticate_as(self.other_token)
        self.assertEqual(
            self.client.post("/api/ai/start/", {"brand_id": self.brand.id}, format="json").status_code,
            404,
        )
        self.assertEqual(self.client.get(f"/api/ai/report/{self.brand.id}/").status_code, 404)
