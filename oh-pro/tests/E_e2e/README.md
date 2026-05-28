# Manual E2E scenarios for oh-pro

These scenarios require a real OpenHands browser session and the user's LLM/API key. Devin prepared inputs and check scripts but does not run them automatically.

## Setup

```bash
cd ~/oh-pro
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY or provider-specific key
docker compose up -d
open http://localhost:3000
```

For each scenario:

1. Create or open the target workspace.
2. Copy the corresponding `E*_input.md` into OpenHands.
3. Let OpenHands finish.
4. Run `./tests/E_e2e/E*_check.sh <workspace>` on the host.

## Scenarios

- E1 — New ML service from scratch: verifies ML baseline, seed, tests, and service files.
- E2 — Legacy bugfix: verifies SWD claim/verify, regression test, and fixed behavior.
- E3 — Long session with 15 tasks: verifies memory/worklog compaction and context continuity.
- E4 — Researcher + PM: verifies explicit researcher activation and product acceptance criteria.
- E5 — Survive OpenHands upgrade: verifies wrapper image arg override and skills/hooks still mounted.
