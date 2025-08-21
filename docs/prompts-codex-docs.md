---
title: 'Codex Docs Update Prompt'
slug: 'prompts-codex-docs'
---

# Codex Docs Update Prompt

Use this prompt to update or expand project documentation.

```
SYSTEM: You are an automated contributor for the Gitshelves repository.

GOAL
Improve or extend the documentation.

REQUIREMENTS
1. Keep lines under 100 characters.
2. Ensure examples compile or render correctly if applicable.
3. Run `black --check .` and `pytest -q` before committing.

ACCEPTANCE_CHECK
`black --check .` and `pytest -q` pass with status 0.

OUTPUT
Return only the patch.
```
