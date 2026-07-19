---
title: "Prometheus Grafana Docker Compose 2GB VPS 메모리 최적화 삽질 기록"
date: 2026-05-05T20:38:50+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "prometheus", "grafana", "docker"]
description: "2GB VPS에서 Prometheus·Grafana Docker Compose 운영 시 OOM Killer 방지법. retention 7일, max-block 설정으로 메모리 600MB 이상 절감한 실제 삽질 기록."
image: "/images/20260505-prometheus-grafana-docker-comp.webp"
technologies: ["Docker"]
faq:
  - question: "Prometheus Grafana Docker Compose 2GB VPS에서 OOM Killed 해결 방법"
    answer: "Prometheus Grafana Docker Compose 저사양 VPS 2GB 메모리 최적화 설정 삽질 기록에 따르면, '--storage.tsdb.retention.time=7d'와 '--query.max-concurrency=2' 플래그를 추가하고 deploy.resources.limits.memory를 512m으로 제한하면 메모리 사용량을 절반 가까이 줄일 수 있어요. 추가로 스왑 512MB를 설정해두면 OOM Killer가 개입하기 전 완충 역할을 해줘서 안정성이 높아져요."
  - question: "Grafana 메모리 사용량 줄이는 방법 저사양 서버"
    answer: "Prometheus Grafana Docker Compose 저사양 VPS 2GB 메모리 최적화 설정 삽질 기록 기준으로, GF_RENDERING_SERVER_URL을 비워서 이미지 렌더러를 비활성화하면 idle 메모리가 약 120–200MB 줄어들어요. GF_LOG_LEVEL=warn 설정도 함께 적용하면 디스크 I/O까지 같이 감소해요."
  - question: "Docker Compose cAdvisor Node Exporter 차이 2GB 메모리 환경"
    answer: "Node Exporter는 idle 상태에서 약 20MB만 사용하며 호스트 CPU, 메모리, 디스크, 네트워크를 모니터링할 수 있어요. cAdvisor는 컨테이너별 리소스 확인이 가능하지만 약 150MB를 상시 점유해서, 2GB VPS에서는 필요할 때만 docker compose up -d cadvisor로 올렸다가 확인 후 내리는 방식이 권장돼요."
  - question: "Prometheus storage.tsdb.retention.time 7d 15d 메모리 차이"
    answer: "기본값인 15d를 7d로 줄이면 TSDB 인덱스 크기와 디스크 I/O가 절반 수준으로 감소하고, 그에 따라 메모리 사용량도 눈에 띄게 줄어요. 2GB VPS에서 기본값 15d를 그대로 두면 Prometheus 단독으로 600–800MB를 차지해서 Grafana가 뜨는 순간 OOM이 발생하는 패턴이 반복돼요."
  - question: "Docker Compose 모니터링 스택 2GB RAM 실제 메모리 사용량"
    answer: "최적화 설정 기준으로 Prometheus 350–450MB, Grafana 180–220MB, Node Exporter 20–30MB, Docker 데몬과 커널 300–400MB로 총 850MB–1.1GB 수준이에요. 실제 서비스 컨테이너가 500MB를 추가로 사용해도 전체가 1.6GB 수준이라 스왑 없이도 운영 가능하지만, 보험용 스왑 512MB는 걸어두는 게 안전해요."
aliases:
  - "/tech/2026-05-05-prometheus-grafana-docker-compose-저사양-vps-2gb-메모리-/"

---

아침에 일어났더니 Grafana가 죽어있어요. Prometheus도 조용히 사라져 있고요. 로그 확인하면 딱 이 메시지예요. `OOM Killed`. 저도 세 번 겪었어요.

Docker Compose로 모니터링 스택 올리는 건 어렵지 않아요. 문제는 그게 *살아남게* 하는 거예요. Hetzner CX11 기준으로 월 3.29유로, 2GB RAM이 현실인 환경에서요.

> **핵심 요약**
> - 기본 설정 그대로 올린 Prometheus는 2GB 환경에서 혼자 600–800MB를 쓰고, Grafana가 200–300MB를 추가로 요구해 OOM Killer가 개입하는 게 일반적인 패턴이에요.
> - `--storage.tsdb.retention.time=7d`와 `--storage.tsdb.max-block-duration=2h` 조합으로 Prometheus 메모리를 절반 가까이 줄일 수 있어요.
> - Grafana의 렌더러를 비활성화하면 idle 상태 메모리가 약 120MB 줄어들어요.
> - Node Exporter는 가볍지만, cAdvisor를 함께 올리면 120–180MB가 추가로 필요해서 2GB 환경에선 신중하게 골라야 해요.

---

## 기본값이 왜 위험한가

### Prometheus 메모리 구조를 모르면 반복 삽질이에요

Prometheus는 스크레이핑한 데이터를 일단 메모리의 WAL(Write-Ahead Log)에 써요. 그리고 2시간 단위로 디스크의 TSDB 블록으로 플러시하죠. 이 과정에서 메모리를 꽤 넉넉하게 잡아둬요.

기본 보존 기간은 `15d`예요. Grafana Labs 공식 문서 기준으로 메모리 추정 공식은 이래요:

> **메모리(bytes) ≈ 활성 시계열 수 × 3,000**

타겟 10개에서 시계열이 2,000개라면 6MB처럼 보이지만, 실제론 WAL 오버헤드, 인덱스, 쿼리 캐시까지 더해서 400–600MB를 쉽게 넘어요. 2GB VPS에서 기본값 그대로 띄우면 OOM이 "언제 터지느냐"의 문제지, "터지느냐 아니냐"의 문제가 아니에요.

### 핵심 설정 세 가지

```yaml
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.retention.time=7d'
  - '--storage.tsdb.max-block-duration=2h'
  - '--query.max-concurrency=2'
```

- `retention.time=7d`: 15일 → 7일로 줄이면 디스크 I/O와 인덱스 크기가 절반이에요.
- `max-block-duration=2h`: 기본값이에요. 명시적으로 써두면 실수로 바꾸는 걸 막아줘요.
- `query.max-concurrency=2`: Grafana 대시보드에서 여러 패널이 동시에 쿼리를 날릴 때 메모리 스파이크를 막아줘요.

Docker Compose에서 메모리 제한도 같이 걸어두세요. 컨테이너가 OOM으로 죽어도 호스트 전체가 망가지지 않아요:

```yaml
deploy:
  resources:
    limits:
      memory: 512m
```

---

## Grafana는 생각보다 무거워요

### 플러그인과 렌더러가 주범이에요

Grafana 기본 이미지는 idle 상태에서 150–200MB를 써요. 여기에 PNG 렌더러(`grafana-image-renderer`)까지 붙으면 추가로 200MB예요. 알림에 스크린샷을 첨부하는 기능 때문인데, 저사양 환경에선 그냥 끄는 게 나아요.

```yaml
environment:
  - GF_RENDERING_SERVER_URL=
  - GF_LOG_LEVEL=warn
  - GF_ANALYTICS_REPORTING_ENABLED=false
  - GF_ALERTING_ENABLED=false
```

`GF_LOG_LEVEL=warn`은 디스크 I/O도 같이 줄여줘요. info 레벨 로그가 꽤 많거든요. 그리고 Grafana가 Prometheus에 쿼리를 날릴 때 응답이 늦으면 연결을 계속 물고 있어요. 저사양 환경에서 이게 쌓이면 Grafana가 느려지거나 재시작해요.

```ini
GF_DATAPROXY_TIMEOUT=30
GF_DATAPROXY_DIAL_TIMEOUT=10
```

---

## cAdvisor를 꼭 써야 하나요?

저사양 VPS에서 cAdvisor 필요 여부는 "뭘 보고 싶으냐"에 달려있어요.

| 항목 | Node Exporter | cAdvisor |
|---|---|---|
| 호스트 CPU/메모리 | ✅ | ❌ |
| 컨테이너별 리소스 | ❌ | ✅ |
| idle 메모리 사용 | ~20MB | ~150MB |
| 2GB VPS 권장 | ✅ | ⚠️ 신중히 |

cAdvisor는 강력하지만 2GB 환경에서 항상 켜두기엔 비용이 커요. 컨테이너별 메모리 사용량을 일시적으로 확인해야 할 때만 올리고, 평소엔 내리는 방식이 현실적이에요. `docker compose up -d cadvisor`와 `docker compose stop cadvisor`를 번갈아 쓰는 거죠.

Node Exporter만으로 호스트 메모리, CPU, 디스크, 네트워크를 충분히 볼 수 있어요. 컨테이너 수가 많지 않다면 필요한 정보의 80%는 Node Exporter로 해결돼요.

---

## 실제로 살아남는 구성

**예상 메모리 분포:**
- Prometheus: ~350–450MB (7일 보존, 타겟 5–8개 기준)
- Grafana: ~180–220MB (렌더러 없음)
- Node Exporter: ~20–30MB
- Docker 데몬 + 커널: ~300–400MB
- **합계: 약 850MB–1.1GB**

2GB에서 버퍼가 900MB–1.1GB 남아요. 실제 서비스 컨테이너가 500MB를 쓴다면 전체가 1.6GB 수준이에요. 스왑 없이도 버텨요. 그래도 스왑 512MB는 보험으로 걸어두세요. OOM Killer가 개입하기 전에 완충 역할을 해줘요.

```bash
fallocate -l 512M /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

## 상황별 대응

**아침에 Grafana가 죽어있어요**
Grafana에 `memory: 256m` 제한을 걸어두세요. 죽더라도 Prometheus는 살아있고, `restart: unless-stopped`가 Grafana를 다시 올려줘요. 원인은 보통 대시보드 로딩 시 과도한 쿼리 동시 실행이에요.

**Prometheus가 며칠 뒤 OOM으로 죽어요**
`prometheus_tsdb_head_series` 메트릭을 확인하세요. 5,000개를 넘으면 2GB에서 위험 신호예요. 타겟을 줄이거나 `scrape_interval`을 `15s → 30s`로 늘려보세요.

**서비스 컨테이너가 느려졌어요**
`docker stats`로 실시간 메모리를 확인하세요. 모니터링 스택이 메모리를 과하게 잡고 있다면 Prometheus의 `memory: 512m` 제한을 `400m`으로 내리고 재시작하세요. Prometheus는 제한 내에서 스스로 조절해요.

---

## 마치며

결국 핵심은 "기본값을 믿지 않는 것"이에요.

- Prometheus: `retention=7d`, `max-block-duration=2h`, 메모리 제한 512m
- Grafana: 렌더러 끄고, 로그 레벨 warn, 메모리 제한 256m
- cAdvisor: 필요할 때만 켜고 평소엔 꺼두기
- 스왑 512MB: 보험

이 네 가지만 지켜도 모니터링 스택이 서버 주인공이 되는 사태는 막을 수 있어요.

지금 VPS에서 `prometheus_process_resident_memory_bytes`를 조회하면 얼마가 나오나요? 생각보다 많이 나온다면, 오늘 설정을 다시 볼 때가 됐다는 신호예요.

## 참고자료

1. [Prometheus + Grafana Docker Compose - Ready to Deploy | Docker Recipes](https://docker.recipes/monitoring/prometheus-grafana)
2. [Prometheus with Docker Compose: The Complete Setup Guide | Last9](https://last9.io/blog/prometheus-with-docker-compose/)
3. [Monitoring a Linux host with Prometheus, Node Exporter, and Docker Compose | Grafana Cloud documenta](https://grafana.com/docs/grafana-cloud/send-data/metrics/metrics-prometheus/prometheus-config-examples/docker-compose-linux/)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
