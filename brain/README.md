# BizPulse Knowledge Base (Brain)

## Purpose
This folder contains critical project documentation, architecture decisions, and technical knowledge that should **NEVER be deleted** during cleanup operations.

## Contents

### System Architecture & Flow
- **MONGODB_CLICKHOUSE_COMPLETE_SETUP_REF.md**: Points to `backend/MONGODB_CLICKHOUSE_SETUP_UNDERSTANDING_AND_ARCHITECTURE.md` — full understanding and architecture for MongoDB + ClickHouse complete setup (from ChatGPT discussion; aligned with FastAPI/Python codebase).
- **MONGODB_CLICKHOUSE_AI_IMPLEMENTATION.md**: Implementation summary for MongoDB + ClickHouse + AI chatbot system with permission-aware caching, RBAC enforcement, and intent-based query generation.
- **COMPLETE_SYSTEM_FLOW_AND_DATABASE_RECOMMENDATIONS.md**: Comprehensive documentation of:
  - Complete dashboard data flow
  - AI Assistant chatbot architecture (6-step process)
  - Local LLM setup (Qwen:32b on Mac Studio)
  - RBAC implementation requirements
  - Database migration recommendations (ClickHouse analysis)
  - Performance benchmarks and optimization strategies

## Usage

### When to Add Files
Add documents to this folder when they contain:
- System architecture decisions
- Critical implementation details
- Performance benchmarks
- Migration strategies
- RBAC and security implementations
- API documentation
- Database schema and relationships

### When to Reference
Refer to these documents when:
- Explaining system architecture to new team members
- Making architectural decisions
- Implementing new features that touch core systems
- Troubleshooting performance issues
- Planning migrations or major changes

## Important Rules

### ⚠️ NEVER DELETE THIS FOLDER
This folder should be excluded from all cleanup scripts and operations. It contains critical institutional knowledge.

### 📝 Keep Documents Updated
When making significant system changes:
1. Update the relevant document in this folder
2. Document the reason for the change
3. Include before/after comparisons
4. Note any breaking changes

### 🔍 Search Before Creating
Before creating new documentation:
1. Check if a related document already exists
2. Update existing documents rather than creating duplicates
3. Cross-reference related documents

## Document Index

### ⭐ Primary Documents (Start Here)

| Document | Version | Last Updated | Purpose |
|----------|---------|-------------|---------|
| **FINAL_ENHANCED_ARCHITECTURE_V2.md** | **v2.0** | **2026-02-08** | **Production-ready system architecture** |
| **PHASE1_IMPLEMENTATION_README.md** | **v1.0** | **2026-02-10** | **12-week Phase 1 implementation roadmap** |
| **CLICKHOUSE_DATABASE_SETUP_COMPLETE.md** | **v1.0** | **2026-02-10** | **Complete ClickHouse setup guide** |
| **CLICKHOUSE_SETUP_SUMMARY.md** | **v1.0** | **2026-02-10** | **Executive summary of ClickHouse setup** |

### 📚 Supporting Documents

| Document | Version | Last Updated | Purpose |
|----------|---------|-------------|---------|
| MONGODB_VS_CLICKHOUSE_DECISION.md | v1.0 | 2026-02-10 | Database recommendation & justification |
| RBAC_QUICK_REFERENCE.md | v1.0 | 2026-02-08 | Quick implementation guide for RBAC |
| LOCAL_LLM_INFRASTRUCTURE.md | v1.0 | 2026-02-08 | Local LLM setup (Qwen:32b on Mac Studio) |
| QUICK_DECISION_GUIDE.md | v1.0 | 2026-02-08 | Quick comparison: what to follow and why |

### 🔐 RBAC & Security Documents (Feb 10, 2026)

| Document | Version | Last Updated | Purpose |
|----------|---------|-------------|---------|
| **RBAC_ARCHITECTURE_AND_FLOW.md** | **v1.1** | **2026-02-10** | **Complete RBAC flow (aligned & production-ready)** |
| **RBAC_PRODUCTION_HARDENED_VERSION.md** | **v1.0** | **2026-02-10** | **Security authority (ChatGPT validated)** |
| **CHATGPT_REVIEW_VERDICT.txt** | **v1.0** | **2026-02-10** | **ChatGPT's original review** |

**Archived**: Alignment changelog files moved to `/docs/history/` (audit trail)

### 📖 Background Documents

| Document | Version | Last Updated | Purpose |
|----------|---------|-------------|---------|
| COMPLETE_SYSTEM_FLOW_AND_DATABASE_RECOMMENDATIONS.md | v1.0 | 2026-02-08 | Original comprehensive design |
| CHATGPT_REVIEW_AND_ENHANCED_ARCHITECTURE.md | v2.0 | 2026-02-08 | ChatGPT's review analysis and improvements |

### 🎯 Quick Navigation

**For Architecture**: `FINAL_ENHANCED_ARCHITECTURE_V2.md`  
**For Implementation**: `PHASE1_IMPLEMENTATION_README.md`  
**For ClickHouse Setup**: `CLICKHOUSE_DATABASE_SETUP_COMPLETE.md`  
**For Executive Summary**: `CLICKHOUSE_SETUP_SUMMARY.md`  
**For RBAC**: `RBAC_QUICK_REFERENCE.md`

## Maintenance

### Monthly Review
- Review and update documents for accuracy
- Archive outdated information
- Add new architectural decisions
- Update performance benchmarks

### Version Control
- All documents are version controlled in Git
- Use meaningful commit messages when updating
- Tag major architectural changes

---

**Maintained by**: Development Team  
**Last Updated**: February 10, 2026

---

## 🚀 Latest Updates (Feb 10, 2026)

### Phase 1 Ready for Implementation
✅ **All files created** for ClickHouse migration and RBAC setup  
✅ **Architecture confirmed** by ChatGPT review - production-ready  
✅ **No rewrites needed** for Phase 2 - only operational controls

**Status**: Ready to deploy Phase 1
