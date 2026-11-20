#!/usr/bin/env python3
"""
MyelofibrosisBench-v1.1 Deterministic Evaluator (`evaluate_agent.py`)
=====================================================================
100% Python standard-library evaluation harness for biomedical, clinical-trial,
structural-pharmacology, and orphan-venture AI agents on MyelofibrosisBench-v1.1
(50 test items + 5 few-shot dev exemplars across 5 translational categories).

Usage:
  # Run built-in schema, citation, balance, zero-PII, and mock-agent self-tests:
  PYTHONDONTWRITEBYTECODE=1 python3 evaluate_agent.py --self-test

  # Score an agent's JSONL predictions locally:
  PYTHONDONTWRITEBYTECODE=1 python3 evaluate_agent.py \
      --predictions path/to/predictions.jsonl \
      --output-json path/to/score_report.json

  # Grade predictions remotely via the Rare Disease Venture Atlas API:
  PYTHONDONTWRITEBYTECODE=1 python3 evaluate_agent.py \
      --predictions path/to/predictions.jsonl \
      --grade-via-api \
      --model-name "example-biomed-agent-v1"

  # Opt-in anonymous aggregate leaderboard/telemetry submission (zero PII/IPs stored):
  PYTHONDONTWRITEBYTECODE=1 python3 evaluate_agent.py \
      --predictions path/to/predictions.jsonl \
      --submit-anonymous-score \
      --model-name "example-biomed-agent-v1"

Expected prediction JSONL format (one JSON object per line):
  {"id": "mf-bench-001", "choice": "A", "reasoning": "Autoimmune Myelofibrosis shows non-clustered megakaryocytes..."}
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from typing import Any

BENCHMARK_VERSION = "MyelofibrosisBench-v1.1"
EXPECTED_TEST_COUNT = 50
EXPECTED_PER_CATEGORY_TEST = 10
EXPECTED_DEV_COUNT = 5
EXPECTED_PER_CATEGORY_DEV = 1
FEEDBACK_ENDPOINT = "https://api.rare-disease-atlas.workers.dev/api/feedback"
GRADE_ENDPOINT = "https://api.rare-disease-atlas.workers.dev/api/grade-benchmark"
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


def resolve_default_paths(script_dir: Path) -> tuple[Path, Path]:
    """Support both standalone repo (`data/test.jsonl`) and `benchmarks/` layouts."""
    data_test = script_dir / "data" / "test.jsonl"
    data_dev = script_dir / "data" / "dev.jsonl"
    flat_test = script_dir / "myelofibrosis_bench.jsonl"
    flat_dev = script_dir / "myelofibrosis_bench_dev.jsonl"

    test_path = data_test if data_test.exists() else flat_test
    dev_path = data_dev if data_dev.exists() else flat_dev
    return test_path, dev_path


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


def validate_split_schema(
    items: list[dict[str, Any]],
    *,
    split: str = "test",
) -> list[str]:
    errors: list[str] = []
    if split == "test":
        expected_total = EXPECTED_TEST_COUNT
        expected_per_cat = EXPECTED_PER_CATEGORY_TEST
        id_prefix = "mf-bench-"
    elif split == "dev":
        expected_total = EXPECTED_DEV_COUNT
        expected_per_cat = EXPECTED_PER_CATEGORY_DEV
        id_prefix = "mf-bench-dev-"
    else:
        return [f"Unknown split '{split}'"]

    if len(items) != expected_total:
        errors.append(f"[{split}] Expected exactly {expected_total} items, found {len(items)}")

    seen_ids: set[str] = set()
    category_counts: dict[str, int] = {cat: 0 for cat in EXPECTED_CATEGORIES}
    choice_counts: collections.Counter[str] = collections.Counter()

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
        expected_id = f"{id_prefix}{idx:03d}"
        item_id = item.get("id")
        if item_id != expected_id:
            errors.append(f"[{split}] Row {idx}: expected id '{expected_id}', got '{item_id}'")
        if item_id in seen_ids:
            errors.append(f"[{split}] Duplicate id '{item_id}'")
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

        gold = item["correct_choice"]
        if gold not in VALID_CHOICES:
            errors.append(f"{item_id}: invalid correct_choice '{gold}'")
        else:
            choice_counts[gold] += 1

        kws = item["required_reasoning_keywords"]
        if (
            not isinstance(kws, list)
            or not (3 <= len(kws) <= 5)
            or not all(isinstance(k, str) and k.strip() for k in kws)
        ):
            errors.append(
                f"{item_id}: required_reasoning_keywords must be a list of 3-5 non-empty strings"
            )

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
        if count != expected_per_cat:
            errors.append(
                f"[{split}] Category '{cat}' expected {expected_per_cat} items, found {count}"
            )

    if split == "test" and len(items) == EXPECTED_TEST_COUNT:
        for ch in VALID_CHOICES:
            cnt = choice_counts.get(ch, 0)
            if not (12 <= cnt <= 13):
                errors.append(
                    f"[test] Unbalanced correct_choice '{ch}': expected 12-13, found {cnt}"
                )

    return errors


def validate_benchmark_schema(items: list[dict[str, Any]]) -> list[str]:
    return validate_split_schema(items, split="test")


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


def grade_via_api(
    predictions: list[dict[str, Any]],
    model_name: str,
    endpoint: str,
) -> dict[str, Any]:
    clean_model = re.sub(r"[^A-Za-z0-9._:/-]+", "-", model_name.strip())[:80] or "anonymous-model"
    normalized_preds = [
        {
            "id": str(row.get("id", "")).strip(),
            "choice": extract_choice(row),
            "reasoning": extract_reasoning(row),
        }
        for row in predictions
        if isinstance(row.get("id"), str) and row.get("id", "").strip()
    ]
    payload = {
        "benchmark_version": BENCHMARK_VERSION,
        "model_name": clean_model,
        "predictions": normalized_preds,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "RareDiseaseVentureAtlas-MyelofibrosisBench/1.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp_text = resp.read().decode("utf-8", errors="replace")
        parsed: Any
        try:
            parsed = json.loads(resp_text)
        except json.JSONDecodeError:
            parsed = {"raw_response": resp_text}
        return {"http_status": resp.status, "data": parsed}


def submit_anonymous_score(report: dict[str, Any], model_name: str, endpoint: str) -> dict[str, Any]:
    clean_model = re.sub(r"[^A-Za-z0-9._:/-]+", "-", model_name.strip())[:80] or "anonymous-model"
    payload = {
        "signal_type": "usage-feedback",
        "disease_id": "jak2-myelofibrosis",
        "source": "myelofibrosis-bench-v1.1-evaluator",
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
            "User-Agent": "RareDiseaseVentureAtlas-MyelofibrosisBench/1.1",
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


def run_self_test(benchmark_path: Path, dev_path: Path) -> int:
    print(f"[self-test] Loading test split from {benchmark_path} ...")
    test_items = load_jsonl(benchmark_path)
    test_errors = validate_split_schema(test_items, split="test")
    if test_errors:
        print("[self-test] FAILED test schema validation:", file=sys.stderr)
        for err in test_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"[self-test] Loading dev split from {dev_path} ...")
    dev_items = load_jsonl(dev_path)
    dev_errors = validate_split_schema(dev_items, split="dev")
    if dev_errors:
        print("[self-test] FAILED dev schema validation:", file=sys.stderr)
        for err in dev_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    # Test 1: Oracle predictions on test split -> 50/50 = 100%
    oracle_preds = [
        {
            "id": it["id"],
            "choice": it["correct_choice"],
            "reasoning": it["rationale"] + " " + " ".join(it["required_reasoning_keywords"]),
        }
        for it in test_items
    ]
    oracle_report = evaluate_predictions(test_items, oracle_preds)
    assert oracle_report["correct_answers"] == EXPECTED_TEST_COUNT, "Oracle must score 50/50"
    assert oracle_report["overall_choice_accuracy"] == 1.0, "Oracle accuracy must be 1.0"
    assert oracle_report["overall_reasoning_keyword_coverage"] == 1.0, "Oracle kw coverage must be 1.0"
    assert oracle_report["composite_translational_score"] == 1.0, "Oracle composite must be 1.0"

    # Test 2: Half-correct deterministic mock predictions (first 5 of each category correct)
    mock_preds = []
    cat_seen: dict[str, int] = {c: 0 for c in EXPECTED_CATEGORIES}
    for it in test_items:
        cat_seen[it["category"]] += 1
        if cat_seen[it["category"]] <= EXPECTED_PER_CATEGORY_TEST // 2:
            choice = it["correct_choice"]
            reasoning = " ".join(it["required_reasoning_keywords"][:2])
        else:
            wrong = next(c for c in VALID_CHOICES if c != it["correct_choice"])
            choice = wrong
            reasoning = "Unrelated generic cytokine discussion."
        mock_preds.append({"id": it["id"], "choice": choice, "reasoning": reasoning})

    mock_report = evaluate_predictions(test_items, mock_preds)
    expected_half = EXPECTED_TEST_COUNT // 2
    assert (
        mock_report["correct_answers"] == expected_half
    ), f"Expected {expected_half}/{EXPECTED_TEST_COUNT} on half-mock, got {mock_report['correct_answers']}"
    assert abs(mock_report["overall_choice_accuracy"] - 0.5) < 1e-6, "Expected 50.0% mock accuracy"
    for cat in EXPECTED_CATEGORIES:
        assert (
            mock_report["category_breakdown"][cat]["correct"] == EXPECTED_PER_CATEGORY_TEST // 2
        ), f"Expected 5/10 in {cat}"

    # Test 3: Oracle predictions on dev split -> 5/5 = 100%
    dev_oracle = [
        {
            "id": it["id"],
            "choice": it["correct_choice"],
            "reasoning": it["rationale"] + " " + " ".join(it["required_reasoning_keywords"]),
        }
        for it in dev_items
    ]
    dev_report = evaluate_predictions(dev_items, dev_oracle)
    assert dev_report["correct_answers"] == EXPECTED_DEV_COUNT, "Dev oracle must score 5/5"
    assert dev_report["overall_choice_accuracy"] == 1.0, "Dev oracle accuracy must be 1.0"

    choice_dist = dict(sorted(collections.Counter(it["correct_choice"] for it in test_items).items()))
    print(
        f"[self-test] PASS — Verified {len(test_items)} test items ({EXPECTED_PER_CATEGORY_TEST}/category, "
        f"choice balance {choice_dist}) + {len(dev_items)} dev exemplars ({EXPECTED_PER_CATEGORY_DEV}/category), "
        "citation accessions, zero-PII checks, oracle (50/50 = 100.0%, dev 5/5 = 100.0%), "
        "and stratified mock evaluation (25/50 = 50.0%)."
    )
    return 0


def main() -> int:
    default_bench, default_dev = resolve_default_paths(Path(__file__).resolve().parent)
    parser = argparse.ArgumentParser(
        description=f"Evaluate AI agent predictions on {BENCHMARK_VERSION} (zero external dependencies)."
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=default_bench,
        help="Path to test split JSONL (default: data/test.jsonl or myelofibrosis_bench.jsonl).",
    )
    parser.add_argument(
        "--dev",
        type=Path,
        default=default_dev,
        help="Path to dev split JSONL (default: data/dev.jsonl or myelofibrosis_bench_dev.jsonl).",
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
        help="Validate test (50) + dev (5) schemas, citations, balance, zero-PII rules, and mock evals.",
    )
    parser.add_argument(
        "--grade-via-api",
        action="store_true",
        help=f"Submit predictions to the hosted deterministic grader ({GRADE_ENDPOINT}).",
    )
    parser.add_argument(
        "--grade-endpoint",
        type=str,
        default=GRADE_ENDPOINT,
        help=f"Remote grading API URL (default: {GRADE_ENDPOINT}).",
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
        help="Model or agent identifier (required for --submit-anonymous-score; recommended for --grade-via-api).",
    )
    parser.add_argument(
        "--feedback-endpoint",
        type=str,
        default=FEEDBACK_ENDPOINT,
        help=f"Feedback webhook URL (default: {FEEDBACK_ENDPOINT}).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_test(args.benchmark, args.dev)

    if not args.predictions:
        parser.error("Provide --predictions path/to/preds.jsonl or run with --self-test.")

    preds = load_jsonl(args.predictions)

    if args.grade_via_api:
        try:
            res = grade_via_api(preds, args.model_name or "anonymous-model", args.grade_endpoint)
            print(f"Remote grading completed (HTTP {res['http_status']}):")
            print(json.dumps(res["data"], indent=2, ensure_ascii=False))
            if args.output_json:
                args.output_json.parent.mkdir(parents=True, exist_ok=True)
                args.output_json.write_text(
                    json.dumps(res["data"], indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                print(f"\nSaved remote grading report to {args.output_json}")
            return 0
        except urllib.error.URLError as exc:
            print(f"Remote grading error ({args.grade_endpoint}): {exc}", file=sys.stderr)
            return 2

    items = load_jsonl(args.benchmark)
    schema_errors = validate_benchmark_schema(items)
    if schema_errors:
        for err in schema_errors:
            print(f"Schema error: {err}", file=sys.stderr)
        return 1

    report = evaluate_predictions(items, preds)
    print_summary(report)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
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
