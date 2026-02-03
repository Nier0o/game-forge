# Game Forge

Game Forge is a web platform that generates simple playable games from natural language prompts using AI and the Godot engine.

## Project Structure

```
game-forge/
├── backend/    # Node.js + Express API
├── frontend/   # React + Vite UI (Tailwind CSS)
├── docker/     # Docker configuration files
├── godot/      # Godot engine projects
├── mcp-server/ # Model Context Protocol server
└── scripts/    # Utility scripts
```

## Architecture & Services

### 1. Frontend
- **Path**: `/frontend`
- **Tech Stack**: React, Vite, Tailwind CSS
- **Port**: 3000 (Docker), 5173 (Local)
- **Role**: User interface for prompting and playing games.

### 2. Backend
- **Path**: `/backend`
- **Tech Stack**: Node.js, Express, Puppeteer
- **Port**: 5000
- **Role**: Orchestrates requests, manages database, and handles AI/Godot pipelines.

### 3. Database
- **Type**: MongoDB
- **Port**: 27017
- **Role**: Stores user profiles, prompts, and game metadata. Data is persisted in a Docker volume.

## Quick Start (Docker)

To run the full stack (Frontend + Backend + Database):

```bash
docker-compose -f docker/docker-compose.yml up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:5000/api/v1/health

## Development Workflow

### 1. Backend & Database
These services are best run via Docker to ensure environment consistency.

```bash
docker-compose -f docker/docker-compose.yml up --build
```

### 2. Frontend (Local Development)
For faster iteration with Hot Module Replacement (HMR), run the frontend locally.

1. Ensure Backend is running (via Docker).
2. Create a `.env` file in the `frontend` folder:
   ```env
   VITE_API_URL=http://localhost:5000
   ```
3. Run the development server:
   ```bash
   cd frontend
   npm install
   npm start
   ```
4. Access at http://localhost:5173

## Current Progress

- [x] Backend: Initial setup, Dockerized, Database connection.
- [x] Frontend: React app initialized, connected to Backend.
- [x] Infrastructure: Docker Compose for orchestration.
- [ ] AI Engine: (Pending)
- [ ] Godot Engine: (Pending)
- [ ] MCP Server: (Pending)
