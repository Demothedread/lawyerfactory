"""
# Script Name: intake_processor.py
# Description: LawyerFactory Intake Processor  Handles processing of case intake form data, including: - Data validation and storage - Jurisdiction and venue determination - Case name and description generation - Integration with downstream systems
# Relationships:
#   - Entity Type: Engine
#   - Directory Group: Workflow
#   - Group Tags: null
LawyerFactory Intake Processor

Handles processing of case intake form data, including:
- Data validation and storage
- Jurisdiction and venue determination
- Case name and description generation
- Integration with downstream systems
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


class PartyType(Enum):
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"


class AgreementType(Enum):
    WRITTEN = "written"
    ORAL = "oral"
    IMPLIED = "implied"
    NONE = "none"


class CourtType(Enum):
    STATE = "state"
    FEDERAL = "federal"


class CauseOfAction(Enum):
    MOTOR_VEHICLE = "motor_vehicle"
    LANDLORD_TENANT = "landlord_tenant"
    PRODUCTS_LIABILITY = "products_liability"
    PROPERTY_DAMAGE = "property_damage"
    BREACH_CONTRACT = "breach_contract"
    NEGLIGENCE = "negligence"
    FRAUD = "fraud"
    EMPLOYMENT = "employment"
    CIVIL_RIGHTS = "civil_rights"
    OTHER = "other"


@dataclass
class IntakeData:
    """Structured intake form data"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Client Information
    client_name: str = ""
    client_address: str = ""
    client_phone: str = ""
    client_email: str = ""

    # Opposing Party Information
    opposing_party_names: str = ""
    opposing_party_address: str = ""

    # Case Classification
    party_type: str = ""
    claim_amount: float = 0.0

    # Location & Timing
    events_location: str = ""
    events_date: str = ""

    # Agreement Information
    agreement_type: str = ""
    has_evidence: str = ""
    has_witnesses: str = ""

    # Case Status
    has_draft: str = ""

    # Cause of Action
    claim_description: str = ""
    causes_of_action: List[str] = field(default_factory=list)
    other_cause: str = ""

    # Generated fields
    case_name: str = ""
    case_description: str = ""
    jurisdiction: str = ""
    venue: str = ""
    court_type: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "client_name": self.client_name,
            "client_address": self.client_address,
            "client_phone": self.client_phone,
            "client_email": self.client_email,
            "opposing_party_names": self.opposing_party_names,
            "opposing_party_address": self.opposing_party_address,
            "party_type": self.party_type,
            "claim_amount": self.claim_amount,
            "events_location": self.events_location,
            "events_date": self.events_date,
            "agreement_type": self.agreement_type,
            "has_evidence": self.has_evidence,
            "has_witnesses": self.has_witnesses,
            "has_draft": self.has_draft,
            "claim_description": self.claim_description,
            "causes_of_action": self.causes_of_action,
            "other_cause": self.other_cause,
            "case_name": self.case_name,
            "case_description": self.case_description,
            "jurisdiction": self.jurisdiction,
            "venue": self.venue,
            "court_type": self.court_type,
            "created_at": self.created_at
        }


class IntakeProcessor:
    """Processes intake form data and generates case information"""

    def __init__(self, storage_path: str = "data/intake_sessions"):
        self.storage_path = storage_path
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        import os
        os.makedirs(self.storage_path, exist_ok=True)

    def process_intake_form(self, form_data: Dict[str, Any]) -> IntakeData:
        """
        Process intake form data and generate case information

        Args:
            form_data: Raw form data from intake form

        Returns:
            Processed IntakeData object with generated fields
        """
        logger.info("Processing intake form data")

        # Create intake data object
        intake_data = IntakeData()

        # Map form data to intake data
        self._map_form_data(intake_data, form_data)

        # Generate case information
        intake_data.case_name = self._generate_case_name(intake_data)
        intake_data.case_description = self._generate_case_description(intake_data)
        intake_data.jurisdiction = self._determine_jurisdiction(intake_data)
        intake_data.venue = self._determine_venue(intake_data)
        intake_data.court_type = self._determine_court_type(intake_data)

        # Store processed data
        self._store_intake_data(intake_data)

        logger.info(f"Processed intake data for session {intake_data.session_id}")
        return intake_data

    def _map_form_data(self, intake_data: IntakeData, form_data: Dict[str, Any]):
        """Map form data to intake data object"""
        # Direct mappings
        intake_data.client_name = form_data.get("client_name", "")
        intake_data.client_address = form_data.get("client_address", "")
        intake_data.client_phone = form_data.get("client_phone", "")
        intake_data.client_email = form_data.get("client_email", "")
        intake_data.opposing_party_names = form_data.get("opposing_party_names", "")
        intake_data.opposing_party_address = form_data.get("opposing_party_address", "")
        intake_data.party_type = form_data.get("party_type", "")
        intake_data.events_location = form_data.get("events_location", "")
        intake_data.events_date = form_data.get("events_date", "")
        intake_data.agreement_type = form_data.get("agreement_type", "")
        intake_data.has_evidence = form_data.get("has_evidence", "")
        intake_data.has_witnesses = form_data.get("has_witnesses", "")
        intake_data.has_draft = form_data.get("has_draft", "")
        intake_data.claim_description = form_data.get("claim_description", "")
        intake_data.other_cause = form_data.get("other_cause", "")

        # Handle claim amount
        try:
            intake_data.claim_amount = float(form_data.get("claim_amount", 0))
        except (ValueError, TypeError):
            intake_data.claim_amount = 0.0

        # Handle causes of action (can be single value or list)
        causes = form_data.get("causes_of_action", [])
        if isinstance(causes, str):
            intake_data.causes_of_action = [causes]
        elif isinstance(causes, list):
            intake_data.causes_of_action = causes
        else:
            intake_data.causes_of_action = []

    def _generate_case_name(self, intake_data: IntakeData) -> str:
        """Generate case name from intake data"""
        plaintiff = intake_data.client_name or "Plaintiff"
        defendant = intake_data.opposing_party_names or "Defendant"

        if intake_data.party_type == "plaintiff":
            case_name = f"{plaintiff} v. {defendant}"
        else:
            case_name =  "in re {defendant}"

        return case_name

    def _generate_case_description(self, intake_data: IntakeData) -> str:
        """Generate case description from intake data"""
        party_type_desc = "Plaintiff" if intake_data.party_type == "plaintiff" else "Defendant"
        location = intake_data.events_location or "Unknown Location"
        date = intake_data.events_date or "Unknown Date"

        # Get primary cause of action
        primary_cause = ""
        if intake_data.causes_of_action:
            cause_map = {
                against_person={
                "motor_vehicle": "Motor Vehicle Accident",
                "landlord_tenant": "Landlord-Tenant Dispute",
                "products_liability": "Products Liability",
                "property_damage": "Property Damage",
                "breach_contract": "Breach of Contract",
                "negligence": "Negligence",
                "fraud": "Fraud/Misrepresentation",
                "employment": "Employment Dispute",
                "civil_rights": "Civil Rights Violation",
                "discrimination": "Discrimination",
                "breach_warranty": "Breach of Implied Warranty of Fitness for a Particular Purpose",
                "respondeat_superior": "Respondeat Superior",
                ""
                "other": intake_data.other_cause or "Other Cause"
                },
                against_property={
                    "motor_vehicle": "Motor Vehicle Accident",
                    "landlord_tenant": "Landlord-Tenant Dispute",
                    "products_liability": "Products Liability",
                    "property_damage": "Property Damage",
                    "breach_contract": "Breach of Contract",
                    "negligence": "Negligence",
                    "fraud": "Fraud/Misrepresentation",
                    "employment": "Employment Dispute",
                    "civil_rights": "Civil Rights Violation",
                    "discrimination": "Discrimination",
                    "breach_warranty": "Breach of Implied Warranty of Fitness for a Particular Purpose",
                    "respondeat_superior": "Respondeat Superior",
                    "other": intake_data.other_cause or "Other Cause"
                }
            }
            primary_cause = cause_map.get(intake_data.causes_of_action[0], "Civil Matter")

        description = f"{party_type_desc} brings this action arising from events occurring in {location} during {date}."

        if primary_cause:
            description += f" The case involves {primary_cause.lower()}."

        if intake_data.claim_amount > 0:
            description += f" The claim seeks ${intake_data.claim_amount:,.2f} in damages."

        return description

    def _determine_jurisdiction(self, intake_data: IntakeData) -> str:
        """Determine the appropriate jurisdiction based on intake data"""
        # Extract state from location
        location = intake_data.events_location
        if location:
            # Simple state extraction - in practice, you'd want more sophisticated parsing
            words = location.split(",")
            if len(words) >= 2:
                state = words[-1].strip()
                return f"State of {state}"
            else:
                # Try to extract from full address
                location_lower = location.lower()
                if "california" in location_lower:
                    return "State of California"
                elif "new york" in location_lower:
                    return "State of New York"
                elif "texas" in location_lower:
                    return "State of Texas"
                elif "florida" in location_lower:
                    return "State of Florida"

        return "State of [To Be Determined]"

    def _determine_venue(self, intake_data: IntakeData) -> str:
        """Determine the appropriate venue based on intake data"""
        location = intake_data.events_location
        if location:
            # Extract city/county for venue
            words = location.split(",")
            if len(words) >= 2:
                city = words[0].strip()
                return f"{city} County Superior Court"

        return "County Superior Court [To Be Determined]"

    def _determine_court_type(self, intake_data: IntakeData) -> str:
        """Determine whether case should be in state or federal court"""
        # Federal court criteria:
        # 1. Complete diversity of citizenship AND amount > $75k
        # 2. Federal question (e.g., civil rights, constitutional issues)

        claim_amount = intake_data.claim_amount

        # Check for federal question
        if "civil_rights" in intake_data.causes_of_action:
            return CourtType.FEDERAL.value

        # Check diversity and amount requirements
        if claim_amount > 75000:
            return CourtType.FEDERAL.value

        # Check for removal threshold
        if claim_amount > 12500:
            return f"{CourtType.STATE.value} (removable to federal)"

        return CourtType.STATE.value

    def _store_intake_data(self, intake_data: IntakeData):
        """Store intake data to file"""
        import os

        filename = f"{intake_data.session_id}.json"
        filepath = os.path.join(self.storage_path, filename)

        with open(filepath, 'w') as f:
            json.dump(intake_data.to_dict(), f, indent=2)

        logger.info(f"Stored intake data to {filepath}")

    def get_intake_data(self, session_id: str) -> Optional[IntakeData]:
        """Retrieve intake data by session ID"""
        import os

        filename = f"{session_id}.json"
        filepath = os.path.join(self.storage_path, filename)

        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)

        intake_data = IntakeData()
        for key, value in data.items():
            if hasattr(intake_data, key):
                setattr(intake_data, key, value)

        return intake_data

    def get_facts_matrix_from_intake(self, intake_data: IntakeData) -> Dict[str, Any]:
        """Convert intake data to facts matrix format for downstream processing"""
        return {
            "undisputed_facts": [
                f"The case involves {intake_data.client_name} as {'plaintiff' if intake_data.party_type == 'plaintiff' else 'defendant'}.",
                f"The events occurred in {intake_data.events_location} during {intake_data.events_date}.",
                f"The claim description states: {intake_data.claim_description}"
            ],
            "disputed_facts": [
                # These would be filled in by the user or legal analysis
            ],
            "procedural_facts": [
                f"Case filed in {intake_data.jurisdiction}",
                f"Venue is {intake_data.venue}",
                f"Court type: {intake_data.court_type}"
            ],
            "case_metadata": {
                "case_name": intake_data.case_name,
                "case_description": intake_data.case_description,
                "jurisdiction": intake_data.jurisdiction,
                "venue": intake_data.venue,
                "court_type": intake_data.court_type,
                "client_name": intake_data.client_name,
                "client_address": intake_data.client_address,
                "opposing_party_names": intake_data.opposing_party_names,
                "claim_amount": intake_data.claim_amount,
                "causes_of_action": intake_data.causes_of_action,
                "session_id": intake_data.session_id
            },
            "evidence_references": {
                "has_evidence": intake_data.has_evidence,
                "has_witnesses": intake_data.has_witnesses,
                "has_draft": intake_data.has_draft
            },
            "key_events": [
                {
                    "date": intake_data.events_date,
                    "description": f"Primary events occurred in {intake_data.events_location}",
                    "location": intake_data.events_location
                }
            ],
            "background_context": [
                f"Agreement type: {intake_data.agreement_type}",
                f"Client contact: {intake_data.client_phone} / {intake_data.client_email}"
            ],
            "damages_claims": [
                {
                    "amount": intake_data.claim_amount,
                    "description": intake_data.claim_description,
                    "type": "general_damages"
                }
            ] if intake_data.claim_amount > 0 else []
        }