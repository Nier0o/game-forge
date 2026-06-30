# Docker Compose Smoke Check (Optional)

This optional smoke check is **separate from the default unit and integration
test suites**. It is not run by `npm test`, `npm run test:unit`,
`npm run test:integration`, or `pytest`. Use it only when you want a quick
end-to-end confirmation that the containerized stack boots and every service
answers its health endpoint.

It does **not** exercise live LLM providers (Groq/OpenRouter), Stability AI, or
a full Godot HTML5 export. Godot export is disabled via `SKIP_GODOT_EXPORT=true`.

## Command

From the `game-forge/` directory:

```powershell
pwsh ./scripts/docker-smoke-check.ps1
```

Equivalent manual invocation:

```powershell
$env:SKIP_GODOT_EXPORT = 'true'
docker compose up -d --build
# probe the endpoints below, then:
docker compose down
```

Pass `-KeepUp` to leave the stack running after the probes:

```powershell
pwsh ./scripts/docker-smoke-check.ps1 -KeepUp
```

## Smoke Scope

The script verifies the following and is intentionally limited to startup +
health wiring:

| Check | Target |
| ----- | ------ |
| Compose service startup | `docker compose up -d --build` (with `SKIP_GODOT_EXPORT=true`) |
| Backend health | `GET http://localhost:5000/api/health` |
| Orchestrator health | `GET http://localhost:6100/health` |
| Planner health | `GET http://localhost:6101/health` |
| Asset health | `GET http://localhost:6102/health` |
| Code health | `GET http://localhost:6103/health` |
| Builder health | `GET http://localhost:6104/health` |
| MinIO health | `GET http://localhost:9000/minio/health/live` |
| Mongo container running | `docker inspect -f '{{.State.Running}}' game-forge-mongo` |

The `server`, `planner`, `asset`, `code`, `builder`, and `minio` services also
declare Compose-level `healthcheck` blocks in `docker-compose.yml`, so
`docker compose ps` will additionally report their health status.

## Out of Scope (by design)

The following are deliberately excluded from the default smoke check and require
separate, explicitly approved runs:

- Live LLM calls (Groq / OpenRouter) — paid/quota-bound and non-deterministic.
- Live Stability AI image/audio generation — paid/quota-bound.
- Full Godot HTML5 export — slow and environment-sensitive; gated behind
  `SKIP_GODOT_EXPORT`.
- Real asset/game generation through the full pipeline.

To run the builder against a real Godot CLI, set `SKIP_GODOT_EXPORT=false` and
ensure a Godot binary is available at `GODOT_PATH` inside the builder image.
