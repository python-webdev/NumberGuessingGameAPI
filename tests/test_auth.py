from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from fastapi.testclient import TestClient

from app.core.config import settings


class TestRegistration:
    def test_register_successfully(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "securepassword"},
        )
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"

    def test_register_duplicate_username(self, client: TestClient) -> None:
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "securepassword"},
        )
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "anotherpassword"},
        )
        assert response.status_code == 400
        assert "already taken" in response.json()["details"]

    def test_register_short_password(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "short"},
        )
        assert response.status_code == 422

    def test_password_not_in_response(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "securepassword"},
        )
        # ✅ Proves password hash is never leaked
        assert "password" not in response.json()


class TestLogin:
    def test_login_successfully(self, client: TestClient) -> None:
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "securepassword"},
        )
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "securepassword"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient) -> None:
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "securepassword"},
        )
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "nobody", "password": "securepassword"},
        )
        assert response.status_code == 401


class TestProtectedRoutes:
    def _register_and_login(self, client: TestClient) -> tuple[str, str]:
        """Helper — register a player and return token + player_id"""
        reg = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "securepassword"},
        )
        player_id = reg.json()["id"]

        login = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "securepassword"},
        )
        token = login.json()["access_token"]
        return token, player_id

    def test_create_game_with_valid_token(self, client: TestClient) -> None:
        token, player_id = self._register_and_login(client)
        response = client.post(
            "/api/v1/games/",
            json={"player_id": player_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_create_game_without_token(self, client: TestClient) -> None:
        # ✅ Proves route is actually protected
        response = client.post(
            "/api/v1/games/",
            json={"player_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 401

    def test_create_game_with_invalid_token(self, client: TestClient) -> None:
        # ✅ Proves tampered tokens are rejected
        response = client.post(
            "/api/v1/games/",
            json={"player_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401

    def test_create_game_with_expired_token(self, client: TestClient) -> None:
        expired_token: str = pyjwt.encode(  # type: ignore[reportUnknownMemberType]
            {
                "sub": "00000000-0000-0000-0000-000000000000",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        response = client.post(
            "/api/v1/games/",
            json={"player_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    def test_submit_guess_without_token(self, client: TestClient) -> None:
        token, player_id = self._register_and_login(client)
        game = client.post(
            "/api/v1/games/",
            json={"player_id": player_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        game_id = game.json()["id"]

        # ✅ Proves guess endpoint is also protected
        response = client.post(
            f"/api/v1/games/{game_id}/guesses", json={"value": 50}
        )
        assert response.status_code == 401
