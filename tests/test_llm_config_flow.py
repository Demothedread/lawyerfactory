#!/usr/bin/env python3
"""
Test script to validate LLM config flow from AgentConfig to WriterBot initialization.
Tests the integration between phase handlers, AgentConfig, and WriterBot.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_config_flow():
    """Test the complete LLM config flow from AgentConfig to WriterBot"""

    try:
        # Import required modules
        from lawyerfactory.compose.agent_registry import AgentConfig
        from lawyerfactory.compose.bots.writer import WriterBot

        logger.info("Testing LLM config flow...")

        # Step 1: Create AgentConfig with LLM parameters (simulating what handle_drafting_phase does)
        llm_config = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000,
            "api_key": os.getenv("OPENAI_API_KEY", "test_key")
        }

        agent_config = AgentConfig(
            agent_type="WriterBot",
            config=llm_config
        )

        logger.info(f"Created AgentConfig with LLM config: {llm_config}")

        # Step 2: Create WriterBot with AgentConfig (simulating agent initialization)
        writer_bot = WriterBot(agent_config)

        logger.info("WriterBot initialized successfully with AgentConfig")

        # Step 4: Verify LLM config was extracted correctly
        expected_provider = llm_config["provider"]
        expected_model = llm_config["model"]
        expected_temperature = llm_config["temperature"]
        expected_max_tokens = llm_config["max_tokens"]

        logger.info(f"Expected LLM config: provider={expected_provider}, model={expected_model}, temperature={expected_temperature}, max_tokens={expected_max_tokens}")
        logger.info(f"WriterBot extracted: provider={writer_bot.llm_provider}, model={writer_bot.llm_model}, temperature={writer_bot.llm_temperature}, max_tokens={writer_bot.llm_max_tokens}")

        # Verify config extraction
        assert writer_bot.llm_provider == expected_provider, f"Provider mismatch: {writer_bot.llm_provider} != {expected_provider}"
        assert writer_bot.llm_model == expected_model, f"Model mismatch: {writer_bot.llm_model} != {expected_model}"
        assert writer_bot.llm_temperature == expected_temperature, f"Temperature mismatch: {writer_bot.llm_temperature} != {expected_temperature}"
        assert writer_bot.llm_max_tokens == expected_max_tokens, f"Max tokens mismatch: {writer_bot.llm_max_tokens} != {expected_max_tokens}"

        logger.info("✓ LLM config extraction verified successfully")

        # Step 5: Test basic WriterBot functionality (process method)
        test_message = "Test legal document generation"
        result = await writer_bot.process(test_message)

        if result and len(result) > 0:
            logger.info(f"✓ WriterBot.process() returned result: {result[:100]}...")
        else:
            logger.warning("⚠ WriterBot.process() returned empty result")

        logger.info("✓ LLM config flow test completed successfully")
        return True

    except Exception as e:
        logger.error(f"✗ LLM config flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_config_creation():
    """Test AgentConfig creation with various LLM configurations"""

    try:
        from lawyerfactory.compose.agent_registry import AgentConfig

        logger.info("Testing AgentConfig creation...")

        # Test different LLM providers
        test_configs = [
            {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 4000,
                "api_key": "test_key"
            },
            {
                "provider": "anthropic",
                "model": "claude-3-sonnet-20240229",
                "temperature": 0.5,
                "max_tokens": 3000,
                "api_key": "test_key"
            },
            {
                "provider": "groq",
                "model": "llama2-70b-4096",
                "temperature": 0.3,
                "max_tokens": 2000,
                "api_key": "test_key"
            }
        ]

        for i, config in enumerate(test_configs):
            agent_config = AgentConfig(
                agent_type=f"TestBot{i}",
                config=config
            )

            logger.info(f"✓ Created AgentConfig {i+1} with provider: {config['provider']}")

            # Verify config is stored correctly
            assert agent_config.config == config, f"Config mismatch for {config['provider']}"
            assert agent_config.agent_type == f"TestBot{i}", f"Agent type mismatch for {config['provider']}"

        logger.info("✓ AgentConfig creation test passed")
        return True

    except Exception as e:
        logger.error(f"✗ AgentConfig creation test failed: {e}")
        return False

async def main():
    """Run all LLM config flow tests"""

    logger.info("Starting LLM config flow validation tests...")

    # Test AgentConfig creation
    config_test_passed = await test_agent_config_creation()

    # Test complete LLM config flow
    flow_test_passed = await test_llm_config_flow()

    if config_test_passed and flow_test_passed:
        logger.info("🎉 All LLM config flow tests passed!")
        return 0
    else:
        logger.error("❌ Some LLM config flow tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)