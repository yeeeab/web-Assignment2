텀프로젝트 진행 중에 새로운 인스턴스 만들어도 된다는 걸 모르고 그대로 해당 인스턴스에 텀프로젝트까지 올렸다가 과제 웹사이트 배포가 중단되었으며 해당 인스턴스로 접속이 되지 않는 오류가 발생하였습니다.
금일 내로 새로운 인스턴스에 배포하여 배포 정보 수정하겠습니다. 죄송합니다.

배포 정보 수정 완료했습니다.

# 중고 경매 플랫폼 백엔드 API 서버

## 프로젝트 설명

본 프로젝트는 **중고 경매 플랫폼을 위한 백엔드 REST API 서버**입니다.
FastAPI와 MySQL을 사용하여 구현하였으며, JWT 기반 인증/인가(RBAC)를 제공합니다.

* Framework: FastAPI
* Database: MySQL
* Auth: JWT (ROLE_USER, ROLE_ADMIN)
* Deployment: JCloud (Ubuntu)

---

## 배포 정보

### API Root

[http://113.198.66.75:10203/api/v1](http://113.198.66.75:10203/api/v1)

### Swagger (OpenAPI)

[http://113.198.66.75:10203/docs](http://113.198.66.75:10203/docs)

### Health Check

GET [http://113.198.66.75:10203/api/v1/health](http://113.198.66.75:10203/api/v1/health)

---

## 코드 설치 및 실행 방법 (FastAPI)

### 1. 가상환경 생성 및 활성화

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

```bash
export PYTHONPATH=src
```

### 4. DB 마이그레이션

```bash
alembic upgrade head
```

### 5. 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## JCloud 서버 실행 방법

### 1. 서버 접속

```bash
ssh -i kyb.pem -p 19203 ubuntu@113.198.66.75
```

### 2. 프로젝트 디렉토리 이동

```bash
cd ~/repo-root
```

### 3. 가상환경 생성 및 활성화

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. 패키지 설치

```bash
pip install -r requirements.txt
```

### 5. 환경변수 파일 생성 (.env)

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=auction
DB_USER=auction_user
DB_PASSWORD=********

JWT_SECRET_KEY=********
JWT_REFRESH_SECRET_KEY=********
```

> `.env` 파일은 **GitHub Public Repository에 포함하지 않으며**,
> Classroom을 통해서만 제출합니다.

### 6. 마이그레이션 및 실행

```bash
export PYTHONPATH=src
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 인증 / 인가

* JWT 기반 인증
* Role 기반 인가 (RBAC)

| Role       | 설명     |
| ---------- | ------ |
| ROLE_USER  | 일반 사용자 |
| ROLE_ADMIN | 관리자    |

---

## 주요 리소스

* auth
* users
* items
* bids
* orders
* categories
* watches
* stats
* admin

총 **30개 이상의 HTTP 엔드포인트**를 제공하며,
CRUD, 검색, 정렬, 페이지네이션, 관계형 Sub-resource를 포함합니다.

---

## Postman

* Postman Collection(JSON) 파일 제공
* 환경 변수(baseUrl, accessToken) 사용
* 인증 토큰 자동 주입 테스트 포함

---
