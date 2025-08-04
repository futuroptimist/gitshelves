# Repo Feature Summary Prompt

Use this prompt to gather the data required for flywheel's `repo-feature-summary.md`.

## Codex Prompt (paste verbatim)

> **System**: You analyze GitHub repositories for flywheel feature adoption.
> **User**:
> 1. Clone `https://github.com/futuroptimist/gitshelves`.
> 2. Report the following in a single table row:
>    - default branch name
>    - latest commit short SHA
>    - whether the latest commit has passing CI (Trunk)
>    - test coverage percentage
>    - whether patch coverage ≥ 90%
>    - presence of a `codecov.yml` file or Codecov badge
>    - primary installation method (pip, uv, etc.)
>    - existence of `LICENSE`, `AGENTS.md`, `CODE_OF_CONDUCT.md`,
>      `CONTRIBUTING.md`, and `pre-commit` config
>    - number of GitHub Actions workflows
>    - counts of dark patterns and bright patterns (use `flywheel` scanning tools if available)
>    - last updated date (UTC) of the commit
> 3. Output the table row using the format in `flywheel/docs/repo-feature-summary.md`.
> **Assistant**: Execute all steps and show your work.
