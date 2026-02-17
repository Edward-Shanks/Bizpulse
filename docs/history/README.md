# Documentation History & Archive

## Purpose

This folder contains **temporal documentation** - files that document specific change events, migrations, or decision points rather than ongoing system reference.

Think of these as:
- Git commit messages in long form
- Pull request descriptions
- Migration reports
- Audit trails
- Decision logs

---

## Files in This Archive

### 2026-02-10: RBAC Documentation Alignment

**Context**: ChatGPT reviewed RBAC documentation and found inconsistencies between `RBAC_ARCHITECTURE_AND_FLOW.md` (conceptual, pilot-era patterns) and `RBAC_PRODUCTION_HARDENED_VERSION.md` (production-ready, security-hardened).

**Files**:

1. **`2026-02-10_RBAC_ALIGNMENT_REPORT.md`** (354 lines)
   - Detailed technical changelog
   - 8 issues identified and fixed
   - Before/after code examples with line numbers
   - Reasoning for each change
   - Production implementation checklist

2. **`2026-02-10_CHATGPT_FEEDBACK_LOG.txt`** (219 lines)
   - Visual summary of the same alignment
   - Easier to scan, less technical detail
   - Same 8 issues, ASCII art formatting

**Outcome**: Both RBAC files now aligned and production-ready. No architectural changes, just documentation consistency.

**Key Changes**:
- JWT: Now contains only `user_id + perm_version` (not full permissions)
- Permissions: Fetched from MongoDB on each request (single source of truth)
- AI SQL: Intent-based approach (LLM generates intent, backend builds SQL)
- RBAC Enforcement: Backend enforces via WHERE clauses (not ClickHouse)

---

## When to Add Files Here

Add files to `/docs/history/` when they:

✅ Document a **specific event** (migration, refactor, alignment)
✅ Have a **date context** (this happened on X date)
✅ Are **no longer needed for daily reference**
✅ Serve as **audit trail** (for compliance, reviews, onboarding)
✅ Answer "what changed and why?" not "how does it work?"

**Examples**:
- Migration reports (`2026-03-15_MONGO_TO_CLICKHOUSE_MIGRATION.md`)
- Architecture decision records (`2026-04-01_ADR_CACHING_STRATEGY.md`)
- Security reviews (`2026-05-10_PENETRATION_TEST_FINDINGS.md`)
- Performance optimization logs (`2026-06-01_QUERY_OPTIMIZATION_REPORT.md`)

---

## When NOT to Archive

Keep in root/main docs when they:

❌ Are **living documents** (constantly referenced, updated)
❌ Answer "how to" questions (setup guides, tutorials)
❌ Define **current state** (architecture, RBAC rules, API docs)
❌ Are **operational** (runbooks, troubleshooting)

**Examples**:
- `START_HERE.md` (always current entry point)
- `COMPLETE_SETUP_CHECKLIST.md` (active guide)
- `RBAC_PRODUCTION_HARDENED_VERSION.md` (security authority)
- `ARCHITECTURE_FINAL_NO_REWRITES.md` (current decisions)

---

## Naming Convention

Use this format for archived files:

```
YYYY-MM-DD_DESCRIPTIVE_NAME.md
YYYY-MM-DD_DESCRIPTIVE_NAME.txt
```

**Examples**:
- `2026-02-10_RBAC_ALIGNMENT_REPORT.md` ✅
- `2026-03-15_CLICKHOUSE_MIGRATION_COMPLETE.md` ✅
- `2026-04-01_ADR_001_CACHING_STRATEGY.md` ✅
- `rbac_changes.md` ❌ (no date, too vague)
- `migration.txt` ❌ (no date, what migration?)

---

## Why This Matters

**Without `/docs/history/`:**
- ❌ Cluttered root folder
- ❌ "Which doc is current?" confusion
- ❌ Engineers read outdated files by accident
- ❌ Hard to find living docs among archived ones

**With `/docs/history/`:**
- ✅ Clean, focused root documentation
- ✅ Clear "current vs historical" separation
- ✅ Easy onboarding (read active docs first)
- ✅ Audit trail preserved but not in the way

---

## How This Helps Onboarding

**New engineer joins:**

1. Reads `START_HERE.md` (current entry point)
2. Follows `COMPLETE_SETUP_CHECKLIST.md` (current process)
3. Reviews `RBAC_PRODUCTION_HARDENED_VERSION.md` (current security)
4. **Optional**: Browses `/docs/history/` to understand evolution

**Result**: Learns **current system** fast, without being confused by **past changes**.

---

## Best Practices (Industry Standard)

This pattern is used by:
- **Stripe**: `/docs/history/` and `/docs/adr/` (Architecture Decision Records)
- **Shopify**: `/docs/decisions/` for dated decisions
- **Airbnb**: `/docs/postmortems/` for incident reports
- **GitHub**: `/docs/rfcs/` for archived RFCs

**Common across all**:
1. Date-prefix for chronological sorting
2. Clear separation from current docs
3. Preserved for audit/context
4. Not deleted (unlike temp files)

---

## When to Review This Folder

**Quarterly Review** (every 3 months):
- Verify files still have value
- Move extremely outdated files (> 2 years) to deeper archive if needed
- Update this README if patterns change

**When Onboarding New Engineers**:
- Show them this folder as "context, not required reading"
- Use for "why did we decide X?" questions

**During Audits/Compliance**:
- Provide as evidence of decision-making process
- Show evolution of security practices

---

## Summary

| Type | Location | Purpose |
|------|----------|---------|
| **Current Docs** | `/` (root) | How system works NOW |
| **Historical Docs** | `/docs/history/` | How we GOT here |
| **Implementation Guides** | `/brain/` | Deep dives & roadmaps |

**This folder = Audit trail, not daily reference.**

---

**Last Updated**: February 10, 2026  
**Maintained By**: Development Team  
**Review Cadence**: Quarterly (every 3 months)
