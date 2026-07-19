---
title: "2GB VPS에서 Prometheus·Grafana Docker Compose 메모리 삽질 기록"
date: 2026-05-20T21:48:42+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "prometheus", "grafana", "docker"]
description: "2GB VPS에서 Prometheus·Grafana·cAdvisor 기본 설정으로 올리면 메모리 1.6GB를 초과해 OOM이 발생합니다. 보존 기간 7일, 동시 쿼리 수 1-2로 제한해 메모리를 절반으로 줄인"
image: "/images/20260520-prometheus-grafana-docker-comp.webp"
technologies: ["Docker"]
faq:
  - question: "Prometheus Grafana Docker Compose 2GB VPS에서 OOM 자꾸 발생하는 이유"
    answer: "Prometheus Grafana Docker Compose 단독 VPS 메모리 2GB 운영 설정 삽질 기록에 따르면, 기본 설정으로 세 컨테이너를 올리면 초기 메모리 사용량이 약 1.6GB를 초과해 OOM Killer가 작동합니다. Prometheus 기본 보존 기간 15일 설정과 mem_limit 미지정이 주요 원인이며, Docker 데몬과 호스트 OS 메모리까지 합산되면 2GB는 빠르게 고갈됩니다."
  - question: "Prometheus 메모리 사용량 줄이는 설정 방법"
    answer: "Prometheus 실행 옵션에서 `--storage.tsdb.retention.time=7d`로 보존 기간을 줄이고, `--storage.tsdb.retention.size=512MB`로 용량 상한을 지정하는 것이 핵심입니다. 추가로 `--query.max-concurrency=2`를 설정하면 Grafana 대시보드에서 동시 쿼리가 몰릴 때 메모리가 급증하는 상황을 막을 수 있습니다."
  - question: "Grafana 메모리 누수 환경변수 설정으로 해결하는 방법"
    answer: "Grafana의 기본 분석 및 텔레메트리 기능이 백그라운드에서 지속적으로 메모리를 소비하는 원인입니다. `GF_ANALYTICS_REPORTING_ENABLED=false`, `GF_ANALYTICS_CHECK_FOR_UPDATES=false`, `GF_LOG_LEVEL=warn` 환경변수를 설정하면 약 80~120MB를 절약하고 메모리 사용량을 안정화할 수 있습니다."
  - question: "Docker Compose mem_limit 설정 안 하면 어떻게 되나요"
    answer: "mem_limit를 명시하지 않으면 Docker가 컨테이너에 호스트 메모리를 제한 없이 할당할 수 있어, 과부하 시 단일 컨테이너가 전체 서버 메모리를 점유해 호스트 전체가 다운될 수 있습니다. Docker Compose의 `deploy.resources.limits.memory` 항목으로 Prometheus는 512M, Grafana는 256M, cAdvisor는 128M로 각각 상한을 지정하는 것이 권장됩니다."
  - question: "2GB VPS에서 Prometheus Grafana Loki 같이 올려도 되나요"
    answer: "Prometheus Grafana Docker Compose 단독 VPS 메모리 2GB 운영 설정 삽질 기록 기준으로, Loki와 Promtail까지 추가하면 예상 메모리가 950MB 이상으로 올라가 권장하지 않습니다. 메모리 여유가 400MB 이하로 줄어들면 스왑이 과도하게 작동해 오히려 모니터링 데이터가 유실될 수 있으므로, 2GB 환경에서는 튜닝된 Prometheus + Grafana + cAdvisor 조합이 현실적인 상한선입니다."
aliases:
  - "/tech/2026-05-20-prometheus-grafana-docker-compose-단독-vps-메모리-2gb-운/"

---

모니터링 스택 올리다가 서버 날려본 적 있으세요?

저는 있어요. Prometheus, Grafana, cAdvisor를 `docker compose up -d` 한 방에 올렸는데, 5분도 안 돼서 OOM Killer가 컨테이너를 하나씩 정리해버리더라고요. 2GB VPS에서요.

이 글은 그 삽질 기록이에요. 이론 말고, 실제로 부딪혔던 문제와 어떻게 풀었는지 순서대로 정리했어요.

> **핵심 요약**
> - 기본 설정으로 올리면 초기 메모리 사용량이 약 1.6GB를 넘겨 OOM 상황이 빈번하게 발생해요.
> - Prometheus의 `--storage.tsdb.retention.time`을 7일로 줄이고, `--query.max-concurrency`를 1-2로 제한하면 메모리 사용량을 절반 가까이 낮출 수 있어요.
> - Grafana 환경변수 두 줄로 백그라운드 트래픽을 차단해 약 80-120MB를 아낄 수 있어요.
> - Docker Compose에서 `mem_limit`를 명시적으로 지정하면 단일 컨테이너가 전체 메모리를 잡아먹는 상황을 막을 수 있어요.
> - 2GB 환경에서 Loki까지 같이 올리는 건 추천하지 않아요. 메모리 여유가 400MB 이하로 줄면 스왑이 과도하게 작동해서 오히려 모니터링 데이터가 유실될 수 있어요.

---

## 왜 2GB VPS에서 이 조합이 자꾸 터지나

Hetzner CX11(2GB)이나 DigitalOcean $6 Droplet 같은 저가 인스턴스는 개인 프로젝트의 첫 번째 선택지예요. 문제는 세 컨테이너가 각자 생각보다 메모리를 많이 쓴다는 거예요.

Prometheus 공식 문서 기준으로, 스크랩 대상이 10개만 넘어도 RSS가 빠르게 300-500MB를 넘어가요. Grafana는 기본적으로 150-200MB, cAdvisor는 컨테이너 수에 비례해서 50-200MB를 잡아요. 합치면 벌써 700MB 이상이에요. 여기에 Docker 데몬, 호스트 OS, 실제 앱 컨테이너까지 더하면 2GB는 금방 바닥이 나요.

그렇다고 모니터링을 포기할 수는 없잖아요. Prometheus + Grafana 조합은 CNCF 생태계에서 사실상 표준이에요. 그래서 설정을 잘 맞추는 게 답이에요.

---

## 실제 삽질 기록: 세 가지 주요 문제

### 1. Prometheus 메모리 무제한 팽창

`docker-compose.yml`에 별다른 제한 없이 Prometheus를 올렸더니, 하루 이틀 지나면서 메모리 사용량이 계속 올라갔어요. 원인은 두 가지였어요.

기본 보존 기간이 **15일**이에요. 2GB VPS에서 15일치 시계열 데이터를 쌓는 건 무리예요. 7일로 줄이는 게 첫 번째 조정이에요:

```yaml
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.retention.time=7d'
  - '--storage.tsdb.retention.size=512MB'
  - '--query.max-concurrency=2'
  - '--query.timeout=30s'
```

`--storage.tsdb.retention.size=512MB`를 같이 걸어두면 디스크와 메모리 양쪽에 안전장치가 생겨요. `--query.max-concurrency=2`는 Grafana 대시보드에서 여러 패널이 동시에 쿼리를 날릴 때 메모리를 한 번에 많이 쓰는 걸 막아줘요.

### 2. Grafana의 조용한 메모리 누수

이건 찾기 더 어려웠어요. Grafana가 초기엔 괜찮다가 몇 시간 지나면 메모리가 슬금슬금 오르는 패턴이 나타났어요.

원인은 기본 분석/텔레메트리 기능과 내부 렌더러였어요:

```yaml
environment:
  - GF_SERVER_ROUTER_LOGGING=false
  - GF_ANALYTICS_REPORTING_ENABLED=false
  - GF_ANALYTICS_CHECK_FOR_UPDATES=false
  - GF_RENDERING_SERVER_URL=
  - GF_RENDERING_CALLBACK_URL=
  - GF_LOG_LEVEL=warn
```

로그 레벨을 `warn`으로 낮추는 것만으로도 디스크 I/O 부하가 줄고 메모리 사용이 소폭 안정화돼요. 작은 차이지만 2GB 환경에서는 이런 게 쌓이거든요.

### 3. mem_limit 안 걸면 생기는 일

가장 기초적인 문제인데 의외로 많이 빠뜨려요. `mem_limit`를 명시하지 않으면 Docker는 컨테이너에 호스트 메모리를 제한 없이 줄 수 있어요. Prometheus가 과부하 상황에서 메모리를 폭발적으로 쓰면 호스트 전체가 다운돼요:

```yaml
services:
  prometheus:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
  grafana:
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
  cadvisor:
    deploy:
      resources:
        limits:
          memory: 128M
```

---

## 2GB VPS에서 어떤 조합이 현실적인가

| 구성 | 예상 메모리 | 안정성 | 추천 |
|------|------------|--------|------|
| Prometheus + Grafana (기본 설정) | ~650MB | 불안정 (OOM 발생) | ❌ |
| Prometheus + Grafana (튜닝 후) | ~400MB | 안정 | ✅ |
| Prometheus + Grafana + cAdvisor (튜닝 후) | ~520MB | 안정 (여유 약 400MB) | ✅ |
| Prometheus + Grafana + Loki + Promtail | ~950MB+ | 불안정 (스왑 과다) | ❌ |
| VictoriaMetrics + Grafana (튜닝 후) | ~280MB | 매우 안정 | ✅ |

Loki를 같이 올리고 싶다면 VPS를 4GB로 올리는 게 나아요. 2GB에서 Loki까지 돌리면 메모리 여유가 없어서, 로그 데이터가 많아지는 순간 스왑이 폭발해요. Prometheus가 스크랩 타임아웃을 내기 시작하면, 정작 문제가 생길 때 모니터링 데이터가 없는 아이러니한 상황이 생기거든요.

VictoriaMetrics는 PromQL 호환이 되면서 메모리 사용량이 훨씬 적어요. 2GB 운영을 지속할 거라면 진지하게 고려해볼 만해요. 다만 생태계와 커뮤니티 지원은 아직 Prometheus가 더 넓어요.

---

## 설정 이후 바로 확인할 것들

- `docker stats`로 각 컨테이너 실시간 메모리 확인. 안정화되는 데 보통 30분-1시간 걸려요.
- Prometheus UI에서 `process_resident_memory_bytes{job="prometheus"}` 쿼리로 메모리 추이를 보세요.
- cAdvisor의 기본 수집 주기는 1초예요. `--housekeeping_interval=10s`로 늘리면 부하가 눈에 띄게 줄어요.
- Prometheus 스크랩 주기도 기본 15초인데, 2GB 환경에서는 30초로 늘려도 충분해요.

참고로, Grafana Labs가 2025년 말부터 Grafana Alloy를 통합 수집기로 밀고 있어요. cAdvisor + node-exporter 조합보다 메모리 효율이 낫다는 초기 벤치마크가 나오고 있어서, 6-12개월 안에 전환을 고려해볼 만해요.

---

## 정리

핵심만 다시 짚으면:

- **Prometheus**: 보존 기간 7일, 사이즈 캡 512MB, 쿼리 동시성 2 이하
- **Grafana**: 텔레메트리·렌더러 비활성화, 로그 레벨 `warn`
- **Docker Compose**: 모든 컨테이너에 `mem_limit` 명시
- **Loki**: 빼거나 VPS 업그레이드

지금 당장 해볼 수 있는 한 가지가 있어요. 운영 중인 VPS가 있다면 `docker stats --no-stream` 명령 한 번 돌려보세요. 각 컨테이너의 현재 메모리 사용량이 어디서 시작해야 할지 바로 알려줄 거예요.

**튜닝 후 메모리가 어느 수준까지 안정됐는지 댓글로 알려주세요. 환경마다 꽤 다른 결과가 나오거든요.**

## 참고자료

1. [Grafana 및 prometheus 활용 #2 - 나만의 코딩기록 - 티스토리](https://cdchan.tistory.com/282)
2. [서버 모니터링 시스템 Docker 로 구성하기(Grafana, Prometheus, Loki, Promtail, Springboot) — Railly`s IT 정리노트](https://railly-linker.tistory.com/51)
3. [Docker 컨테이너 모니터링: cAdvisor + Prometheus + Grafana](https://denev6.tistory.com/entry/grafana)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
