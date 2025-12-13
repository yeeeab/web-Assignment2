# API Design

## 1. 개요

본 프로젝트는 **중고 경매 플랫폼 백엔드 API**로,  
과제 1에서 설계했던 주제와는 다르게 **주제를 변경하여 새롭게 API를 설계 및 구현**하였습니다.

- 기존 과제 1: 단순 CRUD 중심의 예제 도메인
- 과제 2: **실제 서비스 수준의 경매(Auction) 도메인**으로 재설계
- 인증/인가, 상태 전이, 통계 API 등 **비즈니스 로직 중심** 설계

API 설계는 FastAPI + RESTful API 원칙을 기반으로 하며,  
Swagger(OpenAPI)를 통해 자동 문서화됩니다.

---

## 2. API 기본 규칙

- **Base URL**
  ```
  /api/v1
  ```

- **인증 방식**
  - JWT Bearer Token
  - Authorization Header 사용
    ```
    Authorization: Bearer <accessToken>
    ```

- **응답 포맷**
  - 성공: HTTP Status Code + JSON
  - 실패: 공통 에러 응답 포맷 사용

---

## 3. 주요 리소스(도메인)

| 리소스 | 설명 |
|------|------|
| auth | 회원가입, 로그인, 토큰 재발급 |
| users | 사용자 정보, 비밀번호 변경, 내 정보 조회 |
| items | 경매 아이템 CRUD 및 상태 전이 |
| bids | 입찰 및 입찰 내역 조회 |
| orders | 낙찰 후 주문 관리 |
| categories | 아이템 분류 |
| watches | 찜(관심 상품) |
| admin | 관리자 전용 기능 |
| stats | 통계 조회 |
| health | 서버 상태 확인 |

---

## 4. 인증(Auth) API

| Method | Path | 설명 |
|------|------|------|
| POST | /auth/register | 회원가입 |
| POST | /auth/login | 로그인 (Access/Refresh Token 발급) |
| POST | /auth/refresh | 토큰 재발급 |
| POST | /auth/logout | 로그아웃 |

---

## 5. 사용자(User) API

| Method | Path | 설명 |
|------|------|------|
| GET | /users/me | 내 정보 조회 |
| PATCH | /users/me | 내 정보 수정 |
| PATCH | /users/me/password | 비밀번호 변경 |
| GET | /users/me/bids | 내 입찰 내역 |
| GET | /users/{user_id} | 사용자 단건 조회 |

---

## 6. 아이템(Item) API

| Method | Path | 설명 |
|------|------|------|
| POST | /items | 아이템 생성 |
| GET | /items | 아이템 목록 조회 (검색/정렬/페이지네이션) |
| GET | /items/{item_id} | 아이템 상세 조회 |
| PATCH | /items/{item_id} | 아이템 수정 |
| DELETE | /items/{item_id} | 아이템 삭제 |
| POST | /items/{item_id}/publish | 경매 시작 |
| POST | /items/{item_id}/close | 경매 종료 |
| GET | /items/{item_id}/winner | 낙찰자 조회 |

---

## 7. 입찰(Bid) API

| Method | Path | 설명 |
|------|------|------|
| POST | /items/{item_id}/bids | 입찰 |
| GET | /items/{item_id}/bids | 입찰 목록 조회 |
| GET | /items/{item_id}/bids/highest | 최고 입찰가 조회 |

---

## 8. 주문(Order) API

| Method | Path | 설명 |
|------|------|------|
| POST | /items/{item_id}/orders | 주문 생성 (낙찰자만 가능) |
| GET | /orders | 내 주문 목록 |
| GET | /orders/{order_id} | 주문 상세 |
| POST | /orders/{order_id}/cancel | 주문 취소 |

---

## 9. 카테고리(Category) API

| Method | Path | 설명 |
|------|------|------|
| GET | /categories | 카테고리 목록 |
| POST | /categories | 카테고리 생성 (Admin) |
| PATCH | /categories/{category_id} | 카테고리 수정 (Admin) |
| DELETE | /categories/{category_id} | 카테고리 삭제 (Admin) |

---

## 10. 찜(Watch) API

| Method | Path | 설명 |
|------|------|------|
| POST | /items/{item_id}/watch | 찜 등록 |
| DELETE | /items/{item_id}/watch | 찜 해제 |
| GET | /users/me/watches | 내 찜 목록 |

---

## 11. 관리자(Admin) API

| Method | Path | 설명 |
|------|------|------|
| GET | /admin/users | 사용자 목록 조회 |
| PATCH | /admin/users/{user_id}/deactivate | 사용자 비활성화 |
| PATCH | /admin/items/{item_id}/force-close | 아이템 강제 종료 |

---

## 12. 통계(Stats) API

| Method | Path | 설명 |
|------|------|------|
| GET | /stats/items/top-bid-count | 입찰 수 상위 아이템 |
| GET | /stats/sales/daily | 일별 매출 통계 (Admin) |

---

## 13. 헬스체크 API

| Method | Path | 설명 |
|------|------|------|
| GET | /health | 서버 상태 확인 |

- 인증 없이 접근 가능
- 버전, 빌드 시간, 서비스명 반환

---

## 14. 설계 특징 요약

- RESTful URL 구조
- 상태 전이 중심 설계 (Item: DRAFT → OPEN → CLOSED)
- JWT + Role 기반 인가 (USER / ADMIN)
- 검색/정렬/페이지네이션 공통 규칙
- 실제 서비스 흐름을 고려한 API 구성

---
