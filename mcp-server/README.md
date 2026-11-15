# `orphan-disease-opportunity-mcp`

**Open Venture & Translational Opportunity Atlas — Model Context Protocol (MCP) Server**  
**Flagship Deep-Dive #1:** `JAK2 V617F` Myelofibrosis (`jak2-myelofibrosis`) • **Live Feed:** `https://rare-disease-atlas.github.io`

An open, zero-dependency MCP server and OpenAPI 3.1 toolkit designed for technical founders (**Computational / AI-Bio**, **Public Health Systems**, **Venture / Novel Financing**) and autonomous research agents evaluating high-tractability orphan disease startups, drug repurposing wedges, non-dilutive SBIR/venture-philanthropy grants, and ethical clinical validation pathways.

---

## Why This Exists

Over 7,000 rare diseases carry FDA Orphan Drug economic incentives (7-year market exclusivity, ~$4.3M PDUFA fee waiver, 25% clinical trial tax credit, N=120–250 pivotal trials), yet technical founders outside traditional wet-lab pharma rarely discover where **single-mutation structural tractability** intersects **urgent standard-of-care failure**.

**Flagship Case Study #1 (`jak2-myelofibrosis`)** models this completely:
- **Causal Precision:** A single somatic mutation (`JAK2 V617F` in the **JH2 pseudokinase** autoinhibitory domain) drives ~55% of Primary Myelofibrosis.
- **First-Gen SoC Failure Cliff:** All 4 FDA-approved JAK inhibitors (*ruxolitinib, fedratinib, pacritinib, momelotinib*) bind the conserved **JH1 catalytic domain**, suppressing wild-type JAK2 alongside mutant JAK2—causing dose-limiting anemia/thrombocytopenia, ~50% discontinuation within 3 years, minimal clonal eradication, and **14–24 month median survival post-ruxolitinib failure**.
- **Zero-Wet-Lab & Low-Capital Wedges:** From structure-guided JH2 V617F vs WT (`PDB: 6E2Q` vs `4FVP`) allosteric design + CRO screening, to AI bone marrow fibrosis digital pathology (`MF-0..3` replacement), single-cell megakaryocyte repurposing (`GSE153319`), and community-oncology post-ruxolitinib RWE trial matching.

---

## Exposed MCP Capabilities

### Tools (`tools/list` & `tools/call`)
1. **`match_founder_opportunities(background, capital_tier, wet_lab_required)`**  
   Filters startup & research blueprints across `computational-ai-bio`, `public-health`, and `venture-novel-financing`; `bootstrapped-grant` (<$250K), `seed` ($250K–$2.5M), and `series-a-platform`; and `wet_lab_required` (`false` / `true`). Fetches live updates from `https://rare-disease-atlas.github.io/opportunities.json` with automatic fallback to bundled `data/opportunities.json`.
2. **`get_disease_case_study(disease_id="jak2-myelofibrosis")`**  
   Returns causal biology, Type I JH1 SoC failure modes, FDA Orphan Drug Act incentives, M&A benchmarks ($1.7B–$2.9B), and open structural/transcriptomic dataset accessions (`PDB`, `ChEMBL`, `GEO`, `ClinicalTrials.gov`, `Every Cure`).
3. **`find_non_dilutive_grants(track="all")`**  
   Maps SBIR/STTR (`NCI`, `NHLBI`), foundation (`MPN Research Foundation`, `Harrington Discovery Institute`), venture philanthropy (`LLS Therapy Acceleration Program`), `FDA Orphan Products Grants`, and `ARPA-H` pathways.
4. **`get_validation_communities(disease_id="jak2-myelofibrosis")`**  
   Returns institutional & patient research networks (`MPNRF`, `MPN Advocacy & Education International`, `LLS`, `MPN Voice`, `ASH`) paired with strict **non-extractive ethical discovery guidelines**.

### Resource (`resources/read`)
- **`briefing://rare-disease-playbook/jak2-myelofibrosis`** — Full Markdown founder & agent playbook.

### Prompt (`prompts/get`)
- **`evaluate-rare-disease-venture`** — Multi-step 90-day killer-experiment, grant-stacking, and ethical validation workflow.

---

## Quickstart (Zero Dependencies — Python >= 3.10 Stdlib Only)

### 1. Run via PyPI / `uvx` (Once Published)
```bash
uvx orphan-disease-opportunity-mcp
```

### 2. Run Directly from Source (`stdio` MCP Transport)
```bash
PYTHONPATH=/path/to/mcp-server python3 -m orphan_disease_mcp
```

### 3. Configure in Claude Desktop / Cursor / Windsurf / Cline / Antigravity
Add to `claude_desktop_config.json` or `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "orphan-disease-opportunities": {
      "command": "python3",
      "args": ["-m", "orphan_disease_mcp"],
      "cwd": "/path/to/rare-disease-venture-atlas/mcp-server"
    }
  }
}
```

### 4. Run as Remote **Streamable HTTP** MCP Server
```bash
python3 -m orphan_disease_mcp --transport http --host 127.0.0.1 --port 8080
# Exposes:
#   POST http://127.0.0.1:8080/mcp
#   GET  http://127.0.0.1:8080/.well-known/mcp.json
#   GET  http://127.0.0.1:8080/health
```

### 5. Custom GPT Actions & OpenAPI Agents (Zero-Backend S3 Mode)
Import [`openapi.yaml`](./openapi.yaml) into **OpenAI Custom GPT Actions**, LangChain `OpenAPIToolkit`, or any OpenAPI 3.1 agent to query `https://rare-disease-atlas.github.io/opportunities.json` directly over HTTPS with zero server infrastructure.

---

## Run Automated Verification Suite

```bash
python3 test_mcp.py
```
