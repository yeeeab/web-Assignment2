from sqlalchemy import select

from tests.utils import register, login, auth_header, create_category_as_admin, create_item, publish_item
from app.models.user import User, UserRole
from app.models.item import ItemStatus

def make_admin(client, db):
    # admin 생성
    r = register(client, "admin@example.com", "P@ssw0rd!", "admin")
    assert r.status_code in (200, 409)

    # DB에서 role 승격
    admin = db.scalar(select(User).where(User.email == "admin@example.com"))
    admin.role = UserRole.ADMIN
    db.commit()

    # admin 로그인
    admin_tok = login(client, "admin@example.com").json()["accessToken"]
    return admin_tok

def make_user(client, email="u1@example.com", nick="u1"):
    r = register(client, email, "P@ssw0rd!", nick)
    assert r.status_code in (200, 409)
    tok = login(client, email).json()["accessToken"]
    return tok

def test_category_create_admin_only_403(client, db):
    user_tok = make_user(client, "catuser@example.com", "catuser")
    r = client.post("/api/v1/categories", headers=auth_header(user_tok), json={"name": "X"})
    assert r.status_code == 403

def test_category_crud_ok(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "디지털기기")
    assert isinstance(cid, int)

    r = client.get("/api/v1/categories")
    assert r.status_code == 200

    r2 = client.patch(f"/api/v1/categories/{cid}", headers=auth_header(admin_tok), json={"name": "디지털기기2"})
    assert r2.status_code == 200

    r3 = client.delete(f"/api/v1/categories/{cid}", headers=auth_header(admin_tok))
    assert r3.status_code == 200

def test_item_create_and_publish_flow(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "가전")

    seller_tok = make_user(client, "seller@example.com", "seller")
    item_id = create_item(client, seller_tok, cid, title="macbook", start_price=0, bid_unit=100)

    # publish
    pub = publish_item(client, seller_tok, item_id)
    assert pub["ok"] is True

def test_item_update_only_draft_409(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "도서")
    seller_tok = make_user(client, "seller2@example.com", "seller2")

    item_id = create_item(client, seller_tok, cid, title="book", start_price=0, bid_unit=100)
    publish_item(client, seller_tok, item_id)

    r = client.patch(f"/api/v1/items/{item_id}", headers=auth_header(seller_tok), json={"title": "new"})
    assert r.status_code == 409  # 시작된 경매는 수정 불가

def test_bid_too_low_422(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "게임")
    seller_tok = make_user(client, "seller3@example.com", "seller3")
    bidder_tok = make_user(client, "bidder@example.com", "bidder")

    item_id = create_item(client, seller_tok, cid, title="switch", start_price=0, bid_unit=100)
    publish_item(client, seller_tok, item_id)

    r = client.post(f"/api/v1/items/{item_id}/bids", headers=auth_header(bidder_tok), json={"amount": 0})
    assert r.status_code == 422

def test_bid_ok_then_highest(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "스포츠")
    seller_tok = make_user(client, "seller4@example.com", "seller4")
    bidder_tok = make_user(client, "bidder2@example.com", "bidder2")

    item_id = create_item(client, seller_tok, cid, title="bike", start_price=0, bid_unit=100)
    publish_item(client, seller_tok, item_id)

    r1 = client.post(f"/api/v1/items/{item_id}/bids", headers=auth_header(bidder_tok), json={"amount": 100})
    assert r1.status_code == 200

    r2 = client.get(f"/api/v1/items/{item_id}/bids/highest")
    assert r2.status_code == 200
    assert r2.json()["highestBid"] == 100

def test_bid_on_not_open_409(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "기타")
    seller_tok = make_user(client, "seller5@example.com", "seller5")
    bidder_tok = make_user(client, "bidder3@example.com", "bidder3")

    item_id = create_item(client, seller_tok, cid, title="desk", start_price=0, bid_unit=100)
    # publish 안 했으니 DRAFT -> bid should 409
    r = client.post(f"/api/v1/items/{item_id}/bids", headers=auth_header(bidder_tok), json={"amount": 100})
    assert r.status_code == 409

def test_watch_duplicate_409(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "생활")
    seller_tok = make_user(client, "seller6@example.com", "seller6")
    watcher_tok = make_user(client, "watcher@example.com", "watcher")

    item_id = create_item(client, seller_tok, cid, title="vacuum", start_price=0, bid_unit=100)

    r1 = client.post(f"/api/v1/items/{item_id}/watch", headers=auth_header(watcher_tok))
    assert r1.status_code == 200
    r2 = client.post(f"/api/v1/items/{item_id}/watch", headers=auth_header(watcher_tok))
    assert r2.status_code == 409

def test_watch_list_ok(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "패션")
    seller_tok = make_user(client, "seller7@example.com", "seller7")
    watcher_tok = make_user(client, "watcher2@example.com", "watcher2")
    item_id = create_item(client, seller_tok, cid, title="coat", start_price=0, bid_unit=100)

    client.post(f"/api/v1/items/{item_id}/watch", headers=auth_header(watcher_tok))
    r = client.get("/api/v1/users/me/watches", headers=auth_header(watcher_tok))
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_close_and_winner_and_order_flow(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "전자")
    seller_tok = make_user(client, "seller8@example.com", "seller8")
    bidder_tok = make_user(client, "winner@example.com", "winner")
    loser_tok = make_user(client, "loser@example.com", "loser")

    item_id = create_item(client, seller_tok, cid, title="ipad", start_price=0, bid_unit=100)
    publish_item(client, seller_tok, item_id)

    client.post(f"/api/v1/items/{item_id}/bids", headers=auth_header(loser_tok), json={"amount": 100})
    client.post(f"/api/v1/items/{item_id}/bids", headers=auth_header(bidder_tok), json={"amount": 200})

    # close
    rclose = client.post(f"/api/v1/items/{item_id}/close", headers=auth_header(seller_tok))
    assert rclose.status_code == 200

    # winner
    rw = client.get(f"/api/v1/items/{item_id}/winner")
    assert rw.status_code == 200
    assert rw.json()["winnerUserId"] is not None
    assert rw.json()["price"] == 200

    # order: loser는 403
    r_forbidden = client.post(f"/api/v1/items/{item_id}/orders", headers=auth_header(loser_tok), json={"address": "addr"})
    assert r_forbidden.status_code == 403

    # order: winner ok
    r_ok = client.post(f"/api/v1/items/{item_id}/orders", headers=auth_header(bidder_tok), json={"address": "addr"})
    assert r_ok.status_code == 200

    # duplicate order 409
    r_dup = client.post(f"/api/v1/items/{item_id}/orders", headers=auth_header(bidder_tok), json={"address": "addr"})
    assert r_dup.status_code == 409

def test_admin_force_close_requires_admin_403(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "테스트")
    seller_tok = make_user(client, "seller9@example.com", "seller9")
    user_tok = make_user(client, "normal@example.com", "normal")
    item_id = create_item(client, seller_tok, cid, title="t", start_price=0, bid_unit=100)
    publish_item(client, seller_tok, item_id)

    r = client.patch(f"/api/v1/admin/items/{item_id}/force-close", headers=auth_header(user_tok))
    assert r.status_code == 403

def test_admin_force_close_ok(client, db):
    admin_tok = make_admin(client, db)
    cid = create_category_as_admin(client, admin_tok, "테스트2")
    seller_tok = make_user(client, "seller10@example.com", "seller10")
    item_id = create_item(client, seller_tok, cid, title="t2", start_price=0, bid_unit=100)
    publish_item(client, seller_tok, item_id)

    r = client.patch(f"/api/v1/admin/items/{item_id}/force-close", headers=auth_header(admin_tok))
    assert r.status_code == 200
