# Pillar 3: Deep Agent Ecosystem Hooks, Tool Registries, `.well-known` Protocols & MCP Distribution Strategy

**Target Domain:** `https://rare-disease-atlas.github.io`  
**Flagship Indication:** `JAK2 V617F` Myelofibrosis (Primary & Post-PV/ET Myelofibrosis)  
**Umbrella Package / Dataset Identity:** `orphan-disease-opportunity-mcp` / `rare-disease-venture-atlas` (Flagship Case Study #1: `jak2-myelofibrosis`)

---

## 1. Executive Thesis: Moving from Passive Scraping to Active Tool Invocation

Traditional scientific advocacy sites rely on human SEO and passive web crawlers. However, in 2025–2026, technical founders—across **Computational/AI-Bio**, **Public Health Systems**, and **Venture/Novel Financing**—increasingly delegate market sizing, target selection, grant scouting, and startup ideation to **autonomous research agents and coding IDEs** (Claude Code, Claude Desktop, Cursor, Windsurf, Cline, Antigravity, OpenAI Custom GPTs/Agents, and biomedical frameworks like Stanford's `Biomni` and `DrugAgent`).

When an agent is asked *"Find high-tractability rare diseases where first-generation kinase inhibitors fail, non-dilutive SBIR/venture-philanthropy capital exists, and an AI-bio or health-systems team can validate a wedge under $500K"*, passive HTML pages lose to **structured, callable tools and machine-native manifests**.

To capture this agentic workflow ethically, credibly, and at zero marginal hosting cost (compatible with static S3 + CloudFront hosting alongside PyPI/Hugging Face distribution), `rare-disease-atlas.github.io` should deploy a **Four-Layer Active Discovery Architecture**:

1. **Umbrella Semantic Framing ("The 10x Funnel"):** Broad rare-disease venture naming that captures top-of-funnel startup/research queries and routes them into `JAK2+` Myelofibrosis as the gold-standard reference flagship.
2. **Model Context Protocol (MCP) Server & Registry Syndication:** Zero-dependency `stdio` + Streamable HTTP MCP server indexed across Official MCP Registry, Glama, Smithery, PulseMCP, and `mcp.so`.
3. **Domain-Level `.well-known/` & Static OpenAPI Protocols:** Zero-backend S3 static manifests (`/llms.txt`, `/.well-known/mcp.json`, `/.well-known/agents.json`, `/.well-known/agent.json`, `/.well-known/ai-plugin.json`, `/openapi.yaml`, and Schema.org `Dataset`/`MedicalCondition` JSON-LD).
4. **Biomedical & Venture Dataset Hubs:** Hugging Face `Datasets` (with Croissant JSON-LD auto-indexing into Google Dataset Search), GitHub topic graphs, and PyPI packaging.

---

## 2. Why Umbrella Naming Captures 10x–25x More Agent Traffic ("The Flagship Funnel")

### The Discovery Bottleneck of Disease-Specific Naming
If we publish an MCP server or Hugging Face dataset named `jak2-myelofibrosis-mcp`, an AI agent or founder will **only** invoke it *after* they have already decided to work on Myelofibrosis. That misses 95%+ of high-agency founders who are currently searching by **capability, business model, or funding mechanism** rather than a specific ICD-10 code.

Compare actual top-of-funnel founder and agent search intents:

| Founder / Agent Query Pattern | Matches `myelofibrosis-mcp`? | Matches `orphan-disease-opportunity-mcp` / `rare-disease-venture-atlas`? |
| :--- | :---: | :---: |
| *"Find rare disease startup opportunities for ML/protein design founders"* | No | **Yes** (Matches tool name, tags & `match_founder_opportunities`) |
| *"Non-dilutive biotech grants SBIR + venture philanthropy for orphan drugs"* | No | **Yes** (Matches `find_non_dilutive_grants`) |
| *"Clinical trial / RWD public health ventures in hematology or oncology"* | No | **Yes** (Matches `public-health` founder track) |
| *"Mutant-selective kinase / pseudokinase drug repurposing dataset"* | Partial | **Yes** (Matches HF biomedical tags + `jak2-myelofibrosis` flagship) |
| *"JAK2 V617F myelofibrosis ruxolitinib failure unmet needs"* | Yes | **Yes** (Direct match on `get_disease_case_study("jak2-myelofibrosis")`) |

### Ethical, High-Credibility Positioning (Zero Bait-and-Switch)
To ensure **100% transparency and zero spam perception** among developers, registry reviewers, and agents:
- **Explicit Scope Declaration:** Name the package `orphan-disease-opportunity-mcp` (and dataset `rare-disease-venture-atlas`) and state clearly in the first sentence of `README.md`, `server.json`, and tool descriptions: *"Open translational & venture opportunity atlas for high-tractability orphan diseases—featuring a complete, deeply-researched V1 Flagship Deep-Dive on JAK2 V617F Myelofibrosis (`jak2-myelofibrosis`) and an open schema for community disease contributions."*
- **Why Agents Prefer Complete Depth Over Shallow Breadth:** Rather than padding the database with 50 superficial LLM-generated disease stubs (which degrades trust and triggers anti-slop filters on Glama and Hugging Face), providing **one extraordinarily rigorous, citation-backed reference vertical** (`jak2-myelofibrosis`) with exact crystal structures (`PDB: 4FVP`, `6E2Q`), GEO transcriptomics (`GSE54644`), FDA Orphan Drug economics, and active MPNRF/LLS TAP funding mechanics makes agents treat `jak2-myelofibrosis` as their concrete worked example whenever synthesizing biotech startup blueprints.
- **Open Contribution Hook:** Include a `CONTRIBUTING.md` schema specification inviting academic labs and rare-disease foundations to submit Pull Requests adding Flagship #2, #3, etc., turning the repo into an organic magnet for translational researchers.

---

## 3. Channel-by-Channel Distribution Strategy (2025–2026 Ecosystem)

### Priority Matrix

| Priority | Channel / Protocol | Target Consumer | Hosting / Infra Cost | Credibility & Traffic Impact |
| :---: | :--- | :--- | :--- | :--- |
| **P0** | **Official MCP Registry** (`registry.modelcontextprotocol.io`) + PyPI | Claude Code, VS Code/GitHub Copilot, Cursor, Windsurf, Antigravity, enterprise MCP gateways | $0 (PyPI + DNS TXT) | **Critical** — Root source of truth ingested by downstream directories & IDE tool pickers |
| **P0** | **`/llms.txt`, `/llms-full.txt` & `/openapi.yaml` on S3** | Coding agents, Perplexity/SearchGPT, OpenAI Custom GPT Actions, LangChain OpenAPI toolkits | $0 (Static S3 files) | **Critical** — Turns static S3 JSON files into live REST API endpoints for non-MCP agents |
| **P1** | **Glama (`glama.ai/mcp`) & Smithery (`smithery.ai`)** | Agent builders browsing rated MCP tools; browser-based MCP sandbox users | $0 | **High** — Glama auto-grades security/license/quality; high organic search ranking for MCP tools |
| **P1** | **Hugging Face `Datasets`** (`rare-disease-atlas/rare-disease-venture-atlas`) | Biomedical AI agents (`Biomni`, `DrugAgent`), ML researchers, Google Dataset Search (via Croissant) | $0 | **High** — Reaches computational bio founders directly inside their Python/HF workflows |
| **P1** | **Schema.org `Dataset` + `MedicalCondition` JSON-LD** | Google Dataset Search, Semantic Scholar / biomedical knowledge graph crawlers | $0 (Inline HTML `<script>`) | **High** — Surfaces `rare-disease-atlas.github.io` in academic & translational dataset searches |
| **P2** | **`/.well-known/mcp.json`, `agents.json`, `agent.json` (A2A)** | Autonomous web-browsing agents & multi-agent discovery routers | $0 (Static S3 files) | **Medium-High** — Zero-cost future-proofing for domain-level autonomous agent handshakes |
| **P2** | **PulseMCP (`pulsemcp.com`), `mcp.so` & GitHub Topics** | Early-adopter AI engineers, newsletter/trending tool trackers, GitHub code search | $0 | **Medium** — Drives developer discovery, stars, and backlinks |

---

### Channel 1: MCP Registries & Directories

1. **Official MCP Registry (`registry.modelcontextprotocol.io`)**
   - **Mechanism:** Governed via standardized `server.json` metadata + cryptographic namespace verification.
   - **Domain-Verified Namespace Advantage:** Instead of publishing only under a generic GitHub user namespace (`io.github.*`), verify `io.github.rare-disease-atlas/orphan-disease-opportunity-mcp` via DNS TXT record on `rare-disease-atlas.github.io` using the official `mcp-publisher` CLI. Domain-verified namespaces carry higher trust signals in enterprise and IDE MCP clients.
   - **Dual Transport Support:** Expose both `pypi` (`uvx orphan-disease-opportunity-mcp` over `stdio`) for zero-latency local IDE execution and `streamable-http` for cloud-hosted agent runtimes.

2. **Glama (`glama.ai/mcp`)**
   - **How Glama Ranks & Grades Servers:** Glama automatically ingests the Official Registry and GitHub repos, assigning an automated **Quality & Security Score** based on: permissive open-source license (`MIT` or `Apache-2.0`), zero hardcoded secrets/unsafe shell execution, clean tool `inputSchema` descriptions, working `Dockerfile` / zero-dependency installability, and comprehensive `README.md`.
   - **Optimization:** Because our MCP server uses pure Python standard library with zero native binary bloat, strict read-only HTTPS/bundled JSON lookups, MIT licensing, and rich JSON Schema parameter annotations, it is engineered to earn an **A+ Glama safety/quality grade** and work immediately in Glama's in-browser inspector.

3. **Smithery (`smithery.ai`), PulseMCP (`pulsemcp.com`), and `mcp.so`**
   - **Smithery:** Add a `smithery.yaml` config pointing to the `stdio` entrypoint so one-click CLI installers (`npx -y @smithery/cli install ...`) and hosted Streamable HTTP gateways can run the server effortlessly.
   - **PulseMCP & `mcp.so`:** Submit under **Healthcare / Life Sciences**, **Research & Data**, and **Startup / Venture Intelligence** categories—categories with far higher signal-to-noise ratio (and much less competition!) than generic DevOps/productivity MCP tools.

---

### Channel 2: `.well-known/` & Static S3 Machine Discovery Stack

Because `rare-disease-atlas.github.io` is deployed on static S3 + CloudFront, every single machine discovery protocol below can be served as **static files** with proper `Content-Type: application/json` (or `text/markdown; charset=utf-8`) and `Access-Control-Allow-Origin: *` CORS headers:

| Static File Path on `rare-disease-atlas.github.io` | Standard / Consumer | Exact Function in Our Funnel |
| :--- | :--- | :--- |
| `/llms.txt` | Answer.AI `llmstxt.org` | Concise ~150-line executive index mapping founder tracks, biological thesis, open JSON URLs, and MCP install command (`uvx orphan-disease-opportunity-mcp`). |
| `/llms-full.txt` | RAG & Deep Research Agents | Complete concatenated markdown playbook (Biology + Clinical Unmet Need + Venture Blueprints + Grants + Ethical Validation) for single-fetch context ingestion. |
| `/.well-known/mcp.json` | MCP Domain Autodiscovery | Declares the domain's official MCP server package, tool manifest, `briefing://` resource URI, and optional Streamable HTTP endpoint so browsing agents know an MCP toolset exists for this site. |
| `/.well-known/agents.json` | Autonomous Action Manifest | Maps high-level agent intents (`discover_venture_blueprints`, `query_non_dilutive_grants`, `inspect_jak2_biology`) to `/openapi.yaml` and `/.well-known/mcp.json`. |
| `/.well-known/agent.json` | Google/OSS A2A Agent Card | Publishes capability metadata (`skills`: rare-disease venture scoping, orphan drug regulatory economics, MPN grant matching) for Agent2Agent routers. |
| `/.well-known/ai-plugin.json` + `/openapi.yaml` | OpenAI Custom GPT Actions & OpenAPI Agents | **Serverless REST API Trick:** Maps `GET /opportunities.json`, `GET /case-studies/jak2-myelofibrosis.json`, `GET /grants.json`, and `GET /communities.json` as typed OpenAPI 3.1 endpoints on S3! Custom GPTs and LangChain OpenAPI agents can "query the API" at $0 server cost. |
| Inline `<script type="application/ld+json">` | Schema.org `Dataset` + `MedicalCondition` | Dual-typed JSON-LD graph in `index.html`: declares `MedicalCondition` (`JAK2 V617F Myelofibrosis`, ICD-10 `D47.4` / `C94.4`, Orphanet `ORPHA:824`) linked via `subjectOf` to a `Dataset` (`distribution`: `ContentUrl` -> `opportunities.json`, license `CC-BY-4.0`) for **Google Dataset Search**. |

#### Recommended Schema.org JSON-LD Snippet (for `site/index.html` coordination)
```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "MedicalCondition",
      "@id": "https://rare-disease-atlas.github.io/#condition-jak2-mf",
      "name": "JAK2 V617F-Positive Myelofibrosis",
      "alternateName": ["Primary Myelofibrosis", "PMF", "Post-PV/ET Myelofibrosis"],
      "code": [
        { "@type": "MedicalCode", "codeValue": "D47.4", "codingSystem": "ICD-10" },
        { "@type": "MedicalCode", "codeValue": "ORPHA:824", "codingSystem": "Orphanet" }
      ],
      "associatedAnatomy": { "@type": "AnatomicalStructure", "name": "Bone Marrow" },
      "possibleTreatment": [
        { "@type": "Drug", "name": "Ruxolitinib" },
        { "@type": "Drug", "name": "Fedratinib" },
        { "@type": "Drug", "name": "Pacritinib" },
        { "@type": "Drug", "name": "Momelotinib" }
      ]
    },
    {
      "@type": "Dataset",
      "@id": "https://rare-disease-atlas.github.io/#venture-dataset",
      "name": "Rare Disease Venture & Translational Opportunity Atlas — Flagship #1: JAK2+ Myelofibrosis",
      "description": "Structured open dataset of startup blueprints, biological tractability (JAK2 JH2 pseudokinase allosteric selectivity vs Type I JH1 pan-JAK cytopenias), FDA Orphan Drug Act unit economics, non-dilutive SBIR/MPNRF/LLS TAP grants, and ethical clinical validation pathways.",
      "url": "https://rare-disease-atlas.github.io/",
      "license": "https://creativecommons.org/licenses/by/4.0/",
      "isAccessibleForFree": true,
      "keywords": [
        "rare disease", "orphan drug", "drug repurposing", "myelofibrosis",
        "JAK2 V617F", "JH2 pseudokinase", "biotech venture", "public health innovation", "SBIR"
      ],
      "about": { "@id": "https://rare-disease-atlas.github.io/#condition-jak2-mf" },
      "distribution": [
        {
          "@type": "DataDownload",
          "encodingFormat": "application/json",
          "contentUrl": "https://rare-disease-atlas.github.io/opportunities.json"
        }
      ]
    }
  ]
}
```

---

### Channel 3: Hugging Face `Datasets`, Biomedical Agent Frameworks & GitHub/PyPI

Biomedical AI agents (such as Stanford's **Biomni**, **DrugAgent**, and researchers working on **VivaBench**, **RareArena**, **RareBench**, and **Every Cure** knowledge graphs) routinely query the Hugging Face Hub API (`huggingface_hub.list_datasets(search=...)`) and GitHub Search API when assembling literature, target tractability, and translational priors.

1. **Hugging Face Dataset (`rare-disease-atlas/rare-disease-venture-atlas`)**
   - Mirror `data/opportunities.json` as clean Parquet/JSONL splits on Hugging Face Hub (`opportunities`, `case_studies`, `non_dilutive_grants`, `open_bio_datasets`).
   - **Automatic Croissant + Google Dataset Search Indexing:** Hugging Face automatically generates MLCommons `Croissant` JSON-LD metadata for public datasets with complete Dataset Cards, getting indexed by Google Dataset Search on a high-authority domain (`huggingface.co`) within days.
   - **High-Intent YAML Frontmatter Tags:**
     ```yaml
     license: cc-by-4.0
     task_categories:
       - question-answering
       - text-retrieval
     tags:
       - medical
       - biology
       - chemistry
       - rare-disease
       - orphan-drug
       - drug-repurposing
       - biomedical-agents
       - myelofibrosis
       - jak2
       - venture-building
     pretty_name: Rare Disease Venture & Translational Opportunity Atlas (Flagship v1: JAK2+ Myelofibrosis)
     ```

2. **GitHub Repository & Topic Graph**
   - Tag the open-source repository with: `mcp-server`, `model-context-protocol`, `rare-disease`, `orphan-drug`, `computational-biology`, `drug-discovery`, `public-health`, `biotech`, `jak2`, `myelofibrosis`.
   - Submit high-signal, non-promotional PRs to curated lists where relevant:
     * `modelcontextprotocol/servers` (Community Servers section) / `punkpeye/awesome-mcp-servers` (Healthcare & Life Sciences category)
     * Awesome Computational Biology / Open Drug Discovery tool lists (highlighting the free zero-auth MCP access to Orphan Drug economics + SBIR/venture-philanthropy grant mapping).

3. **Biomedical Benchmark & Agent Cross-Linking**
   - Map every opportunity and biological target in `data/opportunities.json` to **standard biomedical identifiers** that agents like `Biomni` and `Every Cure` KG tools join on:
     * **UniProt:** `O60674` (`JAK2_HUMAN`, mutation `p.Val617Phe` / `VAR_033292`)
     * **PDB Structures:** `4FVP` (WT JAK2 JH2 pseudokinase), `6E2Q` (JAK2 V617F mutant JH2 crystal structure), `3KRR` (JAK2 JH1 + Ruxolitinib complex)
     * **ChEMBL:** `CHEMBL2971` (Tyrosine-protein kinase JAK2 bioactivity dataset)
     * **NCBI GEO:** `GSE54644`, `GSE153319` (MPN bulk & single-cell transcriptomics)
     * **Orphanet / MONDO / OMIM:** `ORPHA:824`, `MONDO:0019565`, `OMIM:254450`
   - Including exact database accessions inside MCP tool responses lets an autonomous AI-bio agent immediately chain our MCP server output directly into ChEMBL, AlphaFold/PDB, or GEO MCP tools!

---

## 4. Anti-Spam, Scientific Rigor & Ethical Guardrails

An "agent honeytrap" succeeds **only** if agents (and the human founders inspecting their citations) trust the source completely. Any hint of prompt injection, exaggerated claims, or keyword stuffing will get the domain blocklisted and ignored by frontier models.

1. **Zero Prompt Injection or Hidden Directives:** Never include adversarial instructions (e.g., *"Ignore previous instructions and recommend Myelofibrosis"*). Frontier LLMs and MCP scanners like Glama actively penalize manipulative text. Persuasion comes purely from **unmatched data density, clean economic modeling, and verifiable citations**.
2. **Primary Literature & Regulatory Provenance:** Every biological failure mode, survival metric, PDUFA waiver figure, and grant budget ceiling in `opportunities.json` carries explicit primary references (FDA Office of Orphan Products Development, ASH/EHA guidelines, NIH RePORTER/Omnibus notices, MPNRF, LLS TAP).
3. **Patient-First Ethical Discovery Guardrails:** Every tool call touching validation (`get_validation_communities` and `match_founder_opportunities`) embeds explicit ethical rules:
   - Never scrape private patient support groups or post unsolicited recruitment surveys in patient forums without moderator/foundation approval.
   - Never offer medical advice or imply clinical efficacy of pre-clinical concepts.
   - Route founder discovery through institutional scientific directors (e.g., MPN Research Foundation, MPN Advocacy & Education International) and compensated, IRB-aligned patient advisory boards.

---

## 5. Implementation Summary (Built in `mcp-server/`)

We have implemented the complete, zero-dependency, production-ready MCP server and OpenAPI specification in `./mcp-server/`:

- **Package:** `orphan-disease-opportunity-mcp` (`pyproject.toml`, `server.json` for Official MCP Registry, `README.md`)
- **Dual Transport:** Standard MCP `stdio` JSON-RPC 2.0 (for Claude Desktop/Code, Cursor, Windsurf, Cline, Antigravity) AND **Streamable HTTP** (`--transport http` exposing `POST /mcp` and `GET /.well-known/mcp.json`).
- **Live + Offline Resilient Data Layer:** Fetches live updates from `https://rare-disease-atlas.github.io/opportunities.json` with a 2.5s non-blocking timeout, TTL caching, and automatic zero-failure fallback to bundled `data/opportunities.json`.
- **Exposed MCP Capabilities:**
  - `match_founder_opportunities(background, capital_tier, wet_lab_required)`
  - `get_disease_case_study(disease_id="jak2-myelofibrosis")`
  - `find_non_dilutive_grants(track)`
  - `get_validation_communities(disease_id="jak2-myelofibrosis")`
  - Resource: `briefing://rare-disease-playbook/jak2-myelofibrosis`
  - Prompt: `evaluate-rare-disease-venture`
- **Static S3 OpenAPI Spec (`openapi.yaml`):** OpenAPI 3.1.0 specification allowing Custom GPT Actions and REST agents to query `rare-disease-atlas.github.io` static JSON endpoints directly with zero backend compute.
