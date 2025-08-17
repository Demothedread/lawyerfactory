"""
PDF Processing Module for LawyerFactory Document Generator

This module handles PDF form field extraction, manipulation, and filling
for court document automation.
"""

import logging
import os
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

try:
    import PyPDF2
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is required. Install with: pip install PyMuPDF")

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    raise ImportError("reportlab is required. Install with: pip install reportlab")


class PDFFormField:
    """Represents a form field in a PDF document."""
    
    def __init__(self, name: str, field_type: str, value: str = "",
                 options: Optional[List[str]] = None, required: bool = False):
        self.name = name
        self.field_type = field_type  # 'text', 'checkbox', 'radio', 'dropdown'
        self.value = value
        self.options = options or []
        self.required = required
        
    def __repr__(self):
        return f"PDFFormField(name='{self.name}', type='{self.field_type}', value='{self.value}')"


class PDFHandler:
    """
    Core PDF processing class for reading and manipulating court forms.
    
    This class provides methods to:
    - Extract form fields from PDF templates
    - Fill PDF forms with data
    - Validate form field mappings
    - Create new PDF documents with court formatting
    """
    
    def __init__(self, forms_directory: str = "docs/Court_files"):
        """
        Initialize PDFHandler with forms directory.
        
        Args:
            forms_directory (str): Path to directory containing PDF court forms
        """
        self.forms_directory = Path(forms_directory)
        self.logger = logging.getLogger(__name__)
        
        if not self.forms_directory.exists():
            raise FileNotFoundError(f"Forms directory not found: {forms_directory}")
    
    def extract_form_fields(self, pdf_path: Union[str, Path]) -> List[PDFFormField]:
        """
        Extract all form fields from a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of PDFFormField objects representing the form fields
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF cannot be processed
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        fields = []
        
        try:
            # Try PyPDF2 first for form fields
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                
                if reader.is_encrypted:
                    self.logger.warning(f"PDF {pdf_path} is encrypted, attempting to decrypt")
                    reader.decrypt("")
                
                # Extract form fields if they exist
                if '/AcroForm' in reader.trailer['/Root']:
                    form = reader.trailer['/Root']['/AcroForm']
                    if '/Fields' in form:
                        for field_ref in form['/Fields']:
                            field_obj = field_ref.get_object()
                            field_name = field_obj.get('/T', 'Unknown')
                            field_type = self._determine_field_type(field_obj)
                            field_value = field_obj.get('/V', '')
                            
                            # Handle field options for dropdowns/radios
                            options = []
                            if '/Opt' in field_obj:
                                options = [str(opt) for opt in field_obj['/Opt']]
                            
                            fields.append(PDFFormField(
                                name=str(field_name),
                                field_type=field_type,
                                value=str(field_value) if field_value else "",
                                options=options
                            ))
                
                self.logger.info(f"Extracted {len(fields)} form fields from {pdf_path}")
                
        except Exception as e:
            self.logger.error(f"Error extracting fields from {pdf_path}: {str(e)}")
            # Fallback to PyMuPDF for text analysis
            try:
                fields = self._extract_fields_with_pymupdf(pdf_path)
            except Exception as fallback_error:
                self.logger.error(f"Fallback extraction also failed: {str(fallback_error)}")
                raise Exception(f"Could not extract fields from {pdf_path}: {str(e)}")
        
        return fields
    
    def _determine_field_type(self, field_obj) -> str:
        """Determine the type of a PDF form field."""
        field_type = field_obj.get('/FT', '')
        
        if field_type == '/Tx':
            return 'text'
        elif field_type == '/Btn':
            # Could be checkbox or radio button
            if '/Opt' in field_obj:
                return 'radio'
            else:
                return 'checkbox'
        elif field_type == '/Ch':
            return 'dropdown'
        else:
            return 'unknown'
    
    def _extract_fields_with_pymupdf(self, pdf_path: Path) -> List[PDFFormField]:
        """
        Fallback method using PyMuPDF to extract form information.
        
        This method analyzes text patterns to identify potential form fields
        when standard form field extraction fails.
        """
        fields = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Look for common form field patterns
                import re
                
                # Pattern for fields like "Name: ____" or "Date: ___________"
                field_patterns = [
                    r'([A-Za-z\s]+):\s*_{3,}',  # Label followed by underscores
                    r'([A-Za-z\s]+):\s*\[\s*\]',  # Label followed by checkbox
                    r'\[\s*\]\s*([A-Za-z\s]+)',  # Checkbox followed by label
                ]
                
                for pattern in field_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        field_name = match.strip()
                        if field_name and len(field_name) > 1:
                            fields.append(PDFFormField(
                                name=field_name,
                                field_type='text',  # Default to text
                                value=""
                            ))
            
            doc.close()
            self.logger.info(f"PyMuPDF extracted {len(fields)} potential fields from {pdf_path}")
            
        except Exception as e:
            self.logger.error(f"PyMuPDF extraction failed for {pdf_path}: {str(e)}")
            
        return fields
    
    def fill_pdf_form(self, template_path: Union[str, Path], 
                      field_data: Dict[str, Any], 
                      output_path: Union[str, Path]) -> bool:
        """
        Fill a PDF form with provided data.
        
        Args:
            template_path: Path to the PDF template
            field_data: Dictionary mapping field names to values
            output_path: Path for the output PDF
            
        Returns:
            True if successful, False otherwise
        """
        template_path = Path(template_path)
        output_path = Path(output_path)
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        try:
            with open(template_path, 'rb') as template_file:
                reader = PdfReader(template_file)
                writer = PdfWriter()
                
                if reader.is_encrypted:
                    reader.decrypt("")
                
                # Process each page
                for page_num, page in enumerate(reader.pages):
                    # Update form fields on this page
                    if '/Annots' in page:
                        # Update the form field values
                        writer.update_page_form_field_values(
                            writer.add_page(page), 
                            field_data
                        )
                    else:
                        writer.add_page(page)
                
                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write the filled PDF
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                self.logger.info(f"Successfully filled PDF: {output_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error filling PDF form {template_path}: {str(e)}")
            return False
    
    def validate_field_mapping(self, pdf_path: Union[str, Path], 
                              field_mapping: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Validate that a field mapping matches the actual PDF form fields.
        
        Args:
            pdf_path: Path to the PDF to validate against
            field_mapping: Dictionary mapping logical names to PDF field names
            
        Returns:
            Dictionary with 'valid', 'missing', and 'extra' field lists
        """
        pdf_fields = self.extract_form_fields(pdf_path)
        pdf_field_names = {field.name for field in pdf_fields}
        mapping_field_names = set(field_mapping.values())
        
        return {
            'valid': list(mapping_field_names.intersection(pdf_field_names)),
            'missing': list(pdf_field_names - mapping_field_names),
            'extra': list(mapping_field_names - pdf_field_names)
        }
    
    def get_available_forms(self) -> Dict[str, Path]:
        """
        Get all available PDF forms in the forms directory.
        
        Returns:
            Dictionary mapping form names to their file paths
        """
        forms = {}
        
        if not self.forms_directory.exists():
            self.logger.warning(f"Forms directory does not exist: {self.forms_directory}")
            return forms
        
        for pdf_file in self.forms_directory.glob("*.pdf"):
            # Use filename without extension as form name
            form_name = pdf_file.stem
            forms[form_name] = pdf_file
        
        self.logger.info(f"Found {len(forms)} PDF forms in {self.forms_directory}")
        return forms
    
    def analyze_form_structure(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze the structure of a PDF form for debugging and development.
        
        Args:
            pdf_path: Path to the PDF to analyze
            
        Returns:
            Dictionary containing form analysis data
        """
        fields = self.extract_form_fields(pdf_path)
        
        analysis = {
            'file_path': str(pdf_path),
            'total_fields': len(fields),
            'field_types': {},
            'fields': [],
            'has_form_fields': len(fields) > 0
        }
        
        # Count field types
        for field in fields:
            field_type = field.field_type
            analysis['field_types'][field_type] = analysis['field_types'].get(field_type, 0) + 1
            analysis['fields'].append({
                'name': field.name,
                'type': field.field_type,
                'value': field.value,
                'options': field.options,
                'required': field.required
            })
        
        return analysis


def test_pdf_handler():
    """Test function for PDFHandler functionality."""
    try:
        handler = PDFHandler()
        forms = handler.get_available_forms()
        
        print(f"Found {len(forms)} forms:")
        for name, path in forms.items():
            print(f"  - {name}: {path}")
            
            # Analyze first form as example
            if forms:
                first_form = list(forms.values())[0]
                analysis = handler.analyze_form_structure(first_form)
                print(f"\nAnalysis of {first_form.name}:")
                print(f"  Total fields: {analysis['total_fields']}")
                print(f"  Field types: {analysis['field_types']}")
                
                if analysis['fields']:
                    print("  Sample fields:")
                    for field in analysis['fields'][:5]:  # Show first 5 fields
                        print(f"    - {field['name']} ({field['type']})")
                break
                
    except Exception as e:
        print(f"Test failed: {str(e)}")


if __name__ == "__main__":
    # Enable logging for testing
    logging.basicConfig(level=logging.INFO)
    test_pdf_handler()