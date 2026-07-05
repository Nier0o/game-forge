# Game Forge Presentation PPTX Design

## Goal

Create an editable PowerPoint version of the existing `GameForge_Presentation.html` deck that imports cleanly into Canva, while expanding the microservices section and adding a compact mention of the 10 planner evaluation criteria on the existing component benchmark slide.

## Source Material

- Root `GameForge_Presentation.html` provides the current story, slide order, visual theme, screenshots, embedded charts, and existing architecture/pipeline narrative.
- Root `Final_Doc.docx` and `game-forge/docs/Final_Doc.docx` provide system design, service catalogue, implementation details, testing, and performance evaluation text.
- Repositories under the stack root provide verification for service ports, responsibilities, environment variables, authentication, and pipeline sequencing.
- Existing benchmark assets in `game-forge/benchmarks/report_assets` and `game-forge/benchmarks/results` provide chart imagery where needed.

## Output

- Generate `GameForge_Presentation.pptx` in the stack root.
- Keep the deck editable in PowerPoint and Canva: text as text boxes, diagrams as shapes/connectors, tables as table/text structures, and screenshots/charts as images.
- Preserve the current presentation's core theme: warm paper background, dark text, molten orange primary accent, blue secondary accent, card-based technical explanations, and compact engineering-oriented language.

## Deck Structure

The PPTX should follow the current HTML presentation narrative:

1. Title
2. Problem
3. Motivation
4. User scenario
5. Proposed solution
6. System architecture
7. Generation pipeline
8. Why not just ask an AI?
9. Systems engineering
10. Final product
11. Expanded microservices section
12. Component evaluation
13. Production evaluation
14. Lessons learned
15. Future work
16. Demo
17. Thank you

The exact slide count can differ from the HTML if needed for readability, but the story should remain consistent.

## Microservices Expansion

The microservices section should be stronger than the current two-card-per-service version. It should explain both decomposition and process.

Add or improve slides covering:

- Service catalogue: frontend, backend, server/orchestrator, planner, asset, code, builder, assets-mcp, MongoDB, and MinIO with ports and responsibilities.
- Request flow: user prompt to backend, orchestrator, planner, parallel asset/code branch, builder join point, backend completion, browser play/download.
- Communication model: REST between services, private Docker bridge network, shared MongoDB state, shared MinIO file handoff, and no direct file streaming between services.
- Authentication and security: user-facing JWT auth, internal `x-gen-service-secret`, backend sanitization/rate limiting where space allows.
- Failure isolation: planner fallback plans, asset placeholders or retry opportunities, code validation, builder timeout/stub mode.
- Per-service slides with concise technical details:
  - Frontend: React workspace, chat refinement, progress polling, browser game iframe.
  - Backend: REST API, JWT auth, MongoDB models, MinIO proxy.
  - Server: stateless orchestrator, pipeline state updates through backend, no local persistent state.
  - Planner: two-stage LLM classification and schema fill, JSON cleanup, validation, fallback plan.
  - Asset: tool-free LLM prompt generation, deterministic MCP tool invocation order.
  - Code: template-guided deterministic GDScript assembly from validated fragments.
  - Builder: temp Godot workspace, asset/script download from MinIO, headless import/export, HTML5 upload.
  - Assets MCP: FastMCP tools, Pydantic validation, Stability Image/Audio wrapping, sprite background removal.
  - Data tier: MongoDB as state store, MinIO as object handoff layer.

## Diagrams

Use editable PPTX shapes where practical:

- Architecture diagram: three tiers, service boxes, Docker bridge network, MongoDB, MinIO, and external Stability AI APIs.
- Pipeline diagram: planning, parallel asset/code branch, builder join point, final browser play/download.
- Storage/state handoff diagram: MongoDB documents for status and metadata, MinIO objects for scripts/assets/builds, services exchanging references instead of large files.

If a diagram becomes too dense for editability, keep the layout simple rather than embedding a non-editable screenshot.

## Planner Evaluation Criteria

On the component benchmark slide, briefly mention all 10 planner quality criteria in the same slide:

- `valid_archetype`
- `correct_archetype`
- `has_title`
- `one_player`
- `min_entities`
- `all_described`
- `valid_win_cond`
- `valid_theme`
- `valid_style`
- `has_audio`

Keep the slide readable by placing these as a compact strip, two-row tag list, or small side panel next to the existing planner latency/quality metrics.

## Implementation Approach

Use a local script, preferably Node.js with `pptxgenjs`, to generate the PPTX deterministically from structured slide definitions. This makes the deck reproducible and easier to adjust later.

The script should:

- Define reusable theme constants for colors, fonts, slide dimensions, and spacing.
- Provide helpers for title slides, section headers, cards, stat blocks, service badges, simple connectors, and diagram boxes.
- Reuse existing images/charts when available and preserve aspect ratios.
- Keep all deck text selectable/editable.
- Avoid reliance on browser-only HTML animation behavior.

## Verification

After generation:

- Confirm the PPTX file exists and is non-empty.
- Inspect basic slide count and media relationships with a lightweight ZIP/XML check.
- Open or parse the PPTX enough to confirm it contains editable text runs, not only slide screenshots.
- Validate the file structure with available local tooling; at minimum, confirm the PPTX ZIP package opens and exposes expected `ppt/slides` XML files.

## Out of Scope

- Rebuilding every HTML animation from the source deck.
- Creating a perfect pixel match to the HTML presentation.
- Changing the underlying project code or service behavior.
- Updating the written final documentation unless a direct factual mismatch blocks the deck.
