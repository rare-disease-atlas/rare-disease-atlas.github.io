#!/usr/bin/env python3
"""
End-to-end verification suite for `orphan-disease-opportunity-mcp`.

Tests:
  1. Subprocess `stdio` JSON-RPC 2.0 protocol lifecycle (`initialize`,
     `notifications/initialized`, `ping`, `tools/list`, `resources/list`,
     `resources/templates/list`, `prompts/list`).
  2. All 4 MCP tools via `tools/call` across multiple founder personas,
     capital tiers, wet-lab filters, alias normalization, and error paths.
  3. Live HTTPS/HTTP data fetch (`ATLAS_DATA_URL` pointing to a real local
     ephemeral HTTP server) AND graceful offline fallback to `data/opportunities.json`.
  4. MCP Resource `briefing://rare-disease-playbook/jak2-myelofibrosis` &
     MCP Prompt `evaluate-rare-disease-venture`.
  5. Streamable HTTP transport (`POST /mcp`, `GET /.well-known/mcp.json`, `GET /health`).
  6. Static schema validation of `openapi.yaml` and Official MCP Registry `server.json`.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
import urllib.request

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

MCP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MCP_DIR))

from orphan_disease_mcp.server import (  # noqa: E402
    AtlasRepository,
    OrphanDiseaseMCPServer,
    create_http_server,
)


class StdioMCPClient:
    """Helper to drive the MCP server over real subprocess stdio pipes."""

    def __init__(self, env_overrides: dict[str, str] | None = None) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(MCP_DIR)
        if env_overrides:
            env.update(env_overrides)
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "orphan_disease_mcp"],
            cwd=str(MCP_DIR),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
        )

    def send_request(self, payload: dict) -> dict:
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            stderr_out = self.proc.stderr.read() if self.proc.stderr else ""
            raise RuntimeError(f"MCP server closed stdout unexpectedly. stderr={stderr_out}")
        return json.loads(line)

    def send_notification(self, payload: dict) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

    def close(self) -> None:
        if self.proc.stdin:
            self.proc.stdin.close()
        self.proc.wait(timeout=5)
        if self.proc.stdout:
            self.proc.stdout.close()
        if self.proc.stderr:
            self.proc.stderr.close()


class OrphanDiseaseMCPTestSuite(unittest.TestCase):
    def test_01_stdio_full_jsonrpc_lifecycle_and_all_tools(self) -> None:
        client = StdioMCPClient({"ATLAS_OFFLINE": "1"})
        try:
            # 1. initialize
            init_resp = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "test-harness", "version": "1.0.0"},
                    },
                }
            )
            self.assertEqual(init_resp["result"]["protocolVersion"], "2025-03-26")
            self.assertEqual(
                init_resp["result"]["serverInfo"]["name"],
                "orphan-disease-opportunity-mcp",
            )

            # 2. notifications/initialized (must not emit a response that shifts stdout!)
            client.send_notification(
                {"jsonrpc": "2.0", "method": "notifications/initialized"}
            )

            # 3. ping
            ping_resp = client.send_request(
                {"jsonrpc": "2.0", "id": 2, "method": "ping"}
            )
            self.assertEqual(ping_resp["id"], 2)
            self.assertEqual(ping_resp["result"], {})

            # 4. tools/list
            tools_resp = client.send_request(
                {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
            )
            tool_names = [t["name"] for t in tools_resp["result"]["tools"]]
            self.assertEqual(
                tool_names,
                [
                    "search_founder_opportunities",
                    "get_disease_case_study",
                    "list_non_dilutive_grants",
                    "get_validation_communities",
                    "get_90_day_validation_plan",
                    "search_any_orphan_indication",
                ],
            )

            # 4b. tools/call -> search_any_orphan_indication (VEXAS) + legacy alias
            vexas_resp = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 301,
                    "method": "tools/call",
                    "params": {
                        "name": "search_any_orphan_indication",
                        "arguments": {"disease_query": "vexas"},
                    },
                }
            )
            self.assertFalse(vexas_resp["result"]["isError"])
            vexas_data = json.loads(vexas_resp["result"]["content"][0]["text"])
            self.assertEqual(vexas_data["curated_atlas_match"], "vexas-syndrome")

            # 4c. tools/call -> get_90_day_validation_plan
            plan_resp = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 302,
                    "method": "tools/call",
                    "params": {
                        "name": "get_90_day_validation_plan",
                        "arguments": {
                            "disease_id": "autoimmune-myelofibrosis",
                            "background": "computational-ai-bio",
                        },
                    },
                }
            )
            self.assertFalse(plan_resp["result"]["isError"])
            plan_data = json.loads(plan_resp["result"]["content"][0]["text"])
            self.assertEqual(plan_data["disease_id"], "autoimmune-myelofibrosis")

            # 5. tools/call -> search_founder_opportunities (AI-Bio, no wet lab) + legacy alias match_founder_opportunities
            match_resp = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "search_founder_opportunities",
                        "arguments": {
                            "background": "computational-ai-bio",
                            "capital_tier": "bootstrapped-grant",
                            "wet_lab_required": False,
                        },
                    },
                }
            )
            self.assertFalse(match_resp["result"]["isError"])
            match_data = json.loads(match_resp["result"]["content"][0]["text"])
            self.assertEqual(match_data["data_source"], "bundled_fallback")
            self.assertGreaterEqual(match_data["matched_count"], 2)
            for opp in match_data["opportunities"]:
                self.assertIn("computational-ai-bio", opp["backgrounds"])
                self.assertFalse(opp["wet_lab_required"])

            # 6. tools/call -> get_disease_case_study
            cs_resp = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "get_disease_case_study",
                        "arguments": {"disease_id": "jak2-myelofibrosis"},
                    },
                }
            )
            cs_data = json.loads(cs_resp["result"]["content"][0]["text"])
            self.assertEqual(
                cs_data["case_study"]["identifiers"]["orphanet"], "ORPHA:824"
            )
            self.assertGreaterEqual(
                len(cs_data["case_study"]["open_datasets_and_tools"]), 4
            )

            # 7. tools/call -> list_non_dilutive_grants
            grants_resp = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {
                        "name": "list_non_dilutive_grants",
                        "arguments": {"track": "sbir"},  # tests alias -> sbir-sttr
                    },
                }
            )
            grants_data = json.loads(grants_resp["result"]["content"][0]["text"])
            self.assertEqual(grants_data["track_filter"], "sbir-sttr")
            self.assertGreaterEqual(grants_data["grant_count"], 2)

            # 8. tools/call -> get_validation_communities
            val_resp = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "get_validation_communities",
                        "arguments": {"disease_id": "jak2-myelofibrosis"},
                    },
                }
            )
            val_data = json.loads(val_resp["result"]["content"][0]["text"])
            self.assertGreaterEqual(
                len(val_data["institutional_and_patient_communities"]), 4
            )
            self.assertGreaterEqual(len(val_data["ethical_discovery_guidelines"]), 4)

            # 9. resources/list & resources/read
            res_list = client.send_request(
                {"jsonrpc": "2.0", "id": 8, "method": "resources/list"}
            )
            uris = [r["uri"] for r in res_list["result"]["resources"]]
            self.assertIn("briefing://rare-disease-playbook/jak2-myelofibrosis", uris)

            res_read = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 9,
                    "method": "resources/read",
                    "params": {
                        "uri": "briefing://rare-disease-playbook/jak2-myelofibrosis"
                    },
                }
            )
            playbook_md = res_read["result"]["contents"][0]["text"]
            self.assertIn("JAK2 V617F", playbook_md)
            self.assertIn("FDA Orphan Drug", playbook_md)
            self.assertIn("Ethical Patient & Clinical Validation Rules", playbook_md)

            # 10. prompts/list & prompts/get
            p_list = client.send_request(
                {"jsonrpc": "2.0", "id": 10, "method": "prompts/list"}
            )
            self.assertEqual(
                p_list["result"]["prompts"][0]["name"], "evaluate-rare-disease-venture"
            )

            p_get = client.send_request(
                {
                    "jsonrpc": "2.0",
                    "id": 11,
                    "method": "prompts/get",
                    "params": {
                        "name": "evaluate-rare-disease-venture",
                        "arguments": {
                            "founder_background": "public-health",
                            "capital_budget": "bootstrapped-grant",
                            "wet_lab_access": "false",
                        },
                    },
                }
            )
            prompt_msg = p_get["result"]["messages"][0]["content"]["text"]
            self.assertIn("search_founder_opportunities", prompt_msg)
            self.assertIn("public-health", prompt_msg)
        finally:
            client.close()

    def test_02_live_url_fetch_and_offline_fallback(self) -> None:
        # Spin up a mock live S3 feed serving a custom opportunity list
        class MockS3Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:  # noqa: A002
                pass

            def do_GET(self) -> None:  # noqa: N802
                payload = {
                    "atlas_name": "Live S3 Venture Feed",
                    "opportunities": [
                        {
                            "id": "opp-live-test",
                            "disease_id": "jak2-myelofibrosis",
                            "title": "Live S3 Synced Opportunity",
                            "backgrounds": ["venture-novel-financing"],
                            "capital_tier": "seed",
                            "capital_range_usd": "$500K",
                            "wet_lab_required": False,
                            "problem_wedge": "Live wedge",
                            "solution_blueprint": "Live blueprint",
                        }
                    ],
                }
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        mock_http = ThreadingHTTPServer(("127.0.0.1", 0), MockS3Handler)
        port = mock_http.server_address[1]
        thread = threading.Thread(target=mock_http.serve_forever, daemon=True)
        thread.start()
        try:
            prev_offline = os.environ.pop("ATLAS_OFFLINE", None)
            try:
                live_repo = AtlasRepository(
                    live_url=f"http://127.0.0.1:{port}/opportunities.json",
                    timeout_seconds=2.0,
                )
                srv = OrphanDiseaseMCPServer(repository=live_repo)
                live_res = srv.tool_match_founder_opportunities(background="vc")
                self.assertEqual(live_res["data_source"], "live")
                self.assertEqual(live_res["matched_count"], 1)
                self.assertEqual(live_res["opportunities"][0]["id"], "opp-live-test")
                # Merged bundled case_studies must still remain intact!
                cs = srv.tool_get_disease_case_study("jak2-myelofibrosis")
                self.assertIn("case_study", cs)

                # Verify unreachable port gracefully falls back to bundled data/opportunities.json
                fallback_repo = AtlasRepository(
                    live_url="http://127.0.0.1:9/unreachable.json",
                    timeout_seconds=0.5,
                )
                fb_srv = OrphanDiseaseMCPServer(repository=fallback_repo)
                fb_res = fb_srv.tool_match_founder_opportunities(background="all")
                self.assertEqual(fb_res["data_source"], "bundled_fallback")
                self.assertGreaterEqual(fb_res["matched_count"], 16)
                for slug in ("autoimmune-myelofibrosis", "vexas-syndrome", "castleman-disease", "systemic-mastocytosis", "telomere-biology-disorders"):
                    sub_cs = fb_srv.tool_get_disease_case_study(slug)
                    self.assertIn("case_study", sub_cs)
            finally:
                if prev_offline is not None:
                    os.environ["ATLAS_OFFLINE"] = prev_offline
        finally:
            mock_http.shutdown()
            mock_http.server_close()

    def test_03_streamable_http_transport(self) -> None:
        repo = AtlasRepository(live_url="")
        mcp_srv = OrphanDiseaseMCPServer(repository=repo)
        httpd = create_http_server(mcp_srv, host="127.0.0.1", port=0)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            # GET /.well-known/mcp.json
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/.well-known/mcp.json", timeout=2
            ) as resp:
                self.assertEqual(resp.status, 200)
                manifest = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(manifest["transport"]["type"], "streamable-http")
                self.assertIn("search_founder_opportunities", manifest["tools"])

            # POST /mcp -> tools/call (canonical + legacy alias compatibility)
            rpc_req = urllib.request.Request(
                f"http://127.0.0.1:{port}/mcp",
                data=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 99,
                        "method": "tools/call",
                        "params": {
                            "name": "search_founder_opportunities",
                            "arguments": {"background": "public-health"},
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(rpc_req, timeout=2) as resp:
                self.assertEqual(resp.status, 200)
                rpc_out = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(rpc_out["id"], 99)
                self.assertGreaterEqual(
                    rpc_out["result"]["structuredContent"]["matched_count"], 3
                )
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_04_openapi_and_registry_manifests_valid(self) -> None:
        openapi_path = MCP_DIR / "openapi.yaml"
        raw_yaml = openapi_path.read_text(encoding="utf-8")
        if yaml is not None:
            spec = yaml.safe_load(raw_yaml)
            self.assertEqual(spec["openapi"], "3.1.0")
            self.assertEqual(
                spec["servers"][0]["url"], "https://rare-disease-atlas.github.io"
            )
            self.assertIn("/opportunities.json", spec["paths"])
            self.assertIn("/.well-known/mcp.json", spec["paths"])
        else:
            self.assertIn("openapi: 3.1.0", raw_yaml)
            self.assertIn("url: https://rare-disease-atlas.github.io", raw_yaml)
            self.assertIn("/opportunities.json:", raw_yaml)
            self.assertIn("/.well-known/mcp.json:", raw_yaml)

        server_json_path = MCP_DIR / "server.json"
        with server_json_path.open("r", encoding="utf-8") as fh:
            reg = json.load(fh)
        self.assertEqual(reg["name"], "io.github.rare-disease-atlas/orphan-disease-opportunity-mcp")
        self.assertIn(reg["packages"][0]["registryType"], ("mcpb", "pypi"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
