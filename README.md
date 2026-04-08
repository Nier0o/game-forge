# Game Forge

A web platform that generates browser-playable games from natural language prompts. Describe a game, refine the design through an AI chat, and get back a real Godot 4 HTML5 export you can play in the browser or download.

## How It Works

1. User writes a prompt describing a game
2. An AI assistant (Groq LLM) converses with the user to refine the game design
3. A generation pipeline plans the game, generates assets and GDScript code, and exports it via Godot 4 headless
4. The exported HTML5 game is stored in MinIO and served back through the API

## Repository Layout

This monorepo contains three separate Git repositories and the Docker Compose orchestration:

```
game-forge/               ← you are here (orchestration)
├── docker-compose.yml    ← full-stack Docker Compose
└── docs/

game-forge-backend/       ← Node.js/Express REST API
game-forge-frontend/      ← React/Vite web UI
game-forge-server/        ← AI generation pipeline + Godot export
```

## Services

| Service  | Image / Source                                      | Port       | Description                        |
|----------|-----------------------------------------------------|------------|------------------------------------|
| backend  | `ghcr.io/game-forge-studio/game-forge-backend`      | 5000       | REST API, auth, game pipeline      |
| frontend | `ghcr.io/game-forge-studio/game-forge-frontend`     | 3000       | React UI                           |
| mongo    | `mongo:latest`                                      | 27017      | Database (persistent volume)       |
| minio    | `minio/minio:latest`                                | 9000, 9001 | Object storage for game exports    |

## Quick Start

### Prerequisites

- Docker Desktop

### 1. Configure environment

Create `game-forge-backend/.env` (see [backend README](../game-forge-backend/README.md) for all variables):

```env
JWT_SECRET=your_jwt_secret_here
JWT_EXPIRES_IN=90d
JWT_COOKIE_EXPIRES_IN=90
GROQ_API_KEY=your_groq_api_key
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

Create `game-forge-frontend/.env`:

```env
VITE_API_URL=http://localhost:5000/api
VITE_BACKEND_URL=http://localhost:5000
```

### 2. Run

```bash
cd game-forge
docker compose up
```

| URL                          | What                        |
|------------------------------|-----------------------------|
| http://localhost:3000        | Web UI                      |
| http://localhost:5000/api/health | Backend health check    |
| http://localhost:9001        | MinIO console               |

## Tech Stack

| Layer       | Technology                                          |
|-------------|-----------------------------------------------------|
| Frontend    | React 18, Vite, Tailwind CSS 4                      |
| Backend     | Node.js, Express 4, Mongoose 8                      |
| Auth        | JWT (jsonwebtoken), bcryptjs                        |
| Database    | MongoDB                                             |
| Storage     | MinIO (S3-compatible)                               |
| LLM         | Groq SDK (game design chat)                         |
| Game engine | Godot 4.2.1 (headless HTML5 export)                 |
| Security    | Helmet, express-rate-limit, xss-clean, mongo-sanitize, CORS allowlist |

## Current Status

The platform scaffolding is complete:
- User auth, project management, and chat are fully working
- Docker orchestration, Godot export pipeline infrastructure, and MinIO storage are in place
- The generation pipeline (game-forge-server) handles AI planning, asset generation, code generation, and Godot export
