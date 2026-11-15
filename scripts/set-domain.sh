#!/usr/bin/env bash
# =============================================================================
# set-domain.sh — Update canonical domain across site/, mcp-server/, and specs
#
# Usage:
#   ./scripts/set-domain.sh <new-domain> [--cname]
#
# Examples:
#   ./scripts/set-domain.sh rare-disease-atlas.pages.dev
#   ./scripts/set-domain.sh orphanventureatlas.org --cname
# =============================================================================

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <new-domain> [--cname]" >&2
  exit 1
fi

NEW_DOMAIN="${1#https://}"
NEW_DOMAIN="${NEW_DOMAIN#http://}"
NEW_DOMAIN="${NEW_DOMAIN%/}"
WRITE_CNAME="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

python3 - "${ROOT_DIR}" "${NEW_DOMAIN}" << 'PY'
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
new_domain = sys.argv[2]

# Read current canonical domain from mcp-server/data/opportunities.json
opp_path = root / "mcp-server" / "data" / "opportunities.json"
data = json.loads(opp_path.read_text(encoding="utf-8"))
old_url = data["canonical_url"]  # e.g. https://rare-disease-atlas.org/opportunities.json
old_domain = old_url.split("://", 1)[1].split("/", 1)[0]

def reverse_ns(domain: str) -> str:
    parts = domain.split(".")
    return ".".join(reversed(parts))

old_ns = f"{reverse_ns(old_domain)}/orphan-disease-opportunity-mcp"
new_ns = f"{reverse_ns(new_domain)}/orphan-disease-opportunity-mcp"

if old_domain == new_domain:
    print(f"Domain is already set to {new_domain}")
    sys.exit(0)

count = 0
for p in root.rglob("*"):
    if p.is_file() and ".git/" not in str(p) and "__pycache__" not in str(p) and p.name != "set-domain.sh":
        text = p.read_text(encoding="utf-8")
        updated = text.replace(old_ns, new_ns).replace(old_domain, new_domain)
        if updated != text:
            p.write_text(updated, encoding="utf-8")
            count += 1

print(f"Updated {old_domain} -> {new_domain} across {count} files.")
PY

if [[ "${WRITE_CNAME}" == "--cname" ]]; then
  echo "${NEW_DOMAIN}" > "${ROOT_DIR}/site/CNAME"
  echo "Wrote ${ROOT_DIR}/site/CNAME (${NEW_DOMAIN}) for GitHub Pages custom domain."
else
  rm -f "${ROOT_DIR}/site/CNAME"
  echo "Removed site/CNAME (use --cname when attaching a custom domain on GitHub Pages)."
fi
