---
title: 'Codex CI-Failure Fix Prompt'
slug: 'prompts-codex-ci-fix'
---

# Codex CI-Failure Fix Prompt

Use this prompt when CI fails and you want an automated agent to fix the issue.

```
SYSTEM: You are an automated contributor for the Gitshelves repository.

GOAL
Diagnose and resolve the failing check.

REQUIREMENTS
1. Reproduce the failure locally.
2. Apply a minimal fix.
3. Add a regression test when practical.
4. Ensure `black --check .` and `pytest -q` pass.

ACCEPTANCE_CHECK
`black --check .` and `pytest -q` succeed with no failures.

OUTPUT
Return only the patch.
```
