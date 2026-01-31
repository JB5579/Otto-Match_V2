# Documentation Review Process - Otto.AI

**Created:** 2026-01-02
**Purpose:** Establish monthly review schedule and ongoing maintenance workflow to prevent documentation drift
**Owner:** Development Team
**Review Cadence:** Monthly (1st of each month)

---

## Table of Contents

1. [Overview](#overview)
2. [Monthly Review Schedule](#monthly-review-schedule)
3. [Verification Workflow](#verification-workflow)
4. [Update Triggers](#update-triggers)
5. [Responsibilities](#responsibilities)
6. [Review Checklist](#review-checklist)
7. [Escalation Process](#escalation-process)

---

## Overview

### Purpose

This process ensures Otto.AI documentation remains accurate, synchronized with actual implementation, and useful for AI-assisted development. The 2026-01-02 documentation cleanup revealed significant drift between documented claims and actual code implementation, requiring a systematic review process.

### Core Principles

1. **Evidence-Based Documentation** - All implementation claims must have verifiable evidence
2. **Single Source of Truth** - `sprint-status.yaml` is the authoritative status source
3. **Clear Status Markers** - Every feature must have ✅ IMPLEMENTED, ⚠️ PARTIAL, 📋 PLANNED, or ❌ DEPRECATED
4. **Verification Dates** - All docs must show "Last Verified: YYYY-MM-DD"
5. **No Speculation** - Avoid specific percentages, performance claims, or production readiness without evidence

### Success Metrics

- **Zero contradictions** between sprint-status.yaml, CLAUDE.md, architecture.md
- **100% of docs** have verification dates within 30 days
- **Zero unverified claims** (specific percentages, performance claims)
- **<10 minute** time for new developer to understand project status

---

## Monthly Review Schedule

### Review Timeline

**1st of Each Month:**
- **Day 1-2:** Verification commands and evidence collection
- **Day 3-5:** Documentation updates and status synchronization
- **Day 6-7:** Archive old reports and cleanup

**Participants:**
- Tech Lead (Overall coordination)
- Development Team (Code verification)
- Documentation Owner (Content updates)

### Calendar Integration

**2026 Review Schedule:**
- February 1, 2026 - First monthly review
- March 1, 2026
- April 1, 2026
- May 1, 2026
- June 1, 2026
- July 1, 2026
- August 1, 2026
- September 1, 2026
- October 1, 2026
- November 1, 2026
- December 1, 2026

**Calendar Reminder:** Set recurring monthly calendar event with:
- Title: "Otto.AI Documentation Review"
- Date: 1st of each month
- Duration: 2 hours
- Attendees: Tech Lead, Dev Team Lead, Documentation Owner

---

## Verification Workflow

### Step 1: Run Verification Commands

**Code Existence Verification:**
```bash
# Verify Epic 1 (Search) implementation
ls -la /mnt/d/Otto_AI_v2/src/search/*.py
wc -l /mnt/d/Otto_AI_v2/src/search/*.py

# Verify Epic 2 (Conversation) implementation
ls -la /mnt/d/Otto_AI_v2/src/conversation/*.py
ls -la /mnt/d/Otto_AI_v2/src/intelligence/*.py

# Verify Epic 3 (Frontend) - should return 0
find /mnt/d/Otto_AI_v2 -name "*.tsx" -o -name "*.jsx" | wc -l

# Verify Epic 5 (PDF Pipeline)
ls -la /mnt/d/Otto_AI_v2/src/services/pdf_ingestion_service.py
ls -la /mnt/d/Otto_AI_v2/src/semantic/vehicle_processing_service.py
```

**Test Status Verification:**
```bash
# Run test suite to verify implementation claims
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest --tb=short

# Check test coverage
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest --cov=src --cov-report=term
```

**Integration Verification:**
```bash
# Check what's actually integrated into main.py
grep -r "import.*search" /mnt/d/Otto_AI_v2/main.py
grep -r "import.*conversation" /mnt/d/Otto_AI_v2/main.py
```

**Output Storage:**
Create monthly evidence file:
```
docs/verification-evidence-YYYY-MM-DD.md
```

### Step 2: Compare Against Documentation

**Files to Compare:**
1. `docs/sprint-artifacts/sprint-status.yaml` (SINGLE SOURCE OF TRUTH)
2. `CLAUDE.md` - "Current Development Focus" section
3. `docs/architecture.md` - "Implemented Features Summary"
4. `docs/prd.md` - "Implementation Status Summary"

**Comparison Checklist:**
- [ ] Story statuses in sprint-status.yaml match actual code
- [ ] CLAUDE.md completion percentages match verification evidence
- [ ] architecture.md status markers (✅/⚠️/📋) accurate
- [ ] prd.md FR implementation counts match sprint-status.yaml
- [ ] No contradictions between documents
- [ ] All "Last Verified" dates updated to current month

### Step 3: Update Documentation

**Update Order (Critical):**
1. **First:** Update `sprint-status.yaml` with verified statuses
2. **Second:** Update `CLAUDE.md` to match sprint-status.yaml
3. **Third:** Update `architecture.md` with file path verification
4. **Fourth:** Update `prd.md` FR counts
5. **Last:** Update story files if status changed

**Required Changes Log:**
Create a change summary in monthly verification file:
```markdown
## Documentation Updates - YYYY-MM-DD

### Status Changes
- Epic X: `status_old` → `status_new` (Reason: verification showed...)
- Story X-Y: `status_old` → `status_new` (Reason: ...)

### Corrections Made
- Corrected CLAUDE.md completion percentage from X% to Y%
- Updated architecture.md: Feature Z marked ⚠️ PARTIAL (was ✅ IMPLEMENTED)
- Fixed prd.md FR count: was X, verified Y

### New Implementation Verified
- Story X-Y completed since last review
- Files added: [list]
```

---

## Update Triggers

### Immediate Updates (Same Day)

**Story Status Changes:**
- When story moves: backlog → in-progress
- When story moves: in-progress → done
- When story moves: in-progress → partial
- When story is blocked or reverted

**Update Workflow:**
1. Update `sprint-status.yaml` immediately
2. Add comment with date and reason
3. Update story file header
4. Update CLAUDE.md if epic status changes

**Example:**
```yaml
epic-2:
  status: contexted  # UPDATED 2026-01-15 - Story 2-7 completed
  stories:
    2-7-implement-conversation-history:
      status: done  # COMPLETED 2026-01-15 - All AC met, tests passing
```

### Weekly Updates (Friday EOD)

**Completion Metrics:**
- Update epic completion percentages in CLAUDE.md
- Verify story counts in sprint-status.yaml
- Check for contradictions between docs

**Archive Triggers:**
- Status reports older than 30 days → archive
- Completion reports after retrospective → archive
- Remediation plans after resolution → archive

### Monthly Updates (1st of Month)

See "Monthly Review Schedule" above for full workflow.

---

## Responsibilities

### Tech Lead

**Duties:**
- Coordinate monthly review process
- Run verification commands
- Make final call on contradictions
- Review and approve documentation updates
- Escalate blocking issues

**Time Commitment:** 2-3 hours/month

### Development Team

**Duties:**
- Update story status when completing work
- Provide verification evidence for completed stories
- Review documentation accuracy for their epic areas
- Flag contradictions or inaccuracies

**Time Commitment:** 30 minutes/month

### Documentation Owner

**Duties:**
- Execute documentation updates
- Maintain "Last Verified" dates
- Archive old reports
- Ensure format consistency
- Update verification evidence files

**Time Commitment:** 2-3 hours/month

### Scrum Master (Optional)

**Duties:**
- Facilitate monthly review meeting
- Ensure blockers are addressed
- Track review completion
- Report on documentation health

**Time Commitment:** 1 hour/month

---

## Review Checklist

### Pre-Review (Day 1)

- [ ] Schedule 2-hour review meeting with team
- [ ] Create monthly verification evidence file
- [ ] Run all verification commands
- [ ] Save command outputs to evidence file
- [ ] Identify stories completed since last review
- [ ] Identify contradictions between docs

### Review Meeting (Day 2-3)

**Agenda (2 hours):**

**0:00-0:15 - Setup**
- [ ] Review last month's action items
- [ ] Review verification evidence summary

**0:15-0:45 - Epic-by-Epic Review**
- [ ] Epic 1: Verify implementation status (code checks)
- [ ] Epic 2: Verify implementation status (code checks)
- [ ] Epic 3: Verify implementation status (frontend checks)
- [ ] Epic 4-8: Verify implementation status

**0:45-1:15 - Documentation Updates**
- [ ] Update sprint-status.yaml (FIRST)
- [ ] Update CLAUDE.md completion percentages
- [ ] Update architecture.md status markers
- [ ] Update prd.md FR counts
- [ ] Update story files if needed

**1:15-1:45 - Quality Checks**
- [ ] Verify no contradictions between docs
- [ ] Check all "Last Verified" dates updated
- [ ] Review prohibited claims (percentages, performance)
- [ ] Check for future-dated content

**1:45-2:00 - Wrap-up**
- [ ] Review changes made
- [ ] Assign follow-up actions
- [ ] Schedule next month's review
- [ ] Document any blockers or issues

### Post-Review (Day 4-7)

- [ ] Archive status reports >30 days old
- [ ] Update `docs/archive/ARCHIVE-README.md`
- [ ] Commit documentation updates
- [ ] Send summary email to team
- [ ] Create action items for next month

---

## Escalation Process

### Severity Levels

**Level 1 - Minor (Info):**
- Single doc out of date
- "Last Verified" date >30 days
- Missing verification date

**Action:** Update during next monthly review

**Level 2 - Moderate (Warning):**
- Contradictions between 2+ docs
- Story status mismatch
- Missing status markers
- Unverified percentage claims

**Action:** Update within 1 week

**Level 3 - Critical (Blocker):**
- sprint-status.yaml contradicts actual code
- CLAUDE.md shows wrong epic status
- Major feature claimed but no code exists
- Production readiness claim without evidence

**Action:** Immediate update (same day)

### Escalation Path

**Level 1:**
1. Documentation Owner fixes during monthly review
2. No escalation needed

**Level 2:**
1. Documentation Owner creates issue in tracker
2. Tech Lead reviews within 1 week
3. Team updates docs within 1 week

**Level 3:**
1. Documentation Owner notifies Tech Lead immediately
2. Emergency review meeting scheduled
3. Corrections made same day
4. Incident report created
5. Process improvement identified

### Issue Tracking

**GitHub Issues for Documentation:**
- Label: `documentation`
- Priority: `P0-Critical`, `P1-High`, `P2-Medium`
- Assignee: Documentation Owner
- Milestone: Next monthly review

**Example Issue Template:**
```markdown
## Documentation Inconsistency

**Severity:** Level 2 - Moderate

**Issue:** Epic 3 marked "contexted" in sprint-status.yaml but verification shows 0 .tsx files

**Evidence:**
- `find . -name "*.tsx" | wc -l` returns 0
- sprint-status.yaml line 45: `epic-3: contexted`

**Correction Required:**
- Update sprint-status.yaml: `epic-3: backlog`
- Add comment: "# CORRECTED 2026-01-02 - No frontend code exists"

**Verification:**
- [ ] sprint-status.yaml updated
- [ ] CLAUDE.md updated
- [ ] architecture.md updated
- [ ] Verification date added

**Assigned:** @documentation-owner
**Due Date:** 2026-01-09 (1 week)
```

---

## Appendix A: Quick Reference Commands

### Verification Commands

```bash
# Epic 1 (Search)
ls -la src/search/*.py && wc -l src/search/*.py

# Epic 2 (Conversation)
ls -la src/conversation/*.py src/intelligence/*.py

# Epic 3 (Frontend)
find . -name "*.tsx" -o -name "*.jsx" | wc -l  # Should be 0

# Epic 5 (PDF Pipeline)
ls -la src/services/pdf_ingestion_service.py src/semantic/vehicle_processing_service.py

# Test Status
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest --tb=short

# Coverage
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest --cov=src --cov-report=term
```

### Archive Commands

```bash
# Archive old status reports
mv docs/status-report-OLD.md docs/archive/status-reports/YYYY-MM-DD-status-report.md

# Add archive header (prepend to file)
cat > temp.md << 'EOF'
**ARCHIVED:** 2026-01-02
**Reason:** Superseded by monthly review
**Superseded By:** docs/verification-evidence-2026-01-02.md

---

EOF
cat docs/archive/status-reports/YYYY-MM-DD-status-report.md >> temp.md
mv temp.md docs/archive/status-reports/YYYY-MM-DD-status-report.md
```

---

## Appendix B: File Paths Reference

### Critical Documentation Files (Priority Order)

**Tier 1 - Single Source of Truth:**
1. `/mnt/d/Otto_AI_v2/docs/sprint-artifacts/sprint-status.yaml`

**Tier 2 - Primary Developer Guides:**
2. `/mnt/d/Otto_AI_v2/CLAUDE.md`
3. `/mnt/d/Otto_AI_v2/docs/architecture.md`

**Tier 3 - Requirements Tracking:**
4. `/mnt/d/Otto_AI_v2/docs/prd.md`

**Tier 4 - Story Details:**
5. `/mnt/d/Otto_AI_v2/docs/sprint-artifacts/stories/*.md`

**Tier 5 - Specifications:**
6. `/mnt/d/Otto_AI_v2/docs/ux-design-specification.md`
7. `/mnt/d/Otto_AI_v2/docs/vehicle-ingestion-pipeline.md`
8. `/mnt/d/Otto_AI_v2/docs/rag-strategy-spec.md`
9. `/mnt/d/Otto_AI_v2/docs/test-design-system.md`

### Standards and Process Files

- `/mnt/d/Otto_AI_v2/docs/documentation-standards-checklist.md` (Standards reference)
- `/mnt/d/Otto_AI_v2/docs/documentation-review-process.md` (This file)

### Archive Locations

- `/mnt/d/Otto_AI_v2/docs/archive/status-reports/` - Old status reports
- `/mnt/d/Otto_AI_v2/docs/archive/completion-reports/` - Epic completion reports
- `/mnt/d/Otto_AI_v2/docs/archive/remediation/` - Remediation plans
- `/mnt/d/Otto_AI_v2/docs/archive/obsolete/` - Obsolete/duplicate docs

---

## Version History

| Date | Version | Changes | Author |
| ---- | ------- | ------- | ------ |
| 2026-01-02 | 1.0 | Initial documentation review process | Claude Code (Documentation Cleanup Initiative) |

---

*This process was created during the 2026-01-02 documentation cleanup to prevent future documentation drift and maintain accuracy for AI-assisted development.*
