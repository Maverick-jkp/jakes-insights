---
title: "2GB VPS에서 Prometheus·Grafana 올리면 OOM 나는 이유와 Docker Compose 해결법"
date: 2026-04-23T20:32:40+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "vps", "Node.js"]
description: "2GB VPS에서 Prometheus와 Grafana를 Docker Compose로 함께 실행하면 두 컨테이너가 기본 설정만으로도 1.2–1.5GB를 소비해 OOM Killer가 작동합니다. TSDB 인메모리 청크 문제와 메모리 제한 설정"
image: "/images/20260423-docker-compose-단독-vps-2gb-메모리-.webp"
technologies: ["Node.js", "Docker", "Go"]
faq:
  - question: "Docker Compose 단독 VPS 2GB 메모리 Prometheus Grafana 같이 띄우면 OOM 나는 이유"
    answer: "2GB VPS에서 Docker Compose 단독으로 Prometheus와 Grafana를 같이 띄우면 기본 설정 기준 두 컨테이너가 합산 약 1.2–1.5GB를 소비해 OOM이 거의 필연적으로 발생합니다. Prometheus는 TSDB 인메모리 청크 캐시로 400–700MB, Grafana는 플러그인 초기화로 250–400MB를 점유하는데, 여기에 앱 서버와 OS 메모리까지 합치면 피크 시 2,048MB를 초과하기 때문입니다. OOM Killer는 메모리를 많이 잡은 프로세스를 비즈니스 중요도와 무관하게 강제 종료하므로 앱이 죽고 Prometheus가 살아남는 상황도 발생합니다."
  - question: "VPS 2GB Prometheus 메모리 줄이는 방법"
    answer: "Prometheus의 메모리 급증은 TSDB 헤드 블록 인메모리 캐시 때문이므로, `--storage.tsdb.retention.time=7d`로 보관 기간을 줄이고 `--query.max-samples=500000`으로 PromQL 쿼리 샘플 수를 제한하면 RSS를 30–40% 줄일 수 있습니다. 추가로 `--storage.tsdb.wal-compression` 옵션을 활성화하면 디스크와 메모리를 동시에 절약할 수 있습니다. docker-compose.yml에 `mem_limit: 512m`을 함께 설정해 컨테이너 수준에서 상한을 강제하는 것도 필수입니다."
  - question: "Docker mem_limit 설정 안 하면 OOM Killer 동작 방식"
    answer: "docker-compose.yml에 `mem_limit`을 설정하지 않으면 컨테이너는 호스트 메모리를 제한 없이 사용할 수 있어, 커널이 한계를 감지할 때까지 컨테이너 수준에서 제어할 방법이 없습니다. 결국 호스트 커널의 OOM Killer가 `oom_score`가 높은 프로세스를 선택해 강제 종료하며, 이때 중요한 앱 컨테이너가 먼저 죽는 상황이 발생할 수 있습니다. `mem_limit`과 `memswap_limit`을 컨테이너별로 명시해야 OOM Killer 개입 전에 컨테이너 자체에서 메모리를 제어할 수 있습니다."
  - question: "Grafana 컨테이너 메모리 사용량 줄이기"
    answer: "Grafana는 기동 시 SQLite 메타데이터 처리와 플러그인 초기화로 기본 약 250–400MB를 점유하며, 대시보드 패널이 많을수록 백엔드 쿼리가 동시에 실행돼 피크 사용량이 500MB를 넘기도 합니다. 불필요한 플러그인을 비활성화하는 것만으로 초기 기동 메모리를 80–120MB 줄일 수 있으며, docker-compose.yml에 `mem_limit: 300m`을 설정해 상한을 강제하는 것이 권장됩니다. 2GB 환경에서는 컨테이너별 메모리 상한, 스크래핑 간격 조정, 스왑 설정을 묶어서 적용해야 안정적인 운영이 가능합니다."
  - question: "Docker memory cgroup 작동 안 할 때 확인 방법"
    answer: "`cat /proc/cgroups` 명령으로 `memory` 항목의 값이 `1`인지 확인하면 됩니다. 일부 경량 Linux 빌드에서는 memory cgroup이 기본 비활성화되어 있어 Docker의 `mem_limit` 설정이 아예 적용되지 않는 경우가 있습니다. VPS 환경이라도 이 확인은 기본 사항이며, cgroup이 비활성화된 경우 커널 부팅 파라미터에 `cgroup_enable=memory`를 추가해야 `mem_limit`이 정상 동작합니다."
aliases:
  - "/tech/2026-04-23-docker-compose-단독-vps-2gb-메모리-prometheus-grafana-같/"

---

2GB VPS에서 Docker Compose로 서비스를 올리다 갑자기 컨테이너가 통째로 죽는 경험, 분명 있을 거예요. 로그엔 `Killed`라는 한 단어만 남고. 범인은 OOM Killer — 커널이 메모리 한계를 넘어섰다고 판단해 프로세스를 강제 종료하는 리눅스의 최후 수단이에요. Prometheus와 Grafana를 모니터링 목적으로 추가하는 순간, 이 일이 유독 자주 벌어져요.

> **핵심 요약**
> - 2GB VPS에서 Docker Compose 단독으로 Prometheus + Grafana를 같이 띄우면 기본 설정 기준 두 컨테이너가 합산 약 1.2–1.5GB를 소비해 OOM이 거의 필연적으로 발생한다.
> - Prometheus의 메모리 급증은 TSDB(시계열 데이터베이스)의 인메모리 청크 캐시 때문이며, `--storage.tsdb.retention.time`과 `--query.max-samples` 조정만으로도 RSS를 30–40% 줄일 수 있다.
> - Grafana는 플러그인 로딩과 내부 SQLite 처리로 기본 약 250–400MB를 점유하며, 불필요한 플러그인 비활성화만으로 초기 기동 메모리를 80–120MB 줄일 수 있다.
> - Docker의 `mem_limit` 설정 없이 컨테이너를 올리면 호스트 커널 OOM Killer가 개입하기 전에 컨테이너 수준에서 제어할 방법이 없다.
> - 2GB 환경에서 안정적으로 운영하려면 컨테이너별 메모리 상한, Prometheus 스크래핑 간격 조정, 스왑 설정을 묶어서 적용해야 한다.

---

## Prometheus와 Grafana가 2GB를 얼마나 먹는가

숫자부터 봐요.

Prometheus는 공식 문서에서 "매 시리즈당 약 1–2 byte per sample"이라고 말하지만, 실제로는 TSDB 헤드 블록이 메모리에 상주해요. cAdvisor까지 붙으면 수집 대상이 수백 개 메트릭 시리즈로 늘어나고, 기본 스크래핑 간격 15초 + 15일 보관 설정으로 돌리면 RSS가 빠르게 400–700MB 구간으로 올라가요. 여기에 PromQL 쿼리가 들어오는 순간 메모리는 순간적으로 더 치솟아요.

Grafana는 기동 시 SQLite 메타데이터 처리와 플러그인 초기화로 약 250MB가 기본이에요. 대시보드 패널 수가 늘면 백엔드 쿼리가 동시에 터지면서 피크 사용량이 400MB를 넘어가는 일도 흔해요.

그러면 앱 자체는요? 일반적인 Node.js 또는 Go 애플리케이션이 100–200MB, nginx가 50MB 정도를 잡아먹는다고 치면 2GB 전체 계산이 이렇게 돼요:

| 컨테이너 | 기본 메모리 사용 (RSS 기준) | 피크 시 |
|---|---|---|
| Prometheus (기본 설정) | 400–700MB | 900MB+ |
| Grafana | 250–400MB | 500MB |
| 앱 서버 (Node.js/Go) | 100–200MB | 300MB |
| nginx / reverse proxy | 30–60MB | 80MB |
| OS + Docker daemon | 200–300MB | 350MB |
| **합계** | **980–1,660MB** | **2,130MB+** |

2GB = 2,048MB예요. 피크가 조금만 겹쳐도 넘어서요. OOM이 나는 게 당연한 거예요.

---

## OOM Killer가 개입하는 구조: 컨테이너와 커널의 관계

Docker 컨테이너는 기본적으로 cgroup으로 리소스를 분리해요. 그런데 `docker-compose.yml`에 `mem_limit`을 설정하지 않으면, 컨테이너는 호스트 메모리를 제한 없이 쓸 수 있어요. 각 컨테이너가 서로 얼마나 쓰는지 모르는 채로 메모리를 계속 요청하다가, 호스트 커널이 한계를 감지하면 OOM Killer가 `oom_score`가 높은 프로세스를 골라 죽이는 구조예요.

문제는 OOM Killer가 어느 컨테이너가 더 중요한지를 비즈니스 로직으로 판단하지 않는다는 거예요. 그냥 메모리를 많이 잡고 있는 걸 골라요. 앱이 죽고 Prometheus는 살아남는 어처구니없는 상황이 벌어지는 이유가 여기 있어요.

참고로 Raspberry Pi OS 같은 일부 64-bit lite 빌드에서는 memory cgroup 자체가 기본 비활성화되어 있어서 Docker의 `mem_limit`이 아예 작동 안 하는 경우도 있어요 (GitHub RPi-Distro/pi-gen issue #917 참고). VPS라도 커널 파라미터 확인은 기본이에요: `cat /proc/cgroups`로 `memory` 항목이 `1`인지 꼭 봐야 해요.

---

## 해결책: 세 가지를 같이 적용해야 효과가 있어요

### 1. Prometheus 메모리 상한 및 TSDB 튜닝

`docker-compose.yml`에 아래처럼 넣어요:

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    mem_limit: 512m
    memswap_limit: 768m
    command:
      - '--storage.tsdb.retention.time=7d'
      - '--storage.tsdb.wal-compression'
      - '--query.max-samples=500000'
      - '--storage.tsdb.min-block-duration=2h'
```

`retention.time`을 15일에서 7일로 줄이면 TSDB 헤드 블록 크기가 줄어요. `query.max-samples`를 제한하면 무거운 PromQL 쿼리가 메모리를 폭발적으로 늘리는 걸 막아줘요. WAL 압축은 디스크와 메모리를 동시에 아껴줘요. 이 세 가지만 조합해도 RSS 기준 30–40% 감소를 기대할 수 있어요.

### 2. Grafana 설정 경량화

```yaml
  grafana:
    image: grafana/grafana-oss:latest
    mem_limit: 300m
    memswap_limit: 450m
    environment:
      - GF_RENDERING_SERVER_URL=  # 렌더링 플러그인 비활성화
      - GF_ALERTING_ENABLED=false # 알람 엔진 끄기 (별도 필요 시 Alertmanager 사용)
      - GF_ANALYTICS_REPORTING_ENABLED=false
```

불필요한 플러그인을 끄는 것만으로도 초기 기동 메모리를 80–120MB 줄일 수 있어요.

### 3. 스왑 설정으로 안전망 확보

VPS가 스왑 없이 운영 중이라면 반드시 추가해야 해요:

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

스왑은 성능이 떨어지지만, OOM으로 컨테이너가 죽는 것보다는 훨씬 나아요. `memswap_limit`을 `mem_limit`의 1.5배 정도로 설정하면 스왑을 쓰되 무한정 쓰는 걸 막을 수 있어요.

---

## 2GB 환경 모니터링 스택 구성 선택지 비교

| 기준 | Prometheus + Grafana (기본) | Prometheus + Grafana (튜닝) | VictoriaMetrics + Grafana |
|---|---|---|---|
| 메모리 사용 | 650–1,100MB | 400–700MB | 200–400MB |
| 설정 난이도 | 낮음 | 중간 | 중간 |
| PromQL 호환 | 완전 | 완전 | MetricsQL (호환) |
| 장기 보관 적합성 | 보통 | 보통 | 높음 |
| 2GB VPS 적합도 | ❌ 위험 | ⚠️ 주의 필요 | ✅ 권장 |

메모리가 정말 빠듯하다면 VictoriaMetrics를 Prometheus 대신 쓰는 방법도 있어요. 동일 워크로드 기준 Prometheus 대비 RSS를 절반 이하로 유지하는 경우가 많아요. Grafana와 바로 연동되고 PromQL과 대부분 호환돼서 대시보드를 다시 만들 필요도 없어요.

---

## "모니터링 스택도 리소스다"

Docker Compose로 단독 VPS 2GB에 Prometheus + Grafana를 그냥 올리면 OOM은 시간 문제예요. 원인은 세 가지예요 — Prometheus TSDB 인메모리 캐시, Grafana 플러그인 초기화 비용, 그리고 컨테이너 메모리 상한 부재.

해결은 단일 조치로는 안 돼요. `mem_limit` 설정 + TSDB 튜닝 + 스왑 확보를 묶어서 적용해야 실제로 안정화돼요. 더 작은 메모리 풋프린트가 필요하다면 VictoriaMetrics 전환을 고려해 볼 만해요.

지금 운영 중인 VPS가 있다면 `docker stats` 명령어로 각 컨테이너의 현재 메모리 사용량부터 확인해 보세요. 수치가 보이는 순간, 어디를 줄여야 할지 명확해질 거예요.

## 참고자료

1. [Docker 컨테이너 메모리 관리 및 OOM 대응 - 성장하는 개발자](https://bluedreamer-twenty.tistory.com/6)
2. [Docker 컨테이너 모니터링: cAdvisor + Prometheus + Grafana](https://denev6.tistory.com/entry/grafana)
3. [Consider enabling memory cgroup by default in 64-bit Lite builds (for Docker users) · Issue #917 · R](https://github.com/RPi-Distro/pi-gen/issues/917)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
