"""
# Script Name: shotlist.py
# Description: Shotlist Builder Module  This module provides the ShotlistBuilder class that processes evidence references from the facts matrix to generate comprehensive shot lists for legal case preparation.  The builder integrates with the existing shotlist functionality while providing a clean API that matches the documented data contracts.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: evidence-processing
Shotlist Builder Module

This module provides the ShotlistBuilder class that processes evidence references
from the facts matrix to generate comprehensive shot lists for legal case preparation.

The builder integrates with the existing shotlist functionality while providing
a clean API that matches the documented data contracts.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import the existing shotlist functionality
from lawyerfactory.phases.outline.shotlist.shotlist import (
    build_shot_list,
    validate_evidence_rows,
    _process_evidence_row
)

logger = logging.getLogger(__name__)


class ShotlistBuilder:
    """
    Builder class for generating shot lists from facts matrix evidence data.
    
    This class provides the primary API for shotlist generation, conforming to
    the documented interface while leveraging the robust existing implementation.
    """
    
    def __init__(self, output_directory: Optional[str] = None):
        """
        Initialize the ShotlistBuilder.
        
        Args:
            output_directory: Directory to save shot list files (defaults to current directory)
        """
        self.output_directory = Path(output_directory) if output_directory else Path(".")
        self.statistics = {
            'total_evidence_processed': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'missing_fields': {},
            'quality_score': 0.0
        }
    
    def build(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a shot list from evidence data.
        
        This is the primary API method matching the documented interface.
        
        Args:
            evidence_data: Evidence references from facts matrix
            
        Returns:
            Dictionary containing shot list results and statistics
        """
        logger.info("Building shot list from evidence data")
        
        try:
            # Convert evidence data to normalized rows
            evidence_rows = self._convert_evidence_to_rows(evidence_data)
            
            # Validate evidence rows
            validation_report = validate_evidence_rows(evidence_rows)
            
            if not validation_report["valid"]:
                logger.error(f"Evidence validation failed: {validation_report['error']}")
                return {
                    'success': False,
                    'error': validation_report['error'],
                    'evidence_count': 0,
                    'statistics': self.statistics
                }
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_directory / f"shot_list_{timestamp}.csv"
            
            # Build the shot list
            result_path = build_shot_list(evidence_rows, output_file)
            
            # Update statistics
            self._update_statistics(evidence_rows, validation_report)
            
            logger.info(f"Shot list generated successfully: {result_path}")
            
            return {
                'success': True,
                'output_file': str(result_path),
                'evidence_count': len(evidence_rows),
                'validation_report': validation_report,
                'statistics': self.statistics,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.exception(f"Failed to build shot list: {e}")
            return {
                'success': False,
                'error': str(e),
                'evidence_count': 0,
                'statistics': self.statistics
            }
    
    def _convert_evidence_to_rows(self, evidence_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert facts matrix evidence data to normalized evidence rows.
        
        Args:
            evidence_data: Evidence references from facts matrix
            
        Returns:
            List of normalized evidence row dictionaries
        """
        logger.debug("Converting evidence data to normalized rows")
        
        evidence_rows = []
        
        if not isinstance(evidence_data, dict):
            logger.warning(f"Evidence data is not a dictionary: {type(evidence_data)}")
            return evidence_rows
        
        # Process each evidence entry
        for evidence_id, evidence_info in evidence_data.items():
            try:
                row = self._create_evidence_row(evidence_id, evidence_info)
                evidence_rows.append(row)
                self.statistics['successful_conversions'] += 1
                
            except Exception as e:
                logger.error(f"Failed to convert evidence {evidence_id}: {e}")
                self.statistics['failed_conversions'] += 1
                
                # Create fallback row
                fallback_row = {
                    'fact_id': f"evidence_{evidence_id}",
                    'source_id': evidence_id,
                    'timestamp': '',
                    'summary': f"Error processing evidence: {str(e)[:100]}",
                    'entities': '',
                    'citations': ''
                }
                evidence_rows.append(fallback_row)
        
        self.statistics['total_evidence_processed'] = len(evidence_data)
        logger.debug(f"Converted {len(evidence_rows)} evidence entries to rows")
        
        return evidence_rows
    
    def _create_evidence_row(self, evidence_id: str, evidence_info: Any) -> Dict[str, Any]:
        """
        Create a normalized evidence row from evidence information.
        
        Args:
            evidence_id: Unique identifier for the evidence
            evidence_info: Evidence information (can be string, dict, or other types)
            
        Returns:
            Normalized evidence row dictionary
        """
        # Handle different evidence info formats
        if isinstance(evidence_info, str):
            # Simple string evidence
            return {
                'fact_id': f"evidence_{evidence_id}",
                'source_id': evidence_id,
                'timestamp': '',
                'summary': evidence_info,
                'entities': [],
                'citations': []
            }
        
        elif isinstance(evidence_info, dict):
            # Structured evidence information
            return {
                'fact_id': evidence_info.get('fact_id', f"evidence_{evidence_id}"),
                'source_id': evidence_info.get('source_id', evidence_id),
                'timestamp': evidence_info.get('timestamp', evidence_info.get('date', '')),
                'summary': evidence_info.get('summary', evidence_info.get('description', evidence_info.get('content', ''))),
                'entities': evidence_info.get('entities', evidence_info.get('parties', [])),
                'citations': evidence_info.get('citations', evidence_info.get('references', []))
            }
        
        else:
            # Convert other types to string representation
            return {
                'fact_id': f"evidence_{evidence_id}",
                'source_id': evidence_id,
                'timestamp': '',
                'summary': str(evidence_info) if evidence_info is not None else '[No description available]',
                'entities': [],
                'citations': []
            }
    
    def _update_statistics(self, evidence_rows: List[Dict[str, Any]], validation_report: Dict[str, Any]) -> None:
        """
        Update internal statistics based on processing results.
        
        Args:
            evidence_rows: Processed evidence rows
            validation_report: Validation report from evidence validation
        """
        # Track missing fields
        field_completeness = validation_report.get('field_completeness', {})
        for field, info in field_completeness.items():
            completeness = info.get('completeness_percentage', 0)
            missing_count = info['total_count'] - info['complete_count']
            self.statistics['missing_fields'][field] = {
                'missing_count': missing_count,
                'completeness_percentage': completeness
            }
        
        # Calculate overall quality score
        if field_completeness:
            avg_completeness = sum(
                info.get('completeness_percentage', 0) 
                for info in field_completeness.values()
            ) / len(field_completeness)
            self.statistics['quality_score'] = round(avg_completeness / 100, 2)
        
        logger.debug(f"Updated statistics: {self.statistics}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current processing statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        return self.statistics.copy()
    
    def validate_evidence_data(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate evidence data before processing.
        
        Args:
            evidence_data: Evidence references to validate
            
        Returns:
            Validation report with recommendations
        """
        logger.debug("Validating evidence data structure")
        
        validation_report = {
            'valid': True,
            'total_evidence_entries': 0,
            'issues': [],
            'recommendations': []
        }
        
        if not isinstance(evidence_data, dict):
            validation_report['valid'] = False
            validation_report['issues'].append(f"Evidence data must be a dictionary, got {type(evidence_data)}")
            return validation_report
        
        validation_report['total_evidence_entries'] = len(evidence_data)
        
        if len(evidence_data) == 0:
            validation_report['issues'].append("No evidence entries found")
            validation_report['recommendations'].append("Add evidence references to improve shot list quality")
        
        # Check for common evidence data patterns
        structured_count = 0
        string_count = 0
        
        for evidence_id, evidence_info in evidence_data.items():
            if isinstance(evidence_info, dict):
                structured_count += 1
            elif isinstance(evidence_info, str):
                string_count += 1
        
        if structured_count > 0:
            validation_report['recommendations'].append(f"Found {structured_count} structured evidence entries - good data quality")
        
        if string_count > structured_count:
            validation_report['recommendations'].append("Consider providing more structured evidence data for better shot list details")
        
        return validation_report


# Convenience function for direct usage
def build_shotlist_from_facts_matrix(facts_matrix: Dict[str, Any], 
                                    output_directory: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to build shot list directly from facts matrix.
    
    Args:
        facts_matrix: Complete facts matrix containing evidence_references
        output_directory: Directory to save shot list files
        
    Returns:
        Shot list build results
    """
    evidence_data = facts_matrix.get('evidence_references', {})
    
    if not evidence_data:
        logger.warning("No evidence_references found in facts matrix")
        return {
            'success': False,
            'error': 'No evidence references found in facts matrix',
            'evidence_count': 0
        }
    
    builder = ShotlistBuilder(output_directory)
    return builder.build(evidence_data)