---
title: "2GB VPS에서 Prometheus + Grafana OOM 없이 운영하는 메모리 최적화 설정 삽질 기록"
date: 2026-04-13T20:37:00+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "prometheus", "grafana", "2gb", "Docker"]
description: "2GB VPS에서 Prometheus+Grafana Docker Compose 구성 시 TSDB 캐시가 1.2GB를 초과해 OOM이 발생하는 문제를 실제 삽질로 해결한 기록. retention.time 등 두 플래그로 메모리 30~40% 절감하는 설정"
image: "/images/20260413-prometheus-grafana-2gb-vps-doc.webp"
technologies: ["Docker"]
faq:
  - question: "2GB VPS에서 Prometheus Grafana Docker Compose 올리면 OOM 나는 이유"
    answer: "Prometheus Grafana 2GB VPS Docker Compose OOM 해결 메모리 최적화 설정 삽질 기록에 따르면, Prometheus 기본 설정(15일 보존)만으로도 TSDB 캐시가 1.2GB를 초과할 수 있고, 여기에 Grafana 300~400MB와 OS 기본 점유 400MB가 더해져 총 메모리가 2GB를 넘기게 됩니다. 특히 Docker Compose에서 `mem_limit` 없이 배포하면 한 컨테이너의 메모리 폭발이 VPS 전체를 다운시키는 구조입니다."
  - question: "Prometheus 메모리 사용량 줄이는 플래그 설정 방법"
    answer: "`--storage.tsdb.retention.time=7d`로 보존 기간을 15일에서 7일로 줄이면 TSDB 청크 메모리가 약 절반으로 감소하고, `--query.max-concurrency=4`로 동시 쿼리를 제한하면 대시보드 조회 시 발생하는 순간 메모리 폭발을 막을 수 있습니다. 추가로 `--storage.tsdb.wal-compression` 플래그를 함께 활성화하면 WAL 디스크 사용량도 약 40% 줄어듭니다."
  - question: "Docker Compose mem_limit memswap_limit 차이와 설정 방법"
    answer: "`mem_limit`은 컨테이너가 사용할 수 있는 최대 RAM을 제한하고, `memswap_limit`을 `mem_limit`과 동일하게 설정하면 스왑 사용까지 차단할 수 있습니다. VPS 환경에서는 스왑을 허용하면 디스크 I/O 과부하로 체감 성능이 크게 저하되므로, Prometheus는 700m, Grafana는 300m 수준으로 두 값을 동일하게 맞추는 것이 권장됩니다."
  - question: "Grafana image renderer 플러그인 메모리 얼마나 먹음"
    answer: "Prometheus Grafana 2GB VPS Docker Compose OOM 해결 메모리 최적화 설정 삽질 기록에 따르면, `grafana-image-renderer` 플러그인은 400~600MB를 추가로 점유해 Grafana 전체 메모리를 700~900MB까지 끌어올립니다. PDF 내보내기가 꼭 필요하지 않다면 해당 플러그인을 제거하는 것만으로 400MB 이상을 즉시 확보할 수 있습니다."
  - question: "Prometheus 대신 VictoriaMetrics 쓰면 메모리 얼마나 절약됨"
    answer: "VictoriaMetrics는 동일한 데이터 기준으로 Prometheus 대비 메모리를 절반 이하로 사용하는 대안입니다. 2GB VPS처럼 리소스가 제한된 환경에서 Prometheus의 메모리 최적화만으로 한계를 느낀다면 VictoriaMetrics로 교체하는 것이 근본적인 해결책이 될 수 있습니다."
aliases:
  - "/tech/2026-04-13-prometheus-grafana-2gb-vps-docker-compose-oom-해결-메/"
  - "/ko/tech/2026-04-13-prometheus-grafana-2gb-vps-docker-compose-oom-해결-메/"

---

RAM 2GB짜리 VPS에 모니터링 스택 올렸다가 서버가 통째로 뻗은 경험, 저만 있는 건 아닐 거예요. Prometheus + Grafana + Node Exporter를 Docker Compose로 올리면 얼핏 깔끔해 보이는데, 기본 설정 그대로 두면 메모리가 조용히 차오르다 OOM Killer가 프로세스를 통째로 날려버려요.

> **핵심 요약**
> - Prometheus 기본 설정은 메모리 상한선이 없어서, 2GB VPS에서 TSDB 캐시만으로도 1.2GB 이상을 먹는 경우가 관측돼요.
> - `--storage.tsdb.retention.time`과 `--query.max-concurrency` 두 플래그만 조정해도 메모리 사용량을 30~40% 낮출 수 있어요.
> - Grafana는 기본 설정에 렌더링 플러그인까지 포함하면 600MB를 넘기는데, 경량 설정으로 250MB 아래로 유지할 수 있어요.
> - VictoriaMetrics는 동일 데이터 기준 Prometheus 대비 메모리를 절반 이하로 쓰는 대안이에요.
> - Docker Compose에서 `mem_limit` 설정 없이 배포하면, 한 컨테이너의 누수가 전체 VPS를 죽여요.

---

## 왜 2GB VPS에서 모니터링 스택이 죽는가

문제는 단순해요. Prometheus는 설계상 메모리를 공격적으로 써요.

TSDB(시계열 데이터베이스)는 최근 데이터를 메모리 내 청크로 유지해요. 스크래핑 대상이 많을수록, 보존 기간이 길수록 메모리 점유가 커지는 구조예요. Last9의 Prometheus Docker Compose 가이드에 따르면, 기본 설정으로 15일 보존에 2분 스크래핑 간격을 유지하면 타겟 50개 기준으로도 TSDB 청크가 800MB를 넘길 수 있어요.

여기에 Grafana가 붙어요. Grafana는 기본 이미지에 SQLite, 플러그인 로더, 내장 HTTP 서버가 전부 포함돼서 idle 상태에서도 300MB 근처를 잡고 있어요. 렌더링 플러그인(`grafana-image-renderer`)까지 올리면 400~600MB가 추가돼요.

Node Exporter 자체는 가벼워요. 보통 25~50MB 수준이에요. 문제는 앞의 두 녀석이에요.

결국 2GB VPS에서 기본 설정 그대로 Docker Compose를 올리면 이렇게 돼요:

| 컨테이너 | 기본 메모리 사용량 | 비고 |
|---|---|---|
| Prometheus | 800MB~1.2GB | 15일 보존, 타겟 50개 기준 |
| Grafana (기본) | 300~400MB | 플러그인 없음 |
| Grafana (렌더러 포함) | 700~900MB | image-renderer 포함 |
| Node Exporter | 25~50MB | 경량, 문제 없음 |
| OS + Docker daemon | 300~400MB | 커널, 데몬 기본 점유 |
| **합계 (렌더러 없음)** | **~1.4~1.8GB** | 여유 없음 |
| **합계 (렌더러 포함)** | **~2.1~2.6GB** | **OOM 영역** |

OS가 400MB를 기본으로 쓰는 걸 고려하면, 렌더러 없어도 여유가 200~600MB밖에 안 남아요. 트래픽 스파이크나 쿼리 폭발 한 번이면 OOM Killer가 깨어나요.

---

## Prometheus 메모리를 직접 제어하는 방법

Prometheus는 플래그 몇 개로 메모리 사용 패턴을 크게 바꿀 수 있어요.

### `--storage.tsdb.retention.time`: 보존 기간 줄이기

기본값은 15일이에요. 2GB VPS에서 이건 너무 많아요. 7일로 줄이면 TSDB 청크 메모리가 거의 절반으로 떨어져요. 3일로 줄이면 더 드라마틱하게 줄어들고요.

```yaml
command:
  - '--storage.tsdb.retention.time=7d'
  - '--storage.tsdb.wal-compression'
```

`--storage.tsdb.wal-compression`도 같이 켜면 WAL 디스크 사용량이 약 40% 줄어요. 메모리에도 간접적으로 도움이 돼요.

### `--query.max-concurrency`: 동시 쿼리 제한

기본값은 20이에요. Grafana 대시보드가 여러 패널을 동시에 쿼리하면 순간 메모리가 폭발해요. 2GB VPS에서는 4 이하로 잡는 게 안전해요.

```yaml
  - '--query.max-concurrency=4'
  - '--query.timeout=30s'
```

### 스크래핑 간격: 15초 → 60초

기본 15초 간격은 운영 환경용이에요. 개인 VPS나 소규모 프로젝트면 60초도 충분해요. 간격이 길수록 인메모리 청크 압박이 줄어들어요.

---

## Grafana와 Docker Compose `mem_limit` 설정

Grafana도 손볼 게 있어요.

가장 먼저 할 일은 렌더링 플러그인을 분리하거나 제거하는 거예요. 대시보드 PDF 내보내기가 꼭 필요하지 않다면 `grafana-image-renderer`는 올리지 마세요. 그것만으로도 400MB를 아낄 수 있어요.

```yaml
environment:
  - GF_RENDERING_SERVER_URL=
  - GF_ANALYTICS_REPORTING_ENABLED=false
  - GF_LOG_LEVEL=warn
```

그리고 Docker Compose에서 `mem_limit`을 반드시 걸어야 해요. 이게 없으면 한 컨테이너가 메모리를 다 잡아먹어도 Docker가 개입하지 않아요.

```yaml
services:
  prometheus:
    mem_limit: 700m
    memswap_limit: 700m
  grafana:
    mem_limit: 300m
    memswap_limit: 300m
```

`memswap_limit`을 `mem_limit`과 같게 설정하면 스왑을 못 쓰게 막아요. 스왑을 허용하면 서버가 죽지는 않지만 디스크 I/O 때문에 체감 성능이 바닥을 쳐요. VPS에서 스왑 의존은 권장하지 않아요.

---

## Prometheus 대신 VictoriaMetrics를 고려해야 할 시점

메모리를 아무리 조여도 근본적으로 작은 박스에 무거운 걸 올리는 건 한계가 있어요. 그래서 VictoriaMetrics가 대안으로 자주 거론돼요.

Docker Recipes의 VictoriaMetrics 레시피 기준으로, 동일한 50개 타겟을 30일 보존으로 모니터링할 때 메모리 사용량이 Prometheus의 30~50% 수준이에요. Prometheus 호환 API를 제공해서 Grafana를 그대로 붙일 수 있어요.

| 항목 | Prometheus | VictoriaMetrics |
|---|---|---|
| 메모리 사용 (타겟 50개, 7일 보존) | ~500~800MB | ~200~350MB |
| Prometheus API 호환 | 네이티브 | 호환 (대부분 동일) |
| 클러스터 지원 | 제한적 | 내장 |
| 설정 복잡도 | 낮음 | 낮음 |
| 장기 보존 비용 | 높음 | 낮음 |
| 커뮤니티 규모 | 매우 큼 | 성장 중 |

단, 기존에 PromQL을 깊이 쓰고 있고 AlertManager 연동이 복잡하게 묶여 있다면 이전 비용이 생각보다 클 수 있어요. 새로 세팅하는 거라면 VictoriaMetrics를 처음부터 선택하는 게 낫고, 기존 Prometheus 스택을 운영 중이라면 플래그 조정과 `mem_limit`이 현실적인 1차 해결책이에요.

---

## 당장 적용할 수 있는 순서

1. **`mem_limit` 먼저**: Docker Compose에 메모리 한도부터 걸어요. 이게 없으면 나머지 설정이 의미 없어요.
2. **보존 기간 7일로**: `--storage.tsdb.retention.time=7d`로 줄여요.
3. **스크래핑 간격 60초로**: `scrape_interval: 60s`로 늘려요.
4. **Grafana 렌더러 제거**: 필요 없다면 가장 빠른 메모리 절약이에요.
5. **쿼리 동시성 4로 제한**: 대시보드 쿼리 폭발 방지예요.

이 다섯 가지만 해도 2GB VPS에서 Prometheus + Grafana를 안정적으로 운영할 수 있어요. 메모리 여유가 400MB 이상 나오면 그때부터 대시보드를 늘리거나 타겟을 추가하는 게 안전한 순서예요.

클라우드 VPS 가격이 내려오고 있지만, 여전히 2~4GB 박스에서 모니터링 스택을 올리는 케이스는 많아요. OOM 한 번 겪고 나면 설정의 중요성이 확 와닿죠. 설정 파일 한 줄이 서버 안정성을 결정하니까요.

지금 당장 `free -h` 한 번 찍어보세요. 여유가 얼마나 남아있는지 확인하고 시작하는 게 맞아요.

## 참고자료

1. [Monitor Docker Containers with Prometheus and Grafana](https://computingforgeeks.com/monitor-docker-containers-prometheus-grafana/)
2. [Prometheus with Docker Compose: The Complete Setup Guide | Last9](https://last9.io/blog/prometheus-with-docker-compose/)
3. [VictoriaMetrics Docker Compose - Ready to Deploy | Docker Recipes](https://docker.recipes/monitoring/victoria-metrics)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
