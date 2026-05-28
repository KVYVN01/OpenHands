---
name: sre-debugger
description: Operational debugging for reliability, healthchecks, logs, and incidents.
type: domain
priority: 79
triggers: ["incident", "slo", "latency", "healthcheck", "outage"]
read_only: false
---

# SRE Debugger

## Incident loop
1. Scope impact.
2. Check health, logs, recent changes.
3. Mitigate safely.
4. Verify recovery.
5. Record post-incident action items.

Avoid speculative root cause without evidence.
