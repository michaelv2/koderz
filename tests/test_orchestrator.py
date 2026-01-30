"""Tests for experiment orchestrator."""

import pytest
from unittest.mock import Mock, AsyncMock
from koderz.orchestrator import ExperimentOrchestrator


@pytest.mark.asyncio
async def test_build_iteration_prompt():
    """Test iteration prompt building."""
    cortex = Mock()
    local = Mock()
    frontier = Mock()

    orchestrator = ExperimentOrchestrator(cortex, local, frontier)

    problem = {
        "task_id": "HumanEval/0",
        "prompt": "def test(): pass"
    }

    prompt = await orchestrator._build_iteration_prompt(
        exp_id="test_123",
        problem=problem,
        spec="Test spec",
        iteration=1,
        checkpoint_guidance=None
    )

    assert "Test spec" in prompt
    assert "def test(): pass" in prompt


@pytest.mark.asyncio
async def test_build_iteration_prompt_with_guidance():
    """Test iteration prompt with checkpoint guidance."""
    cortex = Mock()
    local = Mock()
    frontier = Mock()

    orchestrator = ExperimentOrchestrator(cortex, local, frontier)

    problem = {
        "task_id": "HumanEval/0",
        "prompt": "def test(): pass"
    }

    prompt = await orchestrator._build_iteration_prompt(
        exp_id="test_123",
        problem=problem,
        spec="Test spec",
        iteration=6,
        checkpoint_guidance="Try handling edge cases"
    )

    assert "Test spec" in prompt
    assert "Try handling edge cases" in prompt
