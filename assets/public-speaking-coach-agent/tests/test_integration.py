"""Integration test: end-to-end agent flow with mocked LLM."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

import pytest
from agent import SampleAgent, _session_state


@pytest.fixture(autouse=True)
def clear_sessions():
    _session_state.clear()
    yield
    _session_state.clear()


def _make_response(content: str) -> dict:
    msg = MagicMock()
    msg.content = content
    return {"messages": [msg]}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_coaching_flow():
    """
    Integration test: user submits script → gets feedback → revises → masters model.

    Uses mocked LLM — no real AI Core calls are made.
    """
    agent = SampleAgent()
    ctx = "integration-ctx-001"

    # Turn 1: User asks for this week's model
    model_response = _make_response(
        "This week we are learning the PREP Method! Here is how it works:\n"
        "P = Point, R = Reason, E = Example, P = Point\n"
        "Try writing a short speech using this structure."
    )

    with patch.object(agent, "_invoke_with_fallback", new=AsyncMock(return_value=model_response)):
        result1 = await agent.invoke("Show me this week's model", ctx)

    assert result1.status == "completed"
    assert "PREP" in result1.message or "model" in result1.message.lower()

    # Turn 2: User submits a script
    feedback_response = _make_response(
        "✅ What's Working:\n"
        "Your opening point is clear and direct — 'Remote work improves productivity' hits the P in PREP perfectly.\n\n"
        "🔧 Areas to Improve:\n"
        "The Reason section is weak. Add a 'because' statement: 'Because employees save 90 minutes of commute time daily.'\n"
        "Your Example needs a specific statistic — try citing the Stanford study showing a 13% productivity increase."
    )

    script_v1 = (
        "Remote work improves productivity. I think it is good for employees. "
        "Companies should allow it. Remote work is better than office work. "
        "My colleague works from home and is happy. Remote work is the future."
    )

    with patch.object(agent, "_invoke_with_fallback", new=AsyncMock(return_value=feedback_response)):
        result2 = await agent.invoke(script_v1, ctx)

    assert result2.status == "completed"
    assert "Working" in result2.message or "Improve" in result2.message

    # Verify session state tracked the iteration
    from agent import _get_session
    session = _get_session(ctx)
    assert session["iteration_count"] >= 1

    # Turn 3: User revises and resubmits
    improved_response = _make_response(
        "Great improvement from your first draft!\n\n"
        "✅ What's Working:\n"
        "Your Reason is now clear and compelling. The Stanford study example is perfect.\n"
        "The closing restatement ties it all together beautifully.\n\n"
        "🔧 Areas to Improve:\n"
        "The example could be even more vivid — add the company name for credibility.\n\n"
        "Keep going — you're very close!"
    )

    script_v2 = (
        "Remote work improves productivity. Because employees save 90 minutes of commute time "
        "every day, they can redirect that energy into focused work. A Stanford study of 16,000 "
        "employees showed a 13% increase in output for remote workers. That is why embracing "
        "remote work is one of the smartest investments a company can make in its people."
    )

    with patch.object(agent, "_invoke_with_fallback", new=AsyncMock(return_value=improved_response)):
        result3 = await agent.invoke(script_v2, ctx)

    assert result3.status == "completed"
    assert session["iteration_count"] >= 2

    # Turn 4: User submits a polished script and gets completion
    completion_response = _make_response(
        "Your script is ready — well done! 🎉\n\n"
        "✅ What's Working:\n"
        "Every element of the PREP framework is present and well-executed.\n"
        "P: 'Remote work improves productivity' — direct and clear.\n"
        "R: The commute saving reason is compelling.\n"
        "E: The Stanford statistic with company context is credible.\n"
        "P: The closing restatement is memorable.\n\n"
        "You have mastered the PREP Method! Would you like to move on to Week 2: Monroe's Motivated Sequence?"
    )

    script_v3 = (
        "Remote work improves productivity. Because employees save 90 minutes of commute time "
        "every day, they redirect that energy into focused work. In a Stanford study of 16,000 "
        "workers at Ctrip, those working from home showed a 13% increase in output versus their "
        "office counterparts. That is why embracing remote work is one of the smartest investments "
        "a company can make in its people."
    )

    with patch.object(agent, "_invoke_with_fallback", new=AsyncMock(return_value=completion_response)):
        result4 = await agent.invoke(script_v3, ctx)

    assert result4.status == "completed"
    assert "ready" in result4.message.lower() or "well done" in result4.message.lower()
