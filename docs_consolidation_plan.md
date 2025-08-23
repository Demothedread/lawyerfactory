# Documentation Consolidation Plan

## Current Documentation Analysis

### Root Level Documentation (Keep/Consolidate)
- `./README.md` - Main project README (KEEP as authoritative)
- `./SYSTEM_DOCUMENTATION.md` - System overview (MERGE into main README)
- `./POST_PRODUCTION_IMPLEMENTATION_SUMMARY.md` - Implementation details (MERGE into docs)
- `./STATEMENT_OF_FACTS_GENERATOR_README.md` - Specific component docs (MERGE into components)

### Documentation Categories

#### 1. Architecture Documentation (`docs/architecture/`)
- `architecture.md` - Main architecture overview (KEEP)
- `kg_schema.md` - Knowledge graph schema (KEEP)
- `roadmap.md` - Development roadmap (KEEP)

#### 2. API Documentation (`docs/api/`)
- `ingest_pipeline.md` - Ingestion pipeline docs (KEEP)
- `orchestration_implementation.md` - Orchestration details (KEEP)
- `orchestration_maestro_spec.md` - Maestro specifications (KEEP)

#### 3. Component Documentation (`docs/components/`)
- `ai_document_generator_guide.md` - AI document generation (KEEP)
- `claims_matrix.md` - Claims matrix system (KEEP)
- `evidence_workflow_implementation_plan.md` - Evidence workflow (KEEP)
- `form_analysis.md` - Form analysis (KEEP)
- `research.md` - Research components (KEEP)
- `skeletal_outline_system.md` - Outline system (KEEP)
- `ui_workflow_visualization.md` - UI visualization (KEEP)

#### 4. Development Documentation (`docs/development/`)
**Problem**: Many TODO and progress files that should be consolidated
- `claims_matrix_plan.md` - Plan (MERGE with main claims_matrix.md)
- `claims_matrix_progress.md` - Progress updates (MERGE or ARCHIVE)
- `claims_matrix_todo.md` - TODO items (MERGE or ARCHIVE)
- `drafting_pipeline.md` - Drafting pipeline (KEEP)
- `evidence_workflow_todo.md` - TODO items (MERGE or ARCHIVE)
- `implementation_summary_plan_ab_combined.md` - Implementation summary (MERGE)
- `knowledge_graph_integration_todo.md` - TODO items (MERGE or ARCHIVE)
- `legal_specialist_instructions.md` - Legal instructions (KEEP)
- `outline_design.md` - Outline design (KEEP)
- `prompt_instructions.md` - Prompt instructions (KEEP)
- `team.md` - Team information (KEEP)

#### 5. Scattered Documentation (Consolidate)
- `src/lawyerfactory/claims/CAUSE_OF_ACTION_DEFINITION_ENGINE_README.md` - Move to `docs/components/`
- `README_PAN_Analyzer.md` - Specific analyzer docs (KEEP or MERGE)
- `trash/KNOWLEDGE_GRAPH_INTEGRATION_README.md` - Already in trash (IGNORE)
- `trash/LEGAL_RESEARCH_INTEGRATION_README.md` - Already in trash (IGNORE)

## Consolidation Strategy

### Phase 1: Create Consolidated Structure

#### New Documentation Structure
```
docs/
├── README.md                    # Main docs index
├── architecture/                # Architecture docs
│   ├── README.md               # Architecture overview
│   ├── system_architecture.md  # Consolidated architecture
│   ├── knowledge_graph.md      # KG schema and design
│   └── roadmap.md              # Development roadmap
├── api/                        # API documentation
│   ├── README.md               # API overview
│   ├── ingest_pipeline.md      # Ingestion APIs
│   ├── orchestration.md        # Orchestration APIs
│   └── maestro_spec.md         # Maestro specifications
├── components/                 # Component documentation
│   ├── README.md               # Components overview
│   ├── ai_document_generator.md
│   ├── claims_matrix.md        # Consolidated claims matrix docs
│   ├── evidence_workflow.md    # Consolidated evidence workflow
│   ├── research_system.md      # Consolidated research docs
│   ├── outline_system.md       # Consolidated outline docs
│   └── ui_components.md        # Consolidated UI docs
├── development/                # Development documentation
│   ├── README.md               # Development overview
│   ├── getting_started.md      # Setup and development
│   ├── architecture_decisions.md # ADRs and decisions
│   ├── testing_guide.md        # Testing documentation
│   └── deployment.md           # Deployment instructions
├── guides/                     # User guides
│   ├── user_manual.md          # End user documentation
│   ├── api_guide.md            # API usage guide
│   └── troubleshooting.md      # Troubleshooting guide
└── legal/                      # Legal-specific documentation
    ├── case_studies.md         # Case study documentation
    ├── legal_references.md     # Legal references
    └── compliance.md           # Compliance documentation
```

### Phase 2: Content Consolidation

#### Claims Matrix Documentation
**Merge into `docs/components/claims_matrix.md`:**
- `docs/components/claims_matrix.md` (base)
- `docs/development/claims_matrix_plan.md`
- `docs/development/claims_matrix_progress.md`
- `docs/development/claims_matrix_todo.md`
- `src/lawyerfactory/claims/CAUSE_OF_ACTION_DEFINITION_ENGINE_README.md`

#### Evidence Workflow Documentation
**Merge into `docs/components/evidence_workflow.md`:**
- `docs/components/evidence_workflow_implementation_plan.md`
- `docs/development/evidence_workflow_todo.md`

#### Research Documentation
**Merge into `docs/components/research_system.md`:**
- `docs/components/research.md`
- `docs/development/knowledge_graph_integration_todo.md`

#### System Documentation
**Merge into main `README.md`:**
- `SYSTEM_DOCUMENTATION.md`
- `POST_PRODUCTION_IMPLEMENTATION_SUMMARY.md`
- `docs/development/implementation_summary_plan_ab_combined.md`

### Phase 3: Quality Improvements

#### Documentation Standards
1. **Consistent Headers**: Use H1 (#) for main title, H2 (##) for sections
2. **Code Examples**: Include practical code examples
3. **Cross-References**: Link between related documents
4. **Version Information**: Include last updated dates
5. **Table of Contents**: Add TOC for longer documents

#### Content Organization
1. **Purpose**: What does this component do?
2. **Architecture**: How is it structured?
3. **Usage**: How to use it?
4. **Configuration**: How to configure it?
5. **API Reference**: Available functions/methods
6. **Examples**: Practical examples
7. **Troubleshooting**: Common issues and solutions

## Implementation Plan

### Week 1: Structure Creation
1. Create new directory structure
2. Move existing files to appropriate locations
3. Create README files for each section

### Week 2: Content Consolidation
1. Merge related documents
2. Update cross-references
3. Standardize formatting
4. Add missing sections

### Week 3: Quality Enhancement
1. Add code examples
2. Create API references
3. Add troubleshooting sections
4. Review and validate content

### Week 4: Cleanup and Validation
1. Remove duplicate files
2. Update main README.md
3. Validate all links
4. Get team feedback

## Success Criteria

1. **Single Source of Truth**: Each component has one authoritative document
2. **Complete Coverage**: All major components are documented
3. **Easy Navigation**: Clear structure and cross-references
4. **Up-to-date Content**: Current information and examples
5. **Consistent Format**: Standardized documentation style
6. **Accessible**: Easy to find and understand

## Files to Stage for Removal

### Immediate Removal (Duplicates)
- `docs/development/claims_matrix_plan.md` (merged into claims_matrix.md)
- `docs/development/claims_matrix_progress.md` (archived)
- `docs/development/claims_matrix_todo.md` (archived)
- `docs/development/evidence_workflow_todo.md` (merged)
- `docs/development/knowledge_graph_integration_todo.md` (merged)
- `src/lawyerfactory/claims/CAUSE_OF_ACTION_DEFINITION_ENGINE_README.md` (moved)

### Future Review (Potentially Remove)
- `README_PAN_Analyzer.md` (consider merging or keeping separate)
- `trash/KNOWLEDGE_GRAPH_INTEGRATION_README.md` (already in trash)
- `trash/LEGAL_RESEARCH_INTEGRATION_README.md` (already in trash)

## Migration Checklist

- [ ] Create new documentation structure
- [ ] Move existing files to new locations
- [ ] Merge duplicate content
- [ ] Update cross-references
- [ ] Standardize formatting
- [ ] Add missing sections
- [ ] Validate all links
- [ ] Update main README.md
- [ ] Remove duplicate files
- [ ] Get team review