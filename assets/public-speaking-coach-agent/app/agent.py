import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Literal, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool, StructuredTool
from langchain_litellm import ChatLiteLLM
from langgraph.graph.state import CompiledStateGraph
from litellm.exceptions import APIConnectionError, APIError, Timeout
from opentelemetry import trace
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section

from mcp_tools import get_user_sub

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# ─── Public Speaking Curriculum ───────────────────────────────────────────────
CURRICULUM = [
    "PREP Method",
    "Monroe's Motivated Sequence",
    "Minto Pyramid",
    "STAR Method",
    "SBI Feedback Model",
    "Rule of Three",
]

# ─── In-memory session state ───────────────────────────────────────────────────
# keyed by context_id
_session_state: dict[str, dict] = {}


def _get_session(context_id: str) -> dict:
    """Return or initialise session state for a given context_id."""
    if context_id not in _session_state:
        _session_state[context_id] = {
            "week": 1,
            "model_index": 0,
            "iteration_count": 0,
            "mastered_models": [],
        }
    return _session_state[context_id]


# ─── Decorators ───────────────────────────────────────────────────────────────


@agent_model(
    key="config.model",
    label="LLM Model",
    description="The language model powering this agent",
)
def get_model_name() -> str:
    return "sap/anthropic--claude-4.5-sonnet"


@agent_model(
    key="config.fallback_model",
    label="Fallback LLM Model",
    description="Fallback model used when the primary model is unavailable. Leave empty to disable fallback.",
)
def get_fallback_model_name() -> str:
    return ""


@agent_config(
    key="config.temperature",
    label="LLM Temperature",
    description="Controls randomness of responses (0.0 = deterministic, 1.0 = creative)",
)
def get_temperature() -> float:
    return 0.7


@agent_config(
    key="config.checkpointer.ttl_seconds",
    label="Thread TTL (seconds)",
    description="Evict inactive conversation threads after this period of inactivity. Set to 0 to disable eviction.",
)
def thread_ttl_seconds() -> int:
    return 3600  # 1 hour


@prompt_section(
    key="prompts.system",
    label="System Prompt",
    description="The full system prompt defining the agent's role and behavior",
    validation={"format": "markdown", "max_length": 5000},
)
def get_system_prompt() -> str:
    return (
        "You are a friendly, encouraging, expert public speaking coach. "
        "Your role is to guide users through a structured public speaking curriculum, one model per week.\n\n"
        "CORE BEHAVIOUR:\n"
        "1. When the user asks for this week's model or starts a new session, FIRST call the load tool "
        "with path 'curriculum' to load the full curriculum, then present the relevant model.\n"
        "2. BEFORE giving any feedback on a script, call the load tool with path 'feedback-guidelines' "
        "to load the feedback rules, then apply them strictly.\n"
        "3. Always structure feedback in two sections: '✅ What's Working' and '🔧 Areas to Improve'.\n"
        "4. When a user resubmits a revised script, acknowledge improvements from the previous version first.\n"
        "5. When a script fully meets all model criteria, say exactly: 'Your script is ready — well done!' "
        "then call advance_model to move to the next model.\n"
        "6. Call get_progress when the user asks about their journey or how they are doing.\n"
        "7. Stay focused — you evaluate scripts against model criteria only, not general writing quality.\n"
        "8. If a script is off-topic, politely redirect to the current model's criteria.\n"
        "9. IMPORTANT: Never hallucinate data. Always ground feedback in the specific criteria of the "
        "current week's model as loaded from the curriculum skill."
    )


# ─── Tool schemas ─────────────────────────────────────────────────────────────


class GetProgressInput(BaseModel):
    context_id: str = Field(description="The conversation context identifier")


class AdvanceModelInput(BaseModel):
    context_id: str = Field(description="The conversation context identifier")


# ─── Tool implementations ────────────────────────────────────────────────────


async def _get_progress(context_id: str) -> str:
    """Return a summary of the user's progress through the curriculum."""
    session = _get_session(context_id)
    current_model = CURRICULUM[session["model_index"]] if session["model_index"] < len(CURRICULUM) else "Completed all models"
    mastered = session["mastered_models"]
    return (
        f"Current week: {session['week']}\n"
        f"Current model: {current_model}\n"
        f"Script iterations this model: {session['iteration_count']}\n"
        f"Models mastered: {len(mastered)} ({', '.join(mastered) if mastered else 'none yet'})"
    )


async def _advance_model(context_id: str) -> str:
    """Advance the user to the next model after mastering the current one."""
    session = _get_session(context_id)
    current_model = CURRICULUM[session["model_index"]] if session["model_index"] < len(CURRICULUM) else None

    if current_model and current_model not in session["mastered_models"]:
        session["mastered_models"].append(current_model)

    session["iteration_count"] = 0
    session["week"] += 1
    session["model_index"] += 1

    if session["model_index"] < len(CURRICULUM):
        next_model = CURRICULUM[session["model_index"]]
        return f"Congratulations! You have mastered '{current_model}'. Next week's model is: {next_model}."
    else:
        return "Amazing work! You have completed the entire public speaking curriculum. You are ready to speak with confidence!"


def _build_agent_tools(context_id: str) -> list[StructuredTool]:
    """Build the agent's custom tools for a given context_id."""

    async def get_progress_fn(context_id: str = context_id) -> str:  # noqa: N803
        return await _get_progress(context_id)

    async def advance_model_fn(context_id: str = context_id) -> str:  # noqa: N803
        return await _advance_model(context_id)

    get_progress_tool = StructuredTool(
        name="get_progress",
        description="Get the user's progress through the public speaking curriculum. Returns current week, current model, iteration count, and mastered models.",
        args_schema=BaseModel,
        coroutine=get_progress_fn,
    )

    advance_model_tool = StructuredTool(
        name="advance_model",
        description="Advance the user to the next public speaking model after they have mastered the current one. Call this when the user's script meets all criteria.",
        args_schema=BaseModel,
        coroutine=advance_model_fn,
    )

    return [get_progress_tool, advance_model_tool]


# ─── Milestone helpers ────────────────────────────────────────────────────────


def _log_milestone_achieved(milestone_id: str, message: str) -> None:
    logger.info("%s.achieved: %s", milestone_id, message)


def _log_milestone_missed(milestone_id: str, message: str) -> None:
    logger.warning("%s.missed: %s", milestone_id, message)


# ─── Response dataclass ───────────────────────────────────────────────────────


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


# ─── Main Agent ───────────────────────────────────────────────────────────────


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._primary_model = get_model_name()
        self._fallback_model = get_fallback_model_name().strip()
        self._temperature = get_temperature()

        self.llm = ChatLiteLLM(model=self._primary_model, temperature=self._temperature)
        self._fallback_llm = (
            ChatLiteLLM(model=self._fallback_model, temperature=self._temperature)
            if self._fallback_model
            else None
        )

        self._checkpointer = MemorySaver()
        self._summarization_middleware = SummarizationMiddleware(
            model=self.llm,
            trigger=("tokens", 100_000),
            keep=("messages", 4),
        )

    def _create_graph(
        self,
        llm: ChatLiteLLM,
        tools: Sequence[BaseTool],
        system_prompt: str,
    ) -> CompiledStateGraph:
        return create_agent(
            llm,
            tools=list(tools),
            system_prompt=system_prompt,
            checkpointer=self._checkpointer,
            middleware=[self._summarization_middleware],
        )

    async def _invoke_with_fallback(
        self,
        tools: Sequence[BaseTool],
        system_prompt: str,
        query: str,
        context_id: str,
    ) -> dict[str, Any]:
        config = {"configurable": {"thread_id": f"{get_user_sub()}:{context_id}"}}
        messages = {"messages": [HumanMessage(content=query)]}

        try:
            graph = self._create_graph(self.llm, tools, system_prompt)
            return await graph.ainvoke(messages, config)
        except (APIConnectionError, APIError, Timeout) as primary_error:
            if not self._fallback_llm:
                raise
            logger.warning(
                "Primary model '%s' failed. Retrying with fallback model '%s'. Error: %s",
                self._primary_model,
                self._fallback_model,
                primary_error,
            )

        graph = self._create_graph(self._fallback_llm, tools, system_prompt)
        result = await graph.ainvoke(messages, config)
        logger.info(
            "Request completed with fallback model '%s' after primary model '%s' failed.",
            self._fallback_model,
            self._primary_model,
        )
        return result

    async def _run_agent(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool],
    ) -> str:
        """Core agent business logic — instrumented with milestones and OTel spans."""
        session = _get_session(context_id)
        model_index = session["model_index"]
        week = session["week"]
        current_model = CURRICULUM[model_index] if model_index < len(CURRICULUM) else "Completed"

        # Detect if this looks like a model/intro request
        query_lower = query.lower()
        is_model_request = any(
            kw in query_lower
            for kw in ["this week", "week", "model", "start", "begin", "what should", "show me"]
        )
        # Detect script submission (longer text or contains speech-like content)
        is_script_submission = len(query.strip().split()) > 20 or any(
            kw in query_lower for kw in ["script", "draft", "speech", "here is", "here's", "feedback"]
        )

        with tracer.start_as_current_span("run_agent") as span:
            span.set_attribute("model", current_model)
            span.set_attribute("week", week)

            # M1 — Model delivery
            if is_model_request:
                with tracer.start_as_current_span("m1_model_delivery"):
                    try:
                        system_prompt = get_system_prompt()
                        result = await self._invoke_with_fallback(
                            tools=tools,
                            system_prompt=system_prompt,
                            query=query,
                            context_id=context_id,
                        )
                        response = result["messages"][-1].content
                        _log_milestone_achieved(
                            "M1",
                            f"weekly model delivered — model={current_model}, week={week}",
                        )
                        return response
                    except Exception:
                        _log_milestone_missed("M1", f"model delivery did not complete — week={week}")
                        raise

            # M2/M3/M4 — Script submission and feedback
            if is_script_submission:
                session["iteration_count"] += 1
                iteration = session["iteration_count"]

                with tracer.start_as_current_span("m2_script_submission"):
                    _log_milestone_achieved(
                        "M2",
                        f"script submitted — model={current_model}, iteration={iteration}",
                    )

                with tracer.start_as_current_span("m3_feedback"):
                    try:
                        system_prompt = get_system_prompt()
                        result = await self._invoke_with_fallback(
                            tools=tools,
                            system_prompt=system_prompt,
                            query=query,
                            context_id=context_id,
                        )
                        response = result["messages"][-1].content
                        _log_milestone_achieved(
                            "M3",
                            f"feedback delivered — model={current_model}, iteration={iteration}",
                        )
                    except Exception:
                        _log_milestone_missed(
                            "M3",
                            f"feedback generation failed — model={current_model}",
                        )
                        raise

                # M4 — iteration (second+ submission)
                if iteration > 1:
                    with tracer.start_as_current_span("m4_script_iteration"):
                        _log_milestone_achieved(
                            "M4",
                            f"script iterated — model={current_model}, iteration={iteration}",
                        )

                # M5 — model mastered (detected via LLM response content)
                if "your script is ready" in response.lower():
                    with tracer.start_as_current_span("m5_model_mastered"):
                        _log_milestone_achieved(
                            "M5",
                            f"model mastered — model={current_model}, total_iterations={iteration}",
                        )

                return response

            # General conversation (progress queries, greetings, off-topic)
            system_prompt = get_system_prompt()
            result = await self._invoke_with_fallback(
                tools=tools,
                system_prompt=system_prompt,
                query=query,
                context_id=context_id,
            )
            return result["messages"][-1].content

    async def stream(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AsyncGenerator[dict, None]:
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing...",
        }

        try:
            system_prompt = get_system_prompt()
            all_tools: list[BaseTool] = list(tools or [])
            all_tools.extend(_build_agent_tools(context_id))

            if not all_tools:
                system_prompt += "\n\nIMPORTANT: No tools are currently available. Do not attempt to call any tools."

            tool_names = [tool.name for tool in all_tools]
            logger.info("Running agent with %d tool(s): %s", len(tool_names), tool_names)

            response = await self._run_agent(query, context_id, all_tools)

            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }

        except Exception:
            logger.exception("Agent stream() failed")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": "I encountered an error while processing your request. Please try again.",
            }

    async def invoke(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AgentResponse:
        last: dict = {}
        async for chunk in self.stream(query, context_id, tools=tools):
            last = chunk
        if last.get("is_task_complete"):
            return AgentResponse(status="completed", message=last["content"])
        if last.get("require_user_input"):
            return AgentResponse(status="input_required", message=last["content"])
        return AgentResponse(
            status="error", message=last.get("content", "Unknown error")
        )
