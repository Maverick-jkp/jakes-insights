---
title: "Tailwind CSS 한계와 시맨틱 CSS 전환, Julia Evans 사례로 보는 실전 교훈"
date: 2026-05-17T20:09:39+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "tailwind", "css", "/uc2dc/ub9e8/ud2f1", "React"]
description: "Tailwind CSS 한계를 직접 겪은 Julia Evans가 2026년 5월 시맨틱 CSS로 전환한 실제 이유. 클래스 가독성 저하와 디버깅 복잡도 문제, 유틸리티 퍼스트 방식의 규모별 트레이드오프를"
image: "/images/20260517-tailwind-css-한계-시맨틱-css-전환-실전.webp"
technologies: ["React", "Next.js", "Tailwind CSS", "Vite", "Cursor"]
faq:
  - question: "Tailwind CSS 쓰다가 코드 유지보수 힘든 이유"
    answer: "Tailwind CSS는 컴포넌트 수가 50개를 넘기 시작하면 클래스 무더기 문제가 본격화되어 HTML이 구조가 아닌 스타일 명세서로 변해버립니다. 조건부 스타일이 여러 컴포넌트에 중첩되면 DevTools 없이는 어떤 클래스가 실제 적용되는지 추적이 어렵고, 유지보수 기간이 길어질수록 시맨틱 CSS 방식과의 비용 차이가 눈에 띄게 벌어집니다."
  - question: "Tailwind CSS 한계 시맨틱 CSS 전환 실전 실제 경험 후기"
    answer: "Julia Evans는 2026년 5월 Tailwind CSS 한계 시맨틱 CSS 전환 실전 경험을 블로그에 공유하며, 클래스 이름 가독성 저하와 디버깅 복잡도를 주요 이유로 꼽았습니다. 그녀는 별도 프레임워크 없이 순수 CSS 파일을 컴포넌트 단위로 분리하고 명확한 이름 규칙을 적용하는 방식으로 전환했으며, 그 결과 스타일 수정 시 추적이 훨씬 쉬워졌다고 밝혔습니다."
  - question: "shadcn ui Vite React 환경에서 스타일 깨지는 문제 해결법"
    answer: "shadcn/ui는 Tailwind 기반 컴포넌트 라이브러리로, Vite + React 환경에서 content 경로 미스매치, PostCSS 플러그인 순서, purge 설정 문제가 얽히면 스타일이 통째로 사라지는 현상이 반복적으로 보고되고 있습니다. 근본적인 해결을 위해서는 Tailwind 설정 파일의 content 경로를 정확히 맞추거나, 빌드 의존성이 낮은 vanilla CSS 또는 CSS Modules 방식으로 전환을 고려해야 합니다."
  - question: "Tailwind CSS 한계 시맨틱 CSS 전환 실전 언제 해야 하나"
    answer: "Tailwind CSS 한계 시맨틱 CSS 전환 실전을 고려해야 할 시점은 컴포넌트가 50개를 넘거나 팀 규모가 커지기 시작할 때입니다. 시맨틱 CSS 방식은 초기 설계 비용이 높지만 중대형 팀과 장기 서비스에서 유리하며, 초기에 CSS 구조에 투자한 팀이 6개월 뒤 유지보수 시간에서 큰 차이를 냅니다."
  - question: "Tailwind CSS 빌드 오류 프로덕션 스타일 사라지는 이유"
    answer: "Tailwind CSS는 빌드 도구와 강하게 결합되어 있어 content 경로 설정 하나가 틀리면 프로덕션 빌드에서 스타일이 통째로 사라지는 문제가 발생합니다. Vite 버전 업그레이드나 모노레포 구조 변경 후 스타일이 깨지는 사례가 GitHub에서 수십 건씩 보고되고 있으며, vanilla CSS나 CSS Modules를 사용했다면 이런 빌드 의존성 문제 자체가 발생하지 않습니다."
---

Tailwind CSS를 쓰다가 "이거 뭔가 아닌데"라는 느낌, 받은 적 있죠? Julia Evans가 2026년 5월 자신의 블로그에 올린 글이 개발자 커뮤니티에서 꽤 큰 반향을 일으키고 있어요. 수년간 Tailwind를 써온 베테랑 개발자가 직접 손으로 CSS를 구조화하는 방향으로 돌아간 이유, 그리고 그 과정에서 배운 것들. 단순한 개인 경험담이 아니에요. 2026년 현재 프론트엔드 생태계 전체에 질문을 던지고 있거든요.

> **핵심 요약**
> - Julia Evans는 2026년 5월 Tailwind CSS를 떠나 직접 구조화한 시맨틱 CSS로 전환했으며, 가장 큰 이유로 **클래스 이름 가독성 저하와 디버깅 복잡도**를 꼽았어요.
> - Tailwind의 유틸리티 퍼스트 방식은 소규모 프로젝트에서 빠른 개발을 가능하게 하지만, 컴포넌트 수가 50개를 넘기 시작하면 클래스 무더기 문제가 본격화돼요.
> - 시맨틱 CSS 방식은 초기 설계 비용이 높지만 장기 유지보수성과 팀 협업 측면에서 일관되게 유리해요.
> - shadcn/ui처럼 Tailwind 기반 컴포넌트 라이브러리는 Vite + React 환경에서 스타일이 깨지는 이슈가 꾸준히 보고되고 있어요. Tailwind 의존성 자체가 리스크가 될 수 있다는 거죠.

---

## Tailwind가 "유행"이 된 배경

Tailwind CSS는 2019년 v1.0 출시 이후 빠르게 주류로 올라섰어요. 2023년 State of CSS 설문 기준으로 사용률 약 46%, 만족도 약 79%를 기록하며 CSS 프레임워크 중 압도적 1위를 차지했죠.

이유는 단순해요. 클래스만 붙이면 바로 스타일이 나오니까요. CSS 파일 따로 안 만들어도 되고, 이름 짓는 고민도 줄어들고, BEM이나 SMACSS 같은 방법론 없이도 빠르게 결과물이 나와요.

React 생태계와도 찰떡처럼 맞아떨어졌어요. 컴포넌트 단위 개발 방식과 유틸리티 클래스 조합이 자연스럽게 느껴졌고, Next.js 공식 스타터에도 Tailwind가 기본으로 포함됐어요.

그런데 2025년 하반기부터 분위기가 달라졌어요. shadcn/ui가 폭발적으로 퍼지면서 의도치 않은 문제도 함께 따라왔거든요. GitHub 이슈 트래커에는 "Vite + React 환경에서 shadcn 컴포넌트가 스타일 없이 렌더링된다"는 보고가 꾸준히 쌓였어요. Tailwind 설정 파일 경로 미스매치, PostCSS 플러그인 순서, purge 설정 문제가 얽히면서 환경이 조금만 달라지면 스타일이 통째로 날아가는 현상이 반복됐죠.

---

## 실전에서 드러난 Tailwind의 세 가지 벽

**#1 클래스 폭발: HTML이 CSS가 되는 순간**

Tailwind의 철학은 "CSS 파일을 줄여라"예요. 그런데 실제 코드베이스를 보면 얘기가 달라요.

```html
<button class="flex items-center justify-center px-4 py-2 bg-blue-500 
  hover:bg-blue-600 text-white text-sm font-medium rounded-md shadow-sm 
  disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200">
```

버튼 하나에 클래스가 열 개 넘어요. 버튼이 스무 개면요? Julia Evans가 지적한 핵심도 바로 이거예요. HTML이 구조가 아니라 스타일 명세서가 되어버린다는 것. 수정할 때 어떤 클래스를 지워야 할지 헷갈리기 시작해요.

**#2 디버깅 비용이 선형으로 늘어나지 않는다**

작은 프로젝트에서는 괜찮아요. 그런데 컴포넌트 수가 늘고 조건부 스타일이 쌓이면 얘기가 달라져요. `cn('px-4', isActive && 'bg-blue-500', isDisabled && 'opacity-50')` 같은 패턴이 여러 컴포넌트에 걸쳐 중첩되면, 특정 상태에서 어떤 클래스가 실제로 적용되는지 DevTools 없이는 추적이 정말 어렵거든요.

시맨틱 CSS라면 `.button--active` 하나만 찾으면 되는데, Tailwind 방식에서는 클래스 조합 로직 전체를 따라가야 해요. 유지보수 기간이 길어질수록 이 비용 차이가 눈에 띄게 벌어져요.

**#3 빌드 설정 의존성이 만들어내는 취약점**

Tailwind는 빌드 도구와 강하게 결합돼 있어요. `content` 경로 설정 하나가 틀리면 프로덕션 빌드에서 스타일이 통째로 사라지는 일이 생겨요. GitHub shadcn-ui 토론 스레드를 보면, Vite 버전 업그레이드나 모노레포 구조 변경 후 스타일이 깨지는 사례가 수십 건씩 보고됐어요. vanilla CSS나 CSS Modules 방식이었다면 이런 빌드 의존성 문제 자체가 발생하지 않았을 거예요.

---

## Tailwind vs 시맨틱 CSS: 어디에 무엇을 쓸까

| 기준 | Tailwind CSS | 시맨틱 CSS (BEM/CSS Modules) | CSS-in-JS |
|------|-------------|------------------------------|-----------|
| 초기 개발 속도 | ⚡ 빠름 | 🐢 느림 (설계 필요) | 중간 |
| 장기 유지보수 | ⚠️ 클래스 누적 부담 | ✅ 추적 쉬움 | 중간 |
| 빌드 의존성 | 높음 | 낮음 | 중간~높음 |
| 디버깅 용이성 | 클래스 많아지면 어려움 | ✅ 클래스 이름으로 즉시 추적 | 중간 |
| **적합한 팀** | 1-3인 소형, 빠른 프로토타입 | 중대형 팀, 장기 서비스 | React 헤비 팀 |

트레이드오프가 명확해요. Tailwind는 "빠르게 시작해서 빠르게 보여주는" 상황에서 여전히 강해요. 반면 서비스가 커지고 팀이 성장할수록, 초기에 CSS 구조를 잘 짜는 데 투자한 팀이 6개월 뒤 유지보수 시간에서 큰 차이를 내요.

Julia Evans가 선택한 방식은 CSS 파일을 컴포넌트 단위로 분리하고 명확한 이름 규칙을 적용하는 것이었어요. 별도 프레임워크 없이 순수 CSS로. 그 결과, 스타일 수정할 때 무엇을 찾아야 할지 바로 알 수 있게 됐다고 해요.

---

## 언제, 어떻게 전환할까: 세 가지 시나리오

**시나리오 A — 신규 프로젝트라면**
팀 규모와 서비스 수명 예측이 먼저예요. MVP를 두 달 안에 내야 한다면 Tailwind가 여전히 빠른 선택이에요. 그런데 2년 이상 운영할 서비스라면, 설계 단계에서 CSS 구조를 잡는 데 1-2주를 투자하는 게 장기적으로 훨씬 이득이에요.

**시나리오 B — 기존 Tailwind 코드베이스가 있다면**
전체 마이그레이션은 리스크가 커요. 가장 현실적인 접근은 신규 컴포넌트부터 시맨틱 방식으로 만들고, 리팩토링 여유가 생길 때 기존 컴포넌트를 하나씩 교체하는 거예요. 점진적 전환이 핵심이에요.

**시나리오 C — shadcn/ui 같은 라이브러리를 쓰고 있다면**
빌드 설정 문제가 반복된다면 Tailwind의 `content` 경로 설정을 먼저 점검하세요. 그래도 반복된다면, 핵심 컴포넌트는 직접 CSS로 교체하는 선택지도 있어요. 디자인 시스템을 자체 구축 중이라면 외부 라이브러리 의존도를 낮추는 게 더 건강한 방향이에요.

---

## 앞으로 6개월, 뭘 주시해야 할까

지금 이 논의가 활발한 건 단순한 유행의 반전이 아니에요. 몇 가지 흐름을 주시할 필요가 있어요.

- **Tailwind v4 방향성**: CSS 변수 방식으로 테마를 관리하는 방향으로 가고 있는데, 시맨틱 CSS의 장점을 일부 흡수하려는 시도로 볼 수 있어요.
- **CSS Layers의 부상**: 브라우저 네이티브 `@layer` 지원이 안정화되면서 Tailwind 없이도 스타일 우선순위를 체계적으로 관리할 수 있게 됐어요.
- **컴포넌트 라이브러리 전쟁**: shadcn/ui 인기가 지속되는 한 Tailwind 의존 스타일 이슈도 함께 가요. 반면 Radix UI + 자체 CSS 조합을 택하는 팀도 늘고 있어요.

결국 질문은 하나예요. 지금 내 프로젝트에서 CSS 때문에 시간을 얼마나 쓰고 있나요? 그 시간이 예상보다 많다면, 시맨틱 CSS 전환을 직접 경험해볼 때가 된 거예요. Julia Evans처럼 작은 컴포넌트 하나부터 시작해도 충분해요. 어떤 방식이 더 잘 맞는지는 결국 코드베이스가 답해줄 거거든요.

## 참고자료

1. [Moving away from Tailwind, and learning to structure my CSS](https://jvns.ca/blog/2026/05/15/moving-away-from-tailwind--and-learning-to-structure-my-css-/)
2. [How to fix shadcn/ui components rendering without styles in a Vite + React project? · shadcn-ui/ui ·](https://github.com/shadcn-ui/ui/discussions/10595)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-working-at-a-desk-in-a-cozy-home-office-rIPVJ6dMOPI)*
