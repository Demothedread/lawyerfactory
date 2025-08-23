"""
# Script Name: facts_matrix_adapter.py
# Description: Facts Matrix Adapter  This module provides functionality to transform raw ingestion output into the canonical facts_matrix format expected by the StatementOfFactsGenerator.  The adapter ensures a stable data contract between the ingestion pipeline and the document generation components, handling data shape variations gracefully.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Ingestion
#   - Group Tags: null
Facts Matrix Adapter

This module provides functionality to transform raw ingestion output into the canonical
facts_matrix format expected by the StatementOfFactsGenerator.

The adapter ensures a stable data contract between the ingestion pipeline and the
document generation components, handling data shape variations gracefully.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FactsMatrixAdapter:
    """
    Adapter to transform raw ingestion data into the canonical facts_matrix format.
    
    The facts_matrix format is a structured dictionary with the following expected keys:
    - undisputed_facts: List of facts that are agreed upon by all parties
    - disputed_facts: List of facts that are in contention
    - procedural_facts: List of facts related to legal procedures
    - case_metadata: Dictionary containing case information
    - evidence_references: Dictionary mapping facts to supporting evidence
    - key_events: List of timeline highlights (optional, defaults to [])
    - background_context: List of case background information (optional, defaults to [])
    - damages_claims: List of financial claims (optional, defaults to [])
    """
    
    @staticmethod
    def process(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw ingestion data into the canonical facts_matrix format.
        
        This is the primary API method matching the documented interface.
        
        Args:
            raw_data: Raw data from the ingestion pipeline
            
        Returns:
            Dict containing the canonicalized facts_matrix
        """
        return FactsMatrixAdapter.transform_to_facts_matrix(raw_data)
    
    @staticmethod
    def transform_to_facts_matrix(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw ingestion data into the canonical facts_matrix format.
        
        Args:
            raw_data: Raw data from the ingestion pipeline
            
        Returns:
            Dict containing the canonicalized facts_matrix
        """
        logger.info("Transforming raw ingestion data to facts_matrix format")
        
        # Initialize the canonical structure with safe defaults
        facts_matrix = {
            "undisputed_facts": [],
            "disputed_facts": [],
            "procedural_facts": [],
            "case_metadata": {},
            "evidence_references": {},
            # Optional fields with safe defaults
            "key_events": [],
            "background_context": [],
            "damages_claims": []
        }
        
        try:
            # Extract facts from various potential source structures
            facts_matrix["undisputed_facts"] = FactsMatrixAdapter._extract_facts(
                raw_data, ["undisputed_facts", "agreed_facts", "uncontested_facts"]
            )
            
            facts_matrix["disputed_facts"] = FactsMatrixAdapter._extract_facts(
                raw_data, ["disputed_facts", "contested_facts", "disagreed_facts"]
            )
            
            facts_matrix["procedural_facts"] = FactsMatrixAdapter._extract_facts(
                raw_data, ["procedural_facts", "process_facts", "court_facts"]
            )
            
            # Extract case metadata
            facts_matrix["case_metadata"] = FactsMatrixAdapter._extract_case_metadata(raw_data)
            
            # Extract evidence references
            facts_matrix["evidence_references"] = FactsMatrixAdapter._extract_evidence_references(raw_data)
            
            # Extract optional fields with graceful defaults
            facts_matrix["key_events"] = FactsMatrixAdapter._extract_facts(
                raw_data, ["key_events", "timeline", "important_events", "events"]
            )
            
            facts_matrix["background_context"] = FactsMatrixAdapter._extract_facts(
                raw_data, ["background_context", "background", "context", "case_background"]
            )
            
            facts_matrix["damages_claims"] = FactsMatrixAdapter._extract_facts(
                raw_data, ["damages_claims", "damages", "claims", "financial_claims"]
            )
            
            logger.info(f"Successfully transformed data: {len(facts_matrix['undisputed_facts'])} undisputed, "
                       f"{len(facts_matrix['disputed_facts'])} disputed, "
                       f"{len(facts_matrix['procedural_facts'])} procedural facts, "
                       f"{len(facts_matrix['key_events'])} key events, "
                       f"{len(facts_matrix['background_context'])} background items, "
                       f"{len(facts_matrix['damages_claims'])} damage claims")
            
        except Exception as e:
            logger.error(f"Error during facts_matrix transformation: {e}")
            # Return the safe defaults structure even on error
            
        return facts_matrix
    
    @staticmethod
    def _extract_facts(raw_data: Dict[str, Any], possible_keys: List[str]) -> List[str]:
        """
        Extract facts from raw data using multiple possible key names.
        
        Args:
            raw_data: Raw data dictionary
            possible_keys: List of possible key names to check
            
        Returns:
            List of fact strings
        """
        for key in possible_keys:
            if key in raw_data:
                facts = raw_data[key]
                if isinstance(facts, list):
                    return [str(fact) for fact in facts if fact]  # Filter out empty facts
                elif isinstance(facts, str):
                    return [facts] if facts.strip() else []
                elif isinstance(facts, dict):
                    # Handle nested fact structures
                    return FactsMatrixAdapter._flatten_fact_dict(facts)
        
        logger.debug(f"No facts found for keys: {possible_keys}")
        return []
    
    @staticmethod
    def _flatten_fact_dict(fact_dict: Dict[str, Any]) -> List[str]:
        """
        Flatten a nested fact dictionary into a list of fact strings.
        
        Args:
            fact_dict: Dictionary containing nested fact data
            
        Returns:
            List of fact strings
        """
        facts = []
        for key, value in fact_dict.items():
            if isinstance(value, list):
                facts.extend([str(fact) for fact in value if fact])
            elif isinstance(value, str) and value.strip():
                facts.append(value.strip())
            elif isinstance(value, dict):
                facts.extend(FactsMatrixAdapter._flatten_fact_dict(value))
        return facts
    
    @staticmethod
    def _extract_case_metadata(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract case metadata from raw data.
        
        Args:
            raw_data: Raw data dictionary
            
        Returns:
            Dictionary containing case metadata
        """
        metadata_keys = [
            "case_metadata", "metadata", "case_info", "case_data",
            "header", "case_header", "document_info"
        ]
        
        for key in metadata_keys:
            if key in raw_data and isinstance(raw_data[key], dict):
                return raw_data[key].copy()
        
        # Extract common metadata fields from top level
        metadata = {}
        common_fields = [
            "case_number", "case_title", "court", "judge", "date_filed",
            "plaintiff", "defendant", "attorney", "case_type"
        ]
        
        for field in common_fields:
            if field in raw_data:
                metadata[field] = raw_data[field]
        
        return metadata
    
    @staticmethod
    def _extract_evidence_references(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract evidence references from raw data.
        
        Args:
            raw_data: Raw data dictionary
            
        Returns:
            Dictionary mapping facts to evidence
        """
        evidence_keys = [
            "evidence_references", "evidence", "citations", "support_docs",
            "evidence_map", "fact_evidence_map"
        ]
        
        for key in evidence_keys:
            if key in raw_data and isinstance(raw_data[key], dict):
                return raw_data[key].copy()
        
        return {}
    
    @staticmethod
    def validate_facts_matrix(facts_matrix: Dict[str, Any]) -> bool:
        """
        Validate that a facts_matrix has the expected structure.
        
        Args:
            facts_matrix: The facts matrix to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = ["undisputed_facts", "disputed_facts", "procedural_facts", 
                        "case_metadata", "evidence_references"]
        
        if not isinstance(facts_matrix, dict):
            logger.error("facts_matrix must be a dictionary")
            return False
        
        for key in required_keys:
            if key not in facts_matrix:
                logger.error(f"facts_matrix missing required key: {key}")
                return False
            
            # Validate data types for each key
            if key in ["undisputed_facts", "disputed_facts", "procedural_facts"]:
                if not isinstance(facts_matrix[key], list):
                    logger.error(f"facts_matrix[{key}] must be a list")
                    return False
            elif key in ["case_metadata", "evidence_references"]:
                if not isinstance(facts_matrix[key], dict):
                    logger.error(f"facts_matrix[{key}] must be a dictionary")
                    return False
        
        logger.debug("facts_matrix validation passed")
        return True
