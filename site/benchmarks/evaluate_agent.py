#!/usr/bin/env python3
"""
MyelofibrosisBench-v1 Deterministic Evaluator (`benchmarks/evaluate_agent.py`)
==============================================================================
100% Python standard-library evaluation harness for biomedical, clinical-trial,
structural-pharmacology, and orphan-venture AI agents on MyelofibrosisBench-v1.

Usage:
  # Run built-in schema, citation, zero-PII, and mock-agent self-tests:
  PYTHONDONTWRITEBYTECODE=1 python3 benchmarks/evaluate_agent.py --self-test

  # Score an agent's JSONL predictions:
  PYTHONDONTWRITEBYTECODE=1 python3 benchmarks/evaluate_agent.py \
      --predictions path/to/predictions.jsonl \
      --output-json path/to/score_report.json

  # Opt-in anonymous aggregate leaderboard/telemetry submission (zero PII/IPs stored):
  PYTHONDONTWRITEBYTECODE=1 python3 benchmarks/evaluate_agent.py \
      --predictions path/to/predictions.jsonl \
      --submit-anonymous-score \
      --model-name "example-biomed-agent-v1"

Expected prediction JSONL format (one JSON object per line):
  {"id": "mf-bench-001", "choice": "B", "reasoning": "Autoimmune Myelofibrosis shows non-clustered megakaryocytes..."}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from typing import Any

BENCHMARK_VERSION = "MyelofibrosisBench-v1"
FEEDBACK_ENDPOINT = "https://api.rare-disease-atlas.workers.dev/api/feedback"
EXPECTED_CATEGORIES = (
    "aimf_differential_triage",
    "iron_hepcidin_axis",
    "jak2_jh2_structural_selectivity",
    "clinical_trial_forensics",
    "orphan_venture_economics",
)
VALID_CHOICES = ("A", "B", "C", "D")
VALID_DIFFICULTIES = ("medium", "hard")
CITATION_PATTERN = re.compile(
    r"^(?:NCT\d{8}|PMID:\d{5,9}|GEO:GSE\d{4,8}|PDB:[0-9][A-Za-z0-9]{3}|ORPHA:\d+|ChEMBL:CHEMBL\d+)$"
)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LOCAL_PATH_PATTERN = re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            records.append(obj)
    return records


def validate_benchmark_schema(items: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if len(items) != 30:
        errors.append(f"Expected exactly 30 benchmark items, found {len(items)}")

    seen_ids: set[str] = set()
    category_counts: dict[str, int] = {cat: 0 for cat in EXPECTED_CATEGORIES}

    required_keys = {
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

    for idx, item in enumerate(items, start=1):
        expected_id = f"mf-bench-{idx:03d}"
        item_id = item.get("id")
        if item_id != expected_id:
            errors.append(f"Row {idx}: expected id '{expected_id}', got '{item_id}'")
        if item_id in seen_ids:
            errors.append(f"Duplicate id '{item_id}'")
        seen_ids.add(str(item_id))

        missing = required_keys - set(item.keys())
        if missing:
            errors.append(f"{item_id}: missing required keys {sorted(missing)}")
            continue

        cat = item["category"]
        if cat not in category_counts:
            errors.append(f"{item_id}: invalid category '{cat}'")
        else:
            category_counts[cat] += 1

        if item["difficulty"] not in VALID_DIFFICULTIES:
            errors.append(f"{item_id}: invalid difficulty '{item['difficulty']}'")

        choices = item["choices"]
        if not isinstance(choices, dict) or tuple(sorted(choices.keys())) != VALID_CHOICES:
            errors.append(f"{item_id}: choices must be a dict with exact keys A, B, C, D")
        else:
            for choice_key, choice_text in choices.items():
                if not isinstance(choice_text, str) or len(choice_text.strip()) < 10:
                    errors.append(f"{item_id}: choice {choice_key} must be a non-trivial string")

        if item["correct_choice"] not in VALID_CHOICES:
            errors.append(f"{item_id}: invalid correct_choice '{item['correct_choice']}'")

        kws = item["required_reasoning_keywords"]
        if not isinstance(kws, list) or not (3 <= len(kws) <= 5) or not all(isinstance(k, str) and k.strip() for k in kws):
            errors.append(f"{item_id}: required_reasoning_keywords must be a list of 3-5 non-empty strings")

        if not isinstance(item["question"], str) or len(item["question"].strip()) < 40:
            errors.append(f"{item_id}: question too short")
        if not isinstance(item["rationale"], str) or len(item["rationale"].strip()) < 60:
            errors.append(f"{item_id}: rationale too short")

        cites = item["primary_citations"]
        if not isinstance(cites, list) or len(cites) < 1:
            errors.append(f"{item_id}: primary_citations must be a non-empty list")
        else:
            for c in cites:
                if not isinstance(c, str) or not CITATION_PATTERN.match(c):
                    errors.append(f"{item_id}: malformed citation accession '{c}'")

        serialized = json.dumps(item, ensure_ascii=False)
        if EMAIL_PATTERN.search(serialized) or LOCAL_PATH_PATTERN.search(serialized):
            errors.append(f"{item_id}: potential PII or local filesystem path detected")

    for cat, count in category_counts.items():
        if count != 6:
            errors.append(f"Category '{cat}' expected 6 items, found {count}")

    return errors


def extract_choice(pred: dict[str, Any]) -> str:
    raw = pred.get("choice", pred.get("predicted_choice", pred.get("answer", "")))
    if not isinstance(raw, str):
        return ""
    cleaned = raw.strip().upper()
    if cleaned in VALID_CHOICES:
        return cleaned
    match = re.match(r"^([ABCD])(?:[.):\s-]|$)", cleaned)
    return match.group(1) if match else ""


def extract_reasoning(pred: dict[str, Any]) -> str:
    for key in ("reasoning", "rationale", "explanation", "response"):
        val = pred.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def evaluate_predictions(
    benchmark_items: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    pred_by_id: dict[str, dict[str, Any]] = {}
    for row in predictions:
        pid = row.get("id")
        if isinstance(pid, str):
            pred_by_id[pid.strip()] = row

    total = len(benchmark_items)
    correct_total = 0
    kw_ratio_sum = 0.0
    answered_count = 0

    cat_stats: dict[str, dict[str, Any]] = {
        cat: {"total": 0, "correct": 0, "keyword_coverage_sum": 0.0}
        for cat in EXPECTED_CATEGORIES
    }
    diff_stats: dict[str, dict[str, Any]] = {
        diff: {"total": 0, "correct": 0} for diff in VALID_DIFFICULTIES
    }
    item_results: list[dict[str, Any]] = []

    for item in benchmark_items:
        qid = item["id"]
        cat = item["category"]
        diff = item["difficulty"]
        gold = item["correct_choice"]
        req_kws: list[str] = item["required_reasoning_keywords"]

        pred_obj = pred_by_id.get(qid, {})
        pred_choice = extract_choice(pred_obj)
        reasoning_text = extract_reasoning(pred_obj)
        if pred_choice:
            answered_count += 1

        is_correct = pred_choice == gold
        if is_correct:
            correct_total += 1

        reasoning_lower = reasoning_text.lower()
        matched_kws = [kw for kw in req_kws if kw.lower() in reasoning_lower]
        kw_cov = len(matched_kws) / len(req_kws) if req_kws else 0.0
        kw_ratio_sum += kw_cov

        cat_stats[cat]["total"] += 1
        cat_stats[cat]["correct"] += int(is_correct)
        cat_stats[cat]["keyword_coverage_sum"] += kw_cov

        diff_stats[diff]["total"] += 1
        diff_stats[diff]["correct"] += int(is_correct)

        item_results.append(
            {
                "id": qid,
                "category": cat,
                "difficulty": diff,
                "expected_choice": gold,
                "predicted_choice": pred_choice or None,
                "correct": is_correct,
                "matched_reasoning_keywords": matched_kws,
                "missing_reasoning_keywords": [kw for kw in req_kws if kw not in matched_kws],
                "reasoning_keyword_coverage": round(kw_cov, 4),
            }
        )

    choice_accuracy = correct_total / total if total else 0.0
    keyword_coverage = kw_ratio_sum / total if total else 0.0
    composite_score = 0.80 * choice_accuracy + 0.20 * keyword_coverage

    category_breakdown: dict[str, dict[str, Any]] = {}
    for cat, st in cat_stats.items():
        c_tot = st["total"] or 1
        c_acc = st["correct"] / c_tot
        c_kw = st["keyword_coverage_sum"] / c_tot
        category_breakdown[cat] = {
            "correct": st["correct"],
            "total": st["total"],
            "choice_accuracy": round(c_acc, 4),
            "reasoning_keyword_coverage": round(c_kw, 4),
            "composite_score": round(0.80 * c_acc + 0.20 * c_kw, 4),
        }

    difficulty_breakdown: dict[str, dict[str, Any]] = {}
    for diff, st in diff_stats.items():
        d_tot = st["total"] or 1
        difficulty_breakdown[diff] = {
            "correct": st["correct"],
            "total": st["total"],
            "choice_accuracy": round(st["correct"] / d_tot, 4),
        }

    return {
        "benchmark_version": BENCHMARK_VERSION,
        "total_questions": total,
        "answered_questions": answered_count,
        "correct_answers": correct_total,
        "overall_choice_accuracy": round(choice_accuracy, 4),
        "overall_reasoning_keyword_coverage": round(keyword_coverage, 4),
        "composite_translational_score": round(composite_score, 4),
        "category_breakdown": category_breakdown,
        "difficulty_breakdown": difficulty_breakdown,
        "item_results": item_results,
    }


def submit_anonymous_score(report: dict[str, Any], model_name: str, endpoint: str) -> dict[str, Any]:
    clean_model = re.sub(r"[^A-Za-z0-9._:/-]+", "-", model_name.strip())[:80] or "anonymous-model"
    payload = {
        "signal_type": "usage-feedback",
        "disease_id": "jak2-myelofibrosis",
        "source": "myelofibrosis-bench-v1-evaluator",
        "benchmark_version": BENCHMARK_VERSION,
        "model_name": clean_model,
        "summary": (
            f"{BENCHMARK_VERSION} opt-in evaluation for {clean_model}: "
            f"accuracy={report['overall_choice_accuracy']:.1%} "
            f"({report['correct_answers']}/{report['total_questions']}), "
            f"keyword_coverage={report['overall_reasoning_keyword_coverage']:.1%}, "
            f"composite={report['composite_translational_score']:.1%}"
        ),
        "metrics": {
            "overall_choice_accuracy": report["overall_choice_accuracy"],
            "overall_reasoning_keyword_coverage": report["overall_reasoning_keyword_coverage"],
            "composite_translational_score": report["composite_translational_score"],
            "category_accuracy": {
                cat: vals["choice_accuracy"]
                for cat, vals in report["category_breakdown"].items()
            },
        },
    }

    print("======================================================================")
    print("TRANSPARENCY NOTICE — OPT-IN ANONYMOUS BENCHMARK TELEMETRY")
    print("Destination :", endpoint)
    print("Privacy     : Zero PII, zero prompts/completions, zero local paths,")
    print("              and zero client IP persistence in benchmark payload.")
    print("Exact JSON  :", json.dumps(payload, indent=2))
    print("======================================================================")

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "RareDiseaseVentureAtlas-MyelofibrosisBench/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp_text = resp.read().decode("utf-8", errors="replace")
        return {"http_status": resp.status, "response": resp_text}


def print_summary(report: dict[str, Any]) -> None:
    print(f"=== {report['benchmark_version']} Evaluation Summary ===")
    print(
        f"Exact Choice Accuracy      : {report['correct_answers']}/{report['total_questions']} "
        f"({report['overall_choice_accuracy']:.1%})"
    )
    print(
        f"Reasoning Keyword Coverage : {report['overall_reasoning_keyword_coverage']:.1%}"
    )
    print(
        f"Composite Score (80/20)    : {report['composite_translational_score']:.1%}"
    )
    print("\nPer-Category Breakdown:")
    for cat, st in report["category_breakdown"].items():
        print(
            f"  - {cat:<34} {st['correct']}/{st['total']} "
            f"({st['choice_accuracy']:.1%}) | kw={st['reasoning_keyword_coverage']:.1%}"
        )


def run_self_test(benchmark_path: Path) -> int:
    print(f"[self-test] Loading benchmark from {benchmark_path.name} ...")
    items = load_jsonl(benchmark_path)
    errors = validate_benchmark_schema(items)
    if errors:
        print("[self-test] FAILED schema validation:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    # Test 1: Oracle predictions -> 100% choice accuracy & 100% keyword coverage
    oracle_preds = [
        {
            "id": it["id"],
            "choice": it["correct_choice"],
            "reasoning": it["rationale"] + " " + " ".join(it["required_reasoning_keywords"]),
        }
        for it in items
    ]
    oracle_report = evaluate_predictions(items, oracle_preds)
    assert oracle_report["correct_answers"] == 30, "Oracle must score 30/30"
    assert oracle_report["overall_choice_accuracy"] == 1.0, "Oracle accuracy must be 1.0"
    assert oracle_report["overall_reasoning_keyword_coverage"] == 1.0, "Oracle kw coverage must be 1.0"
    assert oracle_report["composite_translational_score"] == 1.0, "Oracle composite must be 1.0"

    # Test 2: Half-correct deterministic mock predictions (first 3 of each category correct)
    mock_preds = []
    cat_seen: dict[str, int] = {c: 0 for c in EXPECTED_CATEGORIES}
    for it in items:
        cat_seen[it["category"]] += 1
        if cat_seen[it["category"]] <= 3:
            choice = it["correct_choice"]
            reasoning = " ".join(it["required_reasoning_keywords"][:2])
        else:
            wrong = next(c for c in VALID_CHOICES if c != it["correct_choice"])
            choice = wrong
            reasoning = "Unrelated generic cytokine discussion."
        mock_preds.append({"id": it["id"], "choice": choice, "reasoning": reasoning})

    mock_report = evaluate_predictions(items, mock_preds)
    assert mock_report["correct_answers"] == 15, f"Expected 15/30 on half-mock, got {mock_report['correct_answers']}"
    assert abs(mock_report["overall_choice_accuracy"] - 0.5) < 1e-6, "Expected 50.0% mock accuracy"
    for cat in EXPECTED_CATEGORIES:
        assert mock_report["category_breakdown"][cat]["correct"] == 3, f"Expected 3/6 in {cat}"

    print(
        f"[self-test] PASS — Verified {len(items)} items across {len(EXPECTED_CATEGORIES)} categories "
        "(6 items/category), citation accessions, zero-PII checks, oracle (30/30 = 100.0%), "
        "and stratified mock evaluation (15/30 = 50.0%)."
    )
    return 0


def main() -> int:
    default_bench = Path(__file__).resolve().parent / "myelofibrosis_bench.jsonl"
    parser = argparse.ArgumentParser(
        description="Evaluate AI agent predictions on MyelofibrosisBench-v1 (zero external dependencies)."
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=default_bench,
        help="Path to myelofibrosis_bench.jsonl (default: alongside evaluate_agent.py).",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        help="Path to agent predictions JSONL file ({id, choice, reasoning}).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional path to write full structured evaluation report JSON.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Validate benchmark schema, citations, zero-PII rules, and run deterministic mock evaluations.",
    )
    parser.add_argument(
        "--submit-anonymous-score",
        action="store_true",
        help="Explicitly opt-in to POST aggregate benchmark metrics (zero PII) to the Atlas feedback API.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="",
        help="Model or agent identifier required when --submit-anonymous-score is enabled.",
    )
    parser.add_argument(
        "--feedback-endpoint",
        type=str,
        default=FEEDBACK_ENDPOINT,
        help=f"Feedback webhook URL (default: {FEEDBACK_ENDPOINT}).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_test(args.benchmark)

    if not args.predictions:
        parser.error("Provide --predictions path/to/preds.jsonl or run with --self-test.")

    items = load_jsonl(args.benchmark)
    schema_errors = validate_benchmark_schema(items)
    if schema_errors:
        for err in schema_errors:
            print(f"Schema error: {err}", file=sys.stderr)
        return 1

    preds = load_jsonl(args.predictions)
    report = evaluate_predictions(items, preds)
    print_summary(report)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nSaved full JSON report to {args.output_json}")

    if args.submit_anonymous_score:
        if not args.model_name.strip():
            parser.error("--submit-anonymous-score requires --model-name <model>.")
        try:
            res = submit_anonymous_score(report, args.model_name, args.feedback_endpoint)
            print(f"Opt-in submission completed (HTTP {res['http_status']}): {res['response']}")
        except urllib.error.URLError as exc:
            print(f"Opt-in submission warning (network/endpoint unreachable): {exc}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
