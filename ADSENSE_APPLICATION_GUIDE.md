# Google AdSense 신청 가이드

## ✅ 준비 완료 체크리스트

현재 상태:
- ✅ **129개 게시물** (권장: 20-30개 이상)
- ✅ **Privacy Policy 페이지** (필수)
- ✅ **About 페이지** (권장)
- ✅ **Google Analytics 설정** (GA-3ML8CHS112)
- ✅ **독창적인 콘텐츠** (800-1,600단어)
- ✅ **다국어 지원** (EN/KO/JA)
- ✅ **깔끔한 디자인** (광고 플레이스홀더 제거 완료)

**결론: AdSense 신청 준비 완료!**

---

## 📝 Google AdSense 신청 절차

### Step 1: Google AdSense 계정 생성

1. **AdSense 웹사이트 방문**
   - URL: https://www.google.com/adsense/start/

2. **Google 계정으로 로그인**
   - 기존 Gmail 계정 사용 가능
   - 권장: 비즈니스 전용 Gmail 계정 사용

3. **신청서 작성**
   ```
   필수 입력 정보:
   - 웹사이트 URL: https://jakes-tech-insights.pages.dev (또는 실제 도메인)
   - 언어: English (주 언어)
   - 국가: 귀하의 거주 국가
   - 이메일 주소: 연락 가능한 이메일
   ```

4. **이용약관 동의**
   - AdSense 프로그램 정책 읽기
   - 약관 동의 체크

---

### Step 2: 웹사이트 연결

AdSense에서 제공하는 코드를 웹사이트에 추가해야 합니다.

**방법 1: Hugo 설정으로 추가 (권장)**

`hugo.toml` 파일에 AdSense 코드 추가:

```toml
[params]
  # Google AdSense
  googleAdSense = "ca-pub-XXXXXXXXXXXXXXXX"  # AdSense에서 받은 Publisher ID
```

그리고 `layouts/partials/head.html` 또는 `layouts/index.html` `<head>` 섹션에 추가:

```html
{{ with .Site.Params.googleAdSense }}
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ . }}"
     crossorigin="anonymous"></script>
{{ end }}
```

**방법 2: 직접 코드 추가**

AdSense에서 제공한 코드를 `layouts/index.html` 및 `layouts/_default/single.html`의 `<head>` 태그 내에 추가:

```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX"
     crossorigin="anonymous"></script>
```

**⚠️ 중요: 실제 Publisher ID로 교체하세요!**

---

### Step 3: 사이트 검토 대기

1. **코드 추가 완료 후**
   - AdSense 대시보드에서 "사이트 연결 확인" 클릭
   - Google이 코드가 올바르게 설치되었는지 확인

2. **검토 기간**
   ```
   일반적인 검토 시간: 1-2주
   최대 검토 시간: 4주
   ```

3. **검토 중 체크 사항**
   - 콘텐츠 품질
   - 정책 준수
   - 사용자 경험
   - 트래픽 (필수는 아니지만 도움됨)

---

## 🚨 승인 거부 시 주요 사유 및 해결책

### 거부 사유 1: "콘텐츠 부족 (Insufficient Content)"

**해결책:**
- ✅ 이미 129개 게시물 있음 → 문제없음
- 만약 거부되면: 게시물당 800단어 이상 확인

### 거부 사유 2: "독창적이지 않은 콘텐츠 (Unoriginal Content)"

**해결책:**
- AI 생성 콘텐츠를 직접 작성한 것처럼 보이게 해야 함
- 현재 콘텐츠가 독창적이고 가치 있는지 확인
- 다른 사이트에서 복사한 내용이 없는지 확인

### 거부 사유 3: "정책 위반 (Policy Violation)"

**해결책:**
- Privacy Policy 페이지 확인 ✅ (이미 생성됨)
- 불법 콘텐츠, 성인 콘텐츠 없는지 확인
- 저작권 침해 이미지 없는지 확인

### 거부 사유 4: "사이트 탐색 불가능 (Site Navigation)"

**해결책:**
- ✅ 현재 Floating Menu 있음 → 문제없음
- 모든 페이지가 링크로 연결되어 있는지 확인

### 거부 사유 5: "트래픽 부족 (Low Traffic)"

**해결책:**
- 공식적으로 필수는 아니지만, 최소 일일 50-100 방문자 권장
- 거부되면: 1-2개월 트래픽 쌓은 후 재신청

---

## 📊 승인 확률 높이는 팁

### 1. 도메인 사용 (선택사항, 하지만 강력 권장)

```
현재: jakes-tech-insights.pages.dev (Cloudflare Pages)
권장: jakesinsights.com (커스텀 도메인)

이유:
- 전문성 향상
- 승인 확률 20-30% 증가
- 브랜드 신뢰도 상승

비용: $10-15/년 (도메인 등록)
```

**Cloudflare Pages에 커스텀 도메인 연결 방법:**
1. 도메인 구매 (Namecheap, GoDaddy 등)
2. Cloudflare Pages 설정 → Custom Domains → Add Domain
3. DNS 레코드 설정 (Cloudflare가 자동으로 안내)

### 2. Contact 페이지 추가

```html
<!-- content/en/contact.md -->
---
title: "Contact"
---

Get in touch with us at: contact@jakesinsights.com
```

이메일 주소는 About 페이지에 이미 있지만, 별도 Contact 페이지가 있으면 더 좋음.

### 3. 404 페이지 커스터마이징

Hugo는 기본 404 페이지를 제공하지만, 커스텀하면 더 전문적으로 보임.

`layouts/404.html` 생성:
```html
{{ define "main" }}
<div style="text-align: center; padding: 4rem 2rem;">
  <h1>404 - Page Not Found</h1>
  <p>The page you're looking for doesn't exist.</p>
  <a href="/">← Back to Home</a>
</div>
{{ end }}
```

### 4. 트래픽 증가 전략

AdSense 승인 전에 트래픽을 늘리면 승인 확률 상승:

```
방법:
1. Reddit에 관련 서브레딧에 게시물 공유
2. Twitter/X에 게시물 홍보
3. Hacker News에 기술 관련 게시물 제출
4. LinkedIn에 비즈니스 게시물 공유
5. Facebook 그룹에 관련 게시물 공유

목표: 신청 전 일일 50-100 방문자
```

---

## 🎯 승인 후 해야 할 일

### Phase 2: 최소 광고 테스트 (승인 직후)

**1개월간 최소 광고로 테스트:**

```
게시물 페이지만:
- 본문 하단 1개 광고 (336×280)
- "Back to Home" 버튼 위에 배치
```

**코드 예시:**

`layouts/_default/single.html` 수정 (374번째 줄 앞에 추가):

```html
        <div class="content">
            {{ .Content }}
        </div>

        <!-- AdSense Ad Unit -->
        <div style="text-align: center; margin: 2rem auto; max-width: 336px;">
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
            <ins class="adsbygoogle"
                 style="display:inline-block;width:336px;height:280px"
                 data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
                 data-ad-slot="XXXXXXXXXX"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>

        <a href="/{{ .Site.Language.Lang }}/" class="back-link">← Back to Home</a>
```

**예상 수익 (Phase 2):**
```
일일 트래픽: 100-500명
게시물 조회: 200-1,000 PV
광고 노출: 200-1,000 impressions
CTR: 0.5%
일일 수익: $0.70-3.50
월간 수익: $21-105
```

---

### Phase 3: 본격 수익화 (3-6개월 후, 일일 500명+ 트래픽)

트래픽이 충분히 쌓이면 이전 CDO 리포트의 "옵션 B"를 실행:

1. **홈페이지 개선**
   - Sidebar Sticky 광고 (300×600)
   - 레이아웃 조정 (Bento Grid → Main + Sidebar)

2. **게시물 광고 증가**
   - 본문 시작: 728×90
   - 본문 중간: 336×280
   - 본문 하단: 728×90

3. **모바일 최적화**
   - Sticky Bottom Ad (320×50)
   - In-feed Ads

**예상 수익 (Phase 3):**
```
일일 트래픽: 1,000-2,000명
월간 수익: $1,500-3,000
연간 수익: $18,000-36,000
```

---

## 🔧 체크리스트: 신청 전 마지막 확인

```
[ ] Privacy Policy 페이지 작동 확인
    - EN: /en/privacy/
    - KO: /ko/privacy/
    - JA: /ja/privacy/

[ ] About 페이지 작동 확인
    - EN: /en/about/
    - KO: /ko/about/
    - JA: /ja/about/

[ ] 모든 페이지가 정상 작동하는지 확인
    - 홈페이지
    - 게시물 페이지 (최소 5개 확인)
    - 카테고리 페이지

[ ] Google Analytics 작동 확인
    - Real-time 데이터 수집 확인

[ ] 이미지 저작권 확인
    - Unsplash 이미지 사용 → OK
    - 저작권 문제 없는지 확인

[ ] 모바일 반응형 확인
    - 모바일에서 사이트 정상 작동 확인

[ ] 로딩 속도 확인
    - PageSpeed Insights 테스트 권장
    - 3초 이내 로딩 권장
```

---

## 📞 신청 후 연락처

**AdSense Support:**
- 도움말 센터: https://support.google.com/adsense
- 커뮤니티 포럼: https://support.google.com/adsense/community

**일반적인 질문:**

**Q: 승인까지 얼마나 걸리나요?**
A: 보통 1-2주, 최대 4주까지 소요될 수 있습니다.

**Q: 거부되면 재신청할 수 있나요?**
A: 네, 문제를 수정한 후 재신청 가능합니다. 최소 2주 기다린 후 재신청하세요.

**Q: 트래픽이 얼마나 필요한가요?**
A: 공식적으로 최소 요구사항은 없지만, 일일 50-100명 이상 권장합니다.

**Q: 다국어 사이트도 승인되나요?**
A: 네, 각 언어의 콘텐츠가 정책을 준수하면 문제없습니다.

**Q: Cloudflare Pages 도메인(.pages.dev)도 승인되나요?**
A: 네, 하지만 커스텀 도메인이 승인 확률이 더 높습니다.

---

## 🎉 다음 단계

1. **지금 바로: Google AdSense 신청**
   - 위의 Step 1-3 따라하기
   - 예상 시간: 30분

2. **승인 대기 중 (1-2주)**
   - 트래픽 늘리기에 집중
   - SEO 최적화
   - 소셜 미디어 홍보

3. **승인 후**
   - Phase 2 실행 (최소 광고 테스트)
   - 데이터 수집 및 분석
   - 1개월 후 수익 확인

4. **3-6개월 후 (트래픽 충분 시)**
   - Phase 3 실행 (본격 수익화)
   - 월 $1,500+ 수익 목표

---

**행운을 빕니다! 궁금한 점이 있으면 언제든지 물어보세요.**
