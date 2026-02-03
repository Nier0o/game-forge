# Game Forge Docker Setup

This directory handles the containerization of the Game Forge platform.

## Quick Start

To run the full stack (Frontend + Backend + Database) from the project root:

### Windows (PowerShell)
```powershell
docker-compose -f docker/docker-compose.yml up --build
```

## Management Commands

Run these commands from the project root directory.

| Action | Command |
|--------|---------|
| Start (Background) | `docker-compose -f docker/docker-compose.yml up -d` |
| Stop | `docker-compose -f docker/docker-compose.yml down` |
| View Logs | `docker-compose -f docker/docker-compose.yml logs -f` |
| Rebuild Images | `docker-compose -f docker/docker-compose.yml build --no-cache` |

## Architecture

1. **Frontend (`gameforge-frontend`)**
   - **Port**: 3000
   - **Hot Reloading**: Enabled via volume mount.

2. **Backend (`gameforge-backend`)**
   - **Port**: 5000
   - **Hot Reloading**: Enabled via volume mount.

3. **Database (`mongo`)**
   - **Port**: 27017
   - **Persistence**: Data is stored in the `mongo-data` Docker volume.
   - **Note**: Data is local to your machine. It is not shared with other developers.

## Hybrid Development

For better performance and faster UI iteration, you can run the Database and Backend in Docker, while running the Frontend locally.

1. **Start Backend & Database Only**:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d backend mongo
   ```

2. **Run Frontend Locally**:
   Refer to the main `README.md` for instructions on setting up the `.env` file and running `npm start`.
