#!/usr/bin/env python3
"""
Integration Example: Enhanced Categorization with Existing LawyerFactory
Shows how to integrate the new categorization system with existing phases.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def integrate_with_phase_1_intake():
    """Show how to integrate with Phase 1 (Intake)"""
    print("📋 Phase 1 Integration: Enhanced Intake Processing")
    print("=" * 60)

    integration_code = '''
# In src/lawyerfactory/phases/01_intake/ingestion/server.py

# Add imports
from enhanced_document_categorizer import EnhancedDocumentCategorizer
from vector_cluster_manager import VectorClusterManager
from enhanced_intake_processor import EnhancedIntakeProcessor

# Initialize enhanced components
categorizer = EnhancedDocumentCategorizer()
cluster_manager = VectorClusterManager()
intake_processor = EnhancedIntakeProcessor()

# Replace simple categorization with enhanced version
@app.route('/api/intake/process-document', methods=['POST'])
async def process_document():
    """Enhanced document processing with categorization"""
    try:
        file = request.files['document']
        case_id = request.form.get('case_id')

        # Read document content
        content = file.read().decode('utf-8', errors='ignore')

        # Enhanced categorization
        document = categorizer.categorize_document(
            text=content,
            filename=file.filename,
            defendant_hint=get_case_defendant(case_id)
        )

        # Add to appropriate cluster
        success = await cluster_manager.add_document(
            document=document,
            text_content=content
        )

        return jsonify({
            'success': success,
            'document_id': document.document_id,
            'document_type': document.document_type.value,
            'authority_level': document.authority_level.value,
            'cluster_id': document.cluster_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''

    print(integration_code)

def integrate_with_phase_5_drafting():
    """Show how to integrate with Phase 5 (Drafting)"""
    print("\n⚖️ Phase 5 Integration: Drafting Validation")
    print("=" * 60)

    integration_code = '''
# In src/lawyerfactory/phases/05_drafting/drafting_validator.py

# Add imports
from drafting_validator import DraftingValidator

# Initialize validator
drafting_validator = DraftingValidator()

# Add validation endpoint
@app.route('/api/drafting/validate', methods=['POST'])
async def validate_draft():
    """Validate draft complaint against defendant cluster"""
    try:
        draft_text = request.form.get('draft_text')
        case_id = request.form.get('case_id')

        # Validate draft
        validation_result = await drafting_validator.validate_draft_complaint(
            draft_text=draft_text,
            case_id=case_id
        )

        return jsonify({
            'validation_result': {
                'is_valid': validation_result.is_valid,
                'overall_score': validation_result.overall_score,
                'similarity_score': validation_result.similarity_score,
                'issues_found': validation_result.issues_found,
                'recommendations': validation_result.recommendations,
                'processing_time': validation_result.processing_time
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Integrate with existing drafting workflow
def enhanced_drafting_workflow(case_data, draft_text):
    """Enhanced drafting workflow with validation"""

    # Step 1: Generate initial draft (existing logic)
    initial_draft = generate_initial_draft(case_data)

    # Step 2: Validate against defendant cluster
    validation = await drafting_validator.validate_draft_complaint(
        draft_text=initial_draft,
        case_id=case_data['case_id']
    )

    # Step 3: Improve draft if needed
    if not validation.is_valid:
        improved_draft = await improve_draft_with_recommendations(
            initial_draft,
            validation.recommendations
        )
        return improved_draft

    return initial_draft
'''

    print(integration_code)

def create_enhanced_assessor():
    """Create enhanced assessor that uses the new categorization"""
    print("\n🔍 Enhanced Assessor Integration")
    print("=" * 60)

    enhanced_assessor_code = '''
# In src/lawyerfactory/phases/01_intake/ingestion/assessor.py

# Enhanced categorization function
def enhanced_categorize_document(content, filename, defendant_hint=None):
    """Enhanced document categorization with defendant recognition"""

    # Use the enhanced categorizer
    from enhanced_document_categorizer import EnhancedDocumentCategorizer

    categorizer = EnhancedDocumentCategorizer()
    document = categorizer.categorize_document(
        text=content,
        filename=filename,
        defendant_hint=defendant_hint
    )

    return {
        'document_type': document.document_type.value,
        'authority_level': document.authority_level.value,
        'defendant_name': document.defendant_name,
        'confidence_score': document.confidence_score,
        'extracted_entities': document.extracted_entities,
        'key_legal_issues': document.key_legal_issues,
        'cluster_id': document.cluster_id
    }

# Replace existing categorize function
def categorize(text, filename=None, defendant_hint=None):
    """Enhanced categorization replacing simple keyword matching"""
    return enhanced_categorize_document(text, filename, defendant_hint)
'''

    print(enhanced_assessor_code)

def show_benefits():
    """Show the benefits of the enhanced system"""
    print("\n🎯 Benefits of Enhanced Categorization System")
    print("=" * 60)

    benefits = [
        {
            'title': 'Advanced Document Recognition',
            'benefits': [
                'Distinguishes judge opinions from complaints',
                'Recognizes defendant-specific documents',
                'Identifies authority levels automatically',
                'Extracts legal entities and issues'
            ]
        },
        {
            'title': 'Defendant-Specific Intelligence',
            'benefits': [
                'Creates dedicated clusters per defendant',
                'Learns patterns from similar cases',
                'Provides defendant-specific recommendations',
                'Validates against relevant precedents'
            ]
        },
        {
            'title': 'Improved Draft Quality',
            'benefits': [
                'Validates drafts against successful complaints',
                'Provides similarity-based feedback',
                'Suggests improvements based on patterns',
                'Ensures consistency with similar cases'
            ]
        },
        {
            'title': 'Generic System Architecture',
            'benefits': [
                'Works with any defendant from intake forms',
                'Scalable to multiple jurisdictions',
                'Adapts to different case types',
                'Maintains separate clusters per defendant'
            ]
        }
    ]

    for benefit in benefits:
        print(f"\n📈 {benefit['title']}:")
        for item in benefit['benefits']:
            print(f"   ✅ {item}")

def create_implementation_roadmap():
    """Create implementation roadmap"""
    print("\n🛣️ Implementation Roadmap")
    print("=" * 60)

    roadmap = [
        {
            'phase': 'Week 1: Foundation',
            'tasks': [
                'Integrate EnhancedDocumentCategorizer with Phase 1',
                'Replace simple categorize() function',
                'Test document type recognition accuracy'
            ]
        },
        {
            'phase': 'Week 2: Cluster System',
            'tasks': [
                'Implement VectorClusterManager',
                'Create defendant-specific clusters',
                'Test cluster creation and document addition'
            ]
        },
        {
            'phase': 'Week 3: Intake Enhancement',
            'tasks': [
                'Integrate EnhancedIntakeProcessor',
                'Add intake form processing with cluster creation',
                'Test with multiple defendants'
            ]
        },
        {
            'phase': 'Week 4: Drafting Validation',
            'tasks': [
                'Implement DraftingValidator',
                'Add validation endpoints to drafting phase',
                'Test validation accuracy and recommendations'
            ]
        },
        {
            'phase': 'Week 5: Integration & Testing',
            'tasks': [
                'End-to-end testing with real documents',
                'Performance optimization',
                'User feedback and refinement'
            ]
        }
    ]

    for phase in roadmap:
        print(f"\n📅 {phase['phase']}:")
        for task in phase['tasks']:
            print(f"   • {task}")

def main():
    """Main integration demonstration"""
    print("🔧 Enhanced Document Categorization Integration Guide")
    print("This guide shows how to integrate the new system with existing LawyerFactory")

    # Show integrations
    integrate_with_phase_1_intake()
    integrate_with_phase_5_drafting()
    create_enhanced_assessor()
    show_benefits()
    create_implementation_roadmap()

    print("\n🎉 Integration Guide Complete!")
    print("=" * 60)
    print("The enhanced categorization system is ready for integration.")
    print("Start with Phase 1 integration and gradually expand to other phases.")

if __name__ == "__main__":
    main()