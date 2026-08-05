# Specification: public-speaking-coach-agent

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-agent.md](../guidelines-agent.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read the project input (`product-requirements-document.md`, `intent.md`)
- [x] Bootstrap agent code in `assets/public-speaking-coach-agent/` using skill `sap-agent-bootstrap` (invoke from inside `assets/public-speaking-coach-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

## Curriculum Knowledge Base

- [x] Create `assets/public-speaking-coach-agent/app/skills/curriculum/SKILL.md` as a runtime skill with:
  - Frontmatter: `name: curriculum`, `description: Public speaking model curriculum with structured definitions, criteria, and examples`
  - Body: Full definitions for at least 6 models in order: PREP, Monroe's Motivated Sequence, Minto Pyramid, STAR, SBI, Rule of Three
  - Each model must include: name, core principles (bullet list), evaluation criteria, and a worked example
- [x] Create `assets/public-speaking-coach-agent/app/skills/feedback-guidelines/SKILL.md` as a runtime skill with:
  - Frontmatter: `name: feedback-guidelines`, `description: Rules for generating constructive, structured feedback on public speaking scripts`
  - Body: Feedback structure rules — always include "What's working" section and "Areas to improve" section; be specific and actionable; reference the model criteria; never be dismissive

## Agent System Prompt & Core Logic

- [x] In `assets/public-speaking-coach-agent/app/agent.py`, update the `@prompt_section` to define the agent's persona and behaviour:
  - Persona: friendly, encouraging, expert public speaking coach
  - Behaviour rules:
    1. On session start or when asked, present the current week's model using the curriculum runtime skill
    2. Accept user-submitted scripts and evaluate them against the current model's criteria
    3. Always provide feedback in two sections: "What's working" and "Areas to improve"
    4. Improvement suggestions must be specific and actionable, referencing the model criteria
    5. On re-submission, acknowledge improvements from the previous version before giving new feedback
    6. When a script fully meets all model criteria, congratulate the user and offer to advance to the next model
    7. Track current week number and model in conversation context
    8. If the user asks for their progress, state which model they are on and how many they have completed
    9. Never act as a general writing editor — stay focused on the public speaking model criteria
    10. If a script is off-topic, redirect politely to the current model's criteria
    11. Instruction: never hallucinate data; always ground feedback in the criteria of the current model
- [x] Implement the `_run_agent()` async helper that encapsulates all business logic (model delivery, script evaluation, feedback generation, progress tracking) — the `stream()` method calls this helper and yields results; no business logic in `stream()` directly

## Business Step Instrumentation (Milestones)

- [x] Instrument M1 (Weekly Model Delivered): emit `M1.achieved: weekly model delivered — model=[model_name], week=[week_number]` when the model explanation is delivered; emit `M1.missed: model delivery did not complete — week=[week_number]` on failure
- [x] Instrument M2 (Script Submitted): emit `M2.achieved: script submitted — model=[model_name], iteration=[iteration_count]` when a non-empty script is accepted; emit `M2.missed: no script submitted for model=[model_name]` when user ends session without submitting
- [x] Instrument M3 (Feedback Provided): emit `M3.achieved: feedback delivered — model=[model_name], iteration=[iteration_count]` after both feedback sections are generated; emit `M3.missed: feedback generation failed — model=[model_name]` on error
- [x] Instrument M4 (Script Iterated): emit `M4.achieved: script iterated — model=[model_name], iteration=[iteration_count]` on resubmission; emit `M4.missed: user did not revise script after feedback — model=[model_name]` when session ends without revision
- [x] Instrument M5 (Model Mastered): emit `M5.achieved: model mastered — model=[model_name], total_iterations=[count]` when script meets all criteria; emit `M5.missed: user did not complete model — model=[model_name]` when session ends before completion
- [x] Add OpenTelemetry custom spans for each milestone inside `_run_agent()` using decorator or context manager form (never inside `stream()` generator)
- [x] Verify `auto_instrument()` is called at top of `main.py` before any AI framework imports

## Session State & Progress Tracking

- [x] Implement session state tracking (current week number, current model index, iteration count per model, list of mastered models) using in-memory storage scoped to `context_id`
- [x] Expose a `get_progress()` tool that returns current week, current model name, and count of mastered models — the agent invokes this tool when the user asks about their progress
- [x] Implement `advance_model()` logic: when M5 is achieved, increment week number and model index; reset iteration count

## Delete Template Skill

- [x] Delete the template runtime skill: `rm -rf assets/public-speaking-coach-agent/app/skills/template-skill/`

## Testing

- [x] `conftest.py` only sets `IBD_TESTING=true` — this causes the agent to run with mock MCP tool results during tests
- [x] Write unit test for `get_progress()` tool — run immediately after writing
- [x] Write unit test for `advance_model()` logic — run immediately after writing
- [x] Write unit test for milestone instrumentation (M1–M5 log emissions) — run immediately after writing
- [x] Write one integration test executing end-to-end agent flow: submit a script → receive feedback → resubmit → receive improved feedback → complete model — use real LLM via AI Core env vars; mock no external non-AI systems (none exist)
- [x] Run `pytest` from `assets/public-speaking-coach-agent/` (no args, no extra flags — `pytest.ini` configures everything) — if coverage < 70%, add tests until threshold met
- [x] Verify `assets/public-speaking-coach-agent/app/agent.py` has exactly 5 decorated functions — run `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/public-speaking-coach-agent/app/agent.py` and confirm it returns 5
- [x] Run `pytest` again from `assets/public-speaking-coach-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/public-speaking-coach-agent/` — if not, run pytest again until it does
