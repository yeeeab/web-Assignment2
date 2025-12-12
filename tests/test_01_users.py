from tests.utils import register, login, auth_header

def test_users_me_unauthorized_401(client):
    r = client.get("/api/v1/users/me")
    assert r.status_code == 401

def test_users_me_ok(client):
    register(client, "me@example.com", "P@ssw0rd!", "me")
    tok = login(client, "me@example.com").json()["accessToken"]
    r = client.get("/api/v1/users/me", headers=auth_header(tok))
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"

def test_update_me_ok(client):
    register(client, "up@example.com", "P@ssw0rd!", "up")
    tok = login(client, "up@example.com").json()["accessToken"]
    r = client.patch("/api/v1/users/me", headers=auth_header(tok), json={"nickname": "newnick"})
    assert r.status_code == 200
    assert r.json()["nickname"] == "newnick"

def test_change_password_wrong_current_401(client):
    register(client, "pw@example.com", "P@ssw0rd!", "pw")
    tok = login(client, "pw@example.com").json()["accessToken"]
    r = client.patch("/api/v1/users/me/password", headers=auth_header(tok),
                     json={"currentPassword": "wrongpass", "newPassword": "NewP@ssw0rd!"})
    assert r.status_code == 401

def test_change_password_ok(client):
    register(client, "pw2@example.com", "P@ssw0rd!", "pw2")
    tok = login(client, "pw2@example.com").json()["accessToken"]
    r = client.patch("/api/v1/users/me/password", headers=auth_header(tok),
                     json={"currentPassword": "P@ssw0rd!", "newPassword": "NewP@ssw0rd!"})
    assert r.status_code == 200
