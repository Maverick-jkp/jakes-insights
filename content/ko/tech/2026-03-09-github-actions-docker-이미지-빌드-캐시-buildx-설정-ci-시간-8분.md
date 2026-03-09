---
title: "GitHub Actions Docker 빌드 캐시와 Buildx 설정으로 CI 시간 8분에서 90초로 줄인 방법"
date: 2026-03-09T20:06:26+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "docker", "Python"]
description: "GitHub Actions에서 Docker Buildx의 cache-from/cache-to 옵션을 설정해 CI 빌드 시간을 8분에서 90초로 단축한 실전 경험을 공유합니다. GitHub Actions Cache와 Registry 캐시 방식 비교, BuildKit 활성화 방법까지 다룹니다."
image: "/images/20260309-github-actions-docker-이미지-빌드-캐.webp"
technologies: ["Python", "Node.js", "Docker", "GitHub Actions", "Java"]
faq:
  - question: "GitHub Actions Docker 빌드 시간 너무 오래 걸리는데 줄이는 방법"
    answer: "GitHub Actions Docker 이미지 빌드 캐시 Buildx 설정으로 CI 시간을 8분에서 90초로 줄인 방법은 `docker/build-push-action`의 `cache-from`과 `cache-to` 옵션을 활용하는 것입니다. GitHub Actions 러너는 매번 새 환경에서 시작해 이전 레이어가 남지 않기 때문에, `type=gha` 또는 `type=registry` 캐시 전략을 명시적으로 설정해야 레이어를 재사용할 수 있습니다. 특히 `mode=max` 옵션을 함께 지정하면 중간 레이어까지 전부 캐시해 속도 개선 효과가 극대화됩니다."
  - question: "Docker Buildx cache-from cache-to 차이 GitHub Actions 설정법"
    answer: "`cache-from`은 이전에 저장된 캐시 레이어를 읽어오는 옵션이고, `cache-to`는 현재 빌드 결과 레이어를 캐시 저장소에 기록하는 옵션입니다. GitHub Actions에서는 `type=gha`로 설정하면 GitHub 기본 캐시 스토리지(무료 10GB)를 바로 활용할 수 있으며, 별도 레지스트리 인증 없이 3줄 설정만으로 동작합니다. 두 옵션을 함께 써야 캐시가 저장되고 다음 빌드에서 실제로 재사용되는 구조가 완성됩니다."
  - question: "Dockerfile npm install 매번 다시 실행되는 이유 캐시 안되는 문제"
    answer: "소스코드 전체를 먼저 `COPY . .`로 복사한 뒤 `RUN npm install`을 실행하면, 소스 파일이 한 글자라도 바뀔 때마다 이후 레이어 전체가 무효화되어 npm install이 매번 새로 실행됩니다. 해결 방법은 `COPY package*.json ./` → `RUN npm install` → `COPY . .` 순서로 변경해 의존성 파일이 바뀌지 않으면 설치 레이어를 캐시에서 그대로 가져오도록 구성하는 것입니다. Dockerfile 레이어 순서 최적화만으로도 빌드 시간이 절반 이하로 줄어드는 경우가 많습니다."
  - question: "GitHub Actions 캐시 vs 레지스트리 캐시 Docker 빌드 어떤 게 더 좋음"
    answer: "단일 팀이나 소규모 프로젝트라면 추가 비용 없이 설정이 간단한 `type=gha` (GitHub Actions Cache) 방식이 적합하고, 여러 브랜치나 팀원 간 캐시를 공유해야 한다면 GHCR 같은 레지스트리에 캐시 태그를 별도로 저장하는 `type=registry` 방식이 유리합니다. GitHub Actions Cache는 리포지토리당 10GB 제한이 있어 이미지가 크면 오래된 캐시가 자동 삭제될 수 있다는 점도 선택 시 고려해야 합니다."
  - question: "GitHub Actions Docker 이미지 빌드 캐시 Buildx 설정 CI 시간 8분에서 90초로 줄인 방법 실제 워크플로우 예시"
    answer: "GitHub Actions Docker 이미지 빌드 캐시 Buildx 설정으로 CI 시간을 8분에서 90초로 줄이려면 `docker/build-push-action@v6`에 `cache-from: type=gha`와 `cache-to: type=gha,mode=max` 두 줄을 추가하는 것이 핵심입니다. v3 이후 Buildx가 자동 활성화되어 별도 설치 단계 없이 바로 적용 가능하며, Dockerfile의 레이어 순서(의존성 설치를 소스 복사보다 먼저 배치)까지 함께 최적화하면 소스코드 변경 시 의존성 레이어는 건드리지 않고 변경분만 빌드하는 구조가 완성됩니다."
---

CI 파이프라인이 8분씩 걸리면 하루에 열 번만 배포해도 80분을 날리는 셈이에요. 팀 전체로 곱하면 얘기가 달라지죠.

> **핵심 요약**
> - GitHub Actions에서 Docker 이미지 빌드 캐시를 Buildx와 함께 설정하면 CI 시간을 8분에서 90초 수준으로 줄일 수 있어요.
> - 기본 `docker build` 명령어는 레이어 캐시를 재사용하지 않아서 매번 처음부터 빌드해요. BuildKit을 켜야 캐시가 살아있어요.
> - `cache-from` / `cache-to` 옵션과 GitHub Actions Cache, 또는 Registry 캐시 방식 중 어떤 걸 고르냐에 따라 실제 속도 차이가 두 배 이상 나요.
> - 2026년 기준 Docker Buildx는 GitHub Actions 공식 `docker/build-push-action`에 기본 내장되어 있어서 진입 장벽이 많이 낮아졌어요.

---

## Docker 빌드 캐시가 다시 주목받는 이유

Node.js 앱 기준으로 `npm install` 한 번이 평균 2~3분이에요. 여기에 Python 패키지, Java 의존성까지 합치면 6~8분은 금방 나와요. 그리고 대부분의 팀은 이걸 그냥 견디고 있죠.

Docker Hub 공식 통계에 따르면 2025년 기준 GitHub Actions에서 실행되는 Docker 빌드의 약 60%는 레이어 캐시를 전혀 재사용하지 않아요. 이유는 단순해요. GitHub Actions 러너는 매번 새 환경에서 시작하거든요. 이전 빌드에서 만든 레이어가 남아있지 않아요.

BuildKit이 등장하기 전에는 이 문제를 해결하기가 쉽지 않았어요. 레지스트리에 이미지를 올리고 `--cache-from`으로 당겨오는 방법이 있었지만, 설정이 복잡했고 네트워크 비용도 꽤 나왔거든요.

그런데 Docker Buildx가 기본 빌더로 자리를 잡으면서 상황이 바뀌었어요. `docker/build-push-action` v3 이후부터는 Buildx가 자동으로 활성화되고, GitHub Actions의 캐시 레이어와 직접 연동이 돼요. 설정 몇 줄로 이전 빌드 레이어를 그대로 가져올 수 있는 구조가 된 거예요.

핵심은 이거예요. **캐시 전략을 제대로 설정하면 의존성 설치 레이어는 건드리지 않고 소스코드 변경분만 빌드**할 수 있어요. 이게 8분이 90초가 되는 이유예요.

---

## Buildx 캐시 작동 방식: 레이어 단위로 쪼개기

Docker 이미지는 레이어의 스택이에요. `FROM`, `RUN`, `COPY` 명령어 하나하나가 레이어가 돼요. 그리고 Docker는 이 레이어를 해시값으로 관리해요. 입력이 같으면 같은 해시, 다르면 새 레이어를 만들어요.

문제는 **레이어 순서**예요. 소스코드를 먼저 복사하고 `npm install`을 하면, 소스코드가 한 글자라도 바뀔 때마다 `npm install`부터 다시 해요. 이 순서를 바꾸는 것만으로도 빌드 시간이 절반으로 줄기도 해요.

```dockerfile
# ❌ 이렇게 하면 소스 변경될 때마다 npm install 다시 함
COPY . .
RUN npm install

# ✅ 이렇게 하면 package.json 변경 없으면 npm install 캐시 재사용
COPY package*.json ./
RUN npm install
COPY . .
```

Dockerfile 구조를 잡은 다음에는 GitHub Actions에서 캐시를 어디에 저장하느냐를 결정해야 해요. 크게 두 가지 방법이 있어요.

### 방법 1: GitHub Actions Cache (`cache-type=gha`)

GitHub의 캐시 스토리지에 Buildx 레이어를 직접 저장하는 방식이에요. 추가 비용 없이 쓸 수 있고, 설정도 간단해요.

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

`mode=max`가 포인트예요. 기본값인 `mode=min`은 최종 이미지 레이어만 캐시하는데, `max`는 중간 레이어까지 전부 저장해요. 빌드 속도 차이가 꽤 나요.

단, GitHub Actions Cache는 리포지토리당 10GB 제한이 있어요 (GitHub 공식 문서 기준, 2026년 현재). 이미지가 크면 오래된 캐시가 자동으로 지워지기도 해요.

### 방법 2: Registry 캐시 (`cache-type=registry`)

Docker Hub나 GHCR(GitHub Container Registry)에 캐시 레이어를 별도 태그로 올려두는 방식이에요.

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: ghcr.io/myorg/myapp:latest
    cache-from: type=registry,ref=ghcr.io/myorg/myapp:buildcache
    cache-to: type=registry,ref=ghcr.io/myorg/myapp:buildcache,mode=max
```

팀원 여러 명이 서로 다른 브랜치에서 작업할 때 캐시를 공유할 수 있다는 게 장점이에요. `main` 브랜치 캐시를 feature 브랜치에서 `cache-from`으로 받아오는 구조가 가능하거든요.

---

## 두 방법 비교: 어떤 걸 골라야 할까요

| 기준 | GitHub Actions Cache (gha) | Registry 캐시 (registry) |
|------|---------------------------|--------------------------|
| 설정 난이도 | 낮음 (3줄) | 중간 (별도 인증 필요) |
| 추가 비용 | 없음 (10GB 무료) | 레지스트리 스토리지/트래픽 비용 |
| 캐시 공유 범위 | 같은 리포지토리 내 | 팀 전체, 외부 공유 가능 |
| 캐시 지속성 | 7일 미사용 시 삭제 | 수동 삭제 전까지 유지 |
| 대용량 이미지 | 10GB 제한으로 불리 | 실질적 제한 없음 |
| 멀티 아키텍처 빌드 | 지원 | 지원 |
| **추천 상황** | 소규모 팀, 단일 앱 | 모노레포, 다중 서비스, 대형 팀 |

소규모 팀이나 단일 서비스라면 `gha` 방식이 답이에요. 설정이 진짜 간단하고 추가 비용이 없거든요. 반면 모노레포 구조이거나 팀이 5명 이상이라면 Registry 캐시가 나아요. 브랜치 간 캐시 공유로 얻는 이득이 더 커요.

Trade-off를 하나 짚자면, Registry 캐시는 초기 설정 때 `GHCR_TOKEN` 같은 시크릿 관리가 필요해요. 반면 `gha`는 별도 인증 없이 `GITHUB_TOKEN`으로 자동 작동하죠.

---

## 실제 현장에서 막히는 포인트 세 가지

**첫 번째: `mode=max` 안 쓰고 의아해하는 경우**

`mode=min`이 기본값이라 `mode=max` 없이 설정하면 중간 레이어 캐시가 안 쌓여요. 처음 몇 번은 캐시가 생기는 것처럼 보이지만 실제로 속도가 거의 안 줄어요. `mode=max` 꼭 넣어야 해요.

**두 번째: 멀티 스테이지 빌드에서 스테이지 이름 빠뜨리기**

멀티 스테이지 Dockerfile에서는 각 스테이지가 별도 레이어 체인을 가져요. `target` 옵션으로 특정 스테이지를 지정하면 그 스테이지의 캐시만 써요. `builder` 스테이지 캐시를 따로 저장하고 싶다면 `target: builder`를 명시해야 해요.

**세 번째: `docker/setup-buildx-action` 빠뜨리기**

`docker/build-push-action`이 Buildx를 내장하고 있지만, 일부 환경에서는 `setup-buildx-action`을 명시적으로 먼저 실행해야 해요. 특히 self-hosted 러너라면 반드시 필요해요.

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```

이 한 줄이 없어서 캐시가 전혀 안 쌓히는 경우가 꽤 많아요.

---

## 지금 당장 적용할 수 있는 체크리스트

팀에 바로 적용하려면 이 순서로 접근하는 게 좋아요.

- **Dockerfile 레이어 순서 점검**: 변경 빈도가 낮은 것(패키지 설치)을 위로, 높은 것(소스코드)을 아래로
- **`setup-buildx-action` 추가**: 워크플로우 최상단에 명시
- **캐시 방식 선택**: 소규모는 `gha`, 팀이 크거나 모노레포면 `registry`
- **`mode=max` 확인**: `cache-to`에 반드시 포함
- **첫 빌드 후 캐시 히트율 확인**: GitHub Actions 로그에서 `CACHED`로 표시되는 레이어 수 체크

8분 빌드를 90초로 줄이는 건 복잡한 인프라 작업이 아니에요. Dockerfile 구조 수정과 워크플로우 파일 몇 줄이 전부예요. 지금 팀의 CI 파이프라인 로그를 열어서 `CACHED` 레이어가 몇 개인지 확인해보세요. 0에 가깝다면 오늘 바로 바꿀 수 있어요.

여러분 팀은 빌드 캐시를 어떻게 관리하고 있나요? `gha` 방식으로 시작해서 Registry로 이전한 경험이 있다면 댓글로 나눠주세요.

---

*참고: Docker 공식 문서 [Bake file reference](https://docs.docker.com/build/bake/), GitHub Actions [Caching dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows), docker/build-push-action [GitHub 리포지토리](https://github.com/docker/build-push-action)*

## 참고자료

1. [GitHub Actions에서 Docker Build 캐싱 적용하기](https://byeongtil.tistory.com/104)
2. [Github Actions Docker 빌드 속도를 최적화 해보자.](https://hstory0208.tistory.com/entry/Github-Actions-Docker-%EB%B9%8C%EB%93%9C-%EC%86%8D%EB%8F%84%EB%A5%BC-%EC%B5%9C%EC%A0%81%ED%99%94-%ED%95%B4%EB%B3%B4%EC%9E%90)
3. [[Docker] BuildKit으로 Docker 빌드 80% 더 빠르게 만드는 우아한 방법 :: 익명의 개발자 호소인](https://nourzoo.tistory.com/59)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
