# Public Speaking Coach Agent

Interactive AI coaching agent that teaches public speaking through weekly models, script practice, and iterative feedback.

## Business challenge

Users want to improve their public speaking skills in an interactive, self-paced way. Each week, a new public speaking model (e.g. Monroe's Motivated Sequence, PREP, Minto Pyramid) is introduced. Users submit their own scripts based on the model, receive structured positive and improvement feedback from the agent, and can iterate their scripts multiple times until satisfied.

## Key Milestones

1. **Weekly Model Delivered** – User receives and acknowledges a new public speaking model with explanation and examples.
2. **Script Submitted** – User submits a script attempt based on the current week's model.
3. **Feedback Provided** – Agent delivers structured feedback (positive highlights + improvement areas).
4. **Script Iterated** – User revises and resubmits; agent re-evaluates the updated version.
5. **Model Mastered** – User completes at least one approved iteration and is ready for the next week's model.

## Business Architecture (RBA)

### End-to-End Process

Recruit to Retire (Develop to Grow)

### Process Hierarchy

```
Recruit to Retire (E2E)
└── Develop to Grow (Phase)
    └── Educate and develop talent (BPS-388)
        └── Develop skills and competencies
```

### Summary

The coaching agent maps to the "Educate and develop talent" sub-process within the Recruit to Retire E2E. The iterative script feedback loop aligns with developing skills and competencies through practice and continuous improvement.

## Fit Gap Analysis

| Requirement | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Gap? | Notes |
|---|---|---|---|---|---|---|
| Weekly public speaking model delivery | SAP SuccessFactors Learning (Training Management) | `sap.sf:apiResource:SuccessionandDevelopmentSD:v1` | — | — | Yes | SF Learning covers structured training but not conversational weekly model coaching |
| Script submission & AI feedback | SAP SuccessFactors (Continuous Feedback) | — | — | — | Yes | No standard product provides AI-driven script analysis and iterative coaching |
| Iterative improvement loop | SAP SuccessFactors Opportunity Marketplace (Social Learning) | — | — | — | Yes | Collaboration features exist but not an agent-driven iteration loop |
| Progress tracking per user | SAP SuccessFactors Learning (Compliance Training Mgmt) | — | — | — | Maybe | Basic tracking possible in SF Learning; deep coaching history requires custom logic |

### Key findings

- No standard SAP product provides interactive AI-driven public speaking coaching with script analysis.
- SAP SuccessFactors Learning covers structured training management but not conversational or iterative script feedback.
- The core value of this solution — personalized, iterative AI feedback on user-submitted scripts — requires a custom AI Agent.
- A Python-based AI Agent using SAP AI Core (LLM) is the best fit for open-ended reasoning, context retention across sessions, and dynamic feedback generation.
- Weekly model scheduling can be handled within the agent's session/memory logic without a separate workflow engine.
- No relevant MCP servers were found for this use case; the agent will use SAP AI Core as its LLM backbone.

## Recommendations

### AI-Powered Public Speaking Coach Agent

#### Executive Summary

Custom AI agent delivering weekly models, script feedback, and iteration coaching.

#### Recommended Solution

A Python-based AI Agent built on SAP AI Core that:
- Maintains a curriculum of public speaking models (e.g. PREP, Monroe's Motivated Sequence, Minto Pyramid, STAR) and delivers one per week to the user.
- Accepts user-submitted scripts and evaluates them against the current week's model.
- Provides structured feedback with clear positive highlights and specific, actionable improvement suggestions.
- Supports unlimited script iterations — each revision is re-evaluated with updated feedback.
- Tracks the user's progress across weeks and models within the agent's memory/context.

#### Recommended solution category

AI Agent

#### Intent fit
95%
