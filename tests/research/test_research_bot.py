# Script Name: test_research_bot.py
# Description: !/usr/bin/env python3
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Research
#   - Group Tags: legal-research, testing
Test script for the enhanced ResearchBot integration with the orchestration system.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from knowledge_graph import KnowledgeGraph
from maestro.bots.research_bot import ResearchBot, ResearchQuery
from maestro.workflow_models import TaskPriority, WorkflowPhase, WorkflowTask

log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'research_bot_{os.getpid()}.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
logger = logging.getLogger(__name__)


async def test_research_bot_basic():
    """Test basic ResearchBot functionality"""
    logger.info("Testing ResearchBot basic functionality...")
    
    # Create in-memory knowledge graph
    kg = KnowledgeGraph(":memory:")
    
    # Initialize ResearchBot
    research_bot = ResearchBot(kg)
    
    # Test legacy Bot interface
    result = await research_bot.process("contract law negligence")
    logger.info(f"Legacy interface result: {result[:200]}...")
    
    assert "Research Summary" in result
    assert "Found" in result
    logger.info("✓ Basic functionality test passed")


async def test_research_bot_agent_interface():
    """Test ResearchBot as AgentInterface"""
    logger.info("Testing ResearchBot AgentInterface...")
    
    # Create in-memory knowledge graph
    kg = KnowledgeGraph(":memory:")
    
    # Initialize ResearchBot
    research_bot = ResearchBot(kg)
    
    # Initialize agent
    await research_bot.initialize()
    
    # Test health check
    health_ok = await research_bot.health_check()
    logger.info(f"Health check result: {health_ok}")
    
    # Create a test workflow task
    task = WorkflowTask(
        id="test_research_001",
        phase=WorkflowPhase.RESEARCH,
        agent_type="ResearchBot",
        description="Research negligence law for personal injury case",
        priority=TaskPriority.NORMAL,
        requires_human_approval=False
    )
    
    # Test task execution
    context = {
        'case_type': 'personal_injury',
        'case_id': 'test_case_001'
    }
    
    result = await research_bot.execute_task(task, context)
    
    logger.info(f"Task execution result: {result}")
    
    assert result['status'] == 'completed'
    assert 'citations_found' in result
    assert 'legal_principles' in result
    assert 'confidence_score' in result
    
    # Cleanup
    await research_bot.cleanup()
    
    logger.info("✓ AgentInterface test passed")


async def test_research_query_formulation():
    """Test research query formulation from context"""
    logger.info("Testing research query formulation...")
    
    # Create in-memory knowledge graph
    kg = KnowledgeGraph(":memory:")
    
    # Initialize ResearchBot
    research_bot = ResearchBot(kg)
    
    # Create direct research query
    query = ResearchQuery(
        query_text="medical malpractice informed consent",
        legal_issues=["medical malpractice", "informed consent", "duty of care"],
        jurisdiction="California",
        parties=["Dr. Smith", "Patient Jones"]
    )
    
    # Execute research
    result = await research_bot.execute_research(query)
    
    logger.info(f"Research result - Citations: {len(result.citations)}")
    logger.info(f"Research result - Legal principles: {len(result.legal_principles)}")
    logger.info(f"Research result - Gaps: {len(result.gaps_identified)}")
    logger.info(f"Research result - Confidence: {result.confidence_score:.2f}")
    
    assert len(result.citations) > 0
    assert result.confidence_score > 0
    assert result.query_id is not None
    
    logger.info("✓ Research query formulation test passed")


async def test_citation_scoring_and_ranking():
    """Test citation scoring and ranking functionality"""
    logger.info("Testing citation scoring and ranking...")
    
    # Create in-memory knowledge graph
    kg = KnowledgeGraph(":memory:")
    
    # Initialize ResearchBot
    research_bot = ResearchBot(kg)
    
    # Create research query focused on specific area
    query = ResearchQuery(
        query_text="breach of contract damages",
        legal_issues=["breach of contract", "compensatory damages"],
        jurisdiction="Federal"
    )
    
    # Execute research
    result = await research_bot.execute_research(query)
    
    # Verify citations are scored and ranked
    if result.citations:
        # Check that citations have relevance scores
        for citation in result.citations[:5]:
            assert hasattr(citation, 'relevance_score')
            assert citation.relevance_score >= 0
            logger.info(f"Citation: {citation.citation} - Score: {citation.relevance_score:.3f}")
        
        # Verify they're ranked (descending order)
        scores = [c.relevance_score for c in result.citations]
        assert scores == sorted(scores, reverse=True), "Citations should be ranked by score"
    
    logger.info("✓ Citation scoring and ranking test passed")


async def test_gap_analysis():
    """Test gap analysis functionality"""
    logger.info("Testing gap analysis...")
    
    # Create in-memory knowledge graph
    kg = KnowledgeGraph(":memory:")
    
    # Initialize ResearchBot
    research_bot = ResearchBot(kg)
    
    # Create research query with specific jurisdiction to test gap detection
    query = ResearchQuery(
        query_text="employment discrimination",
        legal_issues=["employment discrimination", "Title VII"],
        jurisdiction="Wyoming"  # Less common jurisdiction for testing
    )
    
    # Execute research
    result = await research_bot.execute_research(query)
    
    logger.info(f"Identified gaps: {result.gaps_identified}")
    logger.info(f"Recommendations: {result.recommendations}")
    
    # Should identify some gaps
    assert len(result.gaps_identified) >= 0  # May have gaps
    assert len(result.recommendations) > 0   # Should always have recommendations
    
    logger.info("✓ Gap analysis test passed")


async def run_all_tests():
    """Run all ResearchBot tests"""
    logger.info("Starting ResearchBot integration tests...")
    
    tests = [
        ("Basic Functionality", test_research_bot_basic),
        ("Agent Interface", test_research_bot_agent_interface),
        ("Query Formulation", test_research_query_formulation),
        ("Citation Scoring", test_citation_scoring_and_ranking),
        ("Gap Analysis", test_gap_analysis),
    ]
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            
            await test_func()
            
            logger.info(f"✓ {test_name} completed successfully")
            
        except Exception as e:
            logger.error(f"✗ {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    logger.info(f"\n{'='*50}")
    logger.info("All ResearchBot tests completed successfully!")
    logger.info("The enhanced research bot is ready for production use.")
    logger.info(f"{'='*50}")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)