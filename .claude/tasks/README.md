# Tasks Management

이 디렉토리는 프로젝트의 태스크 티켓을 관리합니다.

## 디렉토리 구조

```
tasks/
├── active/          # 진행 중인 작업 티켓
└── archive/         # 완료된 작업 아카이브
    └── YYYY-MM/     # 월별 아카이브
```

## 티켓 생명주기

### 1. 티켓 생성 (선택 사항)

복잡한 작업의 경우 `active/` 디렉토리에 티켓 생성:

```bash
.claude/tasks/active/TASK_001_feature_name.md
```

**티켓 템플릿**:
```markdown
# TASK_001: {기능명}

**생성일**: 2026-01-20
**담당 에이전트**: {AGENT_NAME}
**브랜치**: feature/{branch-name}
**상태**: pending

## 목표
{작업 목표 설명}

## 작업 내용
- {작업 항목 1}
- {작업 항목 2}
- {작업 항목 3}

## 의존성
- {없음 / TASK_XXX 완료 후}

## 완료 조건
- [ ] {체크리스트 1}
- [ ] {체크리스트 2}
- [ ] {체크리스트 3}

## 결과
{완료 후 작성}

**완료일**: {YYYY-MM-DD}
```

### 2. 티켓 진행

- 작업 시작 시: 상태를 `in_progress`로 변경
- 체크리스트 항목 완료 시: `[x]`로 체크

### 3. 티켓 완료 및 아카이빙

작업 완료 및 커밋 후:

```bash
# 1. 완료 날짜 기록
echo "**완료일**: $(date +%Y-%m-%d)" >> .claude/tasks/active/TASK_001_feature_name.md

# 2. 상태 업데이트 (completed)
# 3. 결과 섹션 작성

# 4. 월별 아카이브로 이동
mkdir -p .claude/tasks/archive/$(date +%Y-%m)
mv .claude/tasks/active/TASK_001_feature_name.md .claude/tasks/archive/$(date +%Y-%m)/
```

## 티켓 사용 지침

### 언제 티켓을 생성하나?

**티켓 생성 권장**:
- 여러 단계로 나뉜 복잡한 작업
- 여러 에이전트가 협업하는 작업
- 장기간 진행되는 작업
- 추후 참고가 필요한 작업

**티켓 없이 진행 가능**:
- 간단한 버그 수정
- 단일 파일 수정
- 빠르게 완료되는 작업

### 티켓 명명 규칙

```
TASK_{번호}_{간단한_설명}.md

예시:
- TASK_001_dark_mode.md
- TASK_002_performance_optimization.md
- TASK_003_test_coverage_improvement.md
```

## 아카이브 활용

완료된 티켓은 다음과 같이 활용:
- 유사한 작업 시 참고 자료
- 프로젝트 히스토리 추적
- 작업 패턴 분석
- 향후 개선 사항 도출

## 주의사항

1. **간단한 작업은 티켓 불필요**: 모든 작업에 티켓을 생성할 필요는 없습니다
2. **커밋 메시지로 충분한 경우**: 티켓 대신 상세한 커밋 메시지 활용
3. **정기적 아카이빙**: active/ 디렉토리가 과도하게 쌓이지 않도록 완료된 티켓은 즉시 아카이빙

---

**Last Updated**: 2026-01-20
**Maintained By**: MASTER Agent
