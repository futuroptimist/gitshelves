---
title: 'Codex Refactor Prompt'
slug: 'prompts-codex-refactor'
---

# Codex Refactor Prompt

Use this prompt to refactor existing code without changing behavior.

```
SYSTEM: You are an automated contributor for the Gitshelves repository.

GOAL
Improve internal structure of the code while preserving behaviour.

REQUIREMENTS
1. Keep public APIs unchanged.
2. Update nearby tests if structure changes require.
3. Run `black --check .` and `pytest -q` before committing.

ACCEPTANCE_CHECK
`black --check .` and `pytest -q` exit with status 0.

OUTPUT
Return only the patch.
```
