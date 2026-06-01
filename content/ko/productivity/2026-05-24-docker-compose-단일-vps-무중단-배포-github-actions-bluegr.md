---
title: "단일 VPS에서 Docker Compose blue-green 무중단 배포 GitHub Actions 삽질 후기"
date: 2026-05-24T20:38:22+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "vps", "Kubernetes"]
description: "단일 VPS에서 docker compose up 한 줄로 502 에러 경험했다면? GitHub Actions + Nginx로 블루-그린 무중단 배포 구현한 실패담과 $6 Droplet 운영 노하우를 공유합니다."
image: "/images/20260524-docker-compose-단일-vps-무중단-배포-g.webp"
technologies: ["Docker", "Kubernetes", "AWS", "GitHub Actions"]
faq:
  - question: "Docker Compose 단일 VPS 무중단 배포 GitHub Actions blue-green 배포할 때 502 에러 나는 이유"
    answer: "헬스체크 없이 Nginx 전환을 먼저 실행하면 새 컨테이너가 아직 준비되지 않은 상태에서 트래픽이 유입되어 502 에러가 발생합니다. Spring Boot 기준으로 컨테이너가 완전히 뜨는 데 10-20초가 걸리지만 Nginx reload는 1초 만에 끝나기 때문에, 반드시 헬스체크 폴링으로 컨테이너 준비를 확인한 후에 Nginx 전환을 해야 합니다."
  - question: "단일 VPS docker compose blue green 배포 Nginx upstream 동적 전환 방법"
    answer: "proxy_pass를 nginx.conf에 하드코딩하는 대신, upstream URL을 별도 include 파일(예: service-url.inc)로 분리하고 배포 스크립트에서 해당 파일만 교체한 뒤 nginx -s reload를 실행하는 방식을 사용합니다. Nginx reload는 기존 연결을 끊지 않고 새 연결부터 새 upstream으로 라우팅하기 때문에 진행 중인 요청이 중단되지 않아 실질적으로 다운타임 0초를 달성할 수 있습니다."
  - question: "GitHub Actions SSH 원격 배포 환경변수 컨테이너에 안 전달되는 문제 해결"
    answer: "appleboy/ssh-action으로 SSH 접속한 세션은 /etc/environment를 읽지 못해 .env 파일의 환경변수가 컨테이너에 전달되지 않는 문제가 발생합니다. 해결 방법은 DB 비밀번호 등 민감한 값을 GitHub Secrets에 저장하고, Actions 워크플로에서 echo 명령으로 서버에 .env 파일을 직접 생성해 사용하는 패턴입니다."
  - question: "Docker Compose 단일 VPS 무중단 배포 GitHub Actions blue-green 삽질 후기 blue green 컨테이너 동시 실행 OOM 방지"
    answer: "blue/green 컨테이너가 동시에 실행되는 순간 메모리 사용량이 두 배로 치솟아 단일 VPS 환경에서 OOM(Out of Memory) 이 발생할 수 있습니다. 배포 전 스왑 메모리 설정을 반드시 구성해두고, Nginx 전환이 완료된 직후 구 컨테이너를 즉시 제거하는 순서를 스크립트에 명시해야 합니다."
  - question: "docker-compose blue green 배포 포트 충돌 해결 방법"
    answer: "하나의 docker-compose.yml에서 blue/green을 함께 관리하면 컨테이너 이름과 포트 충돌이 발생합니다. docker-compose.blue.yml과 docker-compose.green.yml을 별도 파일로 분리하거나 --project-name 옵션으로 프로젝트를 격리하면, blue는 8080 포트, green은 8081 포트를 독립적으로 사용할 수 있어 충돌 없이 두 환경을 동시에 운영할 수 있습니다."
---

배포 버튼 누른 순간 서비스가 30초 동안 터진 적 있죠? 단일 VPS 환경에서 `docker compose up`만 했다가 실서비스 사용자들에게 502 폭탄을 날려본 사람이라면, 이 글이 딱 맞아요.

작은 팀이 AWS ECS나 쿠버네티스 없이 단일 VPS에서 GitHub Actions + Docker Compose + Nginx로 무중단 배포를 구현하는 패턴이 빠르게 퍼지고 있어요. 비용 때문이에요. DigitalOcean 기준 $6짜리 Droplet 하나로 운영하다가 Kubernetes 클러스터 세우면 최소 월 $100 넘어가거든요. 그래서 "단일 VPS에서 다운타임을 0에 가깝게 줄이려면?" 이 질문이 개발자 커뮤니티에서 계속 올라오는 거예요.

이 글은 그 질문에 직접 답해요. Docker Compose 기반 blue-green 배포를 GitHub Actions로 자동화하는 과정에서 실제로 겪은 삽질과, 그걸 뚫고 나온 구조를 정리했어요.

> **핵심 요약**
> - Docker Compose 단일 VPS 환경에서 blue-green 배포를 제대로 구현하려면 Nginx `upstream` 동적 전환이 핵심이에요. `proxy_pass` 하드코딩 방식은 컨테이너 교체 중 반드시 다운타임이 생겨요.
> - GitHub Actions에서 SSH로 원격 서버에 접근해 컨테이너를 교체하는 방식은 평균 배포 시간 45초 내외로 줄일 수 있어요 (jhzlo.tistory.com 실측 기준).
> - 헬스체크 없이 Nginx 전환을 먼저 하면 새 컨테이너가 아직 준비 안 됐는데 트래픽이 들어와서 502가 터져요. 순서가 전부예요.
> - 단일 VPS의 메모리 제약 때문에 blue/green 컨테이너가 동시에 뜨는 순간 OOM이 발생할 수 있어요. 스왑 설정은 배포 전 필수예요.

---

## blue-green 배포가 단일 VPS에서 왜 어려운가

쿠버네티스에서 blue-green은 비교적 편해요. 새 파드를 띄우고 서비스 셀렉터만 바꾸면 되거든요. 그런데 Docker Compose + 단일 VPS 조합은 상황이 달라요.

핵심 문제는 두 가지예요.

**첫 번째: Nginx 설정 파일이 정적이에요.**
`nginx.conf`에 `proxy_pass http://app:8080;` 이렇게 써두면, 이 상태에서 `docker compose up -d`를 새로운 이미지로 실행할 때 Docker가 컨테이너를 내리고 다시 올리는 순간 Nginx는 upstream이 사라졌다고 판단해요. 그 간격이 고작 2-3초라도 사용자한테는 502예요.

**두 번째: 포트 충돌이에요.**
blue 컨테이너가 8080, green 컨테이너가 8081을 쓴다고 할 때, `docker-compose.yml`을 두 벌 관리하거나 `--project-name`으로 격리하지 않으면 이름 충돌이 나요. 실제로 jhzlo님의 배포 후기에서도 이 부분을 `docker-compose.blue.yml` / `docker-compose.green.yml`으로 분리해서 해결했어요.

이 두 문제를 해결하지 않으면 GitHub Actions 자동화 파이프라인을 아무리 잘 짜도 배포할 때마다 아슬아슬해요.

---

## 삽질의 실체: 세 번 틀리고 나서 알게 된 것들

### 헬스체크 없는 Nginx 전환 — 502의 근원

가장 많이 저지르는 실수예요. 배포 스크립트를 이렇게 짜는 거예요:

```bash
docker compose -f docker-compose.green.yml up -d
# 바로 Nginx reload
nginx -s reload
```

새 컨테이너는 Spring Boot 기준으로 완전히 뜨는 데 10-20초 걸려요. 근데 Nginx reload는 1초 만에 끝나버리거든요. 결과는 뻔해요. 트래픽이 아직 준비 안 된 green으로 흘러들어가고, 연결 거부 응답이 돌아와요.

해결법은 헬스체크 폴링이에요.

```bash
until curl -sf http://localhost:8081/actuator/health; do
  sleep 2
done
# 헬스체크 통과 후에만 Nginx 전환
```

있고 없고의 차이가 커요. alstn113님의 배포 구조에서도 헬스체크 → Nginx 전환 → 구 컨테이너 제거 순서를 명확히 지키고 있어요.

### Nginx upstream 동적 전환 구조

정적 `proxy_pass` 대신 `upstream` 블록을 파일로 분리해서 교체하는 방식이 제대로 된 blue-green이에요.

```nginx
# /etc/nginx/conf.d/service-url.inc
set $service_url http://127.0.0.1:8080;
```

배포 스크립트에서 이 파일만 바꾸고 `nginx -s reload`를 날리는 거예요. Nginx reload는 기존 연결을 끊지 않고 새 연결부터 새 upstream으로 보내기 때문에, 진행 중인 요청이 끊기지 않아요.

### GitHub Actions에서 SSH 원격 실행 — 권한 함정

`appleboy/ssh-action`을 쓰면 편한데, 여기서도 함정이 있어요. SSH로 접속한 세션은 `/etc/environment`를 못 읽어요. `.env` 파일에 넣어둔 DB 비밀번호가 컨테이너에 안 전달되는 거예요.

해결법은 GitHub Secrets에 환경변수를 직접 넣고, Actions 워크플로에서 `echo "DB_PASSWORD=${{ secrets.DB_PASSWORD }}" >> .env` 형태로 서버에 파일을 만들어 쓰는 방식이에요. jsw5913님 구현에서도 이 패턴을 썼어요.

---

## 배포 방식 비교: 어떤 걸 선택해야 하나

단일 VPS에서 쓸 수 있는 배포 방식 세 가지를 비교했어요.

| 항목 | 단순 docker compose up | Nginx upstream 파일 교체 | Docker rolling update |
|---|---|---|---|
| 구현 난이도 | 낮음 | 중간 | 높음 |
| 다운타임 | 2-5초 | 0초 (정상 구현 시) | 0초 |
| 메모리 사용 | 낮음 (컨테이너 1개) | 높음 (동시 2개 필요) | 낮음 |
| 롤백 속도 | 느림 (재배포 필요) | 빠름 (파일 복원 + reload) | 중간 |
| 적합 서버 스펙 | 512MB RAM 이상 | 2GB RAM 권장 | 1GB RAM 이상 |
| 실서비스 적합성 | ❌ | ✅ | 조건부 ✅ |

RAM 2GB 미만 서버라면 blue-green 동시 구동 자체가 부담이에요. 이 경우엔 rolling update나 `--no-deps --build` 플래그를 써서 컨테이너 교체 시간을 최소화하는 편이 현실적이에요. 실제로 Nginx `--reload`가 기존 커넥션을 보존한다는 점을 활용하면, RAM이 적은 환경에서도 체감 다운타임을 1초 이내로 줄일 수 있어요.

---

## 이 구조를 실제로 쓰려면 뭘 챙겨야 하나

**지금 당장 세팅할 것들:**

- 서버에 스왑 2GB 이상 설정 (`fallocate -l 2G /swapfile`)
- `docker-compose.blue.yml` / `docker-compose.green.yml` 파일 분리, 포트만 다르게
- Nginx 설정에 `service-url.inc` 파일 분리
- GitHub Actions 워크플로에 헬스체크 폴링 루프 추가
- 현재 활성 컨테이너 상태를 파일로 기록 (`echo "blue" > /srv/active_env`)

**배포 스크립트 순서 (반드시 이 순서):**

1. 비활성 환경(green)에 새 이미지 pull
2. green 컨테이너 시작
3. 헬스체크 통과 대기 (최대 60초)
4. Nginx upstream 파일 교체 → reload
5. 구 컨테이너(blue) 제거
6. active_env 파일 업데이트

4번과 5번 사이에 문제가 생기면 green이 살아있고 blue도 살아있는 상태예요. 롤백이 upstream 파일 복원 + nginx reload 두 줄로 끝난다는 뜻이에요. 실제 장애 상황에서 이 차이가 체감상 엄청 크게 느껴져요.

---

## 결론: 단일 VPS blue-green, 삽질 없이 시작할 수 있어요

정리하면 이래요.

- **502의 원인**: 헬스체크 없는 Nginx 전환
- **핵심 구조**: upstream 파일 분리 + 동적 교체
- **GitHub Actions 함정**: SSH 세션 환경변수 문제는 Secrets → .env 파일로 우회
- **리소스 제약**: RAM 2GB 미만이면 blue-green보다 rolling이 현실적

Docker Compose 단일 VPS 무중단 배포는 사례가 쌓일수록 패턴이 명확해지고 있어요. 쿠버네티스 없이도 충분히 안정적인 배포 파이프라인을 만들 수 있어요. 다만 순서 하나 틀리면 바로 다운타임이 나요. 그게 이 구조의 특성이에요.

지금 배포할 때 다운타임이 얼마나 나고 있나요? 30초 이상이라면 이 구조 한번 적용해볼 만해요.

## 참고자료

1. [[CI/CD] blue/green 무중단 배포 (Docker, Github Actions, Nginx) — J_hzlo](https://jhzlo.tistory.com/82)
2. [Gighub Action , Docker Compose, Nginx, code deploy 무중단 배포](https://jsw5913.tistory.com/15)
3. [무중단 배포(블루/그린 배포)로 서비스 중단 없이 배포하기 — alstn113's devlog](https://alstn113.tistory.com/31)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
