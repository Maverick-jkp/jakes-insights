# 🚀 Feature Development Workflow

새로운 기능 개발을 위한 표준 워크플로우

---

## 📋 Overview

```
사용자 요청 → 분석 → 계획 → 티켓 생성 → 병렬/순차 개발 → 통합 → 배포
```

---

## Phase 1: 요구사항 분석 (Master)

### 1.1 요구사항 명확화

```markdown
Master가 수행:
1. 사용자 요청 이해
   - 무엇을 원하는가?
   - 왜 필요한가?
   - 어떤 결과를 기대하는가?

2. 불명확한 부분 질문
   - 우선순위는?
   - 제약사항은?
   - 예상 사용 사례는?

3. 범위 설정
   - MVP 정의
   - 제외할 것 명시
   - 단계적 구현 여부
```

### 1.2 현재 코드베이스 분석

```bash
# Master가 실행할 명령어들
git status                           # 현재 상태
git log --oneline -10               # 최근 커밋
ls -la {관련_디렉토리}                # 구조 파악

# 관련 파일 검색
grep -r "관련_키워드" scripts/
find . -name "*관련_파일명*"
```

---

## Phase 2: 작업 분해 및 계획 (Master)

### 2.1 작업 분해

```markdown
기준:
1. 기능 단위로 분리
   - 각 기능은 독립적으로 동작
   - 명확한 입력/출력
   - 테스트 가능

2. 의존성 파악
   - A가 완료되어야 B 시작 가능?
   - 병렬 작업 가능 여부
   - 공유 리소스 (파일 등)

3. 에이전트 할당
   - UI 변경 → DESIGNER
   - Python 로직 → DEV_BACKEND
   - 아키텍처 결정 → CTO
   - 테스트 → DEV_TESTING
```

### 2.2 브랜치 전략 결정

```markdown
병렬 작업 조건:
✓ 서로 다른 파일 수정
✓ 의존성 없음
✓ 독립적으로 테스트 가능

순차 작업 조건:
⚠️ 같은 파일 수정
⚠️ A의 결과를 B가 사용
⚠️ 통합 테스트 필요
```

**예시:**

```
Task 1: 다크모드 UI (독립) → feature/dark-mode
Task 2: 성능 최적화 (독립) → feature/performance
Task 3: 통합 테스트 (의존) → feature/integration-tests

실행 계획:
Phase 1: Task 1, 2 병렬 실행
Phase 2: Task 3 순차 실행 (1, 2 완료 후)
```

---

## Phase 3: 티켓 생성 (Master)

### 3.1 티켓 파일 생성

```bash
# Master가 생성
.claude/tasks/TASK_001_dark_mode.md
.claude/tasks/TASK_002_performance.md
.claude/tasks/TASK_003_integration_tests.md
```

### 3.2 티켓 내용 (템플릿 사용)

```markdown
# TASK_001: 다크모드 구현

## 목표
사용자가 다크모드를 토글할 수 있도록 UI 추가

## 담당 에이전트
- DESIGNER (Primary)
- DEV_FRONTEND (Support)

## 브랜치
`feature/dark-mode`

## 의존성
- 없음 (독립 작업)

## 요구사항
1. [ ] CSS 변수 기반 색상 시스템
2. [ ] 다크모드 토글 버튼
3. [ ] localStorage 저장
4. [ ] 시스템 설정 존중 (prefers-color-scheme)

## 기술 스펙
- CSS Variables: --color-bg, --color-text, etc.
- Toggle: JavaScript (localStorage)
- 접근성: WCAG AA 색상 대비

## 체크리스트
- [ ] 디자인 시안 확인
- [ ] CSS 변수 리팩토링
- [ ] 토글 버튼 구현
- [ ] localStorage 로직
- [ ] 반응형 테스트 (mobile, tablet, desktop)
- [ ] 접근성 검증 (색상 대비)
- [ ] 커밋 및 푸시

## 예상 작업 시간
1-2 시간

## 참고
- 디자인 시스템: `.claude/docs/design-system.md`
- 색상 팔레트: 기존 스타일 참고
```

---

## Phase 4: 개발 실행

### 4.1 병렬 작업 시작 (사용자)

```markdown
사용자가 수행:
1. 세션 1 (Master): 대기 (모니터링)
2. 세션 2 (DESIGNER): "TASK_001_dark_mode.md 읽고 작업 시작해"
3. 세션 3 (DEV_BACKEND): "TASK_002_performance.md 읽고 작업 시작해"

각 세션에서:
1. 티켓 읽기
2. 브랜치 생성
3. 개발 수행
4. 테스트
5. 커밋 (머지 안 함!)
6. 완료 보고
```

### 4.2 각 에이전트의 작업 흐름

**DESIGNER (예시):**

```bash
# 1. 티켓 읽기
cat .claude/tasks/TASK_001_dark_mode.md

# 2. 브랜치 생성
git checkout -b feature/dark-mode

# 3. 파일 수정
# - layouts/partials/header.html (토글 버튼)
# - assets/css/variables.css (CSS 변수)
# - assets/js/theme-toggle.js (토글 로직)

# 4. 테스트
hugo server  # 수동 확인 요청

# 5. 커밋 (머지는 Master가!)
git add .
git commit -m "feat: Add dark mode toggle with CSS variables"
git push -u origin feature/dark-mode

# 6. 완료 보고 (세션 1의 Master에게 알림)
"feature/dark-mode 작업 완료했습니다!"
```

**DEV_BACKEND (예시):**

```bash
# 1. 티켓 읽기
cat .claude/tasks/TASK_002_performance.md

# 2. 브랜치 생성
git checkout -b feature/performance

# 3. 코드 수정
# - scripts/generate_posts.py (캐싱 추가)
# - .github/workflows/daily-content.yml (병렬화)

# 4. 테스트
pytest tests/test_generate_posts.py

# 5. 커밋
git add .
git commit -m "perf: Add caching to content generation"
git push -u origin feature/performance

# 6. 완료 보고
"feature/performance 작업 완료했습니다!"
```

---

## Phase 5: 통합 (Master)

### 5.1 모든 작업 완료 대기

```markdown
Master 체크리스트:
- [ ] 모든 에이전트 작업 완료 보고 받음
- [ ] 각 브랜치 푸시 확인
- [ ] CI/CD 테스트 통과 확인
```

### 5.2 브랜치 검토

```bash
# Master가 각 브랜치 검토
git fetch --all

# 브랜치별 검토
git checkout feature/dark-mode
git log --oneline
git diff main...feature/dark-mode
pytest  # 테스트 실행

git checkout feature/performance
git log --oneline
git diff main...feature/performance
pytest  # 테스트 실행
```

### 5.3 충돌 확인

```bash
# main으로 돌아가서 머지 시뮬레이션
git checkout main
git merge feature/dark-mode --no-commit --no-ff

# 충돌 있으면:
git merge --abort
# → 담당 에이전트와 상의 후 해결

# 충돌 없으면:
git merge --abort  # 시뮬레이션 취소
```

### 5.4 순차 통합

```bash
# Master가 수행 (충돌 없는 경우)
git checkout main

# 1. 첫 번째 브랜치 머지
git merge feature/dark-mode
pytest  # 통합 테스트

# 2. 두 번째 브랜치 머지
git merge feature/performance
pytest  # 통합 테스트

# 3. 추가 브랜치 (의존성 있는 것)
git merge feature/integration-tests
pytest  # 최종 통합 테스트
```

### 5.5 최종 검증

```bash
# 통합 테스트
pytest --cov=scripts --cov-report=term

# 빌드 확인
hugo

# 수동 테스트 (필요시)
hugo server
# 사용자에게 확인 요청: "localhost:1313 에서 확인해주세요"
```

---

## Phase 6: 배포 (Master)

### 6.1 최종 커밋

```bash
# 변경사항이 있다면 최종 정리 커밋
git add .
git commit -m "$(cat <<'EOF'
feat: Add dark mode and performance improvements

- Dark mode toggle with CSS variables
- Performance optimizations for content generation
- Integration tests for new features

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### 6.2 푸시

```bash
git push origin main
```

### 6.3 브랜치 정리 (선택)

```bash
# 원격 브랜치 삭제
git push origin --delete feature/dark-mode
git push origin --delete feature/performance
git push origin --delete feature/integration-tests

# 로컬 브랜치 삭제
git branch -d feature/dark-mode
git branch -d feature/performance
git branch -d feature/integration-tests
```

### 6.4 문서 업데이트

```bash
# CHANGELOG 업데이트
# docs/ 관련 문서 업데이트
git add .
git commit -m "docs: Update CHANGELOG for v1.2.0"
git push
```

---

## 📊 Decision Matrix

### 병렬 vs. 순차 결정

| 조건 | 병렬 | 순차 |
|------|------|------|
| 서로 다른 파일 수정 | ✓ | |
| 같은 파일 수정 | | ✓ |
| 의존성 없음 | ✓ | |
| A → B 의존성 | | ✓ |
| 독립 테스트 가능 | ✓ | |
| 통합 테스트 필요 | | ✓ |

### 에이전트 할당 기준

| 작업 유형 | 담당 에이전트 |
|-----------|---------------|
| UI/UX 디자인 | DESIGNER |
| 레이아웃 변경 | DESIGNER |
| Python 로직 | DEV_BACKEND |
| API 통합 | DEV_BACKEND |
| 아키텍처 변경 | CTO |
| 성능 최적화 | CTO + DEV_BACKEND |
| 테스트 작성 | DEV_TESTING |
| 테스트 커버리지 | DEV_TESTING |

---

## 🚨 Common Pitfalls

### 1. 병렬 작업 시 같은 파일 수정

```markdown
❌ 문제:
- Task 1: layouts/baseof.html 수정 (dark mode)
- Task 2: layouts/baseof.html 수정 (SEO)
- 결과: 충돌!

✓ 해결:
- 순차 작업으로 변경
- 또는 더 작은 단위로 분리 (partials 사용)
```

### 2. 의존성 미파악

```markdown
❌ 문제:
- Task 1: API 스키마 변경
- Task 2: API 사용하는 로직 수정
- 병렬 실행 → Task 2가 실패

✓ 해결:
- Task 1 완료 후 Task 2 시작 (순차)
```

### 3. Master 외 다른 에이전트가 머지

```markdown
❌ 문제:
- DEV_BACKEND가 자신의 브랜치를 main에 머지
- 통합 검증 없이 배포

✓ 해결:
- Master만 머지 권한
- 다른 에이전트는 커밋만
```

---

## 📖 Templates

- **티켓 템플릿**: `.claude/templates/task-template.md`
- **PR 템플릿**: `.claude/templates/pr-template.md`
- **완료 보고 템플릿**: 각 에이전트 가이드 참고

---

## 📝 Example: 실제 작업 흐름

### 요청: "사용자 인증 시스템 추가"

**Phase 1: 분석 (Master)**
```
복잡도: 높음
에이전트 필요: CTO, DEV_BACKEND, DEV_TESTING
병렬 가능: 부분적
```

**Phase 2: 분해 (Master)**
```
TASK_001: 아키텍처 설계 (CTO)
  - 브랜치: feature/auth-architecture
  - 문서화만 (코드 없음)

TASK_002: Backend API (DEV_BACKEND) - TASK_001 후
  - 브랜치: feature/auth-backend
  - 의존: TASK_001 설계 참고

TASK_003: 테스트 (DEV_TESTING) - TASK_002 후
  - 브랜치: feature/auth-tests
  - 의존: TASK_002 API
```

**Phase 3: 실행**
```
세션 1 (Master): 모니터링
세션 2 (CTO): TASK_001 (문서화)
  → 완료 후 세션 2 종료

세션 3 (DEV_BACKEND): TASK_002 (API 구현)
  → 완료 후 세션 3 종료

세션 4 (DEV_TESTING): TASK_003 (테스트)
  → 완료 후 세션 4 종료
```

**Phase 4: 통합 (Master)**
```bash
git checkout main
git merge feature/auth-architecture  # 문서
git merge feature/auth-backend       # API
git merge feature/auth-tests         # 테스트
pytest  # 최종 검증
git push origin main
```

---

**Last Updated**: 2026-01-20
**Version**: 1.0
