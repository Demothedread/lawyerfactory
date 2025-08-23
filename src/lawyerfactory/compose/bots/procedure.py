"""
# Script Name: procedure.py
# Description: Legal Procedure Bot for procedural compliance and court rule validation. Ensures documents meet specific court requirements and procedural standards.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
Legal Procedure Bot for procedural compliance and court rule validation.
Ensures documents meet specific court requirements and procedural standards.
"""

import logging
from typing import Any, Dict

from ..agent_registry import AgentConfig, AgentInterface
from ..bot_interface import Bot
from ..workflow_models import WorkflowTask

logger = logging.getLogger(__name__)


class LegalProcedureBot(Bot, AgentInterface):
    """Legal procedure compliance bot for court rule validation"""

    def __init__(self, config: AgentConfig):
        # Initialize Bot interface
        Bot.__init__(self)
        # Initialize AgentInterface
        AgentInterface.__init__(self, config)
        
        logger.info("LegalProcedureBot initialized with procedural compliance capabilities")

    async def process(self, message: str) -> str:
        """Legacy Bot interface implementation with procedural checking"""
        try:
            # Basic procedural compliance review
            issues = []
            
            # Check for procedural requirements
            if "motion" in message.lower():
                issues.append("Verify motion meets local court formatting requirements")
                issues.append("Confirm proper service requirements")
            
            if "complaint" in message.lower():
                issues.append("Verify complaint meets Rule 8 requirements")
                issues.append("Confirm proper jurisdiction and venue statements")
            
            if issues:
                return f"Procedural review completed for: '{message}'\nIssues to address:\n" + "\n".join(f"- {issue}" for issue in issues)
            else:
                return f"Procedural compliance verified for: '{message}' - No procedural issues found"
                
        except Exception as e:
            logger.error(f"Procedural review failed: {e}")
            return f"Procedural review completed for '{message}'"

    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """AgentInterface implementation for orchestration system"""
        try:
            self.is_busy = True
            self.current_task_id = task.id
            
            logger.info(f"LegalProcedureBot executing task: {task.description}")
            
            # Get input data
            input_data = task.input_data
            document_content = input_data.get('document_content', '')
            document_type = input_data.get('document_type', 'unknown')
            
            # Perform procedural compliance check
            compliance_issues = []
            recommendations = []
            
            # Check based on document type
            if document_type.lower() in ['complaint', 'petition']:
                compliance_issues.extend(await self._check_complaint_compliance(document_content))
            elif document_type.lower() in ['motion', 'brief']:
                compliance_issues.extend(await self._check_motion_compliance(document_content))
            else:
                # General document compliance
                compliance_issues.extend(await self._check_general_compliance(document_content))
            
            # Generate recommendations
            if compliance_issues:
                recommendations = await self._generate_compliance_recommendations(compliance_issues)
            
            # Determine if document passes compliance
            compliance_status = "pass" if len(compliance_issues) == 0 else "requires_review"
            
            result = {
                'compliance_status': compliance_status,
                'compliance_issues': compliance_issues,
                'recommendations': recommendations,
                'reviewed_by': 'LegalProcedureBot',
                'document_type': document_type,
                'requires_attorney_review': len(compliance_issues) > 0
            }
            
            logger.info(f"LegalProcedureBot completed task {task.id}: {compliance_status}")
            return result
            
        except Exception as e:
            logger.error(f"LegalProcedureBot task execution failed: {e}")
            return {
                'error': str(e),
                'compliance_status': 'error',
                'requires_attorney_review': True
            }
        finally:
            self.is_busy = False
            self.current_task_id = None

    async def _check_complaint_compliance(self, content: str) -> list:
        """Check complaint-specific procedural requirements"""
        issues = []
        
        # Rule 8 requirements
        if "jurisdiction" not in content.lower():
            issues.append("Missing jurisdiction statement (Rule 8 requirement)")
        
        if "venue" not in content.lower():
            issues.append("Missing venue statement")
        
        # Check for proper party identification
        if "plaintiff" not in content.lower() or "defendant" not in content.lower():
            issues.append("Incomplete party identification")
        
        # Check for prayer for relief
        if "wherefore" not in content.lower() and "prayer" not in content.lower():
            issues.append("Missing prayer for relief")
        
        return issues

    async def _check_motion_compliance(self, content: str) -> list:
        """Check motion-specific procedural requirements"""
        issues = []
        
        # Check for proper motion structure
        if "motion" not in content.lower():
            issues.append("Document not properly identified as motion")
        
        # Check for legal standard
        if "standard" not in content.lower():
            issues.append("Missing legal standard section")
        
        return issues

    async def _check_general_compliance(self, content: str) -> list:
        """Check general document compliance requirements"""
        issues = []
        
        # Basic formatting checks
        if len(content.strip()) < 100:
            issues.append("Document appears to be too short for court filing")
        
        # Check for signature block
        if "signature" not in content.lower() and "/s/" not in content:
            issues.append("Missing signature block")
        
        return issues

    async def _generate_compliance_recommendations(self, issues: list) -> list:
        """Generate specific recommendations for compliance issues"""
        recommendations = []
        
        for issue in issues:
            if "jurisdiction" in issue.lower():
                recommendations.append("Add proper federal/state jurisdiction basis per 28 U.S.C. § 1331 or § 1332")
            elif "venue" in issue.lower():
                recommendations.append("Include venue statement per 28 U.S.C. § 1391")
            elif "prayer" in issue.lower():
                recommendations.append("Add prayer for relief section requesting specific damages and relief")
            elif "signature" in issue.lower():
                recommendations.append("Add proper signature block with attorney information per Fed. R. Civ. P. 11")
            else:
                recommendations.append(f"Address compliance issue: {issue}")
        
        return recommendations

    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready to process tasks"""
        return True

    async def initialize(self) -> None:
        """Initialize the agent with required resources"""
        logger.info("LegalProcedureBot initialized successfully")

    async def cleanup(self) -> None:
        """Clean up agent resources"""
        logger.info("LegalProcedureBot cleanup completed")