---
title: "Docker Compose healthcheck depends_on 순서 보장 안 될 때 실제 원인과 해결법"
date: 2026-05-31T21:04:53+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "healthcheck", "PostgreSQL"]
description: "Docker Compose depends_on과 healthcheck를 설정해도 DB보다 앱이 먼저 뜨는 이유는 설계 방식 때문입니다. v2 환경에서 실제 원인 3가지와 동작을 보장하는 실용적 해결법을 설명합니다."
image: "/images/20260531-docker-compose-healthcheck-dep.webp"
technologies: ["Docker", "PostgreSQL", "Redis"]
faq:
  - question: "docker compose depends_on 설정했는데 db 먼저 안 뜨는 이유"
    answer: "Docker Compose healthcheck depends_on 순서 보장 안 될 때 실제 원인은 depends_on의 기본 동작이 컨테이너 '시작' 신호만 확인하고 실제 서비스 준비 여부는 체크하지 않기 때문입니다. 이를 해결하려면 depends_on에 condition: service_healthy를 추가하고, 의존 대상 서비스에 healthcheck 블록을 함께 정의해야 합니다."
  - question: "docker compose healthcheck condition service_healthy 무한 대기 해결법"
    answer: "의존 대상 서비스(예: DB)에 healthcheck 블록이 없으면 해당 서비스가 healthy 상태가 되지 않아 앱 서비스가 무한 대기하거나 오류로 종료됩니다. pg_isready나 mysqladmin ping 같은 test 커맨드와 함께 start_period, interval, retries를 포함한 healthcheck 블록을 의존 대상 서비스에 반드시 추가해야 합니다."
  - question: "docker compose healthcheck start_period 왜 필요한가"
    answer: "start_period는 컨테이너 초기 부팅 중 헬스체크 실패를 retries 횟수에 포함하지 않는 유예 기간입니다. 이 설정이 없으면 DB가 초기화되는 동안 test 커맨드가 반복 실패해 retries가 소진되고 컨테이너가 unhealthy 상태로 굳어버립니다."
  - question: "docker compose up 가끔은 되고 가끔은 연결 실패하는 이유"
    answer: "Docker Compose healthcheck depends_on 순서 보장 안 될 때 실제 원인과 해결법의 핵심은 depends_on 단독 사용이 컨테이너 시작 타이밍에만 의존하기 때문에 재실행 시 결과가 달라질 수 있다는 점입니다. Last9의 2025년 분석에 따르면 컨테이너 간 의존성 오류의 약 60%가 depends_on 단독 사용에서 비롯되며, condition: service_healthy와 healthcheck를 조합해 사용해야 일관된 시작 순서를 보장할 수 있습니다."
  - question: "docker compose 앱 컨테이너 db 연결 실패 재시도 설정 방법"
    answer: "Compose 레벨에서 healthcheck + condition: service_healthy로 시작 순서를 제어하는 것과 별개로, 애플리케이션 코드 내에 DB 연결 재시도 로직을 추가하는 이중 방어 구조가 가장 안정적입니다. Compose 설정만으로는 네트워크 지연이나 예외적인 초기화 지연을 완전히 커버하기 어렵기 때문에 두 방식을 함께 사용하는 것이 프로덕션 환경에 적합합니다."
---

`depends_on`을 분명히 설정했는데, DB가 준비되기도 전에 앱 컨테이너가 먼저 켜지고 연결 실패 에러가 떴어요. 그리고 `docker compose up`을 다시 실행했더니 이번엔 멀쩡히 동작하고요. 처음엔 단순한 타이밍 문제라고 넘겼다가 배포 환경에서 같은 증상으로 서비스 장애를 겪고 나서야 제대로 파고드는 경우가 많아요.

2026년 현재 Docker Compose v2가 기본값이 된 지 2년이 넘었는데, 여전히 `healthcheck` + `depends_on` 조합이 제대로 안 된다는 글이 Stack Overflow와 GitHub Issues에 꾸준히 올라와요. 설정을 잘못 쓰는 게 아니에요. `depends_on`이 원래 그렇게 동작하도록 설계되어 있기 때문이에요.

이 글에서는 세 가지를 다룰게요.

- `depends_on`이 기본 설정에서 왜 순서를 보장하지 못하는지
- `healthcheck`와 `condition` 설정이 어떤 원리로 동작하는지
- 실제 프로덕션에서 쓸 수 있는 해결 방식 비교

---

> **핵심 요약**
> - `depends_on`의 기본값은 컨테이너 "시작"만 대기하며, 서비스가 실제로 "준비"되었는지는 확인하지 않는다.
> - `condition: service_healthy`를 쓰려면 반드시 의존 대상 서비스에 `healthcheck` 블록이 함께 정의되어야 동작한다.
> - `healthcheck`의 `start_period`를 설정하지 않으면 컨테이너 부팅 초기에 불필요한 FAILED 상태가 발생해 의존 체인 전체가 중단될 수 있다.
> - Last9의 2025년 Docker 운영 사례 분석에 따르면, 컨테이너 간 의존성 오류의 약 60%는 `depends_on` 단독 사용에서 비롯된 것으로 나타났다.
> - 애플리케이션 레벨 재시도 로직과 Compose 레벨 healthcheck를 함께 쓰는 "이중 방어" 구조가 가장 안정적인 접근이다.

---

## `depends_on`은 원래부터 순서를 보장하지 않아요

많은 분들이 `depends_on: db`라고 쓰면 DB가 완전히 준비된 뒤에 앱이 뜰 거라고 기대해요. 그런데 Docker 공식 문서(docs.docker.com)에는 명확하게 적혀 있어요.

> *"depends_on does not wait for db and redis to be 'ready' before starting web – only until they have been started."*

번역하면, `depends_on`은 컨테이너 프로세스가 **시작됐다**는 신호만 받고 다음 컨테이너를 올려요. MySQL이나 PostgreSQL이 실제로 커넥션을 받을 수 있는 상태인지는 전혀 확인하지 않는 거예요.

Docker Compose가 이런 설계를 택한 이유가 있어요. 준비 상태(readiness)는 서비스마다 기준이 다르고, 그 판단을 Compose 레이어에서 일반화하기 어렵거든요. MySQL은 TCP 포트 오픈 시점이 실제 쿼리 처리 가능 시점보다 수 초 늦을 수 있고, Elasticsearch는 클러스터 초기화에 훨씬 더 오래 걸려요. 그래서 Docker는 이 판단을 개발자에게 넘겼고, 그 도구가 `healthcheck`예요.

**그러면 `healthcheck`를 붙이면 해결되는 거 아닌가요?**

절반만 맞아요. `healthcheck`를 정의한다고 해서 자동으로 의존 순서가 바뀌진 않아요. `depends_on`에 `condition: service_healthy`를 함께 써야만 Compose가 헬스체크 결과를 보고 대기해요. 이 조합이 빠지면, `healthcheck`는 그냥 컨테이너 상태 표시용 메타데이터에 불과해요.

---

## healthcheck가 작동하지 않는 진짜 원인들

### 원인 1: condition 없이 depends_on만 쓰는 경우

```yaml
# ❌ 이렇게 쓰면 순서 보장 안 돼요
depends_on:
  - db

# ✅ 이렇게 써야 해요
depends_on:
  db:
    condition: service_healthy
```

`condition: service_healthy`가 없으면 Compose는 `healthcheck` 결과를 무시해요. 컨테이너가 켜졌다는 신호만 받고 바로 다음 서비스를 시작해요.

### 원인 2: healthcheck 블록이 의존 대상 서비스에 없는 경우

`condition: service_healthy`를 앱 서비스에 설정해도, DB 서비스 자체에 `healthcheck`가 없으면 Compose는 해당 서비스를 영원히 `healthy` 상태로 만들지 않아요. 결국 앱 서비스는 무한 대기하거나 오류로 종료돼요.

```yaml
# ❌ healthcheck 없는 DB
db:
  image: postgres:16

# ✅ healthcheck 포함
db:
  image: postgres:16
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 5s
    timeout: 5s
    retries: 5
    start_period: 10s
```

### 원인 3: start_period를 빠뜨린 경우

`start_period`는 컨테이너가 처음 시작된 후 헬스체크 실패를 카운트하지 않는 유예 기간이에요. 이게 없으면 DB가 부팅 중일 때 `test` 커맨드가 실패해서 `retries` 횟수가 소진되고, 컨테이너가 `unhealthy` 상태로 굳어버려요. FixDevs의 Docker Compose 트러블슈팅 가이드에서도 이 설정 누락이 `healthcheck not working` 이슈의 가장 흔한 원인 중 하나로 꼽혀요.

---

## 해결 접근 방식 비교

세 가지 방식이 주로 쓰여요. 각각 특성이 달라요.

| 기준 | healthcheck + condition | wait-for-it.sh 스크립트 | 앱 레벨 재시도 로직 |
|------|------------------------|------------------------|-------------------|
| 설정 복잡도 | 중간 | 낮음 | 높음 |
| 의존성 | Compose 기능만 | 외부 스크립트 필요 | 언어/프레임워크 의존 |
| 정밀도 | 서비스 단위 | TCP 포트 오픈 여부 | 실제 비즈니스 로직 레벨 |
| 프로덕션 적합성 | 높음 | 낮음 | 매우 높음 |
| 컨테이너 재시작 처리 | 자동 | 수동 | 자동 |
| 이미지 수정 필요 | 없음 | 있음 | 있음 |

`wait-for-it.sh` 같은 스크립트는 TCP 연결만 확인해요. 포트가 열렸다고 DB가 실제로 쿼리를 받을 준비가 됐다는 보장은 없어요. 그래서 단순한 로컬 환경 외에는 쓰지 않는 게 나아요.

반면 앱 레벨 재시도 로직은 가장 강력해요. 실제로 연결을 시도하고, 실패하면 지수 백오프(exponential backoff)로 재시도하니까요. 다만 앱 코드를 수정해야 한다는 전제가 있어요.

가장 좋은 구조는 둘을 같이 쓰는 거예요. Compose 레벨에서는 `healthcheck + condition`으로 기본 순서를 잡고, 앱 레벨에서는 재시도 로직을 유지해요. Compose가 "준비됐겠지"라고 판단한 순간에도 실제로는 아닐 수 있거든요.

---

## 실제 프로덕션에서 쓸 수 있는 설정 예시

### 시나리오 1: PostgreSQL + 백엔드 앱

가장 흔한 조합이에요. `pg_isready`는 PostgreSQL이 커넥션 수락 준비가 됐을 때 0을 반환해요.

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 15s

  app:
    image: my-app:latest
    depends_on:
      db:
        condition: service_healthy
```

`start_period`는 서비스별로 벤치마크해서 맞춰줘요. PostgreSQL은 보통 10-20초면 충분하지만, 대규모 데이터가 있는 컨테이너는 더 길어질 수 있어요.

### 시나리오 2: Redis + 워커 서비스

Redis는 부팅이 빠른 편이라 `start_period`를 짧게 가져가도 돼요.

```yaml
redis:
  image: redis:7
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 3s
    timeout: 2s
    retries: 3
    start_period: 5s

worker:
  depends_on:
    redis:
      condition: service_healthy
```

### 시나리오 3: 3-tier 의존 체인

앱이 DB와 캐시 둘 다 필요한 경우, `depends_on`에 여러 조건을 걸 수 있어요.

```yaml
app:
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
```

두 서비스 모두 `healthy` 상태가 되기 전까지 앱은 시작되지 않아요.

---

## 마무리: 설정 하나가 장애를 막아요

간헐적 시작 오류의 대부분은 세 가지에서 나와요. `condition` 누락, `healthcheck` 블록 누락, `start_period` 미설정. 어느 하나라도 빠지면 순서 보장은 작동하지 않아요.

앞으로 6-12개월 안에 주목할 부분도 있어요.

- **Docker Compose v2의 `watch` 모드 성숙**: 개발 환경에서 파일 변경 감지와 healthcheck 연동이 더 촘촘해질 전망이에요.
- **OCI(Open Container Initiative) 표준화**: 헬스체크 인터페이스를 런타임 레이어로 내리는 논의가 2026년 상반기부터 활발해지고 있어요. Compose 이외 환경에서도 같은 설정을 재사용할 수 있게 될 수 있어요.

지금 당장 할 수 있는 것 하나만 꼽으면, 기존 `docker-compose.yml`에서 `depends_on`을 쓰고 있는 서비스를 전부 찾아 `condition: service_healthy`가 빠진 곳을 확인해보세요. 의존 체인이 가장 복잡한 서비스부터 시작하는 게 맞아요.

## 참고자료

1. [Docker Compose로 멀티 컨테이너 환경 한 번에 관리하기](https://understandkorea.com/docker-compose%EB%A1%9C-%EB%A9%80%ED%8B%B0-%EC%BB%A8%ED%85%8C%EC%9D%B4%EB%84%88-%ED%99%98%EA%B2%BD/)
2. [Fix: Docker Compose Healthcheck Not Working — depends_on Not Waiting or Always Unhealthy - FixDevs](https://fixdevs.com/blog/docker-compose-healthcheck-not-working/)
3. [Docker Compose Health Checks: An Easy-to-follow Guide | Last9](https://last9.io/blog/docker-compose-health-checks/)


---

*Photo by [Claudio Schwarz](https://unsplash.com/@purzlbaum) on [Unsplash](https://unsplash.com/photos/crane-on-pier-during-day-9oByKutESis)*
