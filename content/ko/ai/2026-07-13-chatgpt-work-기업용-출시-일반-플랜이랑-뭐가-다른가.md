---
title: "ChatGPT Work 기업용 출시, 일반 플랜이랑 뭐가 다른가"
date: 2026-07-13T21:47:26+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "chatgpt", "work", "/uae30/uc5c5/uc6a9"]
description: "ChatGPT Work가 2026년 7월 9일 출시됐어요. Pro(월 200달러)·Enterprise·Edu 플랜 전용으로, GPT-5.6 기반 에이전트가 문서·스프레드시트·발표자료를 몇 시간 동안 자율 처리해요. 일반"
image: "/images/20260713-chatgpt-work-기업용-출시-일반-플랜이랑-뭐가.webp"
faq:
  - question: "Pro 월 200달러가 실제로 뭘 더 해주길래 이 가격인가요?"
    answer: "Scheduled Tasks, Computer Use, Sites 같은 핵심 기능이 Pro와 Enterprise에만 먼저 열렸어요. 단순 질문-응답이 아니라 몇 시간 동안 자율적으로 업무를 처리하고 결과물을 가져다주는 구조라서, 사람이 붙어 있지 않아도 되는 게 결정적인 차이예요."
  - question: "Plus 쓰고 있으면 Work 기능 언제쯤 쓸 수 있나요?"
    answer: "출시 당시 '며칠 내' 확대 예정이라고 했지만, 어떤 기능까지 포함될지는 공식적으로 명시되지 않았어요. Pro랑 요금 차이가 열 배인 만큼 완전히 동일한 기능을 기대하기는 어렵다는 게 현실적인 예측이에요."
  - question: "Computer Use가 뭔지 모르겠는데 일반 자동화랑 다른 건가요?"
    answer: "기존 자동화는 API 연동이 필요한데, Computer Use는 AI가 화면을 직접 보면서 클릭·타이핑·파일 이동을 해요. API가 없는 레거시 시스템이나 내부 도구에도 쓸 수 있다는 게 핵심 차이예요."
  - question: "Sites로 웹앱 만들면 코딩 진짜 하나도 안 해도 되나요?"
    answer: "프롬프트 하나로 대시보드나 내부 포털을 URL 공유 가능한 형태로 만들어주고, 이메일 피드백을 받으면 자동으로 내용을 업데이트하는 구조도 가능해요. 다만 현재는 공개 베타라 안정성은 직접 확인이 필요해요."
  - question: "GPT-5.6이 기존 모델이랑 실제 체감 차이가 있긴 한가요?"
    answer: "Sam Altman이 'OpenAI가 만든 가장 뛰어난 모델'이라고 직접 표현했고, Sol·Terra·Luna 세 변형으로 나뉘어 작업 유형에 따라 다르게 적용돼요. Finance 팀 월말 보고서가 며칠에서 몇 시간으로 줄었다는 내부 사례가 나왔지만, 일반 대화 품질 체감은 개인 차가 있어요."
---

월 200달러 Pro 요금제가 갑자기 더 달라 보이기 시작했어요.

OpenAI가 2026년 7월 9일, ChatGPT Work를 공식 출시했어요. 단순히 새 기능을 추가한 게 아니에요. 지금까지 "질문하면 답변해주는" 챗봇에서, "일 맡기면 몇 시간 동안 스스로 처리해주는" 에이전트로 방향을 완전히 틀었거든요. 근데 이게 모든 사용자에게 열린 건 아니에요. 어떤 플랜을 쓰느냐에 따라 경험이 완전히 달라져요.

> **핵심 요약**
> - ChatGPT Work는 2026년 7월 9일 출시됐고, Pro(월 200달러), Enterprise, Edu 플랜에만 우선 제공됐어요.
> - GPT-5.6 모델 기반으로 몇 시간 동안 자율적으로 복잡한 업무를 처리할 수 있어요 — 문서, 스프레드시트, 발표자료, 간단한 웹앱까지.
> - Slack, Teams, Google Drive, CRM 등 실무 도구와 직접 연동해 데이터를 알아서 모아요.
> - Finance 팀 기준 월말 보고서 작성 시간이 "며칠"에서 "몇 시간"으로 줄었다는 내부 사례가 나왔어요.
> - Plus·Business 플랜 확대는 출시 직후 "며칠 내"로 예고됐지만, 완전한 기능 동등성은 아직 미정이에요.

---

## ChatGPT Work가 뭔지부터 짚고 넘어갈게요

ChatGPT Work를 이해하려면 Codex부터 알아야 해요.

Codex는 개발자용 코딩 에이전트예요. 코드 작성, 디버깅, 테스트를 자율적으로 처리하죠. 근데 비개발자는 쓸 일이 없는 도구예요. ChatGPT Work는 이 Codex의 "자율 작업 실행 엔진"을 비개발자용 업무에 그대로 가져온 거예요.

[AI타임스 보도](https://www.aitimes.com/news/articleView.html?idxno=212610)에 따르면, Codex 주간 사용자는 이미 500만 명을 넘었고 그 중 100만 명 이상이 비개발자예요. OpenAI는 이 신호를 보고 비개발자 시장을 정면으로 공략한 셈이에요.

기존 ChatGPT와 결정적인 차이는 **작동 시간**이에요.

- 기존 ChatGPT: 질문 → 즉시 응답 → 끝
- ChatGPT Work: 지시 → 몇 시간 동안 자율 처리 → 완성된 결과물 전달

[디자인나침반](https://designcompass.org/2026/07/10/openai-chatgpt-work-public-rollout/)에 따르면, 이번 출시는 GPT-5.6 모델 패밀리(Sol, Terra, Luna 세 변형)의 공개와 동시에 이뤄졌어요. Sam Altman은 GPT-5.6을 "OpenAI가 만든 가장 뛰어난 모델"이라고 직접 표현했죠.

---

## 플랜별로 뭐가 달라지나: 핵심 비교표

### ChatGPT Work 접근 가능 여부

| 기능 | Free | Plus | Business | Pro | Enterprise / Edu |
|------|------|------|----------|-----|-----------------|
| ChatGPT Work 접근 | ❌ | 곧 제공 예정 | 곧 제공 예정 | ✅ 출시 즉시 | ✅ 출시 즉시 |
| GPT-5.6 모델 | ❌ | 제한적 | 제한적 | ✅ 전체 | ✅ 전체 |
| Scheduled Tasks | ❌ | 미정 | 미정 | ✅ | ✅ |
| Computer Use | ❌ | 미정 | 미정 | ✅ | ✅ |
| Sites (노코드 웹앱) | ❌ | 미정 | 제한적 | ✅ | ✅ |
| 외부 도구 연동 | ❌ | 일부 | 일부 | ✅ 전체 | ✅ 전체 + 관리 기능 |
| 요금 | 무료 | ~$20/월 | ~$30/월 | ~$200/월 | 별도 협의 |

[arkelab 정리](https://arkelab.com/100)에 따르면, 출시 당시 Plus·Business 사용자에 대한 기능 확대는 "며칠 내"로 예정됐지만, 어떤 기능까지 포함될지는 명시되지 않았어요. 요금 차이가 열 배인 Pro와 Plus가 동일한 기능을 갖게 될 거라고 보기는 어렵다는 게 현실적인 예측이에요.

---

## 세 가지 핵심 기능: Pro/Enterprise에서만 되는 것들

### Scheduled Tasks — 반복 업무를 완전히 위임하기

매주 월요일 아침, Slack 스레드를 알아서 분석해 주간 리포트를 만들어준다고 상상해봐요. 이게 Scheduled Tasks예요. 예약을 걸어두면 ChatGPT Work가 정해진 시간에 자율적으로 실행하고, 완성된 결과물을 가져다줘요.

[AI타임스](https://www.aitimes.com/news/articleView.html?idxno=212610)가 소개한 내부 사례를 보면, Finance 팀에서 월말 보고서 작성 시간이 "며칠"에서 "몇 시간"으로 줄었어요. 자동화가 아니라 위임이에요. 지시만 해두면 알아서 처리되는 구조죠.

### Computer Use — AI가 직접 PC를 조작해요

클릭, 타이핑, 파일 이동을 ChatGPT Work가 직접 해요. API 연동이 없어도 화면을 보면서 조작하는 방식이에요. 레거시 시스템이나 API가 없는 내부 도구에도 쓸 수 있다는 게 포인트예요.

그런데 일반 Plus 사용자에게 언제 열릴지는 아직 불투명해요. 보안 검토가 필요한 기능이라 기업 계약 고객 위주로 관리될 가능성이 높아요.

### Sites — 노코드 웹앱을 프롬프트 하나로

[AI타임스](https://www.aitimes.com/news/articleView.html?idxno=212610) 보도에 따르면, Sites 기능(공개 베타)은 대시보드, 내부 포털, 인터랙티브 리포트를 URL로 바로 공유 가능한 형태로 만들어줘요. 코드 한 줄 없이요. AI가 이메일 피드백을 받으면 자동으로 내용을 업데이트하는 구조도 가능해요.

영업팀 활용 사례로는, 고객 미팅 후 하루 안에 맞춤 기술 제안서를 자동 생성하는 워크플로우가 소개됐어요. 반복 업무를 줄이는 게 아니라 아예 없애버리는 거예요.

---

## 누가 지금 업그레이드를 고민해야 할까

**Free·Plus 사용자라면**
지금 당장 Pro로 올릴 필요는 없어요. Plus·Business 확대가 "며칠 내"로 예정됐으니 어떤 기능이 들어오는지 먼저 확인하세요. 단, Scheduled Tasks와 Computer Use까지 필요하다면 Pro를 검토할 시점이에요. 월 200달러가 크게 느껴질 수 있는데, 반복 업무 몇 시간만 줄여도 본전이 나오는 구조예요.

**Business 플랜 팀이라면**
지금 당장 해야 할 건 반복 업무 목록을 뽑아두는 거예요. ChatGPT Work가 Business 플랜에 열리는 시점에 바로 적용해볼 수 있게요. 매주 같은 패턴으로 만드는 리포트, 데이터 취합 업무, 발표자료 초안 작업이 1순위 후보예요.

**Enterprise 도입을 검토 중인 조직이라면**
Anthropic의 Claude Cowork와 직접 비교 검토가 필요한 시점이에요. [AI타임스](https://www.aitimes.com/news/articleView.html?idxno=212610)는 ChatGPT Work 출시를 "Claude Cowork에 대한 직접 대응"으로 분석했어요. 두 제품 모두 아직 초기 단계라 실제 도입 전 파일럿 테스트가 필수예요.

**주시해야 할 신호 세 가지**
- Plus·Business 확대 시 어떤 기능이 빠지는지 (기능 격차가 요금 격차를 정당화하는 핵심)
- Computer Use의 보안 감사 결과 공개 여부
- GPT-5.6 Sol/Terra/Luna 중 어떤 변형이 어떤 플랜에 배정되는지

---

## 앞으로 6개월, 뭘 봐야 하나

플랜별로 정리하면 이래요.

- Pro·Enterprise는 지금 바로 쓸 수 있고, 핵심 기능 전체가 열려 있어요
- Plus·Business는 곧 열리지만, 어디까지 열릴지가 관건이에요
- Free는 사실상 기존 ChatGPT와 다를 게 없어요

앞으로 6개월 안에 볼 변화는 세 가지예요.

첫째, Plus에 어떤 기능을 주느냐로 Pro 가치가 재정의돼요. 둘째, Computer Use가 보안 이슈 없이 자리잡으면 레거시 시스템 자동화 시장이 열려요. 셋째, [디자인나침반](https://designcompass.org/2026/07/10/openai-chatgpt-work-public-rollout/)이 언급한 것처럼, 정부 승인 후 공개 배포라는 새 규제 패턴이 굳어지면 앞으로 모델 출시 일정 자체가 달라질 수 있어요.

지금 내가 쓰는 플랜에서 반복하고 있는 업무가 뭔지, 한 번 목록으로 써보세요. ChatGPT Work가 열리는 순간, 그 목록이 테스트 케이스가 될 거예요.

---

*이 글에 사용된 정보는 [arkelab](https://arkelab.com/100), [AI타임스](https://www.aitimes.com/news/articleView.html?idxno=212610), [디자인나침반](https://designcompass.org/2026/07/10/openai-chatgpt-work-public-rollout/)을 참조했어요.*

---

*Photo by [Emiliano Vittoriosi](https://unsplash.com/@emilianovittoriosi) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-computer-screen-with-a-menu-on-it-fvxNerA8uk0)*
