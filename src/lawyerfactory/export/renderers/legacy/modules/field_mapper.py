"""
# Script Name: field_mapper.py
# Description: AI-Powered Field Mapping Module for LawyerFactory  This module maps case facts and data to specific PDF form fields using intelligent field name matching and contextual understanding.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Document Generation
#   - Group Tags: null
AI-Powered Field Mapping Module for LawyerFactory

This module maps case facts and data to specific PDF form fields using intelligent
field name matching and contextual understanding.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from .ai_case_classifier import CaseClassification, CaseType
from .pdf_handler import PDFFormField, PDFHandler


@dataclass
class FieldMapping:
    """Represents a mapping between case data and a form field."""

    field_name: str
    field_type: str
    mapped_value: Any
    confidence: float  # 0.0 to 1.0
    source_data: str  # Description of where the value came from
    transformation_applied: Optional[str] = None


@dataclass
class MappingResult:
    """Result of field mapping operation."""

    form_name: str
    mappings: List[FieldMapping]
    unmapped_fields: List[str]  # Fields that couldn't be mapped
    missing_data: List[str]  # Required data that's missing
    mapping_confidence: float  # Overall mapping confidence
    warnings: List[str]


class FieldMapper:
    """
    AI-powered field mapper that maps case data to PDF form fields.

    This class uses intelligent pattern matching, natural language processing,
    and contextual understanding to automatically populate court forms.
    """

    def __init__(self, forms_directory: str = "docs/Court_files"):
        """
        Initialize FieldMapper.

        Args:
            forms_directory: Path to directory containing PDF court forms
        """
        self.forms_directory = Path(forms_directory)
        self.pdf_handler = PDFHandler(forms_directory)
        self.logger = logging.getLogger(__name__)

        # Initialize field mapping patterns and rules
        self._initialize_mapping_patterns()

    def _initialize_mapping_patterns(self):
        """Initialize patterns for mapping case data to form fields."""

        # Standard field name patterns and their corresponding case data keys
        self.field_patterns = {
            # Plaintiff information
            "plaintiff": {
                "patterns": [
                    r"plaintiff.*name",
                    r"name.*plaintiff",
                    r"petitioner.*name",
                    r"name.*petitioner",
                    r"^plaintiff$",
                    r"^petitioner$",
                ],
                "data_key": "plaintiff_name",
                "transform": "name_format",
            },
            "plaintiff_address": {
                "patterns": [
                    r"plaintiff.*address",
                    r"address.*plaintiff",
                    r"petitioner.*address",
                    r"plaintiff.*street",
                    r"plaintiff.*city",
                    r"plaintiff.*state",
                    r"plaintiff.*zip",
                ],
                "data_key": "plaintiff_address",
                "transform": "address_format",
            },
            "plaintiff_phone": {
                "patterns": [
                    r"plaintiff.*phone",
                    r"phone.*plaintiff",
                    r"plaintiff.*telephone",
                    r"tel.*plaintiff",
                ],
                "data_key": "plaintiff_phone",
                "transform": "phone_format",
            },
            # Defendant information
            "defendant": {
                "patterns": [
                    r"defendant.*name",
                    r"name.*defendant",
                    r"respondent.*name",
                    r"name.*respondent",
                    r"^defendant$",
                    r"^respondent$",
                ],
                "data_key": "defendant_name",
                "transform": "name_format",
            },
            "defendant_address": {
                "patterns": [
                    r"defendant.*address",
                    r"address.*defendant",
                    r"respondent.*address",
                    r"defendant.*street",
                    r"defendant.*city",
                    r"defendant.*state",
                    r"defendant.*zip",
                ],
                "data_key": "defendant_address",
                "transform": "address_format",
            },
            # Case information
            "case_number": {
                "patterns": [
                    r"case.*number",
                    r"number.*case",
                    r"docket.*number",
                    r"^case.*no",
                    r"^docket",
                ],
                "data_key": "case_number",
                "transform": "case_number_format",
            },
            "court_name": {
                "patterns": [
                    r"court.*name",
                    r"name.*court",
                    r"^court$",
                    r"jurisdiction",
                ],
                "data_key": "court_name",
                "transform": "court_format",
            },
            "filing_date": {
                "patterns": [r"date.*filed", r"filing.*date", r"file.*date", r"^date$"],
                "data_key": "filing_date",
                "transform": "date_format",
            },
            # Incident/Contract information
            "incident_date": {
                "patterns": [
                    r"incident.*date",
                    r"date.*incident",
                    r"occurrence.*date",
                    r"date.*occurrence",
                    r"accident.*date",
                    r"date.*accident",
                ],
                "data_key": "incident_date",
                "transform": "date_format",
            },
            "contract_date": {
                "patterns": [
                    r"contract.*date",
                    r"date.*contract",
                    r"agreement.*date",
                    r"date.*agreement",
                ],
                "data_key": "contract_date",
                "transform": "date_format",
            },
            # Damage information
            "damages": {
                "patterns": [
                    r"damages.*amount",
                    r"amount.*damages",
                    r"monetary.*damages",
                    r"economic.*damages",
                    r"^damages$",
                    r"compensation",
                ],
                "data_key": "damages_amount",
                "transform": "currency_format",
            },
            "medical_expenses": {
                "patterns": [
                    r"medical.*expenses",
                    r"expenses.*medical",
                    r"medical.*costs",
                    r"costs.*medical",
                    r"hospital.*costs",
                ],
                "data_key": "medical_expenses",
                "transform": "currency_format",
            },
            # Description fields
            "facts": {
                "patterns": [
                    r"statement.*facts",
                    r"facts.*statement",
                    r"factual.*allegations",
                    r"allegations",
                    r"description.*incident",
                    r"incident.*description",
                    r"^facts$",
                    r"narrative",
                ],
                "data_key": "facts_narrative",
                "transform": "text_format",
            },
        }

        # Priority order for field matching
        self.field_priority = [
            "plaintiff",
            "defendant",
            "case_number",
            "court_name",
            "incident_date",
            "contract_date",
            "filing_date",
            "damages",
            "medical_expenses",
            "facts",
            "plaintiff_address",
            "defendant_address",
            "plaintiff_phone",
        ]

    def map_fields(
        self,
        form_name: str,
        case_data: Dict[str, Any],
        classification: CaseClassification,
    ) -> MappingResult:
        """
        Map case data to form fields for a specific form.

        Args:
            form_name: Name of the form to map fields for
            case_data: Dictionary containing case information
            classification: Case classification from CaseClassifier

        Returns:
            MappingResult with field mappings and metadata
        """

        # Get available forms and check if form exists
        available_forms = self.pdf_handler.get_available_forms()
        if form_name not in available_forms:
            return MappingResult(
                form_name=form_name,
                mappings=[],
                unmapped_fields=[],
                missing_data=[f"Form not found: {form_name}"],
                mapping_confidence=0.0,
                warnings=[f"Form {form_name} not available"],
            )

        # Extract form fields
        form_path = available_forms[form_name]
        try:
            form_fields = self.pdf_handler.extract_form_fields(form_path)
        except Exception as e:
            self.logger.error(f"Error extracting fields from {form_name}: {str(e)}")
            return MappingResult(
                form_name=form_name,
                mappings=[],
                unmapped_fields=[],
                missing_data=[f"Error reading form: {str(e)}"],
                mapping_confidence=0.0,
                warnings=[f"Could not read form fields from {form_name}"],
            )

        # Prepare enhanced case data with derived fields
        enhanced_case_data = self._enhance_case_data(case_data, classification)

        # Map each form field
        mappings = []
        unmapped_fields = []

        for field in form_fields:
            mapping = self._map_single_field(field, enhanced_case_data)
            if mapping:
                mappings.append(mapping)
            else:
                unmapped_fields.append(field.name)

        # Check for missing required data
        missing_data = self._identify_missing_data(
            enhanced_case_data, classification.primary_type
        )

        # Calculate overall confidence
        if mappings:
            mapping_confidence = sum(m.confidence for m in mappings) / len(mappings)
        else:
            mapping_confidence = 0.0

        # Generate warnings
        warnings = self._generate_mapping_warnings(
            mappings, unmapped_fields, missing_data
        )

        return MappingResult(
            form_name=form_name,
            mappings=mappings,
            unmapped_fields=unmapped_fields,
            missing_data=missing_data,
            mapping_confidence=mapping_confidence,
            warnings=warnings,
        )

    def _enhance_case_data(
        self, case_data: Dict[str, Any], classification: CaseClassification
    ) -> Dict[str, Any]:
        """Enhance case data with derived and default values."""

        enhanced = case_data.copy()

        # Add current date if filing date not provided
        if "filing_date" not in enhanced:
            enhanced["filing_date"] = datetime.now()

        # Add default court information
        if "court_name" not in enhanced:
            enhanced["court_name"] = "SUPERIOR COURT OF CALIFORNIA"

        # Extract facts narrative from facts list if needed
        if "facts_narrative" not in enhanced and "facts" in enhanced:
            if isinstance(enhanced["facts"], list):
                facts_texts = [
                    fact.get("text", "")
                    for fact in enhanced["facts"]
                    if isinstance(fact, dict)
                ]
                enhanced["facts_narrative"] = ". ".join(facts_texts)
            elif isinstance(enhanced["facts"], str):
                enhanced["facts_narrative"] = enhanced["facts"]

        # Generate case number if not provided
        if "case_number" not in enhanced:
            enhanced["case_number"] = "TO BE ASSIGNED"

        # Ensure names are properly formatted
        for key in ["plaintiff_name", "defendant_name"]:
            if key in enhanced and isinstance(enhanced[key], dict):
                # If name is stored as dict with first/last name
                name_dict = enhanced[key]
                if "first" in name_dict and "last" in name_dict:
                    enhanced[key] = f"{name_dict['first']} {name_dict['last']}"

        return enhanced

    def _map_single_field(
        self, field: PDFFormField, case_data: Dict[str, Any]
    ) -> Optional[FieldMapping]:
        """Map a single form field to case data."""

        field_name_lower = field.name.lower()

        # Try to match field against known patterns
        for pattern_name in self.field_priority:
            pattern_info = self.field_patterns[pattern_name]

            for pattern in pattern_info["patterns"]:
                if re.search(pattern, field_name_lower, re.IGNORECASE):
                    data_key = pattern_info["data_key"]

                    if data_key in case_data:
                        raw_value = case_data[data_key]

                        # Apply transformation
                        transform_func = pattern_info.get("transform")
                        if transform_func:
                            transformed_value, transform_desc = (
                                self._apply_transformation(
                                    raw_value, transform_func, field.field_type
                                )
                            )
                        else:
                            transformed_value = str(raw_value)
                            transform_desc = None

                        # Calculate confidence based on pattern match quality
                        confidence = self._calculate_mapping_confidence(
                            field.name, pattern, pattern_name
                        )

                        return FieldMapping(
                            field_name=field.name,
                            field_type=field.field_type,
                            mapped_value=transformed_value,
                            confidence=confidence,
                            source_data=f"case_data['{data_key}']",
                            transformation_applied=transform_desc,
                        )

        # Try fuzzy matching for unmapped fields
        fuzzy_mapping = self._fuzzy_field_match(field, case_data)
        if fuzzy_mapping:
            return fuzzy_mapping

        return None

    def _apply_transformation(
        self, value: Any, transform_name: str, field_type: str
    ) -> Tuple[str, Optional[str]]:
        """Apply data transformation to prepare value for form field."""

        if transform_name == "name_format":
            if isinstance(value, str):
                return value.strip().title(), "title case formatting"
            return str(value), "string conversion"

        elif transform_name == "address_format":
            if isinstance(value, dict):
                # Format address from components
                parts = []
                for key in ["street", "city", "state", "zip"]:
                    if key in value and value[key]:
                        parts.append(str(value[key]))
                return ", ".join(parts), "address component assembly"
            return str(value), "string conversion"

        elif transform_name == "phone_format":
            phone_str = re.sub(r"[^\d]", "", str(value))
            if len(phone_str) == 10:
                return (
                    f"({phone_str[:3]}) {phone_str[3:6]}-{phone_str[6:]}",
                    "phone number formatting",
                )
            return str(value), "string conversion"

        elif transform_name == "date_format":
            if isinstance(value, datetime):
                return value.strftime("%m/%d/%Y"), "date formatting"
            elif isinstance(value, str):
                # Try to parse and reformat date
                try:
                    parsed = datetime.strptime(value, "%Y-%m-%d")
                    return parsed.strftime("%m/%d/%Y"), "date parsing and formatting"
                except ValueError:
                    return value, "date string passthrough"
            return str(value), "string conversion"

        elif transform_name == "currency_format":
            try:
                amount = float(str(value).replace("$", "").replace(",", ""))
                return f"${amount:,.2f}", "currency formatting"
            except (ValueError, TypeError):
                return str(value), "string conversion"

        elif transform_name == "case_number_format":
            return str(value).upper(), "uppercase formatting"

        elif transform_name == "court_format":
            return str(value).upper(), "uppercase formatting"

        elif transform_name == "text_format":
            # Handle text fields - ensure proper length and formatting
            text = str(value)
            if field_type == "text" and len(text) > 500:
                return text[:497] + "...", "text truncation"
            return text, "text formatting"

        else:
            return str(value), "default string conversion"

    def _calculate_mapping_confidence(
        self, field_name: str, pattern: str, pattern_name: str
    ) -> float:
        """Calculate confidence score for a field mapping."""

        # Base confidence starts high for exact pattern matches
        confidence = 0.8

        # Boost confidence for high-priority fields
        priority_boost = {
            "plaintiff": 0.2,
            "defendant": 0.2,
            "case_number": 0.15,
            "court_name": 0.1,
            "incident_date": 0.1,
        }
        confidence += priority_boost.get(pattern_name, 0.0)

        # Boost confidence for exact field name matches
        if field_name.lower() == pattern_name:
            confidence += 0.1

        # Reduce confidence for very generic patterns
        if pattern in [r"^date$", r"^court$", r"^damages$"]:
            confidence -= 0.1

        return min(confidence, 1.0)

    def _handle_generic_field_names(
        self, field: PDFFormField, case_data: Dict[str, Any]
    ) -> Optional[FieldMapping]:
        """Handle generic field names like FillText42 by mapping them in order."""

        # Extract field number from generic names
        field_name = field.name

        # Check if this is a generic field name pattern
        text_match = re.match(r"FillText(\d+)", field_name)
        checkbox_match = re.match(r"CheckBox(\d+)", field_name)

        if text_match:
            field_number = int(text_match.group(1))
        elif checkbox_match:
            field_number = int(checkbox_match.group(1))
        else:
            return None

            # Create a simple mapping strategy for generic fields
            # This is a basic approach - in production, you'd want form-specific mappings
            basic_fields = [
                ("plaintiff_name", "name_format"),
                ("defendant_name", "name_format"),
                ("court_name", "court_format"),
                ("case_number", "case_number_format"),
                ("incident_date", "date_format"),
                ("contract_date", "date_format"),
                ("filing_date", "date_format"),
                ("damages_amount", "currency_format"),
                ("medical_expenses", "currency_format"),
                ("facts_narrative", "text_format"),
            ]

            # Map fields in order of priority
            if field_number <= len(basic_fields):
                field_index = field_number - 1
                if field_index < len(basic_fields):
                    data_key, transform_func = basic_fields[field_index]

                    if data_key in case_data:
                        raw_value = case_data[data_key]

                        if transform_func:
                            transformed_value, transform_desc = (
                                self._apply_transformation(
                                    raw_value, transform_func, field.field_type
                                )
                            )
                        else:
                            transformed_value = str(raw_value)
                            transform_desc = None

                        return FieldMapping(
                            field_name=field.name,
                            field_type=field.field_type,
                            mapped_value=transformed_value,
                            confidence=0.7,  # Medium confidence for generic mapping
                            source_data=f"case_data['{data_key}'] (generic field mapping)",
                            transformation_applied=transform_desc,
                        )

        return None

    def _fuzzy_field_match(
        self, field: PDFFormField, case_data: Dict[str, Any]
    ) -> Optional[FieldMapping]:
        """Attempt fuzzy matching for unmapped fields."""

        field_name_lower = field.name.lower()

        # Look for partial matches in case data keys
        for data_key, data_value in case_data.items():
            data_key_lower = data_key.lower()

            # Check for substring matches
            if data_key_lower in field_name_lower or field_name_lower in data_key_lower:

                confidence = 0.6  # Lower confidence for fuzzy matches

                return FieldMapping(
                    field_name=field.name,
                    field_type=field.field_type,
                    mapped_value=str(data_value),
                    confidence=confidence,
                    source_data=f"case_data['{data_key}'] (fuzzy match)",
                    transformation_applied="string conversion",
                )

        return None

    def _identify_missing_data(
        self, case_data: Dict[str, Any], case_type: CaseType
    ) -> List[str]:
        """Identify missing data that should be collected for the case type."""

        required_fields = {
            CaseType.BREACH_OF_CONTRACT: [
                "plaintiff_name",
                "defendant_name",
                "contract_date",
                "damages_amount",
            ],
            CaseType.PERSONAL_INJURY: [
                "plaintiff_name",
                "defendant_name",
                "incident_date",
                "medical_expenses",
            ],
            CaseType.NEGLIGENCE: ["plaintiff_name", "defendant_name", "incident_date"],
            CaseType.PRODUCT_LIABILITY: [
                "plaintiff_name",
                "defendant_name",
                "incident_date",
                "product_description",
            ],
        }

        missing = []
        required = required_fields.get(case_type, ["plaintiff_name", "defendant_name"])

        for field in required:
            if field not in case_data or not case_data[field]:
                missing.append(field)

        return missing

    def _generate_mapping_warnings(
        self,
        mappings: List[FieldMapping],
        unmapped_fields: List[str],
        missing_data: List[str],
    ) -> List[str]:
        """Generate warnings about the mapping process."""

        warnings = []

        # Low confidence mappings
        low_confidence = [m for m in mappings if m.confidence < 0.7]
        if low_confidence:
            warnings.append(f"{len(low_confidence)} field mappings have low confidence")

        # Many unmapped fields
        if len(unmapped_fields) > 5:
            warnings.append(f"{len(unmapped_fields)} form fields could not be mapped")

        # Missing critical data
        if missing_data:
            warnings.append(f"Missing required data: {', '.join(missing_data)}")

        # No mappings at all
        if not mappings:
            warnings.append(
                "No form fields could be mapped - check case data completeness"
            )

        return warnings

    def get_mapping_summary(self, result: MappingResult) -> Dict[str, Any]:
        """Get a summary of the mapping result for review."""

        return {
            "form_name": result.form_name,
            "total_mappings": len(result.mappings),
            "high_confidence_mappings": len(
                [m for m in result.mappings if m.confidence >= 0.8]
            ),
            "medium_confidence_mappings": len(
                [m for m in result.mappings if 0.6 <= m.confidence < 0.8]
            ),
            "low_confidence_mappings": len(
                [m for m in result.mappings if m.confidence < 0.6]
            ),
            "unmapped_fields": len(result.unmapped_fields),
            "missing_data_items": len(result.missing_data),
            "overall_confidence": result.mapping_confidence,
            "has_warnings": len(result.warnings) > 0,
            "ready_for_filling": result.mapping_confidence > 0.7
            and len(result.missing_data) == 0,
        }


def test_field_mapper():
    """Test function for FieldMapper functionality."""

    from .ai_case_classifier import CaseClassification, CaseType

    mapper = FieldMapper()

    # Test case data
    test_case_data = {
        "plaintiff_name": "John Doe",
        "defendant_name": "Tesla Motors, Inc.",
        "contract_date": "2024-01-15",
        "incident_date": "2024-03-01",
        "damages_amount": 50000,
        "medical_expenses": 15000,
        "facts": [
            {"text": "Tesla failed to deliver vehicle on agreed date"},
            {"text": "Customer suffered financial losses due to breach"},
        ],
        "court_name": "Superior Court of California, County of San Francisco",
    }

    # Test classification
    test_classification = CaseClassification(
        primary_type=CaseType.BREACH_OF_CONTRACT,
        confidence=0.85,
        secondary_types=[],
        reasoning="Contract breach case",
        key_indicators=["contract", "breach"],
        damages_categories=["economic"],
        urgency_level="medium",
    )

    print("Testing Field Mapper:")
    print("=" * 50)

    # Test with contract form
    result = mapper.map_fields("pld001_contract", test_case_data, test_classification)

    print(f"Form: {result.form_name}")
    print(f"Mappings: {len(result.mappings)}")
    print(f"Overall Confidence: {result.mapping_confidence:.1%}")

    if result.mappings:
        print("\nField Mappings:")
        for mapping in result.mappings[:5]:  # Show first 5 mappings
            print(f"  {mapping.field_name}: {mapping.mapped_value}")
            print(
                f"    Confidence: {mapping.confidence:.1%}, Source: {mapping.source_data}"
            )

    if result.unmapped_fields:
        print(f"\nUnmapped Fields: {len(result.unmapped_fields)}")
        print(f"  Examples: {result.unmapped_fields[:3]}")

    if result.missing_data:
        print(f"\nMissing Data: {result.missing_data}")

    if result.warnings:
        print(f"\nWarnings: {result.warnings}")

    # Show summary
    summary = mapper.get_mapping_summary(result)
    print("\nSummary:")
    print(f"  Ready for filling: {summary['ready_for_filling']}")
    print(f"  High confidence mappings: {summary['high_confidence_mappings']}")
    print(f"  Total unmapped: {summary['unmapped_fields']}")


if __name__ == "__main__":
    # Enable logging for testing
    logging.basicConfig(level=logging.INFO)
    test_field_mapper()
