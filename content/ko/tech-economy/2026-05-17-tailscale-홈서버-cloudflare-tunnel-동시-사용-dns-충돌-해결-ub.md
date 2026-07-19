---
title: "Tailscale과 Cloudflare Tunnel 동시 사용 시 DNS 충돌 해결 — Ubuntu 24.04 실전 가이드"
date: 2026-05-17T20:31:40+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "tailscale", "/ud648/uc11c/ubc84", "cloudflare", "Go"]
description: "Tailscale MagicDNS(100.100.100.100)와 Cloudflare Tunnel DNS 프록시 충돌로 내부 서비스가 먹통 되는 문제, Ubuntu 24.04 실제 설정 파일로 해결법을 정리했습니다."
image: "/images/20260517-tailscale-홈서버-cloudflare-tunne.webp"
technologies: ["Go", "Cloudflare"]
faq:
  - question: "Tailscale이랑 Cloudflare Tunnel 같이 쓰면 DNS가 왜 안 되나요"
    answer: "Tailscale은 MagicDNS(`100.100.100.100`)를 시스템 DNS에 주입하고, cloudflared도 자체 DNS 프록시를 사용하는데, Ubuntu 24.04의 기본 리졸버인 systemd-resolved와 이 둘이 동시에 충돌하면 내부망 DNS 해석이 무너집니다. 증상으로는 Tailscale 내부 주소로 ping은 되지만 서비스 이름으로 접속이 안 되거나, Cloudflare 터널 도메인이 타임아웃되는 경우가 나타납니다."
  - question: "Tailscale 홈서버 Cloudflare Tunnel 동시 사용 DNS 충돌 해결 Ubuntu 24.04 방법"
    answer: "Tailscale 홈서버 Cloudflare Tunnel 동시 사용 DNS 충돌 해결 Ubuntu 24.04 실전 가이드에서 권장하는 방법은 Split DNS 방식으로, `tailscale up --accept-dns=false` 옵션으로 MagicDNS의 시스템 전체 덮어쓰기를 막은 뒤 systemd-resolved에 조건부 DNS 설정을 직접 넣는 것입니다. 이렇게 하면 `ts.net` 도메인은 Tailscale이, 퍼블릭 도메인은 Cloudflare가 각자 담당하도록 충돌 없이 분리할 수 있습니다."
  - question: "tailscale accept-dns false 설정하면 MagicDNS 완전히 꺼지나요"
    answer: "`--accept-dns=false` 옵션은 MagicDNS를 완전히 비활성화하는 게 아니라, Tailscale이 시스템 전체 DNS를 자동으로 덮어쓰는 동작만 막는 옵션입니다. MagicDNS 기능 자체는 유지되므로, systemd-resolved에 직접 조건부 라우팅 설정을 추가하면 `hostname.ts.net` 형태의 내부 DNS 해석을 그대로 사용할 수 있습니다."
  - question: "Ubuntu 24.04 systemd-resolved Tailscale Cloudflare 충돌 진단 방법"
    answer: "`resolvectl status` 명령으로 현재 DNS 상태를 확인하고, `resolvectl dns tailscale0`으로 Tailscale이 주입한 DNS를, `ss -tlnp | grep cloudflared`로 cloudflared가 점유한 포트를 확인할 수 있습니다. `tailscale0` 인터페이스에 `100.100.100.100`이 잡혀 있으면서 다른 네트워크 인터페이스에도 별도 DNS가 설정되어 있다면 충돌 가능 상태로 봐야 합니다."
  - question: "Tailscale 홈서버 Cloudflare Tunnel 동시 사용 DNS 충돌 해결 Ubuntu 24.04 Split DNS vs MagicDNS 완전 비활성화 어느 게 나은가요"
    answer: "Tailscale 홈서버 Cloudflare Tunnel 동시 사용 DNS 충돌 해결 Ubuntu 24.04 실전 가이드에 따르면 Split DNS 방식이 더 권장됩니다. MagicDNS를 완전히 끄면 Tailscale 내부 도메인을 수동으로 관리해야 해 유지보수 부담이 커지는 반면, Split DNS는 한 번 설정해두면 두 도구가 각자 역할을 간섭 없이 수행하고 보안상 포트를 외부에 노출하지 않아도 됩니다."
aliases:
  - "/tech/2026-05-17-tailscale-홈서버-cloudflare-tunnel-동시-사용-dns-충돌-해결-ub/"

---

홈서버에 Tailscale 깔고 Cloudflare Tunnel도 연결했는데, 갑자기 내부 서비스가 안 열리는 상황 겪어봤나요? DNS가 꼬여서 `100.x.x.x` 주소로 접속이 안 되거나, 터널로 연결한 도메인이 엉뚱한 곳으로 가는 경우 — 저도 처음엔 이유를 몰라서 3시간 넘게 헤맸어요. 이 가이드는 Ubuntu 24.04 기준으로, 두 도구를 동시에 쓸 때 생기는 DNS 충돌 패턴과 해결 방법을 실제 설정 파일 기반으로 정리했어요.

> **핵심 요약**
> - Tailscale은 `100.100.100.100` MagicDNS를 시스템 DNS 앞에 끼워넣는데, Cloudflare Tunnel의 `cloudflared`도 로컬 DNS 프록시를 써요. 이 둘이 충돌하면 내부망 해석이 무너져요.
> - Ubuntu 24.04는 `systemd-resolved`를 기본 DNS 리졸버로 사용해요. 이 파일 하나를 잘못 건드리면 두 도구 모두 먹통이 돼요.
> - 해결의 핵심은 Split DNS — Tailscale 도메인(`ts.net`)은 Tailscale이, 퍼블릭 도메인은 Cloudflare가 맡도록 라우팅을 명확히 분리해야 해요.
> - `tailscale up --accept-dns=false` 옵션으로 MagicDNS를 비활성화한 뒤, `systemd-resolved`에 직접 조건부 DNS 설정을 넣는 방식이 가장 안정적이에요.
> - Tailscale v1.78+, cloudflared 2025.x 버전 조합에서 이 가이드가 검증됐어요.

---

## 왜 이 두 도구를 같이 쓰면 DNS가 꼬이는가

Tailscale과 Cloudflare Tunnel은 각자 훌륭한 도구예요. Tailscale은 WireGuard 기반 메시 VPN으로, 홈서버를 외부에서 안전하게 접속하는 데 쓰이고, Cloudflare Tunnel은 포트 포워딩 없이 퍼블릭 도메인으로 서비스를 노출하는 데 써요.

문제는 둘 다 DNS를 건드린다는 거예요.

- **Tailscale MagicDNS**: `100.100.100.100`을 시스템 DNS에 주입해서 `hostname.tail12345.ts.net` 같은 주소를 해석해요.
- **cloudflared**: 기본적으로 DoH(DNS over HTTPS)를 `1.1.1.1`로 연결하지만, `--proxy-dns` 옵션이나 일부 설정에서 로컬 포트를 점유해요.
- **systemd-resolved**: Ubuntu 24.04의 기본 리졸버인데, `127.0.0.53`을 Listen 포트로 써요. 여기서 설정이 꼬이면 두 서비스 모두 영향받아요.

세 요소가 뒤엉키면 결국 이런 증상이 나타나요:
- Tailscale 내부 주소(`100.x.x.x`)로 ping은 되는데 서비스 이름으로 접속 안 됨
- Cloudflare 터널 도메인이 외부에서 열리지 않거나 타임아웃
- `nslookup`으로 확인하면 엉뚱한 DNS 서버가 응답

---

## 구성 방식 비교

| 항목 | **Split DNS (이 가이드 방식)** | MagicDNS 전면 비활성화 | cloudflared 없이 Nginx Proxy |
|------|------|------|------|
| 설정 복잡도 | 중간 | 낮음 | 낮음 |
| Tailscale 내부 DNS | 정상 작동 | 수동 관리 필요 | 정상 작동 |
| 퍼블릭 도메인 | Cloudflare 처리 | Cloudflare 처리 | 포트 개방 필요 |
| 보안 | 높음 (포트 비노출) | 높음 | 낮음 (80/443 개방) |
| 유지보수 | 중간 | 높음 (호스트 관리) | 낮음 |
| 권장 상황 | 두 도구 동시 사용 | 단순 VPN 전용 | 방화벽 제어 가능 환경 |

Split DNS 방식이 복잡해 보이지만, 한 번 잡아두면 두 도구가 서로 간섭 없이 각자 역할을 해요. MagicDNS를 아예 끄면 Tailscale의 핵심 편의 기능 하나가 날아가버리거든요.

---

## 단계별 설정 가이드

### 사전 준비

- Ubuntu 24.04 LTS (서버 또는 데스크탑 버전)
- Tailscale v1.78 이상 설치 완료, 계정 연결 상태
- cloudflared 2025.x 버전, Cloudflare 계정 및 도메인 연결 완료
- `sudo` 권한

---

### Step 1: 현재 DNS 상태 진단

설정 바꾸기 전에 지금 상태를 먼저 확인해요.

```bash
# systemd-resolved 현재 상태 확인
resolvectl status

# Tailscale이 주입한 DNS 확인
resolvectl dns tailscale0

# cloudflared가 점유한 포트 확인 (5053이 기본)
ss -tlnp | grep cloudflared

# DNS 해석 테스트: Tailscale 내부 주소
resolvectl query $(tailscale status --json | jq -r '.Self.DNSName')
```

출력 결과에서 `tailscale0` 인터페이스에 `100.100.100.100`이 잡혀있고, `eth0`나 `ens3`에도 다른 DNS가 잡혀있으면 충돌 가능 상태예요.

---

### Step 2: Tailscale MagicDNS 분리 모드로 재시작

MagicDNS를 완전히 끄는 게 아니라, 시스템 DNS를 덮어쓰지 않도록 설정을 바꿔요.

```bash
# 기존 Tailscale 연결 해제 후 DNS 자동 설정 비활성화로 재연결
sudo tailscale up \
  --accept-dns=false \
  --accept-routes=true

# 재연결 후 상태 확인
tailscale status
```

`--accept-dns=false` 옵션이 핵심이에요. 이렇게 하면 Tailscale이 `100.100.100.100`을 시스템 전체 DNS로 밀어넣지 않아요. 대신 Step 3에서 직접 라우팅을 잡아줄 거예요.

---

### Step 3: systemd-resolved에 Split DNS 설정

`/etc/systemd/resolved.conf.d/` 디렉토리에 설정 파일을 새로 만들어요. 기존 `resolved.conf`를 직접 수정하면 시스템 업데이트 때 덮어쓰일 수 있어서, 드롭인 방식을 써요.

```bash
sudo mkdir -p /etc/systemd/resolved.conf.d/
sudo nano /etc/systemd/resolved.conf.d/tailscale-cloudflare.conf
```

파일 내용:

```ini
# Tailscale + Cloudflare Tunnel Split DNS 설정
# Tailscale MagicDNS는 ts.net 도메인만 처리
# 그 외 퍼블릭 DNS는 Cloudflare DoH로 처리

[Resolve]
# 기본 DNS: Cloudflare (퍼블릭 도메인용)
DNS=1.1.1.1 1.0.0.1
FallbackDNS=8.8.8.8

# DNSSEC 검증 활성화
DNSSEC=yes

# mDNS 비활성화 (홈서버 환경에서 불필요)
MulticastDNS=no
```

저장 후 Tailscale 인터페이스에 `100.100.100.100`을 직접 연결해요:

```bash
# tailscale0 인터페이스에 MagicDNS를 ts.net 도메인 전용으로 설정
sudo resolvectl dns tailscale0 100.100.100.100
sudo resolvectl domain tailscale0 ts.net ~ts.net

# systemd-resolved 재시작
sudo systemctl restart systemd-resolved

# 설정 확인
resolvectl status tailscale0
```

`~ts.net` 앞의 `~`가 핵심이에요. 이 표기가 "ts.net 도메인은 이 DNS 서버로만 보내라"는 라우팅 규칙을 만들어줘요.

---

### Step 4: cloudflared 설정 검토

cloudflared 서비스 파일에서 DNS 프록시 관련 옵션을 확인해요.

```bash
# cloudflared 서비스 상태 확인
sudo systemctl status cloudflared

# 설정 파일 위치 확인
cat /etc/cloudflared/config.yml
```

`config.yml`에서 아래 항목이 없는지 확인해요. 있으면 제거하세요:

```yaml
# 이 설정은 로컬 DNS 포트를 점유해서 충돌 유발 — 제거할 것
# proxy-dns: true
# proxy-dns-port: 53

# 올바른 최소 설정
tunnel: your-tunnel-id
credentials-file: /etc/cloudflared/your-tunnel-id.json

ingress:
  - hostname: yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

변경 후 서비스 재시작:

```bash
sudo systemctl restart cloudflared
sudo systemctl status cloudflared
```

---

### Step 5: 부팅 시 자동 적용 스크립트

재부팅하면 `resolvectl dns tailscale0` 설정이 날아가요. systemd 서비스로 고정해줘야 해요.

```bash
sudo nano /etc/systemd/system/tailscale-dns-fix.service
```

```ini
[Unit]
Description=Tailscale Split DNS 설정 적용
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=oneshot
# tailscale0 인터페이스에 MagicDNS 라우팅 재적용
ExecStart=/usr/bin/resolvectl dns tailscale0 100.100.100.100
ExecStart=/usr/bin/resolvectl domain tailscale0 ts.net ~ts.net
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tailscale-dns-fix
sudo systemctl start tailscale-dns-fix
```

---

## 동작 확인 및 실전 예시

### 설정 완료 후 검증

```bash
# 1. Tailscale 내부 DNS 해석 확인
resolvectl query myserver.tail12345.ts.net
# 예상 결과: 100.x.x.x 주소 반환

# 2. 퍼블릭 도메인 해석 확인 (Cloudflare 터널)
resolvectl query yourdomain.com
# 예상 결과: Cloudflare IP 반환 (104.x.x.x 또는 172.x.x.x)

# 3. 일반 인터넷 도메인 확인
resolvectl query google.com
# 예상 결과: 1.1.1.1이 응답

# 4. Tailscale 터널을 통한 서비스 접속 테스트
curl -v http://myserver.tail12345.ts.net:3000
```

### 흔한 에러와 해결

```bash
# 에러: "NXDOMAIN" — ts.net 도메인이 해석 안 될 때
# 원인: tailscale0 인터페이스 DNS가 빠진 경우
resolvectl dns  # 모든 인터페이스 DNS 출력으로 확인

# 에러: cloudflared "context deadline exceeded"
# 원인: 1.1.1.1 연결 자체가 Tailscale 라우팅에 걸린 경우
# 해결: Tailscale에서 1.1.1.1 트래픽 제외
sudo tailscale up --accept-dns=false --exit-node-allow-lan-access=true
```

---

## 자주 빠지는 함정과 체크리스트

### 흔한 실수

- **`/etc/resolv.conf` 직접 수정**: Ubuntu 24.04에서 이 파일은 `systemd-resolved`가 심볼릭 링크로 관리해요. 직접 수정하면 재부팅 때 초기화돼요.
  - 해결: 반드시 `resolved.conf.d/` 드롭인 방식 사용

- **cloudflared `proxy-dns` 옵션 활성화 상태**: 이 옵션이 켜져 있으면 포트 53을 점유하려 해서 `systemd-resolved`와 충돌해요.
  - 해결: `config.yml`에서 해당 옵션 제거

- **Tailscale 업데이트 후 MagicDNS 재활성화**: `tailscale up` 재실행 시 `--accept-dns=false`를 빠뜨리면 다시 원점이에요.
  - 해결: `/etc/tailscale/`에 설정 스크립트로 관리

### 운영 전 체크리스트

- [ ] `resolvectl status tailscale0`에서 `100.100.100.100` 확인
- [ ] `resolvectl query [ts.net 호스트명]` 성공
- [ ] `resolvectl query [퍼블릭 도메인]` Cloudflare IP 반환
- [ ] 재부팅 후 `tailscale-dns-fix` 서비스 자동 실행 확인
- [ ] cloudflared `proxy-dns` 옵션 비활성화 상태 확인
- [ ] Tailscale 연결 시 `--accept-dns=false` 옵션 포함 확인

---

## 마무리

설정이 좀 많아 보이지만, 핵심은 딱 두 가지예요.

**Tailscale에게는 `ts.net`만 맡기고, 나머지는 Cloudflare에게 맡긴다.**

`--accept-dns=false`로 MagicDNS의 시스템 전체 점령을 막고, `resolvectl domain tailscale0 ~ts.net`으로 라우팅을 명확히 분리하면, 두 도구가 서로 발 안 밟고 잘 돌아가요. 참고로 이 방식이 항상 정답은 아니에요 — 단순히 VPN만 쓰는 환경이라면 MagicDNS 전면 비활성화 쪽이 오히려 관리하기 편할 수 있어요.

Step 1부터 순서대로 따라가면 30분 안에 잡힐 거예요. 설정 중에 막히는 부분이나 특이한 에러가 생기면 댓글로 남겨주세요. 비슷한 상황 겪은 분들이 꽤 많거든요.

**다음에 볼 것**: Tailscale ACL로 서비스별 접근 제어 + Cloudflare Access와 연동해서 외부 접속에 SSO 붙이는 방법도 이어서 정리할 예정이에요.

---

*참고: [Tailscale 공식 문서 - DNS 설정](https://tailscale.com/kb/1054/dns) | [Cloudflare Tunnel 공식 문서](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)*

## 참고자료

1. [[홈서버 VPN 끝판왕] WireGuard 대신 Tailscale + NPM + Split DNS 완벽 구축 가이드](https://betwe.tistory.com/entry/%ED%99%88%EC%84%9C%EB%B2%84-VPN-%EB%81%9D%ED%8C%90%EC%99%95-WireGuard-%EB%8C%80%EC%8B%A0-Tailscale-NPM-Split-DNS-%EC%99%84%EB%B2%BD-%EA%B5%AC%EC%B6%95-%EA%B0%80%EC%9D%B4%EB%93%9C)
2. [Tailscale VPN 실무 가이드: 설치부터 운영까지의 실전 구성 방법 :: GilliLab - 정보관리기술사 노트](https://rupijun.tistory.com/entry/Tailscale-VPN-%EC%8B%A4%EB%AC%B4-%EA%B0%80%EC%9D%B4%EB%93%9C-%EC%84%A4%EC%B9%98%EB%B6%80%ED%84%B0-%EC%9A%B4%EC%98%81%EA%B9%8C%EC%A7%80%EC%9D%98-%EC%8B%A4%EC%A0%84-%EA%B5%AC%EC%84%B1-%EB%B0%A9%EB%B2%95)
3. [Tailscale - 나무위키](https://namu.wiki/w/Tailscale)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
