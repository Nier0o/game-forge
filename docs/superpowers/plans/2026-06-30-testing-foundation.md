# Game Forge Testing Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish deterministic unit and integration testing across the Game Forge multi-service stack without calling paid APIs, production databases, production object storage, or full Godot export by default.

**Architecture:** Add per-service test tooling and scripts first, then implement unit tests for deterministic utilities and service logic, then add service-level HTTP integration tests. External systems are mocked in default suites; Docker-level checks are limited to optional smoke coverage after deterministic suites pass.

**Tech Stack:** Vitest, Supertest, `@vitest/coverage-v8`, React Testing Library, jsdom, pytest, pytest-asyncio, pytest-cov, mocked `fetch`, mocked Mongoose/MinIO/Godot/MCP/Stability/LLM clients.

---

## Approval Gate

This plan is not an approval to implement tests. Test files, test dependencies, package-lock updates, pytest configuration, and test execution must wait until explicit approval is given.

## Strategy Mapping

| Strategy Requirement | Plan Coverage |
| -------------------- | ------------- |
| Unit tests first | Tasks 2 through 7 create unit tests before any integration suite. |
| Integration tests second | Tasks 8 through 11 add Supertest and limited service integration tests after unit coverage. |
| Mock paid/external services | Every service task defines mocks for LLMs, Stability AI, MCP, MinIO, MongoDB, Godot, and inter-service HTTP. ||
| Low-risk, high-value first | The order starts with utilities, validators, route validation, and mocked service clients before broader orchestration. |
| Update section 6.2 with real results | Task 13 updates `game-forge/docs/6-testing-and-evaluation.md` only after verification commands run. |

## Implementation Order Overview

| Required Order | Plan Task |
| -------------- | --------- |
| 1. Establish test tooling and scripts | Task 1 |
| 2. Add unit tests for pure utilities and deterministic services | Tasks 2 and 5 |
| 3. Add unit tests for controllers, route handlers, and service clients with mocks | Tasks 3 and 4 |
| 4. Add frontend unit/component tests | Task 6 |
| 5. Add Python MCP unit tests | Task 7 |
| 6. Add integration tests for HTTP routes and service boundaries | Tasks 8, 9, and 10 |
| 7. Add broader Docker-based integration tests only where practical | Task 11 |
| 8. Run verification commands | Task 12 |
| 9. Update section 6.2 with actual results | Task 13 |

## Framework Choices

| Subproject | Framework | Justification |
| ---------- | --------- | ------------- |
| `game-forge-backend` | Vitest + Supertest + `@vitest/coverage-v8` | Express/Mongoose service needs mocking and LCOV. Vitest aligns with the existing orchestrator setup. |
| `game-forge-server` | Existing Vitest + Supertest, add coverage script | Already has Vitest/Supertest dependencies; add tests and coverage only. |
| `game-forge-planner` | Vitest + Supertest + `@vitest/coverage-v8` | Route contracts plus provider/model mocks; LCOV coverage output. |
| `game-forge-asset` | Vitest + Supertest + `@vitest/coverage-v8` | MCP/provider/storage mocks are simpler with Vitest module mocking. |
| `game-forge-code` | Vitest + Supertest + `@vitest/coverage-v8` | Existing test script references missing files; Vitest gives consistent mocks and coverage. |
| `game-forge-builder` | Vitest + Supertest + `@vitest/coverage-v8` | Convert existing SFX test from `node:test` to Vitest for consistent coverage and mocking. |
| `game-forge-frontend` | Vitest + React Testing Library + jsdom + `@vitest/coverage-v8` | Native fit for Vite/React 18. |
| `assets-mcp` | pytest + pytest-asyncio + pytest-cov | Standard Python unit/async testing stack with coverage. |
| `game-forge/` root | No default live benchmark tests | Existing scripts call live Groq APIs; keep them separate from deterministic automated tests. |

## Dependencies to Add After Approval

| Subproject | Dev/Test Dependencies |
| ---------- | --------------------- |
| Backend | `vitest`, `supertest`, `@vitest/coverage-v8`, optionally `mongodb-memory-server` for selected persistence integration tests. |
| Server | `@vitest/coverage-v8` only, because `vitest` and `supertest` already exist. |
| Planner | `vitest`, `supertest`, `@vitest/coverage-v8`. |
| Asset | `vitest`, `supertest`, `@vitest/coverage-v8`. |
| Code | `vitest`, `supertest`, `@vitest/coverage-v8`. |
| Builder | `vitest`, `supertest`, `@vitest/coverage-v8`. |
| Frontend | `vitest`, `@vitest/coverage-v8`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`. |
| Python MCP | `pytest`, `pytest-asyncio`, `pytest-cov` in `requirements-dev.txt`. |

Lockfiles must be updated when dependencies are added.

## Files to Create or Modify After Approval

### Documentation

- Modify: `game-forge/docs/6-testing-and-evaluation.md`
  - Update section 6.2 with actual results after verification.

### Backend

- Modify: `game-forge-backend/package.json`
- Modify: `game-forge-backend/package-lock.json`
- Modify: `game-forge-backend/eslint.config.js`
- Create: `game-forge-backend/vitest.config.js`
- Create: `game-forge-backend/test/setup/env.js`
- Create: `game-forge-backend/test/unit/middleware/validate.test.js`
- Create: `game-forge-backend/test/unit/middleware/serviceAuth.test.js`
- Create: `game-forge-backend/test/unit/utils/appError.test.js`
- Create: `game-forge-backend/test/unit/utils/catchAsync.test.js`
- Create: `game-forge-backend/test/unit/models/generationJob.test.js`
- Create: `game-forge-backend/test/unit/models/build.test.js`
- Create: `game-forge-backend/test/unit/models/user.test.js`
- Create: `game-forge-backend/test/unit/controllers/authController.test.js`
- Create: `game-forge-backend/test/unit/controllers/chatController.test.js`
- Create: `game-forge-backend/test/unit/controllers/gameController.test.js`
- Create: `game-forge-backend/test/unit/controllers/internalController.test.js`
- Create: `game-forge-backend/test/integration/app.routes.test.js`

### Server Orchestrator

- Modify: `game-forge-server/package.json`
- Modify: `game-forge-server/package-lock.json`
- Modify: `game-forge-server/eslint.config.js`
- Create: `game-forge-server/vitest.config.js`
- Create: `game-forge-server/test/setup/env.js`
- Create: `game-forge-server/test/unit/services/serviceClient.test.js`
- Create: `game-forge-server/test/unit/services/backendClient.test.js`
- Create: `game-forge-server/test/unit/controllers/generateController.test.js`
- Create: `game-forge-server/test/unit/pipeline.test.js`
- Create: `game-forge-server/test/integration/app.routes.test.js`

### Planner

- Modify: `game-forge-planner/package.json`
- Modify: `game-forge-planner/package-lock.json`
- Modify: `game-forge-planner/eslint.config.js`
- Create: `game-forge-planner/vitest.config.js`
- Create: `game-forge-planner/test/setup/env.js`
- Create: `game-forge-planner/test/unit/utils/extractJson.test.js`
- Create: `game-forge-planner/test/unit/utils/retry.test.js`
- Create: `game-forge-planner/test/unit/middleware/serviceAuth.test.js`
- Create: `game-forge-planner/test/unit/controllers/planController.test.js`
- Create: `game-forge-planner/test/unit/services/plannerService.test.js`
- Create: `game-forge-planner/test/integration/app.routes.test.js`

### Asset Service

- Modify: `game-forge-asset/package.json`
- Modify: `game-forge-asset/package-lock.json`
- Modify: `game-forge-asset/eslint.config.js`
- Modify, only if needed for testable helper extraction: `game-forge-asset/src/services/assetService.js`
- Create: `game-forge-asset/vitest.config.js`
- Create: `game-forge-asset/test/setup/env.js`
- Create: `game-forge-asset/test/unit/utils/extractJson.test.js`
- Create: `game-forge-asset/test/unit/utils/retry.test.js`
- Create: `game-forge-asset/test/unit/middleware/serviceAuth.test.js`
- Create: `game-forge-asset/test/unit/models/asset.test.js`
- Create: `game-forge-asset/test/unit/controllers/assetsController.test.js`
- Create: `game-forge-asset/test/unit/services/assetService.test.js`
- Create: `game-forge-asset/test/integration/app.routes.test.js`

### Code Service

- Modify: `game-forge-code/package.json`
- Modify: `game-forge-code/package-lock.json`
- Modify: `game-forge-code/eslint.config.js`
- Create: `game-forge-code/vitest.config.js`
- Create: `game-forge-code/test/setup/env.js`
- Create: `game-forge-code/test/unit/utils/extractJson.test.js`
- Create: `game-forge-code/test/unit/utils/retry.test.js`
- Create: `game-forge-code/test/unit/pipeline/parameterFiller.test.js`
- Create: `game-forge-code/test/unit/pipeline/seedrng.test.js`
- Create: `game-forge-code/test/unit/pipeline/hookInjector.test.js`
- Create: `game-forge-code/test/unit/pipeline/hookValidator.test.js`
- Create: `game-forge-code/test/unit/pipeline/behaviorValidator.test.js`
- Create: `game-forge-code/test/unit/pipeline/behaviorComposer.test.js`
- Create: `game-forge-code/test/unit/pipeline/weaponComposer.test.js`
- Create: `game-forge-code/test/unit/pipeline/archetypeLoader.test.js`
- Create: `game-forge-code/test/unit/controllers/codeController.test.js`
- Create: `game-forge-code/test/integration/app.routes.test.js`

### Builder

- Modify: `game-forge-builder/package.json`
- Modify: `game-forge-builder/package-lock.json`
- Modify: `game-forge-builder/eslint.config.js`
- Modify: `game-forge-builder/test/sfx.test.js`
- Create: `game-forge-builder/vitest.config.js`
- Create: `game-forge-builder/test/setup/env.js`
- Create: `game-forge-builder/test/unit/middleware/serviceAuth.test.js`
- Create: `game-forge-builder/test/unit/controllers/buildController.test.js`
- Create: `game-forge-builder/test/unit/services/godotService.test.js`
- Create: `game-forge-builder/test/unit/services/builderService.test.js`
- Create: `game-forge-builder/test/integration/app.routes.test.js`

### Frontend

- Modify: `game-forge-frontend/package.json`
- Modify: `game-forge-frontend/package-lock.json`
- Modify: `game-forge-frontend/eslint.config.js`
- Modify: `game-forge-frontend/vite.config.js` or create `game-forge-frontend/vitest.config.js`
- Create: `game-forge-frontend/src/test/setup.js`
- Create: `game-forge-frontend/src/utils/api/config.test.js`
- Create: `game-forge-frontend/src/utils/api.test.js`
- Create: `game-forge-frontend/src/features/workspace/workspaceUtils.test.js`
- Create: `game-forge-frontend/src/contexts/auth/authStorage.test.js`
- Create: `game-forge-frontend/src/pages/auth/hooks/useAuthForm.test.jsx`
- Create: `game-forge-frontend/src/components/ProtectedRoute.test.jsx`
- Create: `game-forge-frontend/src/components/chat/ChatInput.test.jsx`
- Create: `game-forge-frontend/src/components/chat/Message.test.jsx`
- Create: `game-forge-frontend/src/features/workspace/useBuildPolling.test.jsx`
- Create: `game-forge-frontend/src/features/workspace/useOptimisticChat.test.jsx`

### Python MCP

- Create: `assets-mcp/requirements-dev.txt`
- Create: `assets-mcp/pytest.ini`
- Create: `assets-mcp/tests/conftest.py`
- Create: `assets-mcp/tests/test_prompts.py`
- Create: `assets-mcp/tests/test_audio.py`
- Create: `assets-mcp/tests/test_schemas.py`
- Create: `assets-mcp/tests/test_minio_storage.py`
- Create: `assets-mcp/tests/test_tools_generate_background.py`
- Create: `assets-mcp/tests/test_tools_generate_sprite.py`
- Create: `assets-mcp/tests/test_tools_generate_music.py`
- Create: `assets-mcp/tests/test_mcp_server.py`

## Task 1: Establish Test Tooling and Scripts

- [ ] Add JavaScript test dependencies to each service listed above.
- [ ] Add frontend testing dependencies.
- [ ] Add Python dev requirements.
- [ ] Add or update `test`, `test:unit`, `test:integration`, and `test:coverage` scripts for JavaScript services.
- [ ] Fix `game-forge-code/package.json` so `npm test` no longer points at missing test files.
- [ ] Add Vitest configs that include:

```js
export default {
  test: {
    environment: 'node',
    globals: true,
    setupFiles: ['./test/setup/env.js'],
    include: ['test/**/*.test.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      reportsDirectory: './coverage',
    },
  },
};
```

- [ ] Use a jsdom test environment for frontend tests.
- [ ] Update ESLint configs to allow test globals only in test files, for example `globals: { ...globals.node, ...globals.vitest }` where applicable.
- [ ] For Python, add `pytest.ini` with async mode and test path configuration:

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

- [ ] Do not run tests until dependencies and scripts are in place.

Commands after implementation:

```powershell
npm install --save-dev vitest supertest @vitest/coverage-v8
npm install --save-dev vitest @vitest/coverage-v8 jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
python -m pip install -r requirements-dev.txt
```

The exact `npm install` command must be run from each relevant service directory so the correct `package-lock.json` is updated.

## Task 2: Add Unit Tests for Shared Deterministic Utilities

- [ ] Test `extractJson` in planner, asset, and code services with raw JSON, fenced JSON, surrounding prose, fallback values, empty input, and invalid input.
- [ ] Test `withRetry` in planner, asset, and code services with success on first try, retry then success, non-retryable failure, invalid function, and invalid tries.
- [ ] Test code pipeline utilities:
  - `fillSlots` coercion, defaults, min/max clamping, string escaping, missing slot errors.
  - `seedrng` deterministic output, integer bounds, choice selection, weighted selection, zero-weight fallback.
  - `injectHooks` replacement, indentation preservation, and `pass` fallback.
  - `validateHookSnippet` allowed identifiers, forbidden patterns, length failures, and string/comment stripping.
  - `validateCustomBehaviorRegistry` valid behavior, invalid names, invalid attach types, missing required behavior functions, and denied tokens.
- [ ] Keep tests independent of MinIO, Godot, LLM providers, and filesystem writes unless the utility explicitly reads local archetype files.

## Task 3: Add Unit Tests for Model Methods and Middleware

- [ ] Backend model unit tests:
  - `GenerationJob.start`, `advanceStep`, `addLog`, `fail`, and `complete`.
  - `Build.complete` and `Build.fail`.
  - `User.changedPasswordAfter` and `comparePassword` with bcrypt mocked or a real hash in memory.
- [ ] Middleware tests:
  - `requireServiceAuth` permits dev with no secret, rejects bad secret, permits matching secret, and returns 503 in production without a secret.
  - Backend `validateBody` trims valid strings and rejects missing, wrong type, too short, and too long fields.
  - `catchAsync` forwards rejected promises.
- [ ] App error and token helper tests with controlled `JWT_SECRET` and `JWT_EXPIRES_IN`.

## Task 4: Add Unit Tests for Controllers and Service Clients

- [ ] Backend controller tests should mock models, LLM service, storage service, and `fetch`.
- [ ] Worker controller tests should validate required fields and service errors:
  - planner `postPlan`
  - asset `postAssets`
  - code `postCode`
  - builder `postBuild`
- [ ] Server controller tests should verify `/generate` returns 400 for missing fields and 202 for valid input while dispatching `runPipeline`.
- [ ] Service client tests:
  - `game-forge-server/src/services/serviceClient.js` should attach JSON headers, optional `x-gen-service-secret`, stringify body, parse JSON/text/empty responses, and throw enriched errors.
  - `backendClient` should call the correct `/internal/*` paths and propagate errors.
  - `game-forge-builder/src/services/backendClient.js` should post complete/fail payloads and parse backend errors.

## Task 5: Add Unit Tests for Code Assembly and Builder Behavior

- [ ] Test `composeEntity` with built-in behavior injection, parameter filling, marker replacement, unknown behavior errors, and incompatible attach errors.
- [ ] Test `composeWeapon` with valid weapon composition, no-weapon marker clearing, unknown weapon errors, and missing source errors.
- [ ] Test `archetypeLoader` with real local archetype manifests, cache clearing, valid IDs, and unknown ID errors.
- [ ] Convert existing builder `test/sfx.test.js` to Vitest while preserving every current assertion.
- [ ] Test `godotService` by mocking `child_process.spawn` for success, non-zero exit, spawn error, stdout/stderr capture, and timeout behavior.
- [ ] Test `builderService.runBuild` with mocked storage, mocked backend client, and skipped/mocked Godot:
  - downloads project files,
  - writes fallback assets,
  - copies library SFX,
  - uploads HTML5 artifacts,
  - marks build complete,
  - marks build failed when storage or output verification fails.

## Task 6: Add Frontend Unit and Component Tests

- [ ] Test `getAuthHeaders`, `fetchApi`, and `api` wrapper request construction with mocked `fetch` and `localStorage`.
- [ ] Test unauthorized responses dispatch `auth:unauthorized`.
- [ ] Test `authStorage` against mocked jsdom `localStorage`.
- [ ] Test `workspaceUtils` for empty build state and absolute game URL conversion.
- [ ] Test `useAuthForm` login/signup mode behavior, validation errors, loading state, and success callback.
- [ ] Test `ProtectedRoute` loading, unauthenticated redirect, and authenticated render behavior inside a memory router.
- [ ] Test `ChatInput` send button, Enter behavior, confirm button, and build button state using a mocked `WorkspaceContext`.
- [ ] Test `useBuildPolling` with fake timers for ready, failed, retry cutoff, interval backoff, and cleanup.
- [ ] Test `useOptimisticChat` for optimistic append, success replacement, rollback, typing toggles, and error message.

## Task 7: Add Python MCP Unit Tests

- [ ] Add prompt helper tests for style hints, asset-type hints, negative prompt extension, slug generation, and audio prompt composition.
- [ ] Add audio format tests for MP3, WAV, OGG, FLAC, and unknown bytes.
- [ ] Add Pydantic schema tests for valid defaults and invalid widths/heights/duration/steps.
- [ ] Add MinIO storage tests with `minio.Minio` monkeypatched:
  - bucket creation path,
  - object key with and without `game_id`,
  - URL generation with SSL and non-SSL,
  - unique filename extension handling.
- [ ] Add tool tests with monkeypatched provider clients and storage:
  - `generate_background` success and provider failure.
  - `generate_sprite` success including background removal and provider failure.
  - `generate_music` success including format detection fallback and provider failure.
- [ ] Add MCP wrapper tests by calling `generate_background`, `generate_sprite`, and `generate_music` wrapper functions directly with Pydantic input objects and monkeypatched underlying tool functions.

## Task 8: Add Backend Integration Tests

- [ ] Use Supertest against `src/app.js`.
- [ ] Set deterministic test env in setup.
- [ ] Cover:
  - `/api/health`,
  - unknown route 404 envelope,
  - protected route without token,
  - auth signup/login error envelopes,
  - project route validation,
  - chat route validation,
  - game status initializing response for unknown `gameId`,
  - internal service-auth rejection and accepted internal route shape.
- [ ] Use mocked models/services first. Add selected in-memory Mongo tests only if environment reliability is acceptable.

## Task 9: Add Orchestrator Integration Tests

- [ ] Use Supertest against `game-forge-server/src/app.js`.
- [ ] Cover:
  - `/health`,
  - 404 envelope,
  - service-auth rejection when `GEN_SERVICE_SECRET` is set,
  - production 503 when secret is missing,
  - `/generate` 400 validation,
  - `/generate` 202 accepted response with `runPipeline` mocked.
- [ ] Keep `runPipeline` success/failure sequencing in unit tests with mocked backend and worker clients.

## Task 10: Add Planner, Asset, Code, and Builder Route Integration Tests

- [ ] For each worker app, use Supertest against `src/app.js`.
- [ ] Cover `/health` without service auth.
- [ ] Cover unauthorized requests when `GEN_SERVICE_SECRET` is configured.
- [ ] Cover required field validation.
- [ ] Cover success envelope with the service implementation mocked:
  - planner returns `{ status: "ok", plan, planId }`,
  - asset returns `{ status: "ok", assets }`,
  - code returns `{ status: "ok", gameId, scriptKeys, archetype, seed }`,
  - builder returns `{ status: "ok", gameUrl, downloadUrl, artifacts }`.
- [ ] Cover service failure returning 500 envelope.

## Task 11: Add Limited Docker-Based Integration Checks Where Practical

- [ ] Keep Docker checks separate from the default unit/integration command.
- [ ] Document an optional smoke command using Docker Compose with `SKIP_GODOT_EXPORT=true`.
- [ ] Smoke scope:
  - compose service startup,
  - backend `/api/health`,
  - server `/health`,
  - planner/asset/code/builder `/health`,
  - MinIO health check,
  - Mongo container running.
- [ ] Do not add live LLM, Stability AI, or full Godot export to default CI.

## Task 12: Verification Commands

Run after implementation, from each service directory:

```powershell
npm run lint
npm run test:unit
npm run test:integration
npm run test:coverage
```

For the frontend:

```powershell
npm run lint
npm run test:unit
npm run test:coverage
npm run build
```

For Python MCP:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest --cov=app --cov-report=term-missing --cov-report=xml
```

For the orchestration root:

```powershell
npm run lint
npm test
```

## Task 13: Section 6.2 Results Update

- [ ] Open `game-forge/docs/6-testing-and-evaluation.md`.
- [ ] Replace pending result entries in section 6.2 with actual command outcomes.
- [ ] Include failed commands truthfully, with the failure reason and any unresolved limitation.
- [ ] Include coverage notes only from generated reports.
- [ ] Do not invent pass/fail status for commands that were not run.

## Risks and Fallback Options

| Risk | Fallback |
| ---- | -------- |
| `mongodb-memory-server` is slow or cannot download binaries. | Keep persistence integration mocked and add optional Docker Mongo smoke checks. |
| Vitest module mocking is blocked by import-time side effects. | Use dynamic imports after `vi.mock` and environment setup; extract small pure helpers only when it improves production clarity. |
| Builder tests import `SKIP_GODOT_EXPORT` before env is set. | Use `vi.resetModules()` and dynamic import after setting env in each builder test. |
| Python tests instantiate real MinIO storage through module globals. | Monkeypatch `app.storage._storage` and provider/storage clients before calling tools. |
| Frontend tests fail because of icon virtual imports. | Add Vitest aliases or lightweight mocks for `~icons/*` modules. |
| Coverage scripts expose currently untested code with low percentages. | Record baseline coverage first; introduce thresholds only after the foundation is stable. |
| Hosted static-analysis tooling is unavailable locally. | Run lint/test/coverage locally and record which local verification commands were executed. |

## Expected Final State After Approved Implementation

- Every service has deterministic unit tests.
- Express services have Supertest route integration tests.
- Frontend has Vitest/jsdom unit and component tests.
- Python MCP has pytest unit tests.
- JavaScript services can emit `coverage/lcov.info`.
- Python MCP can emit `coverage.xml`.
- Section 6.2 contains real command results and coverage notes.
- No default test calls live Groq, OpenRouter, Stability AI, MinIO, production MongoDB, or full Godot export.
