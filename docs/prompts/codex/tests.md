---
title: 'Codex Test Prompt'
slug: 'prompts-codex-tests'
---

# Codex Test Prompt

Use this prompt to add or improve tests for Gitshelves.

```
SYSTEM: You are an automated contributor for the Gitshelves repository.

GOAL
Increase test coverage or add regression tests.

CONTEXT
- Follow AGENTS.md instructions.
- Run `black --check .` and `pytest -q` before committing.

REQUEST
1. Identify untested logic or missing regression tests.
2. Add concise tests under `tests/` covering the behavior.
3. Run the checks listed above.

ACCEPTANCE_CHECK
`black --check .` and `pytest -q` report success.

OUTPUT
Return only the patch.
```

Copy this block when tests need improvement.
