# Post-Production Court Packet Protocol

## Purpose
This protocol defines how LawyerFactory consolidates the sequential multi-phase workflow into a
court-ready packet for filing. Each phase output **must** build on prior phase outputs, ensuring
traceability from intake through finalization.

## Sequential Phase Chain (Ingestion → Finalization)
1. **Ingestion (Intake)**: Client documents, evidence, and case metadata are captured and normalized.
2. **Planning**: The orchestration layer translates intake into an execution plan and task list.
3. **Research**: Authorities, statutes, and precedents are retrieved and validated for jurisdiction.
4. **Outlining**: The case outline and claims matrix formalize legal structure and issues.
5. **Drafting**: Draft pleadings and supporting statements are generated using prior research + outline.
6. **Editing**: The draft is refined for legal accuracy, style, and compliance.
7. **Criticism & Review**: Quality gates identify gaps or missing citations and feed fixes upstream.
8. **Final Drafting**: All revisions are integrated to produce the final document set.
9. **Finalization (Post-Production)**: Court-ready packet is assembled, verified, and packaged.

## Default Court Rules
If no jurisdiction is provided, the protocol defaults to **Superior Court of California** and
California-specific pleading conventions.

## Court Packet Deliverables
The post-production protocol produces:
- **Cover Sheet**: Defaulted to Superior Court of California caption format.
- **Table of Authorities**: Derived from research phase citations and formatted for filing.
- **Supplemental Evidence Index**: Collates evidence and attachments from intake + review.
- **Manifest**: JSON map tying each deliverable to its source phase output.
- **ZIP Package**: Combines the complaint, supporting documents, and generated deliverables.

## Post-Production Assembly Rules
1. **Phase Chain Integrity**: Each artifact includes upstream phase references to maintain lineage.
2. **Jurisdiction Safety**: Defaults to California Superior Court unless overridden by intake data.
3. **Authority Validation**: Only validated authorities are included in the table of authorities.
4. **Evidence Completeness**: Evidence index must include all intake + review items.
5. **Packaging**: Packet outputs must be bundled as a single ZIP for PDF/DOCX delivery.

## Output Locations
All post-production assets are written to:
```
output/post_production/
```

## Operational Checklist
- [ ] Intake metadata includes case caption, parties, and jurisdiction.
- [ ] Research outputs include validated authorities.
- [ ] Outline output references claims and legal structure.
- [ ] Drafts reference outline + research sources.
- [ ] Editing confirms formatting and citation accuracy.
- [ ] Finalization generates cover sheet, TOA, evidence index, and ZIP package.
