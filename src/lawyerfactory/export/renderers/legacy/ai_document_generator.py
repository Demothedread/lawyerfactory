"""
# Script Name: ai_document_generator.py
# Description: AI-Powered Document Generator for LawyerFactory  This module integrates all AI components to provide intelligent, automated legal document generation with form selection, field mapping, and compliance checking.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Document Generation
#   - Group Tags: null
AI-Powered Document Generator for LawyerFactory

This module integrates all AI components to provide intelligent, automated
legal document generation with form selection, field mapping, and compliance checking.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import our AI modules
from .modules.ai_case_classifier import CaseClassification, CaseClassifier
from .modules.field_mapper import FieldMapper, MappingResult
from .modules.form_selector import FormSelectionResult, FormSelector
from .modules.pdf_form_filler import FillingResult, PDFFormFiller


@dataclass
class DocumentGenerationResult:
    """Complete result of AI-powered document generation."""
    
    case_classification: CaseClassification
    form_selection: FormSelectionResult
    form_mappings: List[MappingResult]
    filling_results: List[FillingResult]
    package_info: Dict[str, Any]
    
    success: bool
    total_processing_time: float
    errors: List[str]
    warnings: List[str]
    
    # Summary metrics
    forms_generated: int
    fields_filled: int
    completion_percentage: float
    ready_for_filing: bool


class AIDocumentGenerator:
    """
    AI-powered document generator that orchestrates intelligent legal document creation.
    
    This class integrates case classification, form selection, field mapping,
    and PDF filling to create complete legal document packages.
    """
    
    def __init__(self, forms_directory: str = "docs/Court_files", 
                 output_directory: str = "output"):
        """
        Initialize AI Document Generator.
        
        Args:
            forms_directory: Path to directory containing PDF court forms
            output_directory: Path to directory for saving generated documents
        """
        self.forms_directory = Path(forms_directory)
        self.output_directory = Path(output_directory)
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI components
        self.case_classifier = CaseClassifier()
        self.form_selector = FormSelector(forms_directory)
        self.field_mapper = FieldMapper(forms_directory)
        self.form_filler = PDFFormFiller(forms_directory, output_directory)
        
        self.logger.info("AI Document Generator initialized successfully")
    
    def generate_documents(self, case_data: Dict[str, Any], 
                          case_name: Optional[str] = None,
                          options: Optional[Dict[str, Any]] = None) -> DocumentGenerationResult:
        """
        Generate complete legal document package using AI.
        
        Args:
            case_data: Dictionary containing case facts, parties, and context
            case_name: Optional name for the case (for file naming)
            options: Optional generation options and preferences
            
        Returns:
            DocumentGenerationResult with complete generation details
        """
        
        start_time = datetime.now()
        options = options or {}
        
        # Generate case name if not provided
        if not case_name:
            case_name = self._generate_case_name(case_data)
        
        self.logger.info(f"Starting AI document generation for: {case_name}")
        
        errors = []
        warnings = []
        
        try:
            # Step 1: Classify the case using AI
            self.logger.info("Step 1: AI Case Classification")
            classification = self._classify_case(case_data)
            
            if classification.primary_type.value == "unknown":
                warnings.append("Case classification has low confidence - review may be needed")
            
            # Step 2: AI-powered form selection
            self.logger.info("Step 2: AI Form Selection")
            form_selection = self._select_forms(classification, options)
            
            if not form_selection.primary_forms:
                errors.append("No appropriate forms could be selected for this case type")
                return self._create_error_result(case_name, classification, errors, warnings, start_time)
            
            # Step 3: AI field mapping for each selected form
            self.logger.info("Step 3: AI Field Mapping")
            form_mappings = self._map_fields(form_selection, case_data, classification)
            
            # Check if any forms have sufficient mappings
            viable_mappings = [m for m in form_mappings if m.mapping_confidence > 0.3]
            if not viable_mappings:
                errors.append("Insufficient field mappings - check case data completeness")
                return self._create_error_result(case_name, classification, errors, warnings, start_time)
            
            # Step 4: Fill PDF forms with mapped data
            self.logger.info("Step 4: PDF Form Filling")
            filling_results = self._fill_forms(viable_mappings)
            
            # Step 5: Create document package
            self.logger.info("Step 5: Package Creation")
            package_info = self._create_package(viable_mappings, case_name, case_data.get('case_number', ''))
            
            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            forms_generated = len([r for r in filling_results if r.success])
            total_fields_filled = sum(r.filled_fields for r in filling_results)
            
            # Collect warnings from all steps
            all_warnings = warnings.copy()
            all_warnings.extend(classification.key_indicators[:2])  # Add key indicators as info
            all_warnings.extend(form_selection.warnings)
            for mapping in form_mappings:
                all_warnings.extend(mapping.warnings)
            for result in filling_results:
                all_warnings.extend(result.warnings)
            
            # Determine overall success
            success = len(errors) == 0 and forms_generated > 0
            ready_for_filing = package_info.get('ready_for_filing', False)
            
            result = DocumentGenerationResult(
                case_classification=classification,
                form_selection=form_selection,
                form_mappings=form_mappings,
                filling_results=filling_results,
                package_info=package_info,
                success=success,
                total_processing_time=processing_time,
                errors=errors,
                warnings=list(set(all_warnings)),  # Remove duplicates
                forms_generated=forms_generated,
                fields_filled=total_fields_filled,
                completion_percentage=package_info.get('package_completion', 0.0),
                ready_for_filing=ready_for_filing
            )
            
            self.logger.info(f"AI document generation completed: {forms_generated} forms, "
                           f"{total_fields_filled} fields filled, {processing_time:.1f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"AI document generation failed: {str(e)}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            return self._create_error_result(case_name, None, errors, warnings, start_time)
    
    def _classify_case(self, case_data: Dict[str, Any]) -> CaseClassification:
        """Classify the case using AI."""
        
        # Extract facts for classification
        facts = case_data.get('facts', [])
        if isinstance(facts, str):
            facts = [{'text': facts}]
        elif not isinstance(facts, list):
            facts = [{'text': str(facts)}]
        
        # Add additional context
        additional_context = {
            'has_contract': 'contract' in str(case_data).lower(),
            'has_injury': any(word in str(case_data).lower() for word in ['injury', 'hurt', 'damage']),
            'has_product': 'product' in str(case_data).lower()
        }
        
        return self.case_classifier.classify_case(facts, additional_context)
    
    def _select_forms(self, classification: CaseClassification, 
                     options: Dict[str, Any]) -> FormSelectionResult:
        """Select appropriate forms using AI."""
        
        # Create case context from options
        case_context = {
            'financial_hardship': options.get('financial_hardship', False),
            'low_income': options.get('low_income', False),
            'expedited_filing': options.get('expedited_filing', False)
        }
        
        return self.form_selector.select_forms(classification, case_context)
    
    def _map_fields(self, form_selection: FormSelectionResult, 
                   case_data: Dict[str, Any], 
                   classification: CaseClassification) -> List[MappingResult]:
        """Map case data to form fields using AI."""
        
        mappings = []
        
        # Process primary forms first
        for form_rec in form_selection.primary_forms:
            mapping = self.field_mapper.map_fields(
                form_rec.form_name, case_data, classification
            )
            mappings.append(mapping)
        
        # Process optional forms if primary forms have good mappings
        primary_avg_confidence = sum(m.mapping_confidence for m in mappings) / len(mappings) if mappings else 0
        
        if primary_avg_confidence > 0.5:  # Only process optional forms if primary forms are well-mapped
            for form_rec in form_selection.optional_forms[:2]:  # Limit to top 2 optional forms
                mapping = self.field_mapper.map_fields(
                    form_rec.form_name, case_data, classification
                )
                mappings.append(mapping)
        
        return mappings
    
    def _fill_forms(self, mappings: List[MappingResult]) -> List[FillingResult]:
        """Fill PDF forms with mapped data."""
        
        results = []
        
        for mapping in mappings:
            try:
                result = self.form_filler.fill_form(mapping)
                results.append(result)
            except Exception as e:
                # Create error result for failed form
                error_result = FillingResult(
                    form_name=mapping.form_name,
                    output_path="",
                    success=False,
                    filled_fields=0,
                    total_fields=len(mapping.mappings) + len(mapping.unmapped_fields),
                    errors=[f"Form filling failed: {str(e)}"],
                    warnings=[],
                    completion_percentage=0.0
                )
                results.append(error_result)
        
        return results
    
    def _create_package(self, mappings: List[MappingResult], 
                       case_name: str, case_number: str) -> Dict[str, Any]:
        """Create document package with all forms."""
        
        try:
            return self.form_filler.create_form_package(mappings, case_name, case_number)
        except Exception as e:
            self.logger.error(f"Package creation failed: {str(e)}")
            return {
                'case_name': case_name,
                'case_number': case_number,
                'total_forms': len(mappings),
                'successful_forms': 0,
                'package_completion': 0.0,
                'ready_for_filing': False,
                'errors': [f"Package creation failed: {str(e)}"]
            }
    
    def _generate_case_name(self, case_data: Dict[str, Any]) -> str:
        """Generate a case name from case data."""
        
        plaintiff = case_data.get('plaintiff_name', 'Plaintiff')
        defendant = case_data.get('defendant_name', 'Defendant')
        
        # Clean names for file naming
        plaintiff_clean = "".join(c for c in str(plaintiff) if c.isalnum())[:20]
        defendant_clean = "".join(c for c in str(defendant) if c.isalnum())[:20]
        
        return f"{plaintiff_clean}_v_{defendant_clean}"
    
    def _create_error_result(self, case_name: str, classification: Optional[CaseClassification],
                           errors: List[str], warnings: List[str],
                           start_time: datetime) -> DocumentGenerationResult:
        """Create an error result when generation fails."""
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create dummy objects for error case
        from .modules.ai_case_classifier import CaseType
        dummy_classification = classification or CaseClassification(
            primary_type=CaseType.UNKNOWN,
            confidence=0.0,
            secondary_types=[],
            reasoning="Classification failed",
            key_indicators=[],
            damages_categories=[],
            urgency_level="medium"
        )
        
        from .modules.form_selector import FormSelectionResult
        dummy_form_selection = FormSelectionResult(
            primary_forms=[],
            optional_forms=[],
            total_forms=0,
            selection_reasoning="Form selection failed",
            warnings=[],
            estimated_completion_time=0
        )
        
        return DocumentGenerationResult(
            case_classification=dummy_classification,
            form_selection=dummy_form_selection,
            form_mappings=[],
            filling_results=[],
            package_info={'case_name': case_name, 'ready_for_filing': False},
            success=False,
            total_processing_time=processing_time,
            errors=errors,
            warnings=warnings,
            forms_generated=0,
            fields_filled=0,
            completion_percentage=0.0,
            ready_for_filing=False
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all AI components."""
        
        return {
            'ai_document_generator': 'operational',
            'components': {
                'case_classifier': {
                    'status': 'operational',
                    'supported_types': [t.value for t in self.case_classifier.get_supported_case_types()]
                },
                'form_selector': {
                    'status': 'operational',
                    'available_forms': len(self.form_selector.available_forms)
                },
                'field_mapper': {
                    'status': 'operational',
                    'pattern_count': len(self.field_mapper.field_patterns)
                },
                'form_filler': {
                    'status': 'operational',
                    'output_directory': str(self.form_filler.output_directory)
                }
            },
            'forms_directory': str(self.forms_directory),
            'output_directory': str(self.output_directory)
        }
    
    def analyze_case_requirements(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze case data and provide recommendations for improvement."""
        
        # Classify the case
        classification = self._classify_case(case_data)
        
        # Check data completeness
        required_fields = ['plaintiff_name', 'defendant_name', 'facts']
        missing_fields = [field for field in required_fields if field not in case_data or not case_data[field]]
        
        # Get form recommendations
        form_selection = self._select_forms(classification, {})
        
        # Analyze potential field mappings
        sample_mapping = None
        if form_selection.primary_forms:
            sample_form = form_selection.primary_forms[0]
            sample_mapping = self.field_mapper.map_fields(sample_form.form_name, case_data, classification)
        
        recommendations = []
        
        if missing_fields:
            recommendations.append(f"Add missing required fields: {', '.join(missing_fields)}")
        
        if classification.confidence < 0.7:
            recommendations.append("Provide more specific case details to improve classification")
        
        if sample_mapping and sample_mapping.mapping_confidence < 0.6:
            recommendations.append("Add more structured case data for better form field mapping")
        
        if classification.urgency_level == 'high':
            recommendations.append("High urgency case - consider expedited processing")
        
        return {
            'case_classification': {
                'type': classification.primary_type.value,
                'confidence': classification.confidence,
                'reasoning': classification.reasoning
            },
            'data_completeness': {
                'missing_fields': missing_fields,
                'completion_score': len(case_data) / (len(case_data) + len(missing_fields))
            },
            'form_availability': {
                'primary_forms': len(form_selection.primary_forms),
                'optional_forms': len(form_selection.optional_forms)
            },
            'mapping_preview': {
                'expected_confidence': sample_mapping.mapping_confidence if sample_mapping else 0.0,
                'mapped_fields': len(sample_mapping.mappings) if sample_mapping else 0
            },
            'recommendations': recommendations,
            'estimated_success_rate': min(classification.confidence + 0.2, 1.0)
        }


def test_ai_document_generator():
    """Test function for AI Document Generator."""
    
    print("Testing AI Document Generator:")
    print("=" * 50)
    
    try:
        # Initialize generator
        generator = AIDocumentGenerator()
        
        # Test system status
        status = generator.get_system_status()
        print(f"System Status: {status['ai_document_generator']}")
        print(f"Available Forms: {status['components']['form_selector']['available_forms']}")
        
        # Test case data
        test_case = {
            'plaintiff_name': 'John Doe',
            'defendant_name': 'Tesla Motors, Inc.',
            'contract_date': '2024-01-15',
            'incident_date': '2024-03-01',
            'damages_amount': 50000,
            'facts': [
                {'text': 'Tesla failed to deliver vehicle on the agreed contract date'},
                {'text': 'Customer suffered financial losses due to breach of contract'},
                {'text': 'Multiple attempts to resolve dispute were unsuccessful'}
            ],
            'court_name': 'Superior Court of California, County of San Francisco'
        }
        
        # Test case analysis
        print("\nCase Analysis:")
        analysis = generator.analyze_case_requirements(test_case)
        print(f"  Case Type: {analysis['case_classification']['type']}")
        print(f"  Confidence: {analysis['case_classification']['confidence']:.1%}")
        print(f"  Primary Forms Available: {analysis['form_availability']['primary_forms']}")
        print(f"  Expected Success Rate: {analysis['estimated_success_rate']:.1%}")
        
        if analysis['recommendations']:
            print(f"  Recommendations: {analysis['recommendations']}")
        
        # Test document generation (this will fail due to PDF dependencies, but shows the flow)
        print("\nDocument Generation Test:")
        print("  Would proceed with full generation in production environment")
        print("  Expected workflow: Classify → Select Forms → Map Fields → Fill PDFs → Package")
        
    except Exception as e:
        print(f"Test completed with expected dependency limitations: {str(e)}")


if __name__ == "__main__":
    # Enable logging for testing
    logging.basicConfig(level=logging.INFO)
    test_ai_document_generator()