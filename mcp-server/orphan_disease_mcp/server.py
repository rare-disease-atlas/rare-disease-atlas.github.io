#!/usr/bin/env python3
"""
Orphan Disease Opportunity MCP Server (Flagship #1: JAK2 V617F Myelofibrosis).

Zero-dependency, spec-compliant Model Context Protocol (MCP) server supporting:
  1. Standard MCP `stdio` JSON-RPC 2.0 transport (default; works out of the box
     in Claude Desktop, Claude Code, Cursor, Windsurf, Cline, Antigravity, etc.)
  2. MCP `Streamable HTTP` transport (`--transport http --port 8080`), exposing
     `POST /mcp`, `GET /.well-known/mcp.json`, and `GET /health`.

Data source strategy:
  Attempts a fast live HTTPS fetch from `https://rare-disease-atlas.github.io/opportunities.json`
  (overridable via `ATLAS_DATA_URL`, disable via `ATLAS_OFFLINE=1`) with TTL caching,
  merging/falling back cleanly to the bundled `data/opportunities.json`.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from . import __version__

SERVER_NAME = "orphan-disease-opportunity-mcp"
DEFAULT_LIVE_URL = "https://api.rare-disease-atlas.workers.dev/opportunities.json"
SUPPORTED_PROTOCOL_VERSIONS = (
    "2026-07-28",
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)
DEFAULT_PROTOCOL_VERSION = "2026-07-28"

BACKGROUND_ALIASES: dict[str, str] = {
    "computational-ai-bio": "computational-ai-bio",
    "computational": "computational-ai-bio",
    "ai-bio": "computational-ai-bio",
    "ai": "computational-ai-bio",
    "ml": "computational-ai-bio",
    "bioinformatics": "computational-ai-bio",
    "comp-bio": "computational-ai-bio",
    "techbio": "computational-ai-bio",
    "public-health": "public-health",
    "public_health": "public-health",
    "health-systems": "public-health",
    "clinical": "public-health",
    "epidemiology": "public-health",
    "digital-health": "public-health",
    "rwe": "public-health",
    "venture-novel-financing": "venture-novel-financing",
    "venture": "venture-novel-financing",
    "vc": "venture-novel-financing",
    "novel-financing": "venture-novel-financing",
    "finance": "venture-novel-financing",
    "studio": "venture-novel-financing",
    "biotech-vc": "venture-novel-financing",
    "all": "all",
    "any": "all",
}

CAPITAL_TIER_ALIASES: dict[str, str] = {
    "bootstrapped-grant": "bootstrapped-grant",
    "bootstrap": "bootstrapped-grant",
    "bootstrapped": "bootstrapped-grant",
    "grant": "bootstrapped-grant",
    "low": "bootstrapped-grant",
    "<250k": "bootstrapped-grant",
    "pre-seed": "bootstrapped-grant",
    "seed": "seed",
    "medium": "seed",
    "series-a-platform": "series-a-platform",
    "series-a": "series-a-platform",
    "platform": "series-a-platform",
    "high": "series-a-platform",
    "all": "all",
    "any": "all",
}

DISEASE_ID_ALIASES: dict[str, str] = {
    "jak2-myelofibrosis": "jak2-myelofibrosis",
    "myelofibrosis": "jak2-myelofibrosis",
    "jak2": "jak2-myelofibrosis",
    "jak2-v617f": "jak2-myelofibrosis",
    "pmf": "jak2-myelofibrosis",
    "mpn": "jak2-myelofibrosis",
    "autoimmune-myelofibrosis": "autoimmune-myelofibrosis",
    "aimf": "autoimmune-myelofibrosis",
    "lupus-myelofibrosis": "autoimmune-myelofibrosis",
    "sle-myelofibrosis": "autoimmune-myelofibrosis",
    "vexas-syndrome": "vexas-syndrome",
    "vexas": "vexas-syndrome",
    "uba1": "vexas-syndrome",
    "castleman-disease": "castleman-disease",
    "castleman": "castleman-disease",
    "imcd": "castleman-disease",
    "tafro": "castleman-disease",
    "systemic-mastocytosis": "systemic-mastocytosis",
    "mastocytosis": "systemic-mastocytosis",
    "kit-d816v": "systemic-mastocytosis",
    "telomere-biology-disorders": "telomere-biology-disorders",
    "telomere": "telomere-biology-disorders",
    "tbd": "telomere-biology-disorders",
    "dyskeratosis-congenita": "telomere-biology-disorders",
    "papd5": "telomere-biology-disorders",
}

GRANT_TRACK_ALIASES: dict[str, str] = {
    "all": "all",
    "any": "all",
    "sbir-sttr": "sbir-sttr",
    "sbir": "sbir-sttr",
    "sttr": "sbir-sttr",
    "nih": "sbir-sttr",
    "foundation": "foundation",
    "philanthropy": "foundation",
    "mpnrf": "foundation",
    "venture-philanthropy": "venture-philanthropy",
    "lls": "venture-philanthropy",
    "lls-tap": "venture-philanthropy",
    "federal-translational": "federal-translational",
    "arpa-h": "federal-translational",
    "regulatory-orphan": "regulatory-orphan",
    "fda": "regulatory-orphan",
    "orphan": "regulatory-orphan",
}


class AtlasRepository:
    """Loads opportunity & disease briefing data with live fetch + bundled fallback."""

    def __init__(
        self,
        bundled_path: Path | None = None,
        live_url: str | None = None,
        cache_ttl_seconds: float = 300.0,
        timeout_seconds: float = 2.5,
    ) -> None:
        if bundled_path is None:
            repo_data = Path(__file__).resolve().parent.parent / "data" / "opportunities.json"
            pkg_data = Path(__file__).resolve().parent / "data" / "opportunities.json"
            bundled_path = repo_data if repo_data.exists() else pkg_data
        self.bundled_path = bundled_path
        self.live_url = live_url or os.environ.get("ATLAS_DATA_URL", DEFAULT_LIVE_URL)
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout_seconds = timeout_seconds
        self._cached_payload: dict[str, Any] | None = None
        self._cached_source: str = "bundled_fallback"
        self._cache_timestamp: float = 0.0

    def load_bundled(self) -> dict[str, Any]:
        with self.bundled_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def get_atlas(self) -> tuple[dict[str, Any], str]:
        now = time.monotonic()
        if (
            self._cached_payload is not None
            and (now - self._cache_timestamp) < self.cache_ttl_seconds
        ):
            return self._cached_payload, self._cached_source

        bundled = self.load_bundled()
        offline_mode = os.environ.get("ATLAS_OFFLINE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        if offline_mode or not self.live_url:
            self._cached_payload = bundled
            self._cached_source = "bundled_fallback"
            self._cache_timestamp = now
            return bundled, "bundled_fallback"

        try:
            req = urllib.request.Request(
                self.live_url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": f"{SERVER_NAME}/{__version__} (+https://rare-disease-atlas.github.io)",
                },
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if 200 <= resp.status < 300:
                    raw = json.loads(resp.read().decode("utf-8"))
                    merged = self._merge_live_with_bundled(raw, bundled)
                    self._cached_payload = merged
                    self._cached_source = "live"
                    self._cache_timestamp = now
                    return merged, "live"
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            pass

        self._cached_payload = bundled
        self._cached_source = "bundled_fallback"
        self._cache_timestamp = now
        return bundled, "bundled_fallback"

    @staticmethod
    def _merge_live_with_bundled(
        live_raw: Any, bundled: dict[str, Any]
    ) -> dict[str, Any]:
        """Normalizes live JSON from S3 while preserving rich bundled sections if omitted."""
        merged = dict(bundled)
        if isinstance(live_raw, list):
            merged["opportunities"] = live_raw
            return merged
        if isinstance(live_raw, dict):
            for key, value in live_raw.items():
                if value is not None:
                    merged[key] = value
        return merged


TOOLS_MANIFEST: list[dict[str, Any]] = [
    {
        "name": "search_founder_opportunities",
        "title": "Search Orphan Disease Startup & Translational Blueprints",
        "description": (
            "Search high-tractability orphan disease startup & translational research "
            "blueprints anchored on Paired Flagships Clonal JAK2 V617F+ Myelofibrosis "
            "and Autoimmune Myelofibrosis (plus 4 comparative cohorts)."
        ),
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "background": {
                    "type": "string",
                    "description": (
                        "Founder domain background: 'computational-ai-bio' (ML, structure/protein design, "
                        "bioinformatics), 'public-health' (RWE, clinical trial matching, care delivery), "
                        "'venture-novel-financing' (asset spin-outs, SPVs, venture philanthropy), or 'all'."
                    ),
                    "default": "all",
                },
                "capital_tier": {
                    "type": "string",
                    "description": (
                        "Target initial capital tier: 'bootstrapped-grant' (<$250K), "
                        "'seed' ($250K-$2.5M), 'series-a-platform' ($2M-$12M+), or 'all'."
                    ),
                    "default": "all",
                },
                "wet_lab_required": {
                    "type": "boolean",
                    "description": (
                        "Set false to return software/AI/RWE or CRO-outsourced blueprints requiring "
                        "zero internal wet lab; true to include wet-lab/asset-spinout plays. Omit for all."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_disease_case_study",
        "title": "Get Curated Orphan Disease Translational Case Study",
        "description": (
            "Retrieve biological tractability, standard-of-care failure modes (Flagships: "
            "'jak2-myelofibrosis' and 'autoimmune-myelofibrosis'), FDA Orphan Drug Act "
            "unit economics, and open structural/transcriptomic datasets."
        ),
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "disease_id": {
                    "type": "string",
                    "description": "Disease identifier (Flagships: 'jak2-myelofibrosis' or 'autoimmune-myelofibrosis').",
                    "default": "jak2-myelofibrosis",
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "list_non_dilutive_grants",
        "title": "List Non-Dilutive SBIR, ARPA-H & Rare Disease Foundation Grants",
        "description": (
            "List non-dilutive SBIR/STTR, rare-disease foundation (MPNRF, CDCN/Every Cure, Harrington), "
            "venture philanthropy (Blood Cancer United TAP), FDA Orphan Products, and ARPA-H funding pathways."
        ),
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "track": {
                    "type": "string",
                    "description": (
                        "Funding track filter: 'all', 'sbir-sttr', 'foundation', "
                        "'venture-philanthropy', 'regulatory-orphan', or 'federal-translational'."
                    ),
                    "default": "all",
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_validation_communities",
        "title": "Get Ethical Patient & Clinical Validation Communities",
        "description": (
            "Return established rare-disease patient & hematology clinical networks plus "
            "strict non-extractive ethical guidelines for founder problem discovery."
        ),
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "disease_id": {
                    "type": "string",
                    "description": "Disease identifier (default: 'jak2-myelofibrosis').",
                    "default": "jak2-myelofibrosis",
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_90_day_validation_plan",
        "title": "Get 90-Day Killer-Experiment & Grant Validation Plan",
        "description": (
            "Retrieve a structured 30/60/90-day validation roadmap, open dataset checklist, "
            "non-dilutive grant stack, and ethical patient advisory protocol anchored on "
            "Paired Myelofibrosis Flagships ('jak2-myelofibrosis' and 'autoimmune-myelofibrosis')."
        ),
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "disease_id": {
                    "type": "string",
                    "description": "Target disease slug (default: 'jak2-myelofibrosis').",
                    "default": "jak2-myelofibrosis",
                },
                "background": {
                    "type": "string",
                    "description": "Founder track: 'computational-ai-bio', 'public-health', or 'venture-novel-financing'.",
                    "default": "computational-ai-bio",
                },
                "capital_tier": {
                    "type": "string",
                    "description": "Initial budget tier: 'bootstrapped-grant', 'seed', or 'series-a-platform'.",
                    "default": "bootstrapped-grant",
                },
                "wet_lab_required": {
                    "type": "boolean",
                    "description": "Whether internal wet lab is available (default: false).",
                    "default": False,
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "search_any_orphan_indication",
        "title": "Search & Benchmark Any of 7,000+ Orphan Indications Live",
        "description": (
            "Run live diligence on any of 7,000+ rare diseases via OpenTargets, "
            "ClinicalTrials.gov v2, and PubMed, benchmarked against our Myelofibrosis flagships."
        ),
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "disease_query": {
                    "type": "string",
                    "description": "Any rare disease name (e.g., 'JAK2 V617F myelofibrosis', 'autoimmune myelofibrosis', 'Duchenne muscular dystrophy').",
                },
                "founder_background": {
                    "type": "string",
                    "description": "Optional track: 'computational-ai-bio', 'public-health', 'venture-novel-financing', or 'all'.",
                    "default": "all",
                },
            },
            "required": ["disease_query"],
            "additionalProperties": False,
        },
    },
]

RESOURCES_MANIFEST: list[dict[str, Any]] = [
    {
        "uri": "briefing://rare-disease-playbook/jak2-myelofibrosis",
        "name": "JAK2+ Myelofibrosis Venture & Translational Playbook (Flagship #1)",
        "description": (
            "Complete founder & AI-agent briefing covering JAK2 V617F JH2 biology, "
            "ruxolitinib failure cliff, Orphan Drug unit economics, startup wedges, "
            "non-dilutive capital stack, and ethical patient-partnered validation."
        ),
        "mimeType": "text/markdown",
    }
]

RESOURCE_TEMPLATES_MANIFEST: list[dict[str, Any]] = [
    {
        "uriTemplate": "briefing://rare-disease-playbook/{disease_id}",
        "name": "Rare Disease Venture Playbook by Indication",
        "description": "Retrieve the structured markdown venture briefing for a specific disease_id (e.g., jak2-myelofibrosis).",
        "mimeType": "text/markdown",
    }
]

PROMPTS_MANIFEST: list[dict[str, Any]] = [
    {
        "name": "evaluate-rare-disease-venture",
        "description": (
            "Generate a rigorous 90-day biotech, AI-bio, or public-health venture "
            "evaluation plan tailored to a founder's background and capital constraints, "
            "using JAK2+ Myelofibrosis as the reference orphan indication."
        ),
        "arguments": [
            {
                "name": "founder_background",
                "description": "e.g., computational-ai-bio, public-health, or venture-novel-financing",
                "required": False,
            },
            {
                "name": "capital_budget",
                "description": "e.g., bootstrapped-grant (<$250K), seed ($250K-$2.5M), or series-a-platform",
                "required": False,
            },
            {
                "name": "wet_lab_access",
                "description": "'true' or 'false' indicating internal wet-lab access",
                "required": False,
            },
        ],
    }
]


class OrphanDiseaseMCPServer:
    """Core MCP protocol handler independent of wire transport."""

    def __init__(self, repository: AtlasRepository | None = None) -> None:
        self.repo = repository or AtlasRepository()

    def handle_jsonrpc(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single JSON-RPC 2.0 request or notification."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return self._error_response(
                message.get("id") if isinstance(message, dict) else None,
                -32600,
                "Invalid JSON-RPC 2.0 request.",
            )

        method = message.get("method")
        req_id = message.get("id")
        is_notification = "id" not in message
        params = message.get("params") or {}

        if is_notification:
            # Notifications (e.g. notifications/initialized) produce no response.
            return None

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS_MANIFEST}
            elif method == "tools/call":
                result = self._handle_tool_call(params)
            elif method == "resources/list":
                result = {"resources": RESOURCES_MANIFEST}
            elif method == "resources/templates/list":
                result = {"resourceTemplates": RESOURCE_TEMPLATES_MANIFEST}
            elif method == "resources/read":
                result = self._handle_resource_read(params)
            elif method == "prompts/list":
                result = {"prompts": PROMPTS_MANIFEST}
            elif method == "prompts/get":
                result = self._handle_prompt_get(params)
            else:
                return self._error_response(
                    req_id, -32601, f"Method not found: {method}"
                )
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except ValueError as exc:
            return self._error_response(req_id, -32602, str(exc))
        except Exception as exc:  # pragma: no cover - defensive guard
            return self._error_response(req_id, -32603, f"Internal error: {exc}")

    @staticmethod
    def _error_response(req_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        requested = params.get("protocolVersion", DEFAULT_PROTOCOL_VERSION)
        negotiated = (
            requested
            if requested in SUPPORTED_PROTOCOL_VERSIONS
            else DEFAULT_PROTOCOL_VERSION
        )
        return {
            "protocolVersion": negotiated,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": __version__,
            },
            "instructions": (
                "Orphan Disease Venture & Translational Opportunity Server (v1.6.0). "
                "Start with `search_founder_opportunities` or read "
                "`briefing://rare-disease-playbook/jak2-myelofibrosis` to explore "
                "high-tractability startup, AI-bio, and public-health blueprints."
            ),
        }

    def _handle_tool_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            raise ValueError("Tool 'arguments' must be a JSON object.")

        if name in ("search_any_orphan_indication", "analyze_any_orphan_indication"):
            payload = self.tool_search_any_orphan_indication(
                disease_query=str(args.get("disease_query") or args.get("disease_id") or ""),
                founder_background=str(args.get("founder_background", "all")),
            )
        elif name in ("search_founder_opportunities", "match_founder_opportunities"):
            payload = self.tool_search_founder_opportunities(
                background=args.get("background", "all"),
                capital_tier=args.get("capital_tier", "all"),
                wet_lab_required=args.get("wet_lab_required"),
            )
        elif name == "get_disease_case_study":
            payload = self.tool_get_disease_case_study(
                disease_id=args.get("disease_id", "jak2-myelofibrosis")
            )
        elif name in ("list_non_dilutive_grants", "find_non_dilutive_grants"):
            payload = self.tool_list_non_dilutive_grants(
                track=args.get("track", "all")
            )
        elif name == "get_validation_communities":
            payload = self.tool_get_validation_communities(
                disease_id=args.get("disease_id", "jak2-myelofibrosis")
            )
        elif name in (
            "get_90_day_validation_plan",
            "generate_90_day_validation_plan",
            "build_90_day_validation_plan",
        ):
            payload = self.tool_get_90_day_validation_plan(
                disease_id=str(args.get("disease_id", "jak2-myelofibrosis")),
                background=str(args.get("background", "computational-ai-bio")),
                capital_tier=str(args.get("capital_tier", "bootstrapped-grant")),
                wet_lab_required=bool(args.get("wet_lab_required", False)),
            )
        elif name == "submit_atlas_feedback":
            payload = self.tool_submit_atlas_feedback(
                summary=str(args.get("summary", "")),
                signal_type=str(args.get("signal_type", "missing-wedge")),
                founder_background=str(args.get("founder_background", "unspecified")),
                disease_id=str(args.get("disease_id", "jak2-myelofibrosis")),
                agent_client=str(args.get("agent_client", "mcp-agent")),
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

        is_err = bool(payload.get("error"))
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(payload, indent=2),
                }
            ],
            "structuredContent": payload,
            "isError": is_err,
        }

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def tool_search_any_orphan_indication(
        self,
        disease_query: str,
        founder_background: str = "all",
    ) -> dict[str, Any]:
        q = self._scrub_pii(disease_query)[:120].strip()
        if not q:
            return {"error": "Parameter 'disease_query' must not be empty."}
        atlas, data_source = self.repo.get_atlas()
        norm_key = DISEASE_ID_ALIASES.get(q.lower())
        curated_match = norm_key if (norm_key and norm_key in atlas.get("case_studies", {})) else None
        if not curated_match:
            ql = q.lower()
            for slug, cs in atlas.get("case_studies", {}).items():
                if ql in slug or ql in str(cs.get("name", "")).lower():
                    curated_match = slug
                    break

        offline_mode = os.environ.get("ATLAS_OFFLINE", "").strip().lower() in ("1", "true", "yes")
        live_diligence: dict[str, Any] = {
            "resolved_name": q,
            "clinical_trials": [],
            "top_associated_targets": [],
        }
        if not offline_mode:
            try:
                ct_url = f"https://clinicaltrials.gov/api/v2/studies?query.cond={urllib.parse.quote(q)}&pageSize=5&countTotal=true"
                req = urllib.request.Request(ct_url, headers={"Accept": "application/json", "User-Agent": f"{SERVER_NAME}/{__version__}"})
                with urllib.request.urlopen(req, timeout=4.0) as resp:
                    ct = json.loads(resp.read().decode("utf-8"))
                    live_diligence["total_clinical_trials"] = ct.get("totalCount", len(ct.get("studies", [])))
                    live_diligence["clinical_trials"] = [
                        {
                            "nct_id": s.get("protocolSection", {}).get("identificationModule", {}).get("nctId"),
                            "status": s.get("protocolSection", {}).get("statusModule", {}).get("overallStatus"),
                            "title": s.get("protocolSection", {}).get("identificationModule", {}).get("briefTitle"),
                        }
                        for s in ct.get("studies", [])
                    ]
            except Exception:
                pass

        norm_bg = BACKGROUND_ALIASES.get(founder_background.strip().lower(), "all")
        grants = [
            g for g in atlas.get("non_dilutive_grants", [])
            if norm_bg == "all" or norm_bg in g.get("best_for_backgrounds", [])
        ]
        return {
            "query": q,
            "data_source": data_source,
            "curated_atlas_match": curated_match,
            "curated_case_study": atlas.get("case_studies", {}).get(curated_match) if curated_match else None,
            "live_diligence": live_diligence,
            "fda_orphan_unit_economics": {
                "market_exclusivity": "7 years FDA Orphan Drug exclusivity (10 years EMA)",
                "fy2026_pdufa_fee_waiver_usd": "$4,682,003 (100% waived)",
                "clinical_trial_tax_credit": "25% federal QCTE tax credit",
            },
            "matched_grants": grants[:5],
            "flagship_myelofibrosis_benchmarks": [
                "jak2-myelofibrosis (Clonal JAK2 V617F+ JH2 vs JH1 Primary Myelofibrosis)",
                "autoimmune-myelofibrosis (Reversible AIMF 74-80% marrow fibrosis resolution + dual iron overload)",
            ],
        }

    tool_analyze_any_orphan_indication = tool_search_any_orphan_indication

    def tool_search_founder_opportunities(
        self,
        background: str = "all",
        capital_tier: str = "all",
        wet_lab_required: bool | None = None,
    ) -> dict[str, Any]:
        atlas, data_source = self.repo.get_atlas()
        raw_opps = atlas.get("opportunities", [])

        norm_bg = BACKGROUND_ALIASES.get(
            str(background).strip().lower(), str(background).strip().lower()
        )
        norm_cap = CAPITAL_TIER_ALIASES.get(
            str(capital_tier).strip().lower(), str(capital_tier).strip().lower()
        )

        matched: list[dict[str, Any]] = []
        for opp in raw_opps:
            opp_bgs = [b.lower() for b in opp.get("backgrounds", [])]
            if norm_bg not in ("all", "") and opp_bgs and norm_bg not in opp_bgs:
                continue

            opp_cap = str(opp.get("capital_tier", "")).lower()
            if norm_cap not in ("all", "") and opp_cap and opp_cap != norm_cap:
                continue

            if wet_lab_required is not None:
                opp_wet = bool(opp.get("wet_lab_required", False))
                # If founder requires NO wet lab (wet_lab_required=False), filter strictly to wet_lab_required == False.
                # If wet_lab_required=True, verify exact boolean match.
                if opp_wet != bool(wet_lab_required):
                    continue

            matched.append(opp)

        return {
            "atlas_name": atlas.get("atlas_name"),
            "data_source": data_source,
            "canonical_url": atlas.get("canonical_url", DEFAULT_LIVE_URL),
            "filters_applied": {
                "background": norm_bg,
                "capital_tier": norm_cap,
                "wet_lab_required": wet_lab_required,
            },
            "matched_count": len(matched),
            "opportunities": matched,
            "next_recommended_calls": [
                "get_disease_case_study(disease_id='jak2-myelofibrosis')",
                "get_disease_case_study(disease_id='autoimmune-myelofibrosis')",
                "list_non_dilutive_grants(track='all')",
                "get_validation_communities(disease_id='jak2-myelofibrosis')",
                "get_90_day_validation_plan(disease_id='jak2-myelofibrosis')",
            ],
        }

    tool_match_founder_opportunities = tool_search_founder_opportunities

    def tool_get_disease_case_study(
        self, disease_id: str = "jak2-myelofibrosis"
    ) -> dict[str, Any]:
        atlas, data_source = self.repo.get_atlas()
        norm_id = DISEASE_ID_ALIASES.get(
            str(disease_id).strip().lower(), str(disease_id).strip().lower()
        )
        studies = atlas.get("case_studies", {})
        study = studies.get(norm_id)
        if not study:
            return {
                "error": f"Disease '{disease_id}' is not yet in the V1 atlas.",
                "available_disease_ids": list(studies.keys()),
                "contribution_note": (
                    "Flagship #1 is 'jak2-myelofibrosis'. Community contributions for "
                    "additional high-tractability orphan indications are welcome at "
                    "https://rare-disease-atlas.github.io."
                ),
            }
        return {
            "data_source": data_source,
            "case_study": study,
        }

    def tool_list_non_dilutive_grants(self, track: str = "all") -> dict[str, Any]:
        atlas, data_source = self.repo.get_atlas()
        norm_track = GRANT_TRACK_ALIASES.get(
            str(track).strip().lower(), str(track).strip().lower()
        )
        all_grants = atlas.get("non_dilutive_grants", [])
        if norm_track in ("all", ""):
            filtered = all_grants
        else:
            filtered = [
                g
                for g in all_grants
                if str(g.get("track", "")).lower() == norm_track
            ]
        return {
            "data_source": data_source,
            "track_filter": norm_track,
            "available_tracks": [
                "sbir-sttr",
                "foundation",
                "venture-philanthropy",
                "regulatory-orphan",
                "federal-translational",
            ],
            "grant_count": len(filtered),
            "grants": filtered,
            "capital_stacking_strategy": (
                "Founders commonly pair an MPNRF Seed/Challenge Grant ($100K-$300K) + "
                "NCI/NHLBI Phase I SBIR ($400K, 0% dilution) to generate killer JH2-selectivity "
                "or primary MF CD34+ data before unlocking $1M-$5M from Blood Cancer United TAP or institutional seed VCs."
            ),
        }

    tool_find_non_dilutive_grants = tool_list_non_dilutive_grants

    def tool_get_90_day_validation_plan(
        self,
        disease_id: str = "jak2-myelofibrosis",
        background: str = "computational-ai-bio",
        capital_tier: str = "bootstrapped-grant",
        wet_lab_required: bool = False,
    ) -> dict[str, Any]:
        atlas, data_source = self.repo.get_atlas()
        norm_id = DISEASE_ID_ALIASES.get(
            str(disease_id).strip().lower(), str(disease_id).strip().lower()
        )
        norm_bg = BACKGROUND_ALIASES.get(
            str(background).strip().lower(), "computational-ai-bio"
        )
        norm_cap = CAPITAL_TIER_ALIASES.get(
            str(capital_tier).strip().lower(), "bootstrapped-grant"
        )
        studies = atlas.get("case_studies", {})
        study = studies.get(norm_id) or studies.get("jak2-myelofibrosis", {})
        resolved_id = str(study.get("disease_id", norm_id or "jak2-myelofibrosis"))

        disease_opps = [
            o for o in atlas.get("opportunities", []) if o.get("disease_id") == resolved_id
        ]
        matched_opps = [
            o
            for o in disease_opps
            if (norm_bg == "all" or norm_bg in [b.lower() for b in o.get("backgrounds", [])])
            and (not wet_lab_required and not bool(o.get("wet_lab_required", False)) or wet_lab_required)
        ] or disease_opps[:2]

        primary_opp = matched_opps[0] if matched_opps else {}
        milestones = primary_opp.get("first_90_days_milestones", [
            "Days 1-30: Benchmark open structural/transcriptomic accessions (PDB 4FVR/6E2Q vs WT 4FVP; GEO GSE144568, GSE122198).",
            "Days 31-60: Execute fee-for-service CRO selectivity or SMART-on-FHIR de-identified RWE pilot.",
            "Days 61-90: Submit non-dilutive NCI/NHLBI SBIR Phase I + MPNRF LOI and conduct FMV-compensated ($100-$250/hr) foundation-routed advisory review.",
        ])
        grants = atlas.get("non_dilutive_grants", [])[:4]
        val_group = atlas.get("validation_communities", {}).get(resolved_id, {})

        return {
            "data_source": data_source,
            "disease_id": resolved_id,
            "disease_name": study.get("name", resolved_id),
            "founder_profile": {
                "background": norm_bg,
                "capital_tier": norm_cap,
                "wet_lab_required": wet_lab_required,
            },
            "anchor_opportunity_id": primary_opp.get("id"),
            "anchor_opportunity_title": primary_opp.get("title"),
            "phases": {
                "days_1_to_30_in_silico_and_evidence": milestones[:1],
                "days_31_to_60_killer_experiment": milestones[1:2] or milestones[:1],
                "days_61_to_90_grant_and_clinical_validation": milestones[2:] or milestones[-1:],
            },
            "open_datasets": primary_opp.get("open_datasets", []),
            "recommended_grant_stack": [
                {"id": g.get("id"), "name": g.get("name"), "typical_award_usd": g.get("typical_award_usd")}
                for g in grants
            ],
            "ethical_validation_communities": val_group.get("institutional_and_patient_communities", []),
            "ethical_discovery_guidelines": val_group.get("ethical_discovery_guidelines", []),
        }

    tool_generate_90_day_validation_plan = tool_get_90_day_validation_plan

    def tool_get_validation_communities(
        self, disease_id: str = "jak2-myelofibrosis"
    ) -> dict[str, Any]:
        atlas, data_source = self.repo.get_atlas()
        norm_id = DISEASE_ID_ALIASES.get(
            str(disease_id).strip().lower(), str(disease_id).strip().lower()
        )
        communities_map = atlas.get("validation_communities", {})
        entry = communities_map.get(norm_id)
        if not entry:
            return {
                "error": f"No validation communities found for '{disease_id}'.",
                "available_disease_ids": list(communities_map.keys()),
            }
        return {
            "data_source": data_source,
            **entry,
        }

    @staticmethod
    def _scrub_pii(text: str) -> str:
        """Strip accidental email addresses or phone numbers before outbound transmission."""
        cleaned = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", text)
        cleaned = re.sub(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[redacted-phone]", cleaned)
        return cleaned.strip()[:1000]

    def tool_submit_atlas_feedback(
        self,
        summary: str,
        signal_type: str = "missing-wedge",
        founder_background: str = "unspecified",
        disease_id: str = "jak2-myelofibrosis",
        agent_client: str = "mcp-agent",
    ) -> dict[str, Any]:
        clean_summary = self._scrub_pii(summary)
        if not clean_summary:
            return {"error": "Feedback summary must not be empty."}

        allowed_types = {
            "missing-wedge",
            "citation-errata",
            "new-dataset",
            "disease-expansion",
            "usage-feedback",
        }
        norm_signal = signal_type.strip().lower()
        if norm_signal not in allowed_types:
            norm_signal = "usage-feedback"

        atlas, _ = self.repo.get_atlas()
        webhook_url = (
            os.environ.get("ATLAS_FEEDBACK_URL", "").strip()
            or str(atlas.get("feedback_webhook_url", "")).strip()
        )
        offline_mode = os.environ.get("ATLAS_OFFLINE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )

        record = {
            "schema": "atlas-agent-signal/v1",
            "signal_type": norm_signal,
            "founder_background": self._scrub_pii(founder_background)[:80] or "unspecified",
            "disease_id": self._scrub_pii(disease_id)[:80] or "jak2-myelofibrosis",
            "agent_client": self._scrub_pii(agent_client)[:80] or "mcp-agent",
            "summary": clean_summary,
            "mcp_version": __version__,
        }

        webhook_delivered = False
        webhook_receipt = None
        if webhook_url and not offline_mode:
            try:
                req = urllib.request.Request(
                    webhook_url,
                    data=json.dumps(record).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "User-Agent": f"{SERVER_NAME}/{__version__}",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    if 200 <= resp.status < 300:
                        webhook_delivered = True
                        try:
                            webhook_receipt = json.loads(resp.read().decode("utf-8"))
                        except ValueError:
                            webhook_receipt = {"status": resp.status}
            except (urllib.error.URLError, TimeoutError, OSError):
                webhook_delivered = False

        issue_title = f"[Agent Signal: {norm_signal}] {record['disease_id']} ({record['founder_background']})"
        issue_body = (
            f"### Structured Agent / Builder Signal\n"
            f"- **Signal Type:** `{norm_signal}`\n"
            f"- **Disease Scope:** `{record['disease_id']}`\n"
            f"- **Founder Background:** `{record['founder_background']}`\n"
            f"- **Agent / Client:** `{record['agent_client']}` (`mcp v{__version__}`)\n\n"
            f"### Summary (Zero PII / Zero Confidential IP)\n"
            f"{clean_summary}\n"
        )
        query = urllib.parse.urlencode(
            {
                "labels": "agent-signal",
                "title": issue_title,
                "body": issue_body,
            }
        )
        prefilled_issue_url = (
            f"https://github.com/rare-disease-atlas/rare-disease-atlas.github.io/issues/new?{query}"
        )

        return {
            "status": "delivered_via_webhook" if webhook_delivered else "ready_for_github_issue_submission",
            "webhook_delivered": webhook_delivered,
            "webhook_receipt": webhook_receipt,
            "sanitized_signal": record,
            "prefilled_github_issue_url": prefilled_issue_url,
            "gh_cli_command": (
                "gh issue create --repo rare-disease-atlas/rare-disease-atlas.github.io "
                f"--label agent-signal --title {json.dumps(issue_title)} --body {json.dumps(issue_body)}"
            ),
            "privacy_note": "Emails and phone numbers are automatically redacted. Never submit patient PHI or confidential IP.",
        }

    # ------------------------------------------------------------------
    # Resources & Prompts
    # ------------------------------------------------------------------

    def _handle_resource_read(self, params: dict[str, Any]) -> dict[str, Any]:
        uri = str(params.get("uri", "")).strip()
        prefix = "briefing://rare-disease-playbook/"
        if not uri.startswith(prefix):
            raise ValueError(f"Unsupported resource URI: {uri}")

        disease_slug = uri[len(prefix) :].strip("/") or "jak2-myelofibrosis"
        norm_id = DISEASE_ID_ALIASES.get(disease_slug.lower(), disease_slug.lower())

        atlas, data_source = self.repo.get_atlas()
        study = atlas.get("case_studies", {}).get(norm_id)
        if not study:
            raise ValueError(
                f"Playbook not found for '{disease_slug}'. Available: jak2-myelofibrosis"
            )

        markdown = self._render_playbook_markdown(atlas, study, data_source)
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": markdown,
                }
            ]
        }

    @staticmethod
    def _render_playbook_markdown(
        atlas: dict[str, Any], study: dict[str, Any], data_source: str
    ) -> str:
        opps = [
            o
            for o in atlas.get("opportunities", [])
            if o.get("disease_id") == study.get("disease_id")
        ]
        grants = atlas.get("non_dilutive_grants", [])
        val = atlas.get("validation_communities", {}).get(study.get("disease_id"), {})

        lines = [
            f"# {study['name']} — Venture & Translational Playbook",
            f"_Source: {atlas.get('canonical_url', DEFAULT_LIVE_URL)} ({data_source})_",
            "",
            "## 1. Why This Orphan Indication Is Uniquely Tractable Right Now",
            f"- **Causal Driver:** {study['biological_tractability']['causal_mechanism']}",
            f"- **US Prevalence:** {study['epidemiology']['us_prevalence_estimate']}",
            f"- **Post-Ruxolitinib Survival Cliff:** {study['epidemiology']['median_survival']}",
            "",
            "### Structural & Translational Anchors",
        ]
        for bullet in study["biological_tractability"]["why_highly_tractable_now"]:
            lines.append(f"- {bullet}")

        lines.extend(["", "## 2. Standard-of-Care Failure Modes"])
        for mode in study["standard_of_care_failure_modes"]["core_failure_mechanisms"]:
            lines.append(f"- {mode}")

        lines.extend(["", "## 3. FDA Orphan Drug & Commercial Economics"])
        for inc in study["regulatory_and_commercial_incentives"]["fda_orphan_drug_act"]:
            lines.append(f"- {inc}")
        lines.append(
            f"- **Pivotal Trial Efficiency:** {study['regulatory_and_commercial_incentives']['trial_efficiency']}"
        )
        lines.append(
            f"- **M&A Benchmarks:** {study['regulatory_and_commercial_incentives']['commercial_precedents']}"
        )

        lines.extend(["", "## 4. High-Conviction Founder Blueprints"])
        for opp in opps:
            lines.append(
                f"### {opp['title']} (`{opp['id']}`)\n"
                f"- **Tracks:** {', '.join(opp['backgrounds'])} | **Capital Tier:** `{opp['capital_tier']}` ({opp['capital_range_usd']}) | **Internal Wet Lab Required:** `{opp['wet_lab_required']}`\n"
                f"- **Wedge:** {opp['problem_wedge']}\n"
                f"- **Blueprint:** {opp['solution_blueprint']}"
            )

        lines.extend(["", "## 5. Non-Dilutive & Venture-Philanthropy Capital Stack"])
        for g in grants:
            lines.append(
                f"- **{g['name']}** (`{g['track']}`): {g['typical_award_usd']} — {g['equity_dilution']}"
            )

        lines.extend(["", "## 6. Ethical Patient & Clinical Validation Rules"])
        for rule in val.get("ethical_discovery_guidelines", []):
            lines.append(f"- {rule}")

        return "\n".join(lines) + "\n"

    def _handle_prompt_get(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if name != "evaluate-rare-disease-venture":
            raise ValueError(f"Unknown prompt: {name}")

        args = params.get("arguments") or {}
        bg = args.get("founder_background", "computational-ai-bio")
        budget = args.get("capital_budget", "bootstrapped-grant")
        wet_lab = args.get("wet_lab_access", "false")

        prompt_text = (
            f"You are evaluating a high-impact biotech, AI-bio, or public-health startup opportunity "
            f"for a founder team with background='{bg}', capital_budget='{budget}', and "
            f"internal_wet_lab_access={wet_lab}.\n\n"
            f"Step 1: Call `search_founder_opportunities(background='{bg}', capital_tier='{budget}', "
            f"wet_lab_required={str(wet_lab).lower() == 'true'})` to retrieve tailored startup blueprints.\n"
            f"Step 2: Call `get_disease_case_study(disease_id='jak2-myelofibrosis')` and "
            f"`get_disease_case_study(disease_id='autoimmune-myelofibrosis')` to ground your "
            f"technical thesis in exact structural biology (PDB 4FVR/6E2Q vs 4FVP), transcriptomics (GSE144568, GSE122198), "
            f"Type I JH1 cytopenia failure modes, AIMF 74-80% marrow fibrosis reversal + dual iron overload, and FDA Orphan Drug unit economics.\n"
            f"Step 3: Call `list_non_dilutive_grants(track='all')`, `get_validation_communities(disease_id='jak2-myelofibrosis')`, "
            f"and `get_90_day_validation_plan(disease_id='jak2-myelofibrosis', background='{bg}', capital_tier='{budget}')`.\n"
            f"Step 4: Synthesize a concrete 90-day killer-experiment & grant-stacking execution plan "
            f"that strictly respects non-extractive patient discovery ethics."
        )
        return {
            "description": "90-day translational & venture evaluation workflow for JAK2+ Myelofibrosis",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt_text,
                    },
                }
            ],
        }


# ----------------------------------------------------------------------
# Transports: 1) stdio (newline-delimited + Content-Length compatible)
#             2) Streamable HTTP (POST /mcp + GET /.well-known/mcp.json)
# ----------------------------------------------------------------------


def run_stdio(mcp_server: OrphanDiseaseMCPServer) -> None:
    """Run standard MCP stdio loop supporting newline-delimited JSON-RPC 2.0."""
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        line = stdin.readline()
        if not line:
            break

        stripped = line.strip()
        if not stripped:
            continue

        # Support optional Content-Length header framing if sent by legacy harnesses
        if stripped.lower().startswith(b"content-length:"):
            length = int(stripped.split(b":", 1)[1].strip())
            while True:
                hdr = stdin.readline()
                if not hdr or hdr in (b"\r\n", b"\n"):
                    break
            body = stdin.read(length)
            raw_text = body.decode("utf-8")
        else:
            raw_text = stripped.decode("utf-8")

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            err = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
            stdout.write((json.dumps(err) + "\n").encode("utf-8"))
            stdout.flush()
            continue

        if isinstance(payload, list):
            responses = [
                r for item in payload if (r := mcp_server.handle_jsonrpc(item)) is not None
            ]
            if responses:
                stdout.write((json.dumps(responses) + "\n").encode("utf-8"))
                stdout.flush()
        else:
            response = mcp_server.handle_jsonrpc(payload)
            if response is not None:
                stdout.write((json.dumps(response) + "\n").encode("utf-8"))
                stdout.flush()


def create_http_server(
    mcp_server: OrphanDiseaseMCPServer, host: str = "127.0.0.1", port: int = 8080
) -> ThreadingHTTPServer:
    """Create a Streamable HTTP MCP server exposing POST /mcp & /.well-known/mcp.json."""

    class MCPHTTPHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            # Keep stderr clean unless verbose debugging is enabled
            if os.environ.get("MCP_HTTP_VERBOSE"):
                super().log_message(format, *args)

        def _send_json(self, status: int, body: Any) -> None:
            encoded = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "Content-Type, Accept, Mcp-Session-Id",
            )
            self.end_headers()
            self.wfile.write(encoded)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "Content-Type, Accept, Mcp-Session-Id",
            )
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send_json(
                    200, {"status": "ok", "server": SERVER_NAME, "version": __version__}
                )
            elif self.path == "/.well-known/mcp.json":
                self._send_json(
                    200,
                    {
                        "name": SERVER_NAME,
                        "version": __version__,
                        "description": "Orphan Disease Venture & Translational Opportunity MCP Server (Flagship #1: JAK2+ Myelofibrosis)",
                        "homepage": "https://rare-disease-atlas.github.io",
                        "transport": {
                            "type": "streamable-http",
                            "endpoint": "/mcp",
                        },
                        "tools": [t["name"] for t in TOOLS_MANIFEST],
                        "resources": [r["uri"] for r in RESOURCES_MANIFEST],
                        "prompts": [p["name"] for p in PROMPTS_MANIFEST],
                    },
                )
            else:
                self._send_json(
                    404,
                    {
                        "error": "Not found. Send JSON-RPC 2.0 POST requests to /mcp or GET /.well-known/mcp.json"
                    },
                )

        def do_POST(self) -> None:  # noqa: N802
            if self.path not in ("/mcp", "/"):
                self._send_json(404, {"error": "MCP endpoint is POST /mcp"})
                return

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                self._send_json(
                    400,
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    },
                )
                return

            if isinstance(payload, list):
                responses = [
                    r
                    for item in payload
                    if (r := mcp_server.handle_jsonrpc(item)) is not None
                ]
                if not responses:
                    self.send_response(202)
                    self.end_headers()
                    return
                self._send_json(200, responses)
            else:
                response = mcp_server.handle_jsonrpc(payload)
                if response is None:
                    self.send_response(202)
                    self.end_headers()
                    return
                self._send_json(200, response)

    return ThreadingHTTPServer((host, port), MCPHTTPHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orphan-disease-mcp",
        description="Orphan Disease Opportunity MCP Server (Flagship #1: JAK2+ Myelofibrosis)",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="MCP transport mode: 'stdio' (default) or Streamable 'http'",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host when --transport http is selected (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Bind port when --transport http is selected (default: 8080)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use bundled data/opportunities.json without attempting live HTTPS fetch",
    )
    args = parser.parse_args(argv)

    if args.offline:
        os.environ["ATLAS_OFFLINE"] = "1"

    server = OrphanDiseaseMCPServer()
    if args.transport == "http":
        httpd = create_http_server(server, host=args.host, port=args.port)
        sys.stderr.write(
            f"[{SERVER_NAME}] Streamable HTTP listening on http://{args.host}:{args.port}/mcp\n"
        )
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
        return 0

    run_stdio(server)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
