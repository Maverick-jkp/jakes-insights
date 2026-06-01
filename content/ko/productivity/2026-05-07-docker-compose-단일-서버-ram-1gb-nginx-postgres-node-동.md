---
title: "RAM 1GB 서버에서 Docker Compose로 Nginx·Postgres·Node 동시 운영 시 OOM 방지 설정 방법"
date: 2026-05-07T21:01:07+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "ram", "Node.js"]
description: "RAM 1GB VPS에서 Docker Compose로 Nginx, Postgres, Node 동시 운영 시 OOM 방지하는 법. Docker 데몬 150MB 포함 메모리 한계를 컨테이너별 mem_limit 설정으로 해결합니다."
image: "/images/20260507-docker-compose-단일-서버-ram-1gb-n.webp"
technologies: ["Node.js", "Docker", "PostgreSQL", "Linux"]
faq:
  - question: "Docker Compose 단일 서버 RAM 1GB Nginx Postgres Node 동시 운영 OOM 방지 설정 방법"
    answer: "RAM 1GB 서버에서 Docker Compose로 Nginx, Postgres, Node를 동시에 운영할 때 OOM을 방지하려면 각 컨테이너에 mem_limit과 memswap_limit을 동일하게 설정해 swap 사용을 차단하고, Nginx 64MB, Postgres 256MB, Node 300MB로 배분하면 OS와 Docker 데몬 오버헤드를 포함해도 안정적으로 운영할 수 있습니다. PostgreSQL shared_buffers를 기본 128MB에서 64MB로 낮추고 max_connections를 100에서 20으로 줄이는 튜닝도 필수입니다."
  - question: "도커 컨테이너 OOM Killer 방지하는 법"
    answer: "Linux OOM Killer는 메모리가 부족할 때 가장 많은 메모리를 점유한 프로세스를 강제 종료하는데, Docker Compose에서 mem_limit과 memswap_limit을 같은 값으로 설정하면 컨테이너가 예측 가능한 범위 안에서만 메모리를 사용하도록 강제할 수 있습니다. 이렇게 하면 swap에 의존해 응답 시간이 급격히 느려지는 상황도 함께 예방할 수 있습니다."
  - question: "Node.js V8 힙 메모리 제한 설정하는 방법"
    answer: "Node.js 실행 시 --max-old-space-size=256 플래그를 지정하지 않으면 V8 엔진이 서버 전체 RAM의 최대 절반까지 힙을 자동으로 확장하려 시도합니다. Docker 환경에서는 command: node --max-old-space-size=256 server.js 형태로 명시적으로 상한선을 지정해야 mem_limit 설정과 맞물려 메모리가 통제 범위 안에서 유지됩니다."
  - question: "PostgreSQL Docker 컨테이너 메모리 줄이는 설정"
    answer: "PostgreSQL의 기본 shared_buffers 값인 128MB는 4GB 이상 서버를 기준으로 한 권장값이므로, 1GB 서버에서는 64MB로 낮추면 단독 메모리 점유를 약 35% 줄일 수 있습니다. 추가로 max_connections를 기본값 100에서 20으로 낮추면 connection당 5~10MB씩 추가로 절감되어 소규모 서비스 환경에서는 충분한 성능을 유지하면서 안정성을 높일 수 있습니다."
  - question: "1GB RAM VPS에서 Docker Compose 단일 서버 RAM 1GB Nginx Postgres Node 동시 운영할 때 메모리 배분 기준"
    answer: "1GB RAM 서버에서 Linux 커널과 OS 기본 프로세스에 약 100MB, Docker 데몬에 약 100~150MB가 선점되어 실제 컨테이너에 배분 가능한 메모리는 700~750MB 수준입니다. Nginx 64MB, Postgres 256MB, Node 300MB로 총 620MB를 배분하면 남은 여유분으로 OS와 Docker 데몬 오버헤드를 감당할 수 있어 안정적인 운영이 가능합니다."
---

월 5달러짜리 VPS 하나. 거기다 서비스를 올렸는데 새벽 3시에 서버가 뻗었어요. 로그를 보면 딱 이 메시지예요. `Killed process — Out of Memory`. RAM 1GB짜리 단일 서버에서 Docker Compose로 Nginx, Postgres, Node를 동시에 돌리다 보면 꼭 한 번씩 만나는 상황이죠.

1GB RAM 서버는 여전히 사이드 프로젝트와 소규모 프로덕션 배포의 주력 스펙이에요. DigitalOcean, Vultr, Hetzner 기준으로 월 4~6달러대 가장 저렴한 tier가 1GB거든요. 문제는 Docker 데몬 자체가 약 150MB를 잡아먹고, 거기다 세 컨테이너를 아무 설정 없이 올리면 메모리가 그냥 터진다는 거예요. 이 글은 해당 환경에서 OOM 방지 설정을 어떻게 잡아야 하는지 데이터 기반으로 풀어드릴게요.

> **핵심 요약**
> - Docker 데몬 기본 오버헤드 약 150MB를 제외하면 세 컨테이너에 배분 가능한 실 메모리는 약 700~750MB다.
> - PostgreSQL `shared_buffers`를 기본값(128MB)에서 64MB로 낮추면 단독 메모리 점유를 약 35% 줄일 수 있다.
> - `mem_limit`과 `memswap_limit`을 동일하게 설정하면 Linux OOM Killer가 컨테이너를 강제 종료하기 전에 swap 사용을 차단해 예측 가능한 동작을 보장한다.
> - Node.js `--max-old-space-size` 플래그를 설정하지 않으면 V8 힙이 서버 전체 RAM의 최대 절반까지 자동으로 확장을 시도한다.

---

## 1GB 서버에서 Docker Compose가 자주 터지는 이유

### 기본 메모리 지형도

컨테이너 세 개를 올리기 전에 이미 메모리가 꽤 나가 있어요. 대략 이렇게 생각하면 돼요.

| 항목 | 메모리 점유 (대략) |
|------|------------------|
| Linux 커널 + OS 기본 프로세스 | ~100MB |
| Docker 데몬 (`dockerd`) | ~100~150MB |
| 남은 실사용 가능 메모리 | **~700~800MB** |

시작하기도 전에 사분의 일이 나간 셈이에요. 이 700MB를 세 서비스가 나눠 써야 해요.

### 컨테이너별 기본 점유량

아무 설정 없이 `docker compose up`을 치면 어떻게 될까요?

- **Nginx**: 가볍게 20~30MB. 사실 걱정 안 해도 돼요.
- **PostgreSQL 16**: 기본 `shared_buffers=128MB`에 connection 별 프로세스가 붙어요. idle 상태에서도 150~200MB는 기본이에요.
- **Node.js (Express/Fastify 기준)**: 앱 구조에 따라 다르지만, V8 힙이 기본으로 메모리를 공격적으로 잡아요. 트래픽이 조금만 올라오면 200~350MB까지 찍히는 경우가 흔해요.

합산하면 이미 400~580MB. 여기다 OS 오버헤드 더하면 한계치에 거의 닿아 있는 거예요. 조금만 spike가 오면 OOM Killer가 가장 많이 먹고 있는 프로세스를 찾아서 죽여요. 대부분 Node.js가 희생양이 돼요.

---

## Docker Compose 메모리 제한 설정: 실전 구성

### `mem_limit`과 `memswap_limit`의 차이

Docker Compose에서 메모리를 제어하는 핵심 설정이 이 둘이에요.

- `mem_limit`: 컨테이너가 쓸 수 있는 RAM 상한선
- `memswap_limit`: RAM + Swap 합산 상한선

`memswap_limit`을 `mem_limit`과 같게 설정하면 swap를 아예 못 쓰게 막는 거예요. swap를 쓰기 시작하면 디스크 I/O가 폭발적으로 늘어나고, 1GB 서버 환경에서 swap에 의존하는 순간 응답 시간이 열 배 이상 느려질 수 있거든요. 느려지는 것도 문제지만 SSD 수명도 갉아먹어요.

아래는 실제 `docker-compose.yml` 설정 예시예요.

```yaml
services:
  nginx:
    image: nginx:alpine
    mem_limit: 64m
    memswap_limit: 64m
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    mem_limit: 256m
    memswap_limit: 256m
    environment:
      POSTGRES_SHARED_BUFFERS: 64MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 128MB
      POSTGRES_WORK_MEM: 4MB
      POSTGRES_MAX_CONNECTIONS: 20
    restart: unless-stopped

  node:
    image: node:20-alpine
    mem_limit: 300m
    memswap_limit: 300m
    command: node --max-old-space-size=256 server.js
    restart: unless-stopped
```

총합 64 + 256 + 300 = 620MB. OS와 Docker 데몬 몫 250MB 남겨두면 딱 맞아요.

### PostgreSQL 튜닝이 핵심인 이유

Postgres는 기본 설정이 `shared_buffers=128MB`예요. 공식 문서에 따르면 이 값은 전체 RAM의 25%를 권장하는데, 4GB 이상 서버 기준이에요. 1GB 서버에선 64MB로 낮추는 게 맞아요.

`max_connections=20`도 중요해요. 기본값은 100인데, connection 하나당 약 5~10MB씩 추가 메모리를 잡거든요. 소규모 서비스에서 동시 접속 100개는 거의 없으니 20으로 내리는 게 현실적이에요.

### Node.js V8 힙 제한

`--max-old-space-size=256` 플래그가 없으면 V8은 사용 가능한 메모리를 계속 탐색해서 늘려요. Docker 컨테이너 안에서도 마찬가지예요. `mem_limit`을 300m로 잡고 V8 힙을 256m로 명시하면, Node가 256MB에서 GC를 적극적으로 돌리고 그 이상은 안 가요.

---

## 설정 방식 비교: 어떤 걸 골라야 할까요?

| 기준 | 메모리 제한 없음 | `mem_limit`만 설정 | `mem_limit` + 앱 레벨 튜닝 |
|------|-----------------|-------------------|--------------------------|
| OOM 방지 | ❌ 없음 | △ 부분적 | ✅ 강력 |
| 예측 가능성 | 낮음 | 중간 | 높음 |
| 설정 복잡도 | 없음 | 낮음 | 중간 |
| 재시작 안정성 | 낮음 | 중간 | 높음 |
| 권장 환경 | 로컬 개발 | 스테이징 | 프로덕션 |

`mem_limit`만 설정하면 컨테이너가 한도 초과 시 Docker가 직접 죽여요. 이게 OOM Killer보다는 낫지만, 앱 레벨에서도 제한을 걸어두면 GC가 먼저 정리해줘서 강제 종료 자체가 줄어들어요. 두 층을 같이 쓰는 게 제일 안전해요.

---

## 실전에서 체크해야 할 것들

**`restart: unless-stopped` 반드시 붙이기.** 메모리 제한에 걸려 컨테이너가 죽었을 때 자동으로 살아나야 서비스가 끊기지 않아요. `always`와 차이는, `unless-stopped`는 `docker stop`으로 직접 내린 컨테이너는 재시작 안 한다는 거예요. 의도치 않은 재시작을 막아주죠.

**health check 추가.** Postgres가 뜨기 전에 Node가 연결을 시도하면 크래시가 나요. `depends_on`의 `condition: service_healthy`를 쓰면 순서를 보장할 수 있어요.

**메모리 모니터링은 `docker stats` 커맨드로.** `docker stats --no-stream`을 cron으로 5분마다 기록해두면 어느 컨테이너가 메모리를 갉아먹는지 추적할 수 있어요. 프리미엄 모니터링 도구 없이도 충분히 파악 가능하거든요.

---

## 마무리: 지금 당장 확인해야 할 것

결국 세 가지 층을 동시에 잡는 거예요.

1. **Compose 레벨**: `mem_limit` + `memswap_limit` 동일 설정
2. **데이터베이스 레벨**: `shared_buffers`, `max_connections` 현실적으로 낮추기
3. **앱 레벨**: `--max-old-space-size`로 V8 힙 직접 제한

이 세 가지 중 하나라도 빠지면 어느 날 새벽에 서버가 뻗어 있어요. 세 개 다 잡으면 1GB짜리 서버도 꽤 오래 버텨요.

그럼 지금 운영 중인 서버에서 `docker stats`를 한번 돌려보세요. Node나 Postgres가 제한 없이 메모리를 올리고 있다면, 오늘 이 설정을 적용하는 게 답이에요.

---

*참고: [Setting Up PostgreSQL with Docker Compose — DEV Community](https://dev.to/saiful7778/setting-up-postgresql-with-docker-compose-for-development-and-production-45j8) / [Docker Compose Production Deployment — BetterLearning](https://eastondev.com/blog/en/posts/dev/20260424-docker-compose-production/) / [Docker 컨테이너 메모리 관리 — 성장하는 개발자](https://bluedreamer-twenty.tistory.com/6)*

## 참고자료

1. [Setting Up PostgreSQL with Docker Compose for Development and Production - DEV Community](https://dev.to/saiful7778/setting-up-postgresql-with-docker-compose-for-development-and-production-45j8)
2. [Docker Compose Production Deployment: Health Checks, Restart Policies, and Resource Limits · BetterL](https://eastondev.com/blog/en/posts/dev/20260424-docker-compose-production/)
3. [Docker 컨테이너 메모리 관리 및 OOM 대응 - 성장하는 개발자](https://bluedreamer-twenty.tistory.com/6)


---

*Photo by [Paul Lichtblau](https://unsplash.com/@laup) on [Unsplash](https://unsplash.com/photos/a-street-with-a-building-and-a-sign-on-it-0Hlm-8hB6JI)*
