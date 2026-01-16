"""
# Script Name: legal_intake_form.py
# Description: Legal Intake Form Component for LawyerFactory.  A yellow legal pad-style intake form that collects essential case information before proceeding with legal research and document generation. This form appears as a popup/modal and gathers critical jurisdictional and case details.
# Relationships:
#   - Entity Type: UI Component
#   - Directory Group: Frontend
#   - Group Tags: user-interface
Legal Intake Form Component for LawyerFactory.

A yellow legal pad-style intake form that collects essential case information
before proceeding with legal research and document generation. This form
appears as a popup/modal and gathers critical jurisdictional and case details.
"""

from dataclasses import dataclass, field
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IntakeFormData:
    """Data collected from the legal intake form"""

    first_name: str = ""
    last_name: str = ""
    user_name: str = ""  # Keep for backward compatibility, will be derived
    user_address: str = ""
    other_party_name: str = ""
    other_party_address: str = ""
    party_role: str = ""  # plaintiff or defendant
    event_location: str = ""
    event_date: str = ""
    agreement_type: str = ""  # written, oral, none
    evidence_upload: bool = False
    witnesses: bool = False
    rough_draft: bool = False
    claim_description: str = ""
    selected_causes: List[str] = field(default_factory=list)
    jurisdiction: str = ""
    venue: str = ""
    case_type: str = ""
    amount_in_controversy: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "user_name": self.user_name or f"{self.first_name} {self.last_name}".strip(),
            "user_address": self.user_address,
            "other_party_name": self.other_party_name,
            "other_party_address": self.other_party_address,
            "party_role": self.party_role,
            "event_location": self.event_location,
            "event_date": self.event_date,
            "agreement_type": self.agreement_type,
            "evidence_upload": self.evidence_upload,
            "witnesses": self.witnesses,
            "rough_draft": self.rough_draft,
            "claim_description": self.claim_description,
            "selected_causes": self.selected_causes,
            "jurisdiction": self.jurisdiction,
            "venue": self.venue,
            "case_type": self.case_type,
            "amount_in_controversy": self.amount_in_controversy,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntakeFormData":
        """Create from dictionary"""
        return cls(**data)

    def is_complete(self) -> bool:
        """Check if all required fields are filled"""
        required_fields = [
            self.first_name,
            self.last_name,
            self.other_party_name,
            self.party_role,
            self.event_location,
            self.claim_description,
        ]
        return all(required_fields) and len(self.selected_causes) > 0


class LegalIntakeForm:
    """Main controller for the legal intake form"""

    def __init__(self):
        self.form_data = IntakeFormData()
        self.common_causes = [
            "Breach of Contract",
            "Negligence",
            "Products Liability",
            "Motor Vehicle Accident",
            "Landlord/Tenant Dispute",
            "Property Damage",
            "Fraud/Misrepresentation",
            "Intentional Tort",
            "Employment Dispute",
            "Consumer Protection",
            "Professional Malpractice",
            "Construction Defect",
            "Insurance Bad Faith",
            "Civil Rights Violation",
            "Other",
        ]

    def extract_last_name(self, full_name: str) -> str:
        """Extract the last name from a full name string for case naming."""
        if not full_name:
            return "Unknown"
        parts = full_name.strip().split()
        return parts[-1] if parts else "Unknown"

    def get_html_template(self) -> str:
        """Generate the HTML template for the intake form"""
        return f"""
        <div id="intake-form-overlay" class="intake-overlay" style="display: none;">
            <div class="intake-form-container">
                <div class="legal-pad-header">
                    <div class="pad-spiral"></div>
                    <h2 class="pad-title">LEGAL INTAKE FORM</h2>
                    <button class="close-button" onclick="closeIntakeForm()">×</button>
                </div>

                <div class="legal-pad-content">
                    <form id="intake-form" class="yellow-legal-pad">

                        <!-- Personal Information -->
                        <div class="form-section">
                            <h3>📋 Client Information</h3>
                            <div class="form-row name-row">
                                <div class="name-field">
                                    <label for="first_name">First Name:</label>
                                    <input type="text" id="first_name" name="first_name" class="pad-input" required>
                                </div>
                                <div class="name-field">
                                    <label for="last_name">Last Name:</label>
                                    <input type="text" id="last_name" name="last_name" class="pad-input" required>
                                </div>
                            </div>
                            <div class="form-row">
                                <label for="user_address">Your Address:</label>
                                <textarea id="user_address" name="user_address" class="pad-textarea" rows="2"></textarea>
                            </div>
                        </div>

                        <!-- Other Party Information -->
                        <div class="form-section">
                            <h3>⚖️ Other Party Information</h3>
                            <div class="form-row">
                                <label for="other_party_name">Other Party Name:</label>
                                <input type="text" id="other_party_name" name="other_party_name" class="pad-input" required>
                            </div>
                            <div class="form-row">
                                <label for="other_party_address">Other Party Address (if known):</label>
                                <textarea id="other_party_address" name="other_party_address" class="pad-textarea" rows="2"></textarea>
                            </div>
                            <div class="form-row">
                                <label for="party_role">Are you the:</label>
                                <select id="party_role" name="party_role" class="pad-select" required>
                                    <option value="">Select...</option>
                                    <option value="plaintiff">Plaintiff (Suing)</option>
                                    <option value="defendant">Defendant (Being Sued)</option>
                                </select>
                            </div>
                        </div>

                        <!-- Case Details -->
                        <div class="form-section">
                            <h3>📍 Case Details</h3>
                            <div class="form-row">
                                <label for="event_location">Where did most events occur?</label>
                                <input type="text" id="event_location" name="event_location" class="pad-input"
                                       placeholder="City, State" required>
                            </div>
                            <div class="form-row">
                                <label for="event_date">When did most events occur?</label>
                                <input type="text" id="event_date" name="event_date" class="pad-input"
                                       placeholder="Approximate date or date range">
                            </div>
                            <div class="form-row">
                                <label for="agreement_type">Was there a written or oral agreement?</label>
                                <select id="agreement_type" name="agreement_type" class="pad-select">
                                    <option value="">Select...</option>
                                    <option value="written">Written Agreement</option>
                                    <option value="oral">Oral Agreement</option>
                                    <option value="none">No Agreement</option>
                                </select>
                            </div>
                        </div>

                        <!-- Evidence and Preparation -->
                        <div class="form-section">
                            <h3>📚 Evidence & Preparation</h3>
                            <div class="checkbox-row">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="evidence_upload" name="evidence_upload">
                                    <span class="checkmark"></span>
                                    Do you plan to upload evidence?
                                </label>
                            </div>
                            <div class="checkbox-row">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="witnesses" name="witnesses">
                                    <span class="checkmark"></span>
                                    Do you have witnesses?
                                </label>
                            </div>
                            <div class="checkbox-row">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="rough_draft" name="rough_draft">
                                    <span class="checkmark"></span>
                                    Do you have a rough draft started?
                                </label>
                            </div>
                        </div>

                        <!-- Claim Description -->
                        <div class="form-section">
                            <h3>💰 Claim Description</h3>
                            <div class="form-row">
                                <label for="claim_description">Why does the other party owe you? (Be specific)</label>
                                <textarea id="claim_description" name="claim_description" class="pad-textarea large"
                                          rows="4" placeholder="Describe what happened and why you're entitled to relief..." required></textarea>
                            </div>
                        </div>

                        <!-- Cause of Action Selection -->
                        <div class="form-section">
                            <h3>⚖️ Potential Causes of Action</h3>
                            <p class="form-instruction">Select all that may apply to your case:</p>
                            <div class="causes-grid">
                                {self._generate_causes_checkboxes()}
                            </div>
                        </div>

                        <!-- Form Actions -->
                        <div class="form-actions">
                            <button type="button" class="pad-button secondary" onclick="closeIntakeForm()">Cancel</button>
                            <button type="submit" class="pad-button primary">Submit Intake Form</button>
                        </div>

                    </form>
                </div>

                <!-- Legal Pad Styling -->
                <div class="pad-lines"></div>
            </div>
        </div>
        """

    def _generate_causes_checkboxes(self) -> str:
        """Generate HTML checkboxes for common causes of action"""
        checkboxes = []
        for cause in self.common_causes:
            safe_id = cause.lower().replace(" ", "_").replace("/", "_")
            checkboxes.append(
                f"""
                <div class="cause-checkbox">
                    <label class="checkbox-label">
                        <input type="checkbox" name="causes" value="{cause}" id="cause_{safe_id}">
                        <span class="checkmark"></span>
                        {cause}
                    </label>
                </div>
            """
            )
        return "\n".join(checkboxes)

    def get_css_styles(self) -> str:
        """Generate CSS styles for the intake form"""
        return """
        <style>
        /* Intake Form Overlay */
        .intake-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* Legal Pad Container */
        .intake-form-container {
            background: #feffdb;
            width: 90%;
            max-width: 800px;
            max-height: 90vh;
            overflow-y: auto;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            position: relative;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: scale(0.9) translateY(-20px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }

        /* Legal Pad Header */
        .legal-pad-header {
            background: linear-gradient(145deg, #f5f5dc, #feffdb);
            padding: 20px;
            border-bottom: 2px solid #888;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
        }

        .pad-spiral {
            width: 20px;
            height: 100px;
            background: #666;
            border-radius: 10px;
            position: absolute;
            left: 10px;
            top: 20px;
            opacity: 0.3;
        }

        .pad-title {
            color: #1a1a1a;
            margin: 0;
            font-family: 'kievit', 'Times New Roman', serif;
            font-weight: bold;
            font-size: 1.5em;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
        }

        .close-button {
            background: none;
            border: none;
            font-size: 2em;
            cursor: pointer;
            color: #333;
            padding: 0;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: all 0.2s ease;
        }

        .close-button:hover {
            background: rgba(0, 0, 0, 0.2);
            color: #000;
        }

        /* Legal Pad Content */
        .legal-pad-content {
            padding: 30px;
            position: relative;
        }

        .yellow-legal-pad {
            background: repeating-linear-gradient(
                to bottom,
                transparent,
                transparent 76px,
                rgba(0, 0, 0, 0.25) 76px,
                rgba(0, 0, 0, 0.25) 77px
            );
            line-height: 1.8;
        }

        /* Form Sections */
        .form-section {
            margin-bottom: 30px;
            position: relative;
        }

        .form-section h3 {
            color: #1a1a1a;
            margin-bottom: 15px;
            font-family: 'strelka', 'Arial Black', sans-serif;
            font-weight: 800;
            font-size: 1.2em;
            border-bottom: 2px solid rgba(0, 0, 0, 0.4);
            padding-bottom: 8px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }

        .form-row {
            margin-bottom: 15px;
        }

        .form-row label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #1a1a1a;
            font-family: 'proxima-nova', 'Arial', sans-serif;
            font-size: 0.95em;
            text-shadow: 0.5px 0.5px 1px rgba(0, 0, 0, 0.15);
        }

        /* Form Inputs */
        .pad-input, .pad-select, .pad-textarea {
            width: 100%;
            padding: 10px 14px;
            border: 2px solid #666;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.95);
            font-family: 'kievit', 'Times New Roman', serif;
            font-size: 15px;
            line-height: 1.4;
            box-sizing: border-box;
            color: #1a1a1a;
            font-weight: 500;
        }

        .pad-input:focus, .pad-select:focus, .pad-textarea:focus {
            outline: none;
            border-color: #333;
            box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
            background: rgba(255, 255, 255, 1);
        }

        .pad-textarea {
            resize: vertical;
            min-height: 60px;
        }

        .pad-textarea.large {
            min-height: 100px;
        }

        .pad-select {
            cursor: pointer;
        }

        /* Checkboxes */
        .checkbox-row {
            margin-bottom: 10px;
        }

        .checkbox-label {
            display: flex;
            align-items: center;
            cursor: pointer;
            font-family: 'proxima-nova', 'Arial', sans-serif;
            font-weight: 600;
            color: #1a1a1a;
            text-shadow: 0.5px 0.5px 1px rgba(0, 0, 0, 0.1);
        }

        .checkbox-label input[type="checkbox"] {
            margin-right: 10px;
            transform: scale(1.2);
        }

        .checkmark {
            margin-left: 8px;
            width: 16px;
            height: 16px;
            border: 2px solid #333;
            border-radius: 2px;
            background: rgba(255, 255, 255, 0.95);
            display: inline-block;
        }

        /* Causes of Action Grid */
        .causes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }

        .cause-checkbox {
            background: rgba(255, 255, 255, 0.8);
            border: 2px solid #666;
            border-radius: 4px;
            padding: 12px;
        }

        .cause-checkbox:hover {
            background: rgba(255, 255, 255, 0.95);
            border-color: #333;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        }

        /* Form Actions */
        .form-actions {
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #ccc;
        }

        .pad-button {
            padding: 14px 28px;
            border: 2px solid #333;
            border-radius: 4px;
            background: linear-gradient(145deg, #fff, #f0f0f0);
            color: #1a1a1a;
            font-family: 'strelka', 'Arial Black', sans-serif;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.2s ease;
            text-shadow: 0.5px 0.5px 1px rgba(0, 0, 0, 0.1);
        }

        .pad-button:hover {
            background: linear-gradient(145deg, #f0f0f0, #e0e0e0);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        .pad-button.primary {
            background: linear-gradient(145deg, #4CAF50, #45a049);
            color: white;
            border-color: #4CAF50;
        }

        .pad-button.secondary {
            background: linear-gradient(145deg, #f44336, #da190b);
            color: white;
            border-color: #f44336;
        }

        /* Legal Pad Lines */
        .pad-lines {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: repeating-linear-gradient(
                to bottom,
                transparent,
                transparent 76px,
                rgba(0, 0, 0, 0.15) 76px,
                rgba(0, 0, 0, 0.15) 77px
            );
            pointer-events: none;
            z-index: 1;
        }

        .legal-pad-content {
            position: relative;
            z-index: 2;
        }

        /* Name Row Styling */
        .name-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        .name-field {
            display: flex;
            flex-direction: column;
        }

        /* Form Instructions */
        .form-instruction {
            font-style: italic;
            color: #333;
            margin-bottom: 15px;
            font-family: 'kievit', 'Times New Roman', serif;
            font-weight: 400;
            text-shadow: 0.5px 0.5px 1px rgba(0, 0, 0, 0.1);
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .intake-form-container {
                width: 95%;
                max-height: 95vh;
            }

            .name-row {
                grid-template-columns: 1fr;
                gap: 10px;
            }

            .causes-grid {
                grid-template-columns: 1fr;
            }

            .form-actions {
                flex-direction: column;
                gap: 10px;
            }
        }
        </style>
        """

    def get_javascript(self) -> str:
        """Generate JavaScript for form functionality"""
        return """
        <script>
        function showIntakeForm() {
            document.getElementById('intake-form-overlay').style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }

        function closeIntakeForm() {
            document.getElementById('intake-form-overlay').style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        function submitIntakeForm(event) {
            event.preventDefault();

            const formData = new FormData(event.target);
            const intakeData = {
                first_name: formData.get('first_name'),
                last_name: formData.get('last_name'),
                user_name: `${formData.get('first_name')} ${formData.get('last_name')}`.trim(),
                user_address: formData.get('user_address'),
                other_party_name: formData.get('other_party_name'),
                other_party_address: formData.get('other_party_address'),
                party_role: formData.get('party_role'),
                event_location: formData.get('event_location'),
                event_date: formData.get('event_date'),
                agreement_type: formData.get('agreement_type'),
                evidence_upload: formData.has('evidence_upload'),
                witnesses: formData.has('witnesses'),
                rough_draft: formData.has('rough_draft'),
                claim_description: formData.get('claim_description'),
                selected_causes: formData.getAll('causes')
            };

            // Validate required fields
            if (!intakeData.first_name || !intakeData.last_name || !intakeData.other_party_name ||
                !intakeData.party_role || !intakeData.event_location ||
                !intakeData.claim_description || intakeData.selected_causes.length === 0) {
                alert('Please fill in all required fields and select at least one cause of action.');
                return;
            }

            // Send data to backend
            fetch('/api/intake', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(intakeData)
            })
            .then(response => response.json())
            .then(data => {
                console.log('Intake form submitted:', data);
                closeIntakeForm();

                // Notify AI Maestro
                if (window.orchestrationDashboard) {
                    window.orchestrationDashboard.addChatMessage(
                        'AI Maestro',
                        'Thank you for completing the intake form! I now have the essential case information needed to proceed with legal research and document preparation.',
                        'ai'
                    );
                }
            })
            .catch(error => {
                console.error('Error submitting intake form:', error);
                alert('Error submitting form. Please try again.');
            });
        }

        // Initialize form when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('intake-form');
            if (form) {
                form.addEventListener('submit', submitIntakeForm);
            }

            // Auto-show form if no intake data exists
            if (!localStorage.getItem('intake_completed')) {
                setTimeout(showIntakeForm, 1000);
            }
        });
        </script>
        """

    def process_intake_data(self, intake_data: Dict[str, Any]) -> IntakeFormData:
        """Process submitted intake form data"""
        # Ensure user_name is derived from first_name and last_name if not provided
        if "first_name" in intake_data and "last_name" in intake_data:
            intake_data["user_name"] = f"{intake_data['first_name']} {intake_data['last_name']}".strip()
        
        form_data = IntakeFormData.from_dict(intake_data)

        # Determine jurisdiction and venue based on location
        if form_data.event_location:
            location_parts = form_data.event_location.split(", ")
            if len(location_parts) >= 2:
                state = location_parts[-1].strip()
                form_data.jurisdiction = f"State of {state}"
                form_data.venue = f"{location_parts[0].strip()}, {state}"

        # Determine case type based on selected causes
        if form_data.selected_causes:
            if any("contract" in cause.lower() for cause in form_data.selected_causes):
                form_data.case_type = "contract_dispute"
            elif any(
                "negligence" in cause.lower() for cause in form_data.selected_causes
            ):
                form_data.case_type = "tort_claim"
            elif any("product" in cause.lower() for cause in form_data.selected_causes):
                form_data.case_type = "products_liability"
            else:
                form_data.case_type = "general_civil"

        # Estimate amount in controversy (placeholder logic)
        if "breach of contract" in [c.lower() for c in form_data.selected_causes]:
            form_data.amount_in_controversy = (
                75000  # Minimum for diversity jurisdiction
            )
        elif any("tort" in c.lower() for c in form_data.selected_causes):
            form_data.amount_in_controversy = 50000
        else:
            form_data.amount_in_controversy = 25000

        logger.info(
            f"Processed intake data for {form_data.user_name} vs {form_data.other_party_name}"
        )
        return form_data

    def get_intake_summary(self, form_data: IntakeFormData) -> str:
        """Generate a summary of the intake data for the AI Maestro"""
        client_name = f"{form_data.first_name} {form_data.last_name}".strip() or form_data.user_name
        summary = f"""
**INTAKE FORM SUMMARY**

**Client:** {client_name}
**Address:** {form_data.user_address or 'Not provided'}

**Other Party:** {form_data.other_party_name}
**Address:** {form_data.other_party_address or 'Not provided'}
**Role:** {'Plaintiff' if form_data.party_role == 'plaintiff' else 'Defendant'}

**Case Details:**
- Location: {form_data.event_location}
- Date: {form_data.event_date or 'Not specified'}
- Agreement: {form_data.agreement_type or 'Not specified'}

**Evidence & Witnesses:**
- Evidence Upload: {'Yes' if form_data.evidence_upload else 'No'}
- Witnesses: {'Yes' if form_data.witnesses else 'No'}
- Rough Draft: {'Yes' if form_data.rough_draft else 'No'}

**Claim Description:** {form_data.claim_description[:200]}...

**Selected Causes of Action:** {', '.join(form_data.selected_causes)}

**Jurisdictional Analysis:**
- Jurisdiction: {form_data.jurisdiction}
- Venue: {form_data.venue}
- Case Type: {form_data.case_type}
- Amount in Controversy: ${form_data.amount_in_controversy:,.2f}

This information will guide the legal research and document preparation process.
        """
        return summary


# Global instance
intake_form = LegalIntakeForm()
