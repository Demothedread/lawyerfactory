"""
# Script Name: shotlist.py
# Description: Handles shotlist functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Workflow
#   - Group Tags: null
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def build_shot_list(evidence_rows: List[Dict[str, Any]], out_path: str | Path) -> Path:
    """
    Build a fact-by-fact shot list from normalized evidence rows.
    Handles missing fields gracefully with safe defaults and logging.
    """
    logger.info(f"Building shot list with {len(evidence_rows)} evidence rows")
    
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    fields = ["fact_id", "source_id", "timestamp", "summary", "entities", "citations"]
    
    # Track statistics for quality reporting
    stats = {
        "total_rows": len(evidence_rows),
        "missing_fact_id": 0,
        "missing_source_id": 0,
        "missing_timestamp": 0,
        "missing_summary": 0,
        "missing_entities": 0,
        "missing_citations": 0,
        "errors": 0
    }
    
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        
        for i, row in enumerate(evidence_rows, 1):
            try:
                # Safely extract each field with defaults and error handling
                processed_row = _process_evidence_row(row, i, stats)
                writer.writerow(processed_row)
                
            except Exception as e:
                logger.error(f"Error processing evidence row {i}: {e}")
                stats["errors"] += 1
                # Write a fallback row to maintain continuity
                fallback_row = {
                    "fact_id": f"error_fact_{i}",
                    "source_id": "error_processing",
                    "timestamp": "",
                    "summary": f"Error processing row {i}: {str(e)[:100]}",
                    "entities": "",
                    "citations": ""
                }
                writer.writerow(fallback_row)
    
    # Log processing statistics
    _log_processing_stats(stats, out_path)
    
    logger.info(f"Shot list created successfully at {out_path}")
    return out_path


def _process_evidence_row(row: Dict[str, Any], row_number: int, stats: Dict[str, int]) -> Dict[str, str]:
    """
    Process a single evidence row with robust error handling and safe defaults.
    """
    if not isinstance(row, dict):
        logger.warning(f"Row {row_number} is not a dictionary: {type(row)}")
        row = {}
    
    processed = {}
    
    # Handle fact_id
    fact_id = row.get("fact_id")
    if fact_id is None or fact_id == "":
        fact_id = f"fact_{row_number}"
        stats["missing_fact_id"] += 1
        logger.debug(f"Generated fact_id for row {row_number}: {fact_id}")
    processed["fact_id"] = str(fact_id)
    
    # Handle source_id
    source_id = row.get("source_id")
    if source_id is None:
        source_id = "unknown_source"
        stats["missing_source_id"] += 1
    elif source_id == "":
        source_id = "empty_source"
        stats["missing_source_id"] += 1
    processed["source_id"] = str(source_id)
    
    # Handle timestamp
    timestamp = row.get("timestamp")
    if timestamp is None:
        timestamp = ""
        stats["missing_timestamp"] += 1
    processed["timestamp"] = str(timestamp)
    
    # Handle summary
    summary = row.get("summary")
    if summary is None:
        summary = "[No summary available]"
        stats["missing_summary"] += 1
    elif summary == "":
        summary = "[Empty summary]"
        stats["missing_summary"] += 1
    processed["summary"] = str(summary)
    
    # Handle entities with robust list processing
    entities = row.get("entities", [])
    if entities is None:
        entities = []
        stats["missing_entities"] += 1
    elif not isinstance(entities, list):
        # Try to convert string to list or handle single entity
        if isinstance(entities, str):
            if entities.strip():
                entities = [entities]
            else:
                entities = []
                stats["missing_entities"] += 1
        else:
            entities = [str(entities)]
    
    # Filter out None/empty values and convert to strings
    entities_clean = [str(entity).strip() for entity in entities if entity is not None and str(entity).strip()]
    processed["entities"] = "|".join(entities_clean)
    
    # Handle citations with robust list processing
    citations = row.get("citations", [])
    if citations is None:
        citations = []
        stats["missing_citations"] += 1
    elif not isinstance(citations, list):
        # Try to convert string to list or handle single citation
        if isinstance(citations, str):
            if citations.strip():
                citations = [citations]
            else:
                citations = []
                stats["missing_citations"] += 1
        else:
            citations = [str(citations)]
    
    # Filter out None/empty values and convert to strings
    citations_clean = [str(citation).strip() for citation in citations if citation is not None and str(citation).strip()]
    processed["citations"] = "|".join(citations_clean)
    
    return processed


def _log_processing_stats(stats: Dict[str, int], out_path: Path) -> None:
    """Log processing statistics for quality monitoring."""
    total_rows = stats["total_rows"]
    if total_rows == 0:
        logger.warning("No evidence rows were processed")
        return
    
    logger.info(f"Shot list processing complete:")
    logger.info(f"  Total rows processed: {total_rows}")
    logger.info(f"  Errors encountered: {stats['errors']}")
    
    # Log missing field statistics
    missing_fields = {k: v for k, v in stats.items() if k.startswith("missing_") and v > 0}
    if missing_fields:
        logger.warning("Missing field statistics:")
        for field, count in missing_fields.items():
            field_name = field.replace("missing_", "")
            percentage = (count / total_rows) * 100
            logger.warning(f"  {field_name}: {count}/{total_rows} ({percentage:.1f}%)")
    else:
        logger.info("All evidence rows had complete field data")
    
    logger.info(f"Shot list saved to: {out_path}")


def validate_evidence_rows(evidence_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate evidence rows and return a quality report.
    Useful for pre-processing validation before building shot list.
    """
    if not isinstance(evidence_rows, list):
        return {"valid": False, "error": "evidence_rows must be a list"}
    
    validation_report = {
        "valid": True,
        "total_rows": len(evidence_rows),
        "quality_issues": [],
        "field_completeness": {},
        "recommendations": []
    }
    
    if len(evidence_rows) == 0:
        validation_report["quality_issues"].append("No evidence rows provided")
        validation_report["recommendations"].append("Add evidence data before building shot list")
        return validation_report
    
    required_fields = ["fact_id", "source_id", "timestamp", "summary", "entities", "citations"]
    field_counts = {field: 0 for field in required_fields}
    
    for i, row in enumerate(evidence_rows):
        if not isinstance(row, dict):
            validation_report["quality_issues"].append(f"Row {i+1} is not a dictionary")
            continue
            
        for field in required_fields:
            if field in row and row[field] is not None and str(row[field]).strip():
                field_counts[field] += 1
    
    # Calculate completeness percentages
    total_rows = len(evidence_rows)
    for field, count in field_counts.items():
        completeness = (count / total_rows) * 100 if total_rows > 0 else 0
        validation_report["field_completeness"][field] = {
            "complete_count": count,
            "total_count": total_rows,
            "completeness_percentage": completeness
        }
        
        if completeness < 80:  # Less than 80% complete
            validation_report["quality_issues"].append(f"Field '{field}' is only {completeness:.1f}% complete")
            validation_report["recommendations"].append(f"Improve data collection for '{field}' field")
    
    return validation_report
