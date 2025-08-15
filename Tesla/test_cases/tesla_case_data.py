"""
Tesla Case Test Data for AI Document Generator

This module contains comprehensive test cases based on the Tesla documents
and background materials provided, designed to test the AI document generation system.
"""

from datetime import datetime, date
from typing import Dict, List, Any

# Tesla Case Data - Comprehensive test case
TESLA_CONTRACT_BREACH_CASE = {
    # Basic Case Information
    'case_name': 'Tesla Vehicle Delivery Breach of Contract',
    'case_number': 'CV-2024-001234',
    'filing_date': '2024-04-15',
    'court_name': 'Superior Court of California, County of San Francisco',
    'court_address': '400 McAllister Street, San Francisco, CA 94102',
    
    # Party Information
    'plaintiff_name': 'John David Smith',
    'plaintiff_address': '123 Main Street, San Francisco, CA 94102',
    'plaintiff_phone': '(415) 555-0123',
    'plaintiff_email': 'jsmith@email.com',
    'plaintiff_attorney': 'Sarah Johnson, Esq.',
    'plaintiff_attorney_bar': '12345',
    'plaintiff_attorney_firm': 'Johnson Legal Group',
    'plaintiff_attorney_address': '456 Legal Lane, San Francisco, CA 94102',
    'plaintiff_attorney_phone': '(415) 555-0456',
    'plaintiff_attorney_email': 'sjohnson@johnsonlegal.com',
    
    'defendant_name': 'Tesla Motors, Inc.',
    'defendant_address': '1 Tesla Road, Austin, TX 78725',
    'defendant_type': 'corporation',
    
    # Contract Details
    'contract_date': '2023-12-15',
    'contract_type': 'Vehicle Purchase Agreement',
    'contract_number': 'TESLA-2023-VPA-5678',
    'agreed_delivery_date': '2024-02-15',
    'actual_delivery_date': None,  # Never delivered
    'vehicle_model': 'Tesla Model S Plaid',
    'vehicle_vin': 'Expected: 5YJ3E1EA1PF123456',
    'purchase_price': 129990.00,
    'deposit_paid': 25000.00,
    
    # Incident Details
    'incident_date': '2024-02-16',  # Day after promised delivery
    'breach_description': 'Tesla failed to deliver vehicle by agreed contract date',
    'notice_of_breach_date': '2024-02-20',
    'cure_period_end': '2024-03-01',
    
    # Damages
    'damages_amount': 75000.00,
    'actual_damages': 45000.00,
    'consequential_damages': 20000.00,
    'incidental_damages': 5000.00,
    'punitive_damages': 5000.00,
    'attorney_fees_requested': True,
    'costs_and_expenses': 2500.00,
    
    # Medical/Personal Impact (if applicable)
    'medical_expenses': 0.00,
    'lost_wages': 15000.00,
    'emotional_distress': True,
    
    # Case Facts - Detailed narrative
    'facts': [
        {
            'date': '2023-12-15',
            'text': 'Plaintiff entered into a written Vehicle Purchase Agreement with Defendant Tesla Motors, Inc. for the purchase of a Tesla Model S Plaid vehicle for $129,990.'
        },
        {
            'date': '2023-12-15', 
            'text': 'The contract explicitly stated delivery would occur no later than February 15, 2024, with time being of the essence.'
        },
        {
            'date': '2023-12-20',
            'text': 'Plaintiff paid a deposit of $25,000 and arranged financing for the remaining balance as required by the contract.'
        },
        {
            'date': '2024-01-15',
            'text': 'Plaintiff contacted Tesla to confirm delivery schedule and was assured the February 15th delivery date would be met.'
        },
        {
            'date': '2024-02-10',
            'text': 'Five days before delivery, Tesla contacted Plaintiff stating there would be an indefinite delay due to "production issues."'
        },
        {
            'date': '2024-02-15',
            'text': 'Tesla failed to deliver the vehicle on the agreed contract date, constituting a material breach of contract.'
        },
        {
            'date': '2024-02-16',
            'text': 'Plaintiff suffered immediate financial losses as existing vehicle lease expired and required emergency rental car arrangements.'
        },
        {
            'date': '2024-02-20',
            'text': 'Plaintiff provided written notice of breach to Tesla and demanded cure within 10 days.'
        },
        {
            'date': '2024-03-01',
            'text': 'Tesla failed to cure the breach within the specified cure period.'
        },
        {
            'date': '2024-03-15',
            'text': 'Plaintiff demanded return of deposit and compensation for damages. Tesla refused and offered only partial refund.'
        },
        {
            'date': '2024-04-01',
            'text': 'Tesla continues to refuse full performance and has indicated vehicle delivery may not occur until late 2024.'
        }
    ],
    
    # Legal Theories/Causes of Action
    'causes_of_action': [
        'breach_of_contract',
        'breach_of_warranty',
        'unfair_business_practices'
    ],
    
    # Supporting Evidence
    'evidence': [
        'Written Vehicle Purchase Agreement',
        'Email confirmations of delivery date',
        'Payment records and bank statements',
        'Notice of Breach correspondence',
        'Tesla\'s written acknowledgment of delay',
        'Rental car receipts and expenses',
        'Lost wage documentation',
        'Witness statements from Tesla employees'
    ],
    
    # Settlement Attempts
    'settlement_attempts': [
        {
            'date': '2024-03-10',
            'description': 'Informal negotiation via phone',
            'result': 'Tesla offered 50% deposit refund, rejected by Plaintiff'
        },
        {
            'date': '2024-03-25', 
            'description': 'Written settlement demand',
            'result': 'Tesla failed to respond within 30 days'
        }
    ],
    
    # Jurisdictional Information
    'jurisdiction_basis': [
        'Defendant conducts substantial business in California',
        'Contract was to be performed in California',
        'Plaintiff is a California resident',
        'Damages occurred in California'
    ],
    
    # Case Classification Hints for AI
    'case_type_indicators': [
        'written contract exists',
        'clear breach of delivery terms', 
        'material breach with substantial damages',
        'commercial transaction',
        'time was of the essence clause',
        'defendant failed to cure after notice'
    ],
    
    # Filing Requirements
    'fee_waiver_requested': False,
    'financial_hardship': False,
    'expedited_processing': False,
    'jury_trial_demanded': True,
    
    # Case Complexity
    'complexity_level': 'medium',
    'estimated_trial_length': '3-5 days',
    'discovery_needed': True,
    'expert_witnesses_needed': False,
    
    # Priority/Urgency
    'urgency_level': 'medium',
    'statute_of_limitations': '2028-12-15',  # 4 years from contract date
    'time_sensitive_issues': ['Ongoing financial losses', 'Mitigation of damages']
}

# Additional test cases for different scenarios
TESLA_PERSONAL_INJURY_CASE = {
    'case_name': 'Tesla Autopilot Malfunction Personal Injury',
    'case_number': 'CV-2024-002345',
    'plaintiff_name': 'Maria Rodriguez',
    'defendant_name': 'Tesla, Inc.',
    'incident_date': '2024-01-20',
    'incident_location': 'Highway 101, San Francisco, CA',
    'vehicle_model': 'Tesla Model 3',
    'autopilot_engaged': True,
    'injuries': ['Whiplash', 'Concussion', 'Broken ribs'],
    'medical_expenses': 125000.00,
    'lost_wages': 45000.00,
    'pain_and_suffering': 300000.00,
    'facts': [
        {'text': 'Tesla vehicle autopilot system failed to detect stopped vehicle'},
        {'text': 'Collision occurred at 45 mph causing severe injuries'},
        {'text': 'Tesla had knowledge of similar autopilot defects'}
    ],
    'causes_of_action': ['negligence', 'products_liability', 'strict_liability'],
    'urgency_level': 'high'
}

TESLA_LEMON_LAW_CASE = {
    'case_name': 'Tesla Model Y Lemon Law Violation',
    'case_number': 'CV-2024-003456', 
    'plaintiff_name': 'Robert Chen',
    'defendant_name': 'Tesla Motors, Inc.',
    'vehicle_model': 'Tesla Model Y',
    'purchase_date': '2023-08-15',
    'defects': ['Battery charging failure', 'Door handle malfunction', 'Software glitches'],
    'repair_attempts': 4,
    'days_out_of_service': 45,
    'purchase_price': 67990.00,
    'facts': [
        {'text': 'Vehicle suffered recurring defects affecting safety and use'},
        {'text': 'Tesla made four unsuccessful repair attempts'},
        {'text': 'Vehicle was out of service for 45+ days in first year'}
    ],
    'causes_of_action': ['lemon_law_violation', 'breach_of_warranty'],
    'relief_sought': 'Vehicle replacement or full refund'
}

# Test case validation data
TEST_CASE_VALIDATIONS = {
    'required_fields': [
        'plaintiff_name', 'defendant_name', 'facts', 'damages_amount',
        'incident_date', 'court_name', 'causes_of_action'
    ],
    'expected_case_types': {
        'TESLA_CONTRACT_BREACH_CASE': 'breach_of_contract',
        'TESLA_PERSONAL_INJURY_CASE': 'personal_injury', 
        'TESLA_LEMON_LAW_CASE': 'breach_of_warranty'
    },
    'expected_forms': {
        'breach_of_contract': ['pld001_contract', 'civil_cover_sheet'],
        'personal_injury': ['pld001_injury', 'civil_cover_sheet'],
        'breach_of_warranty': ['pld001_contract', 'civil_cover_sheet']
    }
}

def get_test_case(case_name: str) -> Dict[str, Any]:
    """Get a specific test case by name."""
    cases = {
        'contract_breach': TESLA_CONTRACT_BREACH_CASE,
        'personal_injury': TESLA_PERSONAL_INJURY_CASE,
        'lemon_law': TESLA_LEMON_LAW_CASE
    }
    return cases.get(case_name, TESLA_CONTRACT_BREACH_CASE)

def validate_case_data(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate case data completeness and structure."""
    
    required = TEST_CASE_VALIDATIONS['required_fields']
    missing = [field for field in required if field not in case_data]
    
    validation_result = {
        'valid': len(missing) == 0,
        'missing_fields': missing,
        'completeness_score': (len(required) - len(missing)) / len(required),
        'field_count': len(case_data),
        'has_facts': bool(case_data.get('facts')),
        'facts_count': len(case_data.get('facts', [])),
        'has_damages': bool(case_data.get('damages_amount')),
        'structured_properly': all(
            key in case_data for key in ['plaintiff_name', 'defendant_name', 'facts']
        )
    }
    
    return validation_result

if __name__ == "__main__":
    # Test the case data
    print("Tesla Case Test Data Validation:")
    print("=" * 50)
    
    for case_name in ['contract_breach', 'personal_injury', 'lemon_law']:
        case_data = get_test_case(case_name)
        validation = validate_case_data(case_data)
        
        print(f"\n{case_name.upper()}: ")
        print(f"  Valid: {validation['valid']}")
        print(f"  Completeness: {validation['completeness_score']:.1%}")
        print(f"  Facts count: {validation['facts_count']}")
        print(f"  Plaintiff: {case_data['plaintiff_name']}")
        print(f"  Defendant: {case_data['defendant_name']}")
        
        if validation['missing_fields']:
            print(f"  Missing: {validation['missing_fields']}")