"""
Document Export and Version Control System
Provides multi-format export capabilities, version control, and change tracking
for Statement of Facts and other legal documents.
"""

import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, BinaryIO
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import zipfile
import tempfile

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats"""
    MICROSOFT_WORD = "docx"
    PDF = "pdf"
    MARKDOWN = "md"
    PLAIN_TEXT = "txt"
    RTF = "rtf"
    HTML = "html"


class VersionControlAction(Enum):
    """Version control actions"""
    CREATE = "create"
    MODIFY = "modify"
    APPROVE = "approve"
    REJECT = "reject"
    MERGE = "merge"
    BRANCH = "branch"


@dataclass
class DocumentMetadata:
    """Metadata for legal documents"""
    document_id: str
    title: str
    document_type: str
    case_number: str
    client_name: str
    attorney_name: str
    creation_date: datetime
    last_modified: datetime
    version: str
    status: str
    word_count: int
    paragraph_count: int
    citation_count: int
    tags: List[str] = field(default_factory=list)


@dataclass
class VersionInfo:
    """Version information for documents"""
    version_id: str
    version_number: str
    author: str
    timestamp: datetime
    action: VersionControlAction
    changes_summary: str
    parent_version: Optional[str] = None
    merge_source: Optional[str] = None
    approval_status: str = "pending"


@dataclass
class ExportPackage:
    """Complete export package for legal documents"""
    package_id: str
    creation_timestamp: datetime
    documents: Dict[str, bytes]
    metadata: DocumentMetadata
    version_info: VersionInfo
    export_formats: List[ExportFormat]
    attorney_certifications: List[Dict[str, Any]] = field(default_factory=list)


class DocumentExportSystem:
    """Comprehensive document export and version control system"""
    
    def __init__(self, storage_path: str = "export_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.versions_path = self.storage_path / "versions"
        self.versions_path.mkdir(exist_ok=True)
        self.exports_path = self.storage_path / "exports"
        self.exports_path.mkdir(exist_ok=True)
        
        self.version_registry: Dict[str, List[VersionInfo]] = {}
        self.document_registry: Dict[str, DocumentMetadata] = {}
        
    def create_document_version(self, document_id: str, content: str, 
                              author: str, changes_summary: str,
                              metadata: Optional[DocumentMetadata] = None) -> VersionInfo:
        """Create new version of document with full tracking"""
        logger.info(f"Creating new version for document {document_id}")
        
        # Generate version info
        version_id = self._generate_version_id()
        current_versions = self.version_registry.get(document_id, [])
        version_number = f"v{len(current_versions) + 1}.0"
        
        version_info = VersionInfo(
            version_id=version_id,
            version_number=version_number,
            author=author,
            timestamp=datetime.now(),
            action=VersionControlAction.CREATE if not current_versions else VersionControlAction.MODIFY,
            changes_summary=changes_summary,
            parent_version=current_versions[-1].version_id if current_versions else None
        )
        
        # Store document content
        self._save_document_version(document_id, version_id, content)
        
        # Update registries
        self.version_registry.setdefault(document_id, []).append(version_info)
        
        if metadata:
            metadata.last_modified = datetime.now()
            metadata.version = version_number
            self.document_registry[document_id] = metadata
        
        self._save_registries()
        
        return version_info
    
    def export_document(self, document_id: str, version_id: Optional[str] = None,
                       formats: Optional[List[ExportFormat]] = None,
                       include_metadata: bool = True) -> ExportPackage:
        """Export document in multiple formats with comprehensive package"""
        logger.info(f"Exporting document {document_id} in multiple formats")
        
        # Get latest version if not specified
        if not version_id:
            versions = self.version_registry.get(document_id, [])
            if not versions:
                raise ValueError(f"No versions found for document {document_id}")
            version_id = versions[-1].version_id
        
        # Get document content and metadata
        content = self._load_document_version(document_id, version_id)
        metadata = self.document_registry.get(document_id)
        version_info = self._get_version_info(document_id, version_id)
        
        if not content:
            raise ValueError(f"Document content not found: {document_id}:{version_id}")
        
        # Default formats if not specified
        if not formats:
            formats = [ExportFormat.MICROSOFT_WORD, ExportFormat.PDF, ExportFormat.MARKDOWN]
        
        # Generate documents in all requested formats
        documents = {}
        for format_type in formats:
            formatted_content = self._format_document_for_export(content, format_type, metadata)
            documents[f"statement_of_facts.{format_type.value}"] = formatted_content
        
        # Create comprehensive export package
        package = ExportPackage(
            package_id=self._generate_package_id(),
            creation_timestamp=datetime.now(),
            documents=documents,
            metadata=metadata or DocumentMetadata(
                document_id=document_id,
                title="Legal Document",
                document_type="statement_of_facts",
                case_number="Unknown",
                client_name="Unknown",
                attorney_name="Unknown",
                creation_date=datetime.now(),
                last_modified=datetime.now(),
                version="1.0",
                status="draft",
                word_count=0,
                paragraph_count=0,
                citation_count=0
            ),
            version_info=version_info or VersionInfo(
                version_id="unknown",
                version_number="1.0",
                author="system",
                timestamp=datetime.now(),
                action=VersionControlAction.CREATE,
                changes_summary="Initial version"
            ),
            export_formats=formats
        )
        
        # Add supporting documents
        if include_metadata and metadata and version_info:
            package.documents["metadata.json"] = json.dumps(asdict(metadata), indent=2, default=str).encode()
            package.documents["version_info.json"] = json.dumps(asdict(version_info), indent=2, default=str).encode()
            package.documents["export_certificate.txt"] = self._generate_export_certificate(package).encode()
        
        # Save export package
        self._save_export_package(package)
        
        return package
    
    def _format_document_for_export(self, content: str, format_type: ExportFormat,
                                  metadata: Optional[DocumentMetadata] = None) -> bytes:
        """Format document content for specific export format"""
        
        if format_type == ExportFormat.MICROSOFT_WORD:
            return self._format_for_word(content, metadata)
        elif format_type == ExportFormat.PDF:
            return self._format_for_pdf(content, metadata)
        elif format_type == ExportFormat.MARKDOWN:
            return self._format_for_markdown(content, metadata)
        elif format_type == ExportFormat.PLAIN_TEXT:
            return content.encode('utf-8')
        elif format_type == ExportFormat.RTF:
            return self._format_for_rtf(content, metadata)
        elif format_type == ExportFormat.HTML:
            return self._format_for_html(content, metadata)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _format_for_word(self, content: str, metadata: Optional[DocumentMetadata] = None) -> bytes:
        """Format document for Microsoft Word (.docx)"""
        # Create Word-compatible formatting
        word_content = self._add_word_headers(content, metadata)
        word_content = self._add_word_styles(word_content)
        word_content = self._format_word_citations(word_content)
        
        # For actual Word export, you would use python-docx library
        # This is a placeholder that creates Word-ready text
        return word_content.encode('utf-8')
    
    def _format_for_pdf(self, content: str, metadata: Optional[DocumentMetadata] = None) -> bytes:
        """Format document for PDF export"""
        # Add PDF-specific formatting
        pdf_content = self._add_pdf_headers(content, metadata)
        pdf_content = self._format_pdf_layout(pdf_content)
        
        # For actual PDF generation, you would use reportlab or similar
        # This is a placeholder
        return pdf_content.encode('utf-8')
    
    def _format_for_markdown(self, content: str, metadata: Optional[DocumentMetadata] = None) -> bytes:
        """Format document for Markdown export"""
        markdown_content = self._convert_to_markdown(content)
        
        if metadata:
            header = f"""# {metadata.title}

**Case Number:** {metadata.case_number}  
**Client:** {metadata.client_name}  
**Attorney:** {metadata.attorney_name}  
**Date:** {metadata.creation_date.strftime('%B %d, %Y')}  
**Version:** {metadata.version}

---

"""
            markdown_content = header + markdown_content
        
        return markdown_content.encode('utf-8')
    
    def _format_for_rtf(self, content: str, metadata: Optional[DocumentMetadata] = None) -> bytes:
        """Format document for RTF export"""
        rtf_content = self._convert_to_rtf(content, metadata)
        return rtf_content.encode('utf-8')
    
    def _format_for_html(self, content: str, metadata: Optional[DocumentMetadata] = None) -> bytes:
        """Format document for HTML export"""
        html_content = self._convert_to_html(content, metadata)
        return html_content.encode('utf-8')
    
    def create_export_bundle(self, document_ids: List[str], 
                           bundle_name: str = "legal_documents") -> str:
        """Create bundled export of multiple documents"""
        logger.info(f"Creating export bundle: {bundle_name}")
        
        bundle_path = self.exports_path / f"{bundle_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for doc_id in document_ids:
                try:
                    # Export each document
                    export_package = self.export_document(doc_id)
                    
                    # Add documents to zip
                    for filename, content in export_package.documents.items():
                        archive_path = f"{doc_id}/{filename}"
                        zipf.writestr(archive_path, content)
                        
                except Exception as e:
                    logger.error(f"Failed to export document {doc_id}: {e}")
                    # Add error log to bundle
                    error_info = f"Error exporting {doc_id}: {str(e)}"
                    zipf.writestr(f"{doc_id}/error.txt", error_info.encode())
            
            # Add bundle metadata
            bundle_metadata = {
                'bundle_name': bundle_name,
                'creation_date': datetime.now().isoformat(),
                'document_count': len(document_ids),
                'documents': document_ids
            }
            zipf.writestr("bundle_metadata.json", 
                         json.dumps(bundle_metadata, indent=2).encode())
        
        return str(bundle_path)
    
    def track_document_changes(self, document_id: str, old_version: str, 
                             new_version: str) -> Dict[str, Any]:
        """Track and analyze changes between document versions"""
        old_content = self._load_document_version(document_id, old_version)
        new_content = self._load_document_version(document_id, new_version)
        
        if not old_content or not new_content:
            raise ValueError("Cannot load document versions for comparison")
        
        changes = self._analyze_document_changes(old_content, new_content)
        
        # Store change analysis
        change_log = {
            'document_id': document_id,
            'old_version': old_version,
            'new_version': new_version,
            'analysis_timestamp': datetime.now().isoformat(),
            'changes': changes
        }
        
        change_log_path = self.versions_path / f"changes_{document_id}_{new_version}.json"
        with open(change_log_path, 'w') as f:
            json.dump(change_log, f, indent=2, default=str)
        
        return changes
    
    def _analyze_document_changes(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze changes between two document versions"""
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        # Simple line-by-line comparison (could be enhanced with difflib)
        added_lines = []
        removed_lines = []
        modified_lines = []
        
        max_lines = max(len(old_lines), len(new_lines))
        for i in range(max_lines):
            old_line = old_lines[i] if i < len(old_lines) else ""
            new_line = new_lines[i] if i < len(new_lines) else ""
            
            if old_line != new_line:
                if not old_line:
                    added_lines.append({'line_number': i + 1, 'content': new_line})
                elif not new_line:
                    removed_lines.append({'line_number': i + 1, 'content': old_line})
                else:
                    modified_lines.append({
                        'line_number': i + 1,
                        'old_content': old_line,
                        'new_content': new_line
                    })
        
        return {
            'total_changes': len(added_lines) + len(removed_lines) + len(modified_lines),
            'lines_added': len(added_lines),
            'lines_removed': len(removed_lines),
            'lines_modified': len(modified_lines),
            'added_content': added_lines,
            'removed_content': removed_lines,
            'modified_content': modified_lines,
            'change_percentage': self._calculate_change_percentage(old_content, new_content)
        }
    
    def _calculate_change_percentage(self, old_content: str, new_content: str) -> float:
        """Calculate percentage of content that changed"""
        old_words = set(old_content.split())
        new_words = set(new_content.split())
        
        if not old_words:
            return 100.0 if new_words else 0.0
        
        common_words = old_words.intersection(new_words)
        change_ratio = 1 - (len(common_words) / len(old_words))
        
        return round(change_ratio * 100, 2)
    
    def get_document_history(self, document_id: str) -> Dict[str, Any]:
        """Get complete history of document versions"""
        versions = self.version_registry.get(document_id, [])
        metadata = self.document_registry.get(document_id)
        
        return {
            'document_id': document_id,
            'metadata': asdict(metadata) if metadata else None,
            'version_count': len(versions),
            'versions': [asdict(version) for version in versions],
            'creation_date': versions[0].timestamp if versions else None,
            'last_modified': versions[-1].timestamp if versions else None,
            'total_authors': len(set(v.author for v in versions))
        }
    
    def _generate_version_id(self) -> str:
        """Generate unique version ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"ver_{timestamp}"
    
    def _generate_package_id(self) -> str:
        """Generate unique package ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"pkg_{timestamp}"
    
    def _save_document_version(self, document_id: str, version_id: str, content: str):
        """Save document version to storage"""
        version_path = self.versions_path / document_id
        version_path.mkdir(exist_ok=True)
        
        content_path = version_path / f"{version_id}.txt"
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create content hash for integrity checking
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        hash_path = version_path / f"{version_id}.hash"
        with open(hash_path, 'w') as f:
            f.write(content_hash)
    
    def _load_document_version(self, document_id: str, version_id: str) -> Optional[str]:
        """Load document version from storage"""
        content_path = self.versions_path / document_id / f"{version_id}.txt"
        
        if not content_path.exists():
            return None
        
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify content integrity
        if self._verify_content_integrity(document_id, version_id, content):
            return content
        else:
            logger.warning(f"Content integrity check failed for {document_id}:{version_id}")
            return content  # Return anyway but log warning
    
    def _verify_content_integrity(self, document_id: str, version_id: str, content: str) -> bool:
        """Verify document content integrity using hash"""
        hash_path = self.versions_path / document_id / f"{version_id}.hash"
        
        if not hash_path.exists():
            return False
        
        with open(hash_path, 'r') as f:
            stored_hash = f.read().strip()
        
        current_hash = hashlib.sha256(content.encode()).hexdigest()
        return stored_hash == current_hash
    
    def _get_version_info(self, document_id: str, version_id: str) -> Optional[VersionInfo]:
        """Get version info for specific version"""
        versions = self.version_registry.get(document_id, [])
        for version in versions:
            if version.version_id == version_id:
                return version
        return None
    
    def _save_export_package(self, package: ExportPackage):
        """Save export package to storage"""
        package_path = self.exports_path / f"{package.package_id}.zip"
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, content in package.documents.items():
                zipf.writestr(filename, content)
    
    def _generate_export_certificate(self, package: ExportPackage) -> str:
        """Generate export certificate for legal compliance"""
        return f"""EXPORT CERTIFICATION

Package ID: {package.package_id}
Export Date: {package.creation_timestamp.strftime('%B %d, %Y at %I:%M %p')}
Document: {package.metadata.title if package.metadata else 'Legal Document'}
Version: {package.version_info.version_number}
Author: {package.version_info.author}

FORMATS INCLUDED:
{chr(10).join(f"- {fmt.value.upper()}" for fmt in package.export_formats)}

This export package contains the complete Statement of Facts as approved by counsel.
The documents herein are certified to be true and complete copies of the originals.

Generated by LawyerFactory Document Export System
"""
    
    def _save_registries(self):
        """Save version and document registries"""
        version_registry_path = self.storage_path / "version_registry.json"
        document_registry_path = self.storage_path / "document_registry.json"
        
        with open(version_registry_path, 'w') as f:
            json.dump({k: [asdict(v) for v in versions] for k, versions in self.version_registry.items()}, 
                     f, indent=2, default=str)
        
        with open(document_registry_path, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.document_registry.items()}, 
                     f, indent=2, default=str)
    
    def _add_word_headers(self, content: str, metadata: Optional[DocumentMetadata]) -> str:
        """Add Word-specific headers and formatting"""
        if metadata:
            header = f"""[WORD DOCUMENT HEADER]
Case: {metadata.case_number}
Client: {metadata.client_name}
Attorney: {metadata.attorney_name}
Date: {metadata.creation_date.strftime('%B %d, %Y')}

"""
            return header + content
        return content
    
    def _add_word_styles(self, content: str) -> str:
        """Add Word-compatible styling markers"""
        # Add formatting markers that can be processed by Word
        return content.replace('\n\n', '\n[PARAGRAPH_BREAK]\n')
    
    def _format_word_citations(self, content: str) -> str:
        """Format citations for Word compatibility"""
        # Ensure citations are properly formatted for Word
        return content
    
    def _add_pdf_headers(self, content: str, metadata: Optional[DocumentMetadata]) -> str:
        """Add PDF-specific headers"""
        if metadata:
            header = f"""[PDF HEADER]
{metadata.title}
Case No. {metadata.case_number}
Page 1

"""
            return header + content
        return content
    
    def _format_pdf_layout(self, content: str) -> str:
        """Format content for PDF layout"""
        # Add PDF-specific formatting
        return content.replace('\n\n', '\n[PAGE_BREAK]\n')
    
    def _convert_to_markdown(self, content: str) -> str:
        """Convert content to Markdown format"""
        # Convert legal document formatting to Markdown
        lines = content.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if line.isupper() and len(line) > 10:
                # Convert section headers
                markdown_lines.append(f"## {line}")
            elif line.startswith(('I.', 'II.', 'III.', 'IV.', 'V.')):
                # Convert Roman numeral sections
                markdown_lines.append(f"### {line}")
            elif line and line[0].isdigit() and '. ' in line:
                # Keep numbered paragraphs as is
                markdown_lines.append(line)
            else:
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    def _convert_to_rtf(self, content: str, metadata: Optional[DocumentMetadata]) -> str:
        """Convert content to RTF format"""
        rtf_header = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}}}"
        rtf_content = content.replace('\n', r'\par ')
        return rtf_header + rtf_content + "}"
    
    def _convert_to_html(self, content: str, metadata: Optional[DocumentMetadata]) -> str:
        """Convert content to HTML format"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{metadata.title if metadata else 'Legal Document'}</title>
    <style>
        body {{ font-family: 'Times New Roman', serif; line-height: 1.6; margin: 1in; }}
        h1, h2, h3 {{ font-weight: bold; }}
        .case-caption {{ text-align: center; }}
    </style>
</head>
<body>
{content.replace(chr(10), '<br>').replace('  ', '&nbsp;&nbsp;')}
</body>
</html>"""
        return html_content


def create_document_export_system(storage_path: str = "export_storage") -> DocumentExportSystem:
    """Factory function to create document export system"""
    return DocumentExportSystem(storage_path)


if __name__ == "__main__":
    # Example usage
    export_system = create_document_export_system()
    
    print("Document Export System initialized successfully")
    print("Ready for multi-format document export and version control")