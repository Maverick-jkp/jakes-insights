---
title: "Docker Compose와 Nginx로 단독 VPS에서 Blue-Green 무중단 배포 구성하는 실전 가이드"
date: 2026-04-05T19:59:12+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "vps", "Kubernetes"]
description: "Docker Compose와 Nginx만으로 단독 VPS에서 blue-green 무중단 배포를 구현하는 방법. 셸 스크립트 하나로 컨테이너를 교체하고 Kubernetes 없이 운영 복잡도를 절반으로 줄이는 실전 설정을 다룹니"
image: "/images/20260405-docker-compose-단독-vps-무중단-배포-b.webp"
technologies: ["Docker", "Kubernetes", "GitHub Actions"]
faq:
  - question: "Docker Compose만으로 VPS에서 무중단 배포 가능한가요?"
    answer: "네, Kubernetes 없이도 Docker Compose 단독 VPS 무중단 배포 blue-green 전략 nginx 설정 실전 가이드에서 소개하는 방식으로 구현할 수 있어요. blue/green 두 컨테이너를 번갈아 띄우고 Nginx upstream 설정을 교체하는 구조라 셸 스크립트 하나면 충분해요. 월 $10-20 VPS 한 대에서도 문제없이 동작해요."
  - question: "nginx -s reload 하면 기존 접속자 연결이 끊기나요?"
    answer: "`nginx -s reload`는 기존에 맺어진 커넥션을 끊지 않고 설정 파일만 다시 읽어요. 덕분에 Nginx upstream 파일을 교체한 뒤 reload해도 이미 처리 중인 요청은 정상적으로 완료돼요. 이 동작 방식이 Docker Compose blue-green 무중단 배포의 핵심 원리예요."
  - question: "blue-green 배포에서 롤백은 어떻게 하나요?"
    answer: "blue-green 전략은 이전 버전 컨테이너(예: blue)가 그대로 살아있는 상태에서 새 버전(green)으로 트래픽을 전환하기 때문에, 문제가 생기면 Nginx upstream 설정만 다시 blue로 바꿔주면 5-10초 안에 롤백이 완료돼요. Kubernetes의 롤백(30-120초)보다 훨씬 빠른 이유가 바로 이 구조 덕분이에요. 별도 오케스트레이터나 복잡한 명령어 없이 셸 스크립트 한 줄로 처리할 수 있어요."
  - question: "Docker Compose blue-green 배포할 때 헬스체크는 왜 필요한가요?"
    answer: "새 버전 컨테이너(green)가 실행됐다고 해서 애플리케이션이 바로 요청을 받을 수 있는 상태는 아니에요. 헬스체크를 통과한 것을 확인한 뒤에 Nginx 트래픽을 전환해야 사용자가 실패 응답을 받지 않아요. Docker Compose 단독 VPS 무중단 배포 blue-green 전략 nginx 설정 실전 가이드에서는 `docker compose up -d --no-deps --build`로 컨테이너를 올린 뒤 헬스체크 통과 여부를 확인하고 전환하는 순서를 권장해요."
  - question: "트래픽이 늘어나면 이 방식으로 감당이 안 되나요?"
    answer: "단독 VPS 기반 Docker Compose blue-green 배포는 서버 한 대의 자원 한계가 명확하게 존재해요. 트래픽이 급증해서 단일 서버로 감당이 어려워지면 Docker Swarm이나 Kubernetes로 넘어가는 것을 고려해야 해요. 다만 월 $200 이하 규모의 서비스라면 이 구조가 비용과 운영 복잡도 면에서 충분히 실용적인 선택이에요."
aliases:
  - "/tech/2026-04-05-docker-compose-단독-vps-무중단-배포-bluegreen-전략-nginx-설정/"

---

배포 버튼을 누르는 순간이 제일 떨려요. 서비스가 10초라도 죽으면 바로 슬랙 알림이 쏟아지거든요. 그런데 Kubernetes 같은 무거운 도구 없이, 단독 VPS에서 Docker Compose만으로 무중단 배포를 만들 수 있어요. 셸 스크립트 하나면 충분해요.

> **Key Takeaways**
> - Docker Compose + Nginx만으로 단독 VPS에서 blue-green 무중단 배포를 구성할 수 있고, Kubernetes 대비 운영 복잡도가 절반 이하예요.
> - blue 컨테이너와 green 컨테이너를 번갈아 띄우고, Nginx upstream 설정을 동적으로 교체하는 게 핵심이에요.
> - `docker compose up -d --no-deps --build` 명령 하나로 새 컨테이너를 띄운 뒤 헬스체크를 통과하면 트래픽을 전환해요.
> - `nginx -s reload`는 기존 연결을 끊지 않고 설정만 다시 읽어요. 이 점이 무중단의 핵심이에요.
> - 이 구조는 월 $10-20 VPS에서도 충분히 돌아가요.

---

## 1. 왜 이 방식인가요?

매달 $200 이하 인프라 비용으로 운영하는 서비스 대부분은 단독 VPS 위에 있어요. 그런데 "무중단 배포는 k8s가 있어야 해"라는 오해 때문에 배포 때마다 서비스를 내리는 팀이 아직 많아요.

Docker Compose 단독 VPS에서 blue-green 전략이 각광받는 이유는 단순해요.

- 롤백이 쉬워요 (이전 컨테이너가 살아있으니까요)
- Nginx 설정 교체가 핫리로드를 지원해요
- 별도 오케스트레이터 없이 셸 스크립트만으로 완성돼요

---

## 2. Blue-Green이 뭔가요?

blue-green 배포는 두 개의 동일한 환경을 번갈아 쓰는 전략이에요. 한쪽(blue)이 현재 운영 중이고, 새 버전을 다른 쪽(green)에 먼저 올려요. 헬스체크를 통과하면 Nginx 트래픽을 green으로 전환하고, 문제가 생기면 blue로 즉시 되돌려요.

2015년쯤부터 대형 서비스들이 쓰던 전략인데, Docker가 대중화되면서 소규모 팀도 쓸 수 있게 됐어요. 기존에는 물리 서버 두 대가 필요했지만, 이제는 컨테이너 두 개로 같은 효과를 내거든요.

**필요한 사전 지식:**
- Docker, Docker Compose 기본 명령어
- Nginx 설정 파일 구조 (server 블록, upstream 블록)
- 리눅스 셸 스크립트 기초
- VPS에 SSH로 접속하는 방법

---

## 3. 배포 방식 비교

| 항목 | Docker Compose Blue-Green (단독 VPS) | Docker Swarm | Kubernetes |
|------|--------------------------------------|--------------|------------|
| 비용 | $10-20/월 VPS 1대 | $20-40/월 (노드 추가) | $100+/월 (관리형 기준) |
| 설정 난이도 | 낮음 (셸 스크립트) | 중간 | 높음 |
| 롤백 속도 | 5-10초 | 30-60초 | 30-120초 |
| 확장성 | 단일 서버 한계 | 멀티 노드 가능 | 무제한 |
| 운영 러닝커브 | 낮음 | 중간 | 높음 |

단독 VPS는 DigitalOcean, Vultr, Hetzner 기준 월 $10-20으로 충분해요. Kubernetes 관리형 서비스(EKS, GKE)는 노드 비용만 월 $100을 쉽게 넘어요.

롤백 속도가 가장 빠른 이유도 명확해요. blue-green은 Nginx upstream만 바꾸면 되거든요. blue 컨테이너가 이미 떠있으니까요.

단, 트래픽이 급증해서 서버 한 대로 감당이 안 된다면 Swarm이나 k8s로 넘어가야 해요. 이 방식은 단일 서버 한계가 명확해요.

---

## 4. 단계별 세팅 가이드

### 사전 준비물
- Ubuntu 22.04 LTS 이상 VPS
- Docker Engine 26.x 이상, Docker Compose v2.x 이상
- Nginx (apt로 설치하거나 컨테이너로 띄워도 돼요)
- 도메인 + SSL 인증서 (Let's Encrypt 추천)

---

### Step 1: 디렉터리 구조 잡기

```bash
mkdir -p /opt/myapp/{nginx,blue,green,scripts}
cd /opt/myapp
```

```
/opt/myapp/
├── nginx/
│   ├── nginx.conf          # 메인 설정
│   └── conf.d/
│       └── upstream.conf   # 트래픽 방향 설정 (여기를 교체해요)
├── blue/
│   └── docker-compose.yml
├── green/
│   └── docker-compose.yml
└── scripts/
    └── deploy.sh           # 배포 자동화 스크립트
```

---

### Step 2: Docker Compose 파일 설정

blue와 green의 구조는 같고, 포트 번호만 달라요.

```yaml
# /opt/myapp/blue/docker-compose.yml
version: "3.8"

services:
  app:
    image: myregistry/myapp:${APP_VERSION:-latest}
    container_name: myapp-blue
    restart: unless-stopped
    ports:
      - "8001:3000"  # blue는 8001 포트
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
```

```yaml
# /opt/myapp/green/docker-compose.yml
version: "3.8"

services:
  app:
    image: myregistry/myapp:${APP_VERSION:-latest}
    container_name: myapp-green
    restart: unless-stopped
    ports:
      - "8002:3000"  # green은 8002 포트
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
```

---

### Step 3: Nginx Upstream 설정

```nginx
# /opt/myapp/nginx/conf.d/upstream.conf
# 이 파일만 교체해서 트래픽 방향을 바꿔요

upstream myapp_backend {
    server 127.0.0.1:8001;  # blue 활성 상태
}

server {
    listen 80;
    server_name myapp.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name myapp.example.com;

    ssl_certificate /etc/letsencrypt/live/myapp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myapp.example.com/privkey.pem;

    location / {
        proxy_pass http://myapp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }

    location /health {
        access_log off;
        proxy_pass http://myapp_backend;
    }
}
```

---

### Step 4: 배포 스크립트 작성

이 스크립트가 전체 흐름의 핵심이에요. 잘 읽어보세요.

```bash
#!/bin/bash
# /opt/myapp/scripts/deploy.sh
# 사용법: ./deploy.sh v1.2.3

set -e  # 에러 나면 즉시 중단

APP_VERSION=${1:?"버전을 인자로 넘겨주세요. 예: ./deploy.sh v1.2.3"}
NGINX_CONF_DIR="/opt/myapp/nginx/conf.d"
BLUE_DIR="/opt/myapp/blue"
GREEN_DIR="/opt/myapp/green"

# 현재 어떤 환경이 살아있는지 확인
CURRENT_PORT=$(grep -oP '(?<=server 127.0.0.1:)\d+' $NGINX_CONF_DIR/upstream.conf)

if [ "$CURRENT_PORT" = "8001" ]; then
    ACTIVE="blue"
    STANDBY="green"
    STANDBY_DIR=$GREEN_DIR
    STANDBY_PORT=8002
else
    ACTIVE="green"
    STANDBY="blue"
    STANDBY_DIR=$BLUE_DIR
    STANDBY_PORT=8001
fi

echo "현재 활성: $ACTIVE (포트 $CURRENT_PORT) → 새 버전 배포 대상: $STANDBY"

# 새 컨테이너 빌드 & 시작
cd $STANDBY_DIR
APP_VERSION=$APP_VERSION docker compose up -d --no-deps --build

# 헬스체크 대기 (최대 60초)
echo "헬스체크 대기 중..."
for i in $(seq 1 12); do
    sleep 5
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$STANDBY_PORT/health)
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "헬스체크 통과! ($i회 시도)"
        break
    fi
    echo "아직 준비 중... ($i/12)"
    if [ $i -eq 12 ]; then
        echo "헬스체크 실패. 배포를 중단해요."
        docker compose down
        exit 1
    fi
done

# Nginx upstream 교체
cat > $NGINX_CONF_DIR/upstream.conf << EOF
upstream myapp_backend {
    server 127.0.0.1:$STANDBY_PORT;
}
EOF

# Nginx 핫리로드 (기존 연결 유지!)
nginx -t && nginx -s reload
echo "Nginx 트래픽 전환 완료: $ACTIVE → $STANDBY"

# 구 컨테이너는 30초 후 종료 (기존 연결 처리 시간)
sleep 30
cd /opt/myapp/$ACTIVE
docker compose down
echo "배포 완료! 현재 활성: $STANDBY (포트 $STANDBY_PORT)"
```

```bash
# 실행 권한 부여
chmod +x /opt/myapp/scripts/deploy.sh

# 배포 실행
/opt/myapp/scripts/deploy.sh v1.2.3
```

---

### Step 5: 롤백

문제가 생기면 이전 컨테이너가 이미 다시 떠있기 때문에 Nginx만 바꾸면 돼요.

```bash
#!/bin/bash
# /opt/myapp/scripts/rollback.sh

NGINX_CONF_DIR="/opt/myapp/nginx/conf.d"
CURRENT_PORT=$(grep -oP '(?<=server 127.0.0.1:)\d+' $NGINX_CONF_DIR/upstream.conf)

# 현재 포트의 반대로 전환
if [ "$CURRENT_PORT" = "8002" ]; then
    ROLLBACK_PORT=8001
    ROLLBACK_ENV="blue"
else
    ROLLBACK_PORT=8002
    ROLLBACK_ENV="green"
fi

# 롤백 대상 컨테이너가 떠있는지 확인
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$ROLLBACK_PORT/health)
if [ "$HTTP_STATUS" != "200" ]; then
    echo "롤백 대상($ROLLBACK_ENV)이 응답 없어요. 먼저 컨테이너를 올려주세요."
    exit 1
fi

cat > $NGINX_CONF_DIR/upstream.conf << EOF
upstream myapp_backend {
    server 127.0.0.1:$ROLLBACK_PORT;
}
EOF

nginx -t && nginx -s reload
echo "롤백 완료! → $ROLLBACK_ENV (포트 $ROLLBACK_PORT)"
```

---

## 5. 실전 응용: GitHub Actions 연동

CI/CD 파이프라인에서 이 스크립트를 호출하면 자동 배포가 돼요.

```yaml
# .github/workflows/deploy.yml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: 이미지 빌드 & 레지스트리 푸시
        run: |
          docker build -t myregistry/myapp:${{ github.sha }} .
          docker push myregistry/myapp:${{ github.sha }}

      - name: VPS에 배포
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.VPS_HOST }}
          username: deploy
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            /opt/myapp/scripts/deploy.sh ${{ github.sha }}
```

---

## 6. 자주 하는 실수와 해결 방법

### 흔한 실수들

- **`nginx -s reload` 대신 `nginx restart` 쓰기**
  - `restart`는 기존 연결을 끊어요. 반드시 `reload`를 쓰세요. 이게 무중단의 핵심이에요.

- **헬스체크 엔드포인트 없이 배포하기**
  - 컨테이너가 뜬 것과 앱이 준비된 것은 달라요. `/health` 엔드포인트를 반드시 만들어두세요.

- **DB 마이그레이션을 컨테이너 안에서 실행하기**
  - 두 버전이 동시에 DB를 바라보는 순간이 있어요. 마이그레이션은 배포 전에 따로 실행하고, 하위 호환성을 유지해야 해요.

### 프로덕션 준비 체크리스트

- [ ] `/health` 엔드포인트 구현 완료
- [ ] `deploy.sh`에 실행 권한 설정 (`chmod +x`)
- [ ] Nginx 설정 문법 사전 검증 (`nginx -t`)
- [ ] 배포 전용 SSH 키로 최소 권한만 부여
- [ ] 배포 로그를 파일로 남기기 (`./deploy.sh v1.2.3 >> /var/log/deploy.log 2>&1`)
- [ ] 롤백 스크립트 테스트 완료

---

## 7. 마무리

Docker Compose 단독 VPS, blue-green 전략, Nginx를 조합하면 월 몇만 원짜리 서버에서도 안정적인 배포 파이프라인을 만들 수 있어요. 이 방식이 항상 정답은 아니에요. 트래픽이 급격히 늘어나거나 멀티 서버 환경이 필요해지면 그때 k8s를 검토하면 돼요. 지금 단계에선 복잡한 오케스트레이터보다 이 구조가 훨씬 실용적이에요.

핵심만 다시 정리하면:
- **blue/green 포트 분리** (8001 / 8002)
- **헬스체크 통과 후** Nginx upstream 교체
- **`nginx -s reload`** 로 기존 연결 보호
- **롤백은 5초** — 이전 컨테이너가 살아있으니까요

지금 바로 Step 1부터 따라해 보세요. `/opt/myapp` 디렉터리 만드는 것부터 시작하면 돼요. 막히는 부분이 있으면 댓글로 남겨주세요. 다음 글에서는 이 파이프라인에 Watchtower나 Portainer를 붙여서 모니터링하는 방법을 다룰게요.

## 참고자료

1. [[CI/CD] blue/green 무중단 배포 (Docker, Github Actions, Nginx) — J_hzlo](https://jhzlo.tistory.com/82)
2. [Gighub Action , Docker Compose, Nginx, code deploy 무중단 배포](https://jsw5913.tistory.com/15)
3. [How I Set Up a Resilient Blue/Green Deployment with Docker Compose and Nginx | by Chinecherem Udegbu](https://medium.com/@ChinecheremU/how-i-set-up-a-resilient-blue-green-deployment-with-docker-compose-and-nginx-9726a9a068bf)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
