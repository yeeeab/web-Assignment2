# DB Schema (MySQL)

본 프로젝트는 MySQL을 사용하며, SQLAlchemy ORM + Alembic 마이그레이션으로 스키마를 관리합니다.
주요 테이블은 `users`, `categories`, `items`, `bids`, `orders`, `watches` 입니다.

---

## 1) Tables Overview

* `users`: 회원(일반/관리자), 상태/권한 관리
* `categories`: 상품 카테고리
* `items`: 경매 아이템(판매자, 시작가, 입찰단위, 상태, 경매 기간)
* `bids`: 입찰 내역(아이템별, 사용자별 입찰 기록)
* `orders`: 낙찰 후 주문(아이템당 1개 주문)
* `watches`: 찜(유저-아이템 N:M)
* `alembic_version`: Alembic 마이그레이션 버전 관리

---

## 2) ERD (Logical)

```
users (1) ──< items (N)
users (1) ──< bids  (N) >── (1) items
users (1) ──< orders (N)    (orders.buyer_id)
items (1) ── (0..1) orders  (orders.item_id UNIQUE)
users (N) >──< watches (N) >── (N) items
categories (1) ──< items (N)
```

---

## 3) Table Definitions

> 컬럼명/타입은 구현에 따라 다를 수 있으나, 아래 항목들은 프로젝트 로직상 필수입니다.

### 3-1. `users`

**Purpose**: 사용자/관리자 계정 및 인증 정보

* `id` (PK)
* `email` (UNIQUE, index)
* `password_hash`
* `nickname` (index optional)
* `role` (ENUM: `USER`, `ADMIN`)
* `status` (ENUM: `ACTIVE`, `DEACTIVATED`)
* `created_at`

**Indexes**

* `ix_users_email` (email)

---

### 3-2. `categories`

**Purpose**: 아이템 분류

* `id` (PK)
* `name` (UNIQUE, index)

**Indexes**

* `ix_categories_name` (name)

---

### 3-3. `items`

**Purpose**: 경매 아이템

* `id` (PK)
* `seller_id` (FK → `users.id`, index)
* `category_id` (FK → `categories.id`, index)
* `title` (index)
* `description`
* `start_price`
* `bid_unit`
* `status` (ENUM: `DRAFT`, `OPEN`, `CLOSED`)
* `starts_at` (nullable)
* `ends_at` (nullable, index)
* `created_at`

**Indexes**

* `ix_items_seller_id` (seller_id)
* `ix_items_category_id` (category_id)
* `ix_items_title` (title)
* `ix_items_status` (status)
* `ix_items_ends_at` (ends_at)

---

### 3-4. `bids`

**Purpose**: 입찰 내역

* `id` (PK)
* `item_id` (FK → `items.id`, index)
* `bidder_id` (FK → `users.id`, index)
* `amount` (index)
* `created_at`

**Indexes**

* `ix_bids_item_id` (item_id)
* `ix_bids_bidder_id` (bidder_id)
* `ix_bids_amount` (amount)

---

### 3-5. `orders`

**Purpose**: 낙찰 후 주문(아이템당 1건)

* `id` (PK)
* `item_id` (FK → `items.id`, **UNIQUE**)
* `buyer_id` (FK → `users.id`, index)
* `total_price`
* `address`
* `status` (ENUM: `PENDING`, `PAID`, `SHIPPED`, `COMPLETED`, `CANCELLED`)
* `created_at`

**Constraints**

* `UNIQUE(item_id)` : 아이템당 주문 1개만 생성

**Indexes**

* `ix_orders_buyer_id` (buyer_id)
* `ix_orders_status` (status)

---

### 3-6. `watches`

**Purpose**: 찜(유저-아이템 관계)

* `user_id` (FK → `users.id`)
* `item_id` (FK → `items.id`)
* `created_at`

**Constraints**

* **Composite PK**: `(user_id, item_id)`
  → 동일 유저가 동일 아이템을 중복 찜 불가

**Indexes**

* (Composite PK로 충분 / 필요 시 `(item_id)` 보조 인덱스 추가 가능)

---

## 4) Key Constraints Summary

* `items.seller_id` → `users.id`
* `items.category_id` → `categories.id`
* `bids.item_id` → `items.id`
* `bids.bidder_id` → `users.id`
* `orders.item_id` → `items.id` (UNIQUE)
* `orders.buyer_id` → `users.id`
* `watches.user_id` → `users.id`
* `watches.item_id` → `items.id`
* `watches (user_id, item_id)` composite PK

---

## 5) Notes

* 검색/정렬/페이지네이션을 고려해 `items`의 `status`, `title`, `ends_at`, `category_id` 등에 인덱스를 적용합니다.
* `orders`는 낙찰자(최고 입찰자)만 생성 가능하며, `UNIQUE(item_id)`로 중복 주문을 방지합니다.
* `watches`는 N:M 관계로 composite PK를 사용합니다.
