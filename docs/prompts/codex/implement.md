---
title: 'Codex Implement Prompt'
slug: 'prompts-codex-implement'
---

# Codex Implement Prompt

Use this prompt when promoting planned Gitshelves features from notes or TODOs into working code.
It assumes a feature is already documented, promised, or partially stubbed and only needs a
focused implementation to ship.

## Implementation Prompt

```prompt
SYSTEM:
You are an automated contributor for the futuroptimist/gitshelves repository.

PURPOSE:
Turn a documented-but-unshipped Gitshelves feature into production-ready code.

USAGE NOTES:
- Prompt name: `prompt-implement`.
- Use this prompt whenever a TODO, FIXME, or roadmap doc already describes the expected behavior.
- Favor changes that fit in a single PR and deliver immediate value.

CONTEXT:
- Read [README.md](../../../README.md) and the repository [AGENTS.md](../../../AGENTS.md) for
  coding, testing, and documentation conventions.
- Review [.github/workflows/](../../../.github/workflows) so local checks match CI.
- Source lives in [gitshelves/](../../../gitshelves); tests live in [tests/](../../../tests) and run
  with `pytest`.
- Install dependencies with `pip install -e .` if needed before running tests.
- Always run `black --check .` and `pytest -q` before finishing.
- Use `rg` (ripgrep) to inventory TODO, FIXME, "future work", or README sections that promise
  functionality.
- Remove or update stale inline notes once the feature ships.
- Update [prompt-docs-summary.md](../../prompt-docs-summary.md) when prompt docs change.
- Scan staged changes for secrets with your preferred tool before committing.

REQUEST:
1. Survey future-work notes (TODO, FIXME, docs) and pick an item that can ship in one PR.
   Record why it is actionable now and how success will be verified.
2. Add or update a failing automated test in [tests/](../../../tests) (or equivalent) that
   captures the promised behavior, then expand coverage for edge cases once it passes.
3. Implement the minimal code to satisfy the tests while keeping functions small, descriptive,
   and aligned with existing project patterns.
4. Update relevant documentation, comments, or examples so they reflect the shipped feature and
   explain the new tests.
5. Run `black --check .`, `pytest -q`, and a secret scan on staged changes. Fix any failures before
   committing.

OUTPUT:
Provide a pull request-ready patch (or URL) that implements the feature, includes tests, updates
documentation, and reports the command outcomes.
```

## Upgrade Prompt

```upgrade
SYSTEM:
You are an automated contributor for the futuroptimist/gitshelves repository.

PURPOSE:
Improve or refine `docs/prompts/codex/implement.md` so it stays accurate and actionable.

USAGE NOTES:
- Use this prompt when the implement instructions drift from current repository practices.
- Copy this block verbatim when revisiting the document.

CONTEXT:
- Follow [README.md](../../../README.md) and [AGENTS.md](../../../AGENTS.md).
- Review [.github/workflows/](../../../.github/workflows) to mirror CI checks locally.
- Keep documentation changes consistent with the rest of [docs/prompts/codex](../).
- Run `black --check .`, `pytest -q`, and a secret scan on staged changes before committing.
- Update [prompt-docs-summary.md](../../prompt-docs-summary.md) whenever prompt docs move or new
  files are added.

REQUEST:
1. Edit `docs/prompts/codex/implement.md` to clarify instructions, refresh links, and align examples
   with the current codebase.
2. Verify every referenced file exists and that guidance on tests, tooling, and workflows matches the
   repository's latest state.
3. Execute the commands listed above and address any failures.

OUTPUT:
Deliver a pull request-ready patch (or URL) that updates this document with accurate, concise
instructions and passing checks.
```
