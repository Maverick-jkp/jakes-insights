---
title: "Mac mini M4 GitHub Actions Docker 권한 오류 원인과 해결 방법"
date: 2026-03-25T20:11:17+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "Mac mini M4 Apple Silicon에서 GitHub Actions self-hosted runner 실행 시 Docker 권한 오류의 구조적 원인과 arm64 환경별 해결법을 단계별로 설명합니다."
image: "/images/20260325-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "GitHub Actions", "Linux"]
faq:
  - question: "GitHub Actions self-hosted runner Apple Silicon Docker 권한 오류 해결 arm64 2025"
    answer: "Apple Silicon Mac에서 GitHub Actions self-hosted runner Docker 권한 오류는 소켓 경로 불일치와 runner 실행 컨텍스트 문제가 복합적으로 작용해 발생합니다. Docker Desktop 4.13 이후 macOS 기본 소켓 경로가 ~/.docker/run/docker.sock으로 변경되었고, LaunchDaemon으로 등록된 runner는 Docker Desktop GUI 세션 밖에서 실행되어 소켓에 접근하지 못합니다. Docker Desktop 설정에서 'Allow the default Docker socket to be used' 옵션을 활성화하고 DOCKER_HOST 환경변수를 plist에 명시적으로 주입하면 해결할 수 있습니다."
  - question: "맥미니 M4 GitHub Actions runner docker exit code 1 오류 원인"
    answer: "Mac mini M4에서 발생하는 'Error: The process /usr/bin/docker failed with exit code 1' 오류는 대부분 runner 서비스 계정이 Docker Desktop 소켓에 접근하지 못해서 발생합니다. runner를 ./svc.sh install로 시스템 서비스로 등록하면 LaunchDaemon이 로그인 세션 밖에서 실행되어 Docker Desktop이 열어놓은 소켓과 컨텍스트가 달라집니다. 소켓 경로 불일치, 실행 컨텍스트 분리, arm64 아키텍처 불일치 세 가지 원인을 순서대로 확인해야 합니다."
  - question: "apple silicon mac docker sock 경로 var run docker sock 없다고 나올 때"
    answer: "Apple Silicon Mac에서 Docker Desktop 4.13 이후 기본 소켓 경로가 /var/run/docker.sock이 아닌 ~/.docker/run/docker.sock으로 변경되었기 때문에 기존 Linux나 x86 가이드를 그대로 따르면 소켓을 찾지 못합니다. Docker Desktop 설정에서 'Allow the default Docker socket to be used' 옵션을 켜면 /var/run/docker.sock으로 symlink가 생성됩니다. 이후 DOCKER_HOST 환경변수를 unix:///var/run/docker.sock으로 명시하면 정상 동작합니다."
  - question: "GitHub Actions self-hosted runner arm64 Docker 권한 오류 launchctl 서비스로 등록했을 때 해결법"
    answer: "GitHub Actions self-hosted runner를 launchctl 서비스로 등록했을 때 Docker 권한 오류가 발생한다면, LaunchAgent plist 파일에 DOCKER_HOST 환경변수를 직접 주입하는 방법이 가장 안정적입니다. ~/Library/LaunchAgents/ 경로의 runner plist에 EnvironmentVariables 키로 unix:///var/run/docker.sock을 추가한 뒤 launchctl unload 후 launchctl load로 재시작하면 됩니다. 빠른 임시 해결이 필요하다면 서비스 등록 대신 터미널에서 ./run.sh로 직접 실행해 로그인 세션 컨텍스트를 그대로 활용할 수도 있습니다."
  - question: "colima docker desktop 대신 쓰면 맥 CI 권한 문제 해결되나요"
    answer: "Colima는 Docker Desktop을 대체하는 경량 솔루션으로, macOS 로그인 세션에 종속되지 않아 LaunchDaemon으로 실행되는 runner와의 소켓 권한 문제를 구조적으로 해소할 수 있습니다. Docker Desktop GUI가 없어도 colima start 명령으로 Docker 데몬을 백그라운드에서 안정적으로 유지할 수 있어 24/7 CI 머신에 적합합니다. 다만 arm64 환경에서 x86_64 이미지를 실행할 때는 --platform linux/amd64를 명시해야 아키텍처 불일치로 인한 오류를 방지할 수 있습니다."
aliases:
  - "/tech/2026-03-25-github-actions-selfhosted-runner-apple-silicon-doc/"

---

Mac mini M4로 CI를 돌리다가 `Error: The process '/usr/bin/docker' failed with exit code 1` — 이 오류, 한 번 마주치면 꽤 당황스럽죠.

파이프라인 전체가 멈추는데 원인이 "권한"인지 "소켓"인지 "아키텍처"인지 바로 안 보이거든요. 그래서 많은 팀이 `/var/run/docker.sock` 권한부터 뒤지다가 결국 두 시간을 날려요.

문제는 단순히 권한이 없어서가 아니에요. Apple Silicon + macOS + Docker Desktop + GitHub Actions runner가 겹치는 구조적인 지점에서 발생하는 거라서, 하나만 고쳐서는 해결이 안 돼요. 이 글에서 그 구조를 풀어드릴게요.

다룰 내용을 미리 정리하면:
- Docker 권한 오류가 arm64 Mac에서 더 자주 발생하는 이유
- runner 서비스 계정 vs. 로그인 사용자 권한 차이
- 실전 해결 방법 세 가지와 각각의 trade-off
- 2026년 기준 권장 아키텍처

---

> **Key Takeaways**
> - GitHub Actions self-hosted runner를 macOS LaunchAgent/LaunchDaemon으로 실행할 때 Docker Desktop socket 접근 권한이 기본 차단되어 `exit code 1` 오류가 발생한다.
> - Apple Silicon(arm64)에서 Docker Desktop은 `/var/run/docker.sock` 대신 `~/.docker/run/docker.sock`을 기본 소켓 경로로 사용하며, x86 가이드를 그대로 따르면 소켓 경로 불일치가 생긴다.
> - runner를 `launchctl` 서비스가 아닌 로그인 세션에서 직접 실행하면 Docker Desktop GUI 컨텍스트에 접근할 수 있어 권한 문제를 즉시 우회할 수 있다.
> - 보안과 자동화를 모두 챙기려면 `docker` 그룹 설정 + 소켓 경로 명시 + 환경변수 주입을 조합하는 방식이 가장 안정적이다.

---

## arm64 Mac에서 유독 권한 오류가 잦은 이유

근본 원인은 macOS의 보안 샌드박스 구조에 있어요.

Linux에서는 Docker가 `/var/run/docker.sock` 소켓을 시스템 전체에서 공유해요. `docker` 그룹에 사용자를 추가하면 대부분 끝나죠. 그런데 Apple Silicon + macOS + Docker Desktop 조합에서는 세 가지가 달라져요.

**첫째, 소켓 경로가 달라요.**

Docker Desktop 4.13 이후 macOS에서 기본 소켓 경로가 `~/.docker/run/docker.sock`으로 바뀌었어요. x86 Mac이나 Linux 가이드에서 `/var/run/docker.sock`을 쓰라고 나와 있는데, arm64 Mac에서 그대로 따르면 소켓이 없다고 오류가 나요. Docker Desktop 설정에 symlink로 `/var/run/docker.sock`을 연결하는 옵션이 있긴 한데, 기본값이 아니에요.

**둘째, runner 실행 컨텍스트 문제예요.**

`./svc.sh install`로 runner를 시스템 서비스로 등록하면 LaunchDaemon으로 뜨는데, 이 프로세스는 macOS 로그인 세션 밖에서 실행돼요. Docker Desktop은 GUI 앱이라 로그인 세션에 묶여 있고요. 서비스 계정에서 Docker Desktop이 열어놓은 소켓에 접근하려고 하면, 그 소켓 자체가 다른 세션 컨텍스트에 있는 거예요.

**셋째, arm64 특유의 Rosetta 레이어 충돌도 있어요.**

arm64 환경에서 x86_64 이미지를 돌릴 때 `--platform linux/amd64`를 명시하지 않으면 Docker buildx가 예상치 못한 동작을 해요. 권한 오류처럼 보이지만 사실 아키텍처 불일치인 경우가 꽤 있어요.

---

## 세 가지 해결 방법과 현실적인 trade-off

### 방법 1: runner를 서비스가 아닌 로그인 세션에서 직접 실행

가장 빠른 방법이에요. `./svc.sh install` 대신 터미널에서 `./run.sh`로 직접 실행하면, runner가 현재 로그인 사용자의 세션에서 뜨고 Docker Desktop 소켓에 자연스럽게 접근할 수 있어요.

```bash
cd ~/actions-runner
./run.sh
```

단점은 명확해요. 로그아웃하면 runner가 죽어요. 재부팅 자동 복구도 안 되고요. 개발용 Mac 한두 대를 임시로 runner로 쓸 때는 괜찮지만, 24/7 CI 머신에는 적합하지 않아요.

### 방법 2: Docker Desktop "소켓 symlink" 활성화 + 환경변수 주입

Docker Desktop 설정에서 **"Allow the default Docker socket to be used"** 옵션을 켜면 `/var/run/docker.sock` symlink가 생겨요. 이걸 켠 뒤, runner 서비스 환경에 `DOCKER_HOST` 변수를 명시적으로 주입해요.

LaunchAgent plist 파일(`~/Library/LaunchAgents/actions.runner.*.plist`)에 아래를 추가해요:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>DOCKER_HOST</key>
    <string>unix:///var/run/docker.sock</string>
</dict>
```

그 다음 `launchctl unload` 후 `launchctl load`로 재시작하면 돼요.

서비스 자동 시작을 유지하면서 권한 문제를 해결한다는 게 이 방식의 장점이에요. 다만 Docker Desktop이 켜져 있어야 한다는 전제 조건이 있어요. Docker Desktop이 꺼지면 소켓도 없어지거든요.

### 방법 3: Colima로 Docker Desktop 대체

Docker Desktop 없이 Colima + Docker CLI를 쓰는 방법이에요. Colima는 macOS에서 Docker를 돌리는 경량 대안인데, 소켓을 `~/.colima/default/docker.sock`에 고정으로 만들어요. 서비스 컨텍스트에서도 소켓 경로가 일관되게 유지되고요.

```bash
brew install colima docker
colima start --arch aarch64 --vm-type vz
export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"
```

runner plist에 이 `DOCKER_HOST` 경로를 주입하면 안정적으로 돌아가요. Docker Desktop 라이선스 비용도 없애고요. 단, Colima는 macOS 재부팅 시 자동 시작 설정을 별도로 해줘야 하고, Docker Desktop 대비 GUI가 없어서 모니터링이 불편할 수 있어요.

### 방법 비교

| 기준 | 방법 1 (직접 실행) | 방법 2 (symlink + 환경변수) | 방법 3 (Colima) |
|------|------------------|--------------------------|----------------|
| 설정 난이도 | 낮음 | 중간 | 중간~높음 |
| 재부팅 자동 복구 | ❌ | ✅ | ✅ (설정 필요) |
| Docker Desktop 필요 | ✅ | ✅ | ❌ |
| arm64 네이티브 지원 | ✅ | ✅ | ✅ |
| 라이선스 비용 | Docker Desktop 기준 | Docker Desktop 기준 | 무료 |
| 운영 안정성 | 낮음 | 높음 | 높음 |
| **추천 대상** | 빠른 테스트 | 팀 공용 CI Mac | 비용 절감 + 안정성 |

방법 2와 방법 3 중 선택은 결국 Docker Desktop 라이선스 비용을 어떻게 보느냐예요. 250인 이상 기업은 Docker Desktop 유료 라이선스가 필수라 Colima가 실질적인 대안이 될 수 있어요. 소규모 팀이라면 방법 2가 더 빠르게 안정화할 수 있고요.

---

## GitHub Actions workflow에서 arm64 오류를 줄이는 실전 패턴

### 아키텍처 불일치 방지

runner가 arm64임에도 x86_64 이미지를 끌어오다가 실패하는 케이스예요. workflow YAML에 명시적으로 플랫폼을 지정해야 해요:

```yaml
- name: Build image
  run: docker buildx build --platform linux/arm64 -t myapp:latest .
```

cross-platform 빌드가 필요하면 `linux/amd64,linux/arm64` 두 개를 동시에 지정하는 멀티플랫폼 빌드를 써요. 이때 Rosetta 레이어 오버헤드가 생기는데, 빌드 시간이 x86 단독보다 30~50% 더 걸릴 수 있어요.

### 환경변수 주입을 workflow 레벨에서도 보장

runner 서비스 설정에만 의존하지 말고, workflow 파일에서도 `DOCKER_HOST`를 명시하는 게 더 안전해요:

```yaml
env:
  DOCKER_HOST: unix:///var/run/docker.sock

jobs:
  build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - name: Docker build
        run: docker build .
```

이렇게 하면 runner 설정이 바뀌거나 다른 머신으로 마이그레이션해도 workflow가 자체적으로 소켓 경로를 들고 다닐 수 있어요.

---

## 2026년 기준 실전 권장 구성

**상황별로 정리하면:**

**상황 1: Mac 한 대를 개발자 개인 CI로 쓸 때**
가장 흔한 케이스예요. 방법 2(symlink + 환경변수) + workflow 레벨 `DOCKER_HOST` 명시를 기본으로 가져가세요. 설정 시간 30분 안에 끝나요.

**상황 2: 팀 공용 Mac mini 클러스터를 운영할 때**
Docker Business 라이선스 비용이 부담되면 Colima 전환을 검토해볼 만해요. 단, 각 머신에 Colima 자동 시작 스크립트를 깔고, runner plist에 `DOCKER_HOST`를 박아 넣는 작업이 필요해요. 머신이 세 대 이상이면 Ansible 같은 도구로 프로비저닝을 자동화하는 게 시간을 절약해요.

**상황 3: 멀티플랫폼 빌드가 목표일 때**
Apple Silicon의 진짜 장점이 나오는 케이스예요. QEMU 에뮬레이션 없이 arm64 네이티브 빌드가 가능하고, x86_64 에뮬레이션은 Rosetta가 처리해요. `docker buildx create --use` 한 번만 실행해두면 멀티플랫폼 이미지를 한 번에 만들 수 있어요.

**앞으로 주시해야 할 신호:**
GitHub Actions는 2025년 말부터 공식 Apple Silicon 호스팅 runner 베타를 진행하고 있어요. 이게 GA가 되는 시점에 self-hosted runner의 필요성 자체가 줄어들 수 있어요. 단, 비용 구조를 감안하면 대용량 빌드는 여전히 self-hosted가 유리할 거예요.

---

## 정리하면

GitHub Actions self-hosted runner와 Apple Silicon Docker 권한 오류는 "권한 설정 한 줄"로 끝나는 문제가 아니에요.

핵심만 다시 짚으면:
- **소켓 경로 불일치**가 arm64 특유의 문제예요 — `~/.docker/run/docker.sock` vs. `/var/run/docker.sock`
- **LaunchDaemon 컨텍스트**는 Docker Desktop 세션과 분리돼 있어요 — 환경변수 주입이 필수예요
- **빠른 해결**: Docker Desktop symlink 설정 + plist 환경변수
- **장기 해결**: Colima 전환으로 Docker Desktop 의존성 제거

GitHub가 arm64 호스팅 runner를 본격 제공하는 시점이 오면 이 구조 자체가 바뀌겠지만, 그 전까지는 팀 상황에 맞는 방법을 골라서 쓰는 게 현실적이에요.

지금 파이프라인에서 exit code 1 오류가 반복된다면, 먼저 `echo $DOCKER_HOST`로 소켓 경로부터 확인해보세요. 그게 첫 번째 단서예요.

## 참고자료

1. [Github Actions Sef-hosted runners - Error: The process '/usr/bin/docker' failed with exit code 1 해결 ](https://gerrymandering.tistory.com/entry/Github-Actions-Sef-hosted-runners-Error-The-process-usrbindocker-failed-with-exit-code-1-%ED%95%B4%EA%B2%B0)
2. [GitHub Actions: Self-Hosted Runners - Dominic Rodemer's Blog](https://blog.dominicrodemer.com/github-actions-self-hosted-runners/)
3. [GitHub Actions Self-Hosted Runner: The Complete Practical Guide (2025 Edition) - DevOps Tooling](https://thedevopstooling.com/github-actions-self-hosted-runner/)


---

*Photo by [Vimal S](https://unsplash.com/@vimal_saran) on [Unsplash](https://unsplash.com/photos/a-black-and-white-photo-of-water-droplets-1jPUkDs9aCI)*
