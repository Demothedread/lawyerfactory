# LawyerFactory User Guide

**Comprehensive Guide for Legal Professionals | Version 2.1.0**

## 📖 Quick Navigation

- [Getting Started](#getting-started)
- [Using the Interface](#using-the-interface)
- [Workflow Overview](#workflow-overview)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)
- [Advanced Features](#advanced-features)

---

## Getting Started

### First Launch

1. **System Availability**
   - Backend: http://localhost:5000
   - Frontend: http://localhost:3000
   - Status indicator appears in the footer

2. **Agent Status Check**
   - All 7 agents should show "Ready" status
   - Green indicator means system is operational
   - Red indicator means connectivity issue

3. **First Workflow**
   - Click "New Case" to start intake process
   - Follow the guided workflow through 9 phases
   - Upload documents using the drag-drop zone

### Configuration

Before starting your first case, configure:

1. **LLM Provider** (Settings → LLM Configuration)
   - Choose: OpenAI, Anthropic, or Groq
   - Enter API key
   - Select default model

2. **Legal Research** (Settings → Research)
   - Optional: Add CourtListener API key
   - Configure research depth (basic, standard, comprehensive)
   - Set evidence filter preferences

3. **Output Format** (Settings → Output)
   - Document format (Word, PDF, Markdown)
   - Citation style (Bluebook, ALWD, APA)
   - Additional options (cover sheets, TOA, TOC)

---

## Using the Interface

### Main Control Terminal

**Three-Panel Layout:**

```
┌─ Left Panel ─┬─ Center Panel ─┬─ Right Panel ──┐
│ Workflow     │ Main Content   │ Agent Status   │
│ Status       │                │                │
│ • Phases     │ • Case Intake  │ • Maestro      │
│ • Progress   │ • Document     │ • Reader       │
│              │   Preview      │ • Researcher   │
└──────────────┴────────────────┴────────────────┘
```

**Left Panel - Workflow Progress:**
- Shows all 9 phases of document generation
- Green checkmark = completed
- Blue = in progress
- Gray = not started
- Click any phase to view details

**Center Panel - Main Work Area:**
- Document intake form
- Research results display
- Document preview
- Evidence table editor

**Right Panel - Agent Status:**
- Real-time agent activity
- Current tasks assigned
- Performance metrics
- Communication logs

### Navigation

**Top Menu Bar:**
- **New Case**: Start new legal workflow
- **Open Case**: Resume existing workflow
- **Research**: Access legal research tools
- **Documents**: View/download generated documents
- **Settings**: Configure system
- **Help**: Access documentation

**Keyboard Shortcuts:**
- `Ctrl+N` - New case
- `Ctrl+O` - Open case
- `Ctrl+S` - Save current state
- `Ctrl+R` - Run research
- `Ctrl+E` - Export documents
- `Escape` - Close dialogs

### Settings Panel

**Tabs Available:**

1. **LLM Configuration**
   - Provider selection
   - Model selection
   - API key management
   - Temperature & parameters

2. **Research Settings**
   - API key configuration
   - Search preferences
   - Result filtering
   - Source quality settings

3. **Output Format**
   - Document format
   - Citation style
   - Template selection
   - Advanced formatting

4. **System Preferences**
   - Theme selection
   - Notification settings
   - Auto-save frequency
   - Log level

5. **Advanced**
   - Agent timeout settings
   - Concurrent workflow limits
   - Storage location
   - Debug options

---

## Workflow Overview

### The 9-Phase Process

#### **Phase A01: Intake & Document Processing**
- Upload client documents
- System extracts key information
- Creates initial case profile
- Organizes evidence

**Your Role:**
- Review extracted information
- Add missing details manually
- Confirm client information
- Approve extracted facts

**Expected Time:** 5-10 minutes

#### **Phase A02: Legal Research**
- System searches case law
- Identifies relevant precedents
- Evaluates authority strength
- Compiles research memorandum

**Your Role:**
- Review research results
- Add custom research areas
- Reject low-quality sources
- Approve research findings

**Expected Time:** 10-20 minutes

#### **Phase A03: Case Outline**
- Creates IRAC structure
- Develops claims matrix
- Identifies legal elements
- Maps evidence to claims

**Your Role:**
- Review legal structure
- Modify claims if needed
- Add missing elements
- Approve outline

**Expected Time:** 10-15 minutes

#### **Phase B01: Quality Review**
- System reviews all prior work
- Validates legal accuracy
- Checks for completeness
- Generates quality report

**Your Role:**
- Review quality findings
- Make corrections if needed
- Approve quality review
- Proceed to drafting

**Expected Time:** 5-10 minutes

#### **Phase B02: Document Drafting**
- System generates pleading
- Applies legal research
- Creates professional document
- Integrates all evidence

**Your Role:**
- Review draft document
- Make editorial changes
- Request revisions
- Approve draft

**Expected Time:** 15-30 minutes

#### **Phase C01: Final Editing**
- Professional formatting applied
- Citations verified
- Tables of authorities created
- Court compliance checked

**Your Role:**
- Final proofread
- Confirm formatting
- Check citations
- Approve final version

**Expected Time:** 10-20 minutes

#### **Phase C02: Final Orchestration**
- Prepares complete filing package
- Generates cover sheets
- Creates filing instructions
- Archives case materials

**Your Role:**
- Review filing package
- Confirm all documents
- Print or e-file
- Archive materials

**Expected Time:** 5-10 minutes

---

## Common Tasks

### Creating a New Case

1. Click "New Case" button
2. Fill in case information:
   - Client name and contact
   - Opposing parties
   - Court jurisdiction
   - Case type/claims
3. Upload initial documents
4. Click "Start Workflow"

### Uploading Documents

**Method 1: Drag & Drop**
- Drag document files to upload zone
- System automatically processes

**Method 2: File Browser**
- Click "Select Files"
- Choose multiple documents
- Click "Upload"

**Supported Formats:**
- PDF (including scanned)
- Word documents (.docx)
- Text files (.txt)
- Rich text (.rtf)
- Images with text

### Running Research

1. Go to Research tab
2. Enter search query
3. Select research type:
   - Background research
   - Claim substantiation
   - Fact verification
4. Configure filters
5. Click "Search"
6. Review results
7. Add to evidence table

### Managing Evidence

**Adding Evidence:**
1. Go to Evidence Table
2. Click "Add Evidence"
3. Fill in details:
   - Document description
   - Case importance (key/supporting)
   - Related facts/claims
   - Source information
4. Save

**Editing Evidence:**
1. Find evidence in table
2. Click to edit
3. Update information
4. Save changes

**Linking Evidence:**
- Drag evidence to claims
- Creates fact-claim link
- Shows connections visually
- Helps identify gaps

### Downloading Documents

1. Go to Documents tab
2. Select document
3. Choose format:
   - Microsoft Word
   - PDF
   - Markdown
4. Click "Download"
5. Choose save location

---

## Troubleshooting

### Common Issues

**System Won't Start**
- Check: Is port 5000 available?
- Check: Is port 3000 available?
- Solution: Run `lsof -i :5000 :3000` to see what's using ports

**Agents Not Responding**
- Check: Is backend running?
- Check: Are all 7 agents showing as "Ready"?
- Solution: Restart backend server

**Research Not Working**
- Check: Do you have LLM API key configured?
- Check: Is CourtListener API key valid?
- Solution: Verify API keys in Settings → LLM Configuration

**Documents Won't Generate**
- Check: Is outline complete?
- Check: Is research approved?
- Solution: Go back to previous phase and approve work

**Storage Issues**
- Issue: "Disk space low" warning
- Solution: Archive old cases or clear uploads folder
- Clear: `rm -rf workflow_storage/temp/*`

### Getting Help

**In-App Help:**
- Click Help icon (?) in top right
- Search documentation
- View keyboard shortcuts
- Access system status

**Report Issues:**
- Settings → Advanced → Bug Report
- Provides detailed system information
- Sends to development team

---

## Advanced Features

### Batch Processing

**Process Multiple Cases:**
1. Settings → Advanced → Batch Mode
2. Upload case list (CSV format)
3. System processes sequentially
4. Download all results

### Custom Workflows

**Create Workflow Template:**
1. Settings → Workflows
2. Click "New Template"
3. Configure phase options
4. Save template
5. Use for future cases

### Export & Integration

**Export Options:**
- Complete case package (ZIP)
- Individual documents
- Evidence table (Excel)
- Research memorandum
- Case timeline

**Integration APIs:**
- REST API for external systems
- WebSocket for real-time updates
- Document signing integration
- E-filing system integration

### Performance Optimization

**For Large Cases:**
1. Settings → Performance
2. Enable "Streaming Mode"
3. Reduce concurrent agents
4. Increase timeouts
5. Use incremental processing

---

## FAQ

**Q: How long does document generation take?**
A: Typically 2-5 minutes per phase, so 20-50 minutes total for complete workflow.

**Q: Can I edit generated documents?**
A: Yes, download as Word format and edit, or use in-app editor.

**Q: What if I disagree with research results?**
A: You can add additional research or override system findings at any phase.

**Q: How is my data stored?**
A: All data stored locally in `workflow_storage/` directory. Optional cloud backup available.

**Q: Can multiple attorneys work on same case?**
A: Yes, use "Share Case" feature to invite colleagues (Enterprise only).

**Q: What about attorney confidentiality?**
A: All communications encrypted, audit trails maintained, full HIPAA/GLBA compliance.

---

## Professional Standards

**Ethical Considerations:**
- You retain responsibility for all legal work
- System is tool to enhance, not replace attorney work
- All documents must be reviewed by qualified attorney
- Maintain professional liability insurance

**Court Compliance:**
- System generates court-compliant documents
- Verify local court rules before filing
- Review service requirements
- Confirm jurisdictional procedures

**Record Keeping:**
- System maintains complete audit trail
- All changes tracked with timestamps
- Full version history available
- Meets ABA model rules requirements

---

## Support & Documentation

**Additional Resources:**
- 📖 [Complete System Documentation](./SYSTEM_DOCUMENTATION.md)
- 🛠️ [Technical Reference](./docs/api/)
- 🎓 [Training Materials](./docs/training/)
- 📞 [Professional Support](mailto:support@lawyerfactory.com)

**System Status:**
- View real-time status: Settings → System Status
- Check component health
- Monitor performance metrics
- Access system logs

---

**LawyerFactory Professional Legal Automation Platform**  
*Version 2.1.0 | Production Ready | Enterprise Support Available*

For detailed technical documentation, see [SYSTEM_DOCUMENTATION.md](../../SYSTEM_DOCUMENTATION.md)
