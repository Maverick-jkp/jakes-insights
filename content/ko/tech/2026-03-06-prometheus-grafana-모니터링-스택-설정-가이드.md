---
title: "Spring Boot + Prometheus + Grafana Docker 모니터링 스택 설정 가이드"
date: 2026-03-06T14:23:59+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-data", "prometheus", "grafana", "\ubaa8\ub2c8\ud130\ub9c1", "Docker"]
description: "Docker로 Prometheus + Grafana를 연결하고 Spring Boot 메트릭을 대시보드로 시각화하는 방법을 단계별로 설명합니다. Pull 방식으로 5초마다 수집되는 Actuator 메트릭을 MSA 환경에서 실제로 운영하는 수준까지"
image: "/images/20260306-prometheus-grafana-모니터링-스택-설정-.webp"
technologies: ["Docker", "Linux"]
faq:
  - question: "Prometheus Grafana 모니터링 스택 설정 가이드 처음 시작하려면 뭐 준비해야 하나요?"
    answer: "Prometheus Grafana 모니터링 스택 설정 가이드를 따라 시작하려면 Docker Desktop v24 이상과 Spring Boot 앱, 텍스트 에디터만 있으면 돼요. Spring Boot 앱이 없다면 start.spring.io에서 바로 생성할 수 있어요."
  - question: "Spring Boot Prometheus 연동할 때 어떤 의존성 추가해야 하나요?"
    answer: "build.gradle에 spring-boot-starter-actuator와 micrometer-registry-prometheus 두 가지 의존성을 추가해야 해요. 그 다음 application.yml에서 prometheus 엔드포인트를 활성화하면 /actuator/prometheus 경로로 메트릭 데이터가 노출돼요."
  - question: "Docker 컨테이너에서 localhost로 Spring Boot 앱 연결이 안 되는 이유가 뭔가요?"
    answer: "Docker 컨테이너 내부에서 localhost는 호스트 머신이 아닌 컨테이너 자신을 가리키기 때문이에요. Mac과 Windows에서는 host.docker.internal을 사용하고, Linux에서는 --add-host=host.docker.internal:host-gateway 옵션을 추가해야 정상적으로 연결돼요."
  - question: "Grafana에서 Spring Boot JVM 대시보드 빠르게 만드는 방법 있나요?"
    answer: "Grafana 대시보드 ID 4701(JVM Micrometer)을 임포트하면 수동으로 그래프를 하나씩 만들 필요 없이 완성된 JVM 메트릭 대시보드를 바로 사용할 수 있어요. Grafana의 Import 기능에서 해당 ID를 입력하기만 하면 돼요."
  - question: "Prometheus 스크랩 간격 프로덕션 환경에서 몇 초로 설정하는 게 좋나요?"
    answer: "프로덕션 환경에서는 Prometheus 스크랩 간격을 15초에서 1분 사이로 설정하는 것이 권장돼요. 개발 환경용으로 제안된 5초 간격은 프로덕션에서 서버 부하를 높일 수 있고, 스토리지로는 POSIX 파일시스템이 필요하며 NFS는 사용하면 안 돼요."
---

Spring Boot 앱을 배포하고 나서 "서버가 왜 이렇게 느리지?" 싶은 순간, 아무것도 볼 수 없다면 — 그게 진짜 무서운 거예요. MSA 환경이 표준이 된 지금, 메트릭 시각화 없이 프로덕션을 운영하는 건 눈 감고 운전하는 것과 같아요.

이 글은 Docker 기반으로 Prometheus + Grafana를 직접 연결하고, Spring Boot 앱 메트릭까지 대시보드로 볼 수 있는 수준까지 데려다줘요. DevOps 입문자부터 사이드 프로젝트에 모니터링을 붙이고 싶은 개발자까지 모두 따라올 수 있어요.

> **Key Takeaways**
> - Prometheus는 5초 간격으로 메트릭을 당겨오는(Pull) 방식이며, Spring Boot Actuator + Micrometer 조합으로 `/actuator/prometheus` 엔드포인트를 노출해야 해요
> - Docker 컨테이너 안에서 `localhost`는 호스트를 가리키지 않아요 — `host.docker.internal`이나 컨테이너 이름을 써야 연결돼요
> - Grafana 대시보드 ID **4701** (JVM Micrometer)을 가져오면 수동으로 그래프를 만들 필요가 없어요
> - LGTM 스택(Loki + Grafana + Tempo + Mimir)으로 확장하면 로그, 트레이스, 메트릭을 하나의 UI에서 연결해서 볼 수 있어요
> - 프로덕션에서는 Prometheus 스크랩 간격을 15초~1분으로 조정하고, NFS 스토리지는 쓰면 안 돼요 (POSIX 파일시스템 필요)

---

## Prometheus + Grafana, 왜 이 조합인가요?

쿠버네티스와 MSA가 일반화되면서, 서비스 하나가 수십 개 컨테이너로 쪼개지는 게 당연해졌어요. 로그만 보는 시대는 끝났고, "지금 이 순간 CPU가 몇 %인지", "HTTP 요청 중 5xx 비율이 얼마인지"를 숫자로 봐야 해요.

Prometheus는 2012년 SoundCloud에서 만들어져 2016년 CNCF에 합류했어요. 지금은 쿠버네티스 생태계의 사실상 표준 메트릭 수집기예요. Grafana는 그 데이터를 시각화해주는 역할이고요.

| 항목 | Prometheus + Grafana | Datadog | ELK Stack |
|------|---------------------|---------|-----------|
| 비용 | 무료 (셀프호스팅) | 월 $15~/호스트 | 셀프호스팅 시 무료 |
| 설치 난이도 | Docker로 중간 수준 | 에이전트만 설치 | 설정 복잡 |
| 메트릭 성능 | 빠름 (로컬 TSDB) | 클라우드 의존 | 메트릭보다 로그 특화 |
| 확장성 | Mimir/Thanos로 확장 | 자동 확장 | 노드 추가 필요 |
| 커뮤니티 | CNCF 공식, 활발 | 상업 지원 | 활발하지만 무거움 |

Datadog은 설치가 쉽고 완성도가 높지만, 비용이 빠르게 올라가요. ELK는 로그 분석엔 강하지만 메트릭 모니터링 용도로 쓰기엔 과해요. Spring Boot + Docker 환경에서 빠르게 시작하려면 Prometheus + Grafana 조합이 가장 현실적이에요.

---

## 단계별 설정 가이드

### 사전 준비

- Docker Desktop 설치 (v24 이상 권장)
- Spring Boot 앱 (없으면 [start.spring.io](https://start.spring.io)에서 생성)
- 텍스트 에디터

---

### Step 1: Spring Boot Actuator + Micrometer 설정

`build.gradle`에 두 가지 의존성을 추가해요.

```groovy
// build.gradle
dependencies {
    // Spring Boot Actuator: /actuator/* 엔드포인트 생성
    implementation 'org.springframework.boot:spring-boot-starter-actuator'

    // Micrometer Prometheus: Actuator 데이터를 Prometheus 형식으로 변환
    implementation 'io.micrometer:micrometer-registry-prometheus'
}
```

그리고 `application.yml`에서 엔드포인트를 열어줘요.

```yaml
# application.yml
management:
  endpoints:
    web:
      exposure:
        include: "*"   # 모든 Actuator 엔드포인트 노출
  endpoint:
    prometheus:
      enabled: true
```

앱을 실행하고 `http://localhost:8080/actuator/prometheus`에 접근해보세요. 텍스트로 가득 찬 메트릭 데이터가 보이면 성공이에요. 이걸 Prometheus가 주기적으로 가져가는 거예요.

---

### Step 2: prometheus.yml 설정 파일 작성

프로젝트 루트에 `monitoring/` 폴더를 만들고, 그 안에 `prometheus.yml`을 작성해요.

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 5s      # 5초마다 메트릭 수집 (개발 환경용 — 프로덕션은 15s 이상 권장)

scrape_configs:
  - job_name: 'spring-boot-app'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets:
          - 'host.docker.internal:8080'
          # ⚠️ Docker 컨테이너 내부에서 localhost는 호스트가 아니에요
          # Mac/Windows: host.docker.internal 사용
          # Linux: --add-host=host.docker.internal:host-gateway 옵션 필요
```

---

### Step 3: Docker Compose로 Prometheus + Grafana 실행

같은 `monitoring/` 폴더에 `docker-compose.yml`을 만들어요.

```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin   # 초기 비밀번호 (프로덕션에서 반드시 바꾸세요!)
    depends_on:
      - prometheus
    restart: unless-stopped
```

터미널에서 실행해요.

```bash
cd monitoring
docker-compose up -d

# 컨테이너 상태 확인
docker-compose ps
```

`http://localhost:9090`에서 Prometheus UI, `http://localhost:3000`에서 Grafana 로그인 화면이 뜨면 돼요.

---

### Step 4: Grafana에서 Prometheus 데이터 소스 연결

1. `http://localhost:3000` 접속 → `admin / admin`으로 로그인
2. 좌측 메뉴 → **Connections → Data Sources → Add new data source**
3. **Prometheus** 선택
4. URL에 `http://prometheus:9090` 입력

   > `localhost:9090`이 아니에요! 컨테이너끼리는 서비스 이름으로 통신해요.

5. **Save & Test** 클릭 → "Successfully queried the Prometheus API" 메시지 확인

---

### Step 5: 대시보드 가져오기

처음부터 그래프를 만들 필요 없어요. [Grafana 공식 대시보드 라이브러리](https://grafana.com/grafana/dashboards/)에서 가져오면 돼요.

1. 좌측 메뉴 → **Dashboards → Import**
2. Dashboard ID에 `4701` 입력 → **Load**

   > **4701**: JVM Micrometer 대시보드 — Spring Boot 앱의 힙 메모리, GC, 스레드, HTTP 요청 현황을 한눈에 볼 수 있어요

3. Prometheus 데이터 소스 선택 후 **Import**

실시간으로 JVM 메트릭이 그래프로 올라오기 시작해요. 처음 보는 순간 꽤 짜릿해요.

---

## PromQL 기본 쿼리 예시

대시보드를 커스텀하고 싶을 때 쓸 수 있는 기본 쿼리예요.

```promql
# HTTP 5xx 에러 비율 (5분 평균)
sum(rate(http_server_requests_seconds_count{status=~"5.."}[5m]))
/
sum(rate(http_server_requests_seconds_count[5m]))

# JVM 힙 사용률 (%)
jvm_memory_used_bytes{area="heap"}
/
jvm_memory_max_bytes{area="heap"} * 100

# 초당 요청 수
rate(http_server_requests_seconds_count[1m])
```

참고로, [youngju.dev의 LGTM 스택 가이드](https://www.youngju.dev/blog/observability/grafana_lgtm_stack_complete_guide)에 따르면 Tempo의 `metrics_generator`를 쓰면 트레이스 데이터에서 RED 메트릭(Rate, Error, Duration)을 자동으로 뽑아낼 수도 있어요. 메트릭 계측을 따로 안 해도 되는 거죠.

---

## 자주 하는 실수들

**Pitfall 1: Docker 안에서 localhost 쓰기**
- 문제: `prometheus.yml`의 target을 `localhost:8080`으로 설정하면 Prometheus가 자기 자신에 접근해요
- 해결: Mac/Windows는 `host.docker.internal:8080`, Linux는 `docker-compose.yml`에 `extra_hosts: ["host.docker.internal:host-gateway"]` 추가

**Pitfall 2: NFS 스토리지에 Prometheus 데이터 저장**
- [SUSE Manager 공식 문서](https://documentation.suse.com/suma/4.3/ko/suse-manager/administration/monitoring.html)에도 명시돼 있듯, Prometheus는 POSIX 파일시스템이 필요해요. NFS를 쓰면 데이터 손상이 생길 수 있어요.

**Pitfall 3: 스크랩 간격 너무 짧게 설정**
- 개발 환경에서 5초는 괜찮지만, 프로덕션에서 5초는 Prometheus 서버에 부담을 줘요. 15초~1분 사이로 조정하세요.

### 프로덕션 체크리스트

- [ ] `GF_SECURITY_ADMIN_PASSWORD` 기본값 변경
- [ ] Prometheus 데이터 보존 기간 설정 (`--storage.tsdb.retention.time=30d`)
- [ ] Grafana 볼륨 마운트로 대시보드 영속화
- [ ] 5xx 에러율 5% 초과 시 알림 규칙 설정
- [ ] 스크랩 간격 15초 이상으로 조정

---

## 다음 단계

기본 설정은 이걸로 완성이에요. 지금 바로 `docker-compose up -d` 한 번 실행하고 대시보드 ID 4701을 가져와 보세요. 처음엔 낯설어도, JVM 힙 메트릭이 실시간으로 올라가는 걸 한 번 보고 나면 없으면 불안한 도구가 돼요.

그다음 단계가 보인다면, Loki(로그) + Tempo(트레이스)를 붙여서 LGTM 풀스택으로 확장해보세요. 로그에서 트레이스 ID를 클릭하면 바로 해당 요청의 전체 흐름을 볼 수 있어요. 그게 진짜 옵저버빌리티예요.

막히는 부분 있으면 댓글로 남겨주세요!

---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-abstract-background-with-lines-and-dots-pREq0ns_p_E)*
