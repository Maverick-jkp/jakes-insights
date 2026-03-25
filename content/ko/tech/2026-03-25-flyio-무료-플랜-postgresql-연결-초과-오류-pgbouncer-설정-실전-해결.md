---
title: "Fly.io 무료 플랜 PostgreSQL 연결 초과 오류, PgBouncer 설정으로 실전 해결"
date: 2026-03-25T20:03:11+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-data", "Fly.io \ubb34\ub8cc \ud50c\ub79c PostgreSQL \uc5f0\uacb0 \ucd08\uacfc \uc624\ub958 PgBouncer \uc124\uc815 \uc2e4\uc804 \ud574\uacb0", "Python", "Next.js"]
description: "Fly.io 무료 플랜 PostgreSQL은 max_connections 25개 한도로 앱 확장 시 too many connections 오류가 발생합니다. PgBouncer 설정으로 수백 개 연결을 실제 DB 연결 몇 개로 줄이는 실전 해결법을 다룹니"
image: "/images/20260325-flyio-무료-플랜-postgresql-연결-초과-오.webp"
technologies: ["Python", "Next.js", "Node.js", "PostgreSQL", "Supabase"]
---

Fly.io로 사이드 프로젝트를 돌리다 갑자기 앱이 먹통이 됐어요. 로그를 열면 `too many connections`나 `connection reset by peer` 오류만 잔뜩 쌓여 있고요. 무료 플랜 PostgreSQL의 연결 한도는 생각보다 훨씬 낮아요. 그리고 이 문제, 2026년 현재도 Fly.io 커뮤니티에서 가장 많이 올라오는 질문 중 하나예요.

> **핵심 요약**
> - Fly.io 무료 플랜 PostgreSQL(shared-cpu-1x, 256MB)의 기본 `max_connections`는 약 25개로, 앱 인스턴스 수가 늘어나면 즉시 연결 초과 오류가 발생해요.
> - PgBouncer를 연결 풀러(connection pooler)로 앞에 세우면 수백 개의 앱 연결을 실제 DB 연결 몇 개로 압축할 수 있어요.
> - Fly.io 커뮤니티 포럼(2025~2026)에 따르면, TCP 연결이 조용히 끊기는(silent TCP drop) 현상이 무한 행(hang)을 일으키는 경우도 많아 `keepalive` 설정 조합이 필수예요.
> - 트랜잭션 모드 풀링을 쓰면 연결 한도 문제의 90% 이상을 해결하지만, prepared statement와의 호환성 문제를 별도로 처리해야 해요.

---

## 무료 플랜에서 연결이 자꾸 터지는 이유

Fly.io의 PostgreSQL은 내부적으로 Fly Machines 위에서 돌아가는 컨테이너예요. 무료 티어 기준인 `shared-cpu-1x, 256MB RAM` 환경에서 PostgreSQL이 할당받는 메모리는 넉넉하지 않아요. PostgreSQL은 연결 하나당 약 5~10MB의 메모리를 써요. 256MB 머신에서 안전하게 열 수 있는 연결은 수십 개 수준인 셈이에요.

실제로 `shared-cpu-1x 256MB` 인스턴스에 설정되는 `max_connections`는 기본값 기준 **25개** 내외예요. 반면 Node.js나 Python 앱에서 흔히 쓰는 ORM(Prisma, SQLAlchemy 등)은 앱 기동 시 기본적으로 10~20개 연결을 미리 열어놓아요. 앱 인스턴스가 두 개만 떠도 연결을 거의 다 써버리는 구조예요.

여기에 Fly.io 특유의 문제가 하나 더 있어요. Fly.io 커뮤니티 포럼에서 지속적으로 보고되는 **silent TCP drop** 현상이에요. 네트워크 레이어에서 TCP 연결이 조용히 끊겼는데, 앱이나 DB 양쪽 모두 이걸 인식하지 못한 채 응답을 무한정 기다리는 상황이 생겨요. 연결 풀은 가득 찼는데 아무 쿼리도 실행되지 않는, 가장 까다로운 유형의 오류가 만들어지는 거예요.

이 두 가지 문제가 겹치면 단순히 `max_connections`를 올리는 것만으로는 안 돼요. 연결 풀링과 keepalive 설정을 같이 잡아야 해요.

---

## PgBouncer는 어떻게 이 문제를 해결하나요?

### 연결 풀러의 원리: 적게 연결하고, 많이 처리하기

PgBouncer는 앱과 PostgreSQL 사이에 위치하는 경량 프록시예요. 앱은 PgBouncer에 연결하고, PgBouncer가 내부적으로 PostgreSQL과의 실제 연결 몇 개를 관리해요.

앱 인스턴스 5개가 각각 10개씩 연결을 열어도, PgBouncer는 그 50개 요청을 DB 연결 5개로 처리할 수 있어요. 앱 입장에서는 50개가 열려 있는 것처럼 보이지만, PostgreSQL은 5개만 처리하는 거예요.

PgBouncer가 지원하는 풀링 모드는 세 가지예요:

| 풀링 모드 | 연결 공유 시점 | DB 연결 수 | Prepared Statement | 적합한 상황 |
|-----------|--------------|-----------|-------------------|------------|
| Session | 클라이언트 연결 해제 시 | 많음 | 완전 지원 | 연결 수 절감 효과 낮음 |
| Transaction | 트랜잭션 완료 시 | **적음** | 불가 (우회 필요) | **무료 플랜 추천** |
| Statement | 쿼리 하나 완료 시 | 매우 적음 | 불가 | 단순 쿼리만 있을 때 |

무료 플랜에서는 **트랜잭션 모드(Transaction mode)**가 가장 효과적이에요. DB 연결 수를 가장 적게 유지하면서 동시 요청을 처리할 수 있거든요.

### Fly.io에서 PgBouncer 올리는 실전 설정

Fly.io에서 PgBouncer를 별도 앱으로 배포하는 방식이 가장 깔끔해요. `fly.toml`과 `pgbouncer.ini` 두 파일로 구성해요.

**`pgbouncer.ini` 핵심 설정:**

```ini
[databases]
mydb = host=<your-postgres-app>.internal port=5432 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 5432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 10
server_idle_timeout = 30
server_lifetime = 3600
tcp_keepalive = 1
tcp_keepidle = 10
tcp_keepintvl = 10
```

주목할 설정이 두 군데예요.

`default_pool_size = 10`은 실제 PostgreSQL에 열리는 연결 수예요. 무료 플랜의 `max_connections 25`에서 시스템 예약 연결 5개를 빼면 안전하게 쓸 수 있는 건 20개 안팎이에요. `default_pool_size`를 10~15 사이로 맞추세요.

`tcp_keepalive = 1`, `tcp_keepidle = 10`, `tcp_keepintvl = 10`은 앞서 언급한 silent TCP drop 문제를 잡는 설정이에요. 10초마다 keepalive 패킷을 보내서 끊긴 연결을 빠르게 감지하고 정리해요. Fly.io 커뮤니티 포럼에서 무한 hang의 해결책으로 가장 많이 언급되는 설정이에요.

### Prepared Statement 문제 우회하기

트랜잭션 모드의 유일한 단점은 prepared statement를 지원하지 않는 거예요. Prisma를 쓴다면 `connection_string`에 `?pgbouncer=true`를 추가해야 해요. SQLAlchemy라면 `use_native_enum=False`와 함께 연결 풀 설정에서 `NullPool`이나 `StaticPool`을 고려해야 해요.

Next.js + Prisma 조합이라면 `DATABASE_URL`을 이렇게 바꿔요:

```
postgresql://user:pass@pgbouncer-app.fly.dev:5432/mydb?pgbouncer=true&connection_limit=1
```

`connection_limit=1`은 서버리스 환경에서 각 함수가 연결을 하나만 열도록 강제하는 설정이에요. Fly.io 무료 플랜에서 특히 효과적이에요.

---

## Session 모드 vs Transaction 모드: 어떤 걸 골라야 할까요?

**Session 모드:**
- **장점**: Prepared statement 완전 지원, 앱 코드 수정 거의 없음
- **단점**: DB 연결 절감 효과가 제한적, 연결 수가 많은 상황에서 여전히 한도 초과 가능
- **맞는 상황**: ORM 호환성이 중요하고, 앱 인스턴스가 2~3개 이하일 때

**Transaction 모드:**
- **장점**: DB 연결을 10분의 1로 줄여요, 무료 플랜에서 확실한 효과
- **단점**: Prepared statement 미지원, ORM별 설정 수정 필요
- **맞는 상황**: 앱 인스턴스가 자주 스케일되거나 연결 초과 오류가 반복될 때

결론은 단순해요. 무료 플랜에서 `too many connections`가 뜬 적 있으면 트랜잭션 모드로 가세요.

---

## 실제로 적용하면 무엇이 달라지나요?

### 즉시 확인할 것들

PgBouncer를 올린 직후에는 두 가지를 확인해야 해요.

첫 번째, PostgreSQL에서 실제 연결 수를 봐요:

```sql
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

PgBouncer 전후를 비교하면 연결 수가 눈에 띄게 줄어있을 거예요.

두 번째, PgBouncer 자체 통계를 봐요. `SHOW POOLS;`, `SHOW STATS;` 명령으로 실시간 연결 상태를 확인할 수 있어요. `sv_idle`(대기 중 서버 연결)이 `default_pool_size`보다 훨씬 낮게 유지된다면 설정이 과도하게 잡힌 거예요. 반대로 `cl_waiting`(대기 중 클라이언트)이 자주 쌓이면 `default_pool_size`를 조금 올려야 해요.

### 6~12개월 안에 고려할 것들

Fly.io는 2025년 말부터 관리형 PostgreSQL의 연결 풀링 기능을 플랫폼 레벨에서 제공하는 방향으로 논의하고 있어요. 직접 PgBouncer를 관리하는 오버헤드가 사라질 수도 있어요.

Neon, Supabase 같은 서버리스 DB 서비스는 이미 HTTP 기반 연결 풀링을 제공해요. 무료 티어 한도 안에서 Fly.io 앱과 조합하는 사례도 늘고 있어요. 연결 문제가 반복된다면 DB 레이어 자체를 서버리스로 바꾸는 선택지도 충분히 검토할 만해요.

---

Fly.io 무료 플랜 PostgreSQL 연결 초과 오류는 PgBouncer 설정 하나로 해결할 수 있어요. 핵심은 트랜잭션 모드 풀링으로 DB 연결 수를 줄이고, keepalive 설정으로 silent TCP drop을 잡는 거예요.

지금 `too many connections` 오류가 없더라도, 앱 인스턴스가 두 개 이상이라면 미리 세워두는 편이 나아요. 장애는 항상 트래픽이 몰릴 때 터지거든요.

직접 설정해보고 `SHOW POOLS;`로 연결 수 변화를 확인해보세요. 숫자가 생각보다 극적으로 달라질 거예요.

## 참고자료

1. [Silent TCP connection drops to managed Postgres cause indefinite hangs - Questions / Help - Fly.io](https://community.fly.io/t/silent-tcp-connection-drops-to-managed-postgres-cause-indefinite-hangs/27429)


---

*Photo by [Pedro Henrique Santos](https://unsplash.com/@phcsantos) on [Unsplash](https://unsplash.com/photos/brown-and-black-guitar-hero-controller-ACS_PhO_iZI)*
