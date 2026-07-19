---
title: "Fly.io 무료 플랜 Postgres 연결 초과 오류, PgBouncer 설정으로 실전 해결하기"
date: 2026-04-22T20:49:00+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "Fly.io \ubb34\ub8cc \ud50c\ub79c Postgres \uc5f0\uacb0 \ucd08\uacfc \uc624\ub958 PgBouncer \uc124\uc815 \uc2e4\uc804 \ud574\uacb0", "Django", "FastAPI"]
description: "Fly.io 무료 플랜 Postgres 최대 연결 25개 제한으로 too many clients 오류 발생 시 PgBouncer로 실전 해결하는 방법을 단계별로 설명합니다. 커넥션 풀 설정 실수와 수정 방법 포함."
image: "/images/20260422-flyio-무료-플랜-postgres-연결-초과-오류-.webp"
technologies: ["Django", "FastAPI", "PostgreSQL", "Go", "Supabase"]
faq:
  - question: "Fly.io 무료 플랜 Postgres too many clients already 오류 해결 방법"
    answer: "Fly.io 무료 플랜 Postgres 연결 초과 오류는 PgBouncer 설정으로 실전 해결할 수 있어요. 기본 포트 5432 대신 PgBouncer가 연결되는 5433 포트로 DATABASE_URL을 변경하고, pool_mode를 transaction으로 설정하면 실제 DB 연결 수를 10개 이하로 줄일 수 있어요. Fly.io는 Postgres 앱 내부에 PgBouncer를 공식 지원하므로 별도 서버 없이 설정 파일 수정만으로 즉시 적용 가능해요."
  - question: "PgBouncer transaction 모드 session 모드 차이점"
    answer: "session 모드는 앱 연결이 완전히 종료될 때만 DB 연결을 반환하기 때문에 연결 절감 효과가 거의 없어요. transaction 모드는 트랜잭션이 끝날 때마다 연결을 반환해서 연결 절감 효과가 매우 높고, 대부분의 일반 웹 앱에서 문제없이 사용할 수 있어요. statement 모드는 절감 효과는 가장 크지만 트랜잭션 자체를 사용할 수 없어 실무에서는 거의 사용하지 않아요."
  - question: "Fly.io Postgres max_connections 기본값이 25개인 이유"
    answer: "Fly.io 무료 플랜의 Postgres 인스턴스는 shared-cpu-1x, RAM 256MB 스펙으로 생성되는데, PostgreSQL은 연결 하나당 약 5~10MB 메모리를 소비해요. 256MB 제약 안에서 안정적으로 운영하려면 동시 연결 수를 25개 수준으로 제한할 수밖에 없어요. 이 때문에 워커와 스레드 수가 많은 프레임워크를 배포하면 연결 한도를 금방 초과하게 돼요."
  - question: "Fly.io 배포할 때 롤링 업데이트 중에 DB 연결 오류 나는 이유"
    answer: "Fly.io는 배포 시 롤링 업데이트 방식을 사용하기 때문에 기존 인스턴스와 새 인스턴스가 동시에 실행되는 순간이 발생해요. 이 순간 DB 연결 수가 일시적으로 두 배까지 늘어나 25개 한도를 쉽게 초과할 수 있어요. PgBouncer를 통해 실제 DB 연결 수를 평소에 10개 이하로 유지해두면 이런 배포 순간에도 연결 초과 오류를 피할 수 있어요."
  - question: "Fly.io 무료 플랜 Postgres 연결 초과 오류 PgBouncer 설정 실전 해결 후 연결 상태 확인하는 방법"
    answer: "fly postgres connect -a <앱이름> 명령으로 Postgres에 접속한 뒤, SELECT count(*), state FROM pg_stat_activity GROUP BY state; 쿼리로 현재 연결 수와 상태를 확인할 수 있어요. Fly.io 무료 플랜 Postgres 연결 초과 오류를 PgBouncer 설정으로 실전 해결한 후에는 실제 DB 연결 수가 default_pool_size로 설정한 값(예: 10개) 이하로 유지되는지 이 쿼리로 검증하는 것이 좋아요."
aliases:
  - "/tech/2026-04-22-flyio-무료-플랜-postgres-연결-초과-오류-pgbouncer-설정-실전-해결/"
  - "/ko/tech/2026-04-22-flyio-무료-플랜-postgres-연결-초과-오류-pgbouncer-설정-실전-해결/"

---

배포 직후 앱이 죽었어요. 로그를 보니 `too many clients already`. 접속자는 열 명도 안 됐는데.

Fly.io 무료 플랜으로 사이드 프로젝트를 돌리다 보면 이 상황, 꽤 자주 만나게 돼요. Fly.io 커뮤니티 포럼에서 이 주제 스레드 조회수는 수만 건에 달하고, 같은 오류로 질문을 올리는 사람이 매주 이어지고 있어요.

이 글에서는 왜 이 오류가 발생하는지, 그리고 **PgBouncer 설정으로 연결 초과 오류를 실전 해결**하는 방법을 정리할게요.

- Fly.io 무료 Postgres는 기본 최대 연결 수가 25개로 제한돼요
- 프레임워크의 기본 커넥션 풀 설정이 이 한계를 쉽게 초과시켜요
- PgBouncer는 연결 수를 수십 분의 일로 줄이는 가장 현실적인 해결책이에요
- 설정 방법은 Fly.io 환경에서 생각보다 간단해요

---

> **핵심 요약**
> - Fly.io 무료 플랜의 Postgres 인스턴스(`shared-cpu-1x`, 256MB RAM)는 `max_connections`가 기본 25로 설정되어 있어요.
> - Rails, Django, FastAPI 같은 프레임워크는 워커 수 × 스레드 수만큼 DB 연결을 생성하기 때문에, 인스턴스 두세 개만 띄워도 연결 한도를 금방 넘겨요.
> - PgBouncer의 `transaction` 풀링 모드를 적용하면 실제 DB 연결 수를 5개 이하로 줄이면서 수백 개의 앱 연결을 처리할 수 있어요.
> - Fly.io는 Postgres 앱 내부에 PgBouncer를 직접 실행하는 방식을 공식 지원하고 있고, 설정 파일 한 개로 즉시 적용 가능해요.

---

## Fly.io 무료 플랜, 연결이 이렇게 빨리 꽉 차는 이유

Fly.io는 `fly launch` 한 줄로 Postgres까지 같이 만들어주는 경험이 좋아서, 사이드 프로젝트 배포지로 많이 선택받아요.

문제는 무료 Postgres 인스턴스 스펙이에요. `shared-cpu-1x`에 RAM 256MB로 생성된 인스턴스는 PostgreSQL의 `max_connections` 파라미터가 기본 **25**로 잡혀 있어요. PostgreSQL은 각 연결마다 약 5~10MB의 메모리를 소비하는데, 256MB 제약 안에서 안전하게 운영하려다 보니 생긴 한계예요.

그런데 현대 웹 프레임워크는 연결을 아껴 쓰지 않아요. Fly.io에 배포한 Rails 앱이 워커 2개, 스레드 5개로 돌아가고 있다면, 이미 DB 연결을 최대 10개 잡고 있어요. 여기에 배포 시 롤링 업데이트로 인스턴스가 잠깐 두 배로 늘어나는 순간 20개. 백그라운드 잡 큐까지 있으면 25개를 순식간에 넘겨버려요.

Fly.io 커뮤니티 포럼(`community.fly.io`)에는 이 오류를 겪고 나서야 연결 수 구조를 처음 파악했다는 댓글이 반복해서 등장해요. 무료 플랜 사용자 중 상당수가 첫 배포 후 24시간 안에 이 오류를 만난다는 게 커뮤니티의 공통된 경험담이에요.

---

## PgBouncer가 뭐고, 왜 이게 답인가요

### PgBouncer의 핵심 역할

PgBouncer는 PostgreSQL 앞에 붙는 경량 커넥션 풀러예요. 앱은 PgBouncer에 연결하고, PgBouncer는 그 연결들을 실제 Postgres 연결 몇 개로 묶어서 처리해줘요. 100명이 줄을 서도 실제 창구는 5개만 열면 되는 구조예요.

PgBouncer는 세 가지 풀링 모드를 제공해요.

| 풀링 모드 | 연결 공유 시점 | DB 연결 절감 효과 | 주의사항 |
|-----------|--------------|-----------------|----------|
| `session` | 앱 연결 종료 시 | 낮음 | 기본값, 거의 절감 없음 |
| `transaction` | 트랜잭션 완료 시 | **높음 (권장)** | `SET`, `LISTEN` 등 일부 기능 제한 |
| `statement` | SQL 쿼리 완료 시 | 매우 높음 | 트랜잭션 불가, 실무 부적합 |

이 상황에서는 **`transaction` 모드**가 사실상 표준 답안이에요. `session` 모드는 절감 효과가 미미하고, `statement` 모드는 트랜잭션을 쓰지 못하기 때문에 대부분의 앱에서 쓸 수가 없어요.

### Fly.io 환경에서 PgBouncer 설정하는 방법

Fly.io의 Postgres 앱은 내부적으로 `flypg` 기반으로 동작하고, PgBouncer를 함께 실행하는 구조를 공식 지원해요.

**1단계: 현재 연결 상태 확인**

```bash
fly postgres connect -a <your-postgres-app-name>
```

접속 후:

```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
SHOW max_connections;
```

연결 수가 20개를 넘기 시작했다면 이미 위험 구간이에요.

**2단계: PgBouncer 포트 확인 및 연결 문자열 변경**

Fly.io Postgres 앱은 기본적으로 포트 **5432**가 직접 Postgres, 포트 **5433**이 PgBouncer를 통한 접속이에요. `fly.toml` 또는 앱 환경변수의 `DATABASE_URL`을 다음처럼 포트만 바꿔주면 돼요.

```
# 기존 (직접 연결)
postgres://user:pass@db.fly.dev:5432/mydb

# 변경 (PgBouncer 경유)
postgres://user:pass@db.fly.dev:5433/mydb
```

**3단계: PgBouncer 풀 설정 확인**

`pgbouncer.ini`에서 다음 값을 체크하세요.

```ini
pool_mode = transaction
max_client_conn = 200
default_pool_size = 10
```

`default_pool_size = 10`이면 실제 Postgres 연결은 10개 이내로 유지하면서 앱에서는 최대 200개 연결을 받을 수 있어요.

**4단계: 적용 후 재확인**

앱을 재시작하고 `pg_stat_activity`를 다시 조회하면, 실제 Postgres 연결 수가 10개 이하로 줄어든 걸 바로 확인할 수 있어요.

### 설정 후 주의할 것들

`transaction` 모드에서는 `LISTEN/NOTIFY`, `PREPARE` 구문, `SET LOCAL` 같은 세션 유지형 기능이 제한돼요. Active Record(Rails)나 SQLAlchemy는 대부분 문제없지만, `pg` 젬이나 asyncpg를 직접 쓰면서 세션 변수를 많이 쓰는 경우라면 사전 테스트가 필요해요.

---

## 오류를 방지하는 추가 접근법 비교

PgBouncer가 가장 강력한 해결책이지만, 상황에 따라 다른 방법도 있어요.

**앱 레벨 풀 크기 줄이기**
- **장점**: 코드 변경만으로 즉시 적용, 인프라 수정 불필요
- **단점**: 워커 수가 늘어나면 다시 초과될 수 있음, 근본 해결책 아님
- **적합한 경우**: PgBouncer 설정이 어렵거나, 연결 수가 경계선 수준일 때

**Fly.io Postgres 스케일업 (유료 플랜 전환)**
- **장점**: `max_connections` 한계 자체가 높아짐 (1GB RAM → 약 100개)
- **단점**: 비용 발생, 사이드 프로젝트엔 부담
- **적합한 경우**: 트래픽이 진짜 늘어서 무료 플랜 자체가 한계에 도달했을 때

**외부 관리형 DB 서비스 전환 (Supabase, Neon 등)**
- **장점**: 자체 PgBouncer/풀러 내장, 관리 부담 없음
- **단점**: Fly.io 내부 네트워크를 벗어나 지연 발생 가능
- **적합한 경우**: Fly.io Postgres 자체에 여러 이슈가 겹쳤을 때

그래서 빠른 해결이 목표라면 PgBouncer 설정이 답이에요. 비용 없이 즉시 적용되고, 효과가 가장 뚜렷하거든요.

---

## 지금 당장 해야 할 것, 그다음은

**지금 바로:** `pg_stat_activity`로 현재 연결 수를 확인하세요. 15개를 넘고 있다면 이미 예비 경고 구간이에요. PgBouncer 포트(5433)로 연결 문자열을 바꾸는 것만으로도 오류를 막을 수 있어요.

**다음 단계로:**
- `default_pool_size`와 `max_client_conn` 값을 앱의 워커 수에 맞게 조정하세요
- 롤링 업데이트 시 인스턴스가 일시적으로 늘어나는 구간의 연결 수도 시뮬레이션해보세요
- PgBouncer 로그를 주기적으로 확인해서 `cl_waiting` 값이 올라가는지 모니터링하세요

**앞으로 6~12개월:**

Fly.io는 2026년 들어 Postgres 관련 기능을 계속 업데이트하고 있어요. PgBouncer를 더 쉽게 켜고 끄는 UI가 추가될 가능성이 있고, 무료 플랜 메모리 한계도 조금씩 조정되는 움직임이 보여요. 다만 `max_connections` 제약 자체는 PostgreSQL 아키텍처 특성상 단기간에 사라질 성질의 것은 아니에요.

---

연결 초과 오류는 처음 만나면 당황스럽지만, PgBouncer 설정 하나로 완전히 해결되는 문제예요. 연결 문자열 포트 하나 바꾸는 것부터 시작해보세요. 지금 `pg_stat_activity`를 확인해봤을 때, 연결 수가 얼마나 나오고 있나요?

## 참고자료

1. [Fly Managed Postgres and database connection limit using the PG Bouncer - Phoenix - Fly.io](https://community.fly.io/t/fly-managed-postgres-and-database-connection-limit-using-the-pg-bouncer/27103)


---

*Photo by [Alex Gagareen](https://unsplash.com/@onepilot) on [Unsplash](https://unsplash.com/photos/black-and-silver-car-engine-AapHZdN_1-Y)*
