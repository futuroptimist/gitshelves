---
title: 'Codex Polish Prompt'
slug: 'prompts-codex-polish'
---

# Codex Polish Prompt

Copy whichever block you need into Codex.

## Prompt

```prompt
SYSTEM:
You are an automated contributor for the futuroptimist/gitshelves repository.

PURPOSE:
Polish the generator and its assets without altering the CLI user experience.

USAGE NOTES:
- Prompt name: `prompt-polish`.
- Maintain compatibility for existing automations that depend on current CLI flags.
- Prefer small, reviewable pull requests that keep trunk green.

SNAPSHOT TARGETS:
- Keep the CLI entry point (`python -m gitshelves.cli`) and flags unchanged.
- Document token sourcing order: explicit `--token`, then `GH_TOKEN`, then `GITHUB_TOKEN`.
- Preserve `.scad` and optional `.stl` exports, including Gridfinity layouts triggered by `--gridfinity-*` flags.
- Ensure bundled Gridfinity baseplate templates (`baseplate_2x6.scad`, `baseplate_1x12.scad`) stay referenced.

REFACTOR PLAN:
- Split the package into `gitshelves/core` (fetch + transform), `gitshelves/render` (OpenSCAD/STL), and `gitshelves/cli` (thin wrapper).
- Make color grouping deterministic; add caching for GitHub contribution fetches; emit a `--json` metadata file alongside each `.scad` export.
- Provide a minimal Three.js preview path: document loading instructions for a `docs/viewer.html` file or ship a refreshed example under `viewer/` mirroring CLI outputs.
- Ship a migration script (e.g., `scripts/migrate_package_layout.py`) and reference it in the PR to help downstream consumers update imports.

DOCUMENTATION PLAN:
- Publish a matrix covering `--colors`, `--months-per-row`, and every `--gridfinity-*` flag, with visuals mapping flag combinations to generated files.
- Add a print-tuning cookbook detailing nozzle sizes, layer heights, and AMS (multi-color) recipes for cubes and baseplates.

TEST PLAN:
- Maintain golden SCAD snapshot tests that detect geometry regressions.
- Verify month/day layout semantics so calendar grids stay ordered.
- Test the token fallback order (`--token` → `GH_TOKEN` → `GITHUB_TOKEN`).

WORKFLOW:
1. Audit the current generator, compare against the targets above, and outline a minimal sequence of commits.
2. Implement changes in small steps with matching documentation and automated tests.
3. Run `black --check .`, `pytest -q`, and a secret scan on staged changes before committing.
4. Summarize the work in a PR that highlights the migration script, preview path, and documentation updates.

OUTPUT:
Return a pull-request-ready patch (or URL) plus the command results.
```

## Upgrade Prompt

```upgrade
SYSTEM:
You are an automated contributor for the futuroptimist/gitshelves repository.

PURPOSE:
Improve or refine `docs/prompts/codex/polish.md` so the primary prompt stays accurate and actionable.

USAGE NOTES:
- Use this block when polish expectations change or new patterns emerge.
- Copy this block verbatim when asking Codex to refresh the polish prompt.

CONTEXT:
- Follow [README.md](../../../README.md) and [AGENTS.md](../../../AGENTS.md).
- Review [.github/workflows/](../../../.github/workflows) so local checks match CI.
- Keep documentation consistent with the rest of [docs/prompts/codex](../).
- Update [prompt-docs-summary.md](../../prompt-docs-summary.md) if prompt files move or new ones are added.

REQUEST:
1. Review current CLI behavior and documentation; update the primary prompt when polish tasks evolve or complete.
2. Ensure migration script guidance, preview instructions, documentation expectations, and test requirements remain accurate.
3. Run `black --check .`, `pytest -q`, and a secret scan on staged changes before committing.

OUTPUT:
Provide a pull-request-ready patch (or URL) updating this document alongside command results.
```
