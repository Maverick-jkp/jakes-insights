---
title: "Prometheus Grafana Docker Compose 2GB VPS OOM 없이 안정화하는 설정 방법"
date: 2026-03-10T20:03:26+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "prometheus", "grafana", "docker"]
description: "2GB VPS에서 Prometheus·Grafana Docker Compose 운영 시 기본 15초 스크랩 간격이 수 시간 내 메모리 1GB를 초과합니다. OOM Killer 없이 안정화하는 실전 설정값을 정리했습니다."
image: "/images/20260310-prometheus-grafana-docker-comp.webp"
technologies: ["Docker"]
faq:
  - question: "Prometheus Grafana Docker Compose VPS 메모리 2GB 이하 OOM 없이 안정화 설정 방법"
    answer: "Prometheus에 --storage.tsdb.retention.time=7d와 --storage.tsdb.retention.size=400MB 플래그를 추가하고, Docker Compose에서 Prometheus 600MB, Grafana 200MB로 mem_limit을 명시하면 됩니다. 스크랩 간격을 15초에서 30초로 늘리면 하루 샘플 수가 절반으로 줄어 메모리 사용량이 40~60% 감소해요. 이 세 가지 조합으로 2GB VPS에서 OOM 없이 1.5GB 이내로 안정적으로 운영할 수 있습니다."
  - question: "Prometheus 기본 설정 2GB VPS에서 OOM 나는 이유"
    answer: "Prometheus 기본 스크랩 간격 15초에 보존 기간 15일 기본값이 적용되면, 타깃 하나당 하루 720만 개 샘플이 쌓이면서 WAL 메모리 캐시가 선형으로 증가합니다. 여기에 Docker Compose에서 mem_limit을 지정하지 않으면 컨테이너가 OS 메모리를 무제한으로 점유하다 커널 OOM Killer가 발동해요. 결국 애플리케이션 레벨과 컨테이너 레벨 두 곳 모두 제한을 걸어야 합니다."
  - question: "Grafana image renderer 메모리 많이 먹는 이유 끄는 방법"
    answer: "grafana-image-renderer 플러그인은 Chromium 기반으로 동작해 단독으로 300~500MB 메모리를 점유합니다. Docker Compose 환경변수에서 GF_INSTALL_PLUGINS 값을 비워두면 렌더러 플러그인 로딩을 막을 수 있어요. 저사양 VPS 환경에서는 이미지 렌더링 기능을 포기하는 대신 GF_DATABASE_WAL=true와 GF_SERVER_ENABLE_GZIP=true로 Grafana를 경량화하는 것이 안정적입니다."
  - question: "docker compose mem_limit deploy resources 차이 뭔가요"
    answer: "Docker Compose v3 스펙에서는 mem_limit 대신 deploy.resources.limits.memory 방식으로 메모리 상한을 지정합니다. docker compose up (v2 CLI) 명령어를 사용할 때 deploy.resources 설정이 정상 동작하며, reservations 값으로 최소 보장 메모리도 함께 설정할 수 있어요. 둘 다 지정하지 않으면 OOM Killer가 어떤 컨테이너를 먼저 종료할지 예측이 불가능해집니다."
  - question: "Prometheus tsdb wal-compression 옵션 효과 있나요"
    answer: "--storage.tsdb.wal-compression은 Prometheus 2.11 버전 이후 지원되는 옵션으로, WAL 파일 크기를 평균 35~50% 줄여줍니다. Prometheus Grafana Docker Compose VPS 메모리 2GB 이하 OOM 없이 안정화 설정을 구성할 때 retention.time, retention.size와 함께 이 플래그를 추가하면 메모리와 디스크 사용량을 동시에 절감할 수 있어요. 설정 변경 후 수 시간 내에 메모리 점유 감소 효과를 확인할 수 있습니다."
---

월 5달러짜리 VPS에 모니터링 스택 올렸다가 새벽 3시에 OOM Killer 알림 받아본 적 있나요? Prometheus와 Grafana를 Docker Compose로 구성하면 편리하지만, 메모리 2GB 이하 환경에서 기본 설정 그대로 두면 며칠 안에 서버가 뻗어요. DigitalOcean, Hetzner, Vultr 같은 곳의 2GB 인스턴스가 월 4~6달러까지 내려오면서, 인디 개발자와 소규모 팀이 모니터링 스택을 직접 운영하다 OOM을 겪었다는 사례가 Reddit r/selfhosted와 GitHub Issues에서 눈에 띄게 늘었거든요.

> **핵심 요약**
> - Prometheus 기본 스크랩 간격(15초)을 그대로 두면 2GB VPS에서 수 시간 내 메모리 1GB 이상을 점유해요.
> - `--storage.tsdb.retention.time=7d`와 `--storage.tsdb.retention.size=400MB` 두 플래그만 추가해도 Prometheus 메모리 사용량이 평균 40~60% 줄어들어요.
> - Grafana 이미지 렌더러 플러그인은 Chromium 기반이라 혼자 400MB 이상 잡아먹어요. 꺼야 해요.
> - Docker Compose에서 `mem_limit`를 명시하지 않으면 OOM Killer가 어떤 컨테이너를 죽일지 예측이 안 돼요.
> - 안정적인 구성: Prometheus 600MB + Grafana 200MB + Node Exporter 30MB → 시스템 여유분 포함해도 1.5GB 안에 들어와요.

---

## 기본 설정이 저사양 VPS에서 터지는 이유

Prometheus는 원래 데이터센터 수준 서버를 전제로 설계됐어요. CNCF 문서 기준, 기본 스크랩 간격 15초에 메트릭 500개짜리 타깃 하나만 붙어도 하루 720만 개 샘플이 쌓여요. 15일 보존 기간 기본값이면 디스크뿐 아니라 WAL(Write-Ahead Log) 메모리 캐시도 선형으로 늘어나죠.

Grafana도 마찬가지예요. 기본 SQLite 설정에 플러그인 자동 로딩이 켜져 있으면 부팅할 때마다 메모리 사용량이 들쭉날쭉해요. 특히 `grafana-image-renderer`는 Chromium 기반이라 혼자 300~500MB를 써요.

문제는 두 층위에서 동시에 발생해요.

- **컨테이너 레벨**: 메모리 상한 없이 뜨는 컨테이너가 OS 메모리를 뺏어가다 커널이 OOM Killer를 발동
- **애플리케이션 레벨**: Prometheus TSDB가 보존 기간·크기 제한 없이 캐시를 계속 키움

이 두 가지를 동시에 잡아야 해요.

---

## 핵심 설정 세 가지

### Prometheus: 보존 기간과 WAL 압축이 전부예요

`prometheus.yml`에서 스크랩 간격을 30초로 늘리는 것부터 시작해요. 15초와 30초 차이가 작아 보이지만, 하루 샘플 수로 따지면 정확히 절반이에요.

```yaml
global:
  scrape_interval: 30s
  evaluation_interval: 30s
```

그리고 Docker Compose의 Prometheus 서비스 커맨드에 이 세 줄을 추가해요.

```yaml
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.path=/prometheus'
  - '--storage.tsdb.retention.time=7d'
  - '--storage.tsdb.retention.size=400MB'
  - '--storage.tsdb.wal-compression'
```

`--storage.tsdb.wal-compression`은 Prometheus 2.11 이후 지원하는 옵션으로, WAL 파일 크기를 평균 35~50% 줄여줘요. 이 세 가지만 바꿔도 메모리 점유가 눈에 띄게 달라져요.

### Grafana: 플러그인과 연결 수 제한

Grafana는 환경변수 몇 개로 꽤 많이 가벼워져요.

```yaml
environment:
  - GF_INSTALL_PLUGINS=         # 렌더러 플러그인 제거
  - GF_DATABASE_WAL=true
  - GF_SERVER_ENABLE_GZIP=true
  - GF_ANALYTICS_REPORTING_ENABLED=false
  - GF_USERS_DEFAULT_THEME=light
```

`GF_DATABASE_WAL=true`는 SQLite WAL 모드를 켜서 동시 쓰기 충돌을 줄여줘요. 대시보드를 여러 명이 동시에 열지 않는 개인·소규모 환경이라면 SQLite로 충분하고, 이때 WAL 모드가 안정성을 잡아줘요.

### Docker Compose: mem_limit 명시가 필수예요

가장 많이 놓치는 부분이에요. `mem_limit` 없이 컨테이너를 올리면 어떤 프로세스가 먼저 죽을지 OS에게 완전히 위임하는 셈이에요.

```yaml
services:
  prometheus:
    deploy:
      resources:
        limits:
          memory: 600M
        reservations:
          memory: 256M

  grafana:
    deploy:
      resources:
        limits:
          memory: 200M
        reservations:
          memory: 128M

  node-exporter:
    deploy:
      resources:
        limits:
          memory: 50M
```

`deploy.resources`는 Docker Compose v3 스펙이에요. `docker compose up` (v2 CLI)에서 정상 동작해요.

---

### 설정 옵션 비교: 어떤 조합이 맞을까요

| 구성 | 메모리 예상 사용 | 스크랩 간격 | 데이터 보존 | 적합한 환경 |
|------|-------------|----------|-----------|-----------|
| 기본 설정 (아무것도 안 건드림) | 1.2~1.8GB | 15초 | 15일 | 4GB+ 서버 |
| 보존 기간만 줄임 (7d) | 900MB~1.2GB | 15초 | 7일 | 3GB 서버 |
| 간격 + 보존 + WAL 압축 | 500~750MB | 30초 | 7일/400MB | 2GB VPS ✅ |
| 최소화 (60초 간격, 3d 보존) | 300~450MB | 60초 | 3일 | 1GB VPS |

2GB VPS에서 실용적인 타협점은 세 번째 행이에요. 30초 간격도 인프라 이상 탐지에 충분하고, 7일 보존이면 주간 트렌드도 볼 수 있어요.

---

## 설정 바꾼 뒤 안정화 확인하는 법

설정을 바꿨다고 끝이 아니에요. 컨테이너를 올린 뒤 아래 방법으로 확인해야 해요.

**시나리오 1: 컨테이너가 OOM으로 종료됐는데 이유를 모르겠어요**

```bash
docker inspect prometheus | grep -i oom
# OOMKilled: true 뜨면 메모리 한도 초과
```

`docker stats --no-stream`으로 현재 메모리 점유를 보고, mem_limit을 현재 사용량의 1.3~1.5배 수준으로 재조정해요.

**시나리오 2: Prometheus는 살아있는데 Grafana가 쿼리 타임아웃을 내요**

메모리 문제가 아니라 쿼리 범위 문제일 때가 많아요. Grafana 대시보드 기본 시간 범위가 `Last 6 hours`인데, Node Exporter 메트릭 카디널리티가 높으면 Prometheus가 응답을 늦게 줘요. 대시보드 기본 범위를 `Last 1 hour`로 바꾸면 훨씬 빨라져요.

**시나리오 3: VPS 재부팅했더니 데이터가 날아갔어요**

Docker Compose에서 볼륨을 named volume으로 명시하지 않으면 컨테이너 재생성 시 데이터가 사라져요.

```yaml
volumes:
  prometheus_data:
  grafana_data:

services:
  prometheus:
    volumes:
      - prometheus_data:/prometheus
  grafana:
    volumes:
      - grafana_data:/var/lib/grafana
```

---

## 앞으로 어떻게 될까요

- **Prometheus 3.x**의 native histograms가 기본화되면 카디널리티 대비 메모리 효율이 더 좋아질 거예요. Prometheus 팀은 2026년 중반 안정화를 목표로 작업 중이에요.
- **VictoriaMetrics**나 **Thanos Sidecar** 없이 단일 Prometheus로 버티는 설정이 2GB 이하에서는 여전히 현실적인 선택지예요. 분산 스택을 올리는 순간 메모리 요구량이 두 배 이상 뛰거든요.
- **Grafana Alloy**(구 Grafana Agent)가 Node Exporter를 대체하는 방향으로 생태계가 움직이고 있는데, 2GB 환경에서 Alloy를 쓸 이유는 아직 크지 않아요.

결론은 단순해요. 설정 파일 세 군데, 총 여섯 줄 바꾸면 2GB VPS에서 Prometheus + Grafana를 OOM 없이 돌릴 수 있어요. 스크랩 간격 30초, 보존 기간 7일, WAL 압축, mem_limit 명시. 이게 전부예요.

지금 운영 중인 VPS에서 `docker stats`를 한번 실행해보세요. Prometheus가 이미 700MB를 넘겼다면, 오늘 밤이 고비일 수 있거든요.

## 참고자료

1. [Prometheus with Docker Compose: The Complete Setup Guide | Last9](https://last9.io/blog/prometheus-with-docker-compose/)
2. [Prometheus with Docker Compose: Guide & Examples](https://spacelift.io/blog/prometheus-docker-compose)
3. [서버 모니터링 시스템 Docker 로 구성하기(Grafana, Prometheus, Loki, Promtail, Springboot) — Railly`s IT 정리노트](https://railly-linker.tistory.com/entry/%EC%84%9C%EB%B2%84-%EB%AA%A8%EB%8B%88%ED%84%B0%EB%A7%81-%EC%8B%9C%EC%8A%A4%ED%85%9C-Docker-%EB%A1%9C-%EA%B5%AC%EC%84%B1%ED%95%98%EA%B8%B0Grafana-Prometheus-Loki-Promtail)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
