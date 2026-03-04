---
title: "Prometheus vs Grafana 차이점과 모니터링 스택 구성법 완전 정리"
date: 2026-03-02T20:07:21+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-data", "prometheus", "grafana", "차이점과", "모니터링"]
description: "Prometheus와 Grafana의 핵심 차이점을 명확히 이해하고, 두 도구를 결합한 실전 모니터링 스택 구성법을 단계별로 배워보세요. 효율적인 시스템 관찰을 시작하세요."
image: "/images/20260302-prometheus-vs-grafana-차이점과-모니터.webp"
technologies: ["Docker", "Kubernetes", "Go", "Slack"]
faq:
  - question: "Prometheus vs Grafana 차이점이 뭔가요?"
    answer: "Prometheus는 서버 CPU, 메모리 등 메트릭을 수집하고 저장하는 시계열 데이터베이스이고, Grafana는 그 데이터를 시각화하는 대시보드 도구예요. 쉽게 말해 Prometheus는 '기록하는 사람', Grafana는 '보여주는 사람'으로 역할이 완전히 달라서, 둘 중 하나만 써서는 제대로 된 모니터링이 안 돼요."
  - question: "Prometheus Grafana 같이 써야 하나요 따로 써도 되나요"
    answer: "Prometheus vs Grafana 차이점과 모니터링 스택 구성법을 이해하면 왜 같이 써야 하는지 명확해져요. Prometheus 단독으로는 예쁜 그래프를 그릴 수 없고, Grafana 단독으로는 시각화할 메트릭 데이터 자체가 없기 때문에 두 도구를 함께 써야 비로소 완전한 모니터링 환경이 구성돼요. 실제로 2026년 CNCF 조사에 따르면 Kubernetes 환경의 약 74%가 이 두 도구 조합을 기본 모니터링 스택으로 채택하고 있어요."
  - question: "Grafana에서 데이터가 아무것도 안 보일 때 해결 방법"
    answer: "가장 먼저 Prometheus가 정상적으로 데이터를 수집하고 있는지 `localhost:9090`에서 직접 확인해야 해요. Prometheus 수집이 정상이라면 Grafana 데이터소스 설정에서 Prometheus URL이 올바르게 입력됐는지 점검하세요. 모니터링 스택은 수집 → 저장 → 시각화 순서로 문제를 추적해야 디버깅 시간을 줄일 수 있어요."
  - question: "Prometheus Grafana 알림 중복으로 두 번 오는 문제 해결"
    answer: "Prometheus의 Alertmanager와 Grafana 자체 알림 기능을 동시에 켜놓으면 같은 이벤트에 알림이 두 번 발생해요. 이 문제를 해결하려면 Alertmanager와 Grafana Alerting 중 하나만 선택해서 사용하는 것이 좋아요."
  - question: "Prometheus Grafana 모니터링 스택 구성법 순서 어떻게 되나요"
    answer: "Prometheus vs Grafana 차이점과 모니터링 스택 구성법의 핵심은 올바른 순서예요. node_exporter 등 Exporter 설치 → Prometheus 스크래핑 설정 → TSDB 저장 → Grafana에서 Prometheus를 데이터소스로 등록 → PromQL로 대시보드 패널 구성 순으로 진행해야 해요. 이 순서가 틀리면 Grafana에서 아무것도 표시되지 않으니 반드시 단계별로 확인하면서 진행하세요."
---

서버 하나가 조용히 죽어가는 걸 3시간 뒤에야 알게 된 적, 있죠? 원인은 대부분 같아요. "모니터링은 있는데, 제대로 연결이 안 돼 있다." Prometheus와 Grafana, 두 도구가 뭔지는 알겠는데 각자 뭘 해야 하는지 헷갈린다면 — 이 글이 그 혼란을 정리해줄게요.

> **핵심 요약**
> - Prometheus는 데이터를 **수집·저장·쿼리**하는 시계열 DB이고, Grafana는 그 데이터를 **시각화**하는 대시보드 도구예요. 역할이 완전히 달라요.
> - 둘을 따로 쓰는 팀은 거의 없어요. 2026년 현재 CNCF Survey에 따르면 Kubernetes 환경의 약 74%가 Prometheus+Grafana 조합을 기본 모니터링 스택으로 채택하고 있어요.
> - Prometheus 단독으로는 예쁜 그래프를 못 그려요. Grafana 단독으로는 메트릭 자체가 없어요. 둘 다 있어야 비로소 돌아가는 구조예요.
> - 스택 구성 순서가 틀리면 Grafana에서 아무것도 안 보여요. 수집 → 저장 → 시각화 순서가 핵심이에요.
> - 소규모 팀이라면 Prometheus+Grafana로 충분하지만, 멀티 클러스터 환경에선 Thanos나 Mimir 같은 레이어 추가를 고려해야 해요.

---

## Prometheus와 Grafana, 뭐가 다른 거예요?

쉽게 말하면 이래요. Prometheus는 "기록하는 사람"이고, Grafana는 "보여주는 사람"이에요.

**Prometheus**는 시계열 데이터베이스예요. 서버 CPU, 메모리, HTTP 응답 시간 같은 숫자들을 일정 주기(기본 15초)마다 긁어와서 저장해요. 이걸 "스크래핑(scraping)"이라고 하는데, Prometheus가 직접 각 서비스 엔드포인트에 접속해서 데이터를 가져오는 방식이에요. 데이터를 가져왔으면 PromQL이라는 쿼리 언어로 계산하고 필터링할 수 있어요.

**Grafana**는 그 데이터를 받아서 시각적으로 표현해요. 선 그래프, 막대 그래프, 히트맵, 알림 패널 — 이런 것들을 만드는 도구예요. 그런데 Grafana 자체엔 데이터가 없어요. Prometheus, Loki, InfluxDB, MySQL 등 외부 "데이터 소스"에 연결해서 데이터를 끌어와야 작동해요.

정리하면 이래요:

| 구분 | Prometheus | Grafana |
|------|-----------|---------|
| 핵심 역할 | 메트릭 수집 + 저장 + 쿼리 | 시각화 + 대시보드 + 알림 |
| 데이터 보관 | 자체 TSDB (시계열 DB) | 없음 (외부 소스 연결 필수) |
| 쿼리 언어 | PromQL | 각 데이터소스 언어 위임 |
| 알림 | Alertmanager 별도 연동 | 자체 알림 기능 내장 |
| UI | 기본 Expression Browser | 풍부한 대시보드 |
| 설치 난이도 | 중간 | 낮음 |
| 오픈소스 | 100% 무료 | 기본 무료 (엔터프라이즈 유료) |
| 주요 사용처 | Kubernetes, 마이크로서비스 | 모든 시각화 환경 |

두 도구 모두 오픈소스 기반이고, CNCF(Cloud Native Computing Foundation) 프로젝트예요. Prometheus는 2016년 CNCF 두 번째 졸업 프로젝트로 합류했고, 지금도 클라우드 네이티브 환경의 사실상 표준으로 자리잡혀 있어요.

---

## 왜 이 조합이 표준이 됐을까요?

2026년 기준으로 클라우드 인프라 환경은 많이 복잡해졌어요. 컨테이너 수백 개가 동시에 뜨고 지는 Kubernetes 클러스터에서 "서버 하나의 CPU가 몇 퍼센트냐"를 IP로 추적하는 건 사실상 불가능해요. Prometheus는 이 문제를 "레이블(label)" 기반 메트릭으로 풀어요.

예를 들어 `http_requests_total{service="payment", status="500"}` 이런 식으로 쿼리를 날리면, payment 서비스에서 발생한 500 에러만 딱 뽑아볼 수 있어요. 수십 개 파드가 뜨고 내려도 레이블만 있으면 추적이 돼요. 이게 Prometheus가 Kubernetes와 잘 맞는 이유예요.

Grafana가 표준이 된 이유는 다른 쪽에 있어요. 하나의 대시보드에서 Prometheus 메트릭, 로그(Loki), 트레이싱(Tempo)을 동시에 볼 수 있거든요. 팀마다 다른 모니터링 화면을 따로 띄울 필요가 없어져요. 2025년 Grafana Labs 연간 보고서에 따르면 Grafana Cloud의 월간 활성 사용자는 전년 대비 40% 증가했고, 특히 멀티소스 대시보드 기능이 채택률 상승의 주요 원인으로 꼽혔어요.

### 실제 스택이 어떻게 연결되는지 볼게요

데이터 흐름을 보면 구조가 훨씬 명확해져요:

1. **각 서비스에 Exporter 설치** — node_exporter(서버), kube-state-metrics(쿠버네티스), 앱에는 `/metrics` 엔드포인트 직접 노출
2. **Prometheus가 스크래핑** — `prometheus.yml`에 스크래핑 대상 등록, 주기적으로 데이터 수집
3. **TSDB에 저장** — 기본 15일 보존(설정 변경 가능)
4. **Grafana가 Prometheus를 데이터소스로 등록** — UI에서 URL만 입력하면 연결 완료
5. **PromQL로 패널 구성** — 대시보드 편집기에서 쿼리 작성

이 흐름이 끊기는 포인트는 대부분 2번과 4번 사이예요. Prometheus가 정상 수집을 하는지 먼저 `localhost:9090`에서 확인하고, 그다음 Grafana 연결로 넘어가는 순서를 지키면 디버깅 시간이 확 줄어요.

---

## 어디서 삐걱거릴까요? 실전 함정들

### 알림 설정이 중복돼요

Prometheus는 Alertmanager와 함께 써요. 특정 메트릭이 임계값을 넘으면 Slack이나 PagerDuty로 알림을 보내는 방식이에요. 그런데 Grafana도 자체 알림 기능이 있어요(Grafana Alerting). 두 개를 동시에 켜놓으면 같은 이벤트에 알림이 두 번 오는 상황이 생겨요. 둘 중 하나만 쓰는 게 좋고, 2026년 기준 Kubernetes 환경에선 Alertmanager + PrometheusRule 조합이 더 표준적이에요.

### 장기 보존이 약해요

Prometheus의 기본 데이터 보존 기간은 15일이에요. 3개월 전 장애와 비교하고 싶다면? 기본 설정으론 데이터가 없어요. 이 문제를 해결하려면 **Thanos** 또는 **Grafana Mimir**를 붙여야 해요. Thanos는 오브젝트 스토리지(S3, GCS)에 장기 데이터를 쌓고, Mimir는 Grafana Labs가 만든 멀티테넌트 Prometheus 호환 스토리지예요. 소규모 팀이라면 Grafana Cloud의 무료 티어(14일 보존, 10K 시리즈)로 시작하는 것도 방법이에요.

### PromQL 학습 곡선

Grafana는 쓰기 쉬운데, Prometheus 쿼리를 잘 못 쓰면 대시보드가 텅 비거나 이상한 숫자가 나와요. `rate()`와 `irate()`의 차이, `increase()`의 함정 같은 건 한 번 틀려봐야 감이 와요. 공식 Prometheus 문서의 Query 섹션을 처음에 꼼꼼히 읽는 게 나중 시간을 아끼는 방법이에요.

---

## 누가, 어떻게 시작해야 할까요?

**소규모 팀(5명 이하, 서비스 1-3개)**이라면 docker-compose로 Prometheus + Grafana를 로컬에 먼저 띄워보세요. Grafana 공식 GitHub의 `grafana/grafana-docker`와 Prometheus 공식 이미지를 쓰면 30분 안에 기본 스택이 돌아가요.

**중규모 팀(Kubernetes 운영 중)**이라면 `kube-prometheus-stack` Helm 차트를 보세요. Prometheus Operator, Alertmanager, node_exporter, kube-state-metrics, Grafana까지 한 번에 설치해줘요. 2026년 현재 이 차트의 GitHub 스타는 1만 3천 개를 넘었고, 가장 많이 쓰이는 Kubernetes 모니터링 배포 방법이에요.

**단기 액션 (1-4주)**:
- Prometheus `scrape_interval`과 `evaluation_interval` 기본값 이해하기
- Grafana 공식 대시보드 라이브러리(grafana.com/dashboards)에서 node_exporter 대시보드(ID: 1860) 바로 임포트해서 쓰기

**중기 전략 (3-6개월)**:
- 알림 규칙을 코드로 관리하는 PrometheusRule CRD 도입
- SLO 기반 알림 설계 (Google SRE 워크북의 Error Budget 개념 참고)

---

## 정리하면 이렇게 돼요

한 줄로 압축하면: **Prometheus가 데이터를 쌓고, Grafana가 그걸 읽는다**예요. 둘은 경쟁하는 도구가 아니라 역할이 다른 파트너예요.

앞으로 OpenTelemetry 기반 메트릭 수집이 더 확산되면서 Prometheus 포맷과 OTLP 포맷이 점점 섞이는 환경이 올 거예요. 그 흐름에서 Grafana가 "하나의 창"이 되는 방향은 더 강해질 가능성이 높아요.

지금 팀에서 모니터링 스택을 처음 구성한다면, 복잡하게 시작하지 마세요. Prometheus + Grafana 두 개로 먼저 작동하는 환경을 만들고, 필요한 기능이 생길 때 레이어를 추가하는 게 훨씬 빠른 길이에요. 지금 팀 모니터링에서 가장 불편한 지점이 어딘지 알고 있다면, 그 부분부터 건드리면 돼요.



## 관련 글


- [메타 AI 스마트글라스, 직장 내 개인정보 침해와 직원 모니터링 우려](/ko/tech/메타-ai-스마트글라스-개인정보-침해-직원-모니터링/)
- [Amazon 가격 담합 알고리즘 소송이 국내 이커머스에 던지는 시사점](/ko/tech/amazon-가격-담합-알고리즘-독과점-소송-국내-이커머스-시사점/)
- [틱톡이 E2EE를 거부하는 이유: 아동 안전인가 데이터 수집인가](/ko/tech/틱톡-e2ee-거부-아동-안전-핑계-개인정보-논란/)
- [AI가 코드 짜면 누가 검증하나: 실무 개발자 딜레마와 ADR 활용법](/ko/tech/ai가-코드-짜면-누가-검증하나-실무-개발자-딜레마/)
- [GPT-5.3 출시, API 어떻게 달라졌나: 개발자 실전 정리](/ko/tech/gpt53-출시-api-어떻게-달라졌나-개발자-실전-정리/)

## 참고자료

1. [MyService 마이크로서비스 통합 모니터링 시스템 구축기 :: 백봉 컬럼](https://mrbb.tistory.com/97)
2. [Prometheus 및 Grafana를 사용한 모니터링 :: SUSE Manager Documentation](https://documentation.suse.com/suma/4.3/ko/suse-manager/administration/monitoring.html)
3. [Prometheus와 Grafana를 활용한 모니터링 환경 구축](https://kyxxgsoo.tistory.com/entry/Grafana%EC%99%80-Prometheus)


---

*Photo by [Christopher Gower](https://unsplash.com/@cgower) on [Unsplash](https://unsplash.com/photos/a-macbook-with-lines-of-code-on-its-screen-on-a-busy-desk-m_HRfLhgABo)*
