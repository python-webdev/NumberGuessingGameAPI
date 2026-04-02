import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_limiter_storage


class TestPlayerEndpoints:
    def test_create_player(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/players/",
            json={"username": "testuser", "password": "testpassword"},
        )
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"

    def test_create_player_invalid_username(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/players/",
            json={"username": "ab", "password": "testpassword"},
        )
        assert response.status_code == 422

    def test_get_player(self, client: TestClient) -> None:
        created = client.post(
            "/api/v1/players/",
            json={"username": "testuser", "password": "testpassword"},
        )
        player_id = created.json()["id"]
        response = client.get(f"/api/v1/players/{player_id}")
        assert response.status_code == 200
        assert response.json()["id"] == player_id

    def test_get_player_not_found(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/players/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    def test_update_player_username(self, client: TestClient) -> None:
        created = client.post(
            "/api/v1/players/",
            json={"username": "oldname", "password": "testpassword"},
        )
        player_id = created.json()["id"]
        response = client.put(
            f"/api/v1/players/{player_id}", json={"username": "newname"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "newname"

    def test_search_players(self, client: TestClient) -> None:
        client.post(
            "/api/v1/players/",
            json={"username": "johndoe", "password": "testpassword"},
        )
        client.post(
            "/api/v1/players/",
            json={"username": "janedoe", "password": "testpassword"},
        )
        response = client.get("/api/v1/players/?username=john")
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestGameEndpoints:
    def _register_and_login(self, client: TestClient) -> tuple[str, str]:
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

    def test_create_game(self, client: TestClient) -> None:
        token, player_id = self._register_and_login(client)
        response = client.post(
            "/api/v1/games/",
            json={"player_id": player_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "active"

    def test_secret_number_not_in_response(self, client: TestClient) -> None:
        token, player_id = self._register_and_login(client)
        response = client.post(
            "/api/v1/games/",
            json={"player_id": player_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "secret_number" not in response.json()

    def test_submit_guess(self, client: TestClient) -> None:
        token, player_id = self._register_and_login(client)
        game = client.post(
            "/api/v1/games/",
            json={"player_id": player_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        game_id = game.json()["id"]
        response = client.post(
            f"/api/v1/games/{game_id}/guesses",
            json={"value": 50},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["result"] in ("too_low", "too_high", "correct")

    def test_guess_out_of_range(self, client: TestClient) -> None:
        token, player_id = self._register_and_login(client)
        game = client.post(
            "/api/v1/games/",
            json={"player_id": player_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        game_id = game.json()["id"]
        response = client.post(
            f"/api/v1/games/{game_id}/guesses",
            json={"value": 999},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestRateLimiting:
    @pytest.fixture(autouse=True)
    def reset_limiter(self):
        reset_limiter_storage()
        yield
        reset_limiter_storage()

    def test_create_player_rate_limit(self, client: TestClient) -> None:
        # 10 requests should succeed
        for i in range(10):
            response = client.post(
                "/api/v1/players/",
                json={
                    "username": f"ratelimituser{i}",
                    "password": "testpassword",
                },
            )
            assert response.status_code == 201

        # 11th request should be rate limited
        response = client.post(
            "/api/v1/players/",
            json={
                "username": "ratelimituser_extra",
                "password": "testpassword",
            },
        )
        assert response.status_code == 429

    def test_submit_guess_rate_limit(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/auth/register",
            json={"username": "guesser", "password": "testpassword"},
        )
        player_id = reg.json()["id"]
        login = client.post(
            "/api/v1/auth/token",
            data={"username": "guesser", "password": "testpassword"},
        )
        token = login.json()["access_token"]

        game = client.post(
            "/api/v1/games/",
            json={"player_id": player_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        game_id = game.json()["id"]

        reset_limiter_storage()

        # 30 requests should succeed (or stop when game ends — track active)
        for _ in range(30):
            response = client.post(
                f"/api/v1/games/{game_id}/guesses",
                json={"value": 50},
                headers={"Authorization": f"Bearer {token}"},
            )
            # Game may end before 30 guesses; stop if finished
            if response.status_code != 200:
                break
        else:
            # 31st request should be rate limited
            response = client.post(
                f"/api/v1/games/{game_id}/guesses",
                json={"value": 50},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 429


class TestHealthCheck:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["checks"]["database"]["status"] == "healthy"
