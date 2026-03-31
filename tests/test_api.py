import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import limiter


class TestPlayerEndpoints:
    def test_create_player(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/players/", json={"username": "testuser"}
        )
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"

    def test_create_player_invalid_username(self, client: TestClient) -> None:
        response = client.post("/api/v1/players/", json={"username": "ab"})
        assert response.status_code == 422

    def test_get_player(self, client: TestClient) -> None:
        created = client.post("/api/v1/players/", json={"username": "testuser"})
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
        created = client.post("/api/v1/players/", json={"username": "oldname"})
        player_id = created.json()["id"]
        response = client.put(
            f"/api/v1/players/{player_id}", json={"username": "newname"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "newname"

    def test_search_players(self, client: TestClient) -> None:
        client.post("/api/v1/players/", json={"username": "johndoe"})
        client.post("/api/v1/players/", json={"username": "janedoe"})
        response = client.get("/api/v1/players/?username=john")
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestGameEndpoints:
    def test_create_game(self, client: TestClient) -> None:
        player = client.post("/api/v1/players/", json={"username": "testuser"})
        player_id = player.json()["id"]
        response = client.post("/api/v1/games/", json={"player_id": player_id})
        assert response.status_code == 201
        assert response.json()["status"] == "active"

    def test_secret_number_not_in_response(self, client: TestClient) -> None:
        player = client.post("/api/v1/players/", json={"username": "testuser"})
        player_id = player.json()["id"]
        response = client.post("/api/v1/games/", json={"player_id": player_id})
        assert "secret_number" not in response.json()

    def test_submit_guess(self, client: TestClient) -> None:
        player = client.post("/api/v1/players/", json={"username": "testuser"})
        player_id = player.json()["id"]
        game = client.post("/api/v1/games/", json={"player_id": player_id})
        game_id = game.json()["id"]
        response = client.post(
            f"/api/v1/games/{game_id}/guesses", json={"value": 50}
        )
        assert response.status_code == 200
        assert response.json()["result"] in ("too_low", "too_high", "correct")

    def test_guess_out_of_range(self, client: TestClient) -> None:
        player = client.post("/api/v1/players/", json={"username": "testuser"})
        player_id = player.json()["id"]
        game = client.post("/api/v1/games/", json={"player_id": player_id})
        game_id = game.json()["id"]
        response = client.post(
            f"/api/v1/games/{game_id}/guesses", json={"value": 999}
        )
        assert response.status_code == 422


class TestRateLimiting:
    @pytest.fixture(autouse=True)
    def reset_limiter(self):
        limiter._storage.reset()
        yield
        limiter._storage.reset()

    def test_create_player_rate_limit(self, client: TestClient) -> None:
        # 10 requests should succeed
        for i in range(10):
            response = client.post(
                "/api/v1/players/", json={"username": f"ratelimituser{i}"}
            )
            assert response.status_code == 201

        # 11th request should be rate limited
        response = client.post(
            "/api/v1/players/", json={"username": "ratelimituser_extra"}
        )
        assert response.status_code == 429

    def test_submit_guess_rate_limit(self, client: TestClient) -> None:
        player = client.post("/api/v1/players/", json={"username": "guesser"})
        player_id = player.json()["id"]
        game = client.post("/api/v1/games/", json={"player_id": player_id})
        game_id = game.json()["id"]

        limiter._storage.reset()

        # 30 requests should succeed (or stop when game ends — track active)
        for i in range(30):
            response = client.post(
                f"/api/v1/games/{game_id}/guesses", json={"value": 50}
            )
            # Game may end before 30 guesses; stop if finished
            if response.status_code != 200:
                break
        else:
            # 31st request should be rate limited
            response = client.post(
                f"/api/v1/games/{game_id}/guesses", json={"value": 50}
            )
            assert response.status_code == 429


class TestHealthCheck:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["checks"]["database"]["status"] == "healthy"
