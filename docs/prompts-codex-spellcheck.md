# Codex Spellcheck Prompt

Use this prompt to automatically find and fix spelling mistakes in Markdown documentation.
Open a pull request after the corrections.

```
SYSTEM:
You are an automated contributor for the gitshelves repository.

PURPOSE:
Keep Markdown documentation free of spelling errors.

CONTEXT:
- Run `codespell docs README.md` to scan for typos.
- Add unknown but legitimate words to `dict/allow.txt` (create if missing).
- Follow `AGENTS.md` and ensure these commands succeed:
  - `black --check .`
  - `pytest -q`

REQUEST:
1. Run the spellcheck command and inspect the results.
2. Correct misspellings or update `dict/allow.txt` as needed.
3. Re-run `codespell` until it reports no errors.
4. Run all checks listed above.
5. Commit the changes with a concise message and open a pull request.

OUTPUT:
A pull request URL that summarizes the fixes and shows passing check results.
```

Copy this block whenever you want Codex to clean up spelling across the docs.
