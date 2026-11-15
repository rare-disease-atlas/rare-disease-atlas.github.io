# 01 — Science & Clinical Gaps in `JAK2 V617F` Myelofibrosis

> **Dossier Purpose (`rare-disease-atlas.github.io`):** Objective, citation-verified clinical and molecular briefing for founders (Public Health, Computational/AI-Bio, Venture/Novel Financing) and autonomous AI research agents evaluating high-leverage intervention points in **JAK2+ Myelofibrosis** (current through late 2026).

---

## 1. Epidemiology, Demographics & Molecular Landscape

Myelofibrosis (MF) is a clonal, Philadelphia chromosome-negative ($BCR::ABL1$-negative) myeloproliferative neoplasm (MPN) arising in hematopoietic stem and progenitor cells (HSPCs). It encompasses **Primary Myelofibrosis (PMF)**—including pre-fibrotic (pre-PMF) and overt fibrotic stages—and **Secondary Myelofibrosis**, which evolves from antecedent Polycythemia Vera (**post-PV MF**) or Essential Thrombocythemia (**post-ET MF**). Pathologically, aberrant megakaryocytes and clonal myeloid progenitors secrete profibrotic and proinflammatory cytokines ($\text{TGF-}\beta$, $\text{PDGF}$, $\text{FGF}$, $\text{IL-1}\beta$, $\text{IL-6}$, $\text{TNF-}\alpha$, $\text{S100A8/A9}$ alarmins), reprogramming bone marrow mesenchymal stromal cells into myofibroblasts that deposit dense reticulin and collagen fibers, destroying normal medullary hematopoiesis and forcing extramedullary hematopoiesis in the spleen and liver.

### Verified Epidemiological Metrics (US & Global)

| Metric | Verified Estimate | Notes & Clinical Implications |
| :--- | :--- | :--- |
| **US Annual Incidence (Total MF)** | **1.0 – 1.56 per 100,000** person-years | Includes both PMF and post-PV / post-ET secondary MF (~3,500–5,000 new US diagnoses/year). |
| **US Annual Incidence (PMF only)** | **0.3 – 0.44 per 100,000** person-years | Secondary evolution from PV (~10–15% at 15 yrs) and ET (~4–11% at 15 yrs) accounts for a substantial share of incident cases. |
| **Global / European Incidence** | **0.3 – 1.9 per 100,000** person-years | Comparable across North America, EU, UK, and Australia; underdiagnosed in low/middle-income settings. |
| **US Diagnosed Prevalence** | **~4 – 6 per 100,000** (**~15,000 – 25,000+** living patients) | Well below the FDA Orphan Drug Designation statutory ceiling of **200,000 US patients**. |
| **Median Age at Diagnosis** | **65 – 70 years** | Crucial clinical bottleneck: advanced age and age-associated comorbidities lock the vast majority out of myeloablative transplant. |
| **Sex Distribution** | **~55% – 63% male** (~1.5:1 M:F in PMF) | Male sex independently correlates with higher cytopenic/molecular risk profiles in several cohorts. |

### Canonical Driver Mutation Architecture (~90% Mutually Exclusive Drivers)

Roughly **90%** of MF patients carry one of three somatic phenotypic driver mutations that constitutively activate **JAK2-STAT3/STAT5**, MAPK/ERK, and PI3K/AKT signaling:

1. **`JAK2 V617F` (~50% – 60% of PMF and post-ET MF; >95% of post-PV MF):**
   - Point substitution ($\text{G1849T} \rightarrow \text{Val617Phe}$) in exon 14 encoding the **JH2 pseudokinase domain** of Janus kinase 2.
   - Under normal physiology, JH2 allosterically autoinhibits the catalytic **JH1 kinase domain**. `V617F` stabilizes an aberrant $\pi$-stacking/hydrophobic conformation in JH2 (involving Phe595/Phe617 and the JH2–JH1 linker), driving ligand-independent constitutive homodimeric signaling via homodimeric cytokine receptors (**EPOR**, **MPL/TPOR**, **GCSFR**).
   - Mitotic recombination at chromosome `9p` frequently converts heterozygous clones into `9p` uniparental disomy (**UPD / homozygosity**), elevating variant allele frequency (**VAF >50%**) and accelerating fibrotic and thrombotic progression.
2. **`CALR` Exon 9 Indels (~20% – 35% of PMF and post-ET MF):**
   - $+1\text{ bp}$ frameshift insertions/deletions (most commonly **Type 1** 52-bp deletion `L367fs*46` or **Type 2** 5-bp insertion `K385fs*47`) that create a novel positively charged C-terminal neo-epitope lacking the ER-retention KDEL motif. Mutant CALR complexes with **MPL** in the secretory pathway and traffics to the **cell surface**—making `mutCALR` druggable by extracellular monoclonal antibodies and T-cell engagers, *unlike* strictly intracellular `JAK2 V617F`.
3. **`MPL` Exon 10 Mutations (~5% – 8% of PMF and post-ET MF):**
   - Gain-of-function substitutions at the juxtamembrane tryptophan codon (`MPL W515L/K/A`) or transmembrane `S505N`, constitutively dimerizing the thrombopoietin receptor.
4. **Triple-Negative MF (~10% of PMF):**
   - Lacks canonical `JAK2`, `CALR`, and `MPL` drivers; associated with significantly worse overall survival and higher rates of leukemic transformation.

### Co-Occurring High-Molecular-Risk (HMR) & Subclonal Drivers
Up to **40%–50%+** of MF patients carry somatic co-mutations in epigenetic regulators, spliceosome machinery, or signaling genes tracked in modern prognostic scores (**MIPSS70+ v2.0**):
- **Epigenetic:** `ASXL1` (most frequent HMR lesion, ~25–35%), `EZH2`, `IDH1`, `IDH2`, `TET2`, `DNMT3A`
- **RNA Splicing:** `SRSF2`, `U2AF1` (notably `Q157`), `SF3B1`
- **Genomic Instability / Blast Transformation:** `TP53` (especially multi-hit `TP53` driven by chronic inflammatory selection), `RUNX1`, `NRAS`/`KRAS`, `CBL`

---

## 2. Current Standard of Care: The 4 FDA-Approved JAK Inhibitors & Exact Failure Modes

All four currently FDA-approved targeted therapies for myelofibrosis are **Type I ATP-competitive small molecules** binding the active conformation of the **JH1 catalytic kinase domain** of JAK2 (plus varying off-/co-targets).

### Comparison of Approved JAK Inhibitors (Through Late 2026)

| Drug (Brand, Sponsor) | FDA Approval Date & Pivotal Trial(s) | Primary Kinase Targets | Specific Label Niche & Clinical Strengths | Major Toxicities & Specific Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Ruxolitinib** (*Jakafi* / *Jakafi XR*, Incyte) | **Nov 16, 2011** (*Jakafi XR* once-daily approved **May 1, 2026**)<br>COMFORT-I (`NCT00952289`), COMFORT-II (`NCT00934544`) | JAK1, JAK2 | Intermediate- or high-risk MF. Gold-standard frontline backbone; rapid spleen volume reduction (**SVR35** ~42% at Wk 24 in COMFORT-I) & symptom relief (**TSS50** ~46%); modest pooled OS extension via cachexia/inflammation reversal. | Dose-dependent **anemia** (Hb drop peaks Wks 8–12) and **thrombocytopenia**; herpes zoster/opportunistic infections, non-melanoma skin cancers, weight gain/hyperlipidemia; acute cytokine **withdrawal syndrome** on abrupt stop. |
| **Fedratinib** (*Inrebic*, BMS) | **Aug 16, 2019**<br>JAKARTA (`NCT01437787`), JAKARTA-2 (`NCT01523171`) | JAK2, FLT3, BRD4 (weak) | Intermediate-2 or high-risk MF (JAKi-naïve or post-ruxolitinib). Active salvage spleen/symptom option after ruxolitinib resistance/intolerance. | **FDA Boxed Warning** for serious/fatal **encephalopathy (Wernicke's)** requiring mandatory thiamine ($B_1$) monitoring/repletion; high GI toxicity (diarrhea, nausea/vomiting via FLT3); myelosuppression. |
| **Pacritinib** (*Vonjo*, Sobi / CTI BioPharma) | **Feb 28, 2022** *(Accelerated Approval)*<br>PERSIST-1 (`NCT01773187`), PERSIST-2 (`NCT02055781`) | JAK2, IRAK1, ACVR1 *(spares JAK1)* | Intermediate- or high-risk MF with **severe thrombocytopenia (platelets $<50 \times 10^9/\text{L}$)**. Delivers full-dose NF-$\kappa$B/IRAK1 + JAK2 suppression in cytopenic MF where ruxolitinib cannot be safely dosed. | GI adverse events (diarrhea, nausea), bleeding/hemorrhage risk, QTc prolongation precautions; confirmatory trial obligations ongoing. |
| **Momelotinib** (*Ojjaara*, GSK) | **Sept 15, 2023**<br>MOMENTUM (`NCT04173494`), SIMPLIFY-1/2 | JAK1, JAK2, **ACVR1 (ALK2)** | Intermediate- or high-risk MF in adults **with anemia** (frontline or JAKi-experienced). ACVR1 inhibition suppresses hepatic **hepcidin**, mobilizing sequestered iron to restore erythropoiesis and **RBC transfusion independence**. | Thrombocytopenia, diarrhea, bacterial infections, hepatotoxicity, peripheral neuropathy; does not eradicate mutant HSC clones. |

---

### Why Approved JAK Inhibitors Are Palliative—Not Curative

1. **Zero Wild-Type vs. Mutant Selectivity (The On-Target Cytopenia Trap):**
   - Catalytic JH1 domains of wild-type (`WT`) JAK2 and `JAK2 V617F` are **100% identical in primary sequence** around the ATP-binding cleft.
   - Normal human red blood cell production (**EPOR**) and platelet production (**TPOR/MPL**) strictly require `WT JAK2` homodimer signaling. Consequently, every Type I JH1 inhibitor hits a hard therapeutic ceiling: pushing exposure high enough to fully extinguish `JAK2 V617F` signaling causes severe, dose-limiting **iatrogenic anemia and thrombocytopenia**.
2. **JAK2 Heterodimer "Persistence" Resistance:**
   - Chronic exposure to Type I JAK inhibitors stabilizes JAK2 in an active-like conformation with hyperphosphorylation of the activation loop (`Tyr1007/1008`), promoting trans-activation of `JAK2` via heterodimerization with **JAK1** or **TYK2**. Malignant clones survive and proliferate right through continuous ruxolitinib blockade without needing secondary `JAK2` gatekeeper mutations.
3. **Failure to Eradicate Malignant Stem Cells or Reverse Fibrosis:**
   - Long-term ruxolitinib therapy produces minimal, slow, or absent reductions in `JAK2 V617F` **variant allele frequency (VAF)** in most patients and only rare/modest improvements in bone marrow reticulin/collagen fibrosis grade. Clonal architecture continues to evolve underneath symptom control, acquiring `ASXL1`, `RAS`, or `TP53` subclonal hits.
4. **The "Ruxolitinib Discontinuation Cliff":**
   - Roughly **50% of patients discontinue ruxolitinib within 3 years** (and ~70–75% by 5 years) due to loss of spleen/symptom response, progressive cytopenias, or leukemic transformation.
   - Across multi-center real-world and trial registries, **median overall survival (OS) after ruxolitinib discontinuation is dismal: 11 to 23 months** (~22–27 months if discontinued in chronic phase, plunging to **3 to 4 months** upon transformation to **blast-phase MPN / secondary AML**, defined by $\ge 20\%$ blasts).
5. **The Allogeneic Stem Cell Transplant (Allo-HSCT) Bottleneck:**
   - Allo-HSCT remains the **sole curative intervention** capable of clearing the mutant HSPC clone and resolving marrow fibrosis (5-year OS **~50% – 60%** at experienced centers).
   - Yet **fewer than 10% – 15% of eligible MF patients ever undergo transplant**. Why?
     - **Age & Comorbidity Mismatch:** Median diagnosis age is 65–70 years; even with Reduced-Intensity Conditioning (RIC) pushing select fit recipients past age 70, cardiovascular/renal/hepatic comorbidities (high HCT-CI) disqualify most patients.
     - **Lethal Upfront Risk:** **Non-relapse mortality (NRM) remains 20% – 36%** in the first 1–2 years (driven by graft failure in fibrotic/osteosclerotic marrow, sinusoidal obstruction syndrome, portal hypertension, severe infections, and acute/chronic **GVHD**), plus a **15% – 30% post-transplant relapse rate**.
     - **The Timing Paradox:** Patients feeling temporarily functional on a JAK inhibitor defer a procedure carrying a ~1-in-4 upfront mortality risk—often until clonal evolution or performance-status collapse renders them permanently transplant-ineligible.

---

## 3. Next-Generation & Combination Pipeline (2024–2026 Verified Statuses)

> [!IMPORTANT]
> **Why Objectivity Matters Here:** Between 2024 and late 2026, myelofibrosis experienced *both* historic first-in-class breakthroughs (mutant-selective `JAK2 V617F` JH2 inhibitors entering human trials) *and*sobering Phase 3 casualties (**navitoclax discontinued; imetelstat Phase 3 stopped for OS futility; pelabresib US filing delayed over TSS50/blast-phase questions**). Founders and AI agents who understand *why* those late-stage programs stumbled gain an asymmetric advantage in designing next-wave therapeutics, trials, and biomarker tools.

### A. Mutant-Selective `JAK2 V617F` (JH2 Allosteric) & Type II JAK2 Inhibitors

- **`INCB160058` (Incyte / Prelude Therapeutics collaboration) — Phase 1 (`NCT06313593`):**
  - **Mechanism:** First-in-class, orally bioavailable small molecule engineered to bind selectively into the **JH2 pseudokinase domain pocket** harboring `V617F`, locking mutant JAK2 in an autoinhibited state while sparing `WT JAK2` cytokine signaling.
  - **2024–2026 Status:** Active Phase 1 dose-escalation and expansion (`NCT06313593`) across `JAK2 V617F`-positive MF, PV, and ET (monotherapy and combination). Preclinical data demonstrated selective elimination of mutant HSPCs without suppressing normal erythropoiesis/megakaryopoiesis.
- **`AJ1-11095` (Ajax Therapeutics) — Phase 1 AJX-101 (`NCT06343805`):**
  - **Mechanism:** Computational structure-guided, highly selective **Type II JAK2 inhibitor** that binds the inactive **DFG-out** conformation of JAK2—specifically designed to prevent and reverse the Type I JAKi "persistence" state and reduce mutant allele burden.
  - **2024–2026 Status:** Active Phase 1 (`NCT06343805`) in MF patients who failed prior Type I JAK inhibitors; early clinical updates presented at major hematology congresses (EHA/ASH) showed encouraging spleen/symptom activity and tolerability in heavily pretreated patients.

### B. Epigenetic, Apoptotic & Nuclear-Transport Combination Backbones

- **Pelabresib (`CPI-0610`, Novartis / MorphoSys) — BET Bromodomain Inhibitor — Phase 3 `MANIFEST-2` (`NCT04603495`):**
  - **Mechanism:** Inhibits BRD2/3/4 bromodomains to downregulate NF-$\kappa$B-driven inflammatory cytokines and megakaryocytic differentiation programs alongside ruxolitinib.
  - **2024–2026 Status (Mixed / Regulatory Nuance):** In JAKi-naïve MF (`MANIFEST-2`, *Active, not recruiting*), pelabresib + ruxolitinib nearly doubled Week-24 **SVR35** (~65.9% vs 35.2%) and improved anemia/marrow fibrosis biomarkers, with 96-week follow-up confirming durable spleen responses. **However**, it narrowly missed statistical significance on the key secondary **TSS50** endpoint at Week 24 and drew regulatory scrutiny over a small numerical imbalance in leukemic/blast-phase events—leading Novartis to advance EU filings while engaging FDA on longer-term follow-up data rather than an immediate US accelerated approval.
- **Navitoclax (AbbVie) — BCL-xL / BCL-2 Inhibitor — Phase 3 `TRANSFORM-1` (`NCT04472598`) — [DISCONTINUED]:**
  - **Mechanism:** Pro-apoptotic BH3 mimetic targeting BCL-xL/BCL-2 survival dependency in `JAK2 V617F` clones.
  - **2024–2026 Status (Discontinued):** `TRANSFORM-1` doubled Week-24 **SVR35** (63.2% vs 31.5% with ruxolitinib alone), **but failed to improve TSS50 or overall survival**, while on-target BCL-xL inhibition of circulating platelets caused frequent reversible **thrombocytopenia**. AbbVie **formally discontinued** the navitoclax MF development program in late 2024/early 2025 (with full `TRANSFORM-1` primary data published in *Blood* in 2026).
- **Selinexor (Karyopharm) — XPO1 Nuclear Export Inhibitor — Phase 3 `SENTRY` / `XPORT-MF-034` (`NCT04562389`):**
  - **Mechanism:** Blocks Exportin-1 (XPO1), retaining tumor suppressors (p53, I$\kappa$B, FOXO) in the nucleus and attenuating non-canonical STAT/AKT survival pathways.
  - **2026 Status:** In **March 2026**, topline results from frontline `SENTRY` ($n=353$, selinexor 60 mg + ruxolitinib vs placebo + ruxolitinib) **met the first co-primary endpoint of SVR35** (~50% vs 28%), **missed the second co-primary endpoint of Absolute TSS divergence**, and at **EHA June 2026** revealed a striking early **OS signal (>50% hazard reduction)** plus deeper VAF reductions, prompting planned FDA sNDA discussions.
- **Navtemadlin (`KRT-232`, Kartos Therapeutics) — MDM2 Inhibitor — Phase 3 `BOREAS` (`NCT03662126`) & `POIESIS` (`NCT06479135`):**
  - **Mechanism:** Disrupts MDM2–p53 interaction in **`TP53` wild-type** MF CD34+ cells to trigger p53-mediated apoptosis of malignant progenitors.
  - **2024–2026 Status:** In JAKi-relapsed/refractory `TP53`-WT MF (`BOREAS`), navtemadlin monotherapy nearly tripled SVR35 and doubled TSS50 vs Best Available Therapy alongside VAF and marrow fibrosis reductions. Simultaneously advancing in Phase 3 **`POIESIS` (`NCT06479135`)** as an add-on for JAKi-naïve patients having a suboptimal response to ruxolitinib. *(Caveat: strictly requires `TP53`-WT status; theoretical risk of selecting pre-existing `TP53`-mutant subclones requires longitudinal sequencing vigilance).*
- **Bomedemstat (`MK-3543` / `IMG-7289`, Merck) — LSD1 Demethylase Inhibitor (`NCT06351631` extension):**
  - **Mechanism:** Epigenetically silences GFI1b/LSD1 complexes essential for pathological megakaryocyte maturation and platelet/cytokine overproduction.
  - **2024–2026 Status:** Demonstrated symptom improvement, spleen stabilization, and stable/improved marrow fibrosis in Phase 2 MF cohorts; Merck expanded Phase 3 registration trials in Essential Thrombocythemia (Shorespan-007) alongside ongoing long-term MPN extension protocols (`NCT06351631`).

### C. Telomerase, PIM Kinase, Stromal/Antifibrotic & Immunotherapy Modalities

- **Imetelstat (*Rytelo*, Geron) — Telomerase Inhibitor — Phase 3 `IMpactMF` (`NCT04576156`) — [STOPPED FOR FUTILITY]:**
  - **Mechanism:** Oligonucleotide competitively inhibiting hTERT telomerase enzymatic activity in hyperproliferative malignant clones.
  - **October 2026 Status (Major Setback):** `IMpactMF` was the landmark first Phase 3 MF trial using **Overall Survival (OS)** as its primary endpoint in JAKi-relapsed/refractory MF. In **October 2026**, Geron **discontinued `IMpactMF`** following an Independent Data Monitoring Committee (IDMC) recommendation that the trial was unlikely to achieve its primary OS endpoint (its separate FDA approval in lower-risk MDS remains intact).
- **Nuvisertib (`TP-3654`, Sumitomo Pharma) — Selective PIM1 Kinase Inhibitor — Phase 1/2 (`NCT04176198`):**
  - **Mechanism:** Inhibits PIM1 kinase downstream of JAK/STAT and FLT3, suppressing cap-dependent translation, apoptosis resistance, and $\text{TGF-}\beta$-linked fibrotic cytokine loops **without suppressing normal hematopoiesis**.
  - **2025–2026 Status:** Holds **FDA Fast Track Designation**. Phase 1/2 updates across monotherapy and combinations (with ruxolitinib or momelotinib) showed **no dose-limiting myelosuppression** (sparing platelets and hemoglobin) alongside encouraging SVR, TSS50, and cytokine reductions.
- **TGF-$\beta$ Superfamily Ligand Traps & Direct Antifibrotics — Luspatercept (`INDEPENDENCE`, `NCT04717414` / Phase 2 `NCT03194542`), Elritercept, AVID200:**
  - **Status:** BMS's Phase 3 **`INDEPENDENCE` (`NCT04717414`)** evaluating **luspatercept** (*Reblozyl*) for transfusion-dependent anemia on concomitant JAKi therapy **narrowly missed statistical significance** on its primary 12-week RBC transfusion independence endpoint in 2025 (despite meaningful reductions in transfusion burden). Selective $\text{TGF-}\beta 1/3$ traps (e.g., `AVID200`), LOXL2 inhibitors, and alarmin (`S100A8/A9` / `Tasquinimod` / `GLI1`) stromal disruptors have shown biological proof-of-concept, **leaving true stromal fibrosis-reversing therapy completely unapproved and wide open**.
- **The Immunotherapy Contrast — `INCA033989` (Incyte, `NCT06034002`) vs. `JAK2 V617F`:**
  - In `CALR`-mutant ET/MF, Incyte's Fc-silent anti-`mutCALR` monoclonal antibody **`INCA033989` (`NCT06034002`)** delivered rapid spleen/anemia responses and dramatic VAF reductions in 2025–2026, validating that **selective clonal depletion reverses MPN pathology**.
  - **Why `JAK2 V617F` Needs Different Engineering:** Because `JAK2 V617F` is strictly **intracellular** (and its 9-mer/10-mer neoantigen presentation across common HLA alleles is weak/inconsistent), conventional surface mAbs cannot see it. Eradicating `JAK2 V617F` clones therefore demands **allosteric JH2 small molecules, mutant-selectiveJH2-directed PROTACs/molecular glues, synthetic-lethal combinations, or ultra-high-affinity HLA-restricted TCR-mimetic biologics**.

---

## 4. Summary Matrix of High-Value White Space for Builders

| Unmet Clinical / Biological Gap | Why Incumbents Failed Here | Concrete Target Opportunity |
| :--- | :--- | :--- |
| **Selective `JAK2 V617F` Clonal Eradication** | Type I JH1 inhibitors block `WT JAK2`, causing dose-limiting anemia/thrombocytopenia before clearing mutant HSCs. | Next-gen **JH2 allosteric inhibitors**, **JH2-targeted heterobifunctional degraders (PROTACs)**, and **Type II DFG-out binders** sparing `WT JAK2`. |
| **True Bone Marrow Fibrosis Reversal** | Anti-JAKs quiet systemic cytokines (`IL-6`/`TNF`) but poorly reprogram activated `GLI1+`/`Lepr+` myofibroblasts or cross-linked collagen. | Multi-omics target discovery in **megakaryocyte–stromal crosstalk** (`S100A8/A9`, `TGF-β1/3`, `PIM1`, `LOXL`, mechanotransduction) paired with AI digital pathology quantification of reticulin remodeling. |
| **Preventing `TP53` / HMR Leukemic Progression** | Chronic inflammation + certain cytotoxic/MDM2 pressures select for multi-hit `TP53` or `RAS` blast-phase clones (OS 3–4 mos). | Early longitudinal single-cell / liquid-biopsy risk stratification + inflammation-resolving combos that suppress clonal fitness advantage. |
| **Endpoint Discordance (`SVR35` vs. `TSS50` vs. `OS`)** | `TRANSFORM-1`, `MANIFEST-2`, and `SENTRY` all hit `SVR35` while missing strict `TSS50` thresholds; `IMpactMF` failed on `OS`. | Wearables + continuous high-frequency ePROs + validated composite surrogate biomarkers (VAF + digital marrow morphology + cytokine panels) for regulatory/trial optimization. |
