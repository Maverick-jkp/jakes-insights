---
title: "GitHub Actions Docker 이미지 빌드 캐시 레이어 재사용 안 될 때 원인과 해결법"
date: 2026-03-29T19:59:27+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "docker", "AWS"]
description: "GitHub Actions에서 Docker 캐시 레이어가 매번 무효화되는 원인은 Dockerfile 레이어 순서 문제와 cache-key 불일치입니다. actions/cache와 build-push-action 혼용 시 캐시 히트율이 급감하는 이유와 BuildKit type=gha 설정법을"
image: "/images/20260329-github-actions-docker-이미지-빌드-캐.webp"
technologies: ["Docker", "AWS", "GitHub Actions"]
faq:
  - question: "GitHub Actions Docker 이미지 빌드 캐시 레이어 재사용 안 될 때 원인 해결 방법"
    answer: "GitHub Actions에서 Docker 캐시 레이어가 재사용되지 않는 주요 원인은 Dockerfile 레이어 순서 문제, cache-key 해시 불일치, cache-from 타입 혼용 세 가지입니다. 예를 들어 COPY . .를 의존성 설치 명령어보다 앞에 두면 소스 파일이 조금만 바뀌어도 npm install이나 pip install이 처음부터 다시 실행됩니다. docker/build-push-action v5의 type=gha 캐시 방식을 단독으로 사용하고 Dockerfile 레이어 순서를 최적화하면 대부분의 캐시 무효화 문제를 해결할 수 있습니다."
  - question: "GitHub Actions docker build 매번 처음부터 빌드되는 이유"
    answer: "가장 흔한 원인은 actions/cache의 캐시 키에 ${{ github.sha }}처럼 커밋마다 바뀌는 값을 사용하는 것으로, 이 경우 캐시가 절대 히트하지 않습니다. 캐시 키는 package-lock.json이나 requirements.txt 파일의 해시값을 기반으로 설정해야 의존성이 바뀌지 않는 한 캐시가 유지됩니다. 또한 GitHub Actions 캐시 스토리지는 리포지토리당 10GB 한도가 있고 7일 미접근 시 자동 삭제되므로, 캐시가 있다가 갑자기 사라지는 현상도 이 때문일 수 있습니다."
  - question: "docker buildx type=gha vs type=registry 캐시 차이점"
    answer: "type=gha는 GitHub Actions 네이티브 캐시 스토리지 API를 직접 사용하므로 별도 레지스트리 없이 설정이 간단하지만, 전체 용량이 10GB로 제한됩니다. type=registry는 Docker Hub나 ECR 같은 컨테이너 레지스트리에 캐시를 저장해 속도가 빠르고 브랜치 간 공유도 가능하지만, 레지스트리 권한 설정과 추가 비용이 필요합니다. 1GB 미만 이미지의 중소 규모 프로젝트라면 type=gha로 충분하고, 대형 이미지나 팀 공유가 필요한 경우 type=registry가 더 안정적입니다."
  - question: "Dockerfile npm install pip install 매번 재실행되는 문제 해결"
    answer: "COPY . .를 의존성 설치 명령어보다 앞에 배치하면 소스 파일이 1줄만 바뀌어도 해당 레이어 이하 전체가 무효화되어 npm install이나 pip install이 매번 새로 실행됩니다. 해결책은 COPY package.json package-lock.json ./처럼 의존성 파일만 먼저 복사하고 RUN npm install을 실행한 뒤, 그 다음에 COPY . .로 나머지 소스를 복사하는 순서로 Dockerfile을 작성하는 것입니다. 이 방법만으로도 빌드 시간이 10분에서 1-2분으로 단축되는 경우가 많습니다."
  - question: "GitHub Actions Docker 이미지 빌드 캐시 레이어 재사용 안 될 때 캐시 히트 여부 확인하는 방법"
    answer: "docker buildx build --progress=plain 옵션으로 빌드를 실행하면 출력 로그에서 CACHED 키워드가 포함된 라인 수를 통해 캐시 레이어 재사용률을 바로 확인할 수 있습니다. CACHED 라인이 거의 없다면 캐시가 제대로 작동하지 않는 것이므로 Dockerfile 레이어 순서와 cache-key 설정을 점검해야 합니다. GitHub Actions 워크플로우 로그에서도 동일하게 확인할 수 있어 별도 도구 없이 빠르게 진단이 가능합니다."
aliases:
  - "/tech/2026-03-29-github-actions-docker-이미지-빌드-캐시-레이어-재사용-안-될-때-원인-해/"

---

CI/CD 파이프라인에서 Docker 빌드가 10분씩 걸린다면, 높은 확률로 캐시가 제대로 작동하지 않는 거예요. 설정은 다 해놨는데 매번 처음부터 빌드되는 그 답답함, 맞죠?

> **핵심 요약**
> - GitHub Actions의 `cache-from` / `cache-to` 설정을 해도 캐시가 무효화되는 주된 원인은 Dockerfile 레이어 순서 문제와 `cache-key` 불일치 두 가지다.
> - `actions/cache`와 `docker/build-push-action`의 내장 캐시 방식은 동작 원리가 다르기 때문에 혼용하면 캐시 히트율이 급격히 떨어진다.
> - Docker BuildKit의 `--cache-from type=gha` 방식은 GitHub Actions 네이티브 캐시 스토리지를 쓰기 때문에 별도 레지스트리 없이도 레이어 재사용이 가능하다.
> - 캐시 레이어 재사용률을 측정하려면 `docker buildx build --progress=plain` 출력에서 `CACHED` 라인 수를 확인하는 게 가장 빠른 방법이다.

---

## 설정은 했는데 왜 매번 새로 빌드될까?

GitHub Actions에서 Docker 이미지를 빌드할 때 캐시 레이어가 재사용되지 않는 문제는 생각보다 흔해요. 단순히 "캐시 설정이 없어서"가 아니라, 설정은 했는데도 캐시가 무효화되는 케이스가 대부분이거든요.

핵심 원인은 세 가지로 좁혀져요.

**첫 번째: Dockerfile 레이어 순서.**
Docker는 위에서 아래로 순차적으로 레이어를 빌드하고, 특정 레이어가 바뀌면 그 아래 레이어는 전부 무효화돼요. `COPY . .` 명령어를 의존성 설치보다 앞에 두면, 소스 파일이 1줄만 바뀌어도 `npm install`이나 `pip install`을 처음부터 다시 실행하는 셈이에요.

**두 번째: `cache-key` 해시 불일치.**
`actions/cache`를 쓸 때 `key`에 `${{ github.sha }}`를 넣으면 커밋마다 키가 달라지니까 캐시가 절대 히트하지 않아요. 캐시 키에는 `package-lock.json`이나 `requirements.txt`의 해시를 써야 해요. 의존성 파일이 안 바뀌면 캐시도 유지되니까요.

**세 번째: `cache-from` 타입 혼용.**
`docker/build-push-action` v2 이후 내장 캐시(`type=gha`)와 외부 레지스트리 캐시(`type=registry`)를 동시에 쓰거나, 구버전 액션의 캐시 방식과 섞어 쓰면 캐시 스토리지를 제대로 찾지 못해요.

참고로, GitHub Actions 자체 캐시 스토리지 한도는 리포지토리당 10GB예요. 이 한도를 넘으면 오래된 캐시부터 자동으로 지워지기 때문에 캐시가 있다가 없어지는 현상이 발생하기도 해요. GitHub 공식 문서에 따르면 캐시 항목은 7일 동안 접근이 없으면 자동 삭제돼요.

---

## 레이어 캐시가 실제로 어떻게 작동하는지

Docker 빌드 캐시는 레이어 단위로 동작해요. 각 Dockerfile 명령어(`RUN`, `COPY`, `ADD`)가 하나의 레이어를 만들고, Docker는 이 레이어의 체크섬을 비교해서 변경 여부를 판단하죠.

GitHub Actions에서 이 레이어를 다음 빌드에서 재사용하려면 캐시를 어딘가에 저장해야 해요. 방법은 크게 두 가지예요.

**`type=gha` (GitHub Actions 네이티브 캐시)**
BuildKit이 GitHub의 캐시 스토리지 API를 직접 호출해요. 별도 레지스트리가 필요 없고, 설정도 제일 간단해요. 단, GitHub 캐시 API 속도에 의존하기 때문에 대형 이미지에서는 느릴 수 있어요.

**`type=registry` (컨테이너 레지스트리 캐시)**
Docker Hub, AWS ECR, GitHub Container Registry 같은 레지스트리에 캐시 매니페스트를 별도로 저장해요. 속도는 빠르지만 레지스트리 권한 설정과 비용이 추가로 필요해요.

### 캐시 방식 비교

| 항목 | `type=gha` | `type=registry` | `actions/cache` (구방식) |
|------|-----------|-----------------|------------------------|
| 설정 난이도 | 낮음 | 중간 | 낮음 |
| 추가 인프라 | 불필요 | 레지스트리 필요 | 불필요 |
| 캐시 히트 속도 | 중간 | 빠름 | 중간 |
| 대용량 이미지 | 한계 있음 (10GB 총량) | 레지스트리 용량에 따라 | 압축 오버헤드 있음 |
| 브랜치 간 공유 | 기본 브랜치만 공유 | 가능 | 제한적 |
| 권장 사용 | 중소 규모 프로젝트 | 대형 이미지, 팀 공유 | 레거시 / 비권장 |

캐시 방식 선택은 이미지 크기와 팀 규모에 달려 있어요. 1GB 미만 이미지라면 `type=gha`로 충분하고, 그 이상이라면 레지스트리 캐시가 더 안정적이에요.

### Dockerfile 레이어 순서 최적화 — 실제로 어떻게 바꾸나

잘못된 패턴부터 볼게요.

```dockerfile
# ❌ 이렇게 하면 안 돼요
COPY . .
RUN npm install
```

소스 파일이 조금이라도 바뀌면 `npm install`을 처음부터 실행해요. 10분 빌드의 주범이에요.

```dockerfile
# ✅ 이렇게 바꾸면 돼요
COPY package.json package-lock.json ./
RUN npm install
COPY . .
```

`package-lock.json`이 안 바뀌면 `npm install` 레이어는 캐시에서 그대로 가져와요. 이것만 바꿔도 빌드 시간이 10분에서 1-2분으로 줄어드는 케이스가 많아요.

### workflow 파일 올바른 설정 예시

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ env.IMAGE_TAG }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

`mode=max`를 빠뜨리면 최종 레이어만 캐시되고 중간 레이어는 버려져요. 멀티 스테이지 빌드를 쓴다면 반드시 `mode=max`를 붙여야 모든 스테이지의 레이어가 저장돼요.

---

## 캐시가 안 되는 상황별 진단법

**증상 1: 매 빌드마다 `CACHED` 라인이 전혀 안 보임**
→ `cache-from` 설정이 없거나, 캐시 키가 매번 달라지는 경우예요. `--progress=plain` 옵션으로 빌드 로그를 자세히 보면 어느 레이어부터 캐시 미스가 나는지 바로 확인할 수 있어요.

**증상 2: 처음 빌드는 캐시가 되는데 다른 브랜치에서는 안 됨**
→ GitHub Actions 캐시는 기본적으로 기본 브랜치(`main`)의 캐시만 모든 브랜치가 읽을 수 있어요. 피처 브랜치에서 생성된 캐시는 해당 브랜치 내에서만 유효해요. `restore-keys`를 써서 폴백 키를 설정하면 이 문제를 우회할 수 있어요.

**증상 3: 로컬에서는 캐시가 잘 되는데 CI에서만 안 됨**
→ 로컬과 CI의 BuildKit 버전 차이, 또는 `DOCKER_BUILDKIT=1` 환경변수가 CI에서 설정 안 된 경우예요. `docker/setup-buildx-action`을 워크플로우 초반에 실행하면 BuildKit이 확실히 활성화돼요.

---

## 실제 파이프라인에서 어떻게 접근할까

**소규모 팀 또는 사이드 프로젝트:**
`type=gha` + Dockerfile 레이어 순서 정리만 해도 충분해요. 설정 두 줄에 빌드 시간이 절반 이하로 줄어드는 경우가 많아요.

**프로덕션 레벨 팀:**
멀티 스테이지 빌드와 `type=registry`를 같이 쓰세요. 빌드 스테이지(`builder`)와 런타임 스테이지를 분리하면 캐시할 레이어가 늘어나고, 최종 이미지는 작아져요. AWS ECR이나 GitHub Container Registry에 `-cache` 태그로 캐시 매니페스트를 따로 관리하는 게 팀 간 캐시 공유에도 유리해요.

**지켜볼 신호 세 가지:**
- GitHub이 캐시 API 속도 개선을 예고한 상태라, `type=gha`의 성능 한계가 완화될 수 있어요.
- BuildKit의 `--cache-export`/`--cache-import` 명세는 계속 확장 중이에요. OCI 표준 캐시 포맷이 확정되면 레지스트리 간 이식성이 훨씬 좋아질 거예요.
- `docker/build-push-action` v6 계열에서 캐시 키 자동 생성 로직이 바뀌는 경우가 있으니 버전을 올릴 때는 캐시 히트율을 다시 확인하는 게 좋아요.

---

## 요약: 캐시 문제, 어디서부터 손대야 할까

핵심을 세 줄로 정리하면 이래요.

- **Dockerfile 레이어 순서부터 고치세요.** 변경 빈도가 낮은 것(의존성)이 먼저, 자주 바뀌는 것(소스 코드)이 나중이에요.
- **`cache-from type=gha, mode=max`를 반드시 붙이세요.** 이 한 줄이 없으면 중간 레이어가 전부 버려져요.
- **캐시 키에 `github.sha` 쓰지 마세요.** 의존성 파일의 해시를 키로 써야 캐시가 살아남아요.

캐시 히트율이 올라가면 빌드 시간만 줄어드는 게 아니에요. GitHub Actions 과금도 분 단위라, 한 달 빌드 횟수가 수백 번이면 비용 차이가 꽤 나요.

그럼 지금 당장 `--progress=plain`으로 빌드 로그를 열어서 `CACHED`가 몇 줄이나 뜨는지 세어보세요. 그 숫자가 현재 캐시 상태를 가장 직접적으로 보여줘요.

## 참고자료

1. [GitHub Actions에서 Docker Build 캐싱 적용하기](https://byeongtil.tistory.com/104)
2. [Github Actions Docker 빌드 속도를 최적화 해보자.](https://hstory0208.tistory.com/entry/Github-Actions-Docker-%EB%B9%8C%EB%93%9C-%EC%86%8D%EB%8F%84%EB%A5%BC-%EC%B5%9C%EC%A0%81%ED%99%94-%ED%95%B4%EB%B3%B4%EC%9E%90)
3. [Docker 이미지 빌드 빠르게 하는 방법 (10분 걸리던게 1분에 완료!)](https://jjig810906.tistory.com/109)


---

*Photo by [Robynne O](https://unsplash.com/@roborobs) on [Unsplash](https://unsplash.com/photos/a-group-of-people-standing-next-to-each-other-HOrhCnQsxnQ)*
