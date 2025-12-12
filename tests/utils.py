def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}

def register(client, email, password="P@ssw0rd!", nickname="u"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password, "nickname": nickname})

def login(client, email, password="P@ssw0rd!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})

def ensure_admin(client):
    # admin 계정 생성(이미 있으면 409 나도 무시)
    r = register(client, "admin@example.com", "P@ssw0rd!", "admin")
    if r.status_code not in (200, 409):
        raise AssertionError(r.text)

    # admin role 강제 세팅은 실제로는 DB에서 해야 맞는데,
    # seed 없이 테스트에서 admin을 바로 만들려면 "register에서 admin role"이 필요.
    # => 해결: 테스트에서 DB를 직접 건드려 admin role로 승격.
    # (아래 helper는 conftest에서 db session을 받아 처리)
    return

def create_category_as_admin(client, admin_token: str, name="디지털기기"):
    r = client.post("/api/v1/categories", headers=auth_header(admin_token), json={"name": name})
    if r.status_code == 409:
        # 이미 있으면 목록에서 찾아서 id 반환
        lst = client.get("/api/v1/categories").json()
        for c in lst:
            if c["name"] == name:
                return c["id"]
        raise AssertionError("category exists but cannot find")
    assert r.status_code == 200, r.text
    return r.json()["id"]

def create_item(client, token: str, category_id: int, title="item1", start_price=0, bid_unit=100):
    r = client.post(
        "/api/v1/items",
        headers=auth_header(token),
        json={
            "categoryId": category_id,
            "title": title,
            "description": "desc",
            "startPrice": start_price,
            "bidUnit": bid_unit,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]

def publish_item(client, token: str, item_id: int):
    r = client.post(f"/api/v1/items/{item_id}/publish", headers=auth_header(token))
    assert r.status_code == 200, r.text
    return r.json()
