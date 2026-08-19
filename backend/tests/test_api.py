"""Integration tests hitting the API through a TestClient."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    r = client.post("/api/auth/register", json={"email": "u@x.com", "password": "password123"})
    assert r.status_code == 201
    r = client.post("/api/auth/login", data={"username": "u@x.com", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_duplicate_registration_conflicts(client):
    client.post("/api/auth/register", json={"email": "d@x.com", "password": "password123"})
    r = client.post("/api/auth/register", json={"email": "d@x.com", "password": "password123"})
    assert r.status_code == 409


def test_create_and_list_link(auth_client):
    client, headers = auth_client
    r = client.post("/api/links", json={"original_url": "https://example.com/page"}, headers=headers)
    assert r.status_code == 201
    body = r.json()
    assert body["short_code"]
    assert body["short_url"].endswith(body["short_code"])

    r = client.get("/api/links", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_custom_alias_and_collision(auth_client):
    client, headers = auth_client
    r = client.post(
        "/api/links",
        json={"original_url": "https://example.com", "custom_alias": "mylink"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["short_code"] == "mylink"

    r = client.post(
        "/api/links",
        json={"original_url": "https://other.com", "custom_alias": "mylink"},
        headers=headers,
    )
    assert r.status_code == 409


def test_redirect_flow(auth_client):
    client, headers = auth_client
    r = client.post(
        "/api/links",
        json={"original_url": "https://example.com/dest", "custom_alias": "goto"},
        headers=headers,
    )
    assert r.status_code == 201

    r = client.get("/goto", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com/dest"


def test_redirect_unknown_is_404(client):
    r = client.get("/does-not-exist", follow_redirects=False)
    assert r.status_code == 404


def test_requires_auth(client):
    r = client.get("/api/links")
    assert r.status_code == 401


def test_api_key_shorten_flow(auth_client):
    client, headers = auth_client
    r = client.post("/api/keys", json={"name": "ci", "monthly_quota": 100}, headers=headers)
    assert r.status_code == 201
    api_key = r.json()["api_key"]
    assert api_key.startswith("sx_")

    r = client.post(
        "/api/v1/shorten",
        json={"original_url": "https://example.com/via-api"},
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    assert r.json()["short_code"]

    # A bad key is rejected.
    r = client.post(
        "/api/v1/shorten",
        json={"original_url": "https://example.com"},
        headers={"X-API-Key": "sx_invalid"},
    )
    assert r.status_code == 401


def test_analytics_empty(auth_client):
    client, headers = auth_client
    client.post(
        "/api/links",
        json={"original_url": "https://example.com", "custom_alias": "an1"},
        headers=headers,
    )
    r = client.get("/api/analytics/an1", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_clicks"] == 0
    assert len(body["timeseries"]) == 30
