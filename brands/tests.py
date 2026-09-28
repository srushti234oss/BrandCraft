from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Brand


class BrandApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="StrongPass123!")
        self.other_user = User.objects.create_user("other", password="StrongPass123!")
        self.owner_token = Token.objects.create(user=self.owner)
        self.other_token = Token.objects.create(user=self.other_user)
        self.brand = Brand.objects.create(
            owner=self.owner,
            name="Owner Brand",
            industry="Skincare",
            description="A conscious skincare line.",
            interview_data=[{"question": "Who is it for?", "answer": "Students"}],
            strategy_report="Saved report",
        )

    def authenticate_as(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_anonymous_users_cannot_access_brand_api(self):
        response = self.client.get("/api/brands/")
        self.assertEqual(response.status_code, 401)

    def test_create_brand_ignores_server_controlled_fields(self):
        self.authenticate_as(self.owner_token)
        response = self.client.post(
            "/api/brands/create/",
            {
                "name": "  New Brand  ",
                "industry": " Wellness ",
                "description": "  A wellbeing platform. ",
                "owner": self.other_user.id,
                "interview_data": [{"question": "Injected", "answer": "data"}],
                "strategy_report": "Injected report",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        brand = Brand.objects.get(id=response.data["id"])
        self.assertEqual(brand.owner, self.owner)
        self.assertEqual(brand.name, "New Brand")
        self.assertEqual(brand.industry, "Wellness")
        self.assertEqual(brand.interview_data, [])
        self.assertEqual(brand.strategy_report, "")

    def test_list_only_returns_brands_owned_by_authenticated_user(self):
        Brand.objects.create(
            owner=self.other_user,
            name="Other Brand",
            industry="Technology",
        )
        self.authenticate_as(self.owner_token)

        response = self.client.get("/api/brands/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [self.brand.id])

    def test_other_user_cannot_read_change_or_delete_a_brand(self):
        self.authenticate_as(self.other_token)
        url = f"/api/brands/{self.brand.id}/"

        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.patch(url, {"name": "Taken"}, format="json").status_code,
            404,
        )
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertTrue(Brand.objects.filter(id=self.brand.id).exists())

    def test_owner_can_update_brand_but_not_saved_strategy_fields(self):
        self.authenticate_as(self.owner_token)
        response = self.client.patch(
            f"/api/brands/{self.brand.id}/",
            {
                "name": "Updated Brand",
                "strategy_report": "Overwritten by client",
                "interview_data": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.name, "Updated Brand")
        self.assertEqual(self.brand.strategy_report, "Saved report")
        self.assertEqual(len(self.brand.interview_data), 1)
