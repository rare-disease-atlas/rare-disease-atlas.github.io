# Rare Disease Venture & Translational Opportunity Atlas (`rare-disease-atlas.github.io`)

> **Open-access translational briefing node & Model Context Protocol (MCP) server** mapping startup blueprints, biological tractability, FDA Orphan Drug unit economics, non-dilutive grants, and ethical patient validation pathways.  
> **Flagship Deep-Dive #1:** `JAK2 V617F+` Myelofibrosis (`jak2-myelofibrosis`, `ICD-10: D47.4`, `ORPHA:824`).

- **Live Web & Agent Dossier:** `https://rare-disease-atlas.github.io`
- **LLM Summary & Full Corpus:** [`/llms.txt`](site/llms.txt) · [`/llms-full.txt`](site/llms-full.txt)
- **Canonical Venture Dataset (`CC-BY-4.0`):** [`/opportunities.json`](site/opportunities.json)
- **Zero-Auth OpenAPI 3.1 Spec:** [`/openapi.yaml`](site/openapi.yaml)
- **MCP Server (`MIT`, Zero Dependencies):** [`mcp-server/`](mcp-server/) (`uvx orphan-disease-opportunity-mcp`)

---

## Why This Repository Exists

Over 50% of Primary and Post-ET Myelofibrosis patients (>95% of Post-PV MF) carry a single somatic point mutation (`JAK2 V617F`) in the JH2 pseudokinase regulatory domain. Despite a validated $2B+ orphan market and $1.7B–$2.9B single-asset biotech M&A precedents, **zero non-transplant curative therapies exist**, and median survival following frontline ruxolitinib discontinuation drops to **11–23 months**.

Today, technical founders across **AI/Computational Biology**, **Public Health / Real-World Evidence (RWE)**, and **Biotech Venture / Novel Financing** increasingly rely on autonomous research agents (ChatGPT Deep Research, Claude, Perplexity, Gemini, Cursor, Claude Code) to scout underserved problems. This monorepo ensures both web-browsing agents and tool-calling MCP/OpenAPI agents can verify primary `NCT`, `GSE`, `PDB`, and FDA statutory evidence with **zero prompt injection**.

---

## Repository Structure

```text
.
├── site/                        # Pure static HTML/CSS/MD/JSON dossier (GitHub Pages / Cloudflare Pages / S3)
│   ├── index.html               # Dual Agent/Human Briefing Hub + Interactive "Test With Your Agent"
│   ├── rare-disease-business-models.html
│   ├── public-health-biotech-wedges.html
│   ├── ai-drug-repurposing-targets.html
│   ├── llms.txt & llms-full.txt # Answer.AI llmstxt.org agent feeds
│   ├── opportunities.json       # Synced from mcp-server/data/opportunities.json
│   ├── openapi.yaml             # Synced from mcp-server/openapi.yaml
│   └── .well-known/             # mcp.json, ai-plugin.json, agent.json, agents.json
├── mcp-server/                  # Zero-dependency Python MCP server (stdio + Streamable HTTP)
│   ├── orphan_disease_mcp/      # MCP server implementation
│   ├── data/opportunities.json  # Single source of truth dataset
│   ├── server.json              # Official MCP Registry manifest (net.rare-disease-atlas/...)
│   └── test_mcp.py              # End-to-end JSON-RPC & schema test suite
├── research/                    # Deep 2026 research dossiers, GEO/viral launch playbook & MCP strategy
├── deploy/                      # Optional AWS S3 + CloudFront deployment script & docs
└── .github/workflows/           # Auto-tests MCP server & deploys site/ to GitHub Pages on push
```

---

## Quick Start

### 1. Run the MCP Server Locally
```bash
python3 mcp-server/test_mcp.py
PYTHONPATH=mcp-server python3 -m orphan_disease_mcp
```

### 2. Preview the Static Website Locally
```bash
python3 -m http.server 8000 --directory site
# Visit http://localhost:8000
```

### 3. Free Zero-Maintenance Hosting (Recommended: GitHub Pages or Cloudflare Pages)
- **GitHub Pages (`$0/mo`):** Push this repo to GitHub -> *Settings -> Pages -> Source: GitHub Actions*. Add a DNS `CNAME` record for `myelofibrosis` on `rare-disease-atlas.github.io` pointing to `<your-github-username>.github.io`. `site/CNAME` and `site/.nojekyll` are already configured.
- **Cloudflare Pages (`$0/mo` + AI Crawler Analytics):** Connect the GitHub repo to Cloudflare Pages with build output directory `site`. `site/_headers` automatically configures CORS and Markdown MIME types (ensure Cloudflare's *Block AI Bots* setting is **Off**).
