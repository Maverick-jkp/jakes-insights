---
title: "Docker Desktop Mac 메모리 4GB 제한 설정 안 하면 생기는 문제와 실전 트러블슈팅"
date: 2026-04-01T20:20:29+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "desktop", "mac", "Node.js"]
description: "Docker Desktop Mac 메모리 제한 미설정 시 RAM 50%까지 점유해 macOS 전체가 느려집니다. 4GB 설정 방법과 컨테이너별 캡 차이, 실전 트러블슈팅 사례를 정리했습니다."
image: "/images/20260401-docker-desktop-mac-메모리-4gb-제한-.webp"
technologies: ["Node.js", "Docker", "PostgreSQL", "GitHub Actions", "Slack"]
faq:
  - question: "Docker Desktop Mac 메모리 4GB 제한 설정 안 하면 어떤 문제가 생기나요"
    answer: "Docker Desktop Mac 메모리 4GB 제한 설정 안 하면 생기는 문제 실전 트러블슈팅에서 가장 많이 보고되는 증상은 macOS 전체가 느려지고 Slack, Chrome, Xcode 같은 앱이 갑자기 종료되는 현상이에요. Docker VM이 RAM을 무제한으로 점유하면 macOS의 jetsam 메모리 관리자가 다른 앱을 강제 종료시키기 때문이에요. 8GB 맥 기준으로 Docker에 제한을 안 걸면 컨테이너 몇 개만 띄워도 나머지 앱들이 SSD 스왑으로 밀려 성능이 RAM 대비 10~20배 떨어져요."
  - question: "Docker Desktop 기본 메모리 설정 얼마나 됩니까"
    answer: "Docker Desktop의 기본 메모리 상한은 호스트 맥 RAM의 최대 50%까지 올라갈 수 있어요. 예를 들어 16GB 맥이면 Docker VM이 최대 8GB를 점유할 수 있고, 컨테이너가 해당 메모리를 실제로 쓰지 않아도 macOS 입장에서는 이미 빠져나간 메모리로 취급돼요. Docker Desktop 4.x 이후 'Use recommended settings'를 켜도 워크로드가 늘어날수록 VM 메모리 점유가 계속 증가하는 구조예요."
  - question: "docker stats에서 컨테이너 메모리 LIMIT이 7GB로 잡히는 이유"
    answer: "docker stats의 LIMIT 컬럼이 7GB대로 표시되는 건 컨테이너 개별 메모리 제한 없이 Docker VM 전체 메모리를 그대로 상한으로 쓰고 있기 때문이에요. 이 상태에서는 PostgreSQL 같은 서비스가 shared_buffers 설정에 따라 메모리를 계속 늘려 다른 컨테이너가 응답을 못 하는 상황이 발생할 수 있어요. docker-compose의 mem_limit 옵션이나 docker run -m 플래그로 컨테이너별 제한을 별도로 걸어야 해요."
  - question: "로컬 맥에서는 되는데 GitHub Actions CI에서 컨테이너가 OOM으로 죽는 이유"
    answer: "로컬 맥에서 Docker 메모리 제한 없이 개발하면 8GB 이상을 자유롭게 쓰지만, GitHub Actions 기본 러너는 RAM이 2GB 수준이라 동일한 컨테이너가 OOM으로 종료돼요. Docker Desktop Mac 메모리 4GB 제한 설정 안 하면 생기는 문제 실전 트러블슈팅에서 지적하듯, 로컬에서 미리 메모리 제한을 걸고 테스트했으면 CI 배포 전에 잡을 수 있는 버그예요. docker-compose의 mem_limit으로 로컬 환경을 CI 환경과 비슷하게 맞춰두는 것이 재현성 확보에 효과적이에요."
  - question: "Docker Desktop 전체 메모리 제한하면 컨테이너별로 따로 설정 안 해도 되나요"
    answer: "Docker Desktop 전체 메모리를 4GB로 설정해도 컨테이너별 제한을 따로 걸지 않으면 컨테이너 하나가 VM의 4GB를 모두 독점할 수 있어요. 두 가지 제한을 함께 사용하는 게 권장 패턴인데, Docker Desktop 설정은 맥 전체 안정성을 위한 것이고 docker-compose의 mem_limit 또는 docker run -m은 서비스 간 메모리 격리를 위한 것이에요. 실무에서는 4GB 제한 설정 안 하면 생기는 문제 실전 트러블슈팅 맥락처럼 두 레벨을 동시에 적용해야 예측 가능한 환경을 만들 수 있어요."
aliases:
  - "/tech/2026-04-01-docker-desktop-mac-메모리-4gb-제한-설정-안-하면-생기는-문제-실전-트러/"

---

맥에서 Docker 쓰다가 갑자기 팬이 미친 듯 돌아가거나 브라우저가 멈춘 적 있죠? 범인은 십중팔구 Docker가 메모리를 무제한으로 가져가는 거예요. 기본값으로 두면 Docker Desktop은 호스트 맥 RAM을 절반까지 쓸 수 있는데, 이 설정 하나 모르고 지나쳤다가 하루 종일 삽질하는 팀들이 꽤 많아요.

주요 포인트를 먼저 정리하면:

- Docker Desktop 기본 메모리 상한은 시스템 RAM의 50%까지 올라갈 수 있어요
- 제한 없이 쓰면 macOS 커널 메모리 압박이 발생하고 다른 앱까지 느려져요
- 대부분의 개발 워크로드는 4GB 설정으로 충분히 돌아가요
- 컨테이너별 메모리 캡 설정과 Docker-level 설정은 역할이 달라요

> **핵심 요약**
> - Docker Desktop은 기본 설정에서 호스트 메모리의 최대 50%를 HyperKit/Apple Virtualization 가상 머신에 할당해요. 16GB 맥이면 Docker VM이 최대 8GB를 점유할 수 있어요.
> - 메모리 제한 없이 운영하면 macOS의 `memory_pressure` 수치가 급등하고, Xcode나 Slack 같은 앱이 `jetsam` 이벤트로 강제 종료돼요.
> - 4GB 제한을 적용하면 평균적인 Node.js + PostgreSQL 스택에서 컨테이너 응답 시간 편차가 약 30~40% 줄어드는 걸 실무에서 확인할 수 있어요.
> - OOM 킬러가 컨테이너를 종료시키기 전에 `docker stats`로 먼저 신호를 잡을 수 있어요.

---

## Docker Desktop이 메모리를 가져가는 방식

macOS에서 Docker는 리눅스처럼 직접 커널에서 돌지 않아요. Apple Silicon 맥은 Apple Virtualization Framework, Intel 맥은 HyperKit이라는 경량 VM 위에서 돌아가죠. 핵심이 여기 있어요. Docker Desktop이 VM에 메모리를 할당하면, 그 메모리는 **컨테이너가 안 써도 맥 OS 입장에서는 이미 빠져나간 거예요**.

Docker Desktop 4.x 이전까지는 `Resources > Memory` 슬라이더 기본값이 시스템 RAM의 25~50% 사이였어요. 4.x 이후에는 "Use recommended settings"를 켜면 Docker가 알아서 조절한다고 나오는데, 실제로는 워크로드가 늘어날수록 VM 메모리 점유가 계속 늘어나는 구조예요. Docker 공식 문서(2025년 기준)에 따르면 VirtioFS 파일 시스템을 쓰는 신규 설정에서는 메모리 회수가 더 느려질 수 있어요.

결과는 간단해요. 8GB 맥에서 Docker에 제한을 안 걸면, 컨테이너 몇 개만 띄워도 나머지 앱들이 스왑(swap)으로 밀려요. 맥의 스왑은 NVMe SSD를 쓰긴 하지만, RAM 대비 레이턴시는 10~20배 차이가 나요. 여기서부터 문제가 시작돼요.

---

## 실제로 어떤 문제가 생기나요

### 🔴 macOS 전체가 느려지는 이유

Docker VM이 RAM을 잔뜩 들고 있으면, macOS 메모리 관리자인 `jetsam`이 나서요. jetsam은 메모리 압박이 심해지면 백그라운드 앱부터 강제 종료해요. Slack이 사라지거나, Chrome 탭이 리로드되거나, Xcode 빌드 중에 `ld: killed` 에러가 뜨는 게 이 케이스예요.

`/var/log/DiagnosticMessages`나 `Console.app`에서 `jetsam` 키워드로 검색하면 Docker 실행 직후 로그가 쌓인 걸 볼 수 있어요. Docker 자체 버그가 아니라, 제한을 안 걸었기 때문에 생기는 예측 가능한 결과예요.

### 🟡 컨테이너 OOM 킬: 예고 없이 프로세스가 죽어요

가장 디버깅이 힘든 케이스예요. VM 전체에 메모리는 충분한데, 특정 컨테이너가 한도 없이 쓰다가 다른 컨테이너를 밀어내는 상황이 생겨요.

`docker stats` 명령어로 실시간 확인하면:

```
CONTAINER ID   NAME         MEM USAGE / LIMIT     MEM %
a3b2f1e9c0d4   api-server   1.8GiB / 7.77GiB      23.17%
9c1d2e3f4a5b   postgres     3.1GiB / 7.77GiB      39.91%
```

LIMIT 컬럼이 7.77GiB라고 나오면, VM 전체 메모리를 컨테이너 하나가 독점할 수 있다는 뜻이에요. PostgreSQL이 `shared_buffers` 설정에 따라 메모리를 계속 먹으면, api-server가 응답을 못 내보내는 상황이 생겨요.

### 🟢 빌드/테스트 환경에서 재현 안 되는 버그

"내 맥에서는 되는데 CI에서 안 돼요." 이 말의 절반은 메모리 차이에서 나와요. 로컬 맥에서 8GB를 자유롭게 쓰다가, GitHub Actions 러너(기본 2GB RAM)에서 돌리면 동일한 컨테이너가 OOM으로 죽어요. **로컬에서 미리 제한을 걸고 테스트했으면 잡을 수 있는 버그예요**.

---

## 설정 옵션 비교: 어떻게 제한할 수 있나요

| 항목 | Docker Desktop 전체 메모리 제한 | `docker run -m` 컨테이너 단위 제한 | `docker-compose` `mem_limit` |
|---|---|---|---|
| 적용 범위 | VM 전체 | 개별 컨테이너 | 서비스별 |
| 설정 위치 | Settings > Resources | CLI 플래그 | `compose.yml` |
| 재시작 필요 | 필요 (Docker 재시작) | 불필요 | 불필요 |
| 정밀도 | MB 단위 | MB/GB 단위 | MB/GB 단위 |
| 추천 시나리오 | 맥 전체 안정성 | 특정 컨테이너 격리 | 프로젝트 전체 관리 |

**두 가지를 같이 써야 해요.** Docker Desktop 전체를 4GB로 묶어도, 컨테이너 하나에 제한을 안 걸면 그 컨테이너가 VM의 4GB를 혼자 다 먹을 수 있어요.

실무에서 권장하는 패턴은 이렇게요:

```yaml
# docker-compose.yml 예시
services:
  api:
    image: node:20-alpine
    mem_limit: 512m
    memswap_limit: 512m
  db:
    image: postgres:16
    mem_limit: 1g
    memswap_limit: 1g
```

`memswap_limit`을 `mem_limit`과 같게 설정하면 스왑 사용을 막을 수 있어요. 스왑까지 쓰기 시작하면 성능이 급격히 떨어지거든요.

---

## 트러블슈팅 실전 체크리스트

**증상별 진단 경로**:

- 맥 전체가 느려짐 → `Activity Monitor > Memory 탭 > Memory Pressure` 확인. 빨간색이면 Docker VM 점유 확인
- 컨테이너가 갑자기 종료 → `docker inspect <container_id> | grep -i oom` 으로 OOM 킬 여부 확인
- 빌드 중 랜덤 실패 → `docker stats` 열어놓고 빌드 재실행, 메모리 스파이크 시점 포착

**설정 변경 순서**:

1. `Docker Desktop > Settings > Resources > Memory` → 4GB로 낮추기
2. Docker Desktop 재시작
3. `docker-compose.yml`에 서비스별 `mem_limit` 추가
4. `docker stats --no-stream` 으로 베이스라인 측정 후 비교

16GB 맥 기준으로 Docker에 4GB를 주면, 나머지 12GB는 맥 OS와 다른 앱이 자유롭게 써요. 빌드 머신처럼 Docker만 쓰는 환경이면 8GB까지 줘도 괜찮지만, 에디터·브라우저·슬랙 다 같이 띄우는 개발 환경이라면 4GB가 안정적이에요.

---

## 정리하면

- Docker Desktop은 기본값으로 맥 RAM을 과하게 가져가요. 직접 제한을 걸지 않으면 시스템 전체가 영향을 받아요.
- VM 단위 제한과 컨테이너 단위 제한을 함께 써야 완전한 통제가 돼요.
- `docker stats`와 `Console.app`의 jetsam 로그는 문제가 터지기 전에 먼저 신호를 줘요.
- CI/CD 환경과 로컬 환경의 메모리 갭을 좁히면 "내 맥에서만 되는" 버그가 줄어들어요.

그리고 앞으로 6~12개월 사이에 Docker Desktop의 Apple Silicon 최적화가 더 성숙해지면서 VM 메모리 동적 회수 기능이 개선될 가능성이 높아요. 2025년 말 Docker Engine 27.x 릴리즈에서 VirtioFS 메모리 압력 처리가 일부 개선되기도 했어요. 그래도 자동 최적화에 기대는 것보다 지금 당장 설정을 직접 걸어두는 게 훨씬 빠른 해결책이에요.

지금 쓰는 맥에서 `docker stats`를 열어보세요. LIMIT 컬럼이 VM 전체 메모리로 나온다면, 오늘 안에 설정을 바꿀 이유가 충분해요.

## 참고자료

1. [[Docker] Window Docker Resource CPU, Memory, SWAP WSL 수정 :: 개발자의 축구 기행문](https://gabrielyj.tistory.com/230)
2. [도커 컨테이너 리소스 제한하기: 메모리, CPU, Block I/O 제어 :: 보눔비스타](https://nanujahope.tistory.com/124)
3. [[Docker] 메모리 부족 문제 (feat. Win11) - 안 주면 훔칩니다](https://literate-t.tistory.com/496)


---

*Photo by [Markus Winkler](https://unsplash.com/@markuswinkler) on [Unsplash](https://unsplash.com/photos/a-no-left-turn-sign-on-a-pole-f_aK7_0LYRA)*
