# OpenHands — анализ модернизации (KVYVN01 fork)

## TL;DR

- **Главный баг со скилами:** UI-список скилов и реально загружаемые в агента скилы берутся из **разных источников** и не пересекаются.
  - `/api/v1/skills/search` (app-server) читает с **хоста** `OpenHands/skills/` и `~/.openhands/microagents/`.
  - В диалог агента скилы инжектятся **agent-server'ом**, который читает изнутри песочницы `~/.openhands/skills/`, `~/.openhands/microagents/` и клонит публичный репо `OpenHands/extensions` с GitHub.
  - Локальные `OpenHands/skills/*.md` и пользовательские `~/.openhands/microagents/*` на хосте **никак не попадают** в agent-server (в Docker-песочнице это другой контейнер; в process-песочнице home совпадает, но `OpenHands/skills/` всё равно игнорируется).
  - Фильтр `disabled_skills` срабатывает по имени уже после ответа agent-server'а — поэтому тоггл в UI ни на что не влияет, если имена не пересеклись.
- **Страница авторизации** в OSS-режиме фактически dead-code: `useIsAuthed` сразу возвращает `true`, `LoginPage` редиректит на `/`. Можно безболезненно удалить роут целиком — UX от этого выиграет.
- **API V1** в целом рабочий, но есть наследие V0 (`openhands/server/listen.py` deprecated re-export, `DefaultUserAuth` помечен Legacy-V0). После релиза V1 их планируется вычистить.

---

## 1. Слои и взаимосвязи

### 1.1 Backend (`openhands/`)

| Модуль | Назначение | Статус |
|---|---|---|
| `openhands/app_server/` | V1 FastAPI app, монтируется `/api/v1/*` | Активная разработка |
| `openhands/server/listen.py` | Legacy V0, теперь просто `from openhands.app_server.app import app` | Deprecated |
| `openhands/agent_server` (внешний pip-пакет `openhands-agent-server==1.23.1`) | Запускается внутри песочницы, обслуживает разговоры + скилы | Внешняя зависимость |
| `openhands/sdk` (внешний `openhands-sdk==1.23.1`) | Агентское ядро, типы Skill/Agent/Conversation | Внешняя зависимость |
| `enterprise/` | SaaS-расширение под лицензией Polyform | Не нужно для OSS |

### 1.2 Frontend (`frontend/`)

- React + react-router (file-based routing в `frontend/src/routes.ts`)
- TanStack Query, vitest
- API-слой в `frontend/src/api/*` обёрнут в TanStack-хуки `frontend/src/hooks/query/*`

### 1.3 Скилы и микроагенты

```
host:
  OpenHands/skills/          → читает /api/v1/skills/search (UI)
  ~/.openhands/microagents/  → читает /api/v1/skills/search (UI)
  ~/.openhands/skills/       → НЕ читается app-server'ом
  .openhands/microagents/    → читается agent-server'ом изнутри workspace
  .openhands/skills/         → читается agent-server'ом изнутри workspace

sandbox (Docker или process):
  ~/.openhands/skills/       → читает agent-server в контейнере
  ~/.openhands/microagents/  → читает agent-server в контейнере
  <workspace>/.openhands/skills    → читает agent-server (workspace монтируется)

external:
  github.com/OpenHands/extensions  → клонится agent-server'ом как "public skills"
```

Двойная архитектура (app-server отдельно показывает скилы, agent-server отдельно их применяет) — причина разрыва.

### 1.4 API роуты V1 (`/api/v1`)

Регистрируется в `openhands/app_server/v1_router.py:23-37`:
- `/events`, `/conversations`, `/pending-messages`
- `/sandboxes`, `/sandbox-specs`
- `/settings`, `/secrets`, `/users`, `/skills`
- `/webhooks`, `/web-client`, `/git`, `/config`

API-документация автогенерируется FastAPI → `/docs` и `/openapi.json`.

### 1.5 Аутентификация

- Дефолтный `DefaultUserAuth` (Legacy-V0, но всё ещё используется): `user_id = None`, `email = None`, мульти-тенантности нет.
- В OSS-режиме (`AppMode.OPENHANDS`, env: дефолт) — авторизация фактически не работает и не требуется.
- Зависимость `get_dependencies()` подключает `X-Session-API-Key` header только если задан env `SESSION_API_KEY`, иначе — никакой защиты.

---

## 2. Найденные проблемы и предлагаемые улучшения

### 2.1 [P0] Скилы — UI ≠ агент

**Что происходит:**
- Пользователь видит в `/settings/skills` список скилов из `OpenHands/skills/` и `~/.openhands/microagents/`.
- Создаёт свой `~/.openhands/microagents/my-skill.md` — он появляется в UI.
- Открывает чат — агент его не видит, потому что agent-server в Docker'е читает другой `~/.openhands/`.
- Даже выключив скил тогглом, агент может его всё равно "выполнить", т.к. в его контексте лежит `marketplace_github` из `OpenHands/extensions`, а в UI был просто `github` из `skills/`.

**Где в коде:**
- UI-источник: <ref_snippet file="/home/ubuntu/repos/OpenHands/openhands/app_server/user/skills_router.py" lines="14-16" />
- Источник в агента: <ref_snippet file="/home/ubuntu/repos/OpenHands/openhands/app_server/app_conversation/skill_loader.py" lines="264-303" />
- Фильтрация по имени: <ref_snippet file="/home/ubuntu/repos/OpenHands/openhands/app_server/app_conversation/app_conversation_service_base.py" lines="235-243" />

**Варианты фикса (от лёгкого к радикальному):**

1. **(Рекомендую) Host-side skills bridge.** Перед отправкой `StartConversationRequest` к agent-server'у, app-server подгружает локальные `OpenHands/skills/*.md` и `~/.openhands/microagents/*.md` (теми же путями, что и `/api/v1/skills/search`), парсит их в `Skill` и **дополняет** результат `load_skills_from_agent_server`. Имена/фильтрация теперь совпадают с UI.
   - Преимущество: минимально инвазивно, локальные скилы "работают сразу после инсталляции".
   - Недостаток: дублирование с agent-server'ом для process-режима (но при merge by name это safe — последний выигрывает).

2. **Mount/copy local skills в sandbox.** Для Docker-runtime — добавить bind-mount `~/.openhands/microagents/` (read-only) при создании sandbox. Локальный `OpenHands/skills/` тоже можно копировать в `~/.openhands/skills/` внутрь контейнера.
   - Преимущество: чистая sandbox-архитектура.
   - Недостаток: усложняет sandbox-конфигурацию, не помогает remote runtime.

3. **Унификация endpoint'а.** `/api/v1/skills/search` начинает делегировать в agent-server по тем же путям, что и `_load_skills_onto_request`. Тогда UI и агент точно видят одно и то же.
   - Преимущество: концептуально правильно.
   - Недостаток: требует уже стартанутого sandbox'а для отображения списка → плохой UX (страница долго грузится).

**Дополнительно:** добавить в `/api/v1/skills/search` чтение `~/.openhands/skills/` (V1-имя), сейчас читается только V0-имя `microagents/`. См. <ref_snippet file="/home/ubuntu/repos/OpenHands/openhands/app_server/user/skills_router.py" lines="16-16" />.

### 2.2 [P1] Страница авторизации

В OSS-режиме `/login` — мёртвый код:
- `LoginPage` в самом начале редиректит на `/` если `app_mode === "oss"` (`frontend/src/routes/login.tsx:52-56`).
- `useIsAuthed` сразу возвращает `true` для oss (`frontend/src/api/auth-service/auth-service.api.ts:17`).
- `root-layout` редиректит на `/login` только если `app_mode === "saas"` (`frontend/src/routes/root-layout.tsx:213`).

**Предлагается удалить:**
- роут `login` из `frontend/src/routes.ts`,
- `frontend/src/routes/login.tsx`,
- редирект-логику + `useAutoLogin`/`useAuthCallback` хуки в root-layout (или хотя бы перестать вызывать),
- роут `onboarding` если он тоже SaaS-only (по коду — да, `clientLoader` редиректит на `/` если не SaaS).

Сохранить хуки/компоненты, которые используются enterprise-сборкой, чтобы не сломать SaaS.

### 2.3 [P1] Готовность "из коробки"

Проблемы первого запуска:
- `make build` тянет много зависимостей; на свежем хосте без `npm`/`poetry` нужного minor — упадёт.
- `.openhands/setup.sh` не запускается app-server'ом локально; он исполняется agent-server'ом внутри песочницы.
- `config.template.toml` есть, но пользователь должен сам скопировать его в `config.toml` и заполнить ключи. UI Settings — единственный поддерживаемый путь в V1, и без LLM ключа разговор не стартанёт.

**Предложения:**
- В README прописать "после `make build` запускайте `make run`, открывайте UI и вводите ключ в Settings → Models" (фактически уже есть в Development.md, но плохо видно из README).
- Скрипт `make setup-config` для CLI-сценария.
- Локальные скилы (см. 2.1) должны работать сразу без дополнительных действий — это нынче не так.

### 2.4 [P2] Тестируемость и API

- Юнит-тесты `tests/unit/app_server/test_skills_router.py` отсутствует, хотя сам endpoint есть. Стоит добавить (как минимум — что глобальные/пользовательские скилы корректно листаются и пагинируются).
- `tests/unit/app_server/test_skill_loader.py` — есть, но проверяет HTTP-склейку, не конец-в-конец.
- API V1 не имеет внешнего health-роута помимо `/health` (`status_router`). OK, но стоит добавить `/api/v1/health` для симметрии.
- OpenAPI: видны `X-Session-API-Key` и `X-Access-Token` хедеры в SaaS режиме, но в OSS их нет — что верно. Документация автогенерируется FastAPI'ем.

### 2.5 [P2] Legacy-V0 cleanup

В коде явно помечены к удалению (срок: 1 апреля 2026):
- `openhands/server/listen.py` (re-export)
- `openhands/app_server/user_auth/default_user_auth.py`, `user_auth.py`
- ряд старых модулей в `openhands/app_server/integrations/` имеют пометки

После 2.2 (удаление login) логично заодно вычистить и эти модули — но это отдельная задача.

### 2.6 [P3] Frontend code-quality

- `route-layout.tsx` смешивает много логики: auth-redirect, consent-form, invitation-modal, language-switch. Разделить по отдельным компонентам/хукам.
- `useAutoLogin` имеет тяжёлый список зависимостей (`useEffect`) — после удаления login можно выкинуть весь хук.
- `useIsAuthed` запрашивает `/api/authenticate` (V0-endpoint!), а не `/api/v1/...`. Проверить, что есть совместимость в `app_server`. (См. <ref_snippet file="/home/ubuntu/repos/OpenHands/frontend/src/api/auth-service/auth-service.api.ts" lines="14-22" />)

---

## 3. План фикса (PR в этой ветке)

1. **Удалить страницу авторизации** (P1, безопасно для OSS):
   - выпилить роут `/login` в `frontend/src/routes.ts`,
   - удалить `frontend/src/routes/login.tsx`,
   - удалить редирект на `/login` в `root-layout.tsx`,
   - удалить `useAutoLogin` вызов и его импорт.
2. **Host-side skills bridge** (P0):
   - в `_load_skills_and_update_agent` в `app_conversation_service_base.py` подгружать локальные скилы (`OpenHands/skills/`, `~/.openhands/skills/`, `~/.openhands/microagents/`) и **объединять** их с теми, что вернул agent-server.
   - добавить `~/.openhands/skills/` в `/api/v1/skills/search` (V1-имя),
   - добавить юнит-тесты на оба endpoint'а.
3. **Сообщить пользователю** про preview-URL'ы / способ проверки.

Подтвердите план — стартую внедрение в этой же ветке и собираю PR.
