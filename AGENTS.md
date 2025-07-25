# Agent Workflow Guide

This repository uses a simple Python package for generating 3D printable GitHub contribution charts. When updating code or documentation, follow these guidelines:

- **Install** dependencies in editable mode before running tests:
  ```bash
  pip install -e .
  ```
- **Run tests** after making changes:
  ```bash
  pytest -q
  ```
- **Update documentation** (README.md and this file) if CLI usage or agent instructions change. The CLI now accepts `--start-year`, `--end-year`, `--months-per-row` and optional `--stl` output to control the contribution range and output format.
- New prompt templates or other agent-facing strings should include comments describing their purpose and context.

