"""
# Script Name: prompt_deconstruction.py
# Description: LLM-Powered Prompt Deconstruction Engine for LawyerFactory Replaces regex-based keyword extraction with intelligent semantic analysis. Integrates with the enhanced maestro orchestration system.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Workflow
#   - Group Tags: null
LLM-Powered Prompt Deconstruction Engine for LawyerFactory
Replaces regex-based keyword extraction with intelligent semantic analysis.
Integrates with the enhanced maestro orchestration system.
"""

from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KeywordType(Enum):
    """Types of keywords identified in prompts"""

    DOCUMENT_TYPE = "document_type"
    PRIMARY_SUBJECT = "primary_subject"
    LEGAL_ISSUE = "legal_issue"
    PARTIES = "parties"
    JURISDICTION = "jurisdiction"
    TIMEFRAME = "timeframe"
    CLAIMS = "claims"
    RELIEF_SOUGHT = "relief_sought"
    FACTS = "facts"
    SUBKEY_FACTOR = "subkey_factor"


class ConfidenceLevel(Enum):
    """Confidence levels for keyword extraction"""

    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4


@dataclass
class ExtractedKeyword:
    """A keyword extracted from the prompt with metadata"""

    text: str
    keyword_type: KeywordType
    confidence: float
    position: Tuple[int, int]  # start, end positions in text
    semantic_weight: float = 1.0
    related_entities: List[str] = field(default_factory=list)
    css_class: str = ""

    def __post_init__(self):
        """Set CSS class based on keyword type"""
        css_mapping = {
            KeywordType.DOCUMENT_TYPE: "factor-doc",
            KeywordType.PRIMARY_SUBJECT: "factor-key",
            KeywordType.LEGAL_ISSUE: "factor-key",
            KeywordType.PARTIES: "factor-subkey",
            KeywordType.JURISDICTION: "factor-subkey",
            KeywordType.CLAIMS: "factor-subkey",
            KeywordType.FACTS: "factor-subkey",
            KeywordType.SUBKEY_FACTOR: "factor-subkey",
            KeywordType.TIMEFRAME: "factor-neutral",
            KeywordType.RELIEF_SOUGHT: "factor-neutral",
        }
        self.css_class = css_mapping.get(self.keyword_type, "factor-neutral")


@dataclass
class DeconstructionResult:
    """Result of prompt deconstruction analysis"""

    original_prompt: str
    document_type: Optional[str]
    keywords: List[ExtractedKeyword]
    generated_prompts: List[str]
    confidence_score: float
    preprocessing_notes: List[str] = field(default_factory=list)
    semantic_relationships: Dict[str, List[str]] = field(default_factory=dict)

    def get_highlighted_prompt(self) -> str:
        """Generate HTML with highlighted keywords"""
        highlighted = self.original_prompt

        # Sort keywords by position (reverse to maintain positions)
        sorted_keywords = sorted(
            self.keywords, key=lambda k: k.position[0], reverse=True
        )

        for keyword in sorted_keywords:
            start, end = keyword.position
            original_text = highlighted[start:end]
            highlighted_text = f'<span class="{keyword.css_class}" data-type="{keyword.keyword_type.value}" data-confidence="{keyword.confidence:.2f}" title="Confidence: {keyword.confidence:.1%}">{original_text}</span>'
            highlighted = highlighted[:start] + highlighted_text + highlighted[end:]

        return highlighted

    def get_keywords_by_type(self, keyword_type: KeywordType) -> List[ExtractedKeyword]:
        """Get keywords of a specific type"""
        return [k for k in self.keywords if k.keyword_type == keyword_type]


class LLMPromptDeconstructionEngine:
    """Advanced prompt deconstruction using LLM analysis"""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.document_type_patterns = {
            "legal_claim": [
                "lawsuit",
                "complaint",
                "claim",
                "legal action",
                "litigation",
                "sue",
                "court",
            ],
            "business_proposal": [
                "proposal",
                "business plan",
                "investment",
                "funding",
                "partnership",
                "venture",
            ],
            "white_paper": [
                "white paper",
                "research",
                "analysis",
                "report",
                "study",
                "technical document",
            ],
        }

    async def deconstruct_prompt(
        self, prompt: str, hint_document_type: Optional[str] = None
    ) -> DeconstructionResult:
        """
        Main method to deconstruct a user prompt into semantic components

        Args:
            prompt: The user's input prompt
            hint_document_type: Optional hint about document type

        Returns:
            DeconstructionResult with extracted keywords and analysis
        """
        try:
            logger.info(f"Deconstructing prompt: {prompt[:100]}...")

            # Step 1: Preprocessing and normalization
            cleaned_prompt = self._preprocess_prompt(prompt)

            # Step 2: Document type detection
            document_type = await self._detect_document_type(
                cleaned_prompt, hint_document_type
            )

            # Step 3: Extract keywords using hybrid approach
            keywords = await self._extract_keywords_hybrid(
                cleaned_prompt, document_type
            )

            # Step 4: Generate specialized prompts for agents
            generated_prompts = await self._generate_agent_prompts(
                keywords, document_type
            )

            # Step 5: Calculate overall confidence
            confidence_score = self._calculate_confidence(keywords)

            # Step 6: Build semantic relationships
            relationships = self._build_semantic_relationships(keywords)

            result = DeconstructionResult(
                original_prompt=prompt,
                document_type=document_type,
                keywords=keywords,
                generated_prompts=generated_prompts,
                confidence_score=confidence_score,
                semantic_relationships=relationships,
            )

            logger.info(
                f"Deconstruction complete: {len(keywords)} keywords, confidence: {confidence_score:.2f}"
            )
            return result

        except Exception as e:
            logger.error(f"Prompt deconstruction failed: {e}")
            # Return fallback result
            return self._create_fallback_result(prompt, hint_document_type)

    def _preprocess_prompt(self, prompt: str) -> str:
        """Clean and normalize the prompt"""
        # Remove extra whitespace
        cleaned = re.sub(r"\s+", " ", prompt.strip())

        # Normalize punctuation
        cleaned = re.sub(r"[^\w\s\-.,;:!?()]", " ", cleaned)

        return cleaned

    async def _llm_document_type_detection(self, prompt: str, fallback: str) -> str:
        """Use LLM to detect document type with higher accuracy"""
        try:
            llm_prompt = f"""
            Analyze this user prompt and determine the document type they want to create:
            
            Prompt: "{prompt}"
            
            Document types:
            - legal_claim: Legal complaints, lawsuits, litigation documents
            - business_proposal: Business plans, investment proposals, partnership agreements
            - white_paper: Technical reports, research documents, analysis papers
            
            Respond with just the document type (legal_claim, business_proposal, or white_paper):
            """

            response = await self.llm_service.generate_content(
                llm_prompt, {"max_tokens": 50}
            )
            detected_type = response.content.strip().lower()

            if detected_type in self.document_type_patterns:
                return detected_type
            else:
                return fallback

        except Exception as e:
            logger.warning(f"LLM document type detection failed: {e}")
            return fallback

    async def _extract_keywords_llm(
        self, prompt: str, document_type: str
    ) -> List[ExtractedKeyword]:
        """LLM-powered semantic keyword extraction"""
        try:
            llm_prompt = f"""
            Extract and categorize key information from this {document_type} prompt:
            
            Prompt: "{prompt}"
            
            Identify:
            1. Primary subject/topic
            2. Parties involved (companies, people, organizations)
            3. Legal issues or business concerns
            4. Key facts or circumstances
            5. Desired outcomes or relief sought
            
            Format as JSON with structure:
            {{
                "primary_subject": ["topic1", "topic2"],
                "parties": ["Party Name"],
                "legal_issues": ["issue1", "issue2"],
                "facts": ["fact1", "fact2"],
                "relief_sought": ["outcome1", "outcome2"]
            }}
            """

            response = await self.llm_service.generate_content(
                llm_prompt, {"max_tokens": 500}
            )

            try:
                extracted_data = json.loads(response.content)
                keywords = []

                type_mapping = {
                    "primary_subject": KeywordType.PRIMARY_SUBJECT,
                    "parties": KeywordType.PARTIES,
                    "legal_issues": KeywordType.LEGAL_ISSUE,
                    "facts": KeywordType.FACTS,
                    "relief_sought": KeywordType.RELIEF_SOUGHT,
                }

                for category, items in extracted_data.items():
                    if category in type_mapping and items:
                        for item in items:
                            # Find position in original prompt
                            position = self._find_text_position(prompt, item)
                            if position:
                                keywords.append(
                                    ExtractedKeyword(
                                        text=item,
                                        keyword_type=type_mapping[category],
                                        confidence=0.8,
                                        position=position,
                                        semantic_weight=1.0,
                                    )
                                )

                return keywords

            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON for keyword extraction")
                return []

        except Exception as e:
            logger.error(f"LLM keyword extraction failed: {e}")
            return []

    def _find_text_position(self, prompt: str, text: str) -> Optional[Tuple[int, int]]:
        """Find the position of text in prompt (case-insensitive)"""
        prompt_lower = prompt.lower()
        text_lower = text.lower()

        start = prompt_lower.find(text_lower)
        if start != -1:
            return (start, start + len(text))
        return None

    async def _detect_document_type(
        self, prompt: str, hint: Optional[str] = None
    ) -> str:
        """Detect the document type from the prompt"""
        if hint and hint in self.document_type_patterns:
            return hint

        # Score each document type based on keyword presence
        scores = {}
        prompt_lower = prompt.lower()

        for doc_type, patterns in self.document_type_patterns.items():
            score = sum(1 for pattern in patterns if pattern in prompt_lower)
            scores[doc_type] = score

        # Return the highest scoring type, default to legal_claim
        best_type = (
            max(scores.keys(), key=lambda k: scores[k])
            if any(scores.values())
            else "legal_claim"
        )

        # If using LLM service, enhance with LLM analysis
        if self.llm_service:
            best_type = await self._llm_document_type_detection(prompt, best_type)

        return best_type

    async def _extract_keywords_hybrid(
        self, prompt: str, document_type: str
    ) -> List[ExtractedKeyword]:
        """Extract keywords using both rule-based and LLM approaches"""
        keywords = []

        # Rule-based extraction for reliable patterns
        rule_based_keywords = self._extract_keywords_rules(prompt, document_type)
        keywords.extend(rule_based_keywords)

        # LLM-enhanced extraction for complex semantics
        if self.llm_service:
            llm_keywords = await self._extract_keywords_llm(prompt, document_type)
            keywords.extend(llm_keywords)

        # Deduplicate and merge overlapping keywords
        keywords = self._merge_overlapping_keywords(keywords)

        return keywords

    def _extract_keywords_rules(
        self, prompt: str, document_type: str
    ) -> List[ExtractedKeyword]:
        """Rule-based keyword extraction with improved patterns"""
        keywords = []

        # Document type specific patterns
        if document_type == "legal_claim":
            patterns = {
                KeywordType.PARTIES: [
                    r"(?:against|versus|v\.)\s+([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Company)?)",
                    r"(?:sue|suing)\s+([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Company)?)",
                ],
                KeywordType.LEGAL_ISSUE: [
                    r"(?:for|regarding|concerning|about)\s+(breach of (?:contract|warranty|duty)|negligence|fraud|discrimination|harassment)",
                    r"(?:alleging|claiming)\s+([a-z][a-zA-Z\s]+)",
                ],
                KeywordType.JURISDICTION: [
                    r"(?:in|under)\s+([A-Z][a-zA-Z\s]+ (?:court|jurisdiction|law))",
                    r"(?:federal|state|local)\s+(court|jurisdiction)",
                ],
                KeywordType.RELIEF_SOUGHT: [
                    r"(?:seeking|requesting|demanding)\s+([a-zA-Z\s]+(?:damages|relief|compensation|injunction))",
                ],
            }
        elif document_type == "business_proposal":
            patterns = {
                KeywordType.PRIMARY_SUBJECT: [
                    r"(?:for|to)\s+(fund|invest in|partner with|acquire)\s+([a-zA-Z\s]+)",
                    r"(?:proposal for|plan for)\s+([a-zA-Z\s]+)",
                ],
                KeywordType.PARTIES: [
                    r"(?:with|to|for)\s+([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Company))",
                ],
            }
        else:  # white_paper
            patterns = {
                KeywordType.PRIMARY_SUBJECT: [
                    r"(?:analysis of|research on|study of)\s+([a-zA-Z\s]+)",
                    r"(?:white paper on|report on)\s+([a-zA-Z\s]+)",
                ],
            }

        # Extract using patterns
        for keyword_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.finditer(pattern, prompt, re.IGNORECASE)
                for match in matches:
                    text = match.group(1) if match.groups() else match.group(0)
                    keywords.append(
                        ExtractedKeyword(
                            text=text.strip(),
                            keyword_type=keyword_type,
                            confidence=0.7,
                            position=(match.start(), match.end()),
                            semantic_weight=1.0,
                        )
                    )

        return keywords

    def _merge_overlapping_keywords(
        self, keywords: List[ExtractedKeyword]
    ) -> List[ExtractedKeyword]:
        """Merge overlapping keywords, keeping highest confidence"""
        if not keywords:
            return []

        # Sort by position
        sorted_keywords = sorted(keywords, key=lambda k: k.position[0])
        merged = [sorted_keywords[0]]

        for current in sorted_keywords[1:]:
            last = merged[-1]

            # Check for overlap
            if current.position[0] < last.position[1]:
                # Overlapping - keep the one with higher confidence
                if current.confidence > last.confidence:
                    merged[-1] = current
            else:
                merged.append(current)

        return merged

    async def _generate_agent_prompts(
        self, keywords: List[ExtractedKeyword], document_type: str
    ) -> List[str]:
        """Generate specialized prompts for different agent phases"""
        prompts = []

        # Extract key information for prompt generation
        primary_subjects = [
            k.text for k in keywords if k.keyword_type == KeywordType.PRIMARY_SUBJECT
        ]
        parties = [k.text for k in keywords if k.keyword_type == KeywordType.PARTIES]
        legal_issues = [
            k.text for k in keywords if k.keyword_type == KeywordType.LEGAL_ISSUE
        ]

        if document_type == "legal_claim":
            # Research phase prompt
            if legal_issues and parties:
                prompts.append(
                    f"Research legal precedents for {', '.join(legal_issues)} involving {', '.join(parties)}"
                )

            # Outline phase prompt
            if primary_subjects:
                prompts.append(
                    f"Create legal complaint outline for {', '.join(primary_subjects)} addressing {', '.join(legal_issues)}"
                )

            # Drafting phase prompt
            prompts.append(
                "Draft professional legal complaint incorporating research findings and factual allegations"
            )

        elif document_type == "business_proposal":
            if primary_subjects:
                prompts.append(
                    f"Research market opportunities and competitive landscape for {', '.join(primary_subjects)}"
                )
                prompts.append(
                    f"Create business proposal outline for {', '.join(primary_subjects)}"
                )
                prompts.append(
                    "Draft comprehensive business proposal with financial projections"
                )

        return prompts

    def _calculate_confidence(self, keywords: List[ExtractedKeyword]) -> float:
        """Calculate overall confidence score for the deconstruction"""
        if not keywords:
            return 0.0

        # Weight by keyword importance and confidence
        total_weight = 0
        weighted_confidence = 0

        for keyword in keywords:
            weight = keyword.semantic_weight
            total_weight += weight
            weighted_confidence += keyword.confidence * weight

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    def _build_semantic_relationships(
        self, keywords: List[ExtractedKeyword]
    ) -> Dict[str, List[str]]:
        """Build relationships between extracted keywords"""
        relationships = {}

        # Group related keywords
        for keyword in keywords:
            key = keyword.text.lower()
            relationships[key] = []

            # Find related keywords based on type and proximity
            for other in keywords:
                if other != keyword:
                    # Same type keywords are related
                    if other.keyword_type == keyword.keyword_type:
                        relationships[key].append(other.text)

                    # Proximity-based relationships
                    distance = abs(keyword.position[0] - other.position[0])
                    if distance < 50:  # Within 50 characters
                        relationships[key].append(other.text)

        return relationships

    def _create_fallback_result(
        self, prompt: str, hint_document_type: Optional[str]
    ) -> DeconstructionResult:
        """Create a basic result when full processing fails"""
        # Simple regex fallback
        document_type = hint_document_type or "legal_claim"

        # Extract basic keywords using simple patterns
        keywords = []

        # Extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]+)"', prompt)
        for phrase in quoted_phrases:
            position = prompt.find(f'"{phrase}"')
            if position != -1:
                keywords.append(
                    ExtractedKeyword(
                        text=phrase,
                        keyword_type=KeywordType.PRIMARY_SUBJECT,
                        confidence=0.6,
                        position=(position, position + len(phrase) + 2),
                    )
                )

        # Extract capitalized words (potential proper nouns)
        capitalized = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", prompt)
        for cap in capitalized:
            if len(cap) > 3:  # Ignore short words
                position = prompt.find(cap)
                if position != -1:
                    keywords.append(
                        ExtractedKeyword(
                            text=cap,
                            keyword_type=KeywordType.PARTIES,
                            confidence=0.5,
                            position=(position, position + len(cap)),
                        )
                    )

        return DeconstructionResult(
            original_prompt=prompt,
            document_type=document_type,
            keywords=keywords,
            generated_prompts=[f"Process {document_type} based on user requirements"],
            confidence_score=0.3,
            preprocessing_notes=["Fallback processing used due to analysis failure"],
        )


# Integration class for easy use with existing LawyerFactory system
class PromptDeconstructionService:
    """Service wrapper for easy integration with LawyerFactory enhanced system"""

    def __init__(self, llm_service=None):
        self.engine = LLMPromptDeconstructionEngine(llm_service)

    async def analyze_prompt(
        self, prompt: str, document_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a user prompt and return structured data for frontend integration

        Returns:
            Dictionary compatible with enhanced_factory.html JavaScript and WebSocket events
        """
        result = await self.engine.deconstruct_prompt(prompt, document_type_hint)

        # Convert to format expected by enhanced frontend
        return {
            "original_prompt": result.original_prompt,
            "highlighted_prompt": result.get_highlighted_prompt(),
            "document_type": result.document_type,
            "confidence_score": result.confidence_score,
            "keywords": [
                {
                    "text": kw.text,
                    "type": kw.keyword_type.value,
                    "confidence": kw.confidence,
                    "class": kw.css_class,
                    "position": kw.position,
                    "semantic_weight": kw.semantic_weight,
                }
                for kw in result.keywords
            ],
            "generated_prompts": result.generated_prompts,
            "semantic_relationships": result.semantic_relationships,
            "preprocessing_notes": result.preprocessing_notes,
            "extraction_metadata": {
                "total_keywords": len(result.keywords),
                "high_confidence_keywords": len(
                    [k for k in result.keywords if k.confidence >= 0.8]
                ),
                "document_type_detected": result.document_type,
                "processing_complete": True,
            },
        }

    def get_keyword_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of extracted keywords for UI display"""
        keywords = analysis_result.get("keywords", [])

        # Group by type
        by_type = {}
        for kw in keywords:
            kw_type = kw["type"]
            if kw_type not in by_type:
                by_type[kw_type] = []
            by_type[kw_type].append(kw)

        # Calculate statistics
        total_keywords = len(keywords)
        avg_confidence = (
            sum(kw["confidence"] for kw in keywords) / total_keywords
            if total_keywords > 0
            else 0
        )

        return {
            "total_keywords": total_keywords,
            "average_confidence": avg_confidence,
            "keywords_by_type": by_type,
            "high_confidence_count": len(
                [k for k in keywords if k["confidence"] >= 0.8]
            ),
            "medium_confidence_count": len(
                [k for k in keywords if 0.6 <= k["confidence"] < 0.8]
            ),
            "low_confidence_count": len([k for k in keywords if k["confidence"] < 0.6]),
        }
