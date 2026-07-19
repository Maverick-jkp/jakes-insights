---
title: "Fly.io 무료 플랜 Postgres 연결 수 초과, PgBouncer로 해결한 1인 개발자 트러블슈팅"
date: 2026-05-17T20:26:46+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "fly.io", "postgres", "pgbouncer", "Python"]
description: "Fly.io 무료 플랜 Postgres는 최대 동시 연결 25개 제한으로 트래픽이 적어도 연결 초과가 발생합니다. PgBouncer로 다수 앱 연결을 단일 DB 연결로 묶어 해결한 1인 개발자 트러블"
image: "/images/20260517-flyio-무료-플랜-postgres-연결-수-초과-p.webp"
technologies: ["Python", "Next.js", "Node.js", "FastAPI", "PostgreSQL"]
faq:
  - question: "Fly.io 무료 플랜 Postgres too many connections 에러 해결 방법"
    answer: "Fly.io 무료 플랜 Postgres 연결 수 초과 문제는 PgBouncer 설정으로 해결할 수 있으며, 1인 개발자 트러블슈팅 사례에 따르면 Transaction 모드 적용 후 실제 연결 수를 90% 이상 줄인 경우가 보고됐습니다. pgbouncer.ini에서 default_pool_size를 5로 설정하면 앱 쪽에서 수십 개의 연결 요청이 들어와도 Postgres에는 5개 이내로만 전달됩니다. Fly.io 커뮤니티에서는 별도 앱을 띄우는 대신 기존 Postgres 앱 내부에 PgBouncer 프로세스를 추가하는 방식을 가장 많이 권장합니다."
  - question: "PgBouncer Transaction 모드 단점 prepared statement 문제"
    answer: "PgBouncer Transaction 모드는 연결 절약 효과가 가장 높지만, prepared statement를 사용할 수 없다는 제약이 있습니다. Prisma나 SQLAlchemy의 batch 모드처럼 ORM이 내부적으로 prepared statement를 사용하는 경우 에러가 발생할 수 있으므로 반드시 사전 확인이 필요합니다. Session 모드는 prepared statement를 지원하지만 연결 절약 효과가 낮아 Fly.io 무료 플랜처럼 연결 수가 타이트한 환경에서는 근본적인 해결책이 되기 어렵습니다."
  - question: "Fly.io Postgres max_connections 기본값 몇 개인가요"
    answer: "Fly.io 무료 플랜의 Postgres 인스턴스는 RAM이 256MB 수준으로, max_connections 기본값이 25~100 사이로 설정되지만 실제로는 25개 안팎에서 한도에 걸리는 경우가 많습니다. Node.js pg 라이브러리의 기본 풀 크기가 10개, SQLAlchemy는 최대 15개까지 열릴 수 있어 앱 인스턴스가 서너 개만 떠도 연결이 금방 소진됩니다. 트래픽이 적어도 앱이 idle 상태에서 연결을 계속 붙잡고 있기 때문에 트래픽 문제가 아니라 연결 생성 방식 자체의 구조적 문제입니다."
  - question: "Next.js serverless 환경 Postgres 연결 초과 방지하는 법"
    answer: "Next.js API route 같은 Serverless 환경은 함수 호출마다 새 연결을 열 수 있어 동시 요청 20개만 들어와도 연결이 20개 생성됩니다. PgBouncer Transaction 모드를 앞단에 두면 이 연결 요청을 5개 이내로 압축해 Postgres에 전달하므로 Fly.io 무료 플랜 Postgres 연결 수 초과 문제를 효과적으로 방지할 수 있습니다. 1인 개발자 트러블슈팅 관점에서는 PgBouncer 설정과 함께 DATABASE_URL을 PgBouncer 포트(6432)로 변경하는 것만으로 즉각적인 효과를 볼 수 있습니다."
  - question: "Fly.io PgBouncer 설정 방법 별도 앱 vs 같은 앱 내부"
    answer: "Fly.io에서 PgBouncer를 구성하는 방법은 기존 Postgres 앱 내부에 프로세스를 추가하는 방식과 별도의 전용 앱을 띄우는 방식 두 가지가 있습니다. Fly.io 커뮤니티에서는 같은 앱 내부에서 실행하는 방식을 권장하는데, 네트워크 홉이 줄고 무료 플랜에서 추가 앱을 띄울 필요가 없기 때문입니다. 핵심 설정은 pool_mode를 transaction으로, default_pool_size를 5로 지정하는 것이며 max_client_conn과 default_pool_size의 차이가 커넥션 절약 효과를 결정합니다."
aliases:
  - "/tech/2026-05-17-flyio-무료-플랜-postgres-연결-수-초과-pgbouncer-설정-1인-개발자-트/"
  - "/ko/tech/2026-05-17-flyio-무료-플랜-postgres-연결-수-초과-pgbouncer-설정-1인-개발자-트/"

---

배포는 됐어요. 그런데 앱이 안 뜨죠.

로그를 열었더니 `too many connections for role` 에러. 트래픽은 하루 수십 명 수준인데, Postgres가 연결 수 초과로 죽어 있어요. 1인 개발자 입장에서 이 상황은 꽤 당혹스러워요. Fly.io 무료 플랜에서 Postgres를 쓰는 개발자라면 2026년 현재도 이 함정에 빠지는 경우가 많거든요.

> **핵심 요약**
> - Fly.io 무료 플랜의 Postgres 인스턴스는 기본 최대 동시 연결 수가 25개로 제한되며, Node.js나 Python 기반 앱은 기본 커넥션 풀 설정만으로도 이 한도를 쉽게 초과해요.
> - PgBouncer는 여러 앱 연결을 하나의 Postgres 연결로 묶어주는 커넥션 풀러로, Fly.io 커뮤니티에 따르면 설정 후 실제 연결 수를 90% 이상 줄인 사례가 보고됐어요.
> - Transaction 모드로 PgBouncer를 구성하면 연결 수를 가장 효과적으로 줄일 수 있지만, prepared statement를 못 쓰는 제약이 생겨요.
> - 1인 개발자에게 이 트러블슈팅은 단순한 에러 해결이 아니라, 앱 아키텍처를 처음부터 다시 생각하게 만드는 계기예요.

---

## Fly.io 무료 Postgres, 연결이 이렇게 빨리 차는 이유

Fly.io의 Managed Postgres는 1인 개발자에게 매력적인 선택이에요. 클릭 몇 번으로 Postgres를 띄울 수 있고, 무료 플랜에서 시작해서 나중에 스케일업하면 되니까요.

문제는 구조에 있어요.

Fly.io Postgres는 내부적으로 PostgreSQL 프로세스가 직접 연결을 받아요. PostgreSQL은 연결 하나당 프로세스 하나를 생성하는 방식이에요. RAM이 256MB인 무료 인스턴스에서 `max_connections`는 기본값으로 25~100 사이로 설정되는데, 실제로는 25개 안팎에서 벽이 생기는 경우가 많아요.

그런데 Node.js의 `pg` 라이브러리는 기본 풀 크기가 10이에요. FastAPI + SQLAlchemy 조합이라면 기본 `pool_size=5`에 `max_overflow=10`이라 최대 15개까지 열릴 수 있어요. 앱 인스턴스가 서너 개만 떠도 연결이 꽉 차요.

Fly.io 공식 커뮤니티 포럼에서도 이 주제는 반복적으로 등장해요. 대부분 "트래픽은 적은데 연결 초과가 나냐"는 질문이에요. 트래픽 문제가 아니라 연결 생성 방식 자체의 문제거든요. 앱이 idle 상태에서도 연결을 붙잡고 있기 때문이에요.

---

## PgBouncer가 하는 일: 연결 대리인

PgBouncer는 앱과 Postgres 사이에 앉아서 연결을 중계해줘요. 단순하게 설명하면 이래요:

앱 → PgBouncer → PostgreSQL

앱 쪽에서 연결 100개가 와도, PgBouncer가 Postgres에는 실제로 5개만 열어서 돌려막기 해요. HashCoder의 분석에 따르면 이 방식으로 동일 트래픽 대비 처리량을 세 배까지 높인 사례가 있어요.

PgBouncer에는 세 가지 풀링 모드가 있어요.

### Session 모드 vs Transaction 모드 vs Statement 모드

| 항목 | Session 모드 | Transaction 모드 | Statement 모드 |
|------|------------|----------------|--------------|
| 연결 공유 시점 | 세션 종료 시 | 트랜잭션 종료 시 | 쿼리 종료 시 |
| 연결 절약 효과 | 낮음 | **높음** | 매우 높음 (불안정) |
| Prepared Statement | 가능 | ❌ 불가 | ❌ 불가 |
| SET 명령 유지 | 가능 | 제한적 | 불가 |
| 1인 개발자 추천 | 보조용 | **기본 선택** | 비추천 |

Transaction 모드가 핵심이에요. 연결을 트랜잭션이 끝나는 즉시 풀에 반환하기 때문에 실제 Postgres 연결 수를 극적으로 줄일 수 있어요.

단, prepared statement를 못 써요. SQLAlchemy에서 `use_batch_mode=True` 설정이 있거나, Prisma 같은 ORM이 내부적으로 prepared statement를 쓴다면 에러가 날 수 있어요. 반드시 확인하세요.

### Fly.io에서 PgBouncer 붙이는 현실적인 방법

Fly.io에서 PgBouncer를 쓰는 방법은 크게 두 가지예요.

**방법 A:** Fly.io Postgres 앱 안에서 `pgbouncer` 프로세스를 직접 띄우기 (`fly.toml`에 프로세스 추가)

**방법 B:** 별도의 PgBouncer 전용 Fly 앱을 띄우고, DATABASE_URL을 그쪽으로 연결

Fly.io 커뮤니티 포럼에서 가장 많이 권장되는 방식은 방법 A예요. 같은 앱 내에서 실행하면 네트워크 홉이 줄고, 무료 플랜에서 추가 앱을 띄울 필요도 없어요.

`pgbouncer.ini` 핵심 설정은 이래요:

```ini
[databases]
mydb = host=localhost port=5432 dbname=mydb

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 5
listen_port = 6432
```

`max_client_conn`은 앱이 PgBouncer에 열 수 있는 최대 연결 수고, `default_pool_size`가 실제 Postgres로 가는 연결 수예요. 이 두 값의 차이가 PgBouncer의 마법이에요.

---

## 실제로 어떤 시나리오에서 이게 필요한가

**시나리오 1 - Next.js + Serverless 함수 조합**

Serverless 환경은 함수 호출마다 새 연결을 열 수 있어요. Next.js API route에 동시 요청 20개만 들어와도 연결이 20개 생겨요. PgBouncer Transaction 모드면 이걸 5개 이내로 눌러줘요.

**시나리오 2 - FastAPI + SQLAlchemy**

SQLAlchemy의 `NullPool`을 쓰거나 `pool_size`를 1~2로 낮추는 방법도 있어요. 하지만 이건 성능을 포기하는 방식이에요. PgBouncer를 앞에 두면 SQLAlchemy는 여전히 커넥션 풀을 유지하면서, Postgres로 가는 실제 연결만 줄어들어요.

**시나리오 3 - 여러 앱이 같은 DB를 쓸 때**

Fly.io에서 여러 앱이 하나의 Postgres를 바라볼 때, 각 앱의 DATABASE_URL을 PgBouncer 포트(6432)로 바꾸면 돼요. Postgres 입장에서는 연결이 PgBouncer 하나뿐인 것처럼 보여요.

---

## 1인 개발자가 지금 당장 해야 할 것

트러블슈팅 순서를 정리하면 이래요.

1. **현재 연결 수 확인**: `SELECT count(*) FROM pg_stat_activity;` 로 현재 연결 상태 파악
2. **앱 사이드 풀 설정 점검**: 각 라이브러리의 기본 풀 크기 확인 (Node `pg`: 10, SQLAlchemy: 5+10)
3. **PgBouncer 추가 결정**: 연결 수가 `max_connections`의 70%를 넘으면 추가 고려
4. **Transaction 모드로 시작**: prepared statement 이슈 없으면 Transaction 모드가 가장 효과적
5. **`SHOW POOLS;` 로 모니터링**: PgBouncer에 접속해서 `SHOW POOLS;` 치면 실시간 상태 확인 가능

앞으로 Fly.io 무료 플랜 생태계는 더 많은 1인 개발자들이 진입하면서, 이 연결 수 문제는 더 자주 등장할 거예요. Fly.io 측에서도 Managed Postgres에 내장 PgBouncer 옵션을 제공하는 방향을 커뮤니티에서 요청하고 있는 상태고요.

---

## 마무리: 연결 수 문제는 구조 문제예요

- Fly.io 무료 플랜 Postgres는 연결 수 한도가 낮고, 앱 사이드 기본 설정만으로도 쉽게 초과해요
- PgBouncer는 앱 연결을 Postgres 연결과 분리해서 실제 DB 연결 수를 90% 이상 줄일 수 있어요
- Transaction 모드가 가장 효과적이지만, prepared statement 비호환성은 반드시 테스트해야 해요
- 1인 개발자 트러블슈팅의 핵심은 에러 메시지보다 연결 생성 구조를 이해하는 데 있어요

배포 후 에러가 났을 때, 로그의 `too many connections`는 사실 앱이 아니라 아키텍처가 보내는 신호예요. PgBouncer 설정 한 번으로 해결되는 문제인데, 모르면 유료 플랜으로 업그레이드하거나 앱 자체를 뜯어고치게 되죠.

지금 Fly.io Postgres를 쓰고 있다면, `pg_stat_activity` 쿼리 한 번만 쳐보세요. 연결이 몇 개나 열려 있나요?

## 참고자료

1. [Fly Managed Postgres and database connection limit using the PG Bouncer - Phoenix - Fly.io](https://community.fly.io/t/fly-managed-postgres-and-database-connection-limit-using-the-pg-bouncer/27103)
2. [The Developer's Guide to Taming PostgreSQL: How We Tripled Throughput with PgBouncer | by HashCoder ](https://hashcoder.medium.com/the-developers-guide-to-taming-postgresql-how-we-tripled-throughput-with-pgbouncer-8409854dd4af)


---

*Photo by [Alex Gagareen](https://unsplash.com/@onepilot) on [Unsplash](https://unsplash.com/photos/black-and-silver-car-engine-AapHZdN_1-Y)*
