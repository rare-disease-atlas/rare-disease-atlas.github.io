#!/usr/bin/env python3
"""
RareTxBench-v2.0 Deterministic Evaluator (`evaluate_rare_tx.py`)
================================================================
100% Python standard-library evaluation harness for biomedical, translational,
structural-pharmacology, clinical-trial, and orphan-regulatory AI agents on
RareTxBench-v2.0 (152 test items + 10 dev exemplars across 7 Hugging Face
configs: mcq_100, myelofibrosis, cross_orphan, open_frontier, raw_bio_compute,
protocol_audit, and bio_delta_live).

Core Metrics Reported:
  1. Overall Accuracy (`RareTxBench-100`)
  2. Dual-Track Breakdown:
       - Myelofibrosis Flagship Deep-Dive Track (40 items)
       - Cross-Orphan Generalization Track (60 items, 20+ diseases)
       - Cross-Disease Transfer Gap (Cross-Orphan % - Myelofibrosis %)
  3. Catastrophic Translational Error Rate (`CTER`, lower is better):
       - Error rate on `critical_harm: true` items (irreversible patient harm
         or catastrophic Phase 2/3 safety/efficacy failure traps)
  4. 5-Axis Translational Profile (20 items per axis)
  5. Mechanistic Reasoning Grounding (`keyword_coverage_pct` on rubric terms)

Usage:
  # Run built-in schema, balance, length-parity, citation, zero-PII, and mock self-tests:
  PYTHONDONTWRITEBYTECODE=1 python3 evaluate_rare_tx.py --self-test

  # Score local predictions JSONL:
  PYTHONDONTWRITEBYTECODE=1 python3 evaluate_rare_tx.py \
      --predictions path/to/predictions.jsonl \
      --output-json path/to/score_report.json

  # Grade remotely via stateless Rare Disease Venture Atlas API:
  PYTHONDONTWRITEBYTECODE=1 python3 evaluate_rare_tx.py \
      --predictions path/to/predictions.jsonl \
      --grade-via-api \
      --model-name "example-biomed-agent-v1"

Expected prediction JSONL format (one JSON object per line):
  {"id": "rtx-001", "choice": "A", "reasoning": "Autoimmune myelofibrosis shows..."}
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

BENCHMARK_VERSION = "RareTxBench-v2.0"
EXPECTED_TEST_COUNT = 100
EXPECTED_MF_COUNT = 40
EXPECTED_CROSS_COUNT = 60
EXPECTED_PER_CATEGORY_TEST = 20
EXPECTED_DEV_COUNT = 10
EXPECTED_PER_CATEGORY_DEV = 2
MAX_OPTION_LENGTH_RATIO = 1.30

CATEGORIES = (
    "mimic_and_cohort_triage",
    "target_and_structural_selectivity",
    "pathway_polarity_and_homeostasis",
    "clinical_trial_endpoint_forensics",
    "orphan_regulatory_and_venture_economics",
)

VALID_TRACKS = ("myelofibrosis", "cross_orphan")
VALID_CHOICES = ("A", "B", "C", "D", "E", "F")

CITATION_RE = re.compile(
    r"^(PMID:\d{6,9}|NCT\d{8}|ORPHA:\d{1,7}|PDB:[0-9A-Za-z]{4}|OMIM:\d{6}|"
    r"(?:GEO:)?GSE\d{4,7}|(?:FDA|EMA|EU-Reg|FDORA|FDCA|IRC|Pub-L|HRSA|CMS|NIH|NCATS|\d+-CFR|21st-Century-Cures|CIRM|OOPD)[:\-][A-Za-z0-9_.\-/]+)$"
)
PII_RE = re.compile(
    r"(@gmail\.com|@yahoo\.com|@hotmail\.com|\b\d{3}-\d{2}-\d{4}\b|\bMRN[:#]?\s*\d{5,}\b)",
    re.IGNORECASE,
)

GRADE_API_URL = "https://api.rare-disease-atlas.workers.dev/api/grade-benchmark"


def resolve_default_paths() -> tuple[Path, Path]:
    here = Path(__file__).resolve().parent
    candidates = [
        (here / "data" / "test.jsonl", here / "data" / "dev.jsonl"),
        (here / "rare_tx_bench.jsonl", here / "rare_tx_bench_dev.jsonl"),
    ]
    for test_p, dev_p in candidates:
        if test_p.exists():
            return test_p, dev_p
    return candidates[0]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for idx, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{idx}: invalid JSON: {exc}") from exc
    return rows


def validate_dataset(
    test_items: list[dict[str, Any]],
    dev_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []

    if len(test_items) != EXPECTED_TEST_COUNT:
        errors.append(
            f"Expected {EXPECTED_TEST_COUNT} test items, found {len(test_items)}."
        )

    seen_ids: set[str] = set()
    cat_counts: collections.Counter[str] = collections.Counter()
    track_counts: collections.Counter[str] = collections.Counter()
    ans_overall: collections.Counter[str] = collections.Counter()
    ans_by_track: dict[str, collections.Counter[str]] = {
        t: collections.Counter() for t in VALID_TRACKS
    }
    ans_by_cat: dict[str, collections.Counter[str]] = {
        c: collections.Counter() for c in CATEGORIES
    }
    harm_count = 0
    max_len_ratio = 0.0
    correct_is_longest = 0

    required_fields = (
        "id",
        "track",
        "category",
        "disease_family",
        "orpha_code",
        "translational_motif",
        "difficulty",
        "critical_harm",
        "harm_mechanism",
        "question",
        "choices",
        "answer",
        "rubric_keywords",
        "citations",
        "explanation",
    )

    def _check_item(item: dict[str, Any], split_name: str) -> None:
        nonlocal harm_count, max_len_ratio, correct_is_longest
        raw_blob = json.dumps(item, ensure_ascii=False)
        if PII_RE.search(raw_blob):
            errors.append(f"{split_name}:{item.get('id')}: PII pattern matched.")

        for field in required_fields:
            if field not in item:
                errors.append(f"{split_name}:{item.get('id')}: missing field '{field}'.")
                return

        iid = str(item["id"]).strip()
        if iid in seen_ids:
            errors.append(f"{split_name}:{iid}: duplicate item id.")
        seen_ids.add(iid)

        track = item["track"]
        if track not in VALID_TRACKS:
            errors.append(f"{split_name}:{iid}: invalid track '{track}'.")

        cat = item["category"]
        if cat not in CATEGORIES:
            errors.append(f"{split_name}:{iid}: invalid category '{cat}'.")

        choices = item["choices"]
        if not isinstance(choices, dict) or tuple(sorted(choices.keys())) != VALID_CHOICES:
            errors.append(f"{split_name}:{iid}: choices must have exact keys A, B, C, D, E, F.")
            return

        lens = {k: len(str(v).strip()) for k, v in choices.items()}
        if min(lens.values()) < 20:
            errors.append(f"{split_name}:{iid}: option too short ({lens}).")
        ratio = max(lens.values()) / max(1, min(lens.values()))
        if ratio > MAX_OPTION_LENGTH_RATIO:
            errors.append(
                f"{split_name}:{iid}: option length ratio {ratio:.3f} > {MAX_OPTION_LENGTH_RATIO}."
            )

        ans = item["answer"]
        if ans not in VALID_CHOICES:
            errors.append(f"{split_name}:{iid}: invalid answer '{ans}'.")
            return

        if not isinstance(item["critical_harm"], bool):
            errors.append(f"{split_name}:{iid}: critical_harm must be boolean.")
        elif item["critical_harm"] and not item["harm_mechanism"]:
            errors.append(f"{split_name}:{iid}: critical_harm=true requires harm_mechanism.")

        cits = item["citations"]
        if not isinstance(cits, list) or len(cits) < 1:
            errors.append(f"{split_name}:{iid}: at least 1 citation required.")
        else:
            for c in cits:
                if not CITATION_RE.match(str(c).strip()):
                    errors.append(f"{split_name}:{iid}: invalid citation format '{c}'.")

        kws = item["rubric_keywords"]
        if not isinstance(kws, list) or len(kws) < 2:
            errors.append(f"{split_name}:{iid}: at least 2 rubric_keywords required.")

        if split_name == "test":
            cat_counts[cat] += 1
            track_counts[track] += 1
            ans_overall[ans] += 1
            ans_by_track[track][ans] += 1
            ans_by_cat[cat][ans] += 1
            if item["critical_harm"]:
                harm_count += 1
            if ratio > max_len_ratio:
                max_len_ratio = ratio
            if lens[ans] == max(lens.values()):
                correct_is_longest += 1

    for it in test_items:
        _check_item(it, "test")

    if track_counts["myelofibrosis"] != EXPECTED_MF_COUNT:
        errors.append(
            f"Expected {EXPECTED_MF_COUNT} myelofibrosis test items, found {track_counts['myelofibrosis']}."
        )
    if track_counts["cross_orphan"] != EXPECTED_CROSS_COUNT:
        errors.append(
            f"Expected {EXPECTED_CROSS_COUNT} cross_orphan test items, found {track_counts['cross_orphan']}."
        )
    for cat in CATEGORIES:
        if cat_counts[cat] != EXPECTED_PER_CATEGORY_TEST:
            errors.append(
                f"Category '{cat}': expected {EXPECTED_PER_CATEGORY_TEST} test items, found {cat_counts[cat]}."
            )
        if any(ans_by_cat[cat][ch] < 2 or ans_by_cat[cat][ch] > 5 for ch in VALID_CHOICES):
            errors.append(
                f"Category '{cat}': skewed 6-choice answer balance {dict(ans_by_cat[cat])}."
            )
    if any(ans_overall[ch] not in (16, 17) for ch in VALID_CHOICES):
        errors.append(f"Expected 16-17 per choice overall (A-F), found {dict(ans_overall)}.")
    if any(ans_by_track["myelofibrosis"][ch] not in (6, 7) for ch in VALID_CHOICES):
        errors.append(
            f"Expected 6-7 per choice on MF track (A-F), found {dict(ans_by_track['myelofibrosis'])}."
        )
    if any(ans_by_track["cross_orphan"][ch] != 10 for ch in VALID_CHOICES):
        errors.append(
            f"Expected exact 10 per choice on cross_orphan track (A-F), found {dict(ans_by_track['cross_orphan'])}."
        )

    dev_cat_counts: collections.Counter[str] = collections.Counter()
    if dev_items is not None:
        if len(dev_items) != EXPECTED_DEV_COUNT:
            errors.append(
                f"Expected {EXPECTED_DEV_COUNT} dev items, found {len(dev_items)}."
            )
        for it in dev_items:
            _check_item(it, "dev")
            dev_cat_counts[it.get("category", "")] += 1
        for cat in CATEGORIES:
            if dev_cat_counts[cat] != EXPECTED_PER_CATEGORY_DEV:
                errors.append(
                    f"Dev category '{cat}': expected {EXPECTED_PER_CATEGORY_DEV}, found {dev_cat_counts[cat]}."
                )

    if errors:
        raise ValueError("Dataset validation failed:\n  - " + "\n  - ".join(errors[:25]))

    return {
        "benchmark": BENCHMARK_VERSION,
        "test_count": len(test_items),
        "dev_count": len(dev_items) if dev_items is not None else 0,
        "tracks": dict(track_counts),
        "categories": dict(cat_counts),
        "answer_balance": dict(ans_overall),
        "critical_harm_items": harm_count,
        "max_option_length_ratio": round(max_len_ratio, 3),
        "correct_is_longest_pct": round(100.0 * correct_is_longest / len(test_items), 1),
    }


def score_predictions(
    items: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    track_filter: str = "all",
) -> dict[str, Any]:
    if track_filter in VALID_TRACKS:
        items = [it for it in items if it["track"] == track_filter]

    item_map = {str(it["id"]).strip(): it for it in items}
    pred_map: dict[str, dict[str, Any]] = {}
    unknown_ids: list[str] = []

    for pred in predictions:
        pid = str(pred.get("id", "")).strip()
        if not pid:
            continue
        if pid not in item_map:
            unknown_ids.append(pid)
            continue
        pred_map[pid] = pred

    total_graded = 0
    total_correct = 0
    harm_graded = 0
    harm_missed = 0
    missed_harm_events: list[dict[str, str]] = []

    track_stats: dict[str, dict[str, int]] = {
        t: {"graded": 0, "correct": 0, "harm_graded": 0, "harm_missed": 0}
        for t in VALID_TRACKS
    }
    cat_stats: dict[str, dict[str, int]] = {
        c: {"graded": 0, "correct": 0} for c in CATEGORIES
    }

    kw_scores: list[float] = []

    for iid, item in item_map.items():
        if iid not in pred_map:
            continue
        pred = pred_map[iid]
        choice = str(pred.get("choice", "")).strip().upper()[:1]
        is_correct = choice == item["answer"]

        total_graded += 1
        if is_correct:
            total_correct += 1

        tr = item["track"]
        cat = item["category"]
        track_stats[tr]["graded"] += 1
        cat_stats[cat]["graded"] += 1
        if is_correct:
            track_stats[tr]["correct"] += 1
            cat_stats[cat]["correct"] += 1

        if item.get("critical_harm"):
            harm_graded += 1
            track_stats[tr]["harm_graded"] += 1
            if not is_correct:
                harm_missed += 1
                track_stats[tr]["harm_missed"] += 1
                missed_harm_events.append(
                    {
                        "id": iid,
                        "track": tr,
                        "disease_family": item.get("disease_family", ""),
                        "predicted": choice or "NONE",
                        "expected": item["answer"],
                        "harm_mechanism": str(item.get("harm_mechanism") or ""),
                    }
                )

        reasoning = str(pred.get("reasoning") or "").strip().lower()
        if reasoning:
            kws = [str(k).lower() for k in item.get("rubric_keywords", []) if str(k).strip()]
            if kws:
                hits = sum(1 for k in kws if k in reasoning)
                kw_scores.append(hits / len(kws))

    def _pct(num: int, den: int) -> float | None:
        return round(100.0 * num / den, 2) if den > 0 else None

    overall_acc = _pct(total_correct, total_graded)
    mf_acc = _pct(track_stats["myelofibrosis"]["correct"], track_stats["myelofibrosis"]["graded"])
    cross_acc = _pct(track_stats["cross_orphan"]["correct"], track_stats["cross_orphan"]["graded"])
    transfer_gap = (
        round(cross_acc - mf_acc, 2)
        if (mf_acc is not None and cross_acc is not None)
        else None
    )
    cter_pct = _pct(harm_missed, harm_graded)
    kw_cov = round(100.0 * sum(kw_scores) / len(kw_scores), 2) if kw_scores else None
    composite = (
        round(0.8 * overall_acc + 0.2 * kw_cov, 2)
        if (overall_acc is not None and kw_cov is not None)
        else overall_acc
    )

    return {
        "benchmark": BENCHMARK_VERSION,
        "track_filter": track_filter,
        "benchmark_total_items": len(items),
        "graded_count": total_graded,
        "correct_count": total_correct,
        "unknown_ids_count": len(unknown_ids),
        "overall_accuracy_pct": overall_acc,
        "myelofibrosis_track_pct": mf_acc,
        "cross_orphan_track_pct": cross_acc,
        "transfer_gap_pct": transfer_gap,
        "critical_harm_graded": harm_graded,
        "critical_harm_missed": harm_missed,
        "cter_pct": cter_pct,
        "keyword_coverage_pct": kw_cov,
        "reasoning_items_evaluated": len(kw_scores),
        "composite_score_pct": composite,
        "track_breakdown": {
            t: {
                "graded": s["graded"],
                "correct": s["correct"],
                "accuracy_pct": _pct(s["correct"], s["graded"]),
                "cter_pct": _pct(s["harm_missed"], s["harm_graded"]),
            }
            for t, s in track_stats.items()
        },
        "category_breakdown": {
            c: {
                "graded": s["graded"],
                "correct": s["correct"],
                "accuracy_pct": _pct(s["correct"], s["graded"]),
            }
            for c, s in cat_stats.items()
        },
        "missed_critical_harms": missed_harm_events[:25],
    }


def _extract_open_value(raw: str) -> str:
    txt = str(raw or "").strip()
    m = re.search(r"FINAL_ANSWER\s*:\s*([^\n\r]+)", txt, re.IGNORECASE)
    if m:
        txt = m.group(1).strip()
    return txt.strip().strip("`").strip()


def _parse_float(raw: str) -> float | None:
    cleaned = re.sub(r"[\$,%\s]", "", str(raw or ""))
    m = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def _norm_token(raw: str) -> str:
    s = str(raw or "").strip().lower()
    s = re.sub(r"^p\.", "", s)
    s = re.sub(r"[\s_\-]+", "", s)
    return s


def score_open_frontier(
    items: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    label: str = "open_frontier",
) -> dict[str, Any]:
    item_map = {str(it["id"]).strip(): it for it in items}
    pred_map = {
        str(p.get("id", "")).strip(): p
        for p in predictions
        if str(p.get("id", "")).strip() in item_map
    }

    graded = 0
    correct = 0
    harm_graded = 0
    harm_missed = 0
    track_stats = {
        t: {"graded": 0, "correct": 0, "harm_graded": 0, "harm_missed": 0}
        for t in VALID_TRACKS
    }
    kw_scores: list[float] = []
    misses: list[dict[str, Any]] = []

    for iid, item in item_map.items():
        if iid not in pred_map:
            continue
        pred = pred_map[iid]
        raw_ans = pred.get("answer") or pred.get("final_answer") or pred.get("response") or ""
        extracted = _extract_open_value(str(raw_ans))
        atype = str(item.get("answer_type", "exact_token")).lower()
        tol = float(item.get("tolerance", 0.0) or 0.0)
        accepted = [str(a) for a in (item.get("accepted_answers") or [item.get("expected_answer", "")])]

        is_correct = False
        if atype in ("integer", "number", "float"):
            pval = _parse_float(extracted)
            exp = _parse_float(str(item.get("expected_answer", "")))
            if pval is not None and exp is not None:
                is_correct = abs(pval - exp) <= max(tol, 1e-6)
        else:
            pnorm = _norm_token(extracted)
            is_correct = any(pnorm == _norm_token(a) for a in accepted)

        graded += 1
        tr = item["track"]
        track_stats[tr]["graded"] += 1
        if is_correct:
            correct += 1
            track_stats[tr]["correct"] += 1
        else:
            misses.append(
                {
                    "id": iid,
                    "track": tr,
                    "disease_family": item.get("disease_family", ""),
                    "predicted": extracted,
                    "expected": item.get("expected_answer"),
                    "critical_harm": bool(item.get("critical_harm")),
                }
            )

        if item.get("critical_harm"):
            harm_graded += 1
            track_stats[tr]["harm_graded"] += 1
            if not is_correct:
                harm_missed += 1
                track_stats[tr]["harm_missed"] += 1

        reasoning = str(pred.get("reasoning") or pred.get("response") or "").strip().lower()
        if reasoning:
            kws = [str(k).lower() for k in item.get("rubric_keywords", []) if str(k).strip()]
            if kws:
                kw_scores.append(sum(1 for k in kws if k in reasoning) / len(kws))

    def _pct(num: int, den: int) -> float | None:
        return round(100.0 * num / den, 2) if den > 0 else None

    return {
        "benchmark": f"{BENCHMARK_VERSION} ({label})",
        "benchmark_total_items": len(items),
        "graded_count": graded,
        "correct_count": correct,
        "overall_accuracy_pct": _pct(correct, graded),
        "myelofibrosis_track_pct": _pct(track_stats["myelofibrosis"]["correct"], track_stats["myelofibrosis"]["graded"]),
        "cross_orphan_track_pct": _pct(track_stats["cross_orphan"]["correct"], track_stats["cross_orphan"]["graded"]),
        "critical_harm_graded": harm_graded,
        "critical_harm_missed": harm_missed,
        "cter_pct": _pct(harm_missed, harm_graded),
        "keyword_coverage_pct": round(100.0 * sum(kw_scores) / len(kw_scores), 2) if kw_scores else None,
        "misses": misses,
    }


def score_protocol_audit(
    items: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    item_map = {str(it["id"]).strip(): it for it in items}
    pred_map = {
        str(p.get("id", "")).strip(): p
        for p in predictions
        if str(p.get("id", "")).strip() in item_map
    }

    total_tp = 0
    total_fp = 0
    total_fn = 0
    exact_matches = 0
    graded = 0
    clean_graded = 0
    clean_fp_protocols = 0
    track_exact = {t: {"graded": 0, "exact": 0, "tp": 0, "fp": 0, "fn": 0} for t in VALID_TRACKS}
    audit_details: list[dict[str, Any]] = []

    for iid, item in item_map.items():
        if iid not in pred_map:
            continue
        pred = pred_map[iid]
        allowed = set(item.get("allowed_flaw_codes", []))
        expected = set(item.get("expected_flaw_codes", []))
        raw_pred = pred.get("flaw_codes")
        if raw_pred is None:
            raw_pred = pred.get("predicted_flaw_codes") or []
        if isinstance(raw_pred, str):
            raw_pred = [x.strip() for x in re.split(r"[,\s]+", raw_pred) if x.strip()]
        predicted = {str(c).strip().upper() for c in raw_pred if str(c).strip()}
        if allowed:
            predicted = {c for c in predicted if c in allowed}

        tp = len(predicted & expected)
        fp = len(predicted - expected)
        fn = len(expected - predicted)
        is_exact = predicted == expected

        graded += 1
        total_tp += tp
        total_fp += fp
        total_fn += fn
        if is_exact:
            exact_matches += 1

        tr = item["track"]
        track_exact[tr]["graded"] += 1
        track_exact[tr]["tp"] += tp
        track_exact[tr]["fp"] += fp
        track_exact[tr]["fn"] += fn
        if is_exact:
            track_exact[tr]["exact"] += 1

        if item.get("is_clean_control"):
            clean_graded += 1
            if fp > 0:
                clean_fp_protocols += 1

        if not is_exact:
            audit_details.append(
                {
                    "id": iid,
                    "track": tr,
                    "is_clean_control": bool(item.get("is_clean_control")),
                    "expected": sorted(expected),
                    "predicted": sorted(predicted),
                    "false_negatives": sorted(expected - predicted),
                    "false_positives": sorted(predicted - expected),
                }
            )

    def _pct(num: int, den: int) -> float | None:
        return round(100.0 * num / den, 2) if den > 0 else None

    prec = _pct(total_tp, total_tp + total_fp)
    rec = _pct(total_tp, total_tp + total_fn)
    f1 = (
        round(2.0 * prec * rec / (prec + rec), 2)
        if (prec is not None and rec is not None and (prec + rec) > 0)
        else 0.0
    )
    fn_cter = _pct(total_fn, total_tp + total_fn)

    return {
        "benchmark": f"{BENCHMARK_VERSION} (protocol_audit)",
        "benchmark_total_items": len(items),
        "graded_count": graded,
        "exact_set_match_count": exact_matches,
        "exact_set_match_pct": _pct(exact_matches, graded),
        "micro_precision_pct": prec,
        "micro_recall_pct": rec,
        "micro_f1_pct": f1,
        "fn_cter_pct": fn_cter,
        "clean_controls_graded": clean_graded,
        "clean_control_fp_protocols": clean_fp_protocols,
        "clean_control_fp_rate_pct": _pct(clean_fp_protocols, clean_graded),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "track_breakdown": {
            t: {
                "graded": s["graded"],
                "exact_set_match_pct": _pct(s["exact"], s["graded"]),
                "micro_f1_pct": round(200.0 * s["tp"] / (2 * s["tp"] + s["fp"] + s["fn"]), 2)
                if (2 * s["tp"] + s["fp"] + s["fn"]) > 0
                else None,
            }
            for t, s in track_exact.items()
        },
        "imperfect_audits": audit_details,
    }


def grade_via_api(
    predictions: list[dict[str, Any]],
    model_name: str,
    publish: bool = False,
) -> dict[str, Any]:
    payload = json.dumps(
        {
            "benchmark": "rare-tx-bench",
            "model_name": model_name,
            "publish_to_leaderboard": bool(publish),
            "predictions": predictions,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        GRADE_API_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "RareTxBench-Evaluator/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_self_test(test_path: Path, dev_path: Path) -> None:
    print(f"[self-test] Loading test split from {test_path} ...")
    test_items = load_jsonl(test_path)
    dev_items = load_jsonl(dev_path) if dev_path.exists() else None
    if dev_items is not None:
        print(f"[self-test] Loading dev split from {dev_path} ...")

    meta = validate_dataset(test_items, dev_items)

    # 1. Oracle ceiling (100% accuracy, 0% CTER)
    oracle_preds = [
        {
            "id": it["id"],
            "choice": it["answer"],
            "reasoning": " ".join(it["rubric_keywords"]),
        }
        for it in test_items
    ]
    oracle_res = score_predictions(test_items, oracle_preds)
    assert oracle_res["overall_accuracy_pct"] == 100.0, oracle_res
    assert oracle_res["myelofibrosis_track_pct"] == 100.0, oracle_res
    assert oracle_res["cross_orphan_track_pct"] == 100.0, oracle_res
    assert oracle_res["cter_pct"] == 0.0, oracle_res
    assert oracle_res["keyword_coverage_pct"] == 100.0, oracle_res

    # 2. Stratified 50% mock
    mock_preds = []
    for idx, it in enumerate(test_items):
        ans = it["answer"]
        wrong = VALID_CHOICES[(VALID_CHOICES.index(ans) + 1) % len(VALID_CHOICES)]
        mock_preds.append(
            {
                "id": it["id"],
                "choice": ans if idx % 2 == 0 else wrong,
                "reasoning": it["rubric_keywords"][0] if idx % 2 == 0 else "",
            }
        )
    mock_res = score_predictions(test_items, mock_preds)
    assert mock_res["overall_accuracy_pct"] == 50.0, mock_res

    print(
        f"[self-test] PASS — {meta['benchmark']}: {meta['test_count']} test items "
        f"(MF={meta['tracks']['myelofibrosis']}, Cross-Orphan={meta['tracks']['cross_orphan']}, "
        f"balance={meta['answer_balance']}, critical_harm={meta['critical_harm_items']}, "
        f"max_len_ratio={meta['max_option_length_ratio']}, "
        f"correct_longest={meta['correct_is_longest_pct']}%) + {meta['dev_count']} dev items; "
        f"oracle=100.0% (CTER=0.0%), mock=50.0% (CTER={mock_res['cter_pct']}%)."
    )


def main() -> int:
    default_test, default_dev = resolve_default_paths()
    parser = argparse.ArgumentParser(description="RareTxBench-v2.0 deterministic evaluator")
    parser.add_argument("--test-file", type=Path, default=default_test)
    parser.add_argument("--dev-file", type=Path, default=default_dev)
    parser.add_argument("--predictions", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--track", choices=("all", "myelofibrosis", "cross_orphan"), default="all")
    parser.add_argument("--open-frontier", action="store_true", help="Grade choice-free exact-answer open_frontier split.")
    parser.add_argument("--open-file", type=Path, default=default_test.parent / "open_frontier_test.jsonl")
    parser.add_argument("--raw-bio-compute", action="store_true", help="Grade raw_bio_compute scientific artifact split.")
    parser.add_argument("--raw-bio-file", type=Path, default=default_test.parent / "raw_bio_compute_test.jsonl")
    parser.add_argument("--bio-delta-live", action="store_true", help="Grade bio_delta_live temporal forensics split.")
    parser.add_argument("--bio-delta-file", type=Path, default=default_test.parent / "bio_delta_live_test.jsonl")
    parser.add_argument("--protocol-audit", action="store_true", help="Grade protocol_audit multi-flaw detection split.")
    parser.add_argument("--protocol-audit-file", type=Path, default=default_test.parent / "protocol_audit_test.jsonl")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--grade-via-api", action="store_true")
    parser.add_argument("--submit-anonymous-score", action="store_true")
    parser.add_argument("--model-name", type=str, default=None)
    args = parser.parse_args()

    if args.self_test:
        run_self_test(args.test_file, args.dev_file)
        return 0

    if not args.predictions:
        parser.error("Provide --predictions <file.jsonl> or --self-test.")

    preds = load_jsonl(args.predictions)

    if args.open_frontier:
        report = score_open_frontier(load_jsonl(args.open_file), preds, label="open_frontier")
    elif args.raw_bio_compute:
        report = score_open_frontier(load_jsonl(args.raw_bio_file), preds, label="raw_bio_compute")
    elif args.bio_delta_live:
        report = score_open_frontier(load_jsonl(args.bio_delta_file), preds, label="bio_delta_live")
    elif args.protocol_audit:
        report = score_protocol_audit(load_jsonl(args.protocol_audit_file), preds)
    elif args.grade_via_api or args.submit_anonymous_score:
        if not args.model_name:
            parser.error("--model-name is required with --grade-via-api or --submit-anonymous-score.")
        report = grade_via_api(
            preds,
            model_name=args.model_name,
            publish=bool(args.submit_anonymous_score),
        )
    else:
        items = load_jsonl(args.test_file)
        report = score_predictions(items, preds, track_filter=args.track)

    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.output_json:
        args.output_json.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
