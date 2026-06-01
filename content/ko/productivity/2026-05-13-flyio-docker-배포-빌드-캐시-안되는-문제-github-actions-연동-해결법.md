---
title: "Fly.io Docker 배포 빌드 캐시 안되는 문제, GitHub Actions 연동 해결법 3가지"
date: 2026-05-13T21:24:05+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "fly.io", "docker", "/uc548/ub418/ub294", "Python"]
description: "GitHub Actions에서 Fly.io Docker 배포 시 매 실행마다 캐시가 초기화되는 문제, docker buildx와 GitHub Actions Cache 연동으로 빌드 시간 60-75% 단축하는 방법을 실제 설정 코드와 함께 설명합니다."
image: "/images/20260513-flyio-docker-배포-빌드-캐시-안되는-문제-g.webp"
technologies: ["Python", "Docker", "GitHub Actions", "Go"]
faq:
  - question: "GitHub Actions에서 Fly.io Docker 배포할 때 빌드 캐시가 매번 초기화되는 이유"
    answer: "GitHub Actions는 워크플로 실행마다 완전히 새로운 가상 머신을 할당하기 때문에, 이전 실행에서 생성된 Docker 레이어 캐시가 100% 소실됩니다. Fly.io Docker 배포 빌드 캐시 안되는 문제 GitHub Actions 연동 해결법의 핵심은 캐시를 외부 저장소에 명시적으로 저장하도록 설정하는 것이며, `--cache-from`과 `--cache-to` 옵션을 지정하지 않으면 캐시는 사실상 존재하지 않는 것과 같습니다."
  - question: "Fly.io GitHub Actions 빌드 시간 줄이는 방법 docker buildx 캐시 설정"
    answer: "`docker/build-push-action`에서 `cache-from: type=gha`와 `cache-to: type=gha,mode=max`를 설정하면 GitHub Actions 내장 캐시 스토리지를 활용해 빌드 시간을 평균 60~75% 단축할 수 있습니다. 이 방법은 설정이 간단하고 리포지토리당 10GB 한도 내에서 추가 비용 없이 사용 가능하며, 소규모 팀에 가장 적합합니다."
  - question: "Fly.io Docker 배포 빌드 캐시 안되는 문제 GitHub Actions 연동 해결법 팀 전체 캐시 공유"
    answer: "팀 전체가 빌드 캐시를 공유하려면 GitHub Container Registry(GHCR)를 캐시 백엔드로 사용하는 Registry 캐시 방식이 적합합니다. `cache-from: type=registry,ref=ghcr.io/my-org/my-app:buildcache`로 설정하면 여러 브랜치에서 동시에 작업하는 환경에서도 공통 캐시를 재사용할 수 있으나, 레지스트리 스토리지 비용이 발생할 수 있어 캐시 크기 관리가 별도로 필요합니다."
  - question: "Dockerfile npm install 캐시 안 되는 이유 COPY 순서 문제"
    answer: "`COPY . .`으로 소스 전체를 먼저 복사한 뒤 `RUN npm install`을 실행하면, 소스 코드 한 줄만 변경되어도 그 이후 레이어가 전부 무효화됩니다. 올바른 순서는 `package.json`만 먼저 복사하고 의존성 설치를 완료한 후 나머지 소스를 복사하는 것으로, 이 구조를 지켜야 캐시 히트율이 실질적으로 높아집니다."
  - question: "fly deploy remote-only 캐시 GitHub Actions 직접 빌드 차이점"
    answer: "`fly deploy --remote-only`는 빌드를 Fly.io 원격 빌더에 위임해 설정이 가장 단순하고 Fly.io가 이전 빌드 캐시를 일정 기간 자동 유지해주지만, 캐시 보존 기간이 Fly.io 정책에 종속되고 빌드 로그 가시성이 낮습니다. 반면 GitHub Actions에서 직접 빌드하고 GHA Cache나 GHCR을 활용하면 캐시 만료 시점과 저장 위치를 직접 제어할 수 있어 중·대형 팀 환경에 더 적합합니다."
---

배포 버튼 누를 때마다 5분씩 기다리고 있죠. 코드 한 줄 바꿨을 뿐인데.

GitHub Actions에서 Fly.io로 Docker 배포할 때 캐시가 매번 리셋되는 문제, 꽤 많은 팀이 겪고 있어요. Fly.io 커뮤니티 포럼이나 GitHub Issues를 보면 이 주제가 꾸준히 상위권에 올라와 있거든요.

> **핵심 요약**
> - GitHub Actions 러너는 매 실행마다 초기화되어 로컬 Docker 레이어 캐시가 100% 소실된다.
> - `docker buildx`와 GitHub Actions Cache를 결합하면 빌드 시간을 평균 60-75% 단축할 수 있다.
> - Fly.io의 원격 빌더(`fly deploy --remote-only`)는 빌드 캐시를 자체적으로 보존하지만, 세밀한 제어가 어렵다.
> - `cache-from` / `cache-to` 설정이 빠진 Dockerfile이 가장 흔한 캐시 실패 원인이다.
> - Registry 캐시(GitHub Container Registry)를 쓰면 팀 전체가 캐시를 공유할 수 있다.

---

## 왜 GitHub Actions에서 빌드 캐시가 날아가는 걸까요

Docker 빌드 캐시는 본질적으로 "이 레이어, 전에 만들었으니까 재사용하자"는 개념이에요. 로컬 환경에서는 잘 돼요. 어제 빌드한 내용이 오늘도 디스크에 남아 있으니까요.

그런데 GitHub Actions는 달라요. 매 워크플로 실행마다 완전히 새로운 가상 머신이 할당돼요. 이전 실행에서 만들어둔 Docker 레이어는 그 VM 안에 있었고, 그 VM은 이미 사라졌어요. Fly.io도 마찬가지예요. `fly deploy`를 실행하면 Fly.io 측의 원격 빌더가 돌아가는데, 이 빌더 역시 기본적으로 이전 상태를 보장하지 않아요.

여기서 많은 팀이 놓치는 게 있어요. **캐시를 "어디에 저장할지"를 명시하지 않으면 캐시는 존재하지 않는 거나 다름없어요.**

Docker BuildKit의 `--cache-from`과 `--cache-to` 옵션이 바로 이 문제를 해결하는 열쇠예요. 빌드 결과로 만들어진 캐시를 외부 저장소(레지스트리나 GitHub Cache)에 올려두고, 다음 빌드 때 거기서 가져오는 방식이죠.

그리고 하나 더. `COPY . .` 명령어를 `RUN npm install` 앞에 두는 경우가 있어요. 소스 코드 한 줄만 바뀌어도 그 이후 레이어가 전부 무효화돼요. `package.json`만 먼저 복사하고 의존성 설치를 먼저 하는 레이어 순서가 캐시 효율에 직결돼요.

---

## 주요 해결 방법 세 가지와 실전 비교

### GitHub Actions Cache 백엔드 쓰기

가장 많이 쓰이는 방법이에요. `docker/build-push-action`의 `cache-from` / `cache-to`에 `type=gha`를 지정하면 GitHub Actions 내장 캐시 스토리지를 사용해요.

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: registry.fly.io/my-app:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

`mode=max`는 모든 레이어를 캐시해요. 저장 공간이 좀 더 필요하지만 캐시 히트율이 높아요. GitHub Actions는 브랜치 기준으로 캐시를 격리하고, 저장 한도는 리포지토리당 10GB예요(GitHub 공식 문서 기준).

### Registry 캐시 쓰기 (GHCR 활용)

GitHub Container Registry(GHCR)에 캐시 레이어를 올려두는 방식이에요. 팀원 여러 명이 각자 다른 브랜치에서 작업할 때 공통 캐시를 공유할 수 있어요.

```yaml
cache-from: type=registry,ref=ghcr.io/my-org/my-app:buildcache
cache-to: type=registry,ref=ghcr.io/my-org/my-app:buildcache,mode=max
```

단점은 캐시 데이터가 일반 이미지처럼 레지스트리 스토리지를 쓴다는 거예요. 비용이 발생할 수 있고, 캐시 크기 관리가 따로 필요해요.

### Fly.io Remote Builder에 맡기기

`fly deploy --remote-only` 플래그를 쓰면 GitHub Actions에서 빌드를 직접 하지 않고 Fly.io 원격 빌더에게 넘겨요. Fly.io 원격 빌더는 이전 빌드 캐시를 일정 기간 유지해줘요.

설정이 가장 단순하지만, 캐시 보존 기간이 Fly.io 정책에 달려 있고 빌드 로그 접근성이 떨어져요.

### 세 방법 비교

| 항목 | GHA Cache | Registry 캐시 (GHCR) | Fly.io Remote Builder |
|------|-----------|---------------------|----------------------|
| 설정 복잡도 | 낮음 | 중간 | 매우 낮음 |
| 캐시 공유 | 브랜치 격리 | 팀 전체 공유 | 빌더 단위 |
| 추가 비용 | 없음 (10GB 한도) | 스토리지 비용 발생 | 없음 |
| 캐시 만료 제어 | 가능 (7일 기본) | 직접 관리 필요 | Fly.io 정책 의존 |
| 빌드 로그 가시성 | 높음 | 높음 | 낮음 |
| 적합한 팀 규모 | 소규모 | 중·대형 팀 | 개인/소규모 |

소규모 프로젝트라면 GHA Cache가 가장 무난해요. 팀이 10명 이상이고 여러 브랜치에서 동시에 PR이 올라오는 환경이라면 Registry 캐시가 더 효율적이에요.

---

## Dockerfile 레이어 순서, 여기서 많이 틀려요

캐시 설정을 아무리 잘 해도 Dockerfile 구조가 잘못되면 소용없어요. 실제로 가장 흔히 보이는 실수 패턴이에요.

**잘못된 순서:**
```dockerfile
COPY . .          # 소스 전체 복사 먼저
RUN npm install   # 의존성 설치
```

소스 파일 하나만 바뀌어도 `npm install`이 다시 실행돼요.

**올바른 순서:**
```dockerfile
COPY package*.json ./   # 의존성 파일만 먼저
RUN npm install         # 의존성 설치 (캐시됨)
COPY . .                # 소스 코드 복사
RUN npm run build
```

이렇게 하면 `package.json`이 바뀌지 않는 한 `npm install` 레이어는 캐시에서 가져와요. Python 프로젝트라면 `requirements.txt`, Go라면 `go.mod` / `go.sum`을 먼저 복사하는 게 같은 원리예요.

---

## 실제로 어떻게 적용하면 될까요

**이미 Fly.io + GitHub Actions를 쓰고 있는 팀이라면:**

1. 먼저 Dockerfile 레이어 순서를 점검하세요. 의존성 설치 전에 소스 코드 전체를 복사하고 있지 않은지 확인해요.
2. `docker/setup-buildx-action`으로 BuildKit을 활성화하고, `cache-from: type=gha` / `cache-to: type=gha,mode=max`를 추가하세요. 설정 변경이 5분 안에 끝나요.
3. 다음 배포 실행 시간을 이전과 비교해봐요. 첫 실행은 캐시를 채우는 과정이라 빠르지 않아요. 두 번째 실행부터 차이가 나요.

**팀이 크고 브랜치가 많다면:**

Registry 캐시로 전환을 검토할 시점이에요. 특히 `main` 브랜치 캐시를 feature 브랜치에서 `cache-from`으로 참조하면 PR 빌드 시간도 줄어요.

| 체크 항목 | 확인 여부 |
|-----------|----------|
| BuildKit 활성화 (`DOCKER_BUILDKIT=1` 또는 `buildx`) | ☐ |
| `cache-from` / `cache-to` 설정 존재 | ☐ |
| Dockerfile 레이어 순서 (의존성 → 소스) | ☐ |
| fly.toml의 빌더 설정 확인 | ☐ |

---

## 앞으로 어떻게 될까요

Fly.io는 원격 빌더의 캐시 보존 기능을 점차 강화하고 있어요. 2026년 초 릴리스 노트에서 빌더 캐시 TTL 설정 옵션 추가를 언급했고, 이게 안정화되면 Remote Builder 방식의 매력이 높아질 거예요.

GitHub Actions 쪽에서는 캐시 용량 한도(현재 10GB)가 점차 늘어날 것으로 보여요. GitHub Universe 2025에서 Actions 성능 개선 로드맵을 발표했고, 캐시 관련 개선도 포함돼 있었어요.

**지금 당장 해볼 것:**
- Dockerfile 레이어 순서 점검 → 즉각적인 효과
- GHA Cache 설정 추가 → 두 번째 빌드부터 체감

빌드 시간이 5분에서 2분으로 줄어도, 하루에 배포를 열 번 반복하면 30분이 쌓여요. 작은 설정 하나가 팀 전체의 시간을 바꾸는 거예요. Fly.io에서 Docker 배포를 운영 중인데 빌드 캐시 구성이 아직 안 되어 있다면, 팀 규모에 맞는 방식부터 하나씩 적용해보세요.

## 참고자료

1. [Github Actions Docker 빌드 속도를 최적화 해보자.](https://hstory0208.tistory.com/entry/Github-Actions-Docker-%EB%B9%8C%EB%93%9C-%EC%86%8D%EB%8F%84%EB%A5%BC-%EC%B5%9C%EC%A0%81%ED%99%94-%ED%95%B4%EB%B3%B4%EC%9E%90)
2. [GitHub Actions로 Docker 이미지 자동 빌드 및 배포하기 - 완벽 가이드 - DEV Community](https://dev.to/dss99911/github-actionsro-docker-imiji-jadong-bildeu-mic-baepohagi-wanbyeog-gaideu-5e9)
3. [P4_기존 프로젝트에 배포 자동화 구축하기(github actions)_2 :: Fadet's coding box](https://fadet-coding.tistory.com/93)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
