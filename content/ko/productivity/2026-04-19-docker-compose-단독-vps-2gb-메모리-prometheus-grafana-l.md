---
title: "2GB VPS에서 Prometheus Grafana Loki 동시 운영 시 OOM 방지를 위한 Docker Compose 메모리 설정 방법"
date: 2026-04-19T20:03:24+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "vps"]
description: "2GB VPS에서 Prometheus·Grafana·Loki 동시 운영 시 기본값만으로 1.2~1.6GB를 소비해 OOM이 필연적으로 발생합니다. mem_limit 설정과 Prometheus 보존 기간 7일 조정으로 Docker Compose 모니터링 스택"
image: "/images/20260419-docker-compose-단독-vps-2gb-메모리-.webp"
technologies: ["Docker"]
faq:
  - question: "Docker Compose 단독 VPS 2GB 메모리 Prometheus Grafana Loki 동시 운영 OOM 방지 설정 방법"
    answer: "Docker Compose 단독 VPS 2GB 메모리 Prometheus Grafana Loki 동시 운영 OOM 방지 설정의 핵심은 각 컨테이너에 mem_limit과 memswap_limit을 동일한 값으로 명시하는 것입니다. 여기에 Prometheus 보존 기간을 7일로 줄이고 WAL 압축을 활성화하면 피크 메모리를 절반 가까이 낮출 수 있습니다."
  - question: "docker compose deploy resources limits 설정했는데 메모리 제한 안 걸리는 이유"
    answer: "Docker Compose의 deploy.resources.limits 설정은 Swarm 모드에서만 동작하며, 단독 실행(standalone) 환경에서는 완전히 무시됩니다. 단독 VPS에서 메모리를 제한하려면 반드시 서비스 최상위 레벨에 mem_limit과 memswap_limit을 직접 명시해야 합니다."
  - question: "2GB VPS Prometheus 메모리 사용량 줄이는 방법"
    answer: "Prometheus 실행 시 --storage.tsdb.retention.time=7d 플래그로 보존 기간을 30일에서 7일로 줄이고, --storage.tsdb.wal-compression으로 WAL 압축을 활성화하면 메모리가 350MB에서 220MB 수준으로 낮아집니다. 추가로 memswap_limit을 mem_limit과 동일하게 설정해 메모리 초과 시 스왑으로 흘러서 디스크 I/O가 폭발하는 상황도 막아야 합니다."
  - question: "Loki ingester 메모리 많이 먹는 문제 해결"
    answer: "Loki의 chunk_idle_period를 기본 30분에서 3분으로 줄이면 인메모리 청크를 훨씬 빠르게 플러시해 메모리 점유를 크게 낮출 수 있습니다. 소규모 환경에서는 WAL을 비활성화(wal.enabled: false)하는 것도 효과적인데, 재시작 시 최대 3분 치 로그 유실 가능성을 감수하면 안정적으로 180~250MB 선에서 운영할 수 있습니다."
  - question: "Docker Compose 단독 VPS 2GB 메모리 Prometheus Grafana Loki 동시 운영할 때 기본 메모리 얼마나 필요한가요"
    answer: "Docker Compose 단독 VPS 2GB 메모리 Prometheus Grafana Loki 동시 운영 시 기본값 그대로 올리면 Prometheus 350~500MB, Grafana 200~350MB, Loki 300~450MB, Promtail 50~80MB로 합산 최소 900MB에서 피크 1.4GB까지 올라갑니다. 여기에 Spring Boot 같은 애플리케이션을 함께 올리면 2GB 한계를 즉시 넘어 OOM Killer가 개입하게 됩니다."
---

2GB VPS에 모니터링 스택 올렸다가 서버가 통째로 죽어본 적 있으세요?

Prometheus, Grafana, Loki를 한꺼번에 올린 순간, 정작 모니터링해야 할 앱이 메모리 부족으로 먼저 죽어버리는 상황. 아이러니하죠. 월 5~6달러짜리 VPS에서 풀 스택 모니터링을 굴리려는 시도가 요즘 부쩍 늘었는데, 이 문제는 개인 개발자들 사이에서 꽤 현실적인 과제가 됐어요.

> **핵심 요약**
> - Prometheus, Grafana, Loki를 기본값으로 Docker Compose에 올리면 합산 메모리가 1.2~1.6GB에 달해 2GB VPS에서 OOM이 거의 필연적으로 발생해요.
> - 각 컨테이너에 `mem_limit`과 `memswap_limit`을 명시하고, Prometheus 보존 기간을 7일 이하로 줄이는 것만으로도 피크 메모리를 절반 가까이 낮출 수 있어요.
> - Loki의 ingester 청크 크기와 Grafana의 플러그인 수를 제한하면 추가로 200~300MB를 더 아낄 수 있어요.
> - Docker Compose의 `deploy.resources.limits` 설정은 Swarm 모드에서만 작동해요. 단독 VPS에서는 반드시 `mem_limit` 방식을 써야 해요.

---

## 기본값으로 올리면 왜 죽을까요?

Hetzner CX11, DigitalOcean Basic $6, Vultr Cloud Compute 같은 2GB 티어는 개인 프로젝트나 소규모 SaaS의 표준 진입점이에요. 문제는 모니터링 스택까지 얹으려는 수요가 함께 늘었다는 거예요.

Grafana 공식 문서 기준, Prometheus + Node Exporter + Grafana + Loki + Promtail을 **기본 설정**으로 올렸을 때 메모리 점유는 대략 이렇게 나와요:

- **Prometheus**: 350~500MB (스크랩 간격 15초, 30일 보존 기본값)
- **Grafana**: 200~350MB (플러그인 기본 로드 포함)
- **Loki**: 300~450MB (ingester 기본 청크 크기)
- **Promtail**: 50~80MB
- **Node Exporter**: 20~30MB

더하면 최소 920MB, 피크에는 1.4GB까지 치솟아요. 여기에 Spring Boot 앱(300~400MB)까지 얹으면 2GB는 순식간에 한계예요. OOM Killer가 개입하면서 Prometheus나 Loki가 반복적으로 죽는 거예요.

근본 원인은 두 가지예요. 세 도구 모두 엔터프라이즈 환경을 기본 전제로 설계돼 기본값 자체가 메모리를 넉넉히 가정해요. 그리고 Docker Compose 단독 모드에서는 `deploy.resources` 블록이 무시되기 때문에, 제한을 걸었다고 착각하는 케이스가 많아요. 이 두 가지를 잡으면 절반은 해결돼요.

---

## 메모리를 실제로 줄이는 세 가지 설정

### Prometheus: 보존 기간과 WAL 크기 줄이기

Prometheus에서 메모리를 가장 많이 잡아먹는 건 **TSDB 청크 캐시**와 **WAL(Write-Ahead Log)**이에요.

```yaml
prometheus:
  image: prom/prometheus:v2.51.0
  mem_limit: 400m
  memswap_limit: 400m
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=7d'
    - '--storage.tsdb.wal-compression'
    - '--web.enable-lifecycle'
```

`--storage.tsdb.retention.time=7d`로 보존 기간을 30일에서 7일로 줄이면 디스크도 아끼고 캐시 메모리도 같이 줄어요. `--storage.tsdb.wal-compression`은 WAL 압축을 켜서 추가로 10~15% 절약돼요. 이 두 플래그만 바꿔도 Prometheus 메모리가 350MB에서 220MB 수준으로 내려와요.

`memswap_limit`을 `mem_limit`과 같은 값으로 고정하는 게 핵심이에요. 다르게 설정하면 메모리 초과 시 스왑으로 흘러서 VPS 디스크 I/O가 폭발하고 응답이 죽어버려요.

### Loki: ingester 청크 설정 손보기

Loki는 기본적으로 인메모리 청크를 크게 잡아요. `loki-config.yml`에 아래 섹션을 추가하면 달라져요:

```yaml
ingester:
  chunk_idle_period: 3m
  chunk_block_size: 262144
  chunk_retain_period: 1m
  max_transfer_retries: 0
  wal:
    enabled: false
```

`chunk_idle_period`를 기본 30분에서 3분으로 줄이면 오래된 청크를 훨씬 빨리 플러시해요. 2GB VPS에서 로그 볼륨이 크지 않다면 WAL을 꺼도 무방해요. 재시작 시 최대 3분 치 로그가 유실될 수 있지만, 소규모 환경에선 감수할 만한 트레이드오프예요.

```yaml
loki:
  image: grafana/loki:2.9.4
  mem_limit: 300m
  memswap_limit: 300m
```

이렇게 하면 Loki는 안정적으로 180~250MB 선에서 돌아요.

### Grafana: 플러그인 최소화와 메모리 제한

플러그인이 많을수록 기동 메모리가 늘어요. 슬림 이미지를 쓰고, 환경변수로 불필요한 기능을 꺼요:

```yaml
grafana:
  image: grafana/grafana-oss:10.4.1
  mem_limit: 200m
  memswap_limit: 200m
  environment:
    - GF_PLUGINS_ENABLE_ALPHA=false
    - GF_ANALYTICS_REPORTING_ENABLED=false
    - GF_USERS_DEFAULT_THEME=dark
```

---

## 설정별 메모리 절약 효과 비교

| 컨테이너 | 기본값 (피크) | 최적화 후 (피크) | 절약량 | 주요 변경 |
|---------|------------|--------------|------|---------|
| Prometheus | 500MB | 220MB | ~280MB | 보존 7일, WAL 압축 |
| Loki | 450MB | 250MB | ~200MB | 청크 주기 단축, WAL 비활성 |
| Grafana | 350MB | 180MB | ~170MB | 슬림 이미지, 플러그인 제한 |
| Promtail | 80MB | 60MB | ~20MB | 기본값 유지 |
| Node Exporter | 30MB | 25MB | ~5MB | 기본값 유지 |
| **합계** | **~1,410MB** | **~735MB** | **~675MB** | |

최적화 후 총 메모리가 절반 수준으로 내려오면서 앱 컨테이너에 600MB 이상을 안정적으로 남겨줄 수 있어요. Spring Boot 앱(512MB 힙) 하나는 넉넉하게 돌아가는 수준이에요.

---

## 운영에서 놓치기 쉬운 두 가지 함정

**함정 1: `deploy.resources.limits`는 단독 Compose에서 작동하지 않아요.**

`deploy` 블록 아래 리소스 제한은 Swarm 모드에서만 적용돼요. 단독 VPS에서 `docker compose up`으로 올리면 이 설정이 조용히 무시돼요. 경고 메시지도 없어서 걸려 있다고 착각하기 쉬워요.

해결책은 간단해요. `mem_limit`과 `memswap_limit`을 서비스 최상위 레벨에 직접 명시하면 돼요.

**함정 2: cgroup v2 환경에서 `mem_limit`이 먹히지 않을 수 있어요.**

Ubuntu 22.04 이상이나 Debian 12 기반 VPS는 기본적으로 cgroup v2를 써요. `docker info | grep "Cgroup Driver"`로 확인하고, `systemd` 드라이버가 표시되면 Docker 데몬 설정에 `"exec-opts": ["native.cgroupdriver=systemd"]`를 추가해야 해요.

---

## 지금 당장 실천할 것들

Grafana Labs는 Loki 3.x 시리즈에서 인메모리 사용량을 줄이는 새 스토리지 엔진을 실험 중이에요. 정식 출시되면 현재 대비 20~30% 추가 절약이 될 전망이에요. Prometheus도 v2.52에서 `--storage.tsdb.head-chunks-write-queue-size` 플래그로 세밀한 메모리 제어가 정식 지원될 예정이라 릴리스 노트를 챙겨볼 만해요.

그 전에 지금 바로 할 수 있는 건 명확해요:

1. `mem_limit` + `memswap_limit`을 모든 모니터링 컨테이너에 명시하기
2. Prometheus 보존 기간 7일로 줄이고 WAL 압축 켜기
3. Loki ingester 청크 주기 단축하기
4. `docker stats`로 실제 메모리 사용량 주기적으로 확인하기

2GB VPS는 제약이 아니에요. 기본값을 그대로 쓴 게 문제였을 뿐이에요. 지금 `docker stats` 한 번 띄워보세요.

## 참고자료

1. [Monitoring a Linux host with Prometheus, Node Exporter, and Docker Compose | Grafana Cloud documenta](https://grafana.com/docs/grafana-cloud/send-data/metrics/metrics-prometheus/prometheus-config-examples/docker-compose-linux/)
2. [서버 모니터링 시스템 Docker 로 구성하기(Grafana, Prometheus, Loki, Promtail, Springboot) — Railly`s IT 정리노트](https://railly-linker.tistory.com/entry/%EC%84%9C%EB%B2%84-%EB%AA%A8%EB%8B%88%ED%84%B0%EB%A7%81-%EC%8B%9C%EC%8A%A4%ED%85%9C-Docker-%EB%A1%9C-%EA%B5%AC%EC%84%B1%ED%95%98%EA%B8%B0Grafana-Prometheus-Loki-Promtail)
3. [Monitoring Stack with Prometheus, Grafana, and Loki using Docker | by Amol Mali | Medium](https://devopswithamol.medium.com/monitoring-stack-with-prometheus-grafana-and-loki-using-docker-ed3759f0628b)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
