---
title: "VPS에서 Docker Compose + Caddy 자동 HTTPS + GitHub Actions 무중단 배포 실전 구성과 트러블슈팅"
date: 2026-04-30T20:44:34+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "vps", "Kubernetes"]
description: "Docker Compose + Caddy + GitHub Actions로 git push 한 번에 HTTPS 자동 갱신과 무중단 배포를 구성하는 법. Nginx 설정 없이 단독 VPS에서 실전 트러블슈팅까지 정리했습니다."
image: "/images/20260430-docker-compose-단독-vps-caddy-자동.webp"
technologies: ["Docker", "Kubernetes", "AWS", "GitHub Actions", "Slack"]
faq:
  - question: "Docker Compose Caddy 자동 HTTPS 설정 방법"
    answer: "Caddy는 Caddyfile에 도메인만 명시하면 Let's Encrypt 인증서를 자동으로 발급하고 갱신해줘서 certbot을 별도로 설치하거나 cron 작업을 설정할 필요가 없어요. Docker Compose 단독 VPS Caddy 자동 HTTPS 무중단 배포 GitHub Actions 실전 구성 트러블슈팅 가이드 기준으로 `your-domain.com { reverse_proxy app:8080 }` 형태의 Caddyfile 2줄이면 HTTPS 설정이 끝납니다. 단, 도메인의 A 레코드가 VPS IP를 정확히 가리키고 있어야 인증서 발급이 정상 작동해요."
  - question: "GitHub Actions로 VPS 무중단 배포하는 방법"
    answer: "Docker Compose 단독 VPS Caddy 자동 HTTPS 무중단 배포 GitHub Actions 실전 구성 트러블슈팅 구조의 핵심은 GitHub Actions에서 SSH로 VPS에 접속한 뒤 `docker compose up -d` 명령을 실행하는 방식이에요. Blue/Green 배포 전략을 적용하면 구버전 컨테이너가 살아있는 동안 신버전을 먼저 띄우고, 준비가 완료된 시점에 Caddy 리버스 프록시가 트래픽을 자연스럽게 전환해줘서 다운타임이 발생하지 않아요. 배포 실패 시 빠른 롤백을 위해 `docker compose ps` 기반의 상태 확인 스크립트를 함께 준비하는 것이 필수입니다."
  - question: "VPS 배포 스택 Caddy vs Nginx 어떤 게 나은가요"
    answer: "Nginx는 레퍼런스가 풍부하지만 HTTPS 자동 갱신을 위해 Certbot과 cron 설정을 별도로 관리해야 하고 설정 파일 작성 난이도가 높은 편이에요. 반면 Caddy는 Caddyfile 문법이 단순하고 HTTPS 자동 갱신이 기본 내장되어 있어서 초기 설정과 유지 관리 부담이 훨씬 적습니다. 디버깅 투명성은 두 도구 모두 높은 편이라 문제 원인 파악이 어렵지 않아요."
  - question: "Docker Compose VPS 배포 permission denied 에러 해결"
    answer: "이 에러는 대부분 `sudo usermod -aG docker $USER` 명령으로 사용자를 docker 그룹에 추가한 뒤 로그아웃·재접속을 하지 않아 그룹 변경이 적용되지 않은 경우에 발생해요. VPS에 재접속하거나 `newgrp docker` 명령을 실행해 세션에 그룹 변경을 즉시 반영하면 해결됩니다. GitHub Actions 워크플로우에서 SSH 접속 후 동일 에러가 난다면 배포 스크립트 실행 계정에 docker 그룹이 올바르게 설정되어 있는지 확인하세요."
  - question: "사이드 프로젝트 배포 Kubernetes 대신 Docker Compose 써도 되나요"
    answer: "월 $20 수준의 단일 VPS에서 운영하는 사이드 프로젝트라면 Kubernetes는 관리 오버헤드 대비 실익이 거의 없어요. Docker Compose는 로컬 개발 환경과 프로덕션 환경의 구성 파일을 거의 그대로 공유할 수 있어서 환경 간 차이로 인한 문제가 줄고, GitHub Actions 무료 플랜(퍼블릭 레포 무제한, 프라이빗 월 2,000분)과 조합하면 추가 비용 없이 자동 배포 파이프라인을 구축할 수 있습니다."
---

Nginx 설정 파일 씨름하다 하루 날려본 적 있죠? 저도 그랬어요.

그런데 Caddy 알고 나서 그 시간이 확 줄었어요. `git push` 하나로 HTTPS 자동 갱신에 무중단 배포까지 — Docker Compose + Caddy + GitHub Actions 조합이 소규모 팀이나 사이드 프로젝트에서 비용 대비 가장 균형 잡힌 배포 스택으로 자리잡은 이유예요.

**이런 분들에게 맞아요:**
- 사이드 프로젝트나 소규모 서비스를 운영 중인 개발자
- AWS ECS나 K8s 쓰기엔 과한데, `git push`로 배포하고 싶은 분
- HTTPS 설정마다 Let's Encrypt 씨름하기 싫은 분

---

> **핵심 요약**
> - Caddy는 Let's Encrypt 인증서를 자동 발급/갱신해줘서 HTTPS 설정에 별도 작업이 필요 없어요.
> - Docker Compose의 Blue/Green 전략을 쓰면 다운타임 없이 컨테이너를 교체할 수 있어요.
> - GitHub Actions에서 SSH로 VPS에 접속해 `docker compose up -d`를 실행하는 구조가 핵심이에요.
> - Caddy v2.8 기준, `Caddyfile` 하나로 리버스 프록시 + 자동 HTTPS + 헬스체크를 모두 처리해요.
> - 배포 실패 시 롤백을 위한 `docker compose ps` 기반 상태 확인 스크립트가 필수예요.

---

## 왜 이 조합인가

Kubernetes는 강력하지만 오버스펙이에요. 월 $20짜리 VPS에 K8s 올리는 건 트럭에 쇼핑백 하나 싣는 격이거든요. Heroku 같은 PaaS는 비용이 예측 불가하고요.

그래서 이 세 조합이에요:

- GitHub Actions — 퍼블릭 레포 기준 무료, 프라이빗도 월 2,000분 무료
- Caddy v2 — 자동 HTTPS 기본 탑재. `certbot` 따로 돌릴 필요 없어요
- Docker Compose — 로컬 개발 환경과 프로덕션 환경의 간극을 줄여줘요

"무중단(Zero-downtime)"이 거창하게 들리지만 실제로는 단순해요. 구버전 컨테이너가 살아있는 동안 신버전을 띄우고, 준비되면 트래픽을 넘기는 거예요. 이 패턴을 Blue/Green 배포라고 부르고, Caddy의 리버스 프록시가 이 전환을 담당해요.

---

## 스택 비교: 이 조합 vs 대안들

| 항목 | Compose + Caddy + GH Actions | Nginx + Certbot + GH Actions | Coolify |
|------|-------------------------------|-------------------------------|---------|
| **HTTPS 설정** | 자동 (Caddyfile 2줄) | Certbot 수동 + cron | UI에서 클릭 |
| **배포 복잡도** | 중간 (YAML 직접 작성) | 높음 (nginx conf 필수) | 낮음 (UI 기반) |
| **디버깅 투명성** | 높음 | 높음 | 낮음 (블랙박스) |
| **Blue/Green 지원** | 스크립트로 가능 | 스크립트로 가능 | 제한적 |

Coolify가 편하긴 한데, 뭔가 안 될 때 원인 찾기가 어려워요. Nginx는 레퍼런스가 많지만 HTTPS 갱신 자동화에서 한 번씩 막혀요. Caddy는 그 중간 — 설정은 단순하면서 투명성은 살아있어요.

---

## 단계별 구성 가이드

### 사전 준비

- Ubuntu 22.04 이상 VPS (DigitalOcean, Hetzner, Vultr 등)
- 도메인 A 레코드가 VPS IP를 가리키고 있어야 해요
- Docker 및 Docker Compose v2 설치 완료

---

### Step 1: VPS에 Docker 설치

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

docker --version        # Docker version 26.x.x 확인
docker compose version  # Docker Compose version v2.x.x 확인
```

로그아웃 후 재접속해야 그룹 변경이 적용돼요. 이거 빠뜨리면 Actions에서 `permission denied` 에러 만나요.

---

### Step 2: Caddyfile 작성

```
your-domain.com {
    handle /api/* {
        reverse_proxy app:8080
    }
    handle {
        reverse_proxy frontend:3000
    }
    log {
        output file /var/log/caddy/access.log
    }
}
```

`app`과 `frontend`는 Docker Compose의 서비스 이름이에요. 같은 Docker 네트워크 안에 있으면 서비스 이름으로 바로 통신할 수 있거든요.

---

### Step 3: docker-compose.yml 작성

```yaml
version: "3.9"

services:
  caddy:
    image: caddy:2.8-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data      # 인증서 영구 저장
      - caddy_config:/config
    networks:
      - app_network
    restart: unless-stopped

  app:
    image: ghcr.io/your-username/your-app:${APP_VERSION:-latest}
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - NODE_ENV=production
    networks:
      - app_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s

networks:
  app_network:
    driver: bridge

volumes:
  caddy_data:    # 인증서 데이터 — 절대 삭제하지 마세요
  caddy_config:
```

`healthcheck`가 핵심이에요. 이게 없으면 컨테이너가 뜨는 중에 트래픽이 들어와서 500 에러가 발생해요.

---

### Step 4: GitHub Actions 워크플로우

```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: GitHub Container Registry 로그인
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker 이미지 빌드 & 푸시
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}

      - name: VPS에 배포
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/myapp
            docker compose pull app
            docker compose up -d --no-deps --wait app
            docker compose ps
```

`--wait` 플래그가 중요해요. `healthcheck`가 통과할 때까지 기다렸다가 구버전을 종료해주거든요. 이게 무중단의 핵심이에요.

---

## 실전 트러블슈팅

**Caddy가 인증서를 못 받아요**
도메인 A 레코드가 아직 VPS IP를 안 가리킬 때 발생해요. `dig your-domain.com`으로 확인하고, 전파까지 최대 48시간 기다려야 해요. 급하면 `tls internal`로 로컬 인증서로 먼저 테스트하세요.

**`--wait` 실행 중 timeout**
`healthcheck`의 `start_period`를 늘려주세요. JVM 앱이나 초기화가 무거운 앱은 30~60초가 필요할 수 있어요.

**caddy_data 볼륨 실수로 삭제**
인증서가 날아가면 Let's Encrypt 재발급이 Rate Limit에 걸려요. 도메인당 주 5회 제한이에요. `docker compose down -v`는 절대 쓰지 마세요. 저도 이거 한 번 당했어요.

---

## 프로덕션 체크리스트

- [ ] `.env` 파일은 `.gitignore`에 반드시 포함
- [ ] `caddy_data` 볼륨 백업 주기 설정 (월 1회 이상)
- [ ] `healthcheck` 엔드포인트가 DB 연결 상태까지 확인하는지 검증
- [ ] VPS 방화벽에서 80, 443 포트만 열고 8080 등 앱 포트는 닫기
- [ ] 배포 실패 시 Slack/Discord 알림 연결 (`if: failure()` 활용)

---

## 마무리

`git push` 하나로 HTTPS 자동 갱신과 무중단 배포를 동시에 해결하는 스택이에요. K8s 없이도 충분히 프로덕션 수준의 파이프라인을 만들 수 있거든요.

처음엔 Caddyfile 설정과 Compose healthcheck가 낯설 수 있어요. 그래도 한 번 손에 익히면 새 프로젝트마다 이 템플릿 그대로 가져다 쓸 수 있어요. 실제로 저는 이 구조를 두 번째 프로젝트부터 복붙으로 시작했어요.

**다음 단계로 추천하는 것들:**
- Caddy 공식 문서: [caddyserver.com/docs](https://caddyserver.com/docs)
- `appleboy/ssh-action` 심화 옵션 (타임아웃, 다중 서버 배포)
- 트래픽이 늘면 Compose 대신 Docker Swarm으로 수평 확장 고려

막히는 부분 있으면 댓글로 남겨주세요. 같이 해결해봐요.

## 참고자료

1. [Gighub Action , Docker Compose, Nginx, code deploy 무중단 배포](https://jsw5913.tistory.com/15)
2. [DevOps 골든패스 2026: GitHub Actions와 배포 안전장치 설계 | Chaos and Order](https://www.youngju.dev/blog/devops/2026-03-04-devops-golden-path-2026)
3. [[CI/CD] blue/green 무중단 배포 (Docker, Github Actions, Nginx) — J_hzlo](https://jhzlo.tistory.com/82)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
