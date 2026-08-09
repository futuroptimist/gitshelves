#!/usr/bin/env bash
# Trusted, fixed-operation validation wrapper for the gitshelves @claude
# workflow. This script is always installed from the pinned workflow ref
# (github.workflow_sha), never from arbitrary pull request content, so it
# stays trustworthy even when the checked-out repository content is
# adversarial. Every operation is a verbatim command this repo already runs
# in real CI (.github/workflows/01-lint-format.yml, 02-tests.yml), with no
# arguments and no shell interpolation of caller-provided data.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: claude-validate.sh <operation>

Fixed operations (each takes zero arguments):
  prepare-deps    pip install black pytest pytest-cov coverage && pip install -e .
  lint            black --check .
  test-ci         pytest --cov=gitshelves --cov-report=xml --cov-report=term -q --cov-fail-under=100 && coverage report --fail-under=100
  network-probe   Assert no secret-bearing env vars are visible and outbound network is denied.
EOF
}

if [[ "$#" -ne 1 ]]; then
  usage >&2
  exit 64
fi

op="$1"

pip_install() {
  if command -v uv >/dev/null 2>&1; then
    uv pip install --system "$@"
  else
    python3 -m pip install "$@"
  fi
}

case "$op" in
  prepare-deps)
    pip_install black pytest pytest-cov coverage
    pip_install -e .
    ;;
  lint)
    black --check .
    ;;
  test-ci)
    pytest --cov=gitshelves --cov-report=xml --cov-report=term -q --cov-fail-under=100
    coverage report --fail-under=100
    ;;
  network-probe)
    python3 - <<'PY'
import os
import socket
import sys

secret_markers = ("TOKEN", "SECRET", "OIDC", "ACTIONS_ID_TOKEN", "GITHUB_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")
leaked = [name for name in os.environ if any(marker in name.upper() for marker in secret_markers)]
if leaked:
    print("secret-bearing environment variables visible: " + ",".join(sorted(leaked)), file=sys.stderr)
    sys.exit(1)

sock = socket.socket()
sock.settimeout(2)
reachable = sock.connect_ex(("1.1.1.1", 443)) == 0
sock.close()
if reachable:
    print("outbound network unexpectedly reachable", file=sys.stderr)
    sys.exit(1)
PY
    ;;
  *)
    echo "Unknown operation: $op" >&2
    usage >&2
    exit 64
    ;;
esac
