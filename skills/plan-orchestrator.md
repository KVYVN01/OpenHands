---
name: plan-orchestrator
description: Усиливает встроенный planning agent OpenHands. Заставляет составлять структурированный PLAN.md перед нетривиальными задачами, привязывать каждый шаг к skill'у, фиксировать риски и rollback-план.
type: always
priority: 92
triggers: []
read_only: false
---

# Plan Orchestrator

Этот skill работает в паре с встроенным OH planning agent и `Task List` UI (1.5+).

## Когда план обязателен
- задача требует > 3 файлов изменений;
- задача затрагивает несколько модулей;
- задача требует исследования перед кодом;
- задача связана с миграцией, рефакторингом, security-критичным кодом.

## Когда план не нужен
- одна правка в одном файле, очевидная;
- ответ на вопрос без изменений в коде;
- работа в режиме researcher (там свой формат).

## Формат PLAN.md (создаётся/обновляется в корне проекта)

```markdown
# Plan: 

**Created:** 
**Status:** draft | active | done | abandoned
**Owner-skill:** 

## Goal


## Acceptance criteria
- [ ] 
- [ ] 

## Steps
1. **** — skill: `` — risk: low/med/high
   - input: 
   - output: 
   - rollback: 
2. ...

## Risks
-  → митигация 

## Out of scope
- 

## Decisions log
- : 
```

## Правила работы

1. **Перед любой задачей категории "план обязателен"** — создай/обнови PLAN.md, покажи пользователю, дождись apply/правок.
2. **Привязывай каждый шаг к конкретному skill** (architect, ml-engineer, refactor-surgeon, etc). Если skill не подходит — отметь "manual" и опиши действия явно.
3. **Risk-аннотация:** high-risk шаги требуют явного подтверждения перед началом.
4. **Rollback** обязателен для каждого шага меняющего файлы. "Cannot rollback" — отдельная пометка.
5. **Decisions log append-only.** Если решение меняется — новая запись, не переписывание старой.
6. **Synchroniзация с Task List UI:** каждый Step в PLAN.md соответствует одной задаче в Task List.
7. **При завершении** перенеси PLAN.md в `plans/done/<date>-<name>.md` для истории.

## Анти-паттерны (не делать)

- План на 1-2 пункта типа "сделай X, проверь" — лучше без плана.
- 20+ шагов в одном плане — разбей на под-планы.
- Шаги без acceptance criteria — невозможно проверить done.
- Игнорировать risk-аннотации — high-risk без подтверждения = stop.
