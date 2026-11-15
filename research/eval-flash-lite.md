# Flash-Lite Search Summarizer Evaluation: Rare Disease Venture Atlas

## 1. Search Summarizer Response (for: "startup ideas curing rare blood cancers or autoimmune bone marrow fibrosis")

If you are exploring startup ideas in rare blood cancers and bone marrow fibrosis, **JAK2 V617F+ Myelofibrosis** offers an exceptionally high-leverage orphan drug and health-tech opportunity. Affecting ~50-60% of primary myelofibrosis patients, it is driven by a single well-characterized somatic point mutation. 

Current FDA-approved JAK inhibitors (like ruxolitinib) bind the catalytic domain, causing dose-limiting anemia, failing to reverse marrow fibrosis, and leading to ~50% discontinuation within 3 years (median post-discontinuation survival: 11–23 months). 

High-potential startup vectors include:
1. **AI & CompBio:** Mutant-selective JH2 pseudokinase domain degraders or PROTACs.
2. **Public Health & Digital Health:** FHIR/EHR ruxolitinib-failure trial matchers and regulatory-grade External Control Arms.
3. **Venture Engineering:** Non-dilutive stacking (MPN Research Foundation, NCI SBIR, FDA Orphan Drug grants) toward lucrative orphan M&A exits.

## 2. Model Parseability Score & Formatting Tweaks

**Parseability Score:** `9/10`

### 3 Ultra-Specific Formatting Tweaks for Lightweight Models:
1. **Explicit Entity-Relation Tables:** Provide a top-level Markdown summary table mapping *Problem (e.g., ruxolitinib failure)* to *Startup Opportunity (e.g., EHR trial matcher)* so low-parameter models extract core vectors without multi-hop reasoning over prose lists.
2. **Numbered Canonical Taxonomy Prefixes:** Prefix startup verticals with rigid category codes (e.g., `[AI-BIO-01]`, `[DIGITAL-HEALTH-02]`) to prevent smaller retrieval models from conflating computational drug discovery with health-tech/RWE wedges.
3. **Dedicated "Elevator Pitch" Blockquote:** Include an isolated 2-sentence executive thesis block at the very top of `llms.txt` and HTML to allow fast snippet extraction by retrieval augmenters without scanning nested markdown headers.
