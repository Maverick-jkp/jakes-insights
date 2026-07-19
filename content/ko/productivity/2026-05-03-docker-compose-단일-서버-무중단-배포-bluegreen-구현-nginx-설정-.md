---
title: "Docker Compose 단일 서버 Blue-Green 무중단 배포 nginx 설정 실전 예제"
date: 2026-05-03T20:14:20+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "\ubb34\uc911\ub2e8", "Node.js"]
description: "Docker Compose와 nginx만으로 Blue-Green 무중단 배포 구현하는 법. AWS 없이 단일 서버에서 upstream 전환으로 다운타임 0 달성, proxy_pass 설정과 실전 예제 코드 공개."
image: "/images/20260503-docker-compose-단일-서버-무중단-배포-bl.webp"
technologies: ["Node.js", "FastAPI", "Docker", "Kubernetes", "AWS"]
faq:
  - question: "Docker Compose 단일 서버 무중단 배포 Blue-Green 구현 nginx 설정 실전 예제 어떻게 하나요"
    answer: "Docker Compose 단일 서버 무중단 배포 Blue-Green 구현은 blue/green 두 컨테이너를 각각 다른 포트(8081, 8082)로 띄운 뒤 nginx upstream 설정에서 active 서버만 바꾸고 `nginx -s reload`를 실행하는 방식으로 작동합니다. nginx reload는 기존 커넥션을 끊지 않기 때문에 이론상 다운타임이 0에 가까우며, AWS 로드밸런서나 Kubernetes 없이도 구현 가능합니다. 배포 스크립트로 upstream.conf 주석 전환을 자동화하면 사람 실수도 줄일 수 있습니다."
  - question: "nginx upstream reload 무중단 가능한가요 기존 커넥션 끊기나요"
    answer: "nginx의 `nginx -s reload` 명령은 기존에 처리 중인 커넥션을 강제로 끊지 않고 새 설정을 워커 프로세스에 적용합니다. 덕분에 upstream 서버를 blue에서 green으로 전환할 때 접속 중인 사용자 세션이 유지됩니다. 이 특성이 단일 서버 Blue-Green 무중단 배포의 핵심 기술 요소입니다."
  - question: "docker compose down up 하면 다운타임 얼마나 생기나요"
    answer: "`docker compose down` 후 `docker compose up`을 순차 실행하면 컨테이너가 완전히 내려갔다 올라오는 사이 보통 10~30초의 다운타임이 발생합니다. 이 시간 동안 접속 중인 사용자는 502 또는 503 에러를 경험하게 됩니다. Blue-Green 배포 방식을 쓰면 새 컨테이너가 완전히 준비된 후에만 트래픽을 전환하므로 이 공백을 없앨 수 있습니다."
  - question: "Blue-Green 배포 롤백 방법 빠르게 되돌리려면"
    answer: "Blue-Green 구조에서 롤백은 nginx upstream 설정을 이전 컨테이너로 되돌리고 reload하는 것만으로 완료되며, 이 과정이 30초 안에 끝납니다. 이전 버전의 blue(또는 green) 컨테이너가 아직 실행 중인 상태이기 때문에 새로 빌드하거나 재배포할 필요가 없습니다. 문제가 생겼을 때 즉시 서비스를 복구할 수 있다는 점이 Blue-Green 방식의 가장 큰 운영 장점입니다."
  - question: "소규모 스타트업 단일 서버에서 무중단 배포 구현 가능한가요"
    answer: "Docker Compose 단일 서버 무중단 배포 Blue-Green 구현 nginx 설정 실전 예제처럼, 서버 한 대와 Docker Compose, nginx만으로도 무중단 배포 환경을 만들 수 있습니다. 두 개의 서버 클러스터나 AWS ALB 같은 추가 인프라 없이 동일 서버 내에서 컨테이너 두 개를 번갈아 사용하는 방식이라 비용 부담이 거의 없습니다. 1~3인 개발팀이나 비용을 최소화해야 하는 초기 스타트업에 실용적인 선택입니다."
aliases:
  - "/tech/2026-05-03-docker-compose-단일-서버-무중단-배포-bluegreen-구현-nginx-설정-/"

---

배포 누를 때마다 긴장되죠? "이번엔 또 몇 초 끊기나" 하면서요.

---

단일 서버에서 Docker Compose와 nginx만으로 Blue-Green 무중단 배포를 구현하는 패턴이 실제로 작동해요. AWS 로드밸런서도, Kubernetes도 없이요. 작은 팀이 당장 쓸 수 있는 방법이거든요.

> **핵심 요약**
> - Blue-Green 배포는 두 개의 동일한 환경을 번갈아 배포하는 방식으로, 다운타임을 이론상 0으로 줄일 수 있어요.
> - Docker Compose 단일 서버에서 nginx upstream 전환만으로 무중단 배포가 가능하고, 추가 인프라 비용이 없어요.
> - nginx의 `proxy_pass` 동적 전환과 `docker compose up --no-deps` 옵션 조합이 이 구조의 핵심 기술 요소예요.
> - 롤백도 nginx upstream을 이전 컨테이너로 되돌리는 것만으로 30초 안에 완료돼요.

---

## 단일 서버 Blue-Green, 왜 지금 주목받나요?

Blue-Green 배포라고 하면 보통 두 개의 서버 클러스터, 로드밸런서, AWS ALB 같은 이미지를 떠올려요. 비용이 최소 두 배 이상 들죠.

그런데 스타트업과 1~3인 개발팀이 급격히 늘었어요. GitHub의 2025 State of Developer Report에 따르면 1인 SaaS 프로젝트가 전년 대비 38% 증가했거든요. 이 팀들은 인프라 비용은 최소화하면서 서비스 안정성은 높여야 해요. 모순처럼 들리지만, 단일 서버 Docker Compose로 Blue-Green을 구현하면 그게 가능해요.

원리는 간단해요. 하나의 서버 안에서 blue 컨테이너와 green 컨테이너를 동시에 띄워놓고, nginx가 트래픽 방향만 바꾸는 거예요. 새 버전을 green에 띄운 다음, 헬스체크를 통과하면 nginx가 green을 바라보게 설정을 바꾸고, blue는 조용히 내려요.

**기존 배포 방식의 문제:**
- `docker compose down` → `docker compose up` 사이 다운타임 발생 (보통 10~30초)
- 새 버전에 문제가 생겼을 때 롤백에 추가 시간 소요
- 배포 시점에 접속 중인 사용자 세션 강제 종료

새벽 2시에도 DAU가 수천 명인 서비스라면 이걸 무시할 수 없어요.

---

## Blue-Green 구조 설계: docker-compose.yml과 nginx 설정

### 컨테이너 구조 잡기

핵심 아이디어는 blue와 green 두 서비스를 docker-compose.yml에 정의하는 거예요. 각각 다른 포트를 점유해요.

```yaml
# docker-compose.yml
services:
  app-blue:
    image: myapp:${BLUE_VERSION}
    container_name: app-blue
    ports:
      - "8081:3000"
    networks:
      - app-network

  app-green:
    image: myapp:${GREEN_VERSION}
    container_name: app-green
    ports:
      - "8082:3000"
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    ports:
      - "80:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
    networks:
      - app-network
    depends_on:
      - app-blue
      - app-green

networks:
  app-network:
    driver: bridge
```

app-blue는 8081, app-green은 8082 포트를 써요. nginx는 80번 포트에서 받아서 둘 중 하나로 프록시하는 구조예요.

### nginx upstream 전환 설정

`conf.d` 디렉토리에 파일을 분리해서 관리하면 reload 시 무중단 전환이 가능해요.

```nginx
# nginx/conf.d/upstream.conf
upstream app {
    server app-blue:3000;
    # server app-green:3000;  # 전환 시 주석 교체
}

server {
    listen 80;
    
    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
    }
}
```

배포할 때 `upstream.conf`에서 주석만 바꾸고 `nginx -s reload`를 실행하면 돼요. nginx reload는 기존 커넥션을 끊지 않아요. 이게 무중단의 핵심이에요.

### 배포 스크립트 자동화

매번 수동으로 주석 바꾸면 실수가 나요. 셸 스크립트로 자동화하는 게 맞아요.

```bash
#!/bin/bash
# deploy.sh

CURRENT=$(grep -v "^#" nginx/conf.d/upstream.conf | grep "server app-" | awk '{print $2}' | cut -d: -f1)

if [[ "$CURRENT" == *"blue"* ]]; then
    NEXT="green"
    NEXT_PORT=8082
    PREV="blue"
else
    NEXT="blue"
    NEXT_PORT=8081
    PREV="green"
fi

echo "현재 환경: $PREV → 다음 환경: $NEXT"

# 새 버전 컨테이너 시작
docker compose up -d --no-deps app-$NEXT

# 헬스체크 (최대 30초 대기)
for i in {1..6}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$NEXT_PORT/health)
    if [ "$STATUS" = "200" ]; then
        echo "헬스체크 통과"
        break
    fi
    sleep 5
done

if [ "$STATUS" != "200" ]; then
    echo "헬스체크 실패 - 배포 중단"
    docker compose stop app-$NEXT
    exit 1
fi

# nginx upstream 전환
sed -i "s/server app-$PREV/# server app-$PREV/g" nginx/conf.d/upstream.conf
sed -i "s/# server app-$NEXT/server app-$NEXT/g" nginx/conf.d/upstream.conf

docker exec nginx-proxy nginx -s reload

echo "배포 완료: $NEXT 환경이 트래픽을 받고 있어요"

# 이전 컨테이너 정리 (선택)
# docker compose stop app-$PREV
```

`--no-deps` 옵션이 여기서 핵심이에요. nginx나 다른 서비스를 재시작하지 않고 해당 컨테이너만 업데이트해요.

---

## Blue-Green vs 기타 배포 방식 비교

| 항목 | 단순 재시작 | Rolling Update | **Blue-Green (단일 서버)** | Blue-Green (멀티 서버) |
|------|------------|---------------|--------------------------|----------------------|
| 다운타임 | 10~30초 | 거의 없음 | **없음** | 없음 |
| 롤백 속도 | 2~5분 | 1~2분 | **30초 이내** | 30초 이내 |
| 서버 비용 | 1x | 1x | 1x | 2x |
| 구현 복잡도 | 낮음 | 중간 | **중간** | 높음 |
| 배포 중 세션 유지 | ❌ | ⚠️ 일부 | **✅** | ✅ |
| 장애 격리 | ❌ | ❌ | **✅** | ✅ |
| 필요 인프라 | Docker만 | K8s 권장 | **Docker + nginx** | LB + 복수 서버 |

단일 서버 Blue-Green은 멀티 서버 대비 비용은 절반인데, 다운타임 제거 효과는 동일해요. 트레이드오프는 서버 자체가 죽었을 때예요. 단일 서버니까 서버 장애에는 취약하죠. 그래도 배포 실수로 인한 다운타임은 완전히 없앨 수 있어요.

---

## 실제 운영에서 주의할 점

**도전 1: 세션/쿠키 처리**
blue와 green이 별도 컨테이너라서 메모리 세션을 쓰면 전환 시 세션이 날아가요. Redis 같은 외부 세션 저장소를 쓰거나, JWT처럼 서버리스 인증 방식을 선택해야 해요. 대부분의 Node.js, FastAPI 앱은 Redis를 같은 compose 파일 안에 넣는 방식으로 처리해요.

**도전 2: DB 마이그레이션 타이밍**
새 버전이 DB 스키마 변경을 필요로 하면, blue와 green이 동시에 뜨는 시간 동안 구버전이 새 스키마를 못 읽는 문제가 생겨요. 하위 호환 마이그레이션을 먼저 배포하고, 코드 배포를 다음 사이클에 하는 "두 단계 마이그레이션" 방식으로 해결해요.

**도전 3: 디스크 용량 관리**
blue/green 이미지를 함께 유지하면 디스크를 두 배 써요. 배포 성공 확인 후 이전 이미지를 `docker image prune`으로 정리하는 cron job을 넣으면 돼요.

---

## 앞으로 이 패턴이 어디로 가나요?

세 가지 방향을 지켜볼 만해요.

- **GitHub Actions + self-hosted runner 연동**: 소규모 팀이 이 조합을 CI/CD에 적용하는 사례가 늘고 있어요. 배포 스크립트를 Actions workflow에 넣고, 서버에 self-hosted runner를 올리는 구조예요.
- **Traefik으로 nginx 대체**: nginx reload 방식 대신 Traefik의 동적 라우팅을 쓰는 시도도 늘고 있어요. 설정 파일을 직접 수정하지 않고 레이블 기반으로 전환할 수 있거든요.
- **헬스체크 정교화**: 단순 HTTP 200 체크 대신, DB 커넥션 확인이나 캐시 워밍업 완료 여부까지 체크하는 패턴이 표준이 되어가고 있어요.

정리하면:
- Docker Compose + nginx upstream 전환으로 다운타임 0을 달성할 수 있어요
- 배포 스크립트 자동화와 헬스체크가 없으면 반쪽짜리예요
- 세션 관리와 DB 마이그레이션 전략을 사전에 설계해야 해요
- 단일 서버의 한계는 분명하지만, 비용 대비 효과는 멀티 서버 구조와 동급이에요

지금 당장 적용하고 싶다면, 먼저 서비스의 세션 방식부터 확인하세요. Redis를 쓰는지, JWT인지, 아직 메모리 세션인지가 구현 난이도를 결정하는 가장 큰 변수거든요. 그게 확인되면 나머지는 스크립트 작성 두어 시간이면 충분해요. 배포할 때마다 긴장하는 것보다 낫죠.

---

*이 글은 공개된 기술 문서와 실제 배포 사례를 바탕으로 작성됐어요. Docker 공식 문서, nginx upstream 문서, GitHub State of Developer Report 2025를 참고했어요.*

## 참고자료

1. [[CI/CD] blue/green 무중단 배포 (Docker, Github Actions, Nginx) — J_hzlo](https://jhzlo.tistory.com/82)
2. [Gighub Action , Docker Compose, Nginx, code deploy 무중단 배포](https://jsw5913.tistory.com/15)
3. [무중단 배포(블루/그린 배포)로 서비스 중단 없이 배포하기 — alstn113's devlog](https://alstn113.tistory.com/31)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
