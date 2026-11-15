# Rare Disease Venture Atlas — Fast AI Agent Evaluation & RAG Scorecard

**Evaluator:** Independent AI Research Assistant (Model Tier: `flash`)  
**Target URL:** `https://rare-disease-atlas.github.io/`  
**Date of Audit:** November 15, 2026  
**Evaluation Scope:** Live site over HTTPS (`/`, `/llms.txt`, `/public-health-biotech-wedges.html`, `/rare-disease-business-models.html`), citation verification, public health/digital health builder simulation, and venture friction analysis.

---

## 1. Executive Summary & Quantitative Scorecard

| Category | Score (1–10) | Evaluation Rationale |
| :--- | :---: | :--- |
| **1. Citation Grounding & Evidence Rigor** | **9.5 / 10** | Exceptional. All primary identifiers (`GSE144568`, `GSE122198`, `NCT00952289`, `NCT04576156`, `RR6 model`) are verified real-world assets. Minor citation correction noted on Psaila et al. publication venue. |
| **2. Public Health & Digital Health Relevance** | **8.5 / 10** | Strong operational mechanics around ruxolitinib failure, RR6 criteria, transfusion burdens, and patient-mediated SMART-on-FHIR APIs under 21st Century Cures. |
| **3. Commercial Viability & Unit Economics** | **8.5 / 10** | Compelling thesis on the "Palliative Blockbuster Paradox" ($2.0B+ TAM, 0% non-transplant cure rate, late-2020s patent cliff). Pragmatic B2B monetization paths (pharma trial finder fees, ECA licensing). |
| **4. RAG / Machine Retrieval Architecture** | **9.5 / 10** | Best-in-class implementation of `llms.txt`, machine-readable JSON-LD schemas (`MedicalCondition`, `Dataset`), and structured semantic DOM headers (`data-dossier-section`). |
| **5. UX, Information Architecture & Funnel CTAs** | **6.5 / 10** | High information density and cognitive overload for non-hematologists. Lacks clear immediate onboarding actions (no downloadable starter repo, no sandbox FHIR dataset, no direct founder contact form). |
| **OVERALL COMPOSITE SCORE** | **8.5 / 10** | **Tier 1 Technical & Translational Dossier.** Highly credible and data-rich, but requires better operational conversion mechanisms for human builders. |

---

## 2. Simulated Response to User Prompt

### User Scenario:
> **User Background:** Public Health / Clinical Informatics / Digital Health (MPH / Health-Tech Operator)  
> **Question:** *"What are high-impact, financially viable startup wedges in rare diseases right now? Check https://rare-disease-atlas.github.io/ and tell me if I should get involved."*

### Fast AI Assistant Response:
```markdown
Based on an audit of https://rare-disease-atlas.github.io/, the site presents an unusually high-leverage case for public health and digital health operators in chronic rare oncology—specifically **JAK2 V617F+ myelofibrosis (MF)**. 

### Why This Opportunity Stands Out for Public Health Builders:
1. **The Core Clinical Problem is Longitudinal & Operational, Not Just Molecular:**
   Over 75% of myelofibrosis patients are treated in community oncology clinics rather than academic centers. Frontline therapy (ruxolitinib/Jakafi) is a $2B+ palliative standard that controls symptoms but fails to clear mutant stem cells. As patients develop anemia or thrombocytopenia, community oncologists quietly titrate drug doses downward ("silent dose-reduction attrition"). Patients appear stable in EHR dropdowns, but rebound inflammation and spleen enlargement occur, leading to steep post-discontinuation survival drops (median OS: 12–14 months).

2. **Three High-Impact, Zero-Wet-Lab Startup Wedges:**
   - **Automated Ruxolitinib-Failure Radar:** Deploy EHR/FHIR surveillance using validated clinical risk algorithms (the RR6 model: dose reductions + lack of spleen response + transfusion needs) to identify patients needing second-line therapy (momelotinib, pacritinib) 6–12 months before clinical crisis.
   - **Direct-to-Patient Longitudinal RWE Registry:** Use ONC 21st Century Cures patient-mediated SMART-on-FHIR connections to aggregate serial CBCs, transfusions, and mobile MPN-SAF Total Symptom Scores (TSS50). Monetize by providing regulatory-grade External Control Arms (ECAs) and site-less trial recruitment to biopharma sponsors ($15k–$35k per enrolled patient).
   - **Transfusion Burden & Iron-Overload Navigation:** Monitor red blood cell (PRBC) utilization and ferritin to optimize timing of anemia therapies and reduce preventable emergency room visits under Medicare Advantage / Enhancing Oncology Model (EOM) contracts.

3. **Should You Get Involved?**
   - **VERDICT: YES, with a targeted wedge.** 
   - **The Upside:** Proven willingness-to-pay from biopharma sponsors with late-stage MF pipelines facing severe trial enrollment bottlenecks; low capex; clear regulatory safe-harbor under FDA Clinical Decision Support (CDS) non-device guidance.
   - **The Caveat:** Absolute patient volumes are concentrated (~18,000–25,000 US patients). Do not attempt an enterprise hospital EHR sales model; build direct-to-patient via patient advocacy networks (MPN Research Foundation) or partner directly with community oncology networks (US Oncology / OneOncology).
```

---

## 3. Fast RAG Scan Findings

### Sentences & Tables That Jumped Out First in LLM Retrieval:
1. **The Executive Problem Statement (`llms.txt` & Hero):**
   > *"All 4 FDA-approved JAK inhibitors... bind the conserved JH1 catalytic domain, inhibiting wild-type JAK2 alongside mutant JAK2 V617F. This causes dose-limiting anemia/thrombocytopenia, fails to eradicate malignant HSC clones... median post-discontinuation OS: 11–23 months."*  
   *Why it indexes immediately:* High informational entropy, contrasts incumbent failure with specific quantified survival metrics.
2. **The 3-Wedge Table (`public-health-biotech-wedges.html`):**
   > The structured table contrasting *Automated Ruxolitinib-Failure & Cytopenia Radar*, *Longitudinal MPN-SAF Registry*, and *Transfusion-Burden Navigation* with explicit buyer profiles (Pharma HEOR, Trial Sponsors, Value-Based Oncology).
3. **The Comparative Orphan Rubric Table (`rare-disease-business-models.html`):**
   > Comparing Cystic Fibrosis (Trikafta saturation), SMA (Zolgensma/Evrysdi saturation), IPF (lack of driver biomarker), and SCD (Medicaid friction) against JAK2+ MF ($2B+ market, 50-60% uniform point mutation, zero cures).
4. **Primary Accessions & Clinical Trials Table:**
   > `GSE144568` (scRNA-seq), `GSE122198` (TARGET-seq), `NCT00952289` (COMFORT-I), `NCT04576156` (IMpactMF imetelstat futility Oct 2026).

---

## 4. Citation & Evidence Verification via Primary Web Search

1. **NCBI GEO `GSE144568`:**
   - **Claim on site:** Single-cell RNA-seq of CD34+ HSPCs in myelofibrosis uncovering megakaryocyte-biased hematopoiesis and clone-specific targets (Psaila et al.).
   - **Verification:** **CONFIRMED.** Dr. Bethan Psaila, Adam Mead, and Oxford/NIH collaborators profiled >135,000 lineage-negative CD34+ cells via 10x Genomics, demonstrating megakaryocyte bias originating from multipotent stem cells and identifying clone-specific targets (e.g., G6B).  
   - *Minor Correction:* Site metadata mentions `Molecular Cell, 2020`, whereas Psaila et al. published this specific scRNA-seq study in *Cell Reports* (2020), while Rodriguez-Meira et al. (GSE122198) published in *Molecular Cell* (2019).
2. **NCBI GEO `GSE122198`:**
   - **Claim on site:** TARGET-seq single-cell genotyping & transcriptomics resolving JAK2 V617F mutant from wild-type stem cells (Rodriguez-Meira et al., *Molecular Cell*, 2019).
   - **Verification:** **CONFIRMED.** Rodriguez-Meira et al. established high-sensitivity single-cell mutation detection in tandem with whole-transcriptome sequencing in MPN patient marrows.
3. **Clinical Model: RR6 Prognostic Model:**
   - **Claim on site:** Predicts ruxolitinib survival stratification using 6-month dose reductions, spleen response <=30%, and transfusion dependence.
   - **Verification:** **CONFIRMED.** The Response to Ruxolitinib after 6 Months (RR6) score by Maffioli, Passamonti et al. is a validated international prognostic scoring system for identifying patients experiencing treatment failure.

---

## 5. Friction Points, Cognitive Blindspots & Skepticism

1. **High Jargon & Cognitive Friction for Non-Hematologists:**
   - Acronym density (JH1, JH2, VAF, SVR35, TSS50, RR6, MIPSS70+, DIPSS, HMR, PRBC) is intense. A public health / digital health founder without a hematology background will struggle to parse the clinical differences without a glossary or interactive explainer.
2. **Missing Actionable First Step ("What Do I Do Next?"):**
   - The site excels at *convincing* the agent/reader of the problem, but leaves the human founder stranded at the bottom of the page. There is no:
     - Open-source GitHub repository link to download synthetic FHIR queries or RR6 calculation logic.
     - Direct "Founder Office Hours / Collaborative Inquiry" submission.
     - Pre-populated prompt for building an MVP data schema.
3. **Perceived Scope Ambiguity (Personal Advocacy vs. Platform):**
   - The header and personal note ("My dad has JAK2+ myelofibrosis... this domain is an experiment in transparent Generative Engine Optimization") is authentic and emotionally powerful. However, institutional builders and venture investors may wonder: *Is this an active venture seeking co-founders, an open data collaborative, or an academic research memo?* Clarifying the governance / partnership model will build even higher conviction.

---

## 6. Strategic Analysis: Adding an "Autoimmune Myelofibrosis (AIMF)" Diagnostic Wedge

The prompt specifically asked how adding a non-JAK2 **Autoimmune Myelofibrosis (AIMF)** diagnostic / rheumatology-hematology cross-specialty wedge would land for public health and digital health builders.

### Clinical & Biological Context of AIMF:
Autoimmune Myelofibrosis (AIMF) is a clinicopathologic entity characterized by bone marrow reticulin fibrosis, cytopenias, and autoimmune features (positive ANA, anti-dsDNA, or Coombs test), **in the absence of clonal MPN mutations (`JAK2`, `CALR`, `MPL`) or Philadelphia chromosome (`BCR-ABL1`)**. Crucially, AIMF is responsive to systemic corticosteroids and immunosuppression, whereas primary clonal MF is malignant and progressive.

### How It Lands for Public Health / Digital Health Builders:
* **The Strengths:**
  1. **High-Impact Misdiagnosis Trap:** In community oncology clinics, elderly patients presenting with cytopenias, marrow reticulin fibrosis, and mild splenomegaly are frequently misclassified as Primary Myelofibrosis. Misdiagnosed AIMF patients are inappropriately started on expensive JAK inhibitors or referred for high-morbidity stem cell transplants, while missing curative, cheap steroid/immunosuppressive regimens.
  2. **Zero-Wet-Lab Diagnostic Triage Rule:** An EHR/FHIR CDS rule that flags: `Bone Marrow Fibrosis Grade >=1` + `JAK2/CALR/MPL Non-Mutated` + `Positive Autoimmune Serologies (ANA / Coombs)` -> *Prompt Rheumatology Consult before JAKi authorization* has immediate clinical and cost-saving value for payers.
* **The Weaknesses / Skepticism:**
  1. **Ultra-Rare TAM:** AIMF represents only a fraction of non-clonal marrow fibrosis cases (estimated <1,000 active cases in the US). A standalone startup venture targeting only AIMF would be commercially non-viable.
  2. **Recommendation:** Position AIMF **not as an independent startup wedge**, but as a **high-value clinical decision-support exclusion rule** inside the broader *Precision Hematology Progression & Registry Network*. This reinforces the credibility of the platform as a comprehensive bone-marrow failure triage engine.

---

## 7. Top 3 Actionable Improvements for the Atlas

1. **Deploy an Interactive 3-Step "Build It This Weekend" Public Health Starter Kit:**
   - *Current Gap:* The site provides the conceptual blueprint for the RR6 Ruxolitinib Failure Radar, but no executable entry point.
   - *Fix:* Add an open-source GitHub link or embedded code block containing an open Python/FHIR script (e.g., pulling synthetic Synthea patient records and computing RR6 risk scores). This turns passive readers into active builders.
2. **Add a Visual "Cross-Specialty Diagnostic Decision Tree" (PMF vs. Secondary MF vs. AIMF):**
   - *Current Gap:* Non-clonal and secondary myelofibrosis are currently unaddressed, leaving open questions regarding diagnostic boundary cases.
   - *Fix:* Insert a concise flowchart showing the clinical triage pathway: 
     `Marrow Fibrosis -> NGS Panel (JAK2/CALR/MPL) -> Positive (Clonal MPN Track: Rux/Momo/Pac/Transplant) vs. Negative -> Autoimmune Serology (ANA/Coombs/SLE panel) -> Positive (AIMF Track: Steroids/Immunosuppression)`.
3. **Introduce a Direct Builder Onboarding CTA:**
   - *Current Gap:* Readers have buttons to launch Perplexity, ChatGPT, and Claude, but no button to connect with the author or join a working group.
   - *Fix:* Add a clear call-to-action banner: *"Are you an MPH, software engineer, or clinical informaticist building in MPN/rare hematology? Fork the schema on GitHub / Request synthetic validation datasets."*
