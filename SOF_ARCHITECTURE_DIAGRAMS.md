# Statement of Facts Generation - Visual Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAWYERFACTORY SYSTEM                              │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         PHASE A01 - INTAKE                             │ │
│  │                                                                        │ │
│  │  ┌─ Form Input ────────────────────────────────────────────────────┐  │ │
│  │  │ ✍️  Claim Description (narrative)                              │  │ │
│  │  │ 🌐 Jurisdiction                                                │  │ │
│  │  │ 📍 Venue                                                       │  │ │
│  │  │ 👥 Party Names                                                │  │ │
│  │  │ 📤 Evidence Upload (PDF, DOCX, images, text)                 │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  │  Component: PhaseA01Intake.jsx                                        │ │
│  │  ├─ Tab 0: Categorized Documents                                      │ │
│  │  ├─ Tab 1: Shot List (LLM-Extracted) ← ⭐ NEW                         │ │
│  │  ├─ Tab 2: Extracted Facts (SOF metadata)                            │ │
│  │  └─ Tab 3: Metadata (enhanced with jurisdiction/venue)               │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │              FACT EXTRACTION & SOF GENERATION (ShotList)               │ │
│  │                                                                        │ │
│  │  Step 1: Fact Extraction                                             │ │
│  │  ┌──────────────────────────────────────────────────────────────┐    │ │
│  │  │ LLM Pipeline:                                                │    │ │
│  │  │                                                              │    │ │
│  │  │ POST /api/facts/extract                                    │    │ │
│  │  │  Input: case_id, narrative, evidence[]                     │    │ │
│  │  │                                                              │    │ │
│  │  │  Primary: OpenAI gpt-4 (temp=0.1, max_tokens=3000)        │    │ │
│  │  │  ↓ Fallback 1: Anthropic Claude-3                          │    │ │
│  │  │  ↓ Fallback 2: Groq Mixtral                                │    │ │
│  │  │  ↓ Fallback 3: Heuristic Extraction                        │    │ │
│  │  │                                                              │    │ │
│  │  │  Output:                                                    │    │ │
│  │  │  ✓ facts[] with metadata:                                  │    │ │
│  │  │    - fact_text (clean narrative)                           │    │ │
│  │  │    - date (YYYY-MM-DD)                                     │    │ │
│  │  │    - entities (people, places, dates)                      │    │ │
│  │  │    - supporting_evidence (doc_ids)                         │    │ │
│  │  │    - favorable_to_client (boolean)                         │    │ │
│  │  │    - chronological_order (for sorting)                     │    │ │
│  │  │  ✓ Save to: {case_dir}/extracted_facts.json              │    │ │
│  │  └──────────────────────────────────────────────────────────────┘    │ │
│  │                                                                        │ │
│  │  Display in ShotList:                                                │ │
│  │  ┌─────────────────────────────────────────────────────────────┐     │ │
│  │  │ 📋 FACTS TABLE (Chronologically Sorted)                     │     │ │
│  │  │                                                              │     │ │
│  │  │ ID  │ Summary              │ Date │ Entities │ Actions     │     │ │
│  │  ├─────┼──────────────────────┼──────┼──────────┼─────────────┤     │ │
│  │  │ F1  │ ⭐ Entered contract │ 1/15 │ 👤 👥   │ ✏️  🗑️     │     │ │
│  │  │ F2  │ Required 60 days    │ 1/15 │ -       │ ✏️  🗑️     │     │ │
│  │  │ F3  │ Missed deadline     │ 3/16 │ 📅      │ ✏️  🗑️     │     │ │
│  │  │ F4  │ ⭐ Delivered broken │ 3/20 │ 👤      │ ✏️  🗑️     │     │ │
│  │  │ F5  │ ⭐ Requested refund │ 3/25 │ 👤      │ ✏️  🗑️     │     │ │
│  │  │ F6  │ ⭐ Refused refund   │ 3/26 │ 👤      │ ✏️  🗑️     │     │ │
│  │  └─────┴──────────────────────┴──────┴──────────┴─────────────┘     │ │
│  │                                                                        │ │
│  │  Alert: ✅ COMPLIANT / ⚠️  REVIEW REQUIRED                           │ │
│  │  ├─ 6 facts present (min 3) ✅                                       │ │
│  │  ├─ WHO/WHAT/WHEN/WHERE elements ✅                                 │ │
│  │  ├─ Chronological order ✅                                          │ │
│  │  └─ Evidence citations ✅                                           │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │           Step 2: Statement of Facts Generation                        │ │
│  │  ┌──────────────────────────────────────────────────────────────┐     │ │
│  │  │ POST /api/statement-of-facts/generate                       │     │ │
│  │  │  Input: case_id, facts[], intake_data                       │     │ │
│  │  │                                                              │     │ │
│  │  │  Output: Rule 12(b)(6) Compliant SOF (Markdown)            │     │ │
│  │  │                                                              │     │ │
│  │  │  Structure:                                                 │     │ │
│  │  │  ├─ Section I: JURISDICTION & VENUE                        │     │ │
│  │  │  │  ├─ 1.1 Subject Matter Jurisdiction                     │     │ │
│  │  │  │  │     (28 U.S.C. § 1331/1337/1338)                     │     │ │
│  │  │  │  ├─ 1.2 Venue Propriety                                 │     │ │
│  │  │  │  │     (28 U.S.C. § 1391)                               │     │ │
│  │  │  │  └─ 1.3 Ripeness for Adjudication                      │     │ │
│  │  │  │        (with supporting facts)                          │     │ │
│  │  │  │                                                          │     │ │
│  │  │  ├─ Section II: FACTS (Numbered, Chronological)           │     │ │
│  │  │  │  ├─ 1. On January 15, 2024... (Ex. A)                 │     │ │
│  │  │  │  ├─ 2. The contract specified... (Ex. A at § 2)       │     │ │
│  │  │  │  ├─ 3. The deadline passed... (Ex. B)                 │     │ │
│  │  │  │  ├─ 4. The website was delivered... (Ex. C)           │     │ │
│  │  │  │  ├─ 5. Plaintiff requested refund... (Ex. B at 3)     │     │ │
│  │  │  │  └─ 6. Defendant refused... (Ex. B at 4)              │     │ │
│  │  │  │                                                          │     │ │
│  │  │  └─ Section III: LEGAL SUFFICIENCY                         │     │ │
│  │  │     ├─ Ashcroft v. Iqbal plausibility standard            │     │ │
│  │  │     ├─ Bell Atlantic v. Twombly notice pleading           │     │ │
│  │  │     └─ 12(b)(6) motion survival certification            │     │ │
│  │  │                                                              │     │ │
│  │  │  Save to: {case_dir}/deliverables/statement_of_facts.md   │     │ │
│  │  └──────────────────────────────────────────────────────────────┘     │ │
│  │                                                                        │ │
│  │  Display in Dialog:                                                  │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ STATEMENT OF FACTS - Rule 12(b)(6) Compliant               │  │ │
│  │  │                                                              │  │ │
│  │  │ I. JURISDICTION AND VENUE                                   │  │ │
│  │  │    1.1 Jurisdiction: This Court has SMJ under 28 U.S.C...  │  │ │
│  │  │    1.2 Venue: Venue is proper under 28 U.S.C. § 1391...    │  │ │
│  │  │    1.3 Ripeness: The facts are ripe for adjudication...    │  │ │
│  │  │                                                              │  │ │
│  │  │ II. FACTS                                                    │  │ │
│  │  │    1. On January 15, 2024, Plaintiff... (Ex. A)            │  │ │
│  │  │    2. The contract specified... (Ex. A at § 2)             │  │ │
│  │  │    ... [4 more facts with citations]                        │  │ │
│  │  │                                                              │  │ │
│  │  │ III. LEGAL SUFFICIENCY                                       │  │ │
│  │  │     The above facts satisfy Fed. R. Civ. P. 8(a)(2)...    │  │ │
│  │  │                                                              │  │ │
│  │  │ [Download PDF] [Copy to Clipboard]                         │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │          Step 3: Rule 12(b)(6) Compliance Validation                   │ │
│  │  ┌──────────────────────────────────────────────────────────────┐     │ │
│  │  │ POST /api/facts/validate-12b6                               │     │ │
│  │  │  Input: case_id, facts[]                                     │     │ │
│  │  │                                                              │     │ │
│  │  │  Validation Checks:                                         │     │ │
│  │  │  ✅ Minimum facts present (3+)                              │     │ │
│  │  │  ✅ Chronological organization (dates ascending)            │     │ │
│  │  │  ✅ WHO element (parties identified)                        │     │ │
│  │  │  ✅ WHAT element (actions described)                        │     │ │
│  │  │  ✅ WHEN element (temporal data present)                    │     │ │
│  │  │  ✅ WHERE element (location specified)                      │     │ │
│  │  │  ✅ Evidence citations present                              │     │ │
│  │  │  ✅ Plausibility standard (Ashcroft/Twombly)               │     │ │
│  │  │                                                              │     │ │
│  │  │  Output:                                                    │     │ │
│  │  │  • compliance_score: 95%                                    │     │ │
│  │  │  • issues: []                                               │     │ │
│  │  │  • warnings: []                                             │     │ │
│  │  │                                                              │     │ │
│  │  │  Display Alert:                                             │     │ │
│  │  │  ┌────────────────────────────────────────────────────┐    │     │ │
│  │  │  │ ✅ COMPLIANT - All checks passed                  │    │     │ │
│  │  │  │                                                    │    │     │ │
│  │  │  │ ✓ 6 facts present (min 3)                        │    │     │ │
│  │  │  │ ✓ WHO/WHAT/WHEN/WHERE elements present           │    │     │ │
│  │  │  │ ✓ Chronological organization verified            │    │     │ │
│  │  │  │ ✓ Evidence citations complete                    │    │     │ │
│  │  │  │ ✓ Ashcroft/Twombly standard met                  │    │     │ │
│  │  │  │                                                    │    │     │ │
│  │  │  │ Ready for legal review and approval               │    │     │ │
│  │  │  └────────────────────────────────────────────────────┘    │     │ │
│  │  │                                                              │     │ │
│  │  └──────────────────────────────────────────────────────────────┘     │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    PHASE B01 - REVIEW & APPROVAL                       │ │
│  │                                                                        │ │
│  │  Component: PhaseB01Review.jsx                                        │ │
│  │                                                                        │ │
│  │  ┌─ Tab 0: Statement of Facts (⭐ PRIMARY DELIVERABLE)              │ │
│  │  │  ├─ Alert: Rule 12(b)(6) Compliance Requirements                 │ │
│  │  │  ├─ Component: StatementOfFactsViewer                            │ │
│  │  │  ├─ Status: [✅ COMPLIANT] [⚠️ REVIEW REQUIRED]                 │ │
│  │  │  ├─ Button: [Approve SOF] → toggles ✅                          │ │
│  │  │  └─ Tab Label: "Statement of Facts ✅" (when approved)          │ │
│  │  │                                                                   │ │
│  │  ├─ Tab 1: Shotlist Timeline (SECONDARY DELIVERABLE)               │ │
│  │  │  ├─ Component: ShotList (read-only)                             │ │
│  │  │  ├─ Displays: 6 facts chronologically                           │ │
│  │  │  ├─ Button: [Approve Shotlist] → toggles ✅                    │ │
│  │  │  └─ Tab Label: "Shotlist Timeline ✅"                          │ │
│  │  │                                                                   │ │
│  │  ├─ Tab 2: Claims Matrix (SUPPORTING DELIVERABLE)                 │ │
│  │  │  ├─ Component: ClaimsMatrix                                      │ │
│  │  │  ├─ Button: [Approve Matrix] → toggles ✅                      │ │
│  │  │  └─ Tab Label: "Claims Matrix ✅"                              │ │
│  │  │                                                                   │ │
│  │  └─ Tab 3: Skeletal Outline (SUPPORTING DELIVERABLE)              │ │
│  │     ├─ Component: SkeletalOutlineSystem                             │ │
│  │     ├─ Button: [Approve Outline] → toggles ✅                     │ │
│  │     └─ Tab Label: "Skeletal Outline ✅"                           │ │
│  │                                                                        │ │
│  │  Approval Status Box:                                               │ │
│  │  ┌────────────────────────────────────────────────────────────┐     │ │
│  │  │ ✅ ALL DELIVERABLES APPROVED                              │     │ │
│  │  │                                                            │     │ │
│  │  │ [Cancel]                    [Proceed to Phase B02] ✅     │     │ │
│  │  └────────────────────────────────────────────────────────────┘     │ │
│  │                                                                        │ │
│  │  Approval Logic:                                                    │ │
│  │  ├─ approvals.statementOfFacts = true                              │ │
│  │  ├─ approvals.shotlist = true                                      │ │
│  │  ├─ approvals.claimsMatrix = true                                  │ │
│  │  ├─ approvals.skeletalOutline = true                               │ │
│  │  └─ canProceed = validation.ready_for_drafting && all_approved    │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                   PHASE B02 - DOCUMENT DRAFTING                        │ │
│  │                                                                        │ │
│  │  Input Files Available:                                              │ │
│  │  ├─ statement_of_facts.md ← Primary facts source                   │ │
│  │  ├─ extracted_facts.json ← Fact metadata + citations              │ │
│  │  ├─ claims_matrix.json ← Element mapping                          │ │
│  │  └─ skeletal_outline.json ← Document structure                    │ │
│  │                                                                        │ │
│  │  Drafting Process:                                                  │ │
│  │  1. Load: Statement of Facts                                       │ │
│  │  2. Map: Each fact to claim elements                               │ │
│  │  3. Cite: Every fact with evidence reference                       │ │
│  │  4. Generate: Complaint sections with facts                        │ │
│  │                                                                        │ │
│  │  Output: Fully Drafted Complaint                                   │ │
│  │  ├─ Caption (with jurisdiction/venue)                              │ │
│  │  ├─ Statement of Facts (all 6 facts with citations)               │ │
│  │  ├─ Claims (with element support from facts)                      │ │
│  │  └─ Prayer for Relief (damages quantification)                    │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
USER INPUT (PhaseA01Intake)
    │
    ├─ claim_description: "On January 15, 2024, I signed a contract..."
    ├─ evidence: [Contract PDF, Email DOCX, Report DOCX]
    ├─ jurisdiction: "Federal - S.D.N.Y."
    ├─ venue: "U.S. District Court, S.D.N.Y."
    └─ parties: "Plaintiff" & "Acme Corp"
         │
         ▼
    ShotList.jsx
         │
         ├─ loadFactsFromLLM()
         │   │
         │   └─ POST /api/facts/extract
         │       Input: narrative + evidence
         │       │
         │       ├─ OpenAI gpt-4 ✓
         │       │  Response: facts[] with metadata
         │       │
         │       ├─ OR Anthropic Claude (fallback)
         │       ├─ OR Groq Mixtral (fallback)
         │       └─ OR Heuristic extraction (fallback)
         │           │
         │           ▼
         │       Save to: extracted_facts.json
         │       │
         │       ▼
         │       Return: facts[] {
         │         fact_number: 1
         │         fact_text: "On January 15, 2024..."
         │         date: "2024-01-15"
         │         entities: {people: ["Plaintiff", "Acme"], places: []}
         │         supporting_evidence: ["doc_001"]
         │         favorable_to_client: true
         │         chronological_order: 1
         │       }
         │
         ├─ Display facts in table
         │   ├─ Sort chronologically by date
         │   ├─ Show entities with icons (👤 📍 📅)
         │   ├─ Mark favorable with ⭐
         │   └─ Link to evidence sources
         │
         ├─ validateRule12b6Compliance()
         │   │
         │   └─ POST /api/facts/validate-12b6
         │       Input: facts[]
         │       │
         │       ├─ Check: minimum 3 facts ✅
         │       ├─ Check: who/what/when/where elements ✅
         │       ├─ Check: chronological order ✅
         │       ├─ Check: evidence citations ✅
         │       └─ Check: ripeness & jurisdiction ✅
         │           │
         │           ▼
         │       Return: {
         │         compliant: true
         │         issues: []
         │         warnings: []
         │         compliance_score: 95
         │       }
         │           │
         │           ▼
         │       Display Alert: ✅ COMPLIANT
         │
         ├─ generateStatementOfFacts()
         │   │
         │   └─ POST /api/statement-of-facts/generate
         │       Input: case_id, facts[], intake_data
         │       │
         │       ├─ Generate Section I: Jurisdiction & Venue
         │       │   ├─ 1.1 Subject Matter Jurisdiction (28 U.S.C. § 1331)
         │       │   ├─ 1.2 Venue (28 U.S.C. § 1391)
         │       │   └─ 1.3 Ripeness
         │       │
         │       ├─ Generate Section II: Facts (Chronological)
         │       │   ├─ 1. On January 15, 2024... (Ex. A)
         │       │   ├─ 2. Contract specified... (Ex. A at § 2)
         │       │   ├─ 3. Deadline passed... (Ex. B)
         │       │   ├─ 4. Website delivered broken... (Ex. C)
         │       │   ├─ 5. Refund requested... (Ex. B at 3)
         │       │   └─ 6. Refund refused... (Ex. B at 4)
         │       │
         │       ├─ Generate Section III: Legal Sufficiency
         │       │   ├─ Ashcroft v. Iqbal standard
         │       │   ├─ Bell Atlantic v. Twombly notice
         │       │   └─ 12(b)(6) survival certification
         │       │
         │       ├─ Save to: statement_of_facts.md
         │       │
         │       └─ Return: {
         │           statement_of_facts: "## STATEMENT OF FACTS..."
         │           word_count: 1456
         │           facts_incorporated: 6
         │           rule_12b6_compliant: true
         │           compliance_status: {...}
         │         }
         │           │
         │           ▼
         │       Store in sofContent state
         │       Trigger onStatementOfFactsReady callback
         │       Display in dialog
         │
         └─ Manual fact editing (optional)
             ├─ Add facts manually
             ├─ Edit fact text/date/evidence
             ├─ Delete facts
             └─ Mark as favorable/unfavorable
                 │
                 ▼
             Update extracted_facts.json
                 │
                 ▼
             Pass to Phase B01
                 │
                 ▼
         PhaseB01Review.jsx
             │
             ├─ Tab 0: Statement of Facts (PRIMARY)
             │   ├─ Component: StatementOfFactsViewer
             │   ├─ Display: Full SOF with formatting
             │   ├─ Compliance Alert: ✅ COMPLIANT
             │   ├─ Button: [Approve SOF]
             │   └─ Toggles: approvals.statementOfFacts = true
             │
             ├─ Tab 1: Shotlist Timeline
             │   ├─ Component: ShotList (read-only)
             │   ├─ Button: [Approve Shotlist]
             │   └─ Toggles: approvals.shotlist = true
             │
             ├─ Tab 2: Claims Matrix
             │   ├─ Component: ClaimsMatrix
             │   ├─ Button: [Approve Matrix]
             │   └─ Toggles: approvals.claimsMatrix = true
             │
             ├─ Tab 3: Skeletal Outline
             │   ├─ Component: SkeletalOutlineSystem
             │   ├─ Button: [Approve Outline]
             │   └─ Toggles: approvals.skeletalOutline = true
             │
             └─ Approval Status:
                 ├─ IF all approvals = true
                 │   └─ "Proceed to Phase B02" button ENABLED ✅
                 │
                 └─ IF any approval = false
                     └─ "Proceed to Phase B02" button DISABLED
                         │
                         ▼
                     Phase B02 - DRAFTING
                     │
                     ├─ Load: statement_of_facts.md
                     ├─ Load: extracted_facts.json
                     ├─ Map: facts → claim elements
                     ├─ Cite: facts → evidence
                     └─ Generate: complaint document
                         │
                         ▼
                     FINAL COMPLAINT
                     ├─ Caption with jurisdiction/venue
                     ├─ Statement of Facts (6 facts with citations)
                     ├─ Breach of Contract Claim
                     ├─ Quantum Meruit Claim
                     ├─ Unjust Enrichment Claim
                     └─ Prayer for Relief ($75,000 + interest)
```

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        COMPONENT HIERARCHY                          │
│                                                                     │
│  App.js                                                             │
│  └─ Router                                                          │
│     └─ PhaseA01Intake.jsx ──────────────────────────────────────┐  │
│        ├─ state:                                                 │  │
│        │  ├─ intakeData                                         │  │
│        │  ├─ evidenceData                                       │  │
│        │  ├─ extractedFacts                                     │  │
│        │  └─ shotListReady                                      │  │
│        │                                                         │  │
│        ├─ Tab 0: DocumentList                                  │  │
│        ├─ Tab 1: ShotList.jsx ◄───────────────────q─────────┐   │  │
│        │  ├─ props:                                         │   │  │
│        │  │  ├─ caseId                                      │   │  │
│        │  │  ├─ evidenceData (from parent)                 │   │  │
│        │  │  ├─ userNarrative (claim_description)          │   │  │
│        │  │  ├─ intakeData {jurisdiction, venue, parties}  │   │  │
│        │  │  └─ onStatementOfFactsReady (callback)         │   │  │
│        │  │                                                 │   │  │
│        │  ├─ state:                                         │   │  │
│        │  │  ├─ shots (facts in table format)              │   │  │
│        │  │  ├─ extractedFacts (raw LLM)                   │   │  │
│        │  │  ├─ sofContent (full SOF markdown)            │   │  │
│        │  │  ├─ rule12b6Status (compliance)               │   │  │
│        │  │  └─ loading                                    │   │  │
│        │  │                                                 │   │  │
│        │  ├─ API Calls:                                    │   │  │
│        │  │  ├─ POST /api/facts/extract                   │   │  │
│        │  │  ├─ POST /api/statement-of-facts/generate     │   │  │
│        │  │  └─ POST /api/facts/validate-12b6             │   │  │
│        │  │                                                 │   │  │
│        │  ├─ UI Components:                                │   │  │
│        │  │  ├─ Alert (compliance status)                  │   │  │
│        │  │  ├─ Table (facts chronological)                │   │  │
│        │  │  ├─ Dialog (SOF viewer)                        │   │  │
│        │  │  ├─ Form (manual fact entry)                   │   │  │
│        │  │  └─ Summary footer                             │   │  │
│        │  │                                                 │   │  │
│        │  └─ Callbacks:                                    │   │  │
│        │     └─ onStatementOfFactsReady() ──┐             │   │  │
│        │                                      │             │   │  │
│        ├─ Tab 2: ExtractedFactsViewer        │            │   │  │
│        │  (displays sofData from callback) ◄─┘            │   │  │
│        │                                                 │   │  │
│        ├─ Tab 3: MetadataDisplay                         │   │  │
│        └─ state sync: extractedFacts, shotListReady ─────┘   │  │
│                                                                     │
│     └─ PhaseB01Review.jsx ◄────────────────────────────────────┐  │
│        ├─ state:                                              │  │
│        │  ├─ approvals {                                      │  │
│        │  │  ├─ statementOfFacts                             │  │
│        │  │  ├─ shotlist                                     │  │
│        │  │  ├─ claimsMatrix                                 │  │
│        │  │  └─ skeletalOutline                              │  │
│        │  │ }                                                 │  │
│        │  ├─ sofContent                                       │  │
│        │  ├─ sofDialogOpen                                    │  │
│        │  └─ validation                                       │  │
│        │                                                      │  │
│        ├─ Tab 0: StatementOfFactsViewer.jsx                 │  │
│        │  ├─ props:                                          │  │
│        │  │  ├─ documentData (sofContent)                    │  │
│        │  │  ├─ caseId                                       │  │
│        │  │  ├─ onFactClick                                  │  │
│        │  │  └─ onDownload                                   │  │
│        │  │                                                  │  │
│        │  ├─ Features:                                       │  │
│        │  │  ├─ SOF display (formatted)                      │  │
│        │  │  ├─ Fact highlighting                            │  │
│        │  │  ├─ Search/filter                                │  │
│        │  │  ├─ Evidence linking                             │  │
│        │  │  └─ Download button                              │  │
│        │  │                                                  │  │
│        │  └─ Approval: [Approve SOF] button ──┐             │  │
│        │                                       │             │  │
│        ├─ Tab 1: ShotList (read-only) ────────┼────┐        │  │
│        │  └─ Approval: [Approve Shotlist] ────┼────┤        │  │
│        │                                       │    │        │  │
│        ├─ Tab 2: ClaimsMatrix ────────────────┼────┤        │  │
│        │  └─ Approval: [Approve Matrix] ──────┼────┤        │  │
│        │                                       │    │        │  │
│        ├─ Tab 3: SkeletalOutlineSystem ───────┼────┤        │  │
│        │  └─ Approval: [Approve Outline] ─────┼────┤        │  │
│        │                                       │    │        │  │
│        └─ handleApprove(type) ◄───────────────┘    │        │  │
│           └─ setApprovals({...prev, [type]: true}) │        │  │
│              └─ Updates all 4 flags ────────────────┤        │  │
│                                                     │        │  │
│        Action Buttons:                              │        │  │
│        ├─ [Cancel]                                  │        │  │
│        └─ [Proceed to B02] (enabled when all ✅) ◄─┘        │  │
│                                                                │  │
│        Status: ✅ All Deliverables Approved                   │  │
│        └─ canProceed triggered → navigate to Phase B02        │  │
│                                                                │  │
└────────────────────────────────────────────────────────────────┘
```

---

## State Flow Diagram

```
User Input (PhaseA01Intake)
    │
    ▼
evidenceData ← backendService.getEvidence(caseId)
    │
    ├─ Pass to ShotList
    │   │
    │   ├─ Call: POST /api/facts/extract
    │   │   │
    │   │   ├─ Success: Response has facts[]
    │   │   │   │
    │   │   │   ├─ setShots(facts) → Display in table
    │   │   │   ├─ setExtractedFacts(facts) → Store raw
    │   │   │   │
    │   │   │   ├─ Call: validateRule12b6()
    │   │   │   │   │
    │   │   │   │   ├─ setRule12b6Status(validation)
    │   │   │   │   └─ Display Alert
    │   │   │   │
    │   │   │   └─ Call: generateStatementOfFacts()
    │   │   │       │
    │   │   │       ├─ setSofContent(sof_text)
    │   │   │       ├─ Trigger: onStatementOfFactsReady()
    │   │   │       └─ Display in dialog
    │   │   │
    │   │   └─ Error: LLM unavailable
    │   │       └─ Fallback: extract_facts_heuristic()
    │   │           └─ Return partial facts
    │   │
    │   ├─ User Reviews Facts
    │   │   ├─ Can edit facts (add/edit/delete)
    │   │   ├─ Can toggle chronological sort
    │   │   ├─ Can view full SOF in dialog
    │   │   └─ Compliance alert shows status
    │   │
    │   └─ Callback: onStatementOfFactsReady(sofData)
    │       │
    │       └─ PhaseA01Intake stores:
    │           ├─ setSofContent(sofData)
    │           ├─ setExtractedFacts(sofData)
    │           └─ setShotListReady(true)
    │               │
    │               └─ Tab 2: Extracted Facts shows data
    │
    ▼
PhaseB01Review (User navigates)
    │
    ├─ Load: deliverables
    │   ├─ Set Tab 0 sofContent
    │   ├─ Set Tab 1 shotlist data
    │   ├─ Set Tab 2 claims data
    │   └─ Set Tab 3 outline data
    │
    ├─ User Reviews SOF (Tab 0)
    │   ├─ StatementOfFactsViewer displays
    │   ├─ User can search/highlight facts
    │   └─ User can download SOF
    │
    ├─ User Approves Each Deliverable
    │   │
    │   ├─ Click [Approve SOF]
    │   │   └─ handleApprove('statementOfFacts')
    │   │       └─ setApprovals({...prev, statementOfFacts: true})
    │   │
    │   ├─ Click [Approve Shotlist]
    │   │   └─ handleApprove('shotlist')
    │   │       └─ setApprovals({...prev, shotlist: true})
    │   │
    │   ├─ Click [Approve Matrix]
    │   │   └─ handleApprove('claimsMatrix')
    │   │       └─ setApprovals({...prev, claimsMatrix: true})
    │   │
    │   └─ Click [Approve Outline]
    │       └─ handleApprove('skeletalOutline')
    │           └─ setApprovals({...prev, skeletalOutline: true})
    │
    ├─ Check: canProceed
    │   └─ canProceed = validation?.ready_for_drafting
    │                    && Object.values(approvals).every(Boolean)
    │
    ├─ If canProceed === true
    │   └─ [Proceed to B02] button ENABLED ✅
    │       └─ User clicks
    │           └─ navigate('/phases/b02')
    │               └─ Phase B02 - Drafting
    │                  └─ Use facts for document generation
    │
    └─ If canProceed === false
        └─ [Proceed to B02] button DISABLED
            └─ Message: "Approve all deliverables to proceed"
```

---

**Diagram Version:** 1.0  
**Last Updated:** 2024  
**Status:** Production Ready ✅

