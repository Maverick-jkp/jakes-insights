---
title: "GitHub Actions 무료 플랜 2000분 초과 방지를 위한 캐시 전략 실전 설정"
date: 2026-05-19T22:00:19+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "GitHub Actions /ubb34/ub8cc /ud50c/ub79c 2000/ubd84 /ucd08/uacfc /ubc29/uc9c0 /uce90/uc2dc /uc804/ub7b5 /uc2e4/uc804 /uc124/uc815", "Python", "Node.js"]
description: "GitHub Actions 무료 플랜 월 2000분, 캐시 없이 npm install만 해도 회당 3~5분 소모됩니다. actions/cache로 의존성 캐시를 적용하면 설치 단계를 30초 이하로 줄여 실행 횟수를 3배 이상 확보하"
image: "/images/20260519-github-actions-무료-플랜-2000분-초과-.webp"
technologies: ["Python", "Node.js", "Docker", "GitHub Actions", "Java"]
faq:
  - question: "GitHub Actions 무료 플랜 2000분 금방 소진되는 이유"
    answer: "GitHub Actions 무료 플랜 2000분은 프라이빗 리포지토리 기준으로, Node.js 프로젝트에서 npm install 하나만 실행해도 회당 2~4분이 소요되어 하루 커밋 5회 기준 월 600~1350분이 의존성 설치에만 사용됩니다. 특히 macOS 러너는 분당 소진 배율이 10배라서, 5분짜리 워크플로우 하나가 실제로는 50분을 차감하므로 예상보다 훨씬 빠르게 할당량이 소진됩니다."
  - question: "GitHub Actions 무료 플랜 2000분 초과 방지 캐시 전략 실전 설정 방법"
    answer: "GitHub Actions 무료 플랜 2000분 초과 방지 캐시 전략 실전 설정의 핵심은 actions/cache@v4를 사용해 package-lock.json의 해시값을 키로 node_modules를 캐싱하는 것으로, 이 설정 하나만으로 의존성 설치 단계를 평균 80% 단축할 수 있습니다. Docker 빌드가 포함된 워크플로우라면 docker/build-push-action의 cache-from, cache-to 옵션을 추가로 적용하면 전체 워크플로우 시간을 70% 이상 줄일 수 있습니다."
  - question: "actions/cache npm 캐시 설정 yaml 예시"
    answer: "actions/cache를 사용한 npm 캐시 설정은 path를 ~/.npm으로 지정하고, key를 runner.os와 package-lock.json의 hashFiles 조합으로 구성하면 됩니다. package-lock.json이 변경되지 않으면 npm install이 30초 이하로 완료되며, 변경 시에는 자동으로 새 캐시를 생성합니다."
  - question: "GitHub Actions 캐시 용량 한도 및 자동 삭제 기준"
    answer: "2026년 5월 기준 GitHub Actions 캐시 용량 한도는 리포지토리당 10GB이며, 7일간 사용되지 않은 캐시는 자동으로 삭제됩니다. Docker 레이어 캐시를 mode=max로 여러 이미지에 적용하면 캐시 용량이 빠르게 소진될 수 있으므로, 용량 초과 시 가장 오래된 캐시부터 제거된다는 점을 고려해 전략을 세워야 합니다."
  - question: "GitHub Actions 무료 플랜 2000분 초과 방지 캐시 전략 실전 설정 외에 분 절약하는 방법"
    answer: "GitHub Actions 무료 플랜 2000분 초과 방지 캐시 전략 실전 설정과 함께 워크플로우 트리거 조건을 paths 필터로 좁혀 관련 파일이 변경될 때만 실행되도록 설정하면 불필요한 분 소비를 근본적으로 줄일 수 있습니다. 또한 macOS나 Windows 러너 대신 ubuntu-latest를 기본 환경으로 사용하면 동일한 작업에서 최대 10배까지 분 소진을 절감할 수 있습니다."
---

매달 말일이 다가오면 슬그머니 불안해져요. GitHub Actions 분 수가 얼마 안 남았거든요. 분명 2000분은 충분할 것 같았는데, 어느새 월말 전에 바닥이 나버리는 상황. 프라이빗 프로젝트를 혼자 또는 소규모로 운영하는 개발자라면 한 번쯤 겪어봤을 거예요.

> **핵심 요약**
> - GitHub Actions 무료 플랜은 프라이빗 리포지토리 기준 월 2000분 제공. Node.js 프로젝트에서 캐시 없이 `npm install`만 실행해도 회당 평균 3~5분 소요.
> - `actions/cache`로 의존성 캐시를 적용하면 설치 단계를 30초 이하로 줄일 수 있어, 같은 분량으로 실행 횟수를 세 배 이상 늘릴 수 있어요.
> - Docker 레이어 캐시와 빌드 아티팩트 재사용을 함께 적용하면 전체 워크플로우 시간이 70% 이상 단축된 사례가 보고되고 있어요.
> - 2026년 5월 기준, GitHub Actions 캐시 용량 한도는 리포지토리당 10GB이며 7일 미사용 시 자동 삭제돼요.

---

## 무료 플랜 2000분이 생각보다 빨리 사라지는 구조

GitHub 공식 문서 기준으로 무료 플랜은 프라이빗 리포지토리에 월 2000분을 제공해요. 퍼블릭 리포지토리는 무제한이니 해당 없고요.

문제는 이 2000분이 생각보다 허술하게 쓰인다는 점이에요.

전형적인 Node.js 프로젝트를 예로 들면, 워크플로우 하나에 이런 단계가 있어요.

1. `actions/checkout` — 약 10~20초
2. `npm install` — **평균 2~4분**
3. 테스트 실행 — 1~3분
4. 빌드 — 1~2분

합치면 회당 4~9분이에요. 하루에 커밋 다섯 번 하면? 20~45분. 한 달이면 600~1350분이 의존성 설치 하나에 들어가는 셈이에요. 2000분의 절반 이상이 `npm install` 기다리는 데 쓰이는 거죠.

그게 전부가 아니에요. GitHub Actions는 러너마다 분당 소진 배율이 달라요.

- `ubuntu-latest`: 1배 (기준)
- `windows-latest`: **2배**
- `macos-latest`: **10배**

macOS에서 5분짜리 워크플로우 하나를 돌리면 50분이 사라져요. 이 사실을 모르고 macOS 환경에서 iOS 빌드를 자주 트리거한 팀이 첫 주에 월 할당량을 다 써버린 사례가 실제로 있어요. 놀랍죠?

---

## 캐시 전략 실전: `actions/cache` 기초부터 제대로

### 의존성 캐시 — 가장 먼저 적용해야 할 것

`actions/cache`는 GitHub에서 공식 제공하는 캐시 액션이에요. 핵심 원리는 단순해요. `package-lock.json`의 해시값을 키로 캐시를 저장해두고, 다음 실행 때 키가 동일하면 저장된 `node_modules`를 그냥 꺼내 쓰는 거예요.

```yaml
- name: Cache node_modules
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

`package-lock.json`이 바뀌지 않으면 `npm install`은 수십 초 이하로 끝나요. 바뀌면 새 캐시를 만들고요. 이 설정 하나만 적용해도 반복 실행 기준 설치 단계가 평균 80% 빨라지는 걸 확인할 수 있어요.

Python이라면 `pip` 캐시, Java라면 Maven이나 Gradle 캐시 경로로 바꾸면 돼요. 언어마다 경로만 다를 뿐 구조는 같아요.

### Docker 레이어 캐시 — 빌드가 느린 팀에게

컨테이너 이미지를 빌드하는 워크플로우라면 Docker 레이어 캐시가 훨씬 크게 작용해요. `docker/build-push-action`의 `cache-from`, `cache-to` 옵션을 쓰면 GitHub Actions의 캐시 스토어를 Docker 빌드 캐시로 활용할 수 있어요.

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

`mode=max`는 중간 레이어까지 모두 캐시하는 옵션이에요. 초기 빌드 시간은 같지만, 두 번째부터는 변경된 레이어만 다시 빌드해요. Dockerfile이 잘 짜여 있다면 5분짜리 빌드가 40초 안으로 들어오는 경우도 있어요.

### 전략별 비교: 어떤 캐시를 언제 써야 할까?

| 캐시 유형 | 적용 대상 | 평균 단축 효과 | 설정 난이도 | 캐시 용량 소비 |
|-----------|-----------|----------------|-------------|----------------|
| `actions/cache` (npm) | Node.js 프로젝트 | 60~80% | 낮음 | 100~500MB |
| `actions/cache` (pip) | Python 프로젝트 | 50~70% | 낮음 | 50~300MB |
| Docker GHA 캐시 | 컨테이너 빌드 | 70~90% | 중간 | 1~5GB |
| 빌드 아티팩트 재사용 | 모노레포, 멀티잡 | 40~60% | 중간 | 가변 |
| Self-hosted runner | 대용량, 반복 빌드 | 분 소진 0 | 높음 | N/A |

캐시 용량 한도가 리포지토리당 10GB라는 점은 기억해두세요. Docker 캐시를 `mode=max`로 여러 이미지에 걸어두면 용량이 빠르게 차오를 수 있어요. 오래된 캐시는 7일 뒤 자동 삭제되니 크게 걱정할 필요는 없지만, 용량이 초과되면 오래된 것부터 밀려나요.

---

## 분 소진을 줄이는 추가 패턴 세 가지

### 트리거 조건 좁히기

캐시보다 근본적인 방법이 있어요. 워크플로우가 필요할 때만 돌게 만드는 거예요.

```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'package.json'
```

`docs/` 폴더만 수정했을 때 테스트 전체가 도는 건 낭비예요. `paths` 필터로 트리거 조건을 좁히면 불필요한 실행 자체를 막을 수 있어요. 의외로 여기서 효과가 가장 크게 나오는 경우가 많아요.

### 잡 분리와 `needs` 체이닝

긴 워크플로우를 여러 잡으로 쪼개고, 앞 잡이 실패하면 뒷 잡을 건너뛰게 하면 헛돌리는 분을 줄여요. 테스트가 실패했는데 빌드와 배포까지 돌리는 건 그냥 시간 낭비거든요.

### `concurrency` 옵션으로 중복 실행 막기

PR에 커밋을 빠르게 푸시하면 이전 워크플로우가 끝나기 전에 새 것이 시작돼요. `concurrency` 옵션을 쓰면 같은 브랜치의 이전 실행을 자동으로 취소해요.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

이 세 가지만 잘 조합해도 월 소진량이 절반 수준으로 내려오는 팀이 적지 않아요.

---

## 2026년 하반기, 무엇을 지켜봐야 할까

**지금 당장 할 것:**
- `actions/cache@v4`로 의존성 캐시 적용
- `paths` 트리거 필터 설정
- `concurrency` 옵션 추가

**3~6개월 내 고려할 것:**
- 분 소진이 월 1500분 이상이라면 유료 플랜(Team, $4/유저/월) 전환 비용과 비교해볼 만해요. 개인 개발자 기준으로는 유료 전환보다 캐시 정비가 훨씬 저렴한 경우가 많아요.
- Self-hosted runner는 보안 하드닝이 선행돼야 해요. 편하게 도입했다가 보안 문제가 생기는 팀이 실제로 있거든요.

**지켜볼 신호:**
- GitHub이 2026년 하반기 Actions 요금 체계를 조정할 가능성이 있어요. 공식 changelog를 주기적으로 확인하세요.

---

결국 핵심은 단순해요.

- **캐시로 반복 작업을 없애고**
- **트리거를 좁혀서 불필요한 실행을 막고**
- **중복 실행은 자동으로 취소**

이 세 가지를 적용하고 나면 2000분이 "왜 이렇게 부족하지?"에서 "이게 왜 부족했지?"로 바뀔 거예요.

지금 쓰는 워크플로우 중 캐시가 없는 게 몇 개인지 한번 세어보세요. 거기서 시작하면 돼요.

## 참고자료

1. [GitHub Actions Self-Hosted Runner 대규모 운영과 보안 하드닝 가이드 | Chaos and Order](https://www.youngju.dev/blog/devops/2026-03-05-devops-github-actions-self-hosted-runner-ops)
2. [Supabase 무료 플랜, 2주면 잠든다? GitHub Actions로 자동 깨우는 법 - 비개발자 하랑의 AI 풀스택 도전기](https://lookfortaste.com/supabase-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C-2%EC%A3%BC%EB%A9%B4-%EC%9E%A0%EB%93%A0%EB%8B%A4-github-actions%EB%A1%9C-%EC%9E%90%EB%8F%99-%EA%B9%A8%EC%9A%B0%EB%8A%94-%EB%B2%95/)
3. [GitHub Actions CI/CD 완벽 가이드, YAML 문법부터 자동 배포까지](https://itgenius.tistory.com/167)


---

*Photo by [Ferenc Almasi](https://unsplash.com/@flowforfrank) on [Unsplash](https://unsplash.com/photos/a-computer-screen-with-a-bunch-of-buttons-on-it--FHIdRVGets)*
