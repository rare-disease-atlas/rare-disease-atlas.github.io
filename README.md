# Rare Disease Venture & Translational Opportunity Atlas (`rare-disease-atlas.github.io` · `v1.6.0`)

> **Open-access translational briefing node, SEP-1649 MCP Server Card, A2A Agent Card & Model Context Protocol (`v1.6.0`) server** mapping startup blueprints, biological tractability, FDA Orphan Drug unit economics, non-dilutive grants, 90-day validation plans, and ethical patient validation pathways.  
> **Paired Primary Flagships:**
> 1. **Clonal `JAK2 V617F+` Primary Myelofibrosis** (`jak2-myelofibrosis`, `ICD-10: D47.4`, `ORPHA:824` — `JH2` vs `JH1` selectivity, mutant `CALR`, post-ruxolitinib survival cliff).
> 2. **Reversible `JAK2`-Negative Autoimmune Myelofibrosis (`AIMF`) & Dual Iron Overload** (`autoimmune-myelofibrosis`, `ICD-10: D75.89` — *Nature's Positive Control* achieving 74–80% human marrow fibrosis reversal + transfusional & `IL-6`/hepcidin/ferroportin iron trapping).

- **Live Web & Agent Dossier:** `https://rare-disease-atlas.github.io`
- **Zero-Install Remote Streamable HTTP MCP (`2026-07-28`):** `https://api.rare-disease-atlas.workers.dev/mcp`
- **SEP-1649 MCP Server Card & Manifest:** [`/.well-known/mcp/server-card.json`](site/.well-known/mcp/server-card.json) · [`/.well-known/mcp.json`](site/.well-known/mcp.json)
- **A2A Agent Card (`v1.6.0`):** [`/.well-known/agent.json`](site/.well-known/agent.json) · [`/.well-known/agent-card.json`](site/.well-known/agent-card.json)
- **LLM Summary & Full Corpus:** [`/llms.txt`](site/llms.txt) · [`/llms-full.txt`](site/llms-full.txt)
- **Canonical Venture Dataset (`CC-BY-4.0`, `v1.6.0`):** [`/opportunities.json`](site/opportunities.json)
- **Academic Citation & CodeMeta (`CFF 1.2.0`):** [`CITATION.cff`](CITATION.cff) (`https://rare-disease-atlas.github.io/CITATION.cff`) · [`codemeta.json`](codemeta.json)
- **x402 Free Public-Good Manifest (`$0 USD`):** [`/.well-known/x402.json`](site/.well-known/x402.json)
- **Open Agent Nectar Suite (`CC-BY-4.0` / Zero Auth):**
  - **`MyelofibrosisBench-v1` (30-Item Benchmark + Live Leaderboard):** [`/benchmarks/leaderboard.html`](https://rare-disease-atlas.github.io/benchmarks/leaderboard.html) · `GET https://api.rare-disease-atlas.workers.dev/api/leaderboard.json` · `https://rare-disease-atlas.github.io/benchmarks/myelofibrosis_bench.jsonl`
  - **Queryable Molecular & Comparison Micro-APIs:** `GET /api/gene?symbol=...` · `GET /api/pocket?pdb=...` · `GET /api/compare?a=jak2-myelofibrosis&b=autoimmune-myelofibrosis` (on `https://api.rare-disease-atlas.workers.dev`)
  - **Subscribable Clinical Catalyst Calendar:** `GET https://api.rare-disease-atlas.workers.dev/feeds/catalysts.json` · `GET https://api.rare-disease-atlas.workers.dev/feeds/myelofibrosis-catalysts.ics`
  - **3 Molecular & Clinical HF Parquet Tables:** `myelofibrosis_gene_signatures`, `jak2_structural_pockets`, `myelofibrosis_clinical_trials` on [`rare-disease-atlas/rare-disease-venture-atlas`](https://huggingface.co/datasets/rare-disease-atlas/rare-disease-venture-atlas)
  - **Stateless Hypothesis Red-Team API:** `POST https://api.rare-disease-atlas.workers.dev/api/stress-test`
  - **Two-Way A2A Findings Submission:** Send `"submit finding: ..."` to `POST https://api.rare-disease-atlas.workers.dev/a2a`
  - **Live Daily Myelofibrosis Bio-Delta Wire:** `https://api.rare-disease-atlas.workers.dev/atom.xml` (`/atom.xml`) · `https://api.rare-disease-atlas.workers.dev/feeds/bio-delta.json` (`/feeds/bio-delta.json`)
  - **Open Computational Problems:** `https://rare-disease-atlas.github.io/open-problems.json`
- **Zero-Auth OpenAPI 3.1 Spec:** [`/openapi.yaml`](site/openapi.yaml)
- **MCP Server (`MIT`, Zero Dependencies):** [`mcp-server/`](mcp-server/) (`uvx orphan-disease-opportunity-mcp`)

---

## Why This Repository Exists

Over 50% of Primary and Post-ET Myelofibrosis patients (>95% of Post-PV MF) carry a single somatic point mutation (`JAK2 V617F`) in the JH2 pseudokinase regulatory domain. Despite a validated $2B+ orphan market and $1.7B–$2.9B single-asset biotech M&A precedents, **zero non-transplant curative therapies exist**, and median survival following frontline ruxolitinib discontinuation drops to **11–23 months**. Meanwhile, **Autoimmune Myelofibrosis (`AIMF`)** proves human bone marrow reticulin fibrosis is physically reversible in **74–80% of patients** once the underlying inflammatory driver is extinguished, while illuminating dual transfusional + `IL-6`/hepcidin iron toxicity.

Today, technical founders across **AI/Computational Biology**, **Public Health / Real-World Evidence (RWE)**, and **Biotech Venture / Novel Financing** rely on autonomous research agents (ChatGPT Deep Research, Claude, Perplexity, Gemini, Cursor, Claude Code, Antigravity) to scout underserved problems. This monorepo ensures both web-browsing agents (`<link rel="mcp-server">`, `<link rel="agent-card">`, `llms.txt`) and tool-calling MCP/OpenAPI/A2A agents can verify primary `NCT`, `GSE`, `PDB`, and FDA statutory evidence with **zero prompt injection**.

---

## Canonical `v1.6.0` Read-Verb MCP Tools (`readOnlyHint: true`)

1. **`search_founder_opportunities`** *(legacy alias: `match_founder_opportunities`)* — Filter 16 curated startup blueprints across `computational-ai-bio`, `public-health`, and `venture-novel-financing` by capital tier and wet-lab requirement.
2. **`get_disease_case_study`** — Retrieve deep biological, clinical-trial, and unit-economics dossiers across our Paired Myelofibrosis Flagships (`jak2-myelofibrosis`, `autoimmune-myelofibrosis`) and 4 comparative cohorts (`vexas-syndrome`, `castleman-disease`, `systemic-mastocytosis`, `telomere-biology-disorders`).
3. **`list_non_dilutive_grants`** *(legacy alias: `find_non_dilutive_grants`)* — Stack NIH NCI/NHLBI SBIR/STTR, ARPA-H, MPNRF, Blood Cancer United TAP, CDCN/Every Cure, and FDA OOPD non-dilutive capital.
4. **`get_validation_communities`** — Retrieve established patient registries and academic consortia with mandatory non-extractive ethical guidelines.
5. **`get_90_day_validation_plan`** *(legacy aliases: `generate_90_day_validation_plan`, `build_90_day_validation_plan`)* — Generate a 30/60/90-day killer-experiment, dataset, CRO/FHIR budget, and grant-stacking roadmap.
6. **`search_any_orphan_indication`** *(legacy alias: `analyze_any_orphan_indication`)* — Run live federated diligence across all 7,000+ orphan diseases via OpenTargets v4, ClinicalTrials.gov v2, and PubMed benchmarked against Paired Myelofibrosis Flagships.

---

## Repository Structure

```text
.
├── site/                        # Pure static HTML/CSS/MD/JSON dossier (GitHub Pages / Cloudflare Edge)
│   ├── index.html               # Dual Agent/Human Briefing Hub (<link rel="mcp-server"> & <link rel="agent-card">)
│   ├── autoimmune-myelofibrosis-iron-wedge.html
│   ├── rare-disease-business-models.html
│   ├── public-health-biotech-wedges.html
│   ├── ai-drug-repurposing-targets.html
│   ├── hematology-immunology-orphan-expansion.html
│   ├── llms.txt & llms-full.txt # Answer.AI llmstxt.org agent feeds
│   ├── opportunities.json       # Synced from mcp-server/data/opportunities.json (v1.6.0)
│   ├── openapi.yaml             # Synced from mcp-server/openapi.yaml
│   └── .well-known/             # mcp/server-card.json (SEP-1649), mcp.json, agent.json, agent-card.json, agents.json
├── mcp-server/                  # Zero-dependency Python MCP server (v1.6.0 stdio + Streamable HTTP)
│   ├── orphan_disease_mcp/      # MCP server implementation (6 canonical read-verb tools + legacy aliases)
│   ├── data/opportunities.json  # Single source of truth dataset (v1.6.0)
│   ├── server.json              # Official MCP Registry manifest (io.github.rare-disease-atlas/...)
│   └── test_mcp.py              # End-to-end JSON-RPC & schema test suite
├── research/                    # Deep 2026 research dossiers, GEO/viral launch playbook & MCP strategy
└── .github/workflows/           # Auto-tests MCP server & deploys site/ to GitHub Pages on push
```

---

## Quick Start

### 1. Connect Zero-Install Remote MCP (`Streamable HTTP`)
```bash
claude mcp add --transport http orphan-disease-atlas https://api.rare-disease-atlas.workers.dev/mcp
```

### 2. Run the MCP Server Locally (`STDIO`)
```bash
PYTHONDONTWRITEBYTECODE=1 python3 mcp-server/test_mcp.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=mcp-server python3 -m orphan_disease_mcp
```

### 3. Preview the Static Website Locally
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m http.server 8000 --directory site
# Visit http://localhost:8000
```
