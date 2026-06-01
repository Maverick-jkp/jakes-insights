---
title: "GitHub Actions 모노레포 선택적 빌드: paths-filter 실전 설정과 삽질 기록"
date: 2026-05-31T20:48:17+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "/ubaa8/ub178/ub808/ud3ec", "GitHub Actions"]
description: "GitHub Actions 모노레포에서 dorny/paths-filter로 변경된 패키지만 선택적 빌드하는 실전 설정법. CI 시간 70% 단축 가능하지만 공식 문서엔 없는 삽질 포인트를 짚어드립니다."
image: "/images/20260531-github-actions-모노레포-변경된-패키지만-선.webp"
technologies: ["GitHub Actions"]
faq:
  - question: "GitHub Actions 모노레포 변경된 패키지만 선택적 빌드 paths-filter 실전 설정 삽질 기록 어디서 볼 수 있나요"
    answer: "GitHub Actions 모노레포 변경된 패키지만 선택적 빌드 paths-filter 실전 설정 삽질 기록은 dorny/paths-filter 액션을 활용한 CI 최적화 경험을 정리한 글로, 경로 패턴 오류·공유 패키지 의존성 처리·빈 매트릭스 에러 등 세 가지 핵심 삽질 포인트를 다루고 있어요. 이 설정을 제대로 적용하면 평균 CI 시간을 70% 이상 단축할 수 있다고 소개하고 있습니다."
  - question: "dorny/paths-filter 경로 설정했는데 변경 감지가 안 되는 이유"
    answer: "경로 패턴 끝에 `/**`를 빠뜨린 경우가 가장 흔한 원인이에요. `apps/web`이라고 쓰면 해당 파일 자체의 변경만 감지하고, 디렉터리 내부 변경은 잡지 못하기 때문에 반드시 `apps/web/**` 형태로 작성해야 합니다. `apps/web/*`은 한 단계 아래만 감지하므로 깊은 경로 변경도 놓칠 수 있어요."
  - question: "모노레포 공유 패키지 수정했을 때 의존하는 앱도 같이 빌드하려면"
    answer: "dorny/paths-filter는 파일 변경만 감지하고 패키지 간 의존 관계는 알지 못해요. 각 앱의 필터 설정에 해당 앱이 의존하는 공유 패키지 경로를 함께 명시하는 방식으로 해결할 수 있어요. 예를 들어 web 앱 필터에 `apps/web/**`과 `packages/ui/**`를 같이 넣으면, UI 패키지 변경 시에도 web 빌드가 트리거됩니다."
  - question: "GitHub Actions matrix 빈 배열일 때 워크플로우 에러 해결 방법"
    answer: "변경된 패키지가 없을 때 매트릭스 값이 빈 배열이 되면 GitHub Actions는 이를 에러로 처리해요. 잡 실행 조건에 `if: matrix_value != '[]'` 형태의 조건을 추가해서 빈 매트릭스 상황을 미리 걸러내야 합니다. 이 한 줄을 빠뜨리면 실제 변경 없는 커밋에서 워크플로우 전체가 실패하는 문제가 생겨요."
  - question: "모노레포 패키지 몇 개 이상이면 Turborepo paths-filter 같이 써야 하나요"
    answer: "GitHub Actions 모노레포 변경된 패키지만 선택적 빌드 paths-filter 실전 설정 삽질 기록에 따르면 패키지 5개 이하는 paths-filter 단독으로 충분하고, 5~20개 규모부터 Turborepo와 조합하는 것을 권장해요. 20개 이상이라면 Nx의 affected 명령어와 원격 캐시까지 활용하는 방식이 적합하며, 동일 커밋의 두 번째 빌드가 거의 즉시 완료될 수 있습니다."
---

모노레포에 패키지가 열다섯 개 있는데, 버튼 색상 하나 바꿨더니 전체 빌드가 돌아간 적 있죠? CI 시간 20분, 비용은 그대로 낭비. 대형 프론트엔드 팀의 절반 이상이 모노레포 구조를 쓰고 있는데, 선택적 빌드를 제대로 설정한 곳은 훨씬 적어요.

`dorny/paths-filter` 액션 하나로 이 문제를 꽤 깔끔하게 잡을 수 있어요. 근데 공식 문서만 보고 따라 하면 반드시 한 번은 막히는 지점들이 있거든요. 이 글은 그 삽질 포인트를 중심으로 정리한 실전 기록이에요.

> **핵심 요약**
> - `dorny/paths-filter`를 쓰면 변경된 패키지만 골라 빌드할 수 있어서, 평균 CI 시간을 70% 이상 단축할 수 있어요 (패키지 수 기준 선형 감소).
> - `filters` 설정에서 경로 패턴을 잘못 쓰면 모든 잡이 항상 실행되는 함정에 빠져요 — 경로 끝의 `/**` 유무가 결정적이에요.
> - 공유 패키지(`packages/ui`, `packages/utils` 등) 변경 시 의존 앱 전체를 트리거하는 로직은 별도로 설계해야 해요.
> - `matrix` 전략과 조합하면 병렬 빌드도 가능하지만, 빈 매트릭스 처리를 빠뜨리면 워크플로우가 에러로 멈춰요.

---

## 왜 지금 모노레포 선택적 빌드인가

모노레포는 사실상 표준이 됐어요. Nx, Turborepo, pnpm workspaces 조합이 워낙 성숙해졌고, 팀 규모가 커질수록 코드 공유 비용이 멀티레포보다 훨씬 낮거든요.

문제는 CI예요. 패키지 하나를 고치면 전체 파이프라인이 돌아가는 구조라면, 팀이 10명만 넘어도 GitHub Actions 비용이 꽤 나와요. 리눅스 런너는 분당 $0.008인데, 열다섯 개 패키지가 각각 10분씩 빌드하면 커밋 하나에 $1.20이에요. 하루 커밋이 20개면 월 $720. 작은 숫자가 아니죠.

그래서 "변경된 패키지만 빌드"가 핵심 과제가 됐어요. Turborepo의 `--filter` 플래그나 Nx의 `affected` 명령어가 로컬에선 잘 작동하는데, GitHub Actions와 붙이는 순간 경로 감지 로직을 직접 짜야 해요. 여기서 `dorny/paths-filter`가 등장하는 거고요.

GitHub Actions 자체에 `on.push.paths` 옵션이 있긴 해요. 근데 이건 워크플로우 단위 트리거 조건이라, 여러 패키지를 동시에 조건부로 빌드하는 데는 안 맞아요. 결국 잡 레벨에서 필터링하는 `paths-filter`가 필요한 이유가 여기에 있어요.

---

## 기본 설정과 삽질 포인트 세 가지

`paths-filter`의 기본 구조는 단순해요.

```yaml
- uses: dorny/paths-filter@v3
  id: filter
  with:
    filters: |
      web:
        - 'apps/web/**'
      dashboard:
        - 'apps/dashboard/**'
      ui:
        - 'packages/ui/**'
```

이후 잡에서 `if: steps.filter.outputs.web == 'true'`로 조건을 걸면 돼요. 개념은 단순한데, 실제로 쓰다 보면 세 지점에서 꼭 막혀요.

### 삽질 #1: 경로 패턴 끝의 `/**` 빠뜨리기

`apps/web`이라고 쓰면 정확히 그 파일이 변경될 때만 트리거해요. 디렉터리 안의 변경을 잡으려면 `apps/web/**`이 필요해요. `apps/web/*`은 딱 한 단계 아래만 잡으니까, 깊은 디렉터리 변경을 놓치는 함정이 생기고요. 분명히 설정했는데 안 걸린다 싶으면, 대부분 여기서 막힌 거예요.

### 삽질 #2: 공유 패키지 변경 시 의존 앱 트리거

`packages/ui`를 고치면 그걸 쓰는 앱들도 다시 빌드해야 해요. 근데 `paths-filter`는 파일 변경만 보거든요. 의존 관계는 몰라요. 해결책은 각 앱 필터에 의존하는 공유 패키지 경로를 같이 넣는 거예요.

```yaml
filters: |
  web:
    - 'apps/web/**'
    - 'packages/ui/**'
    - 'packages/utils/**'
  dashboard:
    - 'apps/dashboard/**'
    - 'packages/ui/**'
```

약간 중복 설정이 생기지만, 명시적이라서 관리하기가 오히려 편해요.

### 삽질 #3: 빈 매트릭스 처리

변경된 패키지 목록을 동적으로 만들어서 `matrix`에 넘기는 패턴을 많이 써요. 아무것도 안 바뀐 경우엔 매트릭스가 빈 배열이 되고, GitHub Actions는 빈 매트릭스를 에러로 처리해요. `if: ... != '[]'` 조건이 없으면 워크플로우 전체가 실패해요. 빠뜨리기 쉬운 한 줄이에요.

---

## 접근 방식 비교: 세 가지 선택지

| 방식 | 설정 복잡도 | 정밀도 | 의존성 처리 | 적합한 규모 |
|------|-----------|--------|------------|-----------|
| `paths-filter` 단독 | 낮음 | 중간 | 수동 명시 | 패키지 5개 이하 |
| Turborepo + `paths-filter` | 중간 | 높음 | 자동 | 5~20개 |
| Nx affected + `paths-filter` | 높음 | 매우 높음 | 자동 + 증분 캐시 | 20개 이상 |

Turborepo와 `paths-filter` 조합은 꽤 깔끔해요. `paths-filter`로 변경된 패키지를 감지하고, `turbo run build --filter=web...`처럼 넘기면 Turborepo가 의존 그래프를 타고 필요한 것만 실행해요. Nx는 설정 비용이 크지만, 원격 캐시까지 붙으면 같은 커밋의 두 번째 빌드는 거의 즉시 끝나요.

패키지 다섯 개 이하라면 `paths-filter` 단독으로 충분해요. 그 이상이면 Turborepo 조합을 먼저 고려하세요.

---

## 실제 적용할 때 챙겨야 할 것들

**PR 기준 diff를 명확히 설정하세요.** `paths-filter`는 기본으로 `HEAD~1`과 현재 커밋을 비교해요. PR에서 쓸 때는 `base` 옵션으로 타깃 브랜치를 명시해야 정확한 변경 범위가 나와요.

**`push`와 `pull_request` 이벤트를 분리하세요.** `push`는 직전 커밋과 비교하고, `pull_request`는 베이스 브랜치와 비교해요. 같은 설정이 두 이벤트에서 다르게 동작하는 이유가 여기에 있어요.

**루트 설정 파일 변경은 전체 빌드를 트리거하도록 별도로 두세요.** `package.json`, `turbo.json`, `.github/workflows/**` 변경은 모든 패키지 필터에 포함시키거나, 별도 잡으로 "전체 빌드" 경로를 열어두는 게 안전해요.

---

## 지금 당장 시작한다면

세 단계로 정리해요.

1. `dorny/paths-filter@v3`를 `detect-changes` 잡으로 분리하고, 현재 패키지 구조에 맞게 필터 경로 작성
2. 각 빌드 잡에 `needs: detect-changes`와 `if` 조건 추가
3. 공유 패키지 경로를 의존 앱 필터에 명시적으로 추가

복잡한 의존 그래프가 있다면 이 시점에 Turborepo 도입을 같이 검토해보세요. `paths-filter`로 변경 감지를 하고, Turborepo로 의존성 추적을 맡기면 두 도구의 역할이 명확히 나뉘어요.

CI 시간과 비용을 잡는 가장 빠른 방법은 불필요한 빌드를 아예 안 도는 거예요. 설정 한 번에 매 커밋마다 아끼는 시간이 쌓이니까요. 여러분 팀 모노레포엔 지금 몇 개의 패키지가 매번 불필요하게 빌드되고 있을까요?

## 참고자료

1. [GitHub Action - 나무위키](https://namu.wiki/w/GitHub%20Action)
2. [[DevOps 삽질일지] Vercel Hobby + Private Repo로 모노레포 배포하기 — 커밋심는 정원](https://highgarden.tistory.com/35)
3. [GitHub Actions CI/CD 완전 정복: Go 빌드부터 브랜치 전략, 자동 배포까지 | Chaos and Order](https://www.youngju.dev/blog/culture/2026-03-23-github-actions-cicd-go-build-branch-strategy-guide)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
