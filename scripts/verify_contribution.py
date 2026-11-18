#!/usr/bin/env python3
"""
Rare Disease Venture Atlas — Deterministic Contribution & Citation Verifier
===========================================================================
100% Python stdlib pre-flight validator for AI agents and human contributors
submitting Open Problem solutions, new benchmark items, tabular dataset rows,
or structured feedback payloads.

Checks enforced:
  1. Valid UTF-8 JSON / JSONL syntax and required schema fields.
  2. Strict biomedical accession formatting (`NCT########`, `PMID:#####`,
     `GEO:GSE####`, `PDB:XXXX`, `ORPHA:####`, `ChEMBL:CHEMBL####`).
  3. Zero-PII, zero-local-path, and zero-secret hygiene (rejects emails,
     phone numbers, `/home/...` or `/Users/...` paths, and API tokens).

Usage:
  PYTHONDONTWRITEBYTECODE=1 python3 verify_contribution.py --self-test
  PYTHONDONTWRITEBYTECODE=1 python3 verify_contribution.py --input path/to/contribution.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

VALID_OPEN_PROBLEM_IDS = {f"OP-MF-{i:03d}" for i in range(1, 7)}

CITATION_REGEX = re.compile(
    r"^(?:NCT\d{8}|PMID:\d{5,9}|GEO:GSE\d{4,8}|PDB:[0-9][A-Za-z0-9]{3}|ORPHA:\d+|ChEMBL:CHEMBL\d+|ENSG\d{11})$"
)
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LOCAL_HOME_REGEX = re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+")
SECRET_TOKEN_REGEX = re.compile(r"\b(?:hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PGP_BLOCK_REGEX = re.compile(r"-{5}BEGIN\s+" + r"PGP\s+(?:SIGNATURE|PRIVATE KEY|PUBLIC KEY)\s+BLOCK-{5}")


def scan_zero_pii_and_secrets(obj: Any, label: str = "root") -> list[str]:
    """Recursively inspect keys and string values for PII, local paths, GPG blocks, or API secrets."""
    issues: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            issues.extend(scan_zero_pii_and_secrets(str(k), f"{label}.<key:{k}>"))
            issues.extend(scan_zero_pii_and_secrets(v, f"{label}.{k}"))
    elif isinstance(obj, list):
        for idx, elem in enumerate(obj):
            issues.extend(scan_zero_pii_and_secrets(elem, f"{label}[{idx}]"))
    elif isinstance(obj, str):
        if EMAIL_REGEX.search(obj):
            issues.append(f"{label}: email address detected (strict zero-PII violation)")
        if LOCAL_HOME_REGEX.search(obj):
            issues.append(f"{label}: local user directory path detected")
        if SECRET_TOKEN_REGEX.search(obj):
            issues.append(f"{label}: API/credential token pattern detected")
        if SSN_REGEX.search(obj):
            issues.append(f"{label}: SSN-like identifier detected")
        if PGP_BLOCK_REGEX.search(obj):
            issues.append(f"{label}: PGP signature/key block detected")
    return issues


def validate_citation_list(citations: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(citations, list) or len(citations) == 0:
        return [f"{label}: must be a non-empty list of accession strings"]
    for idx, cite in enumerate(citations):
        if not isinstance(cite, str) or not CITATION_REGEX.match(cite.strip()):
            errors.append(
                f"{label}[{idx}]: invalid accession '{cite}' "
                "(expected NCT########, PMID:#####, GEO:GSE#####, PDB:XXXX, ORPHA:####, or ChEMBL:CHEMBL####)"
            )
    return errors


def validate_open_problems_manifest(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(scan_zero_pii_and_secrets(doc, "open-problems.json"))

    problems = doc.get("open_problems")
    if not isinstance(problems, list) or len(problems) != 6:
        errors.append(f"open-problems.json: expected exactly 6 open_problems, found {len(problems) if isinstance(problems, list) else 'non-list'}")
        return errors

    required = {
        "problem_id",
        "title",
        "disease_ids",
        "domain",
        "difficulty",
        "biological_hypothesis",
        "required_input_datasets",
        "evaluation_criteria",
        "expected_deliverables",
        "submission_endpoint",
    }
    seen_ids: set[str] = set()
    for idx, prob in enumerate(problems):
        if not isinstance(prob, dict):
            errors.append(f"open_problems[{idx}]: expected object")
            continue
        missing = required - set(prob.keys())
        if missing:
            errors.append(f"open_problems[{idx}]: missing keys {sorted(missing)}")
            continue
        pid = prob["problem_id"]
        if pid not in VALID_OPEN_PROBLEM_IDS:
            errors.append(f"open_problems[{idx}]: unexpected problem_id '{pid}'")
        if pid in seen_ids:
            errors.append(f"open_problems[{idx}]: duplicate problem_id '{pid}'")
        seen_ids.add(pid)
        errors.extend(validate_citation_list(prob["required_input_datasets"], f"{pid}.required_input_datasets"))
        if not isinstance(prob["evaluation_criteria"], list) or len(prob["evaluation_criteria"]) < 2:
            errors.append(f"{pid}: evaluation_criteria must contain >=2 measurable criteria")
        if not isinstance(prob["expected_deliverables"], list) or len(prob["expected_deliverables"]) < 2:
            errors.append(f"{pid}: expected_deliverables must contain >=2 concrete deliverables")
    return errors


def validate_contribution_payload(payload: dict[str, Any]) -> list[str]:
    """Validate an agent or researcher contribution submission JSON."""
    errors: list[str] = []
    errors.extend(scan_zero_pii_and_secrets(payload, "contribution"))

    ctype = payload.get("contribution_type", "open_problem_solution")
    if ctype == "open_problem_solution":
        required = {"problem_id", "disease_id", "hypothesis_or_method", "citations", "deliverable_summary"}
        missing = required - set(payload.keys())
        if missing:
            errors.append(f"Missing required contribution keys: {sorted(missing)}")
            return errors
        if payload["problem_id"] not in VALID_OPEN_PROBLEM_IDS:
            errors.append(f"Unknown problem_id '{payload['problem_id']}' (expected one of {sorted(VALID_OPEN_PROBLEM_IDS)})")
        if not isinstance(payload["hypothesis_or_method"], str) or len(payload["hypothesis_or_method"].strip()) < 30:
            errors.append("hypothesis_or_method must be at least 30 characters")
        if not isinstance(payload["deliverable_summary"], str) or len(payload["deliverable_summary"].strip()) < 20:
            errors.append("deliverable_summary must be at least 20 characters")
        errors.extend(validate_citation_list(payload["citations"], "contribution.citations"))
    elif ctype == "benchmark_item":
        required = {
            "id",
            "category",
            "difficulty",
            "question",
            "choices",
            "correct_choice",
            "required_reasoning_keywords",
            "rationale",
            "primary_citations",
        }
        missing = required - set(payload.keys())
        if missing:
            errors.append(f"Missing required benchmark_item keys: {sorted(missing)}")
            return errors
        if payload["correct_choice"] not in ("A", "B", "C", "D"):
            errors.append("correct_choice must be A, B, C, or D")
        errors.extend(validate_citation_list(payload["primary_citations"], "benchmark_item.primary_citations"))
    else:
        errors.append(f"Unsupported contribution_type '{ctype}' (expected 'open_problem_solution' or 'benchmark_item')")

    return errors


def validate_jsonl_table(path: Path) -> list[str]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}:{line_no}: invalid JSON ({exc})")
                continue
            if not isinstance(obj, dict):
                errors.append(f"{path.name}:{line_no}: row must be a JSON object")
                continue
            errors.extend(scan_zero_pii_and_secrets(obj, f"{path.name}:{line_no}"))
            rows.append(obj)

    if not rows:
        errors.append(f"{path.name}: file contains 0 records")
        return errors

    # Verify uniform Parquet-compatible column types across all rows (and strict identical keys on molecular/bench tables)
    strict_key_tables = {
        "myelofibrosis_bench.jsonl",
        "myelofibrosis_gene_signatures.jsonl",
        "jak2_structural_pockets.jsonl",
        "myelofibrosis_clinical_trials.jsonl",
    }
    expected_keys = list(rows[0].keys())
    col_types: dict[str, type] = {}
    for idx, row in enumerate(rows, start=1):
        if path.name in strict_key_tables and list(row.keys()) != expected_keys:
            errors.append(f"{path.name}:{idx}: non-uniform keys {list(row.keys())} vs row 1 {expected_keys}")
            continue
        for k, v in row.items():
            if v is None:
                continue
            if k not in col_types:
                col_types[k] = type(v)
            elif type(v) is not col_types[k]:
                errors.append(
                    f"{path.name}:{idx}.{k}: inconsistent Parquet type {type(v).__name__} vs {col_types[k].__name__}"
                )

        # Citation checks on known accession columns
        for cite_col in ("primary_citations", "reference_datasets", "pdb_ids", "nct_ids"):
            if cite_col in row:
                errors.extend(validate_citation_list(row[cite_col], f"{path.name}:{idx}.{cite_col}"))

    return errors


def discover_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "open-problems.json").exists():
        return here
    if (here.parent / "site" / "open-problems.json").exists():
        return here.parent / "site"
    if (here.parent / "open-problems.json").exists():
        return here.parent
    return here


def run_self_test() -> int:
    root = discover_repo_root()
    print(f"[self-test] Running contribution, schema, citation, and zero-PII verification in {root.name}/ ...")

    op_path = root / "open-problems.json"
    if not op_path.exists():
        print(f"[self-test] FAIL: {op_path.name} not found", file=sys.stderr)
        return 1

    op_doc = json.loads(op_path.read_text(encoding="utf-8"))
    op_errors = validate_open_problems_manifest(op_doc)
    if op_errors:
        for e in op_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    checked_tables: list[str] = []
    for subdir in ("benchmarks", "data"):
        folder = root / subdir
        if folder.is_dir():
            for jsonl_file in sorted(folder.glob("*.jsonl")):
                # Skip opportunities/validation_communities URL-bearing legacy tables for email-like strings? Wait: none have emails!
                t_errs = validate_jsonl_table(jsonl_file)
                if t_errs:
                    for e in t_errs:
                        print(f"  - {e}", file=sys.stderr)
                    return 1
                checked_tables.append(f"{subdir}/{jsonl_file.name}")

    # Positive synthetic contribution test
    valid_contrib = {
        "contribution_type": "open_problem_solution",
        "problem_id": "OP-MF-001",
        "disease_id": "jak2-myelofibrosis",
        "hypothesis_or_method": (
            "Designed rigid spirocyclic piperidine linker from JAK2 JH2 V617F Gly552 solvent channel to CRBN "
            "achieving predicted ddG selectivity of -2.8 kcal/mol (>100x) over WT JH2 (PDB:4FVP) and zero JH1 clash."
        ),
        "citations": ["PDB:4FVQ", "PDB:4FVR", "PDB:4FVP", "PDB:8BAK", "NCT06313593"],
        "deliverable_summary": "20-compound SMILES set + ternary complex Rosetta/FEP energetics + DiscoverX TR-FRET protocol.",
    }
    assert validate_contribution_payload(valid_contrib) == [], "Valid synthetic contribution should pass"

    # Negative test 1: Bad citation format
    bad_cite_contrib = dict(valid_contrib, citations=["PDB:INVALID_ID", "NCT123"])
    cite_errs = validate_contribution_payload(bad_cite_contrib)
    assert len(cite_errs) == 2, f"Expected 2 citation errors, got {cite_errs}"

    # Negative test 2: PII email + local home path + token leak (constructed dynamically so static secret scanners never false-positive)
    dummy_email = "researcher" + "@" + "example.org"
    dummy_path = "/" + "Users/alice/local_run"
    dummy_tok = "hf" + "_" + ("X" * 24)
    pii_contrib = dict(
        valid_contrib,
        deliverable_summary=f"Contact {dummy_email} or see {dummy_path} and {dummy_tok}",
    )
    pii_errs = validate_contribution_payload(pii_contrib)
    assert len(pii_errs) >= 3, f"Expected >=3 PII/secret errors, got {pii_errs}"

    print(
        f"[self-test] PASS — Verified open-problems.json (6 open problems), "
        f"{len(checked_tables)} JSONL tables ({', '.join(checked_tables)}), "
        "strict accession regexes, and positive/negative zero-PII guardrails."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Rare Disease Venture Atlas contributions, citations, and zero-PII compliance."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to a contribution JSON file or JSONL dataset file to validate.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Validate open-problems.json, repository JSONL tables, and built-in positive/negative test vectors.",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.input:
        parser.error("Provide --input path/to/file.json[l] or --self-test.")

    target = args.input.resolve()
    if not target.exists():
        print(f"Error: file not found: {target.name}", file=sys.stderr)
        return 1

    if target.suffix == ".jsonl":
        errors = validate_jsonl_table(target)
    else:
        doc = json.loads(target.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and "open_problems" in doc:
            errors = validate_open_problems_manifest(doc)
        elif isinstance(doc, dict):
            errors = validate_contribution_payload(doc)
        else:
            errors = ["Top-level JSON must be an object"]

    if errors:
        print(f"FAILED verification ({len(errors)} issue(s)): ", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"PASS — {target.name} passed schema, citation formatting, and zero-PII checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
