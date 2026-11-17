# `orphan-disease-opportunity-mcp` (`v1.6.0`)

**Open Venture & Translational Opportunity Atlas — Model Context Protocol (MCP) Server**  
**Paired Primary Flagships:** Clonal `JAK2 V617F+` Primary Myelofibrosis (`jak2-myelofibrosis`) & Reversible `JAK2`-Negative Autoimmune Myelofibrosis (`autoimmune-myelofibrosis`, AIMF + dual iron overload) • **Live Feed:** `https://rare-disease-atlas.github.io`

An open, zero-dependency MCP server (`2026-07-28` & `2025-11-25` Streamable HTTP + `stdio`) and OpenAPI 3.1 toolkit designed for technical founders (**Computational / AI-Bio**, **Public Health Systems**, **Venture / Novel Financing**) and autonomous research agents evaluating high-tractability orphan disease startups, drug repurposing wedges, non-dilutive SBIR/venture-philanthropy grants, 90-day validation plans, and ethical clinical validation pathways.

---

## Exposed `v1.6.0` MCP Capabilities

### 6 Canonical Read-Verb Tools (`tools/list` & `tools/call`, `readOnlyHint: true`)
1. **`search_founder_opportunities(background, capital_tier, wet_lab_required)`** *(legacy alias: `match_founder_opportunities`)*  
   Filters startup & research blueprints across `computational-ai-bio`, `public-health`, and `venture-novel-financing`; `bootstrapped-grant` (<$250K), `seed` ($250K–$2.5M), and `series-a-platform`; and `wet_lab_required` (`false` / `true`).
2. **`get_disease_case_study(disease_id="jak2-myelofibrosis")`**  
   Returns causal biology, Type I JH1 SoC failure modes, AIMF 74–80% marrow fibrosis reversal & dual iron overload, FDA Orphan Drug Act incentives, M&A benchmarks ($1.7B–$2.9B), and open structural/transcriptomic dataset accessions (`PDB`, `ChEMBL`, `GEO`, `ClinicalTrials.gov`).
3. **`list_non_dilutive_grants(track="all")`** *(legacy alias: `find_non_dilutive_grants`)*  
   Maps SBIR/STTR (`NCI`, `NHLBI`), foundation (`MPN Research Foundation`, `CDCN/Every Cure`, `Harrington Discovery Institute`), venture philanthropy (`Blood Cancer United TAP`), `FDA Orphan Products Grants`, and `ARPA-H` pathways.
4. **`get_validation_communities(disease_id="jak2-myelofibrosis")`**  
   Returns institutional & patient research networks paired with strict **non-extractive ethical discovery guidelines**.
5. **`get_90_day_validation_plan(disease_id="jak2-myelofibrosis", background="computational-ai-bio", capital_tier="bootstrapped-grant", wet_lab_required=False)`** *(legacy aliases: `generate_90_day_validation_plan`, `build_90_day_validation_plan`)*  
   Generates a structured 30/60/90-day killer-experiment, open dataset, CRO/FHIR budget, non-dilutive grant stack, and ethical patient advisory plan.
6. **`search_any_orphan_indication(disease_query, founder_background="all")`** *(legacy alias: `analyze_any_orphan_indication`)*  
   Runs live diligence across any of 7,000+ orphan diseases paired with FY2026 FDA Orphan Drug unit economics and benchmarked against Paired Myelofibrosis Flagships.

### Resources (`resources/read`)
- **`briefing://rare-disease-playbook/jak2-myelofibrosis`** — Clonal `JAK2 V617F+` Myelofibrosis founder & agent playbook.
- **`briefing://rare-disease-playbook/autoimmune-myelofibrosis`** — Reversible Autoimmune Myelofibrosis (`AIMF`) & dual iron overload playbook.

### Prompt (`prompts/get`)
- **`evaluate-rare-disease-venture`** — Multi-step 90-day killer-experiment, grant-stacking, and ethical validation workflow.

---

## Quickstart

```bash
# Zero-Install Remote Streamable HTTP
claude mcp add --transport http orphan-disease-atlas https://api.rare-disease-atlas.workers.dev/mcp

# Local STDIO Verification Suite
PYTHONDONTWRITEBYTECODE=1 python3 test_mcp.py
```
