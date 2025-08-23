#!/bin/bash

# Restore ONLY Tesla files from trash to Tesla folder

echo "🔄 Starting Tesla file restoration process..."

# Create Tesla directory structure
mkdir -p Tesla/background
mkdir -p Tesla/test_cases/__pycache__
mkdir -p Tesla/Drafts/Statement\ of\ Facts
mkdir -p Tesla/Tweets\ \&\ Statements
mkdir -p Tesla/car\ data
mkdir -p Tesla/Main/Account\ Details
mkdir -p Tesla/Main/evidence
mkdir -p Tesla/Main/News\ Artcles\ \(Tesla\)
mkdir -p Tesla/Main/Tesla\ Case\ Law
mkdir -p Tesla/Main/Peer-Reviewed
mkdir -p Tesla/Main/All\ tesla\ comms

# Counter for restored files
restored_count=0
error_count=0

# Function to restore file
restore_file() {
    trash_file="$1"
    original_file="$2"

    if [[ -f "$trash_file" ]]; then
        mv "$trash_file" "$original_file"
        echo "✅ Restored: $original_file"
        ((restored_count++))
    else
        echo "⚠️  Not found: $trash_file"
        ((error_count++))
    fi
}

# Restore Tesla root files
restore_file "trash/LIBOPSCivil-273-CivilEfilingTipsForReducingRejectionsMAY2025.pdf" "Tesla/LIBOPSCivil-273-CivilEfilingTipsForReducingRejectionsMAY2025.pdf"
restore_file "trash/Court_Citing_guidelines.pdf" "Tesla/Court_Citing_guidelines.pdf"
restore_file "trash/California-2025-SB511-Amended.pdf" "Tesla/California-2025-SB511-Amended.pdf"
restore_file "trash/CourtFiling_Topsheet_Packet.pdf" "Tesla/CourtFiling_Topsheet_Packet.pdf"
restore_file "trash/Tesla_FSD_Master_Bibliography.csv" "Tesla/Tesla_FSD_Master_Bibliography.csv"

# Restore Tesla/background files
restore_file "trash/RegisteredAgent_Tesla.pdf" "Tesla/background/RegisteredAgent_Tesla.pdf"
restore_file "trash/Legal Search API – CourtListener.com.pdf" "Tesla/background/Legal Search API – CourtListener.com.pdf"
restore_file "trash/Level-of-Automation-052522-tag.pdf" "Tesla/background/Level-of-Automation-052522-tag.pdf"
restore_file "trash/Summons-100.pdf" "Tesla/background/Summons-100.pdf"
restore_file "trash/Tipstoavoidrejection.pdf" "Tesla/background/Tipstoavoidrejection.pdf"
restore_file "trash/CADMV-DisengagementStatsAV-2023.csv" "Tesla/background/CADMV-DisengagementStatsAV-2023.csv"
restore_file "trash/sc100_claimfordamages.pdf" "Tesla/background/sc100_claimfordamages.pdf"

# Restore Tesla/test_cases files
restore_file "trash/tesla_workflow_test.py" "Tesla/test_cases/tesla_workflow_test.py"
restore_file "trash/tesla_case_data.py" "Tesla/test_cases/tesla_case_data.py"
restore_file "trash/tesla_workflow_test.cpython-311-pytest-7.4.2.pyc" "Tesla/test_cases/__pycache__/tesla_workflow_test.cpython-311-pytest-7.4.2.pyc"
restore_file "trash/tesla_case_data.cpython-311.pyc" "Tesla/test_cases/__pycache__/tesla_case_data.cpython-311.pyc"

# Restore Tesla/Drafts files
restore_file "trash/Tesla's Pursuit of Level 4 \"Full Self-Driving\" (FSD) – 2022–2025 Evidence Table (1).docx" "Tesla/Drafts/Tesla's Pursuit of Level 4 \"Full Self-Driving\" (FSD) – 2022–2025 Evidence Table (1).docx"
restore_file "trash/Tesla's Self-Driving Tech_ Legal Battles, Regulatory Scrutiny, and Technical Insights.docx" "Tesla/Drafts/Tesla's Self-Driving Tech_ Legal Battles, Regulatory Scrutiny, and Technical Insights.docx"
restore_file "trash/Tesla's Self-Driving Tech_ Legal Battles, Regulatory Scrutiny, and Technical Insights.pdf" "Tesla/Drafts/Tesla's Self-Driving Tech_ Legal Battles, Regulatory Scrutiny, and Technical Insights.pdf"
restore_file "trash/TeslaTheStory.pdf" "Tesla/Drafts/TeslaTheStory.pdf"
restore_file "trash/Tesla_StatementOfFacts-Macropicture-WorkInProgress.docx" "Tesla/Drafts/Statement of Facts/Tesla_StatementOfFacts-Macropicture-WorkInProgress.docx"

# Restore Tesla/Tweets & Statements files
restore_file "trash/@elonmusk.png" "Tesla/Tweets & Statements/@elonmusk.png"
restore_file "trash/Twitter_MuskDataset.csv" "Tesla/Tweets & Statements/Twitter_MuskDataset.csv"
restore_file "trash/2021-extremelyconfidentinLevel5.png" "Tesla/Tweets & Statements/2021-extremelyconfidentinLevel5.png"
restore_file "trash/TSLAQ12024_EarningsCall.pdf" "Tesla/Tweets & Statements/TSLAQ12024_EarningsCall.pdf"
restore_file "trash/dataset_twitter-x-data-tweet-scraper-pay-per-result-cheapest_2025-08-03_16-26-47-758.csv" "Tesla/Tweets & Statements/dataset_twitter-x-data-tweet-scraper-pay-per-result-cheapest_2025-08-03_16-26-47-758.csv"

# Restore Tesla/car data files
restore_file "trash/tesladatalog042724short.csv" "Tesla/car data/tesladatalog042724short.csv"
restore_file "trash/2024-04-26_briefly.csv" "Tesla/car data/2024-04-26_briefly.csv"
restore_file "trash/3MonthPeriod_Safe Driving Score Data.csv" "Tesla/car data/3MonthPeriod_Safe Driving Score Data.csv"
restore_file "trash/TeslaCrashpics.png" "Tesla/car data/TeslaCrashpics.png"
restore_file "trash/2024-04-26 Tesla Impact Report.pdf" "Tesla/car data/2024-04-26 Tesla Impact Report.pdf"
restore_file "trash/Safety Score Data.csv" "Tesla/car data/Safety Score Data.csv"

# Restore Tesla/Main/Account Details files
restore_file "trash/Access Your Payment Details.pdf" "Tesla/Main/Account Details/Access Your Payment Details.pdf"
restore_file "trash/Warranties.csv" "Tesla/Main/Account Details/Warranties.csv"
restore_file "trash/Customer Support Activity.csv" "Tesla/Main/Account Details/Customer Support Activity.csv"
restore_file "trash/Orders.csv" "Tesla/Main/Account Details/Orders.csv"
restore_file "trash/Documents.csv" "Tesla/Main/Account Details/Documents.csv"
restore_file "trash/Vehicle Details.csv" "Tesla/Main/Account Details/Vehicle Details.csv"
restore_file "trash/Account Details.csv" "Tesla/Main/Account Details/Account Details.csv"

# Restore Tesla/Main/evidence files
restore_file "trash/Tesla-early-access-FSD-signinscreen.webp" "Tesla/Main/evidence/Tesla-early-access-FSD-signinscreen.webp"
restore_file "trash/Your Full Self-Driving (Supervised) Trial starts now!.png" "Tesla/Main/evidence/Your Full Self-Driving (Supervised) Trial starts now!.png"
restore_file "trash/Nov302024-SubmissionToTeslaLegal-NoticeofClaim7DaysBegins.jpg" "Tesla/Main/evidence/Nov302024-SubmissionToTeslaLegal-NoticeofClaim7DaysBegins.jpg"
restore_file "trash/NHTSAReportonTesla-042524.pdf" "Tesla/Main/evidence/NHTSAReportonTesla-042524.pdf"
restore_file "trash/TeslaInvoiceMay7th-Newkeydidntrrequestit.pdf" "Tesla/Main/evidence/TeslaInvoiceMay7th-Newkeydidntrrequestit.pdf"
restore_file "trash/PAsadena-Preliminary Estimate.pdf" "Tesla/Main/evidence/PAsadena-Preliminary Estimate.pdf"
restore_file "trash/ECF teslaamountowed.pdf" "Tesla/Main/evidence/ECF teslaamountowed.pdf"
restore_file "trash/STandingORder_NHTSA.pdf" "Tesla/Main/evidence/STandingORder_NHTSA.pdf"
restore_file "trash/Reback_NHTSAFiling.pdf" "Tesla/Main/evidence/Reback_NHTSAFiling.pdf"

echo ""
echo "📊 Tesla File Restoration Summary:"
echo "✅ Successfully restored: $restored_count Tesla files"
echo "❌ Errors: $error_count Tesla files"

if [[ $restored_count -gt 0 ]]; then
    echo ""
    echo "🎉 Tesla file restoration completed!"
    echo "📝 Tesla files are now back in the Tesla/ folder."
fi