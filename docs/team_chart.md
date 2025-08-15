# Agent Team Chart

The project follows an assembly-line approach involving specialized GPT-4.1-mini agents. Each phase represents a step in the process with human review at critical points.

| Phase | Purpose | Agents Involved |
|------|---------|----------------|
| 1. Intake | Gather user prompt and uploaded documents. Extract facts and key terms. Set up primary/secondary evidence databases. | **Maestro**, Reader, Paralegal |
| 2. Outline | Identify legal area, jurisdiction, grounds for recovery. Draft outline and raise outstanding questions for user. | Outliner, Paralegal |
| 3. Research | Conduct background research and locate relevant caselaw. Build knowledge base and caselaw database. | Researcher, Legal Researcher |
| 4. Drafting | Produce modular content following "Law of Threes" structure. | Writer, Paralegal |
| 5. Legal Review | Apply legal formatting, procedure checks, and ensure IRAC compliance. | Legal Formatter, Legal Procedure Agent |
| 6. Editing | Review for clarity, style, and coherence. | Editor |
| 7. Orchestration | Manage flow between phases and coordinate agents. | **Maestro** |

Human approval is required after phases 2, 3, 4, and 6.

