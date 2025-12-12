from tests.utils import register, login

def test_register_ok(client):
    r = register(client, "a@example.com", "P@ssw0rd!", "a")
    assert r.status_code == 200
    assert "accessToken" in r.json()

def test_register_duplicate_email_409(client):
    register(client, "dup@example.com", "P@ssw0rd!", "dup")
    r = register(client, "dup@example.com", "P@ssw0rd!", "dup2")
    assert r.status_code == 409

def test_login_ok(client):
    register(client, "b@example.com", "P@ssw0rd!", "b")
    r = login(client, "b@example.com")
    assert r.status_code == 200
    assert "accessToken" in r.json()

def test_login_wrong_password_401(client):
    register(client, "c@example.com", "P@ssw0rd!", "c")
    r = client.post("/api/v1/auth/login", json={"email": "c@example.com", "password": "wrongpass"})
    assert r.status_code == 401

def test_refresh_ok(client):
    register(client, "d@example.com", "P@ssw0rd!", "d")
    tokens = login(client, "d@example.com").json()
    r = client.post("/api/v1/auth/refresh", json={"refreshToken": tokens["refreshToken"]})
    assert r.status_code == 200
    assert "accessToken" in r.json()

def test_refresh_invalid_401(client):
    r = client.post("/api/v1/auth/refresh", json={"refreshToken": "invalid"})
    assert r.status_code == 401
