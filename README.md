# AI Transfer Planner

AI Transfer Planner is a full-stack application for helping California Community College students plan transfers to University of California and California State University campuses.

The project currently includes a Phase 1 student-profile workflow backed by PostgreSQL, SQLAlchemy, Alembic, FastAPI, and React.

## Requirements

- macOS
- Python 3.13 for the Phase 1 environment
- Node.js 20.19+ on the 20.x line, or 22.12+ (Node 24 is used locally)
- npm
- Docker Desktop with Docker Compose

## Backend setup

Phase 1 uses a Python 3.13 virtual environment at `backend/.venv313`. If you have an older environment from Phase 0 (for example `backend/.venv`), leave it in place; it is not used by Phase 1.

```bash
# From the directory containing your clone:
cd AI-Transfer-Planner
# Run only if backend/.venv313 does not already exist:
python3.13 -m venv backend/.venv313
source backend/.venv313/bin/activate
python -m pip install -r backend/requirements.txt
```

## PostgreSQL and environment configuration

For a new checkout, copy the example only if `.env` does not exist:

```bash
test -e .env || cp .env.example .env
```

For a new database, fill in the empty `POSTGRES_PASSWORD` and `DATABASE_URL` fields before starting PostgreSQL. The example deliberately cannot authenticate as supplied. Set `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`, and use matching credentials in `DATABASE_URL`. Percent-encode special characters in the URL's username/password (for example, `@` becomes `%40`, `%` becomes `%25`). The PostgreSQL password variable holds the original, unencoded password. Quote values in `.env` when necessary; keep this file private and never put credentials in `VITE_` variables.

For an existing database, **keep the current `.env` and credentials**. PostgreSQL initialization variables only configure a new, empty volume. Changing `.env` does not change the password stored inside an existing database. A future approved password rotation must update the PostgreSQL role password and both configuration values together, without deleting the volume. Avoid putting a password in shell history; the interactive `psql` command `\password` can be used during that separately approved operation.

FastAPI, Alembic, and the seed script read the repository-root `.env` automatically. An exported `DATABASE_URL` takes precedence; use `unset DATABASE_URL` if an old shell value overrides your file. No password fallback exists. Database operations require a complete `postgresql+psycopg` URL; `/` and `/health` remain database-independent liveness endpoints.

Start PostgreSQL with its database port bound only to the local machine:

```bash
docker compose up -d postgres
docker compose ps
```

The database uses the named Docker volume `transfer_planner_postgres_data`, so stopping the container does not remove local data.

Apply migrations and load the intentionally limited demonstration catalog:

```bash
PYTHONPATH=backend alembic upgrade head
PYTHONPATH=backend alembic check
PYTHONPATH=backend python backend/scripts/seed_demo_data.py
```

The demo catalog is not authoritative articulation or major-requirement data. Run migrations before seeding. Repeated seed runs retain existing records and IDs; database uniqueness and conflict handling prevent duplicate catalog entries, including concurrent runs.

Start the FastAPI development server:

```bash
PYTHONPATH=backend uvicorn app.main:app --reload
```

The backend runs at <http://localhost:8000>. The health endpoint is available at <http://localhost:8000/health>. Profile APIs are under `/api/v1`.

Stop the backend with `Control+C` in the terminal running Uvicorn.

## Frontend setup

Open a second Terminal window at the repository root, then run:

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

The frontend normally runs at <http://localhost:5173>. It shows the backend health status and the student profile form, which loads the demonstration catalog from the API. If the backend is healthy but the catalog fails to load, check that migrations and the seed script have been run.

Stop the frontend with `Control+C` in the terminal running Vite.

## Running backend tests

With the virtual environment activated:

```bash
PYTHONPATH=backend python -m pytest backend/tests
```

Backend tests use isolated in-memory SQLite databases with foreign-key enforcement and do not change development or production data. Coverage includes the original health/CORS tests, profile validation, campus/major matching, atomic rejection, uniqueness, seed repeatability, configuration, generated migration validity, and migration upgrade/downgrade checks. PostgreSQL integration verification is also performed against the local Docker service during development; SQLite tests alone do not prove PostgreSQL behavior.

Frontend checks (from `frontend/`):

```bash
npm run build
npm run lint
npm test
```

`npm test` runs Playwright browser regression tests in installed Google Chrome using a separate Vite server on port 5174. All API responses are mocked on port 18080, so no database is contacted. Tests cover stale campus responses, blocked overlapping saves, demo labeling, catalog-load failures, and readable validation errors. Test dependencies are development-only and installed by `npm ci`. Stop any service occupying port 5174 before running them; the test runner manages its own server.

## Student profile workflow

After starting both services, open the Vite URL shown in the frontend terminal, normally <http://localhost:5173>. Select a demonstration community college, target campus, major, and transfer term, then save the profile.

The current API supports:

- `GET /api/v1/institutions`
- `GET /api/v1/campuses`
- `GET /api/v1/majors?institution_id={id}`
- `POST /api/v1/student-profiles`
- `GET /api/v1/student-profiles/{id}`

Profiles are local development records and are not authenticated accounts.

Transfer terms accept Fall, Winter, Spring, or Summer and a year from 2000–2199. Whitespace and capitalization are normalized. This records a student's intention; it does not establish whether a campus accepts applications for that term. The API supports up to ten distinct campus/major pairs; the current form captures one pair. Repeated saves after a completed request create new records; the form prevents overlapping submissions, not intentional later saves.

## Database migrations

Create a new migration after changing models:

```bash
PYTHONPATH=backend alembic revision --autogenerate -m "describe the change"
```

Use `PYTHONPATH=backend alembic upgrade head` and `PYTHONPATH=backend alembic check` from the root. Revision `0002_unique_catalog_targets` adds unique campus/major names and unique target pairs within a profile. It preserves the original `0001_initial` migration and existing records. If duplicates already exist, it stops and requests review; it never silently removes or merges them. Rollbacks can remove schema or data, so review their impact before using them.

## Stopping the application

- Stop FastAPI and Vite with `Control+C` in their terminals.
- Stop PostgreSQL while preserving its data with:

```bash
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete the local database volume.

## Optional frontend API configuration

The frontend defaults to `http://localhost:8000`. To use another local backend URL, create `frontend/.env.local`:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Do not put secrets in frontend environment variables. Vite exposes variables beginning with `VITE_` to browser code.

## Product roadmap and schema decisions

The following requirements are accepted for future development; they are not implemented in Phase 1.

1. **Identity and privacy foundation:** support temporary guest browsing, academic history, target selection, and schedules without sign-in. Accounts will own persistent profiles, histories, university lists, schedules, and progress across devices. Define guest retention/expiry, explicit account attachment, authorization on every owned resource, and deletion/export behavior before exposing saved records remotely. Existing local demo profiles must not be automatically assigned to a new account.
2. **Multi-institution academic history:** record each course attempt's source institution, course identifier, term, units, calendar, status (completed/in-progress/planned), final grade, and grading basis. Model semester/quarter calendars explicitly; retain original units alongside rule-based conversions. Store AP scores separately. Projected grades belong to scenarios, never overwrite completed history.
3. **Verified academic data and deterministic evaluation:** version rules and source references by academic year. Implement and test articulation, transferability, prerequisites, repeat handling, pass/no-pass treatment, unit conversion, and supported overall/UC/CSU/major-preparation GPAs using verified rules. Missing rules produce explicit uncertainty. Institutions and rule sets should permit later expansion beyond California.
4. **Application lists and planning:** keep university/major targets independent of individual schedules. Allow a selected subset of targets per plan. Determine shared and university-specific requirements, conflicting constraints, feasibility, and tradeoffs before adding schedule generation.
5. **Editable schedule versions:** allow moving courses between terms (preferably drag-and-drop), adding/removing courses, locking placements, regeneration that preserves locks, saving multiple versions, and comparing alternatives. Every edit must recalculate prerequisites, sequencing, workload, unit limits, unmet requirements, and progress for selected targets, with clear conflict/readiness warnings.
6. **Grounded guidance and competitiveness:** add OpenAI for explanations and conversation around verified results. Keep academic evaluation deterministic. Later introduce campus/major-specific historical admissions statistics and GPA distributions, clearly separated from eligibility and individualized analysis. Do not invent acceptance percentages. Consider prediction only after representative data, validation, and calibration justify it.

Phase 1 has four tables: institutions, campus-specific majors, local student profiles, and profile targets. Important evolution points:

- `current_college_id` is a primary/home college, not a restriction on where coursework can originate. Future course attempts must reference their own source institution; add attendance relationships when needed.
- `student_profile_targets` already permits multiple campuses and majors. Its uniqueness constraint applies to the complete profile/campus/major tuple, allowing more than one major at a campus. Future schedules should link selected targets through a separate association and preserve target snapshots per plan version.
- Profiles currently have no account owner. Add explicit account ownership and guest-session lifecycle rules before production persistence. Numeric profile IDs are identifiers, not access-control tokens; CORS is not authentication.
- A validated transfer-term string is adequate for this form. Calendar-aware scheduling will require structured institution-specific academic terms and a migration of existing values. Preserve original credit units and effective rules when converting units.
- Current majors are demo labels without catalog year, stable external identifier, or authoritative source. Verified catalog ingestion will require versioned program records; the present campus/name uniqueness is for this limited catalog, not a permanent identifier strategy.
- Future schedule versions and GPA scenarios should reference immutable inputs/rule versions rather than modifying historical coursework. These tables are deliberately deferred until their workflows are implemented.
