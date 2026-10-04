from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


TEST_USER_ID = "507f1f77bcf86cd799439011"


def fake_current_user():
    return {
        "_id": TEST_USER_ID,
        "name": "Test User",
        "email": "test@example.com",
    }


def fake_brand_service():
    class FakeBrandProfileService:

        def create_brand_profile(self, **kwargs):
            return {
                "id": "brand123",
                "user_id": kwargs["user_id"],
                "company_name": kwargs["company_name"],
                "industry": kwargs["industry"],
                "description": kwargs.get("description", ""),
                "target_audience": kwargs.get("target_audience", ""),
                "products_services": kwargs.get("products_services", []),
                "brand_tone": kwargs.get("brand_tone", ""),
                "website": kwargs.get("website", ""),
                "location": kwargs.get("location", ""),
                "competitors": kwargs.get("competitors", []),
                "social_links": kwargs.get("social_links", {}),
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }

        def get_brand_profile(self, user_id):
            return {
                "id": "brand123",
                "user_id": user_id,
                "company_name": "Test Company",
                "industry": "Technology",
                "description": "AI company",
                "target_audience": "Developers",
                "products_services": ["AI Software"],
                "brand_tone": "Professional",
                "website": "https://example.com",
                "location": "Mumbai",
                "competitors": ["Company A"],
                "social_links": {},
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }

        def update_brand_profile(self, **kwargs):
            profile = self.get_brand_profile(kwargs["user_id"])
            profile.update(kwargs["updates"])
            return profile

        def delete_brand_profile(self, user_id):
            return True

    return FakeBrandProfileService()


app.dependency_overrides.clear()

from routes.brand_profile import get_brand_profile_service
from utils.auth import get_current_user

app.dependency_overrides[get_current_user] = fake_current_user
app.dependency_overrides[get_brand_profile_service] = fake_brand_service


def test_create_brand_profile():
    response = client.post(
        "/api/brand-profile",
        json={
            "company_name": "Test Company",
            "industry": "Technology",
            "description": "AI company",
            "target_audience": "Developers",
            "products_services": ["AI Software"],
            "brand_tone": "Professional",
            "website": "https://example.com",
            "location": "Mumbai",
            "competitors": ["Company A"],
            "social_links": {},
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["company_name"] == "Test Company"
    assert data["industry"] == "Technology"
    assert data["user_id"] == TEST_USER_ID


def test_get_brand_profile():
    response = client.get("/api/brand-profile")

    assert response.status_code == 200

    data = response.json()

    assert data["company_name"] == "Test Company"
    assert data["industry"] == "Technology"
    assert data["user_id"] == TEST_USER_ID


def test_update_brand_profile():
    response = client.put(
        "/api/brand-profile",
        json={
            "company_name": "Updated Company",
            "brand_tone": "Friendly",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_name"] == "Updated Company"
    assert data["brand_tone"] == "Friendly"


def test_delete_brand_profile():
    response = client.delete("/api/brand-profile")

    assert response.status_code == 204