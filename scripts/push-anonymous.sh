#!/usr/bin/env bash
# =============================================================================
# push-anonymous.sh — Safe, Isolated Push to an Anonymous GitHub Repository
#
# Guarantees:
#   1. Audits working tree & full git commit history against local OS username
#      and global ~/.gitconfig name/email before allowing a push.
#   2. Disables system/global credential helpers (-c credential.helper=) so git
#      NEVER silently pushes using a cached personal GitHub token on this PC.
#
# Usage:
#   ./scripts/push-anonymous.sh https://github.com/<anon-username>/rare-disease-venture-atlas.git
# =============================================================================

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <https://github.com/ANON_USER/REPO.git>" >&2
  exit 1
fi

REMOTE_URL="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "==> [1/4] Auditing repository files & git history for local identity leaks..."
LOCAL_USER="$(whoami)"
GLOBAL_NAME="$(git config --global user.name 2>/dev/null || true)"
GLOBAL_EMAIL="$(git config --global user.email 2>/dev/null || true)"

PATTERNS=("${LOCAL_USER}" "/home/${LOCAL_USER}")
[[ -n "${GLOBAL_NAME}" ]] && PATTERNS+=("${GLOBAL_NAME}")
[[ -n "${GLOBAL_EMAIL}" ]] && PATTERNS+=("${GLOBAL_EMAIL}")

for pat in "${PATTERNS[@]}"; do
  if [[ -n "${pat}" ]]; then
    if git grep -Fq "${pat}" 2>/dev/null; then
      echo "ABORT: Found personal identifier '${pat}' in tracked files!" >&2
      git grep -Fn "${pat}" >&2
      exit 1
    fi
    if git log --all --format="%an %ae %cn %ce %B" | grep -Fq "${pat}"; then
      echo "ABORT: Found personal identifier '${pat}' in git commit metadata!" >&2
      exit 1
    fi
  fi
done

if git log --show-signature -n 20 2>&1 | grep -Eq "gpg:|Good signature"; then
  echo "ABORT: Detected GPG/SSH signature in commit history (could leak key fingerprint)!" >&2
  exit 1
fi

echo "    [PASS] Zero personal names, emails, home paths, or GPG signatures detected."

echo "==> [2/4] Configuring remote 'origin' -> ${REMOTE_URL}"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "${REMOTE_URL}"
else
  git remote add origin "${REMOTE_URL}"
fi

echo "==> [3/4] Pushing branch 'main' with isolated credentials (cached personal logins bypassed)..."
echo "    When prompted:"
echo "      Username: your NEW anonymous GitHub username"
echo "      Password: a Fine-Grained Personal Access Token from your anonymous GitHub account"
echo "                (Settings -> Developer settings -> Personal access tokens -> Fine-grained -> Contents: Read & Write, Workflows: Read & Write)"
echo ""

GIT_TERMINAL_PROMPT=1 git -c credential.helper= push -u origin main

echo "==> [4/4] Push complete! Next: In GitHub repo Settings -> Pages -> Source, select 'GitHub Actions'."
