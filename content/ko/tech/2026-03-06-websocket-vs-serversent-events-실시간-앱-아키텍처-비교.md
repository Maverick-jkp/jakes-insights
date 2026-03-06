---
title: "WebSocket vs SSE, 실시간 앱 아키텍처 선택 기준 비교"
date: 2026-03-06T14:17:58+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "websocket", "server-sent", "events", "Node.js"]
description: "WebSocket vs SSE, 95%의 실시간 앱엔 SSE가 낫습니다. Shopify 3,230억 건 처리 사례와 메모리·인프라 비용 데이터로 당신의 아키텍처 선택을 검증하세요."
image: "/images/20260306-websocket-vs-serversent-events.webp"
technologies: ["Node.js", "AWS", "REST API", "GPT", "OpenAI"]
faq:
  - question: "WebSocket vs Server-Sent Events 실시간 앱 아키텍처 비교할 때 어떤 걸 선택해야 하나요?"
    answer: "WebSocket vs Server-Sent Events 실시간 앱 아키텍처 비교 시 핵심 기준은 데이터 흐름 방향이에요. 실시간 앱의 95%는 서버→클라이언트 단방향 흐름만 필요하므로 SSE로 충분하고, 채팅·게임처럼 클라이언트→서버 실시간 송신이 필수인 경우에만 WebSocket이 적합해요. SSE는 구현 코드가 약 10줄로 WebSocket(50줄 이상) 대비 유지보수 비용도 크게 낮아요."
  - question: "SSE랑 WebSocket 메모리 사용량 차이가 얼마나 나나요?"
    answer: "동시 접속 1만 명 기준으로 SSE는 약 20MB, WebSocket은 약 50MB를 사용해 두 배 이상 차이가 나요. WebSocket은 연결 유지를 위한 ping/pong 프레임이 지속적으로 오가기 때문에 유휴 상태에서도 CPU를 더 소비하는 구조예요. 대규모 동시 접속 서비스일수록 이 차이가 인프라 비용으로 직결돼요."
  - question: "ChatGPT 텍스트 스트리밍이 WebSocket 안 쓰고 SSE 쓰는 이유가 뭔가요?"
    answer: "ChatGPT의 텍스트 스트리밍은 서버가 클라이언트로 응답을 순차 전송하는 단방향 흐름이라 SSE가 구조적으로 더 적합해요. SSE는 일반 HTTP 트래픽으로 처리되어 방화벽·CDN 통과가 용이하고, 브라우저 네이티브 자동 재연결 기능도 지원해요. Shopify가 3,230억 건 이벤트를 SSE로 처리한 사례처럼, 단방향 고처리량 환경에서는 WebSocket보다 SSE가 더 효율적인 선택이에요."
  - question: "배달의민족은 왜 WebSocket 대신 SSE를 선택했나요?"
    answer: "배달의민족은 MQTT 기반 주문 알림 시스템에서 방화벽 포트 차단과 WebView 비호환성 문제를 겪은 뒤 SSE로 전환했어요. 클라이언트→서버 통신은 이미 REST API가 담당하고 있었기 때문에 WebSocket을 추가하면 두 프로토콜을 병행 관리해야 하는 복잡도가 생기는 반면, SSE는 기존 HTTP 인프라와 자연스럽게 연결되는 장점이 있었어요. 구현은 Spring WebFlux + Coroutines 기반으로, Last-Event-ID 헤더를 활용해 재연결 시 누락 이벤트도 처리했어요."
  - question: "WebSocket vs Server-Sent Events 실시간 앱 아키텍처 비교에서 처리량·지연시간 성능 차이가 실제로 크게 나나요?"
    answer: "Timeplus 2024 벤치마크 기준으로 WebSocket과 SSE의 처리량·지연시간 차이는 사실상 무시할 수준이에요. 초당 10만 이벤트 환경에서 두 프로토콜 모두 초당 약 300만 이벤트 처리에 도달했고, 지연시간도 WebSocket 45ms, SSE 48ms로 3ms 차이에 불과해요. 성능보다는 메모리 효율, 인프라 호환성, 구현 복잡도가 실제 선택 기준이 돼요."
---

실시간 앱 만들다가 습관처럼 WebSocket 고른 적 있죠? 그런데 ChatGPT는 SSE로 스트리밍하고, Shopify는 3,230억 건의 이벤트를 SSE로 처리했어요. "WebSocket이 기본값"이라는 전제, 이미 흔들리고 있어요.

2026년 현재, WebSocket vs SSE 선택은 단순한 기술 취향이 아니에요. 메모리 비용, 유지보수 복잡도, 인프라 구조 전체에 영향을 미치는 결정이에요. 데이터를 보면 꽤 명확한 답이 나와요.

> **핵심 요약**
> - [DEV Community 벤치마크](https://dev.to/polliog/server-sent-events-beat-websockets-for-95-of-real-time-apps-heres-why-a4l) 기준, 실시간 앱의 95%는 서버→클라이언트 단방향 흐름만 필요 — SSE로 충분히 대체 가능
> - 동시 접속 1만 명 기준, SSE는 약 20MB, WebSocket은 약 50MB — 메모리 기준 두 배 차이
> - ChatGPT, Shopify, Split.io 등 대규모 프로덕션이 이미 SSE를 메인 채널로 채택
> - 배달의민족은 MQTT에서 SSE로 마이그레이션하며, 기존 REST 인프라와 자연스럽게 연결
> - SSE 구현 코드 약 10줄, WebSocket 50줄 이상 — 복잡도 차이가 유지보수 비용으로 직결

---

## WebSocket이 '기본값'이 된 이유, 그리고 균열

WebSocket은 2011년 RFC 6455로 표준화됐어요. 당시엔 양방향 실시간 통신 수요가 많았고, HTTP 폴링의 비효율을 대체할 수단으로 빠르게 퍼졌죠.

그 이후 10년 넘게 "실시간 = WebSocket"이라는 공식이 굳어졌어요. 채팅, 알림, 대시보드, 라이브 피드 — 양방향이 필요한지 따지기도 전에 WebSocket부터 고르는 패턴이 생긴 거예요.

SSE는 다른 길을 걸었어요. 2004년 HTML5 스펙 논의에서 등장했지만 주목받지 못했죠. 브라우저당 HTTP/1.1 연결 제한(최대 6개)이 SSE의 실용성을 막았거든요. 그런데 HTTP/2가 보급되면서 상황이 달라졌어요. 멀티플렉싱 덕분에 연결 수 제한이 사실상 사라졌고, SSE는 오히려 WebSocket보다 인프라 친화적인 선택지가 됐어요.

2026년 기준, 기업 네트워크 환경도 SSE에 유리해요. 많은 방화벽과 CDN이 WebSocket 업그레이드 헤더를 차단하는 반면, SSE는 일반 HTTP 트래픽처럼 통과하거든요. 배달의민족 기술팀도 MQTT의 1883/8883 포트가 식당 방화벽에 막히는 문제를 겪은 뒤 SSE로 전환한 사례가 [우아한형제들 기술블로그](https://techblog.woowahan.com/23199/)에 기록돼 있어요.

---

## 성능 데이터가 말해주는 것

숫자부터 볼게요.

[DEV Community에 공개된 Timeplus 2024 벤치마크](https://dev.to/polliog/server-sent-events-beat-websockets-for-95-of-real-time-apps-heres-why-a4l)는 꽤 흥미로운 결과를 보여줘요.

### 처리량과 지연시간: 차이가 거의 없다

초당 10만 이벤트, 동시 접속 10~30개 환경에서 SSE와 WebSocket 모두 초당 약 300만 이벤트 처리에 도달했어요. 지연시간은 WebSocket이 45ms, SSE가 48ms — 3ms 차이예요. 일반 네트워크 왕복시간(20~100ms)을 감안하면 무시해도 되는 수준이에요.

CPU도 WebSocket 약 40%, SSE 약 42%. 사실상 같아요.

### 동시 접속 1만 명: 메모리가 갈린다

| 항목 | SSE | WebSocket |
|------|-----|-----------|
| 메모리 사용 | ~20MB | ~50MB |
| 유휴 CPU | 15% | 25% |
| 연결당 헤더 오버헤드 | HTTP 헤더 (1회) | 2~14바이트 프레임 지속 |
| 자동 재연결 | 브라우저 네이티브 | 수동 구현 필요 |
| 방화벽 통과 | HTTP로 투명 통과 | 업그레이드 헤더 차단 가능 |
| 구현 코드 | ~10줄 | 50줄 이상 |
| HTTP/2 호환성 | 최적화됨 | 제한적 |
| 적합한 사용 사례 | 단방향 스트림, 알림, AI | 채팅, 게임, 협업 도구 |

WebSocket의 ping/pong 프레임은 연결 유지를 위해 계속 오가요. 그 비용이 CPU와 메모리에 쌓이죠. 유휴 상태에서도 WebSocket이 CPU를 더 쓰는 이유가 여기 있어요.

### 프로덕션 규모의 검증

숫자만이 아니에요. 실제 서비스들이 이미 SSE를 선택했어요.

- **OpenAI/ChatGPT**: 모든 텍스트 스트리밍을 SSE로 처리
- **Shopify**: 블랙프라이데이·사이버먼데이 기간 중 3,230억 건 이벤트를 수백만 SSE 동시 연결로 300ms 이하 지연시간에 처리
- **Split.io**: 월 1조 건 이벤트를 SSE로, 300ms 이하 유지

이 정도 규모면 SSE가 "간단한 알림용"이라는 편견은 이제 유효하지 않아요.

### 배달의민족 사례: 실전 마이그레이션

[우아한형제들 기술블로그](https://techblog.woowahan.com/23199/)가 공개한 배달의민족 사례는 이 비교에서 가장 실질적인 참고가 돼요.

MQTT 기반 주문 알림 시스템의 문제는 세 가지였어요.

- 페이로드 크기 제한 → 빈 메시지 + API 별도 호출 → 지연 발생
- 포트 차단 → 식당 방화벽에서 MQTT 포트 막힘
- WebView 비호환성

AWS IoT를 거쳐 최종적으로 SSE를 선택할 때, WebSocket을 고르지 않은 이유가 명확했어요. 클라이언트→서버 통신은 이미 REST API가 담당하고 있었거든요. WebSocket을 추가하면 두 프로토콜을 병행 관리해야 하는 복잡도가 생기는 거예요.

기술 스택은 Spring WebFlux + Coroutines, `Flow<ServerSentEvent<String>>`으로 응답. `Last-Event-ID` 헤더로 재연결 시 누락 메시지 재전송, `CommitEvent` 패턴으로 주문 수신 중복 출력 방지까지 구현했어요.

한 가지 주의할 점도 있었어요. Kafka 컨슈머의 `max.poll.interval.ms`를 초과하는 백프레셔 문제가 생겼는데, Kotlin Channel의 `capacity = Channel.BUFFERED` 설정으로 해결했다고 해요. SSE 자체의 문제가 아니라 비동기 파이프라인 설계 이슈였던 셈이에요.

---

## 그러면 언제 WebSocket이 맞는가

여기서 균형 잡힌 시각이 필요해요. SSE가 우세한 수치를 보인다고 WebSocket이 잘못된 선택은 아니에요.

양방향 통신이 필수인 경우는 여전히 WebSocket이에요.

- **채팅 앱**: 사용자가 서버로 메시지를 보내야 하죠
- **멀티플레이어 게임**: 클라이언트 입력이 실시간으로 서버에 전달돼야 해요
- **동시 편집 도구** (Figma, Notion 같은): 여러 클라이언트 간 상태 동기화가 필요해요

이 세 가지가 아니라면, 다시 생각해봐야 해요. 알림, 라이브 피드, AI 응답 스트리밍, 로그 테일링, 주식 가격 업데이트 — 이건 모두 서버→클라이언트 단방향이에요. SSE의 영역이죠.

---

## 팀별로 다르게 봐야 할 것들

**서버 사이드 개발자라면**: 기존 REST 인프라가 있다면 SSE 연동이 훨씬 자연스러워요. Node.js 기준 세 개 헤더(`Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`)와 `res.write()`면 서버 구현이 끝나요. WebSocket 서버 구축보다 다섯 배는 빠르게 프로토타입을 만들 수 있어요.

**인프라/DevOps 팀이라면**: CDN 캐시 설정과 방화벽 정책을 확인해봐야 해요. SSE는 HTTP 트래픽으로 처리되니까 기존 정책이 그대로 적용돼요. WebSocket은 `Upgrade` 헤더를 따로 허용해야 하는 경우가 많아요.

**제품/기획 팀이라면**: 질문 하나면 충분해요. "클라이언트가 서버로 실시간 데이터를 보내야 하나요?" NO면 SSE를 먼저 검토하세요.

앞으로 주시할 신호도 있어요. HTTP/3(QUIC 기반)가 확산되면 SSE의 연결 안정성이 더 좋아질 거예요. QUIC은 패킷 손실 시 다른 스트림에 영향을 주지 않는 구조라, 장시간 SSE 연결에 유리하거든요.

---

## 정리: 선택 기준은 단순해요

한 문장으로 줄이면 이렇게 돼요. "데이터가 한 방향으로만 흐르면 SSE, 양방향이 필요하면 WebSocket."

핵심을 다시 정리하면:

- 실시간 앱의 95%는 단방향 데이터 흐름 — SSE로 충분
- 동시 접속 1만 명 기준 메모리 두 배 차이, CPU 10%p 차이
- ChatGPT, Shopify, 배달의민족 — 프로덕션이 이미 답을 냈어요
- 구현 복잡도 차이(10줄 vs 50줄+)는 장기 유지보수 비용이에요

2026년 하반기엔 HTTP/3 기반 SSE 최적화 사례가 더 나올 거예요. WebSocket 기반 아키텍처를 새로 설계하려 한다면, 왜 양방향이어야 하는지 먼저 설명할 수 있어야 해요.

지금 팀의 실시간 기능 스펙을 꺼내보세요. 클라이언트에서 서버로 가는 데이터가 얼마나 되나요?

---

*Photo by [Growtika](https://unsplash.com/@growtika) on [Unsplash](https://unsplash.com/photos/diagram-TKAg3WignSw)*
