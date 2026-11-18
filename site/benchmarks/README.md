# MyelofibrosisBench-v1 (`benchmarks/myelofibrosis_bench.jsonl`)

**MyelofibrosisBench-v1** is a 30-question, primary-literature-grounded, 100% deterministically gradable benchmark evaluating biomedical, structural-pharmacology, clinical-trial, and orphan-venture AI agents across the **Paired Myelofibrosis Flagships** of the Rare Disease Venture Atlas (`jak2-myelofibrosis` `ORPHA:824` and reversible `autoimmune-myelofibrosis` `ICD-10: D75.89`) and comparative myeloid/immunology mimics (`VEXAS` `ORPHA:597743`, `iMCD-TAFRO` `ORPHA:93685`, `Systemic Mastocytosis` `ORPHA:2467`, and `Telomere Biology Disorders` `ORPHA:1775`).

## Benchmark Architecture (5 Categories x 6 Questions = 30 Items)

| Category | IDs | Core Translational & Venture Competencies Tested |
| :--- | :--- | :--- |
| **`aimf_differential_triage`** | `mf-bench-001`..`006` | Separating reversible `JAK2/CALR/MPL`-negative Autoimmune Myelofibrosis (`AIMF` in `SLE`, `Sjogren's`, `Evans syndrome`, `PBC` — non-clustered megakaryocytes, polyclonal `CD8+/CD4+` lymphoid aggregates, 0% `ASXL1`/`SRSF2`/`U2AF1`/`EZH2` clonality, **74–80% human marrow reticulin resolution** on steroids/rituximab/MMF) from clonal `TN-PMF`, `UBA1` `VEXAS` (`NCT05027945`), and `iMCD-TAFRO` (`NCT03933904`) prior to myeloablative `allo-HSCT` or cytopenic `JAKi` misrouting. |
| **`iron_hepcidin_axis`** | `mf-bench-007`..`012` | Dissecting dual iron overload in `AIMF` & `PMF`: inflammatory `IL-6 -> JAK/STAT3` + `BMP6/ACVR1 -> HAMP (hepcidin) -> SLC40A1 (ferroportin)` macrophage iron trapping (`momelotinib` `NCT04173494`, `pacritinib` `NCT02055781`) vs transfusional parenchymal hemosiderosis (`NTBI`/`LPI`, `GPX4` ferroptosis, `deferasirox` chelation) vs `PV` erythrocytosis (`rusfertide` `NCT05210790` contraindication in anemic MF). |
| **`jak2_jh2_structural_selectivity`** | `mf-bench-013`..`018` | Structural & clinical pharmacology of `JAK2 V617F` (`F595`/`F537` pi-stacking in `PDB:4FVQ`/`4FVR` vs WT `PDB:4FVP`), pan-`JH1` `EPO`/`TPO` dose-limiting cytopenias (`PDB:3KRR`), Type I `Y1007/Y1008` heterodimer persistence vs Type II `DFG-out` breakers (`AJ1-11095` `NCT06343805`), selective `JH2` inhibitors (`INCB160058` `NCT06313593`) & `PROTAC` degraders (`PDB:8BAK`/`8EX2`), cell-surface mutant `CALR` mAbs (`INCA033989` `NCT06034002`), and BBB-excluded `KIT D816V` design (`PDB:4U0I`). |
| **`clinical_trial_forensics`** | `mf-bench-019`..`024` | Phase 2/3 endpoint forensics: why Week-24 `SVR35` + `TSS50` dissociate (`MANIFEST-2` `pelabresib` `NCT04603495`, `TRANSFORM-1` `navitoclax` `NCT04472598`), `IMpactMF` (`imetelstat` `NCT04576156`) OS primary endpoint tradeoffs, zero-washout add-on trial design (`POIESIS` `navtemadlin` `NCT06479135`), non-myelosuppressive `PIM1` (`nuvisertib` `NCT04181788`) & `XPO1` (`SENTRY` `selinexor` `NCT04562389`/`NCT05210790`) combinations, and continuous WSI reticulin morphometry. |
| **`orphan_venture_economics`** | `mf-bench-025`..`030` | FY2026 FDA Orphan Drug Act unit economics (~$4.68M PDUFA waiver, 25% ODTC tax credit, 7-yr exclusivity vs Rare Pediatric PRV boundaries), non-dilutive grant sequencing (`MPNRF`, `NIH/NCI SBIR`, `Blood Cancer United TAP`, `CDCN/Every Cure`, `ARPA-H`), 21st Century Cures CDS & RWE External Control Arm monetization, 505(b)(2) generic repurposing mechanics, and ethical patient-registry governance (`NCT07362225`). |

## Record Schema (`myelofibrosis_bench.jsonl`)

Every row is uniform JSONL compatible with Hugging Face Parquet auto-conversion and DuckDB:
- `id`: `"mf-bench-001"` .. `"mf-bench-030"`
- `category`: one of the 5 canonical categories above
- `difficulty`: `"medium"` or `"hard"`
- `question`: scenario-grounded clinical, structural, trial-design, or venture question
- `choices`: `{"A": "...", "B": "...", "C": "...", "D": "..."}`
- `correct_choice`: `"A"`, `"B"`, `"C"`, or `"D"`
- `required_reasoning_keywords`: 3–5 mechanistic/accession terms scored in free-text rationale rubrics
- `rationale`: detailed primary-literature explanation
- `primary_citations`: verified `NCT`, `PMID`, `GEO`, `PDB`, and `ORPHA` identifiers

## Quickstart Evaluation (Zero External Dependencies)

```bash
# 1. Run built-in schema, citation, zero-PII, and mock-agent self-tests
PYTHONDONTWRITEBYTECODE=1 python3 benchmarks/evaluate_agent.py --self-test

# 2. Score your agent's predictions JSONL ({id, choice, reasoning})
PYTHONDONTWRITEBYTECODE=1 python3 benchmarks/evaluate_agent.py \
  --predictions my_agent_predictions.jsonl \
  --output-json score_report.json

# 3. Optional, explicitly opt-in anonymous aggregate telemetry (zero PII/prompts sent)
PYTHONDONTWRITEBYTECODE=1 python3 benchmarks/evaluate_agent.py \
  --predictions my_agent_predictions.jsonl \
  --submit-anonymous-score \
  --model-name "claude-sonnet-4-5-mcp"
```
