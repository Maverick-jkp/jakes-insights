# Content Strategy Execution Plan

**Date**: 2026-01-22
**Based on**: master-content-strategy-analysis-2026-01-22.md
**System**: 4.5 (Pragmatic Parallel)
**Status**: Ready to Execute

---

## Executive Summary

Content strategy 분석 리포트를 기반으로 **실행 가능한 작업 계획**을 세웠습니다.

**핵심 발견 (재확인)**:
1. 🟢 EN: Medium 스타일 성공적이나 개인 일화 과다
2. 🟡 KO: 토스 스타일 좋으나 정보 밀도 부족
3. 🔴 JA: 자연스러우나 "私" 과다 + 결론 늦게 나옴
4. 🟡 키워드: 트렌드는 좋으나 검색 의도 불일치

**Tier 1 액션 (즉시 실행)**:
1. ✅ System Prompt 수정 (EN/KO/JA)
2. ⏳ 중복 References 제거 (이미 코드 수정 완료)
3. ⏳ 기존 인기 글 최적화 (optional)

---

## Part 1: 작업 분해 (System 4.5 적용)

### 작업 1: System Prompt 개선

**Agent**: CTO (owns `scripts/generate_posts.py`)
**Scope**: `scripts/` only
**Parallel 가능**: YES (단독 작업)
**예상 시간**: 1-1.5 hours

**Task Description**:
```markdown
Modify `scripts/generate_posts.py` SYSTEM_PROMPTS section:

EN improvements:
- Remove personal anecdote patterns: "My friend", "I spoke with", "In my experience"
- Add: "Use data sources: 'According to [Source]', 'Industry reports show'"
- Emphasize: Strong facts over personal stories

KO improvements:
- Front-load key information: "도입부 1-2단락으로 핵심 전달"
- Add specific numbers requirement: "구체적 수치 필수 (%, 금액, 날짜)"
- Reduce "~거든요" usage

JA improvements:
- 結論ファースト structure: "最初に結論/要点を述べる"
- Minimize "私": "筆者 또는 주어 생략 선호"
- Add spec requirements for tech: "Tech 카테고리는 価格/スペック 필수"
```

**Deliverable**: Updated `scripts/generate_posts.py` + Report

---

### 작업 2: 기존 글 최적화 (Optional)

**Option A: Manual Edit (Master)**
- Master가 직접 인기 글 2-3개 수정
- 실용 정보 섹션 추가
- 예상 시간: 2-3 hours

**Option B: Skip for Now**
- 새 글부터 improved prompts 적용
- 기존 글은 트래픽 모니터링 후 판단
- 우선순위: 낮음

**추천**: Option B (새 콘텐츠에 집중)

---

### 작업 3: Pre-Commit Hook 설치

**Agent**: Master (owns `.git/hooks/`)
**Scope**: Git hooks only
**Parallel 가능**: N/A (5분 작업)
**예상 시간**: 5 minutes

**Task**: System 4.5 pre-commit hook 설치 및 테스트

---

## Part 2: System 4.5 Parallel Analysis

### Can We Parallelize?

**작업 1 (System Prompt)**: CTO → `scripts/`
**작업 2 (글 최적화)**: Master → `content/`
**작업 3 (Hook 설치)**: Master → `.git/hooks/`

**Scope Overlap Check**:
- 작업 1 vs 2: `scripts/` vs `content/` → **No overlap**
- 작업 1 vs 3: `scripts/` vs `.git/` → **No overlap**
- 작업 2 vs 3: `content/` vs `.git/` → **No overlap**

**Dependency Check**:
- 작업 1 완료 후 새 글 생성해야 효과 확인 가능
- 작업 2는 독립적 (기존 글 수정)
- 작업 3은 독립적 (시스템 설정)

**Decision**:
- **작업 1 단독 실행** (가장 중요, 새 콘텐츠에 영향)
- **작업 2 Skip** (우선순위 낮음)
- **작업 3 Master가 빠르게 처리** (5분)

**Result**: Sequential execution, but fast (1.5h total)

---

## Part 3: Detailed Execution Steps

### Step 1: Pre-Commit Hook 설치 (5 min)

**Master executes**:
```bash
# Copy code from CLAUDE-4.5.md
cat > .git/hooks/pre-commit << 'EOF'
[hook code from CLAUDE-4.5.md]
EOF

chmod +x .git/hooks/pre-commit

# Test
git config user.name "Master"
echo "test" > test-file.txt
git add test-file.txt
git commit -m "test: Pre-commit hook validation"
# Should pass

git config user.name "Designer"
echo "test" >> scripts/test.py
git add scripts/test.py
git commit -m "test"
# Should FAIL with scope violation
git reset HEAD scripts/test.py
```

**Expected**: ✅ Hook blocks Designer from modifying scripts/

---

### Step 2: Delegate to CTO (System Prompt Improvements)

**Master delegates**:

```markdown
You are CTO Agent.

Task: Improve SYSTEM_PROMPTS in scripts/generate_posts.py

Context:
Based on master-content-strategy-analysis-2026-01-22.md, we need to fix:

EN (line ~57):
- Problem: Too many personal anecdotes ("My friend", "I spoke with")
- Fix: Add strong directive to use data sources instead
- Add to prompt:
  ```
  **Sources over Stories**:
  - ❌ Avoid: "My friend Sarah...", "I spoke with an expert..."
  - ✅ Prefer: "According to [Source]", "Research shows...", "Data from [Org]"
  - Use statistics and published reports over personal anecdotes
  ```

KO (line ~131):
- Problem: Information comes too late (3 paragraphs before key facts)
- Fix: Add front-loading requirement
- Add to prompt:
  ```
  **정보 우선 구조 (Information-First)**:
  - 도입부 1-2단락 내에 핵심 정보 제시
  - 구체적 수치 필수 (%, 금액, 날짜, 비율)
  - "~거든요" 사용 제한 (전체 글에서 5회 이하)
  ```

JA (line ~205):
- Problem: "私" overuse, conclusion comes late, missing specs for tech
- Fix: Add 結論ファースト structure + spec requirement
- Add to prompt:
  ```
  **結論ファースト構造**:
  - 最初の2段落で結論/要点を提示
  - "私" の使用を最小限に (筆者 または 主語省略を選好)
  - Tech カテゴリ: 価格/スペック/比較表 必須

  **Tech コンテンツの必須要素**:
  - 価格情報 (available or estimated)
  - スペック比較表
  - 購入可能な場所/リンク
  ```

Your scope: scripts/ only (pre-commit hook will enforce)

Expected output:
- Modified scripts/generate_posts.py
- Report: .claude/reports/active/cto-system-prompts-improvement-2026-01-22.md

Test your changes:
- Run: python scripts/generate_posts.py --count 1
- Verify: Generated content follows new guidelines

DO NOT commit. Create report and return to Master.
```

**CTO works**: ~1-1.5 hours
**CTO delivers**: Report with changes

---

### Step 3: Master Reviews & Tests

**Master executes**:
```bash
# Review CTO's report
cat .claude/reports/active/cto-system-prompts-improvement-2026-01-22.md

# Test generation with new prompts
python scripts/generate_posts.py --count 1

# Check output
# EN: Should have "According to", "Research shows" instead of "My friend"
# KO: Should have key info in first 2 paragraphs
# JA: Should have 結論 first, less "私"

# If tests pass:
git add scripts/generate_posts.py
git commit -m "feat: Improve writing style prompts for native appeal

EN: Replace personal anecdotes with data sources
KO: Front-load key information, add specific numbers
JA: 結論ファースト structure, minimize 私, add spec tables

Based on content-strategy-analysis report.
Tested with 1 generation - prompts working as expected.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin main
```

---

### Step 4: Monitor Next Generation (Verification)

**Tomorrow's 18:00 KST automation**:
- 3 posts will be generated with new prompts
- Master should check:
  - EN posts: Data sources > personal stories?
  - KO posts: Key info in first 2 paragraphs?
  - JA posts: 結論ファースト? Less 私?

**If improvements visible**: ✅ System Prompt fix successful
**If not**: Iterate on prompts (may need stronger directives)

---

## Part 4: Why Not Parallel This Time?

**Analysis**:
- Only 1 critical task (System Prompt fix)
- Other tasks are low priority (글 최적화) or quick (hook 설치)
- CTO task is 1.5h → Adding parallel work doesn't save time

**System 4.5 principle**: **Don't force parallel for sake of parallel**

**Better approach**:
- Quick wins first (hook: 5min)
- Critical work focus (CTO: 1.5h)
- Skip non-critical (글 최적화: later)

**Total time**: 1.5h + 5min = **1h 35min** (efficient)

---

## Part 5: Future Content Strategy Work (Later)

### Tier 2: Evergreen Content (Week 3-4)

**When**: After new prompts proven effective

**Tasks**:
1. Add evergreen keywords to queue
   - EN: "how to calculate national pension korea"
   - KO: "국민연금 수령액 계산 방법"
   - JA: "ギター初心者 アンプモデラー おすすめ"

2. Generate 5-10 evergreen posts
3. Monitor traffic patterns (expect: steady vs spike)

**Agent**: CTO (keyword addition) + Automation (generation)
**Parallel**: N/A (automated)

---

### Tier 3: Internal Linking (Month 2)

**When**: After 50+ posts

**Tasks**:
1. Analyze related posts (category, tags)
2. Add "관련 글" section to popular posts
3. Create linking strategy (3-5 links per post)

**Agent**: CTO (script to suggest links) + Master (manual review)
**Parallel**: Possible (CTO script, Designer template update)

---

## Part 6: Success Metrics

### Week 1 (After System Prompt Fix)
- [ ] New posts use data sources (EN) - target: 80%+
- [ ] Key info in first 2 paragraphs (KO) - target: 90%+
- [ ] 結論ファースト structure (JA) - target: 80%+
- [ ] Average "私" usage (JA) - target: < 5 per post

### Month 1
- [ ] Average page duration: 1min 30sec → 2min+ (target)
- [ ] Bounce rate: 65% → <60% (target)
- [ ] AdSense CTR improvement: 5-10% increase

### Month 3
- [ ] Evergreen traffic: 20% → 40% of total
- [ ] Page views per session: 1.2 → 1.8 (internal linking)
- [ ] Organic search: 40% → 60% of traffic

---

## Part 7: Risk Mitigation

### Risk 1: New Prompts Too Restrictive

**Symptom**: Claude generates "robotic" content, lacks personality

**Mitigation**:
- Test 3-5 posts before automation
- Balance "data sources" with natural flow
- Iterate on prompt wording if needed

**Fallback**: Revert to old prompts, refine gradually

### Risk 2: JA Prompts Culturally Off

**Symptom**: Japanese readers report content feels "translated" or unnatural

**Mitigation**:
- Test JA posts with native speaker review (if available)
- Monitor bounce rate for JA posts specifically
- A/B test 結論ファースト vs traditional structure

**Fallback**: Reduce 結論ファースト strictness, focus on "私" reduction first

### Risk 3: KO Readers Want More Depth, Not Less Intro

**Symptom**: Comments like "너무 짧다", "설명이 부족하다"

**Mitigation**:
- Front-load key facts, but keep depth in middle sections
- Don't reduce total word count, just reorganize
- Monitor engagement metrics (comments, shares)

**Fallback**: Adjust "정보 우선" to mean "organize better" not "write less"

---

## Part 8: Next Session Action Items

**Immediate** (This session or next):
1. ✅ Install pre-commit hook (5min)
2. ⏳ Delegate to CTO: System Prompt improvements (1.5h)
3. ⏳ Master review & commit (30min)

**This Week**:
4. Monitor tomorrow's 18:00 automation (3 posts with new prompts)
5. Analyze new posts against old posts (qualitative review)
6. Collect metrics baseline (page duration, bounce rate)

**Next 2 Weeks**:
7. Iterate on prompts if needed (based on automation results)
8. Plan evergreen keyword addition
9. Start tracking SEO metrics (GSC)

**Month 2-3**:
10. Implement internal linking
11. Add evergreen content stream (parallel with trending)
12. A/B test CTA improvements

---

## Conclusion

**This session's focus**: System Prompt improvements (EN/KO/JA)

**Why this first**:
- Affects all future content (high leverage)
- Quick to implement (1.5h)
- Easy to test (tomorrow's automation)
- Low risk (can revert if issues)

**Not doing now** (lower priority):
- 기존 글 최적화 (can do later if metrics show need)
- Evergreen keywords (need new prompts proven first)
- Internal linking (need more posts first)

**System 4.5 in action**:
- Sequential execution (1 critical task)
- Clear scope (CTO owns scripts/)
- Pre-commit hook enforces boundaries
- Fast iteration (1.5h + test)

**Expected outcome**:
- 30% better native appeal (EN: less "I", KO: faster info, JA: 結論ファースト)
- Measurable in 1 week (tomorrow's automation + monitoring)

---

**Ready to execute?**

**Option 1**: Start now (CTO task: 1.5h)
**Option 2**: Next session (fresh start)
**Option 3**: Modify plan first (what changes?)

---

**Report Created**: 2026-01-22 21:15 KST
**Status**: Ready for user approval
**Next**: Await user decision to proceed
