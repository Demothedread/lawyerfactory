"""
# Script Name: pdf_form_filler.py
# Description: PDF Form Filling Module for LawyerFactory  This module takes field mappings and applies them to PDF forms, creating completed court documents ready for filing.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Document Generation
#   - Group Tags: null
PDF Form Filling Module for LawyerFactory

This module takes field mappings and applies them to PDF forms, creating
completed court documents ready for filing.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .field_mapper import FieldMapping, MappingResult
from .pdf_handler import PDFHandler


@dataclass
class FillingResult:
    """Result of PDF form filling operation."""
    
    form_name: str
    output_path: str
    success: bool
    filled_fields: int
    total_fields: int
    errors: List[str]
    warnings: List[str]
    completion_percentage: float


class PDFFormFiller:
    """
    PDF form filler that populates court forms with case data.
    
    This class takes field mappings and applies them to PDF forms,
    creating completed documents ready for filing.
    """
    
    def __init__(self, forms_directory: str = "docs/Court_files", 
                 output_directory: str = "output"):
        """
        Initialize PDFFormFiller.
        
        Args:
            forms_directory: Path to directory containing PDF court forms
            output_directory: Path to directory for saving filled forms
        """
        self.forms_directory = Path(forms_directory)
        self.output_directory = Path(output_directory)
        self.pdf_handler = PDFHandler(forms_directory)
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
    def fill_form(self, mapping_result: MappingResult, 
                  output_filename: Optional[str] = None) -> FillingResult:
        """
        Fill a PDF form using field mappings.
        
        Args:
            mapping_result: Result from FieldMapper containing field mappings
            output_filename: Optional custom filename for output (without extension)
            
        Returns:
            FillingResult with success status and details
        """
        
        form_name = mapping_result.form_name
        
        # Validate form exists
        available_forms = self.pdf_handler.get_available_forms()
        if form_name not in available_forms:
            return FillingResult(
                form_name=form_name,
                output_path="",
                success=False,
                filled_fields=0,
                total_fields=0,
                errors=[f"Form not found: {form_name}"],
                warnings=[],
                completion_percentage=0.0
            )
        
        # Generate output filename
        if not output_filename:
            output_filename = f"{form_name}_filled"
        
        output_path = self.output_directory / f"{output_filename}.pdf"
        
        # Convert mappings to field data dictionary
        field_data = {}
        filled_count = 0
        errors = []
        warnings = []
        
        for mapping in mapping_result.mappings:
            try:
                # Validate and convert mapping value
                converted_value = self._convert_mapping_value(mapping)
                field_data[mapping.field_name] = converted_value
                filled_count += 1
                
                # Add warning for low confidence mappings
                if mapping.confidence < 0.7:
                    warnings.append(f"Low confidence mapping for {mapping.field_name}: {mapping.confidence:.1%}")
                    
            except Exception as e:
                error_msg = f"Error processing mapping for {mapping.field_name}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
        
        # Fill the PDF form
        template_path = available_forms[form_name]
        
        try:
            success = self.pdf_handler.fill_pdf_form(
                template_path=template_path,
                field_data=field_data,
                output_path=output_path
            )
            
            if not success:
                errors.append("PDF form filling failed")
            
        except Exception as e:
            error_msg = f"Error filling PDF form: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            success = False
        
        # Calculate completion percentage
        total_fields = len(mapping_result.mappings) + len(mapping_result.unmapped_fields)
        completion_percentage = (filled_count / total_fields * 100) if total_fields > 0 else 0.0
        
        # Add warnings for unmapped fields
        if mapping_result.unmapped_fields:
            warnings.append(f"{len(mapping_result.unmapped_fields)} fields remain unmapped")
        
        # Add warnings for missing data
        if mapping_result.missing_data:
            warnings.append(f"Missing required data: {', '.join(mapping_result.missing_data)}")
        
        return FillingResult(
            form_name=form_name,
            output_path=str(output_path) if success else "",
            success=success,
            filled_fields=filled_count,
            total_fields=total_fields,
            errors=errors,
            warnings=warnings,
            completion_percentage=completion_percentage
        )
    
    def _convert_mapping_value(self, mapping: FieldMapping) -> str:
        """Convert and validate a mapping value for PDF form filling."""
        
        value = mapping.mapped_value
        field_type = mapping.field_type
        
        # Handle None or empty values
        if value is None or value == "":
            return ""
        
        # Convert to string and handle field type specific formatting
        str_value = str(value)
        
        if field_type == 'checkbox':
            # For checkboxes, convert boolean-like values
            if isinstance(value, bool):
                return "Yes" if value else ""
            elif str_value.lower() in ['true', 'yes', '1', 'on']:
                return "Yes"
            elif str_value.lower() in ['false', 'no', '0', 'off']:
                return ""
            else:
                # If uncertain, leave checkbox unchecked
                return ""
        
        elif field_type == 'text':
            # For text fields, ensure reasonable length
            if len(str_value) > 1000:  # Arbitrary limit
                return str_value[:997] + "..."
            return str_value
        
        else:
            # Default string conversion
            return str_value
    
    def fill_multiple_forms(self, mapping_results: List[MappingResult], 
                           case_prefix: str = "case") -> List[FillingResult]:
        """
        Fill multiple PDF forms for a case.
        
        Args:
            mapping_results: List of mapping results for different forms
            case_prefix: Prefix for output filenames
            
        Returns:
            List of FillingResult objects
        """
        
        results = []
        
        for i, mapping_result in enumerate(mapping_results):
            # Generate unique filename for each form
            output_filename = f"{case_prefix}_{mapping_result.form_name}_{i+1:02d}"
            
            try:
                result = self.fill_form(mapping_result, output_filename)
                results.append(result)
                
                if result.success:
                    self.logger.info(f"Successfully filled {mapping_result.form_name}")
                else:
                    self.logger.warning(f"Failed to fill {mapping_result.form_name}: {result.errors}")
                    
            except Exception as e:
                error_msg = f"Error filling form {mapping_result.form_name}: {str(e)}"
                self.logger.error(error_msg)
                
                results.append(FillingResult(
                    form_name=mapping_result.form_name,
                    output_path="",
                    success=False,
                    filled_fields=0,
                    total_fields=0,
                    errors=[error_msg],
                    warnings=[],
                    completion_percentage=0.0
                ))
        
        return results
    
    def create_form_package(self, mapping_results: List[MappingResult], 
                           case_name: str, case_number: str = "") -> Dict[str, Any]:
        """
        Create a complete package of filled forms for a case.
        
        Args:
            mapping_results: List of mapping results for all forms
            case_name: Name identifier for the case
            case_number: Optional case number
            
        Returns:
            Dictionary with package information and results
        """
        
        # Clean case name for filename
        clean_case_name = "".join(c for c in case_name if c.isalnum() or c in (' ', '-', '_')).strip()
        case_prefix = clean_case_name.replace(' ', '_')
        
        if case_number:
            case_prefix = f"{case_prefix}_{case_number}"
        
        # Fill all forms
        filling_results = self.fill_multiple_forms(mapping_results, case_prefix)
        
        # Analyze results
        successful_forms = [r for r in filling_results if r.success]
        failed_forms = [r for r in filling_results if not r.success]
        
        total_filled_fields = sum(r.filled_fields for r in filling_results)
        total_fields = sum(r.total_fields for r in filling_results)
        
        package_completion = (total_filled_fields / total_fields * 100) if total_fields > 0 else 0.0
        
        # Collect all files
        output_files = [r.output_path for r in successful_forms if r.output_path]
        
        # Collect warnings and errors
        all_warnings = []
        all_errors = []
        
        for result in filling_results:
            all_warnings.extend(result.warnings)
            all_errors.extend(result.errors)
        
        package_info = {
            'case_name': case_name,
            'case_number': case_number,
            'package_prefix': case_prefix,
            'total_forms': len(mapping_results),
            'successful_forms': len(successful_forms),
            'failed_forms': len(failed_forms),
            'total_filled_fields': total_filled_fields,
            'total_fields': total_fields,
            'package_completion': package_completion,
            'output_files': output_files,
            'form_results': filling_results,
            'warnings': list(set(all_warnings)),  # Remove duplicates
            'errors': list(set(all_errors)),      # Remove duplicates
            'ready_for_filing': len(failed_forms) == 0 and package_completion > 80.0
        }
        
        # Log package summary
        self.logger.info(f"Created form package for {case_name}:")
        self.logger.info(f"  - {len(successful_forms)}/{len(mapping_results)} forms filled successfully")
        self.logger.info(f"  - {package_completion:.1f}% field completion")
        self.logger.info(f"  - Ready for filing: {package_info['ready_for_filing']}")
        
        return package_info
    
    def validate_filled_form(self, output_path: str) -> Dict[str, Any]:
        """
        Validate a filled PDF form for completeness and correctness.
        
        Args:
            output_path: Path to the filled PDF form
            
        Returns:
            Dictionary with validation results
        """
        
        if not Path(output_path).exists():
            return {
                'valid': False,
                'errors': [f"File not found: {output_path}"],
                'warnings': [],
                'field_analysis': {}
            }
        
        try:
            # Extract fields from filled form to check completion
            filled_fields = self.pdf_handler.extract_form_fields(Path(output_path))
            
            errors = []
            warnings = []
            field_analysis = {}
            
            empty_fields = 0
            filled_fields_count = 0
            
            for field in filled_fields:
                if field.value and field.value.strip():
                    filled_fields_count += 1
                    field_analysis[field.name] = {
                        'filled': True,
                        'value': field.value,
                        'type': field.field_type
                    }
                else:
                    empty_fields += 1
                    field_analysis[field.name] = {
                        'filled': False,
                        'value': '',
                        'type': field.field_type
                    }
            
            # Generate warnings for empty fields
            if empty_fields > 0:
                warnings.append(f"{empty_fields} fields remain empty")
            
            completion_rate = (filled_fields_count / len(filled_fields) * 100) if filled_fields else 0
            
            if completion_rate < 50:
                warnings.append(f"Low completion rate: {completion_rate:.1f}%")
            
            validation_result = {
                'valid': len(errors) == 0,
                'completion_rate': completion_rate,
                'filled_fields': filled_fields_count,
                'empty_fields': empty_fields,
                'total_fields': len(filled_fields),
                'errors': errors,
                'warnings': warnings,
                'field_analysis': field_analysis
            }
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'field_analysis': {}
            }


def test_pdf_form_filler():
    """Test function for PDFFormFiller functionality."""
    
    from .field_mapper import FieldMapping

    # Create test data
    test_mappings = [
        FieldMapping(
            field_name="FillText1",
            field_type="text",
            mapped_value="John Doe",
            confidence=0.95,
            source_data="plaintiff_name",
            transformation_applied="name formatting"
        ),
        FieldMapping(
            field_name="FillText2", 
            field_type="text",
            mapped_value="Tesla Motors, Inc.",
            confidence=0.90,
            source_data="defendant_name",
            transformation_applied="name formatting"
        )
    ]
    
    # Create mock mapping result
    from .field_mapper import MappingResult
    mock_mapping_result = MappingResult(
        form_name="pld001_contract",
        mappings=test_mappings,
        unmapped_fields=["FillText3", "FillText4"],
        missing_data=[],
        mapping_confidence=0.85,
        warnings=[]
    )
    
    print("Testing PDF Form Filler:")
    print("=" * 50)
    
    try:
        filler = PDFFormFiller()
        print(f"Output directory: {filler.output_directory}")
        
        # Test single form filling
        result = filler.fill_form(mock_mapping_result, "test_contract")
        
        print("\nForm Filling Result:")
        print(f"  Form: {result.form_name}")
        print(f"  Success: {result.success}")
        print(f"  Filled fields: {result.filled_fields}/{result.total_fields}")
        print(f"  Completion: {result.completion_percentage:.1f}%")
        
        if result.output_path:
            print(f"  Output file: {result.output_path}")
        
        if result.errors:
            print(f"  Errors: {result.errors}")
        
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
        
        # Test package creation
        package = filler.create_form_package([mock_mapping_result], "Tesla Contract Case", "2024-001")
        
        print("\nPackage Summary:")
        print(f"  Case: {package['case_name']}")
        print(f"  Forms: {package['successful_forms']}/{package['total_forms']} successful")
        print(f"  Overall completion: {package['package_completion']:.1f}%")
        print(f"  Ready for filing: {package['ready_for_filing']}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")


if __name__ == "__main__":
    # Enable logging for testing
    logging.basicConfig(level=logging.INFO)
    test_pdf_form_filler()