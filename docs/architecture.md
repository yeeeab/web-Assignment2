# Architecture

## 1) Overview

본 프로젝트는 **중고 경매(auction) 플랫폼**을 위한 REST API 서버입니다.
FastAPI 기반으로 API 레이어를 구성하고, SQLAlchemy ORM으로 MySQL DB에 접근하며, Alembic으로 마이그레이션을 관리합니다.
인증은 **JWT(Access/Refresh)** 기반이며, **RBAC(Role-based Access Control)** 로 `ROLE_USER / ROLE_ADMIN` 권한을 분리합니다.

* **Framework**: FastAPI
* **DB**: MySQL + SQLAlchemy
* **Migration**: Alembic
* **Auth**: JWT (Access / Refresh)
* **Docs**: Swagger(OpenAPI) `/docs`
* **Rate Limit**: slowapi (global default limit)
* **Deploy**: JCloud (Uvicorn)

---

## 2) Module Structure

프로젝트 주요 구조는 다음과 같습니다.

```
repo-root
├─ alembic.ini
├─ docs/
│  ├─ api-design.md
│  ├─ architecture.md
│  └─ db-schema.md
├─ postman/
│  └─ auction-api.postman_collection.json
├─ src/
│  ├─ alembic/
│  │  ├─ env.py
│  │  └─ versions/
│  └─ app/
│     ├─ main.py
│     ├─ api/
│     │  └─ v1/
│     │     ├─ router.py
│     │     ├─ auth.py
│     │     ├─ users.py
│     │     ├─ items.py
│     │     ├─ bids.py
│     │     ├─ orders.py
│     │     ├─ categories.py
│     │     ├─ watches.py
│     │     ├─ admin.py
│     │     ├─ stats.py
│     │     └─ health.py
│     ├─ core/
│     │  ├─ config.py
│     │  ├─ security.py
│     │  └─ errors.py
│     ├─ db/
│     │  ├─ session.py
│     │  └─ base.py
│     ├─ models/
│     │  ├─ user.py
│     │  ├─ item.py
│     │  ├─ bid.py
│     │  ├─ order.py
│     │  ├─ category.py
│     │  └─ watch.py
│     ├─ schemas/
│     │  ├─ common.py
│     │  ├─ auth.py
│     │  ├─ user.py
│     │  ├─ item.py
│     │  ├─ bid.py
│     │  ├─ order.py
│     │  ├─ category.py
│     │  ├─ watch.py
│     │  └─ admin.py
│     └─ api/
│        └─ deps.py
└─ tests/
```

---

## 3) Layered Design

요청 처리 흐름은 다음과 같은 계층 구조를 가집니다.

### 3-1. API Layer (Router / Controller)

* 위치: `src/app/api/v1/*.py`
* 역할:

  * URL 라우팅 및 HTTP 메서드 매핑
  * Request/Response 스키마 적용(Pydantic)
  * 인증/인가 의존성(Depends) 적용
  * DB 세션 주입 및 트랜잭션 처리
  * 표준 에러(AppError) 발생/전달

예) `/api/v1/items`, `/api/v1/auth/login` 등

### 3-2. Schema Layer (DTO)

* 위치: `src/app/schemas/*`
* 역할:

  * Request body 검증 (타입/필수값/형식)
  * Response 형태 고정 (Swagger 자동 문서화 포함)
  * 목록 응답 공통 포맷(PageRes 등) 정의

### 3-3. Domain/Model Layer (ORM)

* 위치: `src/app/models/*`
* 역할:

  * SQLAlchemy ORM 모델 정의
  * 관계(FK), 인덱스, Enum 상태 값 정의
  * 데이터 무결성 제약(Unique 등) 반영

### 3-4. Infrastructure Layer (DB / Config / Security)

* DB Session: `src/app/db/session.py`

  * MySQL 연결, 세션 생성/반환(`get_db`)
* Base/Meta: `src/app/db/base.py`

  * 모델 메타데이터 통합 (Alembic target_metadata)
* Settings: `src/app/core/config.py`

  * `.env` 기반 환경변수 로딩 및 설정값 제공
* Security: `src/app/core/security.py`

  * 비밀번호 해시/검증
  * JWT 생성/검증 (access/refresh)
* Error Handling: `src/app/core/errors.py`

  * AppError 정의
  * 표준 에러 응답 포맷 생성

---

## 4) Dependency Graph (High Level)

```
FastAPI app (main.py)
  └─ API Router (api/v1/router.py)
      ├─ endpoints (api/v1/*.py)
      │    ├─ depends (api/deps.py)
      │    ├─ schemas (schemas/*)
      │    ├─ models (models/*)
      │    └─ db session (db/session.py)
      └─ common infra (core/config.py, core/security.py, core/errors.py)
```

* **api/v1** 는 **schemas/models/db/core** 를 참조하지만,
* **models** 는 API 레이어를 참조하지 않도록 유지합니다. (단방향 의존성)

---

## 5) Request Lifecycle

1. Client → `FastAPI(app.main:app)` 요청
2. `api/v1/router.py`에서 라우팅
3. Endpoint 함수에서:

   * Pydantic Request 검증
   * `Depends(get_current_user / require_admin)` 등 인증/인가 수행
   * `Depends(get_db)`로 DB 세션 주입
4. 비즈니스 로직 수행 및 DB Commit
5. Pydantic Response로 직렬화 후 반환
6. 예외 발생 시:

   * `AppError` → `error_response()`로 통일된 JSON 반환
   * `RateLimitExceeded` → 429 표준 JSON 반환

---

## 6) Auth / RBAC

* JWT 구성

  * Access Token: API 접근용
  * Refresh Token: Access 재발급용
* Role

  * `ROLE_USER`: 일반 사용자 기능 사용
  * `ROLE_ADMIN`: 관리자 기능(유저 관리/통계 등) 접근
* 적용 방식

  * `get_current_user`: Access Token 검증 + 사용자 식별
  * `require_admin`: role 확인 후 관리자만 통과

---

## 7) Migration (Alembic)

* 위치: `src/alembic/`
* 설정: `alembic.ini`의 `script_location = src/alembic`
* `env.py`에서 모델 메타데이터를 참조하여 autogenerate 수행

---

## 8) Logging / Rate Limiting

* Rate limit:

  * `slowapi`를 사용해 전역(default) 제한 적용
* 에러 로깅:

  * 서버 콘솔 로그에 스택트레이스 기록(민감정보 제외)

---

## 9) Notes (Future Improvements)

* Service Layer 분리(비즈니스 로직을 API에서 분리)로 테스트/유지보수성 향상
* 캐시(Redis) 도입 및 검색 최적화
* 비동기 작업 큐(Celery/RQ)로 대용량 처리 대응
