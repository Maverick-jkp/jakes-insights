---
title: "Docker Compose 단독 VPS에서 blue-green 무중단 배포 구현하기"
date: 2026-03-18T20:16:22+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "vps", "Kubernetes"]
description: "Docker Compose 단독 VPS에서 블루-그린 배포로 다운타임 0ms를 구현하는 실전 가이드. nginx reload 시그널로 기존 커넥션을 유지하면서 업스트림만 전환하는 셸 스크립트를 단계별로 설명합니다."
image: "/images/20260318-docker-compose-단독-vps-무중단-배포-b.webp"
technologies: ["Docker", "Kubernetes", "AWS", "GitHub Actions"]
faq:
  - question: "Docker Compose 단독 VPS 무중단 배포 blue-green 전환 nginx reload 실전 스크립트 구현 방법"
    answer: "Docker Compose 단독 VPS 무중단 배포 blue-green 전환은 별도 오케스트레이터 없이 셸 스크립트만으로 구현할 수 있어요. blue/green 두 Compose 파일을 각각 다른 포트(예: 8081, 8082)로 구성한 뒤, 새 버전 헬스체크 통과 후 nginx upstream.conf를 sed로 수정하고 `nginx -s reload`를 실행하면 기존 커넥션을 끊지 않고 트래픽이 전환돼요."
  - question: "docker compose up -d 재시작할 때 다운타임 얼마나 생기나요"
    answer: "`docker compose up -d`만 단순 실행하면 컨테이너가 재시작되는 동안 nginx가 죽은 컨테이너로 요청을 계속 보내기 때문에 평균 2-8초의 다운타임이 발생해요. 이 문제를 해결하려면 blue-green 패턴처럼 새 컨테이너를 먼저 완전히 띄운 뒤 트래픽을 전환하는 방식이 필요해요."
  - question: "nginx reload 와 restart 차이점 무중단 배포에서"
    answer: "`nginx -s reload`는 기존 worker 프로세스가 처리 중인 커넥션을 끊지 않고 새 설정을 적용한 신규 worker를 띄우기 때문에 사실상 다운타임이 0에 수렴해요. 반면 `restart`는 프로세스 자체를 재시작해 짧더라도 실제 서비스 중단이 발생하므로, 무중단 배포에서는 반드시 `reload`를 사용해야 해요."
  - question: "VPS 한 대로 Kubernetes 없이 무중단 배포 가능한가요"
    answer: "월 $10-20짜리 싱글 VPS에서도 Docker Compose 단독 VPS 무중단 배포 blue-green 전환 nginx reload 실전 스크립트 패턴을 적용하면 Kubernetes 없이 99.9% 업타임 달성이 가능해요. kubeconfig나 Helm chart 없이 YAML 두 개와 셸 스크립트만으로 구성되기 때문에 1인 개발자나 소규모 팀이 당일 바로 적용할 수 있어요."
  - question: "blue green 배포 헬스체크 실패하면 자동 롤백 어떻게 하나요"
    answer: "새 버전 컨테이너를 올린 뒤 일정 시간(예: 30초) 동안 `/health` 엔드포인트에 HTTP 200이 오지 않으면 배포 스크립트에서 해당 Compose 서비스를 `docker compose down`으로 내리고 `exit 1`로 종료하면 돼요. nginx upstream은 아직 기존 버전 포트를 바라보고 있는 상태이므로 별도 롤백 명령 없이 자동으로 이전 버전이 트래픽을 계속 처리하게 돼요."
aliases:
  - "/tech/2026-03-18-docker-compose-단독-vps-무중단-배포-bluegreen-전환-nginx-re/"
  - "/ko/tech/2026-03-18-docker-compose-단독-vps-무중단-배포-bluegreen-전환-nginx-re/"

---

배포 버튼을 누르는 순간, 5초 동안 503 에러가 뜨는 상황. 트래픽이 많지 않아도 찜찜하죠. 그렇다고 Kubernetes 클러스터를 올리기엔 VPS 한 대짜리 프로젝트에서 오버스펙이에요. Docker Compose 단독 VPS 환경에서 무중단 배포를 구현하는 방법, 지금 정리해볼게요.

> **핵심 요약**
> - Docker Compose 단독 VPS에서 blue-green 전환은 별도 오케스트레이터 없이 셸 스크립트만으로 구현할 수 있어요.
> - nginx의 `reload` 시그널은 기존 커넥션을 끊지 않고 새 설정을 적용하기 때문에, 진짜 무중단의 열쇠예요.
> - blue/green 두 Compose 서비스를 동시에 올려두고 nginx 업스트림만 전환하면, 다운타임은 이론상 0ms에 수렴해요.
> - 단일 VPS 프로젝트에서 이 패턴으로 AWS ECS나 Kubernetes 없이 99.9% 업타임을 달성한 사례가 실제로 보고되고 있어요.

---

## "그냥 docker compose up -d 하면 안 돼요?"

스타트업과 1인 개발자 사이에서 "Kubernetes는 너무 무거워"라는 피로감이 공공연하게 나오고 있어요. CNCF 2025 Annual Survey에 따르면, 응답자의 38%가 소규모 프로젝트에서 Kubernetes 대신 단순 컨테이너 오케스트레이션으로 회귀하는 추세를 보였어요.

그 결과 Docker Compose 단독 VPS 무중단 배포 방식이 다시 조명받고 있어요. 이유는 세 가지예요.

- **비용**: 싱글 VPS(월 $10-20)로 운영 가능
- **복잡도**: kubeconfig, Helm chart 없이 YAML 두 개로 끝
- **속도**: 인프라 세팅 없이 당일 적용 가능

근데 "그냥 `docker compose up -d` 하면 되는 거 아니야?"라는 오해가 있어요. 기본 명령만 쓰면 컨테이너가 재시작되는 동안 nginx는 여전히 죽은 컨테이너로 요청을 보내요. 실제로 `docker compose up -d` 재시작 시 평균 2-8초의 다운타임이 커뮤니티 벤치마크에서 반복 확인돼요.

그래서 blue-green 전환 패턴이 필요해요.

---

## Blue-Green 전환 구조: 어떻게 작동하나요?

개념 자체는 단순해요. 애플리케이션 인스턴스를 **blue**와 **green** 두 벌 준비해두고, 현재 트래픽을 받는 쪽이 blue라면 새 버전은 green에 배포해요. 배포가 완료되면 nginx 업스트림을 green으로 전환하고, blue는 잠시 대기 상태로 두는 거예요.

### Compose 파일 구성

`docker-compose.blue.yml`과 `docker-compose.green.yml`을 분리하는 게 핵심이에요.

```yaml
# docker-compose.blue.yml
services:
  app-blue:
    image: myapp:${IMAGE_TAG}
    container_name: app-blue
    ports:
      - "8081:8080"
    networks:
      - webnet

networks:
  webnet:
    external: true
```

```yaml
# docker-compose.green.yml
services:
  app-green:
    image: myapp:${IMAGE_TAG}
    container_name: app-green
    ports:
      - "8082:8080"
    networks:
      - webnet

networks:
  webnet:
    external: true
```

포트만 다르게 잡아두는 거예요. blue는 8081, green은 8082. nginx는 이 포트 중 하나만 바라보게 해요.

### nginx 설정

```nginx
# /etc/nginx/conf.d/upstream.conf
upstream app {
    server 127.0.0.1:8081;  # 현재 active: blue
}
```

`nginx -s reload`를 실행하면 기존 연결을 끊지 않고 새 worker 프로세스가 업스트림을 바꿔요. 이게 무중단의 핵심이에요.

---

## 실전 배포 스크립트 분석

### 전환 로직 전체 흐름

```bash
#!/bin/bash
# deploy.sh

CURRENT=$(cat /var/deploy/active 2>/dev/null || echo "blue")
if [ "$CURRENT" = "blue" ]; then
  NEXT="green"
  NEXT_PORT=8082
else
  NEXT="blue"
  NEXT_PORT=8081
fi

echo "▶ Deploying to $NEXT (port $NEXT_PORT)"

# 새 버전 올리기
IMAGE_TAG=$1 docker compose -f docker-compose.${NEXT}.yml up -d --pull always

# 헬스체크 (최대 30초 대기)
for i in $(seq 1 30); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${NEXT_PORT}/health)
  if [ "$STATUS" = "200" ]; then
    echo "✅ Health check passed"
    break
  fi
  sleep 1
done

if [ "$STATUS" != "200" ]; then
  echo "❌ Health check failed. Aborting."
  docker compose -f docker-compose.${NEXT}.yml down
  exit 1
fi

# nginx 업스트림 전환
sed -i "s/server 127.0.0.1:[0-9]*/server 127.0.0.1:${NEXT_PORT}/" \
  /etc/nginx/conf.d/upstream.conf

nginx -s reload
echo "$NEXT" > /var/deploy/active

# 이전 버전 정리 (30초 후)
sleep 30
docker compose -f docker-compose.${CURRENT}.yml down
echo "✅ Deploy complete. Active: $NEXT"
```

스크립트에서 주목할 지점 세 가지예요.

1. **헬스체크 후 전환**: 새 컨테이너가 실제로 200을 반환하기 전까지는 nginx를 건드리지 않아요.
2. **`nginx -s reload`**: `restart`가 아니에요. `reload`는 master 프로세스가 새 worker를 띄우고 기존 worker는 요청을 다 처리한 후 graceful shutdown해요.
3. **30초 대기 후 이전 버전 종료**: 이미 맺어진 keep-alive 커넥션을 위한 buffer예요.

### Blue-Green vs 다른 무중단 방식 비교

| 기준 | Blue-Green (Compose) | Rolling Update | Canary |
|------|---------------------|---------------|--------|
| 다운타임 | 0ms | 2-5초 가능 | 0ms |
| VPS 사양 요구 | 2배 메모리 필요 | 1배 | 1.x배 |
| 롤백 속도 | 즉각 (설정 되돌리기) | 느림 | 중간 |
| 구현 복잡도 | 낮음 | 매우 낮음 | 높음 |
| 트래픽 분산 제어 | 불가 (all-or-nothing) | 불가 | 가능 |
| **추천 대상** | 단일 VPS 프로덕션 | CI/CD 실험 환경 | 대규모 서비스 |

메모리 2배 문제는 자주 나오는 걱정이에요. 실제로는 전환 시점에 잠깐만 두 컨테이너가 동시에 뜨고, 30초 후 이전 버전이 꺼져요. 512MB 앱이라면 전환 중 1GB만 있으면 돼요. VPS $20짜리도 보통 2-4GB RAM이라 충분해요.

---

## 팀별 적용 시나리오

**시나리오 1: 사이드 프로젝트 / 1인 개발**
새벽 배포 중 서비스가 잠깐 끊겨도 "에이, 아무도 안 봐"라고 넘겼던 적 있죠. 근데 서비스가 자라면 그 태도가 사용자 이탈로 이어져요. 위 스크립트를 GitHub Actions에 연결하면 `git push` 하나로 무중단 배포가 끝나요. 설정 시간 2시간 이내예요.

**시나리오 2: 스타트업 초기 (팀 2-5명)**
Docker Compose 단독 VPS에서 blue-green 전환을 쓰면 CI/CD 파이프라인을 Kubernetes 없이 프로덕션 수준으로 올릴 수 있어요. GitHub Actions free tier(월 2,000분)로 하루 10회 배포해도 비용 제로예요.

**주시할 신호들**:
- Docker Compose Watch 기능(v2.22+)이 개발 환경 핫리로드를 지원하기 시작했어요. 프로덕션 배포 패턴에도 영향을 줄 수 있어요.
- nginx Unit 프로젝트가 설정 API를 통한 동적 업스트림 변경을 지원해요. `reload` 없이 전환이 가능해지면 스크립트가 더 단순해질 거예요.

---

## 정리: 스크립트 하나가 바꾸는 것들

- Docker Compose 단독 VPS에서 blue-green 전환은 셸 스크립트 50줄로 구현 가능해요
- nginx reload는 무중단의 핵심 메커니즘이에요 — restart와 혼동하면 의미 없어요
- 헬스체크 없는 자동 전환은 "무중단인 척하는 배포"에 불과해요
- 메모리 2배 걱정은 전환 시간(30-60초) 동안만 해당돼요

지금 당장 해볼 수 있는 한 가지. 기존 `docker compose up -d` 배포 스크립트에 헬스체크 루프 하나만 추가해보세요. 그것만으로도 "배포 중 503" 절반은 없앨 수 있어요. 그다음이 blue-green 전환이에요.

VPS 한 대로 99.9%를 노리는 게 무모한 목표일까요? 스크립트 하나면 충분히 현실적인 얘기예요.

## 참고자료

1. [[CD] 블루/그린 무중단 배포 구현하기 1편 (NGINX/Docker Compose) :: kimyu0218](https://kimyu0218.tistory.com/55)
2. [GitHub Actions + Docker + NGINX를 활용한 Blue/Green 무중단 배포 환경 구축 — jwooo's log](https://jwooo.tistory.com/12)
3. [무중단 배포(블루/그린 배포)로 서비스 중단 없이 배포하기 — alstn113's devlog](https://alstn113.tistory.com/31)


---

*Photo by [Egor Komarov](https://unsplash.com/@egorkomarov) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-control-panel-with-buttons-n2jspRppehw)*
