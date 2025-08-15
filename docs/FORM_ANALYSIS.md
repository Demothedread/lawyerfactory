# Court Forms Analysis and System Design

## Available Forms Catalog

Based on the files in `docs/court_files/`:

### 1. Complaint Forms (PLD-C-001 series)
- **pld001_complaint-general.pdf** - General civil complaint form
- **pld001_contract.pdf** - Breach of contract specific complaint

### 2. Personal Injury/Property Damage Forms (PLD-PI-001 series)  
- **pld001_injury-property-death.pdf** - Personal injury, property damage, wrongful death
- **pld001_intentional-tort.pdf** - Intentional tort complaints
- **pld001_products-liability.pdf** - products liability, strict liability
- **pld001_negligence.pdf** - negligence
- **pld001_exemplary-damages.pdf** - fraud, malice, oppression, or gross negligence exemplary damages

### 3. Administrative Forms
- **additionalfeewaiver_002.pdf** - Fee waiver application
- **feewaiver_001.pdf** - Primary fee waiver (referenced but missing)

## Form Selection Logic Design

### AI-Driven Form Classification System

```python
def select_forms(case_facts):
    """
    AI-powered form selection based on case facts
    Returns list of required PDF forms to fill
    """
    
    # Primary case type classification
    case_type = classify_case_type(case_facts)
    required_forms = []
    
    # Base complaint form selection
    if case_type == "breach_of_contract":
        required_forms.append("pld001_contract.pdf")
    elif case_type in ["personal_injury", "property_damage", "wrongful_death"]:
        required_forms.append("pld001_injury-property-death.pdf")
    elif case_type == "intentional_tort":
        required_forms.append("pld001_intentional-tort.pdf")
    else:
        required_forms.append("pld001_complaint-general.pdf")  # General complaint
    
    # Add administrative forms based on circumstances
    if needs_fee_waiver(case_facts):
        required_forms.append("feewaiver_001.pdf")
        if complex_financial_situation(case_facts):
            required_forms.append("additionalfeewaiver_002.pdf")
    
    return required_forms

def classify_case_type(case_facts):
    """Use AI/NLP to classify the primary cause of action"""
    # Implementation will use prompt engineering or fine-tuned model
    pass

def needs_fee_waiver(case_facts):
    """Determine if plaintiff qualifies for fee waiver"""
    # Check income, assets, public benefits status
    pass
```

## PDF Form Field Analysis

Each PDF form contains fillable fields that need to be programmatically populated:

### Common Fields Across Forms:
- **Court Information**: County, judicial district, case number
- **Party Information**: Plaintiff name, defendant name, addresses
- **Attorney Information**: Name, bar number, address, phone
- **Case Caption**: Brief description of the case

### Form-Specific Fields:
- **Contract Forms**: Contract date, breach details, damages sought
- **PI/PD Forms**: Incident date, location, injury/damage description
- **Fee Waiver Forms**: Income, assets, household size, public benefits

## Technical Implementation Plan

### 1. PDF Form Reading and Field Extraction
```python
import PyPDF2
from pdfplumber import PDF
import fitz  # PyMuPDF

def extract_form_fields(pdf_path):
    """Extract all fillable fields from a PDF form"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        if reader.is_encrypted:
            reader.decrypt('')  # Handle basic encryption
        
        fields = {}
        for page in reader.pages:
            if '/Annots' in page:
                for annot in page['/Annots']:
                    field = annot.get_object()
                    if field.get('/FT') == '/Tx':  # Text field
                        field_name = field.get('/T')
                        field_value = field.get('/V', '')
                        fields[field_name] = field_value
        
        return fields
```

### 2. AI-Powered Field Mapping
```python
def map_case_facts_to_fields(case_facts, form_fields):
    """Use AI to intelligently map case facts to form fields"""
    
    prompt = f"""
    Given these case facts: {case_facts}
    And these form fields: {list(form_fields.keys())}
    
    Create a mapping of case facts to appropriate form fields.
    Return as JSON with field_name: value pairs.
    
    Guidelines:
    - Use proper legal formatting
    - Include all required fields
    - Format dates as MM/DD/YYYY
    - Use full legal names
    - Include proper addresses with ZIP codes
    """
    
    # Call to AI service (OpenAI, Claude, etc.)
    return ai_response_to_mapping(prompt)
```

### 3. PDF Form Filling Engine
```python
from reportlab.pdfgen import canvas
from PyPDF2 import PdfWriter, PdfReader

def fill_pdf_form(template_path, field_data, output_path):
    """Fill PDF form fields with provided data"""
    
    reader = PdfReader(template_path)
    writer = PdfWriter()
    
    for page_num, page in enumerate(reader.pages):
        # Update form fields
        if '/Annots' in page:
            writer.update_page_form_field_values(
                writer.add_page(page), 
                field_data
            )
        else:
            writer.add_page(page)
    
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
```

## Integration with Existing System

### Enhanced DocumentGenerator Class
```python
class EnhancedDocumentGenerator(DocumentGenerator):
    def __init__(self):
        super().__init__()
        self.form_selector = FormSelector()
        self.pdf_filler = PDFFormFiller()
        self.compliance_checker = ComplianceChecker()
    
    def generate_court_filing_packet(self, case_facts):
        """Main method to generate complete filing packet"""
        
        # 1. Select required forms
        required_forms = self.form_selector.select_forms(case_facts)
        
        # 2. Fill each form
        filled_forms = []
        for form_template in required_forms:
            filled_form = self.pdf_filler.fill_form(form_template, case_facts)
            filled_forms.append(filled_form)
        
        # 3. Generate complaint text
        complaint_text = self.generate_complaint(case_facts)
        
        # 4. Apply compliance formatting
        complaint_pdf = self.compliance_checker.format_complaint(complaint_text)
        
        # 5. Combine into final packet
        final_packet = self.combine_documents(filled_forms + [complaint_pdf])
        
        return final_packet
```

## Compliance Requirements Integration

### From FormatAndFilingRules.pdf:
- **Font**: Times New Roman, 12-point minimum
- **Margins**: 1-inch on all sides  
- **Line spacing**: Double-spaced
- **Page numbering**: Bottom center or top right
- **Line numbering**: Left margin, every 5th line
- **Paper**: 8.5" x 11", white

### Implementation:
```python
class ComplianceFormatter:
    def format_document(self, text_content):
        """Apply court formatting rules to document"""
        
        # Create PDF with proper formatting
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,  # 1 inch
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Apply court-compliant styling
        styles = getSampleStyleSheet()
        court_style = styles['Normal']
        court_style.fontName = 'Times-Roman'
        court_style.fontSize = 12
        court_style.leading = 24  # Double spacing
        
        # Add line numbering, page numbering, etc.
        return formatted_pdf
```

## Next Steps

1. **Implement PDF field extraction** for each form type
2. **Create form selection AI prompts** based on case classification
3. **Build PDF filling engine** with proper field mapping
4. **Integrate compliance formatting** according to court rules
5. **Test with Tesla case data** to validate the complete workflow

This system will provide the full AI-driven document generation capability requested, handling form selection, filling, complaint generation, and compliance formatting in an integrated workflow.