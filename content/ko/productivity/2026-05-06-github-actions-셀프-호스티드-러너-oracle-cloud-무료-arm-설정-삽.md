---
title: "GitHub Actions 셀프 호스티드 러너 Oracle Cloud 무료 ARM 설정 삽질 기록"
date: 2026-05-06T21:04:48+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "\ud638\uc2a4\ud2f0\ub4dc", "Python"]
description: "Oracle Cloud 무료 ARM에 GitHub Actions 셀프 호스티드 러너 설정 시 마주치는 실제 오류와 해결법. 월 2,000분 제한을 넘어 $0으로 CI/CD 운영한 삽질 기록."
image: "/images/20260506-github-actions-셀프-호스티드-러너-orac.webp"
technologies: ["Python", "Docker", "GitHub Actions", "Linux"]
faq:
  - question: "GitHub Actions 셀프 호스티드 러너 Oracle Cloud 무료 ARM 설정하는 법"
    answer: "GitHub Actions 셀프 호스티드 러너를 Oracle Cloud 무료 ARM에 설정하려면 Ampere A1 인스턴스 생성 후 linux-arm64 버전의 GitHub Actions Runner를 설치하고, systemd 서비스로 등록해야 재부팅 후에도 러너가 유지됩니다. 실제 설정 과정에서는 인스턴스 가용성 부족, ARM 아키텍처 호환성, 러너 데몬 자동 재시작 설정이 가장 많이 막히는 지점입니다. Workflow 파일에서 `runs-on: [self-hosted, linux, ARM64]` 라벨을 지정해 해당 러너를 명시적으로 타겟팅할 수 있습니다."
  - question: "Oracle Cloud Free Tier ARM 인스턴스 Out of Capacity 오류 해결 방법"
    answer: "Oracle Cloud Free Tier ARM 인스턴스는 물리 서버 자원 한계로 'Out of Host Capacity' 오류가 빈번하게 발생하며, 이는 Oracle의 공식 Known Issue입니다. 커뮤니티에서 공유된 우회 방법은 OCI SDK의 `launch_instance`를 반복 호출하다가 성공 시 알림을 보내는 Python 자동화 스크립트를 사용하는 것입니다. 리전 선택도 중요한데, 서울·도쿄보다 Ashburn(us-ashburn-1)이나 Phoenix(us-phoenix-1) 리전이 가용성이 높은 경향이 있습니다."
  - question: "GitHub Actions 셀프 호스티드 러너 재부팅 후 자동 실행 안 될 때"
    answer: "GitHub Actions Runner를 `./run.sh`로 포어그라운드에서 실행하면 VM 재부팅 시 러너가 종료됩니다. 이를 방지하려면 Runner를 systemd 서비스로 등록해 부팅 시 자동으로 시작되도록 설정해야 합니다. Runner 설치 디렉토리에서 `./svc.sh install` 및 `./svc.sh start` 명령으로 서비스 등록이 가능합니다."
  - question: "Oracle Cloud ARM에서 Docker Action x86 이미지 실행 안 되는 문제"
    answer: "ARM64 환경에서 `linux/amd64`로 고정된 Docker 베이스 이미지를 사용하는 Action은 QEMU 에뮬레이션으로 느리게 돌아가거나 아예 실패할 수 있습니다. 해결책은 Dockerfile에서 `--platform linux/arm64`를 명시하거나, multi-arch를 지원하는 이미지로 교체하는 것입니다. 서드파티 Action 사용 시에도 ARM64 지원 여부를 미리 확인하는 것이 좋습니다."
  - question: "GitHub Actions 무료 플랜 2000분 초과 시 셀프 호스티드 러너 비용 비교"
    answer: "GitHub Actions 기본 제공 Linux 러너는 월 2,000분 초과 시 분당 $0.008이 과금되어, 하루 100분씩 30일 사용하면 월 $24, 연간 $288에 달합니다. GitHub Actions 셀프 호스티드 러너 Oracle Cloud 무료 ARM 설정 삽질 기록에 따르면, Oracle Cloud의 Ampere A1 인스턴스(4 OCPU, 24GB RAM)를 활용하면 빌드 비용을 실질적으로 $0에 수렴시킬 수 있습니다. 다만 초기 설정 시간과 보안 관리 등 운영 유지 비용은 별도로 고려해야 합니다."
---

월 $0. 이 숫자 하나로 많은 개발자가 Oracle Cloud Free Tier ARM 인스턴스에 눈독을 들이기 시작했어요.

CI/CD 비용은 개인 개발자와 소규모 팀에게 작지 않은 부담이에요. GitHub Actions의 기본 제공 러너는 월 2,000분이 무료지만, 조금만 파이프라인이 복잡해지면 순식간에 소진돼요. Docker 빌드나 테스트 스위트가 많은 프로젝트라면 더더욱요. 그래서 많은 이들이 GitHub Actions 셀프 호스티드 러너를 Oracle Cloud 무료 ARM에 올리는 설정을 시도해요. 말은 쉬운데, 실제로 해보면 생각보다 막히는 지점이 많아요. 이 글은 그 삽질 기록을 데이터와 함께 정리한 거예요.

> **핵심 요약**
> - Oracle Cloud Free Tier의 Ampere A1 ARM 인스턴스는 최대 4 OCPU, 24GB RAM을 월 $0으로 제공하며, 이는 GitHub Actions 기본 러너(2-core, 7GB RAM) 대비 스펙이 세 배 이상 높아요.
> - GitHub Actions 셀프 호스티드 러너를 Oracle Cloud ARM에 세팅하는 과정에서 가장 많이 막히는 지점은 인스턴스 가용성, ARM 아키텍처 호환성, 그리고 Runner 데몬 설정 세 곳이에요.
> - Oracle Cloud의 Always Free ARM 인스턴스는 "Out of Capacity" 오류로 생성 자체가 막히는 사례가 빈번하며, 이를 우회하는 자동화 스크립트가 커뮤니티에 공유되어 있어요.
> - 셀프 호스티드 러너로 전환 시 월 빌드 비용을 GitHub-hosted 대비 실질적으로 $0에 수렴시킬 수 있지만, 운영 유지 비용(설정 시간, 보안 관리)은 별도로 계산해야 해요.

---

## Oracle Cloud Free Tier ARM, 왜 다들 쓰려고 할까요?

배경부터 잠깐 짚고 가요.

Oracle Cloud Infrastructure(OCI)는 2020년부터 Always Free 티어에서 Ampere A1 Compute를 제공하고 있어요. 계정당 3,000 OCPU 시간/월, 18,000 GB 메모리 시간/월이 무료예요. 이걸 고정 인스턴스로 환산하면 4 OCPU + 24GB RAM짜리 VM 하나를 계속 켜둘 수 있어요.

GitHub Actions가 제공하는 기본 ubuntu-latest 러너는 2-core CPU에 7GB RAM이에요. 이걸 초과하는 사용량은 분당 과금이 붙어요. 2026년 현재 GitHub의 Linux 러너 요금은 분당 $0.008이에요. 하루 100분 빌드를 30일 돌리면 월 $24, 연간 $288이 나와요.

Oracle Free ARM이 매력적인 이유가 바로 여기 있어요. 스펙은 더 좋은데, 비용은 $0이에요. 그러니 셀프 호스티드 러너를 Oracle Cloud 무료 ARM에 올리려는 시도가 끊이지 않는 거죠.

### 그런데 왜 삽질이 생기냐고요?

세 가지 장벽이 있어요.

첫째, **인스턴스 생성 자체가 안 돼요.** Oracle의 ARM 인스턴스는 물리 서버 자원이 한정적이라 특정 리전에서는 "Out of Host Capacity" 오류가 뜨면서 생성이 계속 실패해요. Oracle의 공식 Known Issue이기도 해요.

둘째, **ARM 아키텍처 호환성 문제.** x86 환경에서 검증된 Docker 이미지나 바이너리가 ARM64에서 바로 돌아가지 않는 경우가 있어요. 특히 레거시 도구들이 그래요.

셋째, **러너 데몬 자동 재시작 설정.** GitHub Actions Runner는 설치 후 서비스로 등록해야 하는데, systemd 설정 없이 그냥 두면 VM 재부팅 시 죽어버려요.

---

## 세 가지 핵심 삽질 포인트 분석

### 인스턴스 생성 실패: "Out of Capacity" 우회하기

이게 가장 먼저 맞닥뜨리는 벽이에요.

Oracle Free Tier ARM 인스턴스는 특정 Availability Domain에 물리적 자원이 몰려 있어요. 도쿄, 서울, 싱가포르 리전 기준으로 생성 성공까지 수십 번 재시도가 필요한 경우도 많았어요.

커뮤니티에서 공유된 방법은 OCI API를 반복 호출하는 자동화 스크립트예요. Bash나 Python으로 일정 간격마다 인스턴스 생성을 재시도하고, 성공하면 알림을 보내는 방식이에요. 실제로 marinesnow34가 공개한 Python 기반 스크립트도 이 원리를 써요 — OCI SDK로 `launch_instance`를 반복 호출하고, `ServiceError: Out of host capacity` 예외가 잡히면 대기 후 재시도하는 구조예요.

리전 선택도 중요해요. 경험적으로 Ashburn(us-ashburn-1)이나 Phoenix(us-phoenix-1) 리전이 서울/도쿄보다 가용성이 높은 경향이 있어요. 레이턴시를 조금 희생하더라도 안정적인 인스턴스 확보가 먼저예요.

### ARM 호환성: 생각보다 많이 걸려요

인스턴스를 떴어요. 이제 끝이냐고요? 아니에요.

GitHub Actions Runner 자체는 ARM64(aarch64) 빌드를 공식 제공해요. GitHub Releases 페이지에서 `linux-arm64` 버전을 받으면 돼요. 이건 문제없어요.

문제는 Workflow 안에서 쓰는 서드파티 도구들이에요. `actions/setup-node`는 ARM64를 잘 지원하지만, 일부 오래된 Action들은 x86_64 바이너리만 번들링해요. `runs-on: self-hosted` 태그에 `linux, ARM64`를 같이 붙여주면 라벨로 러너를 특정할 수 있어요.

Docker 기반 Action도 주의해야 해요. `Dockerfile`의 베이스 이미지가 `linux/amd64`로 고정된 경우 ARM에서 QEMU 에뮬레이션으로 돌아가거나 아예 실패해요. `--platform linux/arm64`를 명시하거나, multi-arch 이미지로 교체하는 게 깔끔해요.

### systemd 서비스 등록: 재부팅 후 러너가 죽는 이유

`./run.sh`로 포어그라운드에서 실행하면, VM 재부팅 시 당연히 꺼져요. 서비스로 등록해야 해요.

Runner 폴더에서 `sudo ./svc.sh install` 명령을 실행하면 systemd 서비스로 등록돼요. 그 다음 `sudo ./svc.sh start`로 시작하고, `sudo systemctl enable actions.runner.*`로 부팅 시 자동 시작을 켜줘요.

한 가지 더. Oracle Cloud의 ARM 인스턴스는 Oracle Linux 8이나 Ubuntu 22.04를 올리는 경우가 많은데, 방화벽 설정을 놓치면 러너가 GitHub에 연결을 못 해요. OCI의 Security List와 OS 레벨 firewalld/ufw 둘 다 확인해야 해요. GitHub Actions Runner는 outbound HTTPS(443)만 있으면 되는데, 이게 막혀 있으면 러너가 `Connecting to GitHub...` 상태에서 멈춰버려요.

### 비교: GitHub-hosted vs 셀프 호스티드 (Oracle Free ARM)

| 항목 | GitHub-hosted 러너 | 셀프 호스티드 (Oracle Free ARM) |
|------|-------------------|-----------------------------|
| 월 비용 | 무료 2,000분 초과 시 $0.008/분 | $0 (Always Free) |
| CPU | 2-core x86_64 | 최대 4 OCPU ARM64 |
| RAM | 7GB | 최대 24GB |
| 설정 난이도 | 없음 (즉시 사용) | 높음 (인스턴스 생성 + 러너 설정) |
| 보안 관리 | GitHub 관리 | 직접 관리 필요 |
| 아키텍처 호환 | x86_64 보장 | ARM64 — 도구별 확인 필요 |
| 가용성 | GitHub SLA 기준 | 본인 VM 상태에 의존 |
| 비공개 레포 적합성 | 높음 | 보안 설정에 따라 다름 |

결론부터 말하면, 월 빌드 시간이 2,000분 이하고 팀 규모가 작다면 굳이 셀프 호스티드를 세팅할 필요가 없어요. 설정에 들어가는 시간이 절약되는 비용보다 클 수 있거든요. 반면 월 빌드가 5,000분을 넘거나, 빌드 환경을 커스텀해야 하거나, ARM 네이티브 빌드가 필요한 프로젝트라면 Oracle Free ARM 셀프 호스티드는 꽤 매력적인 선택이에요.

---

## 실제로 쓸 때 주의할 점

**보안은 타협 없이.** 셀프 호스티드 러너는 GitHub 공식 문서에서도 "public repository에는 사용하지 말 것"을 권고해요. 외부 PR에서 악의적인 코드가 자신의 VM에서 실행될 수 있기 때문이에요. Private repo에서만 쓰거나, `GITHUB_TOKEN` 권한을 최소화하는 게 기본이에요.

**러너 라벨 전략을 미리 설계해요.** 여러 러너를 관리한다면 라벨로 구분하는 게 나중에 편해요. `self-hosted`, `linux`, `ARM64`, `oracle-free` 같은 라벨을 Workflow의 `runs-on`에 배열로 지정하면 특정 러너 그룹에만 잡을 보낼 수 있어요.

**모니터링을 붙여요.** Oracle Free ARM 인스턴스는 가끔 Oracle 측 유지보수로 재부팅될 수 있어요. systemd 서비스가 자동 재시작 설정이 돼 있더라도, 러너 상태를 GitHub 레포의 Settings → Actions → Runners에서 주기적으로 확인하거나, 간단한 heartbeat 스크립트를 연결해 두는 게 좋아요.

---

## 삽질을 줄이는 방법, 그리고 앞으로

GitHub Actions 셀프 호스티드 러너를 Oracle Cloud 무료 ARM에 올리는 작업은 처음엔 벽처럼 느껴지지만, 포인트를 알고 나면 반복 가능한 작업이에요.

핵심을 다시 짚으면:

- **인스턴스 생성 실패는 자동화 스크립트로 우회**하고, 리전은 가용성이 높은 곳을 선택하세요.
- **ARM 호환성은 Runner 자체보다 Workflow 내 서드파티 도구에서 문제**가 생겨요. 각 Action의 aarch64 지원 여부를 먼저 확인하세요.
- **systemd 서비스 등록과 방화벽 설정**은 빠뜨리면 나중에 찾기 어려운 문제로 남아요.

참고로, GitHub는 2024년부터 Larger Runners 옵션에 ARM64를 포함시켰지만 유료예요. Free Tier에서의 ARM 지원은 아직 로드맵에 없는 상태라, Oracle Free ARM 셀프 호스티드 조합은 당분간 비용 절감을 원하는 개발자들 사이에서 계속 쓰일 거예요.

그리고 설정에 드는 시간을 시급으로 환산해 봤나요? 그 숫자가 연간 GitHub Actions 요금보다 크다면, 어떤 선택이 진짜 더 싼 건지 다시 계산해볼 필요가 있어요.

## 참고자료

1. [Terraform execution using GitHub Actions with self-hosted runners on Oracle Cloud Infrastructure | b](https://medium.com/@subhashchandra.b/terraform-execution-using-github-actions-with-self-hosted-runners-on-oracle-cloud-infrastructure-7bedfc31df20)
2. [Oracle Cloud 인스턴스 자동 생성 매크로 만들기 | marinesnow34](https://marinesnow34.github.io/2025/02/03/oracle-cloud-ampere/)
3. [10. Github Action Hosted Runner 생성 :: Somaz의 IT 공부 일지](https://somaz.tistory.com/371)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
