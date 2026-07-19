---
title: "GitHub Actions Docker 레이어 캐시 무효화 원인 분석과 빌드 시간 단축 실전 설정"
date: 2026-04-17T20:18:23+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "docker", "GitHub Actions"]
description: "GitHub Actions에서 COPY . . 위치 하나로 500MB 레이어가 재빌드되고 빌드 시간이 3배 늘어나는 이유와, cache-type=gha 설정으로 레이어 캐시를 유지해 8분 빌드를 단축하는 실전 방법을 설명"
image: "/images/20260417-github-actions-docker-레이어-캐시-무.webp"
technologies: ["Docker", "GitHub Actions", "Go"]
faq:
  - question: "GitHub Actions Docker 빌드 매번 처음부터 다시 시작되는 이유"
    answer: "GitHub Actions의 hosted runner는 매 실행마다 새 VM에서 시작되기 때문에 이전 빌드의 Docker 레이어 캐시가 전부 사라져요. 이를 해결하려면 docker/build-push-action에 cache-from과 cache-to 설정을 추가해 GitHub Actions Cache API나 컨테이너 레지스트리에 캐시를 저장해야 해요."
  - question: "GitHub Actions Docker 레이어 캐시 무효화 원인 분석 빌드 시간 단축 실전 설정 방법"
    answer: "캐시 무효화의 가장 흔한 원인은 Dockerfile에서 COPY . . 명령어가 의존성 설치 전에 위치한 경우로, 소스 파일이 조금만 바뀌어도 이후 모든 레이어가 재실행돼요. 해결책은 변경 빈도가 낮은 레이어(package.json 복사 및 npm ci)를 위쪽에, 소스 파일 복사를 아래쪽에 배치하고 cache-type=gha 옵션을 워크플로에 추가하는 거예요."
  - question: "Dockerfile COPY 순서 바꾸면 빌드 속도 얼마나 빨라지나요"
    answer: "package.json만 먼저 복사해 npm ci를 실행하고 그 다음에 소스 파일을 COPY하는 구조로 바꾸면, 의존성이 변경되지 않는 한 npm ci 레이어는 캐시를 그대로 재사용해요. 실제로 이 레이어 순서 재배치만으로 빌드 시간이 절반 수준으로 줄어드는 경우가 많다고 알려져 있어요."
  - question: "docker/build-push-action cache-type gha mode=max 차이점"
    answer: "mode=min은 최종 이미지 레이어만 캐시에 저장하고, mode=max는 빌드 중간 레이어까지 전부 저장해요. 멀티스테이지 빌드처럼 중간 스테이지가 많은 경우에는 mode=max를 써야 캐시 히트율이 높아지고 빌드 시간 단축 효과를 제대로 누릴 수 있어요."
  - question: "GitHub Actions Docker 레이어 캐시 무효화 원인 분석 없이 빌드 시간 줄이는 법 있나요"
    answer: "원인 분석 없이 무작정 캐시를 추가해도 Dockerfile 레이어 순서가 잘못돼 있으면 효과가 거의 없어요. COPY . . 위치처럼 캐시를 깨뜨리는 근본 원인을 먼저 파악한 뒤 cache-type=gha 설정을 함께 적용하는 것이 빌드 시간 단축에 가장 확실한 방법이에요."
aliases:
  - "/tech/2026-04-17-github-actions-docker-레이어-캐시-무효화-원인-분석-빌드-시간-단축-실전/"

---

PR 하나 올릴 때마다 8분씩 기다린 적 있어요? `COPY . .` 한 줄 때문에 500MB 레이어가 통째로 재빌드되고 있었던 거예요. 원인을 알면 고치는 건 10분이면 돼요.

---

> **핵심 요약**
> - GitHub Actions에서 Docker 빌드 캐시가 무효화되는 가장 흔한 원인은 `COPY . .` 명령어의 위치로, 소스 파일 변경 시 이후 모든 레이어가 강제 재실행된다.
> - `cache-from` / `cache-to` 설정 없이 Actions 워크플로를 구성하면 러너가 새로 뜰 때마다 캐시 레이어가 0에서 시작되어 평균 빌드 시간이 세 배 이상 늘어난다.
> - `docker/build-push-action`에 `cache-type=gha`를 적용하면 레이어 캐시를 Actions Cache API에 저장해 재사용율을 높일 수 있다.
> - Dockerfile 레이어 순서를 "변경 빈도 낮은 것 → 높은 것" 순으로 재배치하면 캐시 히트율이 크게 오르고 빌드 시간이 절반 수준으로 줄어드는 경우가 많다.

---

## 1. 캐시 무효화, 지금 왜 다시 문제가 되냐면요

CI/CD 파이프라인 비용이 다시 도마에 올랐어요. GitHub Actions 무료 플랜은 월 2,000분이 상한선이고, 유료 플랜도 분당 과금이에요. 팀 규모가 커질수록 "이 PR이 왜 10분짜리 빌드를 트리거하는 거지?"라는 질문이 자연스럽게 나오죠.

문제는 대부분의 팀이 Dockerfile을 처음 한 번 작성한 뒤로 거의 손대지 않는다는 점이에요. 레이어 순서가 엉망이어도, 캐시 설정이 빠져 있어도 "일단 빌드는 되니까" 그냥 두는 경우가 많아요.

GitHub 공식 문서(2025년 업데이트 기준)에 따르면 `docker/build-push-action`의 `cache-type=gha` 옵션은 2023년 GA로 전환됐는데, 아직 이 설정을 모르거나 적용하지 않은 팀이 꽤 많아요.

이 글에서 다루는 핵심은 세 가지예요.

- 레이어 캐시가 무효화되는 원인을 구체적으로 짚는다
- GitHub Actions 환경에서 캐시를 실제로 유지하는 설정을 보여준다
- 상황별로 어떤 캐시 전략이 맞는지 비교한다

빌드 시간 단축은 코드 품질 문제가 아니에요. 설정 문제예요.

---

## 2. Docker 레이어 캐시, 어떻게 동작하냐면요

Docker는 Dockerfile의 각 명령어를 레이어로 쌓아요. `RUN`, `COPY`, `ADD` 같은 명령어가 실행될 때마다 새 레이어가 생기고, 각 레이어는 해시값으로 식별돼요.

핵심 규칙이 하나 있어요. **어떤 레이어가 바뀌면 그 이후의 모든 레이어는 캐시를 쓰지 못하고 다시 실행돼요.** 위에서 아래로 흐르는 폭포수처럼요.

예를 들어 이런 Dockerfile이 있다고 해볼게요.

```dockerfile
FROM node:20
WORKDIR /app
COPY . .                    # ← 여기가 문제
RUN npm ci
RUN npm run build
```

`src/index.ts` 파일 한 줄 바꾸면요? `COPY . .`가 변경을 감지하고, 그 아래 `npm ci`와 `npm run build`가 전부 다시 돌아요. `node_modules`가 500MB든 1GB든 상관없이요. 놀랍죠?

고치는 방법은 단순해요. 변경 빈도가 낮은 것을 위로, 높은 것을 아래로 내리는 거예요.

```dockerfile
FROM node:20
WORKDIR /app
COPY package.json package-lock.json ./   # 의존성 파일만 먼저
RUN npm ci                               # 이 레이어는 잘 안 바뀜
COPY . .                                 # 소스 파일은 나중에
RUN npm run build
```

이렇게 하면 `package.json`이 바뀌지 않는 한 `npm ci` 레이어는 캐시를 그대로 써요. PR을 100번 올려도 의존성 설치는 한 번만 하는 셈이에요.

---

## 3. GitHub Actions에서 캐시가 사라지는 진짜 이유

### 3-1. 러너 환경의 휘발성

GitHub Actions의 hosted runner는 매 실행마다 새 VM에서 시작해요. 지난 빌드의 Docker 이미지 레이어는 흔적도 없이 사라지죠. 로컬에서 `docker build`를 두 번 돌리면 두 번째는 훨씬 빠른데, Actions에서는 매번 처음부터 하는 것처럼 느려지는 이유가 바로 이거예요.

이 문제를 해결하는 게 **외부 캐시 스토리지**예요. 현재 주로 쓰이는 방식은 두 가지예요.

- `cache-type=gha`: GitHub Actions Cache API를 캐시 저장소로 씀
- `cache-type=registry`: 컨테이너 레지스트리(예: GHCR, ECR)에 캐시 레이어를 저장

### 3-2. `cache-from` 미설정

많은 팀이 `docker/build-push-action`을 이렇게만 써요.

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: myapp:latest
```

캐시 설정이 전혀 없어요. 매번 풀빌드예요. 아래처럼 바꿔야 해요.

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: myapp:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

`mode=max`는 중간 레이어까지 전부 캐시에 저장하는 설정이에요. 기본값인 `mode=min`은 최종 이미지 레이어만 저장하는데, 멀티스테이지 빌드에서는 효과가 떨어질 수 있어요.

### 3-3. 브랜치 간 캐시 격리

GitHub Actions의 캐시는 브랜치 단위로 격리돼요. `main` 브랜치에서 만든 캐시는 feature 브랜치에서 읽을 수 있지만, feature 브랜치 캐시를 `main`으로 가져오진 못해요.

그래서 새 브랜치를 만들어 첫 빌드를 돌리면 `main`의 캐시를 폴백으로 써요. `main`을 자주 빌드하고 캐시를 유지하는 게 팀 전체 빌드 시간을 줄이는 기반이 되는 이유가 이거예요.

---

## 4. 캐시 전략 비교: 내 상황엔 뭐가 맞을까요?

| 항목 | `cache-type=gha` | `cache-type=registry` | 로컬 캐시 (`--cache-dir`) |
|---|---|---|---|
| 별도 인프라 필요 | 없음 | 레지스트리 필요 | 없음 |
| 캐시 용량 한도 | 10GB (Actions Cache 전체) | 레지스트리 용량에 따라 다름 | 러너 디스크 용량 |
| 속도 | 빠름 | 네트워크 대역폭 영향 받음 | 제일 빠름 |
| Self-hosted runner 지원 | 가능 | 가능 | 가능 |
| 캐시 만료 정책 | 7일 미사용 시 삭제 | 정책 직접 설정 | 러너 재시작 시 소멸 |
| 추천 상황 | 소규모~중규모 팀, 빠른 설정 | 대규모 팀, 캐시 재사용율이 높을 때 | Self-hosted + 영구 러너 환경 |

`cache-type=gha`는 설정이 두 줄이에요. 당장 쓸 수 있어요. 반면 `cache-type=registry`는 레지스트리 인증 설정이 추가로 필요하지만, 10GB 용량 한도를 걱정하지 않아도 된다는 장점이 있어요.

Self-hosted runner를 영구적으로 운영 중이라면 얘기가 달라요. 같은 머신에서 계속 빌드가 돌기 때문에 로컬 Docker 레이어 캐시가 자연스럽게 쌓여요. youngju.dev의 Self-hosted Runner 가이드(2026년 3월)에서도 이 환경에선 `cache-type=local`과 `--cache-dir` 조합이 가장 빠른 결과를 낸다고 설명해요.

---

## 5. 지금 바로 적용할 수 있는 설정

**상황 1: 빌드가 매번 8분 이상 걸리는 팀**

먼저 Dockerfile을 열고 `COPY . .`의 위치를 확인하세요. 의존성 설치(`pip install`, `npm ci`, `go mod download`) 앞에 있으면 순서를 바꿔야 해요. 의존성 파일만 먼저 복사하고, 소스 전체 복사는 맨 마지막으로 내리세요.

**상황 2: 워크플로에 캐시 설정이 없는 팀**

`docker/build-push-action`에 `cache-from: type=gha`와 `cache-to: type=gha,mode=max`를 추가하세요. Actions 캐시 사용량은 레포지토리 Settings → Actions → Caches에서 바로 볼 수 있어요.

**상황 3: 멀티스테이지 빌드 쓰는 팀**

각 스테이지에 `--target` 옵션을 명시하고 `mode=max`로 중간 스테이지 캐시도 저장하세요. 빌드 스테이지와 런타임 스테이지가 분리된 구조에서 이 설정이 없으면 빌드 스테이지 캐시가 매번 날아가요.

---

## 결론: 8분짜리 빌드를 2분으로 줄이는 건 설정 문제예요

레이어 순서 조정과 `cache-type=gha` 설정, 이 두 가지만 바꿔도 빌드 시간이 절반 이하로 줄어드는 케이스가 많아요. 맞아요.

앞으로 주시할 변화도 있어요. GitHub가 Actions Cache 용량 한도를 늘릴 가능성(현재 10GB는 대형 모노레포엔 빡빡해요), Depot·Namespace 같은 고속 빌더 서비스가 `docker/build-push-action`과의 통합을 확대하는 추세, OCI 아티팩트 기반 캐시 스펙이 표준화되면 레지스트리 간 캐시 이동도 더 쉬워질 거예요.

지금 당장 해볼 것 하나. 본인 레포의 Dockerfile에서 `COPY . .` 위치를 찾아보세요. 의존성 설치 전에 있다면, 그게 빌드 시간의 주범일 가능성이 높아요.

---

*참고: hstory0208.tistory.com의 GitHub Actions Docker 빌드 속도 최적화 포스트, velog.io/@gdgocgachon의 Docker 빌드 최적화 분석, youngju.dev의 Self-hosted Runner 운영 가이드(2026년 3월)를 바탕으로 작성했어요.*

## 참고자료

1. [Github Actions Docker 빌드 속도를 최적화 해보자.](https://hstory0208.tistory.com/entry/Github-Actions-Docker-%EB%B9%8C%EB%93%9C-%EC%86%8D%EB%8F%84%EB%A5%BC-%EC%B5%9C%EC%A0%81%ED%99%94-%ED%95%B4%EB%B3%B4%EC%9E%90)
2. [나만 몰랐던 Docker 빌드 최적화 방법](https://velog.io/@gdgocgachon/how-to-optimize-docker-build)
3. [GitHub Actions Self-Hosted Runner 대규모 운영과 보안 하드닝 가이드 | Chaos and Order](https://www.youngju.dev/blog/devops/2026-03-05-devops-github-actions-self-hosted-runner-ops)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
