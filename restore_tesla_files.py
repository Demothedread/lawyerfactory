#!/usr/bin/env python3
"""
Restore ONLY Tesla files from trash directory to Tesla folder.
Based on the staging manifest and deduplication report.
"""

import os
import shutil
from pathlib import Path

def restore_tesla_files():
    """Restore ONLY Tesla files to their original locations."""

    # Define ONLY Tesla file restore mapping
    tesla_restore_mapping = {
        # Tesla root files
        'trash/LIBOPSCivil-273-CivilEfilingTipsForReducingRejectionsMAY2025.pdf': 'Tesla/LIBOPSCivil-273-CivilEfilingTipsForReducingRejectionsMAY2025.pdf',
        'trash/Court_Citing_guidelines.pdf': 'Tesla/Court_Citing_guidelines.pdf',
        'trash/.DS_Store.dup.20250822051739': 'Tesla/.DS_Store',
        'trash/California-2025-SB511-Amended.pdf': 'Tesla/California-2025-SB511-Amended.pdf',
        'trash/CourtFiling_Topsheet_Packet.pdf': 'Tesla/CourtFiling_Topsheet_Packet.pdf',
        'trash/Tesla_FSD_Master_Bibliography.csv': 'Tesla/Tesla_FSD_Master_Bibliography.csv',

        # Tesla/background files
        'trash/RegisteredAgent_Tesla.pdf': 'Tesla/background/RegisteredAgent_Tesla.pdf',
        'trash/Legal Search API – CourtListener.com.pdf': 'Tesla/background/Legal Search API – CourtListener.com.pdf',
        'trash/Level-of-Automation-052522-tag.pdf': 'Tesla/background/Level-of-Automation-052522-tag.pdf',
        'trash/Summons-100.pdf': 'Tesla/background/Summons-100.pdf',
        'trash/Tipstoavoidrejection.pdf': 'Tesla/background/Tipstoavoidrejection.pdf',
        'trash/CADMV-DisengagementStatsAV-2023.csv': 'Tesla/background/CADMV-DisengagementStatsAV-2023.csv',
        'trash/sc100_claimfordamages.pdf': 'Tesla/background/sc100_claimfordamages.pdf',

        # Tesla/test_cases files
        'trash/tesla_workflow_test.py': 'Tesla/test_cases/tesla_workflow_test.py',
        'trash/tesla_case_data.py': 'Tesla/test_cases/tesla_case_data.py',
        'trash/tesla_workflow_test.cpython-311-pytest-7.4.2.pyc': 'Tesla/test_cases/__pycache__/tesla_workflow_test.cpython-311-pytest-7.4.2.pyc',
        'trash/tesla_case_data.cpython-311.pyc': 'Tesla/test_cases/__pycache__/tesla_case_data.cpython-311.pyc',

        # Tesla/Drafts files
        'trash/Tesla\'s Pursuit of Level 4 "Full Self-Driving" (FSD) – 2022–2025 Evidence Table (1).docx': 'Tesla/Drafts/Tesla\'s Pursuit of Level 4 "Full Self-Driving" (FSD) – 2022–2025 Evidence Table (1).docx',
        'trash/Tesla\'s Self-Driving Tech_ Legal Battles, Regulatory Scrutiny, and Technical Insights.docx': 'Tesla/Drafts/Tesla\'s Self-Driving Tech_ Legal Battles, Regulatory Scrutiny, and Technical Insights.docx',
        'trash/Tesla\'s Self-Driving Tech_ Legal Battles, Regulatory Scrutiny, and Technical Insights.pdf': 'Tesla/Drafts/Tesla\'s Self-Driving Tech_ Legal Battles, Regulatory Scrutiny, and Technical Insights.pdf',
        'trash/TeslaTheStory.pdf': 'Tesla/Drafts/TeslaTheStory.pdf',
        'trash/Tesla_StatementOfFacts-Macropicture-WorkInProgress.docx': 'Tesla/Drafts/Statement of Facts/Tesla_StatementOfFacts-Macropicture-WorkInProgress.docx',

        # Tesla/Tweets & Statements files
        'trash/@elonmusk.png': 'Tesla/Tweets & Statements/@elonmusk.png',
        'trash/Twitter_MuskDataset.csv': 'Tesla/Tweets & Statements/Twitter_MuskDataset.csv',
        'trash/2021-extremelyconfidentinLevel5.png': 'Tesla/Tweets & Statements/2021-extremelyconfidentinLevel5.png',
        'trash/TSLAQ12024_EarningsCall.pdf': 'Tesla/Tweets & Statements/TSLAQ12024_EarningsCall.pdf',
        'trash/dataset_twitter-x-data-tweet-scraper-pay-per-result-cheapest_2025-08-03_16-26-47-758.csv': 'Tesla/Tweets & Statements/dataset_twitter-x-data-tweet-scraper-pay-per-result-cheapest_2025-08-03_16-26-47-758.csv',

        # Tesla/car data files
        'trash/tesladatalog042724short.csv': 'Tesla/car data/tesladatalog042724short.csv',
        'trash/2024-04-26_briefly.csv': 'Tesla/car data/2024-04-26_briefly.csv',
        'trash/3MonthPeriod_Safe Driving Score Data.csv': 'Tesla/car data/3MonthPeriod_Safe Driving Score Data.csv',
        'trash/TeslaCrashpics.png': 'Tesla/car data/TeslaCrashpics.png',
        'trash/2024-04-26 Tesla Impact Report.pdf': 'Tesla/car data/2024-04-26 Tesla Impact Report.pdf',
        'trash/Safety Score Data.csv': 'Tesla/car data/Safety Score Data.csv',

        # Tesla/Main files
        'trash/Access Your Payment Details.pdf': 'Tesla/Main/Account Details/Access Your Payment Details.pdf',
        'trash/Warranties.csv': 'Tesla/Main/Account Details/Warranties.csv',
        'trash/Customer Support Activity.csv': 'Tesla/Main/Account Details/Customer Support Activity.csv',
        'trash/Orders.csv': 'Tesla/Main/Account Details/Orders.csv',
        'trash/Documents.csv': 'Tesla/Main/Account Details/Documents.csv',
        'trash/Vehicle Details.csv': 'Tesla/Main/Account Details/Vehicle Details.csv',
        'trash/Account Details.csv': 'Tesla/Main/Account Details/Account Details.csv',

        # Tesla/Main/evidence files
        'trash/Tesla-early-access-FSD-signinscreen.webp': 'Tesla/Main/evidence/Tesla-early-access-FSD-signinscreen.webp',
        'trash/Your Full Self-Driving (Supervised) Trial starts now!.png': 'Tesla/Main/evidence/Your Full Self-Driving (Supervised) Trial starts now!.png',
        'trash/Nov302024-SubmissionToTeslaLegal-NoticeofClaim7DaysBegins.jpg': 'Tesla/Main/evidence/Nov302024-SubmissionToTeslaLegal-NoticeofClaim7DaysBegins.jpg',
        'trash/NHTSAReportonTesla-042524.pdf': 'Tesla/Main/evidence/NHTSAReportonTesla-042524.pdf',
        'trash/TeslaInvoiceMay7th-Newkeydidntrrequestit.pdf': 'Tesla/Main/evidence/TeslaInvoiceMay7th-Newkeydidntrrequestit.pdf',
        'trash/PAsadena-Preliminary Estimate.pdf': 'Tesla/Main/evidence/PAsadena-Preliminary Estimate.pdf',
        'trash/ECF teslaamountowed.pdf': 'Tesla/Main/evidence/ECF teslaamountowed.pdf',
        'trash/STandingORder_NHTSA.pdf': 'Tesla/Main/evidence/STandingORder_NHTSA.pdf',
        'trash/Reback_NHTSAFiling.pdf': 'Tesla/Main/evidence/Reback_NHTSAFiling.pdf',

        # Tesla/Main/News Articles files
        'trash/Tesla Under Another Federal Investigation for Fraud Related to Self-Driving Claims.pdf': 'Tesla/Main/News Artcles (Tesla)/Tesla Under Another Federal Investigation for Fraud Related to Self-Driving Claims.pdf',
        'trash/-61225-Rogue\' Tesla demonstration shows dangers to Texas roads.pdf': 'Tesla/Main/News Artcles (Tesla)/-61225-Rogue\' Tesla demonstration shows dangers to Texas roads.pdf',
        'trash/May82024-NewsArticle-TeslaInvestsInLidar.pdf': 'Tesla/Main/News Artcles (Tesla)/May82024-NewsArticle-TeslaInvestsInLidar.pdf',
        'trash/Inside the WSJ Tesla Autopilot Crash Investigation_ How We Analyzed Hundreds of Incidents - WSJ.pdf': 'Tesla/Main/News Artcles (Tesla)/Inside the WSJ Tesla Autopilot Crash Investigation_ How We Analyzed Hundreds of Incidents - WSJ.pdf',
        'trash/newsArt_Tesla13FatalAccidentsCausebyFSD_042624.pdf': 'Tesla/Main/News Artcles (Tesla)/newsArt_Tesla13FatalAccidentsCausebyFSD_042624.pdf',
        'trash/May2024-NewsArticle-LiDarPricesToBeHalvedby2025-Hesai.pdf': 'Tesla/Main/News Artcles (Tesla)/May2024-NewsArticle-LiDarPricesToBeHalvedby2025-Hesai.pdf',
        'trash/Report_april152024-10PercentLaidOff.pdf': 'Tesla/Main/News Artcles (Tesla)/Report_april152024-10PercentLaidOff.pdf',
        'trash/100624-U.S. to probe Tesla\'s \'Full Self-Driving\' system after pedestrian killed _ NPR.pdf': 'Tesla/Main/News Artcles (Tesla)/100624-U.S. to probe Tesla\'s \'Full Self-Driving\' system after pedestrian killed _ NPR.pdf',
        'trash/Wapo-Tesla Autopilot crashes and recall raise questions about federal oversight - The Washington Post-062024.pdf': 'Tesla/Main/News Artcles (Tesla)/Wapo-Tesla Autopilot crashes and recall raise questions about federal oversight - The Washington Post-062024.pdf',
        'trash/TheVerge_Tesla_SelfDrivingIssue.png': 'Tesla/Main/News Artcles (Tesla)/TheVerge_Tesla_SelfDrivingIssue.png',
        'trash/Wapo-Tesla employee in fiery crash may be first \'Full Self-Driving\' death-102023.pdf': 'Tesla/Main/News Artcles (Tesla)/Wapo-Tesla employee in fiery crash may be first \'Full Self-Driving\' death-102023.pdf',
        'trash/NewsArt_Nytimes_AutopilotRenewedScrutiny.pdf': 'Tesla/Main/News Artcles (Tesla)/NewsArt_Nytimes_AutopilotRenewedScrutiny.pdf',
        'trash/Tesla \'Autopilot\' crashes and fatalities surge, despite Musk\'s claims - The Washington Post-062023.pdf': 'Tesla/Main/News Artcles (Tesla)/Tesla \'Autopilot\' crashes and fatalities surge, despite Musk\'s claims - The Washington Post-062023.pdf',
        'trash/Tesla bought over $2 million worth of lidar sensors from Luminar this year _ The Verge.pdf': 'Tesla/Main/News Artcles (Tesla)/Tesla bought over $2 million worth of lidar sensors from Luminar this year _ The Verge.pdf',
        'trash/Inside the final seconds of a deadly Tesla Autopilot crash - Washington Post.pdf': 'Tesla/Main/News Artcles (Tesla)/Inside the final seconds of a deadly Tesla Autopilot crash - Washington Post.pdf',
        'trash/NewsArt_Sept2021Jun23Updated-Inside Tesla_ How Elon Musk Pushed His Vision for Autopilot - The New York Times.pdf': 'Tesla/Main/News Artcles (Tesla)/NewsArt_Sept2021Jun23Updated-Inside Tesla_ How Elon Musk Pushed His Vision for Autopilot - The New York Times.pdf',

        # Tesla/Main/Tesla Case Law files
        'trash/CaseLaw_Packet_Tesla.pdf': 'Tesla/Main/Tesla Case Law/CaseLaw_Packet_Tesla.pdf',
        'trash/CrespoVTesla.pdf': 'Tesla/Main/Tesla Case Law/CrespoVTesla.pdf',
        'trash/Tesla_Lawsuit_Example.pdf': 'Tesla/Main/Tesla Case Law/Tesla_Lawsuit_Example.pdf',
        'trash/Second-Amended-SGO-2021-01_2023-04-05_2.pdf': 'Tesla/Main/Tesla Case Law/Second-Amended-SGO-2021-01_2023-04-05_2.pdf',
        'trash/gov.uscourts.cand.310416.43.0.pdf': 'Tesla/Main/Tesla Case Law/gov.uscourts.cand.310416.43.0.pdf',
        'trash/PeopleVConagra_PublicNuisance.pdf': 'Tesla/Main/Tesla Case Law/PeopleVConagra_PublicNuisance.pdf',
        'trash/CreateAIvBotAuto_Texas_TradeSecrets_FSD.pdf': 'Tesla/Main/Tesla Case Law/CreateAIvBotAuto_Texas_TradeSecrets_FSD.pdf',
        'trash/FloresvTesla_DeceptiveMarketing.pdf': 'Tesla/Main/Tesla Case Law/FloresvTesla_DeceptiveMarketing.pdf',
        'trash/Lamontagne v. Tesla, Inc. et al, No. 3_2023cv00869 - Document 77 (N.D. Cal. 2024) __ Justia.pdf': 'Tesla/Main/Tesla Case Law/Lamontagne v. Tesla, Inc. et al, No. 3_2023cv00869 - Document 77 (N.D. Cal. 2024) __ Justia.pdf',
        'trash/JooVTesla_complaint_Example.pdf': 'Tesla/Main/Tesla Case Law/JooVTesla_complaint_Example.pdf',
        'trash/Case-395482439-Tesla-Inc-vs-Martin-Tripp.pdf': 'Tesla/Main/Tesla Case Law/Case-395482439-Tesla-Inc-vs-Martin-Tripp.pdf',
        'trash/Tesla_Answer_gov.uscourts.caed.464536.6.0.pdf': 'Tesla/Main/Tesla Case Law/Tesla_Answer_gov.uscourts.caed.464536.6.0.pdf',

        # Tesla/Main/Peer-Reviewed files
        'trash/EpilepticlikeSeizuresInFSD.pdf': 'Tesla/Main/Peer-Reviewed/EpilepticlikeSeizuresInFSD.pdf',
        'trash/AddressingDriverDisengagementandProperSystemUse.pdf': 'Tesla/Main/Peer-Reviewed/AddressingDriverDisengagementandProperSystemUse.pdf',

        # Tesla/Main/All tesla comms files
        'trash/TeslaCommspdf.pdf': 'Tesla/Main/All tesla comms/TeslaCommspdf.pdf',
        'trash/TeslaConvo-ServiceComplete.jpeg': 'Tesla/Main/All tesla comms/TeslaConvo-ServiceComplete.jpeg',
        'trash/May8-EmailChainwithPasadena-WaitingonOutcomeofWarrantyClaim.pdf': 'Tesla/Main/All tesla comms/May8-EmailChainwithPasadena-WaitingonOutcomeofWarrantyClaim.pdf',
        'trash/Tesla-Aug27-Payment.PNG': 'Tesla/Main/All tesla comms/Tesla-Aug27-Payment.PNG',
        'trash/Aug28-EmailtoPaymentResolution-SeekingHelpGoesUnanswered.pdf': 'Tesla/Main/All tesla comms/Aug28-EmailtoPaymentResolution-SeekingHelpGoesUnanswered.pdf',
        'trash/Tesla-LaysOutWhatHappened.PNG': 'Tesla/Main/All tesla comms/Tesla-LaysOutWhatHappened.PNG',
        'trash/teslacomma_allApr28-May8.pdf': 'Tesla/Main/All tesla comms/teslacomma_allApr28-May8.pdf',
        'trash/May14-May20-PasadenaCollisionEmails-JReffortstogetResponsefromBurbank.pdf': 'Tesla/Main/All tesla comms/May14-May20-PasadenaCollisionEmails-JReffortstogetResponsefromBurbank.pdf',
        'trash/May29_PaymentResolutionSeekingHelp.pdf': 'Tesla/Main/All tesla comms/May29_PaymentResolutionSeekingHelp.pdf',
        'trash/Gmail-thread-TeslaInsurance_ClaimClosureCL-18-922JPH-1.pdf': 'Tesla/Main/All tesla comms/Gmail-thread-TeslaInsurance_ClaimClosureCL-18-922JPH-1.pdf',
        'trash/Arbitration_OptOut.pdf': 'Tesla/Main/All tesla comms/Arbitration_OptOut.pdf',
        'trash/TeslaInsurance-August13-ClaimClosure.pdf': 'Tesla/Main/All tesla comms/TeslaInsurance-August13-ClaimClosure.pdf',
        'trash/TeslaInsurance_DenialofClaimOfficial.pdf': 'Tesla/Main/All tesla comms/TeslaInsurance_DenialofClaimOfficial.pdf',
        'trash/0428-29_Thread_TeslaNopermissiontomovecar.pdf': 'Tesla/Main/All tesla comms/0428-29_Thread_TeslaNopermissiontomovecar.pdf',
        'trash/May29-EmailtoPaymentRes-PleaseHelp-Unanswered.pdf': 'Tesla/Main/All tesla comms/May29-EmailtoPaymentRes-PleaseHelp-Unanswered.pdf',
        'trash/Tesla-EstimateSentOver.PNG': 'Tesla/Main/All tesla comms/Tesla-EstimateSentOver.PNG',
    }

    restored_count = 0
    error_count = 0

    print("🔄 Starting Tesla file restoration process...")
    print(f"📁 Found {len(tesla_restore_mapping)} Tesla files to restore")

    for trash_path, original_path in tesla_restore_mapping.items():
        try:
            # Check if trash file exists
            if not os.path.exists(trash_path):
                print(f"⚠️  Warning: {trash_path} not found in trash")
                continue

            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(original_path)
            os.makedirs(dest_dir, exist_ok=True)

            # Move file back to original location
            shutil.move(trash_path, original_path)
            print(f"✅ Restored Tesla file: {original_path}")
            restored_count += 1

        except Exception as e:
            print(f"❌ Error restoring {original_path}: {str(e)}")
            error_count += 1

    print (f"Tesla File Restoration Summary:")
    print(f"✅ Successfully restored: {restored_count} Tesla files")
    print(f"❌ Errors: {error_count} Tesla files")

    if restored_count > 0:
        print(f"🎉 Tesla file restoration completed!")
        print("📝 Tesla files are now back in the Tesla/ folder.")
if __name__ == "__main__":
    restore_tesla_files()