# AI Transfer Planner

AI Transfer Planner is a full-stack application for helping California Community College students plan transfers to University of California and California State University campuses.

The project currently contains the Phase 0 foundation: a FastAPI backend, a React + TypeScript + Vite frontend, a local health-check connection between them, and basic backend tests.

## Requirements

- macOS
- Python 3.11 or newer
- Node.js 18 or newer
- npm

## Backend setup

From the repository root, create and activate a Python virtual environment:

```bash
cd "AI-Transfer-Planner"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload --app-dir backend
```

The backend runs at <http://localhost:8000>. The health endpoint is available at <http://localhost:8000/health>.

Stop the backend with `Control+C` in the terminal running Uvicorn.

## Frontend setup

Open a second Terminal window, then run:

```bash
cd "frontend"
npm install
npm run dev
```

The frontend normally runs at <http://localhost:5173>. It calls the backend `/health` endpoint and displays the returned status.

Stop the frontend with `Control+C` in the terminal running Vite.

## Running backend tests

With the virtual environment activated:

```bash
PYTHONPATH=backend python -m pytest backend/tests
```

## Optional frontend API configuration

The frontend defaults to `http://localhost:8000`. To use another local backend URL, create `frontend/.env.local`:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Do not put secrets in frontend environment variables. Vite exposes variables beginning with `VITE_` to browser code.
