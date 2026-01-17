# Google Custom Search API Setup Guide

Google Custom Search API를 사용하여 실시간 트렌드 데이터를 가져오는 방법입니다.

## 1. Google API Key 발급

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성 또는 선택
3. 왼쪽 메뉴에서 **APIs & Services** → **Credentials** 클릭
4. 상단의 **Create credentials** → **API key** 클릭
5. 생성된 키 복사 → 이것이 `GOOGLE_API_KEY`

### API 활성화

6. 왼쪽 메뉴에서 **APIs & Services** → **Library** 클릭
7. "Custom Search API" 검색
8. **Custom Search API** 클릭 → **Enable** 버튼 클릭

## 2. Custom Search Engine 생성

1. [Programmable Search Engine](https://programmablesearchengine.google.com/) 접속
2. **Add** 버튼 클릭
3. 검색엔진 설정:
   - **Name**: Jake's Tech Insights Trends
   - **What to search**: Search the entire web
   - **Search settings**:
     - Turn on "Search the entire web"
     - Turn off "Image search"
4. **Create** 버튼 클릭
5. 생성된 **Search Engine ID** 복사 → 이것이 `GOOGLE_CX`

## 3. 환경 변수 설정

### macOS/Linux (`.zshrc` 또는 `.bashrc`에 추가)

```bash
# Google Custom Search API
export GOOGLE_API_KEY="your-google-api-key-here"
export GOOGLE_CX="your-search-engine-id-here"
```

설정 후:
```bash
source ~/.zshrc
```

### 확인

```bash
echo $GOOGLE_API_KEY
echo $GOOGLE_CX
```

## 4. 테스트

```bash
cd /Users/jakepark/projects/jakes-tech-insights
python3 scripts/keyword_curator.py --count 15
```

성공 시:
```
============================================================
  🔍 Fetching trending topics from Google...
============================================================

  ✓ Fetched 5 results for: AI trends 2026
  ✓ Fetched 5 results for: tech news today
  ...
```

## 5. 비용 안내

- **Custom Search API**: 하루 100회 무료, 이후 $5/1000 쿼리
- **주간 키워드 수집**: 8개 쿼리 × 4주 = 32회/월 (무료 범위 내)
- **추가 비용 없음** (월 100회 미만)

## 6. 문제 해결

### API Key가 작동하지 않는 경우

1. Google Cloud Console → **APIs & Services** → **Credentials**
2. API Key 클릭 → **API restrictions**
3. "Restrict key" → "Custom Search API" 선택
4. Save

### CX ID를 찾을 수 없는 경우

1. [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. 생성한 검색엔진 클릭
3. **Setup** → **Basic** → **Search engine ID** 복사

### "API not enabled" 오류

1. Google Cloud Console → **APIs & Services** → **Library**
2. "Custom Search API" 검색 → Enable

## 7. 자동화 스크립트

환경 변수가 설정되면 cron job이 자동으로 작동합니다:

```bash
# Weekly keyword curation (Sundays 6 PM KST)
0 18 * * 0 cd /Users/jakepark/projects/jakes-tech-insights && source ~/.zshrc && python3 scripts/keyword_curator.py --count 15
```

---

**참고**: API 키는 절대 GitHub에 커밋하지 마세요. 환경 변수로만 관리하세요.
