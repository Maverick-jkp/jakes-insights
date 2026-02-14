# 성장 전략 보고서 (Updated)

**Created**: 2026-02-10
**Last Updated**: 2026-02-10
**Status**: Phase 0 완료, Phase 1 준비 중

---

## 현재 상태 (Phase 0 완료 후)

| 항목 | Before | After |
|------|--------|-------|
| 언어 | EN/KO/JA 3개 | EN/KO 2개 |
| 일일 포스팅 | 25개 | 5개 |
| 키워드 전략 | trend only | mixed (trend 70% + evergreen 30%) |
| 사이트 브랜딩 | AI-powered multilingual blog | In-depth tech analysis, data-driven reports |
| 기존 콘텐츠 | 275개 (80 JA 삭제) | 198개 (EN 107 + KO 91) |
| 콘텐츠 품질 | EN 평균 1,631 words, KO 평균 782 words | thin content 0개 |

---

## Part A: 벤치마크 요약

### 티스토리/네이버 시사점
- 하루 5개 넘으면 저품질 판정 위험 → **5개로 축소 완료**
- 자체 도메인 + Hugo 장점: 플랫폼 정책 변경에 영향 없음
- 네이버 서치어드바이저 등록으로 KO 트래픽 별도 확보 가능

### JA 시장 판단
- JA 트래픽 0 → **완전 제거 (Phase 0-1에서 완료)**
- 향후 트래픽/수요 확인 시 재진입 가능하나, 현재는 EN/KO 집중이 최선

---

## Part B: 남은 고급 전략

### 1. Answer Engine Optimization (AEO) - 최우선
- FAQPage 스키마 추가 (모든 글에 Q&A 구조화 데이터)
- "Key Takeaways" 블록 (generate_posts.py 프롬프트에 3-5개 핵심 문장)
- 선언적 데이터 문장 → AI 검색 인용률 3배 증가 기대

### 2. Tech 100% + 커뮤니티 기반 토픽 전략 (CORE STRATEGY)
- **범위**: **Tech/SaaS/Dev 100%** (Business, Society, Sports, Entertainment 완전 제외)
- **토픽 소스** (구현 완료):
  - 🌍 해외: Dev.to, HackerNews, Hashnode → `community_miner.py`
  - 🇰🇷 국내: GeekNews, Velog, 44BITS, 요즘IT, Toss/Kakao 블로그 → `korean_community_miner.py`
  - 📊 Google Trends: 보조 (최신성 확인용)
- **전략**: 커뮤니티에서 논의되는 핫한 주제 + 깊이 있는 데이터 분석
- **CPC**: Tech/SaaS ($5-15) 집중, YMYL ($10-50+) 및 저CPC 주제 ($0.3-2) 제외
- **현황**: 커뮤니티 마이너 활성화됨, generate_posts.py에 통합 완료

### 3. 콘텐츠 신디케이션 (EN만 우선)
| 플랫폼 | 방법 | 대기 기간 |
|--------|------|-----------|
| Dev.to | API v1 + canonical_url | 3일 |
| Medium | RSS import | 5일 |
| Hashnode | API + canonical | 3일 |

- KO: Velog RSS 연동 (7일 대기)

### 4. Programmatic SEO (주의 필요)
- ❌ 대규모 자동 생성 페이지 위험 (Scaled Content Abuse)
- ✅ technologies taxonomy → /technologies/claude-ai/ 등 허브 페이지는 안전
- ✅ X vs Y 비교 페이지도 실질 콘텐츠 있으면 OK

### 5. 키워드 전략: 하이브리드 접근
| 유형 | 비중 | 설명 |
|------|------|------|
| 트렌드 앵커 + 분석 깊이 | 50% | 최신 트렌드를 앵커로 삼되 깊은 분석 제공 |
| 니치 에버그린/업데이트형 | 30% | "2026년 Best SaaS tools" 같은 연갱신형 |
| 순수 트렌드 | 20% | 속보성 트래픽 확보 |

---

## 우선순위 (수정 반영)

### ✅ 완료 (Phase 0)
- [x] JA 언어 완전 제거 (콘텐츠, 코드, 설정, 문서)
- [x] 사이트 브랜딩 업데이트 ("AI-powered" → "In-depth tech analysis")
- [x] 포스팅 볼륨 25 → 5개/일 축소
- [x] keyword_type 하드코딩 해제 (mixed mode: trend 70% + evergreen 30%)
- [x] 기존 콘텐츠 감사 (thin content 0개 확인)
- [x] 푸터 "Powered by Claude AI" 제거
- [x] Python 스크립트 JA 코드 전부 제거 (~18개 파일)

### 다음 (Phase 1 - 2주 내)
- [ ] AEO 최적화 - FAQPage 스키마 + Key Takeaways 블록
- [ ] technologies taxonomy 추가 → 허브 페이지 자동 생성
- [ ] 네이버 서치어드바이저 등록 (KO 트래픽)
- [ ] generate_posts.py 프롬프트 개선 (리포트형 데이터 분석 글)

### Phase 2 (1개월 내)
- [ ] Dev.to 크로스포스팅 자동화 (EN)
- [ ] Amazon Associates + 쿠팡파트너스 활성화
- [ ] 이메일 캡처 기본 설정

### Phase 3 (2-3개월)
- [ ] 비교 페이지 자동 생성기
- [ ] Cloudflare Worker (지역별 광고)
- [ ] 트렌드 인텔리전스 리포트 MVP

---

## AdSense 승인 전략

현재 상태: Auto Ads 활성화됨, 승인 대기 중

**승인 요인 개선:**
1. ✅ 볼륨 축소 (Scaled Content Abuse 위험 감소)
2. ✅ 콘텐츠 품질 양호 (EN 1,631 avg words)
3. ⏳ About/Privacy 페이지 메타데이터 보완 필요
4. ⏳ 사이트 연령 아직 짧음 (~3주) → 시간 필요

---

*이 보고서는 실행한 변경 사항을 반영하여 업데이트됨*
