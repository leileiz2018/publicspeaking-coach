# Product Requirements Document (PRD)

**Title:** Public Speaking Coach Agent  
**Date:** 2026-08-05  
**Owner:** Product Owner  
**Solution Category:** AI Agent

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Most people struggle with public speaking but lack an accessible, personalized coach. This agent delivers weekly public speaking models directly to the user, accepts their practice scripts, and provides detailed, iterative feedback — acting as a patient personal coach available anytime.

**Business Need:**  
Public speaking is a critical professional skill yet most employees receive no structured coaching. Traditional training is expensive, infrequent, and not personalized. This agent fills that gap with a conversational, self-paced learning experience.

**Expected Value:**  
- Users develop structured public speaking skills progressively, one model per week.
- Each user receives personalized, actionable feedback rather than generic advice.
- Users can iterate scripts as many times as needed without waiting for a human coach.

**Product Objectives:**
1. Deliver one public speaking model per week in a clear, engaging format.
2. Provide structured, personalized feedback (positive + improvement) on every script submission.
3. Support unlimited script iterations per model until the user is satisfied.
4. Track user progress across weeks and models within the session context.

## Requirements

### Must-Have Requirements

**R1: Weekly Model Delivery**
- **User Story**: As a learner, I need to receive a new public speaking model each week so that I progressively build my skills with a structured curriculum.
- **Acceptance Criteria**:
  - Given a new week begins or the user asks for this week's model, the agent presents the model name, core principles, a brief explanation, and a worked example.
  - The agent covers a sequenced curriculum (e.g. PREP, Monroe's Motivated Sequence, Minto Pyramid, STAR, SBI, Rule of Three, etc.).
- **Priority Rank:** 1

**R2: Script Submission & Evaluation**
- **User Story**: As a learner, I need to submit my own script based on the current week's model so that I can practice applying the framework in my own words.
- **Acceptance Criteria**:
  - Given a user submits a script, the agent evaluates it against the current week's model criteria.
  - The agent clearly identifies which elements of the model are well applied.
- **Priority Rank:** 2

**R3: Structured Feedback**
- **User Story**: As a learner, I need to receive balanced feedback with specific positive highlights and clear improvement suggestions so that I know what I am doing well and what to change.
- **Acceptance Criteria**:
  - Feedback always contains a "What's working" section and an "Areas to improve" section.
  - Improvement suggestions are specific and actionable (e.g. "Your opening lacks a hook — try starting with a surprising statistic or a short story").
  - Feedback references the specific model criteria being evaluated.
- **Priority Rank:** 3

**R4: Iterative Script Revision**
- **User Story**: As a learner, I need to revise and resubmit my script multiple times so that I can refine my work until I feel confident.
- **Acceptance Criteria**:
  - The agent accepts any number of revised script submissions per model.
  - Each revision receives fresh feedback that acknowledges improvements from the previous version.
  - The agent signals when a script meets all model criteria ("Your script is ready — well done!").
- **Priority Rank:** 4

**R5: Progress Awareness**
- **User Story**: As a learner, I need to know which models I have completed and which is current so that I can track my journey.
- **Acceptance Criteria**:
  - The agent can tell the user which model they are on and how many they have completed when asked.
  - The agent congratulates the user when they move from one model to the next.
- **Priority Rank:** 5

## Solution Architecture

**Architecture Overview:**  
A Python-based AI Agent running on SAP AI Core. The agent maintains a built-in curriculum of public speaking models and manages the learner's session state (current week, model, iteration count). The LLM powers script evaluation and feedback generation.

**Key Components:**
- **AI Agent (Python, SAP AI Core)**: Core reasoning engine for model delivery, script evaluation, and feedback generation.
- **Curriculum Knowledge Base**: Built-in structured definitions of public speaking models with criteria and examples.
- **Session/Context Manager**: Tracks the user's current week, model, and iteration count within the conversation.

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The curriculum (model list and criteria) should be defined as a configurable data structure so new models can be added without code changes.
- Feedback tone and depth should be adjustable via system prompt configuration.

**Business Step Instrumentation:**
- All key milestones must emit structured log entries for observability.
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent (LLM-driven, conversational)

**Actions performed without human approval:**
- Delivering the weekly public speaking model.
- Evaluating a submitted script against model criteria.
- Generating positive and improvement feedback.
- Confirming script completion and advancing to the next model.

**Actions requiring human review:** None — this is a self-contained learning interaction.

**Model used:** SAP AI Core (LLM via SAP Generative AI Hub)

**Knowledge & data sources:**
- Built-in public speaking model curriculum (PREP, Monroe's Motivated Sequence, Minto Pyramid, STAR, SBI, Rule of Three, and others).
- User-submitted scripts (processed in-session, not persisted externally).

**Guardrails & fail-safes:**
- The agent only evaluates scripts in the context of the current week's model — it does not act as a general-purpose writing editor.
- If a script is off-topic, the agent politely redirects to the model's criteria.
- Feedback must always be constructive; the agent must not produce dismissive or discouraging responses.

## Milestones

### M1: Weekly Model Delivered
- **Description**: The agent successfully presents the current week's public speaking model to the user.
- **Achieved when**: The user receives the model explanation with principles and an example.
- **Log on achievement**: `M1.achieved: weekly model delivered — model=[model_name], week=[week_number]`
- **Log on miss**: `M1.missed: model delivery did not complete — week=[week_number]`

### M2: Script Submitted
- **Description**: The user submits a script attempt for the current week's model.
- **Achieved when**: A non-empty script is received and accepted for evaluation.
- **Log on achievement**: `M2.achieved: script submitted — model=[model_name], iteration=[iteration_count]`
- **Log on miss**: `M2.missed: no script submitted for model=[model_name]`

### M3: Feedback Provided
- **Description**: The agent delivers structured feedback on the submitted script.
- **Achieved when**: Both "What's working" and "Areas to improve" sections are delivered to the user.
- **Log on achievement**: `M3.achieved: feedback delivered — model=[model_name], iteration=[iteration_count]`
- **Log on miss**: `M3.missed: feedback generation failed — model=[model_name]`

### M4: Script Iterated
- **Description**: The user submits a revised version of their script after receiving feedback.
- **Achieved when**: A revised script is submitted and re-evaluated by the agent.
- **Log on achievement**: `M4.achieved: script iterated — model=[model_name], iteration=[iteration_count]`
- **Log on miss**: `M4.missed: user did not revise script after feedback — model=[model_name]`

### M5: Model Mastered
- **Description**: The user's script meets all criteria for the current model and they advance to the next.
- **Achieved when**: The agent confirms the script is complete and the user is ready for the next week's model.
- **Log on achievement**: `M5.achieved: model mastered — model=[model_name], total_iterations=[count]`
- **Log on miss**: `M5.missed: user did not complete model — model=[model_name]`
