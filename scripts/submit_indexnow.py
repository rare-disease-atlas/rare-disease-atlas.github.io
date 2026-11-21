#!/usr/bin/env python3
"""
IndexNow Instant Search Crawler Notification (`api.indexnow.org`) for v1.6.0.

Submits all canonical HTML, Markdown (`llms.txt`, `llms-full.txt`, `AGENTS.md`),
Croissant JSON-LD, OpenAPI, SEP-1649 MCP Server Card (`/.well-known/mcp/server-card.json`),
A2A Agent Cards (`/.well-known/agent.json`, `/.well-known/agent-card.json`), and
structured JSON URLs for every active Atlas host (`atlas.rare-disease-atlas.workers.dev`
and `rare-disease-atlas.github.io`) to Bing, Yandex, Seznam, Naver, and IndexNow subscribers.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

HOSTS = (
    "atlas.rare-disease-atlas.workers.dev",
    "rare-disease-atlas.github.io",
)
KEY = "9f4c2e8a71b540d38e6c1a92f0b74d5e"

PATHS = (
    "/",
    "/rare-disease-business-models.html",
    "/public-health-biotech-wedges.html",
    "/ai-drug-repurposing-targets.html",
    "/autoimmune-myelofibrosis-iron-wedge.html",
    "/hematology-immunology-orphan-expansion.html",
    "/llms.txt",
    "/llms-full.txt",
    "/AGENTS.md",
    "/opportunities.json",
    "/croissant.json",
    "/openapi.yaml",
    "/feeds/ai-bio.json",
    "/feeds/public-health.json",
    "/feeds/venture.json",
    "/feeds/aimf.json",
    "/sitemap.xml",
    "/.well-known/mcp/server-card.json",
    "/.well-known/mcp.json",
    "/.well-known/agent.json",
    "/.well-known/agent-card.json",
    "/.well-known/agents.json",
    "/.well-known/x402.json",
    "/open-problems.json",
    "/benchmarks/rare-tx-bench.html",
    "/benchmarks/rare_tx_raw_bio_compute.jsonl",
    "/benchmarks/rare_tx_protocol_audit.jsonl",
    "/benchmarks/rare_tx_bio_delta_live.jsonl",
    "/benchmarks/rare_tx_bench.jsonl",
    "/benchmarks/rare_tx_open_frontier.jsonl",
    "/benchmarks/leaderboard.html",
    "/benchmarks/myelofibrosis_bench.jsonl",
    "/benchmarks/myelofibrosis_bench_dev.jsonl",
    "/benchmarks/evaluate_agent.py",
    "/benchmarks/README.md",
    "/CITATION.cff",
    "/codemeta.json",
    "/atom.xml",
    "/feeds/bio-delta.json",
    "/data/myelofibrosis_gene_signatures.jsonl",
    "/data/jak2_structural_pockets.jsonl",
    "/data/myelofibrosis_clinical_trials.jsonl",
    "/notebooks/myelofibrosis_translational_quickstart.ipynb",
)


def submit_host(host: str) -> bool:
    key_location = f"https://{host}/{KEY}.txt"
    try:
        req_check = urllib.request.Request(
            key_location, headers={"User-Agent": "atlas-indexnow-verifier/1.6.0"}
        )
        with urllib.request.urlopen(req_check, timeout=10) as r:
            body = r.read().decode("utf-8").strip()
            if body != KEY:
                print(f"Skipping {host}: key file mismatch ({body!r})")
                return False
    except (urllib.error.URLError, TimeoutError) as err:
        print(f"Skipping {host} (currently offline: {err})")
        return False

    urls = [f"https://{host}{p}" for p in PATHS]
    payload = {
        "host": host,
        "key": KEY,
        "keyLocation": key_location,
        "urlList": urls,
    }
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(
            f"IndexNow submission HTTP {resp.status}: submitted {len(urls)} URLs for {host}"
        )
    return True


def main() -> int:
    any_ok = False
    for h in HOSTS:
        if submit_host(h):
            any_ok = True
    return 0 if any_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
