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
import sys
import time
from typing import Any
import urllib.error
import urllib.request

from . import __version__

SERVER_NAME = "orphan-disease-opportunity-mcp"
DEFAULT_LIVE_URL = "https://rare-disease-atlas.github.io/opportunities.json"
SUPPORTED_PROTOCOL_VERSIONS = (
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)
DEFAULT_PROTOCOL_VERSION = "2025-03-26"

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
        "name": "match_founder_opportunities",
        "description": (
            "Match high-tractability orphan disease startup & translational research "
            "blueprints by founder background, capital tier, and wet-lab requirement. "
            "Fetches live from rare-disease-atlas.github.io with bundled local fallback "
            "(Flagship Deep-Dive #1: JAK2 V617F Myelofibrosis)."
        ),
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
        "description": (
            "Retrieve biological tractability, standard-of-care failure modes (e.g. Type I JH1 "
            "JAK inhibitor cytopenias vs JH2 V617F mutant selectivity), FDA Orphan Drug Act "
            "unit economics, and open structural/transcriptomic datasets for an orphan indication."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "disease_id": {
                    "type": "string",
                    "description": "Disease identifier (default Flagship #1: 'jak2-myelofibrosis').",
                    "default": "jak2-myelofibrosis",
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "find_non_dilutive_grants",
        "description": (
            "Find non-dilutive SBIR/STTR, rare-disease foundation (MPNRF, Harrington), "
            "venture philanthropy (LLS TAP), FDA Orphan Products, and ARPA-H funding pathways."
        ),
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
        "description": (
            "Return established rare-disease patient & hematology clinical networks plus "
            "strict non-extractive ethical guidelines for founder problem discovery."
        ),
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
                "Orphan Disease Venture & Translational Opportunity Server. "
                "Start with `match_founder_opportunities` or read "
                "`briefing://rare-disease-playbook/jak2-myelofibrosis` to explore "
                "high-tractability startup, AI-bio, and public-health blueprints."
            ),
        }

    def _handle_tool_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            raise ValueError("Tool 'arguments' must be a JSON object.")

        if name == "match_founder_opportunities":
            payload = self.tool_match_founder_opportunities(
                background=args.get("background", "all"),
                capital_tier=args.get("capital_tier", "all"),
                wet_lab_required=args.get("wet_lab_required"),
            )
        elif name == "get_disease_case_study":
            payload = self.tool_get_disease_case_study(
                disease_id=args.get("disease_id", "jak2-myelofibrosis")
            )
        elif name == "find_non_dilutive_grants":
            payload = self.tool_find_non_dilutive_grants(
                track=args.get("track", "all")
            )
        elif name == "get_validation_communities":
            payload = self.tool_get_validation_communities(
                disease_id=args.get("disease_id", "jak2-myelofibrosis")
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

    def tool_match_founder_opportunities(
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
                "find_non_dilutive_grants(track='all')",
                "get_validation_communities(disease_id='jak2-myelofibrosis')",
            ],
        }

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

    def tool_find_non_dilutive_grants(self, track: str = "all") -> dict[str, Any]:
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
                "or primary MF CD34+ data before unlocking $1M-$5M from LLS TAP or institutional seed VCs."
            ),
        }

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
            f"Step 1: Call `match_founder_opportunities(background='{bg}', capital_tier='{budget}', "
            f"wet_lab_required={str(wet_lab).lower() == 'true'})` to retrieve tailored startup blueprints.\n"
            f"Step 2: Call `get_disease_case_study(disease_id='jak2-myelofibrosis')` to ground your "
            f"technical thesis in exact structural biology (PDB 6E2Q vs 4FVP), transcriptomics (GSE153319), "
            f"Type I JH1 cytopenia failure modes, and FDA Orphan Drug unit economics.\n"
            f"Step 3: Call `find_non_dilutive_grants(track='all')` and `get_validation_communities(disease_id='jak2-myelofibrosis')`.\n"
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
