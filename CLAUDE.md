# CLAUDE.md - Technical Notes for LLM Council

This file contains technical details, architectural decisions, and important implementation notes for future development sessions.

## Project Overview

LLM Council is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions. The key innovation is anonymized peer review in Stage 2, preventing models from playing favorites.

The app shell also hosts **JD Creator**, an unrelated second workflow (guided job-description drafting for HR) built on the same frontend/backend — see the "JD Creator Backend" and "JD Creator Wizard Frontend" sections below. The two features share infra (FastAPI app, CORS, port config) but not domain logic.

## Architecture

### Backend Structure (`backend/`)

**`config.py`**
- Contains `COUNCIL_MODELS` (list of OpenRouter model identifiers)
- Contains `CHAIRMAN_MODEL` (model that synthesizes final answer)
- Uses environment variable `OPENROUTER_API_KEY` from `.env`
- Backend runs on **port 8001** (NOT 8000 - user had another app on 8000)

**`openrouter.py`**
- `query_model()`: Single async model query
- `query_models_parallel()`: Parallel queries using `asyncio.gather()`
- Returns dict with 'content' and optional 'reasoning_details'
- Graceful degradation: returns None on failure, continues with successful responses

**`council.py`** - The Core Logic
- `stage1_collect_responses()`: Parallel queries to all council models
- `stage2_collect_rankings()`:
  - Anonymizes responses as "Response A, B, C, etc."
  - Creates `label_to_model` mapping for de-anonymization
  - Prompts models to evaluate and rank (with strict format requirements)
  - Returns tuple: (rankings_list, label_to_model_dict)
  - Each ranking includes both raw text and `parsed_ranking` list
- `stage3_synthesize_final()`: Chairman synthesizes from all responses + rankings
- `parse_ranking_from_text()`: Extracts "FINAL RANKING:" section, handles both numbered lists and plain format
- `calculate_aggregate_rankings()`: Computes average rank position across all peer evaluations

**`storage.py`**
- JSON-based conversation storage in `data/conversations/`
- Each conversation: `{id, created_at, messages[]}`
- Assistant messages contain: `{role, stage1, stage2, stage3}`
- Note: metadata (label_to_model, aggregate_rankings) is NOT persisted to storage, only returned via API

**`main.py`**
- FastAPI app with CORS enabled for localhost:5173 and localhost:3000
- POST `/api/conversations/{id}/message` returns metadata in addition to stages
- Metadata includes: label_to_model mapping and aggregate_rankings

### JD Creator Backend (`backend/jd*.py`)

A second, independent feature sharing the same FastAPI app and CORS config: HR staff at Aditya Birla Group use a guided wizard to draft structured, Hay-methodology job descriptions instead of starting from a blank document. See "JD Creator Wizard Frontend" below for the UI.

- **`jd_config.py`**: Static config (LOB options, dropdown option lists, per-LOB org context templates, min/max thresholds) served to the frontend via `GET /api/jd/config`.
- **`jd.py`**: API routes under `/api/jd` — draft CRUD, per-step autosave (`PATCH /steps/{step_key}`), generate, Excel template download/upload.
- **`jd_storage.py`**: Postgres-backed draft storage (primary).
- **`jd_db.py`**: asyncpg connection pool + schema bootstrap.
- **`jd_local_storage.py`**: JSON-file fallback storage used when Postgres is unreachable (mirrors `storage.py`'s one-file-per-record pattern); the frontend shows an offline banner (`jd_offline_banner` in `App.jsx`) when this fallback is active. Design doc: `docs/superpowers/specs/2026-07-12-jd-creator-local-storage-fallback-design.md`.
- **`jd_excel.py`**: Generates/parses an Excel workbook (one sheet per wizard step) for bulk-filling a draft outside the UI.

### Frontend Structure (`frontend/src/`)

**`App.jsx`**
- Main orchestration: manages conversations list and current conversation
- Handles message sending and metadata storage
- Important: metadata is stored in the UI state for display but not persisted to backend JSON

**`components/ChatInterface.jsx`**
- Multiline textarea (3 rows, resizable)
- Enter to send, Shift+Enter for new line
- User messages wrapped in markdown-content class for padding

**`components/Stage1.jsx`**
- Tab view of individual model responses
- ReactMarkdown rendering with markdown-content wrapper

**`components/Stage2.jsx`**
- **Critical Feature**: Tab view showing RAW evaluation text from each model
- De-anonymization happens CLIENT-SIDE for display (models receive anonymous labels)
- Shows "Extracted Ranking" below each evaluation so users can validate parsing
- Aggregate rankings shown with average position and vote count
- Explanatory text clarifies that boldface model names are for readability only

**`components/Stage3.jsx`**
- Final synthesized answer from chairman
- Green-tinted background (#f0fff0) to highlight conclusion

**Styling (`*.css`)**
- Light mode theme (not dark mode)
- Primary color: Sky Blue `#21a6f1` (design token `--brand`, see `DESIGN.md`) — not the older `#4a90e2` some pre-rebrand code still had hardcoded; if you find that literal value anywhere, it's stale and should be replaced with `var(--brand)`.
- Global markdown styling in `index.css` with `.markdown-content` class
- 12px padding on all markdown content to prevent cluttered appearance

### JD Creator Wizard Frontend (`frontend/src/components/jd/`, `frontend/src/jdApi.js`)

- **`JdWizard.jsx`**: shell — left rail (LOB tag, delete button, stepper with per-step completion/error state from `JdValidation.js`), main content area, footer (Back / Clear / Save Draft / Next). Autosaves the active step 800ms after the last edit (`AUTOSAVE_DELAY_MS`).
- 8 step components (`JdStep*.jsx`), one per `config.wizard_steps` key: Basics, Purpose, Dimensions, Context, Accountabilities, Reports, Hay, SignOff.
- **Content-layout patterns** (established in a 2026-07-15 content-restructure pass — reuse these before inventing new ones):
  - `.jd-field-group` / `.jd-field-group-heading`: clusters related fields under a quiet mono-uppercase label instead of one flat field grid. Used in `JdStepBasics` (Role Identity & Position IDs / Location & Org Placement / Reporting Line) and the Reports sub-panels.
  - `.jd-subnav-tablist` / `.jd-subnav-tab` (+ `.jd-subnav-tab-error-dot`): a step-internal tab bar showing one dense sub-section at a time instead of stacking all of them on one long scroll. Keyboard-accessible (arrow-key roving tabindex). Used in `JdStepHay` (Know-How / Decision-Making / Problem Solving), `JdStepReports` (Direct Reports / Internal / External Relationships), and `JdStepContext` (Context / Key Challenges). Each tab shows an error dot when validation flags a field inside it — see the `sectionHasError`/`factorHasError` helpers in those three files.
  - `.jd-field-row-2`: explicit 50/50-width row for two fields that must sit side by side regardless of viewport width, unlike `.jd-field-grid`'s auto-fit columns (used for e.g. Financial Approval Limit + Advisory vs Final Authority in Hay).
  - `.jd-table` headers use the brand-wash pastel-blue background with a bordered, rounded-top-corner treatment (`border-collapse: separate` on `.jd-table`) rather than the plain grey/paper background used elsewhere.
  - Tables scroll with the page, not internally — an internal per-table `overflow-y` scroll container was tried and explicitly reverted per user feedback, so don't reintroduce it without asking first.
- **`JdValidation.js`**: plain-JS validators mirroring `_validate_for_generate` in `backend/jd.py` — keep the two in sync manually (no shared-language validation library).
- **`jdApi.js`**: API client, same `API_BASE` pattern as `api.js` (localhost:8001 in dev, deployed URL in prod).

## Key Design Decisions

### Stage 2 Prompt Format
The Stage 2 prompt is very specific to ensure parseable output:
```
1. Evaluate each response individually first
2. Provide "FINAL RANKING:" header
3. Numbered list format: "1. Response C", "2. Response A", etc.
4. No additional text after ranking section
```

This strict format allows reliable parsing while still getting thoughtful evaluations.

### De-anonymization Strategy
- Models receive: "Response A", "Response B", etc.
- Backend creates mapping: `{"Response A": "openai/gpt-5.1", ...}`
- Frontend displays model names in **bold** for readability
- Users see explanation that original evaluation used anonymous labels
- This prevents bias while maintaining transparency

### Error Handling Philosophy
- Continue with successful responses if some models fail (graceful degradation)
- Never fail the entire request due to single model failure
- Log errors but don't expose to user unless all models fail

### UI/UX Transparency
- All raw outputs are inspectable via tabs
- Parsed rankings shown below raw text for validation
- Users can verify system's interpretation of model outputs
- This builds trust and allows debugging of edge cases

## Important Implementation Details

### Relative Imports
All backend modules use relative imports (e.g., `from .config import ...`) not absolute imports. This is critical for Python's module system to work correctly when running as `python -m backend.main`.

### Port Configuration
- Backend: 8001 (changed from 8000 to avoid conflict)
- Frontend: 5173 (Vite default)
- Update both `backend/main.py` and `frontend/src/api.js` if changing

### Markdown Rendering
All ReactMarkdown components must be wrapped in `<div className="markdown-content">` for proper spacing. This class is defined globally in `index.css`.

### Model Configuration
Models are hardcoded in `backend/config.py`. Chairman can be same or different from council members. The current default is Gemini as chairman per user preference.

## Common Gotchas

1. **Module Import Errors**: Always run backend as `python -m backend.main` from project root, not from backend directory
2. **CORS Issues**: Frontend must match allowed origins in `main.py` CORS middleware
3. **Ranking Parse Failures**: If models don't follow format, fallback regex extracts any "Response X" patterns in order
4. **Missing Metadata**: Metadata is ephemeral (not persisted), only available in API responses

## Future Enhancement Ideas

- Configurable council/chairman via UI instead of config file
- Streaming responses instead of batch loading
- Export conversations to markdown/PDF
- Model performance analytics over time
- Custom ranking criteria (not just accuracy/insight)
- Support for reasoning models (o1, etc.) with special handling

## Testing Notes

Use `test_openrouter.py` to verify API connectivity and test different model identifiers before adding to council. The script tests both streaming and non-streaming modes.

## Data Flow Summary

```
User Query
    ↓
Stage 1: Parallel queries → [individual responses]
    ↓
Stage 2: Anonymize → Parallel ranking queries → [evaluations + parsed rankings]
    ↓
Aggregate Rankings Calculation → [sorted by avg position]
    ↓
Stage 3: Chairman synthesis with full context
    ↓
Return: {stage1, stage2, stage3, metadata}
    ↓
Frontend: Display with tabs + validation UI
```

The entire flow is async/parallel where possible to minimize latency.

## Design Context

`PRODUCT.md` and `DESIGN.md` at the project root capture the app's strategic and visual design system (register: product, platform: web), maintained via the `impeccable` skill (`.claude/skills/impeccable/`). Read them before design-related work — `DESIGN.md` wins on visual decisions, `PRODUCT.md` on strategic/voice decisions. Run `/impeccable` for the full command menu (`critique`, `polish`, `live`, etc.).
