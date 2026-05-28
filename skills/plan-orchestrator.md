---
name: plan-orchestrator
description: Amplifies the built-in OpenHands planning agent. Enforces a structured PLAN.md before non-trivial tasks, binds each step to a skill, captures risks and rollback plans. Syncs with Task List UI.
type: process
priority: 92
triggers: ["plan", "multi-file", "multi-module", "migration", "refactor", "architecture"]
read_only: false
---

# Plan Orchestrator

Works in tandem with the built-in OpenHands planning agent and `Task List` UI.

## When a plan is required
- Task touches > 3 files;
- Task spans multiple modules;
- Task requires research before coding;
- Task involves migration, refactoring, or security-critical code.

## When a plan is NOT needed
- Single-file, obvious fix;
- Answering a question with no code changes;
- Working in researcher mode (has its own format).

## PLAN.md format (created/updated in project root)

```markdown
# Plan: <short title>

**Created:** <ISO date>
**Status:** draft | active | done | abandoned
**Owner-skill:** <skill name>

## Goal
<1-2 sentences>

## Acceptance criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Steps
1. **<step name>** — skill: `<skill>` — risk: low/med/high
   - input: <what this step needs>
   - output: <what this step produces>
   - rollback: <how to undo>
2. ...

## Risks
- <risk description> → mitigation: <how to handle>

## Out of scope
- <explicitly excluded>

## Decisions log
- <timestamp>: <decision>
```

## Operating rules

1. **Before any "plan required" task** — create/update PLAN.md, show to user, wait for approval.
2. **Bind every step to a concrete skill** (architect, ml-engineer, refactor-surgeon, etc.). If no skill fits, mark as "manual" and describe actions explicitly.
3. **Risk annotation:** high-risk steps require explicit confirmation before execution.
4. **Rollback** is mandatory for every file-modifying step. "Cannot rollback" is a valid annotation — state it explicitly.
5. **Decisions log is append-only.** If a decision changes — new entry, never overwrite old.
6. **Sync with Task List UI:** each Step in PLAN.md maps to one task in Task List.
7. **On completion** move PLAN.md to `plans/done/<date>-<name>.md` for history.

## Anti-patterns (avoid)

- 1-2 line plan like "do X, check Y" — skip the plan.
- 20+ steps in one plan — split into sub-plans.
- Steps without acceptance criteria — impossible to verify done.
- Ignoring risk annotations — high-risk without confirmation = stop.
