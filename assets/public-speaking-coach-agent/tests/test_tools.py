"""Unit tests for agent tools: get_progress and advance_model."""
import sys
from pathlib import Path

# Ensure app/ is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

import pytest
from agent import (
    CURRICULUM,
    _advance_model,
    _get_progress,
    _get_session,
    _session_state,
)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear session state before each test."""
    _session_state.clear()
    yield
    _session_state.clear()


@pytest.mark.asyncio
async def test_get_progress_initial_state():
    """get_progress returns correct initial state for a new session."""
    ctx = "test-ctx-001"
    result = await _get_progress(ctx)
    assert "Current week: 1" in result
    assert CURRICULUM[0] in result
    assert "Models mastered: 0" in result


@pytest.mark.asyncio
async def test_get_progress_after_iteration():
    """get_progress reflects iteration count correctly."""
    ctx = "test-ctx-002"
    session = _get_session(ctx)
    session["iteration_count"] = 3
    result = await _get_progress(ctx)
    assert "Script iterations this model: 3" in result


@pytest.mark.asyncio
async def test_advance_model_moves_to_next_week():
    """advance_model increments week number and model index."""
    ctx = "test-ctx-003"
    session = _get_session(ctx)
    assert session["week"] == 1
    assert session["model_index"] == 0

    result = await _advance_model(ctx)

    assert session["week"] == 2
    assert session["model_index"] == 1
    assert CURRICULUM[0] in session["mastered_models"]
    assert CURRICULUM[1] in result


@pytest.mark.asyncio
async def test_advance_model_resets_iteration_count():
    """advance_model resets iteration count to 0 for the new model."""
    ctx = "test-ctx-004"
    session = _get_session(ctx)
    session["iteration_count"] = 5

    await _advance_model(ctx)

    assert session["iteration_count"] == 0


@pytest.mark.asyncio
async def test_advance_model_completion():
    """advance_model returns completion message after all models mastered."""
    ctx = "test-ctx-005"
    session = _get_session(ctx)
    session["model_index"] = len(CURRICULUM) - 1
    session["week"] = len(CURRICULUM)

    result = await _advance_model(ctx)

    assert "completed" in result.lower() or "entire" in result.lower()


@pytest.mark.asyncio
async def test_advance_model_tracks_mastered():
    """advance_model correctly tracks mastered models list."""
    ctx = "test-ctx-006"

    await _advance_model(ctx)
    result = await _get_progress(ctx)

    assert "Models mastered: 1" in result
    assert CURRICULUM[0] in result
