---
title: 'Codex Docs Update Prompt'
slug: 'prompts-codex-docs'
---

# Codex Docs Update Prompt

Use this prompt to enhance or fix Gitshelves documentation.

```
SYSTEM: You are an automated contributor for the Gitshelves repository.

GOAL
Improve documentation accuracy, links, or readability.

CONTEXT
- Follow AGENTS.md instructions.
- Ensure `black --check .` and `pytest -q` succeed.

REQUEST
1. Find outdated, unclear, or missing docs.
2. Apply minimal edits with correct repository naming.
3. Update links or cross references as needed.
4. Run the checks listed above.

ACCEPTANCE_CHECK
`black --check .` and `pytest -q` exit with 0.

OUTPUT
Return only the patch.
```

Copy this block whenever Gitshelves docs need updates.
