---
title: "GitHub Actions 캐시 미스 원인 분석: Docker layer·node_modules·모노레포 삽질 해결 가이드"
date: 2026-05-18T23:07:00+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "docker", "GitHub Actions"]
description: "GitHub Actions 캐시가 매번 미스 나는 이유, CI 5분 지연의 주범은 키 설계 실수입니다. Docker layer 캐시, node_modules, 모노레포 환경별 원인과 실제 해결법을 데이터 기반으로 정리했습니다."
image: "/images/20260518-github-actions-캐시-미스-원인-docker.webp"
technologies: ["Docker", "GitHub Actions"]
faq:
  - question: "GitHub Actions 캐시 설정했는데 매번 새로 다운로드되는 이유"
    answer: "GitHub Actions 캐시 미스 원인 중 가장 흔한 것은 캐시 키 설계 실수예요. 모노레포 환경에서 `**/package-lock.json`처럼 글로브로 전체 lockfile을 해싱하면, 일부 패키지 하나만 바뀌어도 전체 캐시가 무효화되어 매번 새로 다운로드됩니다. 캐시가 '설정'된 것과 '실제로 작동'하는 것은 완전히 다른 문제이므로 키 구조를 먼저 점검해야 해요."
  - question: "Docker layer 캐시 GitHub Actions에서 CACHED 안 뜨는 이유"
    answer: "GitHub Actions 캐시 미스 원인 중 Docker layer 문제는 `docker buildx build`를 사용하지 않거나 `cache-to: type=gha` 설정을 빠뜨렸을 때 주로 발생해요. 또한 Dockerfile에서 `COPY . .`를 `npm install` 이전에 배치하면 소스 코드가 바뀔 때마다 install 레이어가 통째로 무효화됩니다. 이 세 가지 원인을 순서대로 확인하면 대부분 해결돼요."
  - question: "모노레포 node_modules 캐시 일부 패키지만 바뀌어도 전체 무효화 해결법"
    answer: "모노레포 삽질 해결의 핵심은 루트 lockfile 하나로 캐시 키를 잡지 않고, 패키지별로 캐시 키를 분리하는 거예요. 예를 들어 `packages/web`과 `packages/api` 각각의 lockfile 해시를 별도 캐시 키로 구성하면, 한 패키지의 의존성 변경이 다른 패키지 캐시에 영향을 주지 않습니다. 이 방법만으로도 불필요한 전체 캐시 무효화를 크게 줄일 수 있어요."
  - question: "pnpm node_modules 캐시 히트인데 빌드 실패하는 상황"
    answer: "pnpm에서 `node_modules`를 캐시할 때 해시 대상 파일을 `package.json`으로 잡으면, lockfile이 바뀌지 않아도 실제 의존성 버전이 달라질 수 있어 캐시는 히트하지만 빌드가 깨지는 최악의 상황이 생겨요. pnpm은 반드시 `pnpm-lock.yaml`을 해시 대상으로 사용하고, `--frozen-lockfile` 옵션을 함께 적용해야 안전합니다. npm·yarn berry와 캐시 경로 및 해시 대상 파일이 모두 다르므로 패키지 매니저에 맞는 설정을 별도로 확인하세요."
  - question: "GitHub Actions Docker 빌드 캐시 type=gha vs S3 어떤 게 나은가요"
    answer: "500MB 이상의 큰 Docker 레이어에서는 S3 외부 캐시가 복원 속도가 최대 40% 빠르지만, 설정 복잡도가 높아서 팀 규모가 작으면 `type=gha` 방식이 훨씬 실용적이에요. `type=gha`는 GitHub Actions 캐시 스토리지에 바로 저장되므로 별도 인프라 없이 빠르게 적용할 수 있습니다. 레이어 크기와 팀 운영 역량을 함께 고려해 선택하는 게 좋아요."
aliases:
  - "/tech/2026-05-18-github-actions-캐시-미스-원인-docker-layer-nodemodules-모/"

---

CI 파이프라인이 매번 5분씩 걸려요. 캐시를 설정했는데도 매번 새로 내려받고 있고요. 이 현상, 생각보다 많은 팀이 겪고 있어요.

캐시를 "설정"하는 것과 캐시가 "실제로 작동"하는 건 완전히 다른 이야기예요. 특히 Docker layer 캐시, `node_modules` 캐시, 모노레포 환경이 섞이면 미스 원인이 겹겹이 쌓여요. 이 글에서는 GitHub Actions 캐시 미스 원인을 데이터 기반으로 풀고, 모노레포 삽질 해결까지 한 번에 다뤄볼게요.

> **핵심 요약**
> - GitHub Actions 캐시 미스의 가장 흔한 원인은 키 설계 실수예요. `package-lock.json` 해시를 빠뜨리거나 OS 조건을 빠뜨리면 캐시가 쌓이기만 하고 재사용이 안 돼요.
> - Docker layer 캐시는 `buildx`의 `cache-to`/`cache-from` 설정 없이는 레이어가 매번 재빌드되며, 이것만으로도 빌드 시간이 세 배 이상 늘어날 수 있어요.
> - `node_modules`를 직접 캐시할 때 `pnpm`과 `npm`은 캐시 경로와 해시 대상 파일이 달라요. 잘못 섞으면 캐시는 히트하는데 빌드가 깨지는 최악의 상황이 생겨요.
> - 모노레포에서는 루트 `lockfile` 하나로 캐시 키를 잡으면 일부 패키지만 바뀌어도 전체 캐시가 무효화돼요. 패키지별 해시 분리가 필수예요.

---

## 캐시가 "있는데도" 미스 나는 이유

GitHub Actions의 캐시는 `actions/cache` 액션이 키와 일치하는 캐시 엔트리를 찾으면 히트, 못 찾으면 미스예요. 구조 자체는 단순해요. 그런데 왜 이렇게 자주 미스가 날까요?

문제는 **키 설계**에 있어요. GitHub 공식 문서에 따르면 캐시 키는 최대 512자까지 쓸 수 있고, 키가 완전히 일치해야만 히트가 발생해요. 부분 일치는 `restore-keys`로 따로 처리해야 해요.

youngju.dev의 GitHub Actions 운영 가이드에 따르면, 대규모 팀에서 캐시 히트율이 낮은 가장 흔한 이유 두 가지는 **불필요하게 자주 바뀌는 해시값 포함**과 **워크플로 파일 자체를 해시에 포함하지 않아 캐시 오염이 발생하는 것**이에요.

예를 들어 이렇게 키를 잡으면 어떻게 될까요?

```yaml
key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

얼핏 맞아 보이지만, 모노레포에서 `packages/api/package-lock.json`만 바뀌어도 `**/` 글로브가 모든 lockfile을 해싱하기 때문에 캐시 전체가 무효화돼요. 결국 변경이 없는 패키지도 전부 다시 내려받는 거예요.

---

## 원인별 해부: Docker layer·node_modules·모노레포

### Docker layer 캐시가 매번 초기화되는 구조

Docker 빌드에서 레이어 캐시 미스는 GitHub Actions 캐시 미스 중에서도 특히 조용하게 발생해요. 빌드 로그를 보면 `CACHED` 표시가 없고 매번 `RUN npm install`이 돌아가는 걸 볼 수 있어요.

가장 흔한 원인은 세 가지예요.

- **`docker buildx build`를 쓰지 않음**: `buildx` 없이는 `--cache-from`/`--cache-to` 옵션 자체를 제대로 쓸 수 없어요.
- **`COPY . .` 순서 문제**: `package.json`을 먼저 복사하고 `npm install` 후에 소스를 복사해야 해요. 순서가 바뀌면 소스 변경마다 `npm install` 레이어가 무효화돼요.
- **캐시 저장 위치 미지정**: `cache-to: type=gha` 설정 없이는 빌드 캐시가 GitHub Actions 캐시 스토리지에 저장 자체가 안 돼요.

runs-on.com의 S3 캐시 분석 자료에 따르면, `type=gha` 캐시와 S3 외부 캐시를 비교했을 때 큰 레이어(500MB 이상)에서는 S3 캐시가 최대 40% 빠르게 복원됐어요. 단, 설정 복잡도가 높아서 팀 규모가 작으면 `type=gha`가 훨씬 실용적이에요.

### node_modules 캐시: npm vs pnpm 혼용의 함정

`node_modules`를 직접 캐시할 때 패키지 매니저마다 경로와 캐시 대상 파일이 달라요.

| 항목 | npm | pnpm | yarn berry |
|------|-----|------|-----------|
| 캐시 경로 | `~/.npm` | `~/.local/share/pnpm/store` | `.yarn/cache` |
| 해시 대상 파일 | `package-lock.json` | `pnpm-lock.yaml` | `yarn.lock` |
| `node_modules` 직접 캐시 권장 여부 | 보통 권장 | 불필요 (store 캐시로 충분) | 조건부 |
| 주의 사항 | lockfile 없으면 매번 미스 | `--frozen-lockfile` 필수 | PnP 모드면 경로 다름 |

특히 `pnpm`에서 `node_modules`를 캐시하면서 `pnpm-lock.yaml`이 아닌 `package.json`을 해시 대상으로 잡으면 문제가 생겨요. lockfile이 바뀌지 않아도 의존성 버전이 실제로 달라질 수 있고, 캐시는 히트하는데 빌드가 깨지는 상황이 생기는 거예요.

### 모노레포 캐시 미스: 글로브 한 줄이 문제

모노레포에서 GitHub Actions 캐시 미스가 자주 나는 원인은 명확해요. 루트에서 `**/package-lock.json`을 한꺼번에 해싱하면, `packages/web`만 의존성이 바뀌어도 `packages/api`, `packages/shared` 캐시까지 통째로 날아가요.

해결 방향은 두 가지예요.

**방법 A — 패키지별 캐시 분리**:

```yaml
key: ${{ runner.os }}-web-${{ hashFiles('packages/web/package-lock.json') }}
key: ${{ runner.os }}-api-${{ hashFiles('packages/api/package-lock.json') }}
```

**방법 B — 워크스페이스 루트 lockfile만 사용 (pnpm 권장)**:

pnpm workspace는 루트 `pnpm-lock.yaml` 하나가 전체 의존성 트리를 관리해요. 이 경우 루트 lockfile만 해시해도 정확도가 높아요. npm workspace는 각 패키지별 lockfile이 분리되는 경우가 있어서 주의가 필요해요.

okorion의 GitHub Actions 캐시 기술 분석에 따르면, `restore-keys`를 잘 설정하면 완전 히트가 아닌 **부분 히트**도 캐시로 활용할 수 있어요. `restore-keys: ${{ runner.os }}-web-`을 달아두면, 키가 완전히 일치하지 않아도 가장 최신 캐시를 불러온 뒤 차이만 추가로 설치해요. 완전 미스보다 30~50% 빠른 복원이 가능한 구조예요.

---

## 팀 규모별로 다른 접근이 필요해요

**소규모 팀 (3~10명, 단일 레포)**

캐시 설정에 너무 공들일 필요 없어요. `actions/setup-node`의 `cache: 'npm'` 옵션 하나면 `~/.npm` 캐시를 자동으로 잡아줘요. Docker layer가 필요하다면 `docker/build-push-action`의 `cache-from: type=gha`만 추가하면 대부분 해결돼요.

**중간 규모 팀 (10~50명, 모노레포 시작)**

패키지별 캐시 키 분리가 필요한 시점이에요. pnpm workspace로 전환하면 `pnpm-lock.yaml` 단일 파일 해시로 전체 관리가 가능해요. 실제로 빌드 시간이 3분에서 1분 미만으로 줄어드는 경우가 많아요.

**대규모 팀 (50명 이상, 복잡한 모노레포)**

GitHub Actions 기본 캐시 스토리지(10GB 제한)가 금방 차요. runs-on.com 사례처럼 S3 외부 캐시나 self-hosted runner + 로컬 캐시 전략을 고려해야 해요. youngju.dev 가이드에 따르면, self-hosted runner에서 캐시를 로컬 디스크에 직접 저장하면 네트워크 왕복 없이 복원이 가능해서 큰 `node_modules`에서 특히 효과가 커요.

**앞으로 주시할 신호**:
- GitHub Actions 캐시 스토리지 한도 변화 (2026년 하반기 조정 예정 논의 중)
- Turborepo의 Remote Cache와 `actions/cache` 통합 사례 증가
- `docker/build-push-action` v7 이후 `cache-to` 기본값 변경 여부

---

## 정리: 원인을 알면 금방 잡혀요

- 캐시 미스 원인의 절반 이상은 키 설계 실수예요. 해시 대상 파일과 글로브 패턴을 먼저 점검하세요.
- Docker layer는 `buildx` + `cache-to: type=gha` 조합 없이는 실질적인 캐시 효과가 없어요.
- `node_modules` 캐시는 패키지 매니저마다 경로와 해시 대상이 달라요. pnpm은 store 캐시만으로도 충분한 경우가 많아요.
- 모노레포에서는 패키지별 lockfile 해시를 분리하거나, pnpm workspace 루트 lockfile 단일 관리로 넘어가는 게 가장 깔끔해요.

캐시 히트율이 낮으면 워크플로 로그에서 `Cache not found for input keys`를 먼저 검색해보세요. 미스 원인이 정확히 표시돼요. 그 키를 역으로 추적하면 어디서 해시가 달라졌는지 금방 나와요.

팀의 모노레포 캐시 전략이 지금 어느 단계인지 점검해보세요. 패키지 매니저 전환을 고려 중이라면, pnpm workspace로의 이전이 캐시 구조를 가장 많이 단순화해줄 거예요.

## 참고자료

1. [GitHub Actions 아티팩트 & 캐시 | CI 속도·결과 관리 핵심 기술](https://velog.io/@okorion/GitHub-Actions-%EC%95%84%ED%8B%B0%ED%8C%A9%ED%8A%B8-%EC%BA%90%EC%8B%9C-CI-%EC%86%8D%EB%8F%84%EA%B2%B0%EA%B3%BC-%EA%B4%80%EB%A6%AC-%ED%95%B5%EC%8B%AC-%EA%B8%B0%EC%88%A0-1dfjtj31)
2. [S3 cache for GitHub Actions - RunsOn](https://runs-on.com/caching/s3-cache-for-github-actions/)
3. [GitHub Actions Self-Hosted Runner 대규모 운영과 보안 하드닝 가이드 | Chaos and Order](https://www.youngju.dev/blog/devops/2026-03-05-devops-github-actions-self-hosted-runner-ops)


---

*Photo by [Ferenc Almasi](https://unsplash.com/@flowforfrank) on [Unsplash](https://unsplash.com/photos/a-computer-screen-with-a-bunch-of-buttons-on-it--FHIdRVGets)*
