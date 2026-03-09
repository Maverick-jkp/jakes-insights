---
title: "WSL2로 윈도우11에서 Docker Desktop 없이 Ubuntu 24.04 + containerd 직접 설치하기"
date: 2026-03-09T20:08:59+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "wsl2", "docker", "desktop", "Kubernetes"]
description: "WSL2와 Ubuntu 24.04에 containerd를 직접 설치해 Docker Desktop 월 $21/유저 비용을 절감하는 방법. nerdctl로 기존 Docker 명령어 호환성을 유지하며 Kubernetes 표준 런타임을 윈도우11에서 바로 구성합니다."
image: "/images/20260309-wsl2-docker-desktop-없이-ubuntu-.webp"
technologies: ["Docker", "Kubernetes"]
faq:
  - question: "WSL2 Docker Desktop 없이 Ubuntu 24.04 containerd 직접 설치 윈도우11 실전 세팅 방법"
    answer: "윈도우11 빌드 22000 이상에서 PowerShell에 'wsl --install -d Ubuntu-24.04' 명령어 하나로 WSL2와 Ubuntu 24.04를 설치한 뒤, apt로 containerd를 설치하고 SystemdCgroup을 true로 설정하면 됩니다. 이 세팅은 Docker Desktop 없이 containerd를 직접 운영하는 가장 깔끔한 방법으로, 별도 PPA 없이 Ubuntu 공식 저장소만으로 구성이 완료됩니다."
  - question: "Docker Desktop 유료 전환 이후 무료 대안이 있나요"
    answer: "Docker Desktop은 250인 이상 기업 기준 월 $21/유저로, 팀 10명이면 연간 약 250만 원의 비용이 발생합니다. WSL2 위에 containerd를 직접 설치하거나 Podman을 사용하는 방식이 대표적인 무료 대안이며, 특히 containerd + nerdctl 조합은 기존 docker 명령어 습관을 거의 그대로 유지할 수 있어 마이그레이션 비용이 낮습니다."
  - question: "nerdctl이 docker 명령어랑 호환되나요"
    answer: "nerdctl은 'docker run', 'docker build', 'docker compose'와 명령어 구조가 거의 동일하게 설계되어 있어, 기존 Docker 워크플로를 대부분 그대로 가져올 수 있습니다. 기존 docker-compose.yml 파일도 'nerdctl compose' 명령으로 바로 읽을 수 있어 스타트업이나 소규모 팀의 마이그레이션에 특히 적합합니다."
  - question: "WSL2 Docker Desktop 없이 Ubuntu 24.04 containerd 설치할 때 SystemdCgroup 설정 왜 해야 하나요"
    answer: "Ubuntu 24.04는 cgroup v2를 기본으로 사용하는데, SystemdCgroup을 true로 설정하지 않으면 컨테이너 내부 프로세스가 이 환경에서 정상적으로 동작하지 않습니다. containerd config.toml 파일에서 'SystemdCgroup = false'를 'SystemdCgroup = true'로 변경하는 것이 WSL2 Ubuntu 24.04 환경에서 containerd를 안정적으로 운영하기 위한 핵심 설정입니다."
  - question: "containerd vs Podman 뭐가 더 나은가요"
    answer: "containerd + nerdctl 조합은 Kubernetes와의 네이티브 CRI 연동, Docker CLI 호환성, 약 30~50MB의 낮은 메모리 사용량이 장점으로 K8s 기반 팀에 적합합니다. Podman은 데몬 프로세스 없이 각 컨테이너가 독립 프로세스로 실행되는 rootless 구조 덕분에 보안 요구사항이 높은 금융·공공 환경에서 선호되지만, docker-compose와의 완전한 호환성에서 일부 엣지케이스가 존재합니다."
---

Docker Desktop 청구서, 받아본 적 있어요? 팀 10명이면 연간 약 250만 원이에요. 그 순간부터 "꼭 Docker Desktop이어야 하나?"라는 질문이 시작되죠.

> **핵심 요약**
> - Docker Desktop 유료 전환(250인 이상 기업 기준 월 $21/유저) 이후, WSL2 + containerd 직접 세팅이 현실적 대안으로 자리잡았어요.
> - Ubuntu 24.04 LTS는 2029년까지 공식 지원이 보장돼서, 장기 안정성이 필요한 팀에 맞는 베이스예요.
> - containerd는 CNCF 졸업 프로젝트로, Kubernetes 표준 런타임이며 Docker Engine보다 메모리 풋프린트가 낮아요.
> - nerdctl을 같이 쓰면 기존 Docker 명령어 습관 그대로 옮겨올 수 있어요.
> - 윈도우11 빌드 22000 이상에서는 `wsl --install` 단일 명령으로 WSL2 + Ubuntu 설치까지 끝나요.

---

## Docker Desktop 없이 가는 사람들이 늘어난 이유

2022년 8월, Docker Inc.는 대기업 상업적 사용에 유료 구독을 의무화했어요. Pro 플랜 기준 월 $21/유저. 숫자만 보면 작아 보이지만, 팀 규모가 커질수록 빠르게 부담이 쌓여요.

그래서 나온 흐름이 두 가지예요. 첫째, Rancher Desktop 같은 대체 툴. 둘째, WSL2 위에서 containerd를 직접 설치해 Docker 레이어 자체를 걷어내는 방법. 윈도우 개발자라면 두 번째가 훨씬 더 직접적이에요.

Kubernetes 1.20 이후로 Docker shim이 deprecated되고 containerd가 표준 CRI로 자리잡으면서, "어차피 K8s 쓸 건데 왜 Docker Desktop을 거쳐야 하지?"라는 질문이 자연스럽게 생겨났죠.

---

## WSL2 + Ubuntu 24.04 환경 기반 이해하기

WSL2는 단순한 리눅스 에뮬레이터가 아니에요. Hyper-V 기반 경량 VM 위에서 실제 리눅스 커널을 돌려요. 2026년 기준 최신 WSL 버전은 GPU 패스스루, `systemd` 기본 활성화, 네트워크 미러링 모드를 지원해요.

윈도우11 빌드 22000 이상이면 이것 하나로 시작해요:

```powershell
wsl --install -d Ubuntu-24.04
```

WSL2 활성화 + Ubuntu 24.04 설치까지 자동으로 처리돼요. 재부팅 후 Ubuntu 터미널을 열면 사용자 계정 생성 단계로 바로 넘어가죠.

Ubuntu 24.04 LTS "Noble Numbat"는 2029년 4월까지 표준 지원이 보장돼요. containerd 1.7.x와 runc 1.1.x가 공식 apt 저장소에 포함돼 있어서 별도 PPA 없이 깔끔하게 설치돼요.

### containerd 직접 설치 흐름

```bash
sudo apt update
sudo apt install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl enable --now containerd
```

`SystemdCgroup = true` 설정이 핵심이에요. 이 옵션 없이는 컨테이너 내부 프로세스가 cgroup v2 환경에서 제대로 안 돌아요. Ubuntu 24.04는 cgroup v2를 기본으로 쓰거든요.

---

## 세 가지 접근 방식 비교

| 항목 | Docker Desktop | containerd + nerdctl | Podman (rootless) |
|------|---------------|---------------------|------------------|
| **라이선스 비용** | 기업 $21/유저/월 | 무료 | 무료 |
| **Docker CLI 호환성** | 완전 호환 | nerdctl로 대부분 호환 | 대부분 호환 |
| **Kubernetes 연동** | 별도 설정 필요 | 네이티브 CRI | CRI-O 경유 |
| **메모리 사용** | GUI 포함 약 500MB+ | 약 30-50MB | 약 20-40MB |
| **설치 난이도** | 낮음 (GUI) | 중간 (CLI 설정) | 중간 |
| **적합한 상황** | 빠른 온보딩, 소규모 | 비용 절감, K8s 친화 | 보안 우선 |

nerdctl은 `docker run`, `docker build`, `docker compose`와 명령어 구조가 거의 동일해서 기존 Docker 워크플로를 그대로 가져올 수 있어요. containerd + nerdctl + BuildKit 조합이 현재 가장 많이 쓰이는 패턴이에요.

Podman은 rootless 컨테이너에서 강점을 보여요. 데몬 프로세스 없이 각 컨테이너가 독립 프로세스로 실행되는 구조라서 보안 요구사항이 높은 환경에서 선호돼요. 다만 `docker-compose`와의 완전한 호환성은 아직 일부 엣지케이스가 있어요.

---

## 어떤 팀에 어떤 선택이 맞을까요?

**스타트업 개발팀 10-30명**: containerd + nerdctl 조합을 권장해요. 기존 `docker-compose.yml`을 `nerdctl compose`로 바로 읽을 수 있어서 마이그레이션 비용이 낮거든요. 추천 세팅은 WSL2 Ubuntu 24.04 + containerd 1.7.x + nerdctl 1.7.x + BuildKit이에요.

**K8s 기반 프로덕션 팀**: 로컬 개발 환경도 containerd로 맞추는 게 일관성 면에서 훨씬 나아요. "로컬에서 됐는데 클러스터에서 안 된다"는 문제의 상당 부분이 런타임 차이에서 생기거든요. 추천 세팅은 containerd + crictl + k3d예요.

**금융·공공 환경**: rootless 컨테이너가 필수라면 Podman이 더 맞아요. WSL2 위에서 잘 돌아가고, Ubuntu 24.04 apt 저장소에서 바로 설치할 수 있어요.

---

## 앞으로 뭘 봐야 할까요?

이 방식은 이미 "실험적 선택"이 아니에요. 그런데 앞으로 6개월 안에 볼 변화가 있어요.

Microsoft가 WSL2 네트워킹 레이어를 대폭 개선하고 있어서, NAT 모드에서 미러링 모드로 전환하면 containerd 컨테이너의 네트워크 접근성이 더 자연스러워질 거예요. BuildKit의 WSL2 통합이 더 성숙해지면 멀티플랫폼 빌드 경험도 containerd에서 기대할 수 있고요. 한 가지 주시할 건 nerdctl의 `docker compose` 호환 커버리지예요. 현재 99% 수준이지만 일부 플러그인 지원이 아직 불완전해요.

- **정리하면**:
  - 팀 규모가 클수록 containerd 직접 설치의 ROI가 빠르게 올라가요.
  - Ubuntu 24.04 LTS + containerd 1.7.x 조합은 2029년까지 안정적인 지원을 받아요.
  - nerdctl로 Docker CLI 호환성을 유지하면 마이그레이션 러닝커브가 생각보다 낮아요.
  - K8s 표준 런타임과 로컬 환경을 맞추면 "내 로컬에서는 됐는데" 문제가 확실히 줄어요.

지금 Docker Desktop 청구서를 받고 있다면, 이번 주 안에 한 번 직접 해보세요. 설치는 30분이면 끝나요. 그 30분이 연간 수백만 원짜리 판단이 될 수도 있어요.

막히는 부분이 있었나요? 어떤 단계에서 어려움을 겪었는지 댓글로 알려주세요.

## 참고자료

1. [윈도우 11에서 WSL로 우분투 설치하고 리눅스 쓰는 방법](https://bluesharehub.com/windows-11-wsl-ubuntu-install/)
2. [[Linux] Windows 11에서 WSL2 설치하고 VSCode 연동하기](https://cuffyluv.tistory.com/245)
3. [WSL 설치부 Docker CLI 설치까지 완벽 가이드 🐳 :: 혠의 기술블로그](https://devhyen.tistory.com/25)


---

*Photo by [BoliviaInteligente](https://unsplash.com/@boliviainteligente) on [Unsplash](https://unsplash.com/photos/a-3d-rendering-of-the-word-sw2-surrounded-by-cubes-dIJxTWRelA4)*
