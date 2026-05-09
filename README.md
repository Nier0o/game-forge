# Game Forge

Web platform that turns a natural-language prompt into a playable Godot 4 HTML5 game. A user describes a game; the system plans it, generates sprites + audio, writes GDScript, runs the Godot CLI, and serves the playable export back through the browser.

This folder is the **orchestration root** — Docker Compose bringing together 8 services from sibling repos.

## Architecture

```
                ┌───────────┐
                │ frontend  │ :3000   React UI
                └─────┬─────┘
                      │ /api/*
                ┌─────▼─────┐
                │  backend  │ :5000   REST API + auth + /internal
                └─────┬─────┘         owns User, Chat, GameProject,
                      │               GenerationJob, Build
                      │ POST /generate
                ┌─────▼─────┐
                │  server   │ :6100   Orchestrator (HTTP only,
                └─────┬─────┘         no DB, no storage)
        ┌─────────────┼──────────────┬──────────────┐
        │             │              │              │
   ┌────▼────┐  ┌─────▼─────┐  ┌─────▼────┐  ┌─────▼─────┐
   │ planner │  │   asset   │  │   code   │  │  builder  │
   │  :6101  │  │   :6102   │  │  :6103   │  │   :6104   │
   │  Groq   │  │ Groq +    │  │  Groq +  │  │  Godot +  │
   │GamePlan │  │ canvas +  │  │  MinIO ↗ │  │  MinIO ↘  │
   │         │  │ Asset doc │  │ (scripts)│  │ (export)  │
   └────┬────┘  └─────┬─────┘  └──────────┘  └─────┬─────┘
        │             │                            │ updates Build
        │             │                            │ via backend /internal
        └─────────────┴────────────────────────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
            ┌─────▼─────┐           ┌─────▼─────┐
            │   mongo   │ :27017    │   minio   │ :9000 / :9001
            └───────────┘           └───────────┘
```

## Service catalogue

| Service  | Port  | Image                  | Purpose                              |
|----------|-------|------------------------|--------------------------------------|
| frontend | 3000  | game-forge-frontend    | React UI                             |
| backend  | 5000  | game-forge-backend     | REST API, auth, canonical models     |
| server   | 6100  | game-forge-server      | Stateless HTTP orchestrator          |
| planner  | 6101  | game-forge-planner     | LLM → GamePlan                       |
| asset    | 6102  | game-forge-asset       | Sprites, backgrounds, sound (canvas) |
| code     | 6103  | game-forge-code        | GDScript generation → MinIO          |
| builder  | 6104  | game-forge-builder     | Godot CLI export → MinIO             |
| mongo    | 27017 | mongo:latest           | Database                             |
| minio    | 9000/9001 | minio/minio:latest | S3-compatible object storage         |

## Quick start

Requires **Docker Desktop**.

```bash
# 1. Copy env templates and fill in secrets
cp game-forge/.env.example game-forge/.env       # not present yet — see below
cp game-forge-backend/.env.example game-forge-backend/.env
cp game-forge-frontend/.env.example game-forge-frontend/.env
cp game-forge-server/.env.example  game-forge-server/.env

# 2. Edit game-forge/.env to set GROQ_API_KEY (and optionally per-agent providers)

# 3. Bring up the stack
cd game-forge
docker compose up -d --build
```

| URL                              | What                       |
|----------------------------------|----------------------------|
| http://localhost:3000            | Frontend                   |
| http://localhost:5000/api/health | Backend health             |
| http://localhost:6100/health     | Orchestrator health        |
| http://localhost:6101–6104/health| Worker services            |
| http://localhost:9001            | MinIO console (gameforge / change-me-in-production) |

## Key environment variables

`game-forge/.env` is the **compose interpolation file**. Compose substitutes `${VAR}` references in `docker-compose.yml` from it.

| Var                              | Default                | Purpose |
|----------------------------------|------------------------|---------|
| `GEN_SERVICE_SECRET`             | empty                  | Inter-service auth header. Empty disables auth (dev-friendly). |
| `GROQ_API_KEY`                   | empty                  | Required when any `_PROVIDER` is `groq`. |
| `PLANNER_PROVIDER` / `_MODEL`    | groq / qwen3-32b       | LLM for game design (only `groq` supported) |
| `CODER_PROVIDER` / `_MODEL`      | groq / gpt-oss-120b    | LLM for GDScript |
| `THEME_PROVIDER` / `_MODEL`      | groq / qwen3-32b       | LLM for sprite/background JSON specs |
| `AUDIO_PROVIDER` / `_MODEL`      | groq / qwen3-32b       | LLM for sound effect JSON specs |
| `SKIP_GODOT_EXPORT`              | false                  | If `true`, builder writes stub artifacts (skips Godot — fast for orchestration testing) |
| `MINIO_ACCESS_KEY` / `_SECRET_KEY` | gameforge / change-me-in-production | Must match `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` set on the minio container in compose |

## Common operations

```bash
# Tail logs from one service
docker compose logs -f builder

# Restart a single service after editing its code
docker compose up -d --force-recreate --build planner

# Stop everything (volumes preserved)
docker compose down

# Nuke everything including mongo + minio data
docker compose down -v

# Inspect the inter-service network
docker network inspect game-forge_default
```

## Pipeline flow

When the user clicks "Generate" in the frontend:

1. Frontend → `POST /api/games/create-godot-game` (backend)
2. Backend creates `GameProject`, `GenerationJob`, `Build` and POSTs to `server:6100/generate`
3. Server returns 202 immediately and runs the pipeline in the background:
   - `planner-service` is called → returns `{ plan }`
   - `asset-service` and `code-service` run in parallel
     - asset uploads sprites/audio to MinIO + writes `Asset` docs
     - code uploads `.gd` files to MinIO at `${gameId}/godot-project/scripts/`
   - `builder-service` is called → downloads scripts + assets from MinIO, runs Godot, uploads HTML5 export to MinIO, calls backend `/internal/builds/:id/complete`
4. Server pushes status updates and logs to backend `/internal/jobs/:id/*` throughout
5. Frontend polls `GET /api/games/status/:gameId` to track progress

## Repository layout

```
GradProject/
├── game-forge/             ← orchestration (you are here)
├── game-forge-frontend/    ← React UI
├── game-forge-backend/     ← REST API + auth + canonical models
├── game-forge-server/      ← thin HTTP orchestrator
├── game-forge-planner/     ← planner microservice
├── game-forge-asset/       ← asset microservice
├── game-forge-code/        ← code microservice
└── game-forge-builder/     ← builder microservice
```

## Troubleshooting

- **`Error response from daemon: Conflict. The container name "/game-forge-mongo" is already in use`** — leftover container from a previous run. Run `docker compose down` first.
- **Builder fails with `wget exit code 5`** — SSL verification failure during Godot download; means `ca-certificates` is missing from the Dockerfile (already added).
- **Asset image build fails compiling `canvas`** — missing cairo/pango dev libs. Check `game-forge-asset/Dockerfile`.
- **Service exits with `MongoServerError`** — mongo isn't reachable; check `docker compose ps` for mongo's state and ensure `MONGODB_URL` points to `mongo:27017` from inside the network.
- **Plan generation hangs / 401** — `GROQ_API_KEY` missing or invalid in `game-forge/.env`. Check with `docker compose exec planner env | grep GROQ`.
