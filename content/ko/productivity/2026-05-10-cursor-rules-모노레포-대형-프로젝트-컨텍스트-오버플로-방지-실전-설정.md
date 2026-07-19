---
title: "Cursor Rules 모노레포 대형 프로젝트 컨텍스트 오버플로 방지 실전 설정법"
date: 2026-05-10T20:21:11+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "cursor", "rules", "\ubaa8\ub178\ub808\ud3ec", "TypeScript"]
description: "모노레포 5개 이상 패키지에서 단일 .cursorrules로 컨텍스트 오버플로가 발생하는 이유와, 200k 토큰 윈도우를 실질적으로 확보하는 Cursor Rules 분리 설정법을 다룹니다."
image: "/images/20260510-cursor-rules-모노레포-대형-프로젝트-컨텍스트.webp"
technologies: ["TypeScript", "React", "Cursor"]
faq:
  - question: "Cursor Rules 모노레포 대형 프로젝트 컨텍스트 오버플로 방지 실전 설정 방법"
    answer: "Cursor Rules 모노레포 대형 프로젝트 컨텍스트 오버플로 방지 실전 설정의 핵심은 `.cursor/rules` 디렉토리를 활용해 글로벌 Rules와 패키지별 Rules를 계층적으로 분리하는 것입니다. 글로벌 Rules에는 언어 설정·공통 컨벤션만, 패키지별 Rules에는 해당 패키지에서만 쓰는 로컬 컨텍스트만 넣으면 토큰 낭비를 크게 줄일 수 있습니다. 이 방식을 통해 UI 작업 시 API 관련 Rules가 불필요하게 컨텍스트에 끼어드는 문제를 방지할 수 있습니다."
  - question: "모노레포에서 Cursor AI가 엉뚱한 파일 기준으로 코드 짜는 이유"
    answer: "모노레포에서 Cursor AI가 관련 없는 파일을 참조하는 주요 원인은 컨텍스트 오버플로입니다. `.cursorrules` 파일이 루트에 하나만 있을 경우 매 요청마다 전체 프로젝트 맥락이 주입되고, 패키지가 많아질수록 AI의 실질적인 유효 컨텍스트가 절반 이하로 줄어듭니다. 결과적으로 AI가 프론트엔드 작업 중 백엔드 로직까지 건드리거나 패키지마다 다른 코드를 제안하는 현상이 나타납니다."
  - question: "Cursor Project Rules always auto-attached 차이 언제 써야 하나"
    answer: "`always` 타입은 매 요청마다 자동 주입되므로 코딩 컨벤션·언어 설정처럼 프로젝트 전역에 적용되는 최소한의 규칙에만 사용해야 합니다. `auto-attached`는 특정 파일 패턴(glob)에 매칭될 때만 Rules가 포함되므로, 패키지별 규칙이나 특정 확장자 규칙에 활용하면 불필요한 토큰 낭비를 막을 수 있습니다. 많은 팀이 아키텍처 설명이나 패키지 목록까지 `always`로 설정하는 실수를 하는데, 이러면 간단한 수정 요청에도 수천 토큰짜리 Rules가 매번 붙게 됩니다."
  - question: "cursor rules glob 패턴 설정 어떻게 해야 토큰 절약되나"
    answer: "glob 패턴은 `**/*.ts`처럼 넓게 잡으면 의도치 않게 여러 패키지의 Rules가 동시에 활성화되어 컨텍스트를 낭비하게 됩니다. `packages/ui/**/*.tsx`처럼 패키지 디렉토리 단위로 경계를 명확히 잡는 것이 가장 균형 잡힌 설정으로, 실제 운영 경험에서 검증된 방식입니다. 반대로 너무 좁게 설정하면 관련 파일에서 Rules가 아예 활성화되지 않으므로 패키지 경계를 기준으로 조정하는 것이 권장됩니다."
  - question: "Cursor Rules 모노레포 대형 프로젝트 컨텍스트 오버플로 방지 실전 설정에서 문서 참조 넣으면 안 되는 이유"
    answer: "Rules 파일 내부에 `@docs/api-spec.md`나 `@README` 같은 문서 참조를 넣으면, 해당 문서 크기만큼 매 요청마다 컨텍스트 토큰이 소모되어 오버플로를 가속시킵니다. 문서 참조는 Rules에 고정하지 말고, 실제 작업이 필요한 시점에 채팅창에서 수동으로 `@`를 통해 호출하는 방식이 훨씬 효율적입니다. 또한 Rules 파일 하나를 300줄 이하로 유지하는 것도 컨텍스트 절약을 위한 커뮤니티 검증 경험칙으로 알려져 있습니다."
aliases:
  - "/tech/2026-05-10-cursor-rules-모노레포-대형-프로젝트-컨텍스트-오버플로-방지-실전-설정/"
  - "/ko/tech/2026-05-10-cursor-rules-모노레포-대형-프로젝트-컨텍스트-오버플로-방지-실전-설정/"

---

모노레포를 쓰다 보면 어느 순간 AI가 엉뚱한 파일을 기준으로 코드를 짜기 시작해요. 프론트엔드 컴포넌트를 수정해달라고 했는데 백엔드 로직까지 건드리거나, 공통 유틸 함수를 패키지마다 다르게 제안하는 일이 생기죠. 원인은 대부분 하나예요. 컨텍스트 오버플로.

패키지가 5개 이상인 모노레포에서 `.cursorrules` 하나로 모든 컨텍스트를 감당하려다 AI 응답 품질이 크게 떨어지는 사례가 반복되고 있어요. Cursor의 공식 컨텍스트 윈도우는 약 200k 토큰이지만, 대형 모노레포에서 파일 탐색과 히스토리가 쌓이면 실질적인 유효 컨텍스트는 절반 이하로 줄어드는 경우가 많아요.

이 글에서는 Cursor Rules를 모노레포 대형 프로젝트에 맞게 설정해서 컨텍스트 오버플로를 방지하는 실전 방법을 다뤄요.

> **핵심 요약**
> - Cursor의 컨텍스트 윈도우는 200k 토큰이지만, 모노레포 대형 프로젝트에서는 실질 유효 범위가 50~60%까지 줄어드는 현상이 보고되고 있어요.
> - `.cursor/rules` 디렉토리를 활용한 패키지별 Rules 분리 설정이 현재 가장 현실적인 컨텍스트 오버플로 방지 방법이에요.
> - Rule 유형을 `always`, `auto-attached`, `agent-requested`, `manual` 네 가지로 나눠 적재적소에 쓰면 토큰 낭비를 크게 줄일 수 있어요.
> - 글로벌 Rules에는 프로젝트 전체 컨벤션만, 패키지별 Rules에는 해당 패키지 로컬 컨텍스트만 넣는 역할 분리가 핵심이에요.

---

## 컨텍스트 오버플로가 모노레포에서 더 심각한 이유

단일 레포에서는 AI가 참조할 파일 범위가 제한적이에요. 그런데 모노레포는 달라요. `packages/ui`, `packages/api`, `packages/shared`, `apps/web`, `apps/mobile` 같은 구조가 중첩되면, AI가 관련 없는 패키지의 타입 정의나 설정 파일까지 컨텍스트로 끌어오는 일이 잦아요.

Cursor는 기본적으로 열려 있는 파일과 연관된 import 경로, 그리고 활성화된 Rules를 합산해서 컨텍스트를 구성해요. 문제는 `.cursorrules` 파일이 루트에 하나만 있을 경우, 이게 매 요청마다 전체 프로젝트 맥락으로 주입된다는 거예요. 패키지가 열 개, 각 패키지에 `README`와 타입 파일이 수십 개씩 있다면, 유효한 작업 컨텍스트는 급격히 좁아져요.

2025년 말부터 Cursor가 공식 지원하기 시작한 `.cursor/rules` 디렉토리 구조가 주목받는 이유가 여기 있어요. 단일 파일로 모든 걸 해결하려는 방식에서 벗어나, **계층적 Rules 설계**로 전환하는 흐름이 생겼거든요.

---

## Rules 유형별 역할 분리: 실전 구조 설계

Cursor의 Project Rules는 동작 방식에 따라 크게 네 가지로 나뉘어요.

| 유형 | 동작 방식 | 모노레포 활용 포인트 |
|------|----------|-------------------|
| `always` | 매 요청마다 자동 주입 | 코딩 컨벤션, 언어 설정 등 전역 규칙 |
| `auto-attached` | 특정 파일 패턴 매칭 시 자동 포함 | 패키지별 규칙, 특정 확장자 규칙 |
| `agent-requested` | AI가 필요하다고 판단할 때만 포함 | 복잡한 도메인 로직, 레거시 설명 |
| `manual` | 사용자가 명시적으로 호출할 때만 | 마이그레이션 가이드, 일회성 작업 |

여기서 핵심은 `always` 타입을 최소화하는 거예요. 많은 팀이 실수하는 게 전체 아키텍처 설명, 패키지 목록, 의존성 관계 같은 내용을 전부 `always`로 설정하는 거거든요. 이러면 간단한 수정 요청에도 수천 토큰짜리 Rules가 매번 붙어요.

### 글로벌 Rules vs 패키지 Rules: 역할을 딱 잘라야 해요

```
.cursor/
  rules/
    global.mdc          # always: 언어, 공통 컨벤션
    react-components.mdc # auto-attached: **/*.tsx
    api-handlers.mdc     # auto-attached: packages/api/**
    migration-v3.mdc     # manual: 마이그레이션 시에만
```

글로벌 Rules에는 이것만 넣는 게 맞아요.

- 사용 언어 (TypeScript, 한국어 주석 등)
- import 스타일 (named export 우선 등)
- 에러 핸들링 패턴

패키지별 Rules에는 해당 패키지에서만 쓰는 맥락만요.

- `packages/ui`라면 → 디자인 토큰 사용 규칙, Storybook 연동 컨벤션
- `packages/api`라면 → Express 미들웨어 패턴, 응답 포맷

이렇게 하면 UI 컴포넌트 작업할 때 API 핸들러 관련 Rules가 컨텍스트에 끼어드는 일이 없어요.

### `auto-attached`의 glob 패턴을 정밀하게 쓰세요

```
# ❌ 너무 넓은 범위
globs: **/*.ts

# ✅ 패키지 경계를 명확히
globs: packages/ui/**/*.tsx, apps/web/components/**/*.tsx
```

glob 패턴을 느슨하게 잡으면 의도치 않게 여러 패키지의 Rules가 동시에 붙어요. 반대로 너무 좁히면 관련 파일에서 Rules가 활성화되지 않고요. 실제로 운영해보면 패키지 디렉토리 단위로 경계를 잡는 게 가장 균형 잡힌 설정이더라고요.

---

## 컨텍스트 오버플로를 방지하는 세 가지 실전 패턴

### 패턴 1: `@docs` 참조를 Rules 내부에 넣지 마세요

많은 팀이 Rules 파일 안에 `@docs/api-spec.md`나 `@README` 같은 참조를 넣어요. 문서가 크면 이게 곧바로 컨텍스트를 잡아먹어요. 문서 참조는 작업 시점에 채팅창에서 수동으로 `@`로 호출하는 편이 훨씬 나아요.

### 패턴 2: Rules 파일 하나당 300줄 이하로 유지

Cursor 공식 권장은 아니지만, 커뮤니티에서 검증된 경험칙이 있어요. Rules 파일이 길어질수록 AI가 해당 Rules에서 실제로 적용하는 내용이 줄어드는 경향이 있어요. 300줄을 넘어가면 파일을 쪼개는 게 맞아요.

### 패턴 3: 공통 타입은 `shared` 패키지로 분리하고 Rules에서 명시

```markdown
# packages/shared Rules 예시
shared 패키지의 타입은 packages/shared/types에서만 정의해요.
다른 패키지에서 타입을 중복 정의하지 마세요.
```

이 규칙 하나로 AI가 패키지마다 비슷한 타입을 새로 만드는 패턴을 방지할 수 있어요. 중복 생성은 코드 품질 문제이기도 하지만, 컨텍스트 측면에서도 유사한 타입 정의가 여러 군데 존재하면 AI가 혼란스러워하거든요.

---

## 팀 단위로 도입할 때 주의할 점

**지금 당장 바꿔야 할 것:**
루트의 `.cursorrules` 파일을 `.cursor/rules/global.mdc`로 이전하고, `always` 타입으로 설정하되 내용을 100줄 이하로 줄이세요. 불필요한 배경 설명, 패키지 목록 나열, 아키텍처 다이어그램은 전부 제거해요.

**4~8주 안에 진행할 것:**
패키지별 `auto-attached` Rules를 순차적으로 만들어요. 한 번에 전체를 바꾸려다 보면 설정 충돌이 생겨요. 작업 빈도가 높은 패키지부터 시작하는 게 현실적이에요.

**주시할 신호:**
Cursor는 2026년 상반기 중 Rules 디버깅 뷰를 개선할 예정이에요. 어떤 Rules가 현재 요청에 포함되어 있는지 실시간으로 확인하는 기능이 추가되면, 컨텍스트 오버플로 진단이 훨씬 쉬워질 거예요.

---

## 지금 설정을 바꿔야 하는 이유

정리하면 이래요.

- 모노레포 대형 프로젝트에서 Cursor Rules 컨텍스트 오버플로는 AI 응답 품질을 절반 이하로 떨어뜨릴 수 있어요
- Rules 유형(`always`, `auto-attached`, `agent-requested`, `manual`)을 제대로 나누는 게 가장 직접적인 해법이에요
- 글로벌 Rules는 최소화하고 패키지 경계를 명확히 반영한 `auto-attached` 설정이 핵심이에요
- 팀 전체가 같은 Rules 구조를 공유해야 개인 설정 차이로 인한 AI 응답 편차도 줄어요

앞으로 6~12개월 안에 Cursor의 Rules 관리 인터페이스는 더 정교해질 거예요. 지금처럼 파일 기반으로 직접 관리하는 방식에서 GUI 기반 설정으로 진화할 가능성도 있고요. 그 전까지는 지금 소개한 계층적 Rules 설계가 현장에서 쓸 수 있는 가장 현실적인 방법이에요.

지금 쓰고 있는 `.cursorrules` 파일, 마지막으로 내용을 검토한 게 언제예요? 한 번 열어보세요. 생각보다 많은 내용이 `always`로 주입되고 있을 거예요.

## 참고자료

1. [Cursor, AI Coding #5 Rules 셋팅](https://velog.io/@artbiit/Cursor-AI-Coding-5-Rules-%EC%85%8B%ED%8C%85)
2. [Cursor 완전 가이드 2025: AI 코딩 워크플로우, rules·context 설정법 :: 쵸코쿠키의 연습장](https://jjeongil.tistory.com/3171)
3. [Cursor Project Rules가 똑똑하게 코딩을 돕는 법 — 동작 방식과 Rule 유형 정리](https://digitalbourgeois.tistory.com/1402)


---

*Photo by [Harshit Katiyar](https://unsplash.com/@harshitkatiyar) on [Unsplash](https://unsplash.com/photos/computer-code-on-a-dark-screen-with-line-numbers-CxOPZszqCQ0)*
