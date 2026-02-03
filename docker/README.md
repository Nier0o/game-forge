# Game Forge Docker Setup

This directory handles the containerization of the Game Forge platform.

## 🚀 Quick Start

To run the full stack (Frontend + Backend + Database):

**From the Project Root:**

### Windows (PowerShell)
```powershell
docker-compose -f docker/docker-compose.yml up --build
```

### Mac / Linux / Bash
```bash
docker-compose -f docker/docker-compose.yml up --build
```

## 🛠️ Management Commands

| Action | Command (from root) |
|--------|---------------------|
| **Start (Background)** | `docker-compose -f docker/docker-compose.yml up -d` |
| **Stop** | `docker-compose -f docker/docker-compose.yml down` |
| **View Logs** | `docker-compose -f docker/docker-compose.yml logs -f` |
| **Rebuild Images** | `docker-compose -f docker/docker-compose.yml build --no-cache` |

## 🏗️ Architecture

### Services
1.  **Frontend (`gameforge-frontend`)**
    *   **Port**: `3000`
    *   **Env**: `VITE_API_URL` is automatically set to `http://backend:5000`.
    *   **Hot Reloading**: Enabled via volume mount.

2.  **Backend (`gameforge-backend`)**
    *   **Port**: `5000`
    *   **Database**: Connects to `mongo` service internally.
    *   **Hot Reloading**: Enabled via `nodemon` and volume mount.

3.  **Database (`mongo`)**
    *   **Port**: `27017` (Exposed to host)
    *   **Persistence**: Data is stored in the `mongo-data` Docker volume.

## 💡 Hybrid Development
For better performance, you can run the database in Docker and the frontend locally.

1.  **Start DB & Backend Only**:
    ```bash
    docker-compose -f docker/docker-compose.yml up -d backend mongo
    ```
2.  **Run Frontend Locally**:
    (See `../frontend/README.md` or main README for details)
