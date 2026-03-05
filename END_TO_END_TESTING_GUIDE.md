# End-to-End Testing & Lawsuit Generation Guide

**Complete walkthrough to test the system and output a legal document (complaint/lawsuit)**

---

## 🎯 Quick Overview: The 8-Phase Workflow

LawyerFactory transforms client intake into a court-ready complaint through 8 phases:

```
PhaseA01: Intake      → User submits facts, evidence, jurisdiction
         ↓
PhaseA02: Research    → AI researches relevant case law
         ↓
PhaseA03: Outline     → Creates skeletal outline & claims matrix
         ↓
PhaseB01: Review      → Attorney reviews facts & evidence
         ↓
PhaseB02: Drafting    → Agents write complaint with claims
         ↓
PhaseC01: Editing     → Final formatting & citations
         ↓
PhaseC02: Orchestration → Complete integration & final output
         ↓
POST-PRODUCTION       → Generate PDF/DOCX files
```

---

## ⚡ Fastest Path: Run End-to-End Tests (5 minutes)

### Step 1: Start the System

```bash
cd /Users/jreback/Projects/LawyerFactory

# Option A: Full system (frontend + backend)
./launch.sh

# Option B: Backend only (for testing)
cd apps/api && python server.py

# Option C: Manual Python setup
python -m pytest --collect-only  # Verify test infrastructure
```

### Step 2: Run the Complete E2E Test Suite

```bash
# From project root
python -m pytest tests/e2e/test_sof_e2e.py -v

# Expected output:
# ✅ Test 1: Facts extracted from narrative and evidence
# ✅ Test 2: Facts organized chronologically
# ✅ Test 3: WHO/WHAT/WHEN/WHERE extraction
# ✅ Test 4: Evidence citation mapping
# ✅ Test 5: Favorable/neutral classification
# ✅ Test 6: Rule 12(b)(6) compliance elements
# ✅ Test 7: Statement of Facts structure
# ✅ Test 8: PhaseA01 intake data flows to SOF
# ✅ Test 9: ShotList facts delivered to PhaseB01
# ✅ Test 10: Approval workflow logic
# ✅ Test 11: Complete end-to-end workflow
# ✅ FULL PIPELINE INTEGRATION TEST
```

---

## 🚀 Full System Test: Generate Real Lawsuit Output (15 minutes)

### Step 1: Launch the Complete System

```bash
# Terminal 1: Backend API
cd /Users/jreback/Projects/LawyerFactory/apps/api
python server.py
# Expected: "Running on http://localhost:5000"

# Terminal 2: Frontend (React UI)
cd /Users/jreback/Projects/LawyerFactory/apps/ui/react-app
npm run dev
# Expected: "Local: http://localhost:5173"

# Terminal 3: Health check
cd /Users/jreback/Projects/LawyerFactory
./scripts/heath-check.sh
```

### Step 2: Access the UI

Open browser: **http://localhost:5173** (or http://localhost:3000 for production)

### Step 3: Complete the Intake Form (PhaseA01)

The UI will prompt you through:

1. **Client Information**

   - Client name: "John Doe"
   - Phone: "555-0123"
   - Email: "john@example.com"

2. **Case Details**

   - Case type: "Contract Breach"
   - Jurisdiction: "Federal - U.S. District Court"
   - Venue: "Southern District of New York"

3. **Legal Narrative**

   ```
   On January 15, 2024, I entered into a service agreement with Acme Corporation
   for website development. They promised delivery within 60 days for $50,000.
   The website was never delivered and now (March 2024) they refuse to refund.
   I've lost business and spent time pursuing this.
   ```

4. **Upload Evidence** (Optional)
   - Service agreement (contract)
   - Emails showing non-delivery
   - Payment receipts
   - Damage calculations

### Step 4: Navigate to ShotList (PhaseA01 Tab 1)

The system automatically:

- ✅ Extracts facts from your narrative
- ✅ Organizes facts chronologically
- ✅ Identifies key entities (people, places, dates)
- ✅ Marks facts favorable to client
- ✅ Shows supporting evidence

### Step 5: Generate Statement of Facts

Click "Generate Statement of Facts" button:

- ✅ Creates Rule 12(b)(6) compliant document
- ✅ Shows word count & compliance status
- ✅ Displays formal legal narrative

### Step 6: Proceed to PhaseB01 (Review)

Attorney review interface shows:

- ✅ Statement of Facts
- ✅ Claims Matrix (legal claims to pursue)
- ✅ Skeletal Outline (document structure)
- ✅ Shot List (supporting facts)

**Click "Approve All" to proceed**

### Step 7: PhaseB02 - Document Drafting

The system automatically generates:

- ✅ **Complaint Caption** (case header)
- ✅ **Statement of Facts** (detailed narrative)
- ✅ **Causes of Action** (legal claims):
  - Breach of Contract
  - Quantum Meruit
  - Unjust Enrichment
- ✅ **Prayer for Relief** (damages requested)

### Step 8: PhaseC01 - Editing & Final Output

Final processing includes:

- ✅ Citation validation
- ✅ Legal authority verification
- ✅ Document formatting
- ✅ Compliance checks

### Step 9: PhaseC02 - Generate Final Documents

Output formats available:

- 📄 **PDF** (ready for court filing)
- 📋 **DOCX** (Word format for editing)
- 📝 **MD** (Markdown for review)

**Your complaint is now ready to file!**

---

## 🧪 Advanced: Run Specific Tests

### Test the Statement of Facts Generation

```bash
# Run SOF-specific tests
python -m pytest tests/e2e/test_sof_e2e.py::TestStatementOfFactsE2E::test_fact_extraction_from_narrative_and_evidence -v

# Test compliance validation
python -m pytest tests/e2e/test_sof_e2e.py::TestStatementOfFactsE2E::test_rule_12b6_compliance_elements -v

# Test full integration
python -m pytest tests/e2e/test_sof_e2e.py::TestStatementOfFactsE2E::test_full_pipeline_integration -v
```

### Test Document Generation

```bash
# Test AI Document Generator
python src/lawyerfactory/export/renderers/legacy/ai_document_generator.py

# Test Skeletal Outline
python src/lawyerfactory/outline/generator.py

# Test Claims Matrix
python -m pytest tests/test_phase_connectivity.py -v
```

### Test the Complete Workflow

```bash
# Run all integration tests
python -m pytest tests/integration/ -v

# Run all unit tests
python -m pytest tests/unit/ -v

# Full test suite
python -m pytest -v
```

---

## 🔌 API Testing (Advanced)

### Quick API Test Script

```bash
cat > /tmp/test_api.sh << 'EOF'
#!/bin/bash

# Test Facts Extraction
curl -X POST http://localhost:5000/api/facts/extract \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "test_001",
    "narrative": "On Jan 15, 2024, I hired Acme Corp for web development. They failed to deliver.",
    "evidence": []
  }'

# Test SOF Generation
curl -X POST http://localhost:5000/api/statement-of-facts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "test_001",
    "facts": ["Jan 15: Contract signed", "Mar 20: No delivery", "Demanded refund"],
    "intake_data": {
      "jurisdiction": "Federal",
      "venue": "SDNY",
      "plaintiff": "John Doe",
      "defendant": "Acme Corp"
    }
  }'

# Test Document Generation
curl -X POST http://localhost:5000/api/generate-document \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "complaint",
    "case_data": {
      "plaintiff_name": "John Doe",
      "defendant_name": "Acme Corp",
      "jurisdiction": "Federal",
      "facts": ["Jan 15: Contract", "Mar 20: Non-delivery"]
    }
  }'
EOF

chmod +x /tmp/test_api.sh
/tmp/test_api.sh
```

---

## 📊 Key Components by Phase

### PhaseA01: Intake

- **File**: `src/lawyerfactory/phases/phaseA01_intake/reader.py`
- **UI**: `apps/ui/react-app/src/components/phases/PhaseA01Intake.jsx`
- **Input**: Client narrative, evidence files
- **Output**: Structured intake data

### PhaseA02: Research

- **File**: `src/lawyerfactory/agents/research/research.py`
- **Agent**: Research bot using Tavily integration
- **Output**: Relevant case law, statutes, rules

### PhaseA03: Outline

- **File**: `src/lawyerfactory/outline/generator.py`
- **Components**:
  - Claims matrix: `src/lawyerfactory/claims/matrix.py`
  - Skeletal outline: Detected from facts
  - Shot list: `src/lawyerfactory/evidence/shotlist.py`

### PhaseB01: Review

- **UI**: `apps/ui/react-app/src/components/phases/PhaseB01Review.jsx`
- **Purpose**: Attorney reviews facts, claims, evidence
- **Output**: Approval for drafting

### PhaseB02: Drafting

- **Writer Bot**: `src/lawyerfactory/compose/bots/writer.py`
- **Editor Bot**: `src/lawyerfactory/compose/bots/editor.py`
- **Output**: Draft complaint with all claims

### PhaseC01: Editing

- **File**: `src/lawyerfactory/phases/phaseC01_editing/pdf_generator.py`
- **Tasks**:
  - Validate citations
  - Format document
  - Check compliance
- **Output**: Formatted document

### PhaseC02: Orchestration

- **Maestro**: `src/lawyerfactory/compose/maestro/maestro.py`
- **Purpose**: Orchestrate all agents
- **Output**: Final case package

### POST-PRODUCTION

- **PDF Export**: `src/lawyerfactory/post_production/pdf_generator.py`
- **Output**: Court-ready PDF files

---

## 🎓 Example: Complete Workflow

### Input Case Data:

```json
{
  "case_id": "ACME_001",
  "plaintiff_name": "Jane Smith",
  "defendant_name": "TechCorp Inc.",
  "jurisdiction": "Northern District of California",
  "venue": "San Francisco",
  "narrative": "On March 1, 2024, I purchased a defective laptop. It overheated and failed after 2 weeks. The company ignored my complaints and refused to repair or refund.",
  "evidence": [
    { "type": "receipt", "date": "2024-03-01", "amount": 1500 },
    { "type": "warranty", "coverage": "1 year" },
    { "type": "email", "content": "Customer service refused refund" }
  ]
}
```

### Processing Steps:

1. **PhaseA01**: Extract structured intake data
2. **PhaseA02**: Research product liability cases
3. **PhaseA03**: Detect claims (Breach of Warranty, Products Liability, Fraud in inducement)
4. **PhaseB01**: Attorney reviews claims are valid
5. **PhaseB02**: Generate complaint with:
   - Caption with court info
   - Statement of Facts (narrative)
   - Three causes of action with legal elements
   - Prayer for Relief ($1500 + damages)
6. **PhaseC01**: Format, validate citations
7. **PhaseC02**: Final orchestration
8. **POST**: Export PDF/DOCX

### Output Complaint:

```
IN THE UNITED STATES DISTRICT COURT
FOR THE NORTHERN DISTRICT OF CALIFORNIA

JANE SMITH,
    Plaintiff,
v.
TECHCORP INC.,
    Defendant.
                                        Case No. [TBD]

COMPLAINT FOR DAMAGES

STATEMENT OF FACTS

1. On March 1, 2024, Plaintiff purchased a laptop from Defendant TechCorp Inc.
   for $1,500.00.

2. The laptop was defective and overheated, becoming non-functional after two weeks.

3. Plaintiff requested repair and refund; Defendant refused both requests.

CAUSES OF ACTION

I. BREACH OF IMPLIED WARRANTY OF MERCHANTABILITY
...

II. PRODUCTS LIABILITY - DEFECTIVE PRODUCT
...

III. BREACH OF EXPRESS WARRANTY
...

PRAYER FOR RELIEF

WHEREFORE, Plaintiff seeks:
1. $1,500.00 (purchase price) plus damages
2. Pre-judgment and post-judgment interest
3. Attorney's fees and costs
4. Such other relief as the Court deems proper
```

---

## 🚨 Troubleshooting

### System won't start

```bash
# Check dependencies
python -m pip install -r requirements.txt

# Check ports
lsof -i :3000  # Check frontend port
lsof -i :5000  # Check backend port
```

### Tests fail

```bash
# Verify test setup
python -m pytest --collect-only tests/e2e/test_sof_e2e.py

# Run with debug output
python -m pytest tests/e2e/test_sof_e2e.py -v -s
```

### Document generation errors

```bash
# Check templates
ls -la src/lawyerfactory/export/renderers/legacy/templates/

# Test generator directly
python src/lawyerfactory/export/renderers/legacy/generator.py
```

---

## 📚 Important Files Reference

| Purpose              | File                                                     | Status               |
| -------------------- | -------------------------------------------------------- | -------------------- |
| **Entry Point**      | `src/lawyerfactory/compose/maestro/maestro.py`           | ✅ Main orchestrator |
| **Workflow Control** | `src/lawyerfactory/compose/maestro/workflow_enhanced.py` | ✅ Phase management  |
| **Document Export**  | `src/lawyerfactory/export/legal_document_generator.py`   | ✅ Output formats    |
| **Backend API**      | `apps/api/server.py`                                     | ✅ REST endpoints    |
| **Frontend UI**      | `apps/ui/react-app/src/App.jsx`                          | ✅ React interface   |
| **Tests**            | `tests/e2e/test_sof_e2e.py`                              | ✅ End-to-end tests  |

---

## ✅ Success Criteria

You'll know it's working when:

- ✅ Tests pass: `pytest tests/e2e/test_sof_e2e.py -v` shows all tests green
- ✅ UI loads: http://localhost:5173 shows the control terminal
- ✅ Forms work: Can submit intake data
- ✅ Document generated: Output folder contains complaint PDF
- ✅ Compliance verified: SOF marked as Rule 12(b)(6) compliant

---

## 🎯 Next Steps

1. **Run E2E tests first** to verify system integrity
2. **Use UI to test manually** with the intake form
3. **Check output folder** for generated documents
4. **Review generated complaint** for quality
5. **Customize for your jurisdiction** (jurisdiction-specific rules)

Good luck! 🚀
