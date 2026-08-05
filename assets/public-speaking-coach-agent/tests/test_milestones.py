"""Unit tests for milestone instrumentation (M1–M5 log emissions)."""
import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

import pytest
from agent import (
    SampleAgent,
    _log_milestone_achieved,
    _log_milestone_missed,
    _session_state,
)


@pytest.fixture(autouse=True)
def clear_sessions():
    _session_state.clear()
    yield
    _session_state.clear()


def test_milestone_achieved_log(caplog):
    """_log_milestone_achieved emits correct log message."""
    with caplog.at_level(logging.INFO, logger="agent"):
        _log_milestone_achieved("M1", "weekly model delivered — model=PREP Method, week=1")
    assert "M1.achieved" in caplog.text
    assert "PREP Method" in caplog.text


def test_milestone_missed_log(caplog):
    """_log_milestone_missed emits correct warning message."""
    with caplog.at_level(logging.WARNING, logger="agent"):
        _log_milestone_missed("M1", "model delivery did not complete — week=1")
    assert "M1.missed" in caplog.text
    assert "week=1" in caplog.text


def test_m2_milestone_format(caplog):
    """M2 milestone log contains model and iteration information."""
    with caplog.at_level(logging.INFO, logger="agent"):
        _log_milestone_achieved("M2", "script submitted — model=PREP Method, iteration=1")
    assert "M2.achieved" in caplog.text
    assert "iteration=1" in caplog.text


def test_m3_milestone_format(caplog):
    """M3 milestone log contains correct feedback delivery info."""
    with caplog.at_level(logging.INFO, logger="agent"):
        _log_milestone_achieved("M3", "feedback delivered — model=PREP Method, iteration=1")
    assert "M3.achieved" in caplog.text
    assert "feedback delivered" in caplog.text


def test_m4_milestone_format(caplog):
    """M4 milestone log records script iteration correctly."""
    with caplog.at_level(logging.INFO, logger="agent"):
        _log_milestone_achieved("M4", "script iterated — model=PREP Method, iteration=2")
    assert "M4.achieved" in caplog.text
    assert "iteration=2" in caplog.text


def test_m5_milestone_format(caplog):
    """M5 milestone log records model mastery with iteration count."""
    with caplog.at_level(logging.INFO, logger="agent"):
        _log_milestone_achieved("M5", "model mastered — model=PREP Method, total_iterations=3")
    assert "M5.achieved" in caplog.text
    assert "total_iterations=3" in caplog.text


@pytest.mark.asyncio
async def test_m2_m3_triggered_on_script_submission():
    """M2 and M3 milestones are triggered when a script is submitted."""
    import agent as agent_module

    agent_obj = SampleAgent()
    fake_response = MagicMock()
    fake_response.content = "Here is your feedback on the PREP model."
    mock_result = {"messages": [fake_response]}

    achieved_calls = []

    def capture_achieved(milestone_id, message):
        achieved_calls.append((milestone_id, message))

    with patch.object(agent_obj, "_invoke_with_fallback", new=AsyncMock(return_value=mock_result)):
        with patch.object(agent_module, "_log_milestone_achieved", side_effect=capture_achieved):
            # Use "feedback" keyword to trigger is_script_submission path
            script = "Please give me feedback on my script. Here is my PREP speech."
            await agent_obj._run_agent(script, "ctx-m2-m3-test", [])

    milestone_ids = [c[0] for c in achieved_calls]
    assert "M2" in milestone_ids, f"M2 not triggered. Got: {milestone_ids}"
    assert "M3" in milestone_ids, f"M3 not triggered. Got: {milestone_ids}"


@pytest.mark.asyncio
async def test_m5_triggered_on_completion_phrase():
    """M5 milestone is triggered when LLM response contains completion phrase."""
    import agent as agent_module

    agent_obj = SampleAgent()
    fake_response = MagicMock()
    fake_response.content = "Your script is ready — well done! You've mastered the PREP method."
    mock_result = {"messages": [fake_response]}

    achieved_calls = []

    def capture_achieved(milestone_id, message):
        achieved_calls.append((milestone_id, message))

    with patch.object(agent_obj, "_invoke_with_fallback", new=AsyncMock(return_value=mock_result)):
        with patch.object(agent_module, "_log_milestone_achieved", side_effect=capture_achieved):
            # Use "feedback" keyword to trigger is_script_submission path
            script = "Please give me feedback on my script. Here is my PREP speech."
            await agent_obj._run_agent(script, "ctx-m5-test", [])

    milestone_ids = [c[0] for c in achieved_calls]
    assert "M5" in milestone_ids, f"M5 not triggered. Got: {milestone_ids}"
