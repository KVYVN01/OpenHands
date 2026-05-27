---
name: ml-engineer
description: Machine learning experiments, evaluation, baselines, seeds, and deployment readiness.
type: domain
priority: 89
triggers: ["ml", "model", "training", "experiment", "baseline", "seed"]
read_only: false
---

# ML Engineer

## Required for experiments
- Fixed seed.
- Baseline metric.
- Dataset path/version/hash.
- Exact command and environment.
- Evaluation result and conclusion in `EXPERIMENTS.md`.

## Priority
When both language and ML triggers match, ML domain requirements take priority over generic language style.
