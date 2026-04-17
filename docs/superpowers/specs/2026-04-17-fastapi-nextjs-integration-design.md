# FastAPI + Next.js Integration Design

## Goal

Replace the Streamlit dashboard with the existing Next.js orbital UI, connected to real backend logic via a FastAPI layer. Users access everything at `altagro.site`.

## Architecture

```
altagro.site  →  agro-frontend (Next.js, Railway)
                      │
                      │ HTTP via BACKEND_URL (Railway internal URL)
                      ▼
              altagrocontent (FastAPI, Railway)
                      │
                      ▼
                  Postgres (Railway)
```

- `altagrocontent` service: `start.sh` changes from `streamlit run` to `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- `agro-frontend` service: Next.js at `web/`, root directory `/web`, domain `altagro.site`
- Next.js calls `/api/*` route handlers which proxy to `BACKEND_URL`
- `BACKEND_URL` env var on `agro-frontend` = internal Railway URL of `altagrocontent`

## Authentication

- Single shared password stored as `APP_PASSWORD` env var on `agro-frontend`
- Next.js middleware (`web/middleware.ts`) checks for `auth_token` httpOnly cookie on all routes except `/login`
- Login page at `/login`: password field → POST to `/api/auth/login` → sets cookie → redirect to `/`
- Cookie value: `sha256(APP_PASSWORD + salt)`, salt stored as `AUTH_SECRET` env var
- No per-user accounts. One password for the whole team.

## FastAPI — `api/`

New directory at repo root alongside `src/`, `dashboard/`.

### File structure
```
api/
  main.py           # FastAPI app, mounts all routers
  routers/
    competitors.py  # /competitors endpoints
    carousel.py     # /carousel endpoints
    news.py         # /news endpoints
    reports.py      # /reports endpoints
    voice.py        # /voice endpoints
    studio.py       # /studio endpoints
```

### Endpoints

| Method | Path | Description | Python module |
|--------|------|-------------|---------------|
| GET | `/health` | Health check | — |
| GET | `/competitors` | List active profiles with post count + last sync | `src/models.py` |
| POST | `/competitors` | Add profile `{handle, type}` | `src/models.py` |
| DELETE | `/competitors/{id}` | Deactivate profile | `src/models.py` |
| POST | `/competitors/sync` | Collect + analyze all profiles (may take 30-120s) | `src/collector/collector.py`, `src/analyzer/image_analyzer.py` |
| GET | `/competitors/gap` | Gap analysis report | `src/analyzer/gap_analyzer.py` |
| GET | `/carousel` | List past carousels (last 10) | `src/models.py` |
| POST | `/carousel/generate` | Generate carousel `{theme}` (10-30s) | `src/carousel/generator.py` |
| GET | `/news` | List recent news items | `src/collector/news_monitor.py` |
| GET | `/reports` | List weekly reports | `src/models.py` |
| GET | `/voice` | Get latest voice profile | `src/models.py` |
| POST | `/voice/analyze` | Generate new voice analysis | `src/reporter/voice_profiler.py` |
| GET | `/studio/history` | List generated posts | `src/models.py` |
| POST | `/studio/generate` | Generate adapted post `{post_id}` | `src/generator/content_generator.py` |

All endpoints return JSON. Long operations (sync, carousel, studio) run synchronously with HTTP timeout of 180s — spinner on frontend while waiting.

## Next.js changes — `web/`

### New files
```
web/
  middleware.ts                    # auth guard
  app/login/page.tsx               # login page
  app/api/auth/login/route.ts      # POST: validate password, set cookie
  app/api/auth/logout/route.ts     # POST: clear cookie
  app/api/[...proxy]/route.ts      # catch-all proxy to BACKEND_URL
```

### Modified files
- `web/components/drawers/DrawerCarrossel.tsx` — real POST `/api/carousel/generate`, show history
- `web/components/drawers/DrawerConcorrentes.tsx` — real GET `/api/competitors`, add/remove/sync
- `web/components/drawers/DrawerNoticias.tsx` — real GET `/api/news`
- `web/components/drawers/DrawerRelatorios.tsx` — real GET `/api/reports`
- `web/components/drawers/DrawerIdentidade.tsx` — real GET `/api/voice`
- `web/components/drawers/DrawerStudio.tsx` — real POST `/api/studio/generate`

### Proxy pattern
`app/api/[...proxy]/route.ts` forwards all `/api/*` requests to `BACKEND_URL`, stripping the `/api` prefix. Passes through method, body, headers. Returns FastAPI response directly.

Exception: `/api/auth/*` routes are handled locally in Next.js (never forwarded to FastAPI).

## Environment Variables

### `agro-frontend` (Next.js)
| Var | Value |
|-----|-------|
| `BACKEND_URL` | Railway internal URL of `altagrocontent` service |
| `APP_PASSWORD` | Chosen team password |
| `AUTH_SECRET` | Random 32-char string for cookie signing |

### `altagrocontent` (FastAPI)
Existing vars remain (`DATABASE_URL`, `OPENAI_API_KEY`, `APIFY_API_TOKEN`). No new vars needed.

## Railway / DNS

- `altagrocontent` service: no public domain needed (internal only)
- `agro-frontend` service: custom domain `altagro.site` added in Railway dashboard
- DNS: CNAME `altagro.site` → Railway-provided hostname for `agro-frontend`
- `agro-frontend-production.up.railway.app` remains as fallback

## What gets removed

- `dashboard/` directory — entire Streamlit dashboard deleted
- `streamlit` removed from `requirements.txt`
- `start.sh` updated to run uvicorn
- `agro-frontend` service created in previous session remains as the Next.js host
