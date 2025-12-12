import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus
from app.models.category import Category
from app.models.item import Item, ItemStatus
from app.models.bid import Bid
from app.models.watch import Watch
from app.models.order import Order, OrderStatus

UTC = timezone.utc

CATEGORIES = [
    "디지털기기", "가구/인테리어", "생활/주방", "유아동", "여성의류",
    "남성의류", "도서", "스포츠", "게임/취미", "기타",
]

ITEM_TITLES = [
    "맥북", "아이패드", "에어팟", "닌텐도 스위치", "PS5", "모니터",
    "키보드", "의자", "책상", "자전거", "러닝화", "카메라",
    "스피커", "마우스", "드라이기", "청소기",
]

def rand_email(i: int) -> str:
    return f"user{i:03d}@example.com"

def rand_nick(i: int) -> str:
    return f"user{i:03d}"

def rand_title() -> str:
    base = random.choice(ITEM_TITLES)
    return f"{base} {random.randint(1,999)}"

def rand_desc() -> str:
    return "상태 양호 / 직거래 선호 / 구성품 일부 포함"

def now() -> datetime:
    return datetime.now(UTC)

def ensure_admin_and_user(db: Session):
    # admin
    admin = db.scalar(select(User).where(User.email == "admin@example.com"))
    if not admin:
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("P@ssw0rd!"),
            nickname="admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        db.add(admin)

    user1 = db.scalar(select(User).where(User.email == "user1@example.com"))
    if not user1:
        user1 = User(
            email="user1@example.com",
            password_hash=hash_password("P@ssw0rd!"),
            nickname="user1",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(user1)

    db.commit()

def seed_categories(db: Session) -> list[Category]:
    existing = db.scalars(select(Category)).all()
    if existing:
        return existing

    cats = []
    for name in CATEGORIES:
        c = Category(name=name)
        db.add(c)
        cats.append(c)
    db.commit()
    return db.scalars(select(Category)).all()

def seed_users(db: Session, n: int = 30) -> list[User]:
    users = db.scalars(select(User)).all()
    if len(users) >= n:
        return users

    # 이미 있는 admin/user1 제외하고 추가
    existing_emails = {u.email for u in users}
    created = 0
    i = 1
    while created < n:
        email = rand_email(i)
        if email not in existing_emails and email not in ("admin@example.com", "user1@example.com"):
            u = User(
                email=email,
                password_hash=hash_password("P@ssw0rd!"),
                nickname=rand_nick(i),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            )
            db.add(u)
            created += 1
        i += 1
    db.commit()
    return db.scalars(select(User)).all()

def seed_items(db: Session, users: list[User], cats: list[Category], n: int = 120) -> list[Item]:
    existing = db.scalars(select(Item)).all()
    if len(existing) >= n:
        return existing

    # seller는 USER만
    sellers = [u for u in users if u.role == UserRole.USER and u.status == UserStatus.ACTIVE]
    items = []

    for _ in range(n):
        seller = random.choice(sellers)
        cat = random.choice(cats)
        start_price = random.randrange(0, 200_000, 1000)
        bid_unit = random.choice([100, 500, 1000, 5000])

        # 상태 랜덤: 대부분 OPEN, 일부 DRAFT/CLOSED
        status = random.choices(
            [ItemStatus.OPEN, ItemStatus.DRAFT, ItemStatus.CLOSED],
            weights=[70, 20, 10],
            k=1
        )[0]

        created_at = now() - timedelta(days=random.randint(0, 20))
        starts_at = None
        ends_at = None

        if status in (ItemStatus.OPEN, ItemStatus.CLOSED):
            starts_at = created_at
            ends_at = starts_at + timedelta(days=3)

        it = Item(
            seller_id=seller.id,
            category_id=cat.id,
            title=rand_title(),
            description=rand_desc(),
            start_price=start_price,
            bid_unit=bid_unit,
            status=status,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        db.add(it)
        items.append(it)

    db.commit()
    return db.scalars(select(Item)).all()

def seed_bids(db: Session, users: list[User], items: list[Item], n: int = 300) -> list[Bid]:
    existing = db.scalars(select(Bid)).all()
    if len(existing) >= n:
        return existing

    bidders = [u for u in users if u.role == UserRole.USER and u.status == UserStatus.ACTIVE]
    open_items = [it for it in items if it.status in (ItemStatus.OPEN, ItemStatus.CLOSED)]

    # 아이템별 현재가 추적
    current_price = {it.id: it.start_price for it in open_items}

    bids_created = 0
    tries = 0
    while bids_created < n and tries < n * 10:
        tries += 1
        it = random.choice(open_items)
        bidder = random.choice(bidders)
        if bidder.id == it.seller_id:
            continue

        cur = current_price[it.id]
        amount = cur + it.bid_unit * random.randint(1, 5)
        b = Bid(item_id=it.id, bidder_id=bidder.id, amount=amount)
        db.add(b)

        current_price[it.id] = amount
        bids_created += 1

    db.commit()
    return db.scalars(select(Bid)).all()

def seed_watches(db: Session, users: list[User], items: list[Item], n: int = 150):
    existing = db.scalars(select(Watch)).all()
    if len(existing) >= n:
        return

    user_ids = [u.id for u in users if u.role == UserRole.USER]
    item_ids = [it.id for it in items]

    created = 0
    tries = 0
    while created < n and tries < n * 10:
        tries += 1
        uid = random.choice(user_ids)
        iid = random.choice(item_ids)
        # 복합 PK 중복 방지
        if db.get(Watch, {"user_id": uid, "item_id": iid}):
            continue
        db.add(Watch(user_id=uid, item_id=iid))
        created += 1

    db.commit()

def seed_orders(db: Session, items: list[Item], n: int = 30):
    existing = db.scalars(select(Order)).all()
    if len(existing) >= n:
        return

    closed_items = [it for it in items if it.status == ItemStatus.CLOSED]
    random.shuffle(closed_items)

    created = 0
    for it in closed_items:
        if created >= n:
            break
        # 이미 주문 있으면 스킵
        if db.scalar(select(Order).where(Order.item_id == it.id)):
            continue

        # 낙찰자 = 최고입찰자
        top = db.scalar(select(Bid).where(Bid.item_id == it.id).order_by(Bid.amount.desc()).limit(1))
        if not top:
            continue

        st = random.choice([OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.COMPLETED])
        db.add(Order(
            item_id=it.id,
            buyer_id=top.bidder_id,
            total_price=top.amount,
            address="서울시 어딘가 123-45",
            status=st,
        ))
        created += 1

    db.commit()

def main():
    db = SessionLocal()
    try:
        ensure_admin_and_user(db)
        cats = seed_categories(db)
        users = seed_users(db, n=30)
        items = seed_items(db, users, cats, n=120)
        bids = seed_bids(db, users, items, n=300)
        seed_watches(db, users, items, n=150)
        seed_orders(db, items, n=30)

        # 대략 카운트 출력
        print("Seed done.")
        print("users:", len(db.scalars(select(User)).all()))
        print("categories:", len(db.scalars(select(Category)).all()))
        print("items:", len(db.scalars(select(Item)).all()))
        print("bids:", len(db.scalars(select(Bid)).all()))
        print("watches:", len(db.scalars(select(Watch)).all()))
        print("orders:", len(db.scalars(select(Order)).all()))
    finally:
        db.close()

if __name__ == "__main__":
    main()
