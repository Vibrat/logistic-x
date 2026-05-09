# LogisticsAI — AI-Powered Logistics Analytics Dashboard

A full-stack analytics dashboard that combines live KPI metrics, interactive charts, and a natural-language AI interface backed by real logistics order data.

**Stack:** Next.js 14 · FastAPI · PostgreSQL 16 · Groq (`llama-3.3-70b-versatile`) · Recharts · statsmodels

---

## Features

- **Dashboard** — live KPI cards (total orders, on-time rate, avg delivery days) and three pre-built charts
- **Ask AI** — chat interface that accepts plain-English questions, reasons about them in a multi-step loop, and returns charts + explanations
- **Demand Forecasting** — Holt-Winters / linear regression / moving-average models, rendered as a connected historical + forecast line chart
- **Agentic clarification** — if a question is ambiguous, the AI queries the database to discover real values before either proceeding automatically or asking the user to choose
- **KPI registry** — all metrics are declared in a single JSON file; the AI is constrained to only those IDs

---

## Quick Start (Docker — recommended)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A free [Groq API key](https://console.groq.com/)

### 1. Clone and configure

```bash
git clone <repo-url>
cd spaceship

# Create the root .env file (only GROQ_API_KEY is required)
cp .env.example .env          # if you have one, otherwise create manually
echo "GROQ_API_KEY=gsk_..." >> .env
```

The root `.env` only needs:

```env
GROQ_API_KEY=gsk_your_key_here
```

### 2. Start all services

```bash
docker compose up
```

On first run this:
1. Starts PostgreSQL 16
2. Runs `alembic upgrade head` to create the `orders` table
3. Seeds 400 rows from `product/mock_logistics_data.csv`
4. Starts the FastAPI backend on `http://localhost:8000`
5. Starts the Next.js frontend on `http://localhost:3000`

Open **http://localhost:3000** in your browser.

### 3. Stop

```bash
docker compose down          # stop containers, keep DB volume
docker compose down -v       # stop + wipe the database
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create backend/.env
cp .env.example .env
# Edit .env — set DATABASE_URL and GROQ_API_KEY
```

`.env` values:

```env
DATABASE_URL=postgresql://logistics_user:logistics_pass@localhost:5432/logistics
GROQ_API_KEY=gsk_your_key_here
```

Start a local Postgres instance (or use Docker for just the DB):

```bash
docker compose up db -d
```

Run migrations and seed:

```bash
alembic upgrade head
python -m db.seed
```

Start the dev server:

```bash
uvicorn main:app --reload --port 8000
```

API docs available at **http://localhost:8000/docs**

### Frontend

```bash
cd frontend
npm install

# Create frontend/.env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

Frontend runs on **http://localhost:3000**

---

## Project Structure

```
spaceship/
├── docker-compose.yml
├── .env                        # GROQ_API_KEY (not committed)
│
├── backend/
│   ├── main.py                 # FastAPI app, router registration
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── config/
│   │   └── kpi.json            # ← KPI metric definitions (edit to add new KPIs)
│   │
│   ├── ai/
│   │   ├── orchestrator.py     # Agentic loop: explore → clarify → compute
│   │   └── tool_schemas.py     # Groq tool definitions (explore_data, analytics_query, forecast)
│   │
│   ├── db/
│   │   ├── models.py           # SQLAlchemy Order model
│   │   ├── connection.py       # Engine, SessionLocal, get_db()
│   │   ├── seed.py             # CSV → PostgreSQL seeder
│   │   ├── kpi_engine.py       # Evaluates kpi.json metrics against the DB
│   │   ├── query_builder.py    # Builds + executes analytics queries
│   │   └── explorer.py         # Safe SELECT DISTINCT for the AI's explore_data tool
│   │
│   ├── forecasting/
│   │   └── engine.py           # Holt-Winters, linear regression, moving average
│   │
│   ├── routers/
│   │   ├── ask.py              # POST /api/ask
│   │   ├── dashboard.py        # GET /api/dashboard/kpis|charts
│   │   └── forecast.py         # POST /api/forecast
│   │
│   ├── schemas/
│   │   └── responses.py        # Pydantic response models
│   │
│   └── alembic/
│       └── versions/
│           └── 0001_create_orders_table.py
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Dashboard + KPI guide
│   │   └── chat/page.tsx       # Ask AI thread UI
│   ├── components/
│   │   ├── ChartRenderer.tsx   # Bar / Line / Pie via Recharts
│   │   ├── KPICard.tsx
│   │   ├── ExplainPanel.tsx
│   │   └── DataTable.tsx
│   └── lib/
│       └── api.ts              # Typed fetch wrappers
│
└── product/
    ├── mock_logistics_data.csv # 400-row seed dataset
    └── *.md                    # Product specs
```

---

## Adding a New KPI

Edit **`backend/config/kpi.json`** — no code changes needed. The AI picks up new entries automatically.

```json
{
  "id": "exception_rate",
  "label": "Exception Rate",
  "description": "Percentage of orders with status = exception",
  "aggregation": "ratio",
  "numerator":   { "field": "*", "filters": { "status": "exception" } },
  "denominator": { "field": "*", "filters": {} },
  "format": "percent"
}
```

Supported `aggregation` types:

| Type | Behaviour |
|---|---|
| `count` | `COUNT(field)` with optional filters |
| `sum` | `SUM(field)` |
| `avg` | `AVG(field)` |
| `ratio` | `numerator ÷ denominator × 100` |
| `avg_date_diff` | `AVG(delivery_date − order_date)` in days |

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/dashboard/kpis` | All KPI values from `kpi.json` |
| `GET` | `/api/dashboard/charts` | Three fixed chart datasets |
| `POST` | `/api/ask` | Natural language query with conversation history |
| `POST` | `/api/forecast` | Direct forecast by SKU or product category |

### `POST /api/ask`

```json
{
  "question": "Which carrier has the highest delay rate?",
  "history": [
    { "role": "user",      "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

The `history` array enables multi-turn conversations. Each call returns:

```json
{
  "answer": "FedEx has the highest delay rate at 42%.",
  "needs_clarification": false,
  "chart_type": "bar",
  "chart_data": { "labels": [...], "datasets": [...] },
  "explanation": { "metric": "...", "group_by": "...", ... },
  "filters_used": {},
  "raw_data": [...]
}
```

When `needs_clarification` is `true`, the AI is asking a follow-up question. Send the user's answer as the next message in `history`.

---

## Environment Variables

| Variable | Where | Description |
|---|---|---|
| `GROQ_API_KEY` | root `.env` or backend `.env` | Groq API key — get one free at [console.groq.com](https://console.groq.com/) |
| `DATABASE_URL` | backend `.env` | Full PostgreSQL connection string |
| `NEXT_PUBLIC_API_URL` | frontend `.env.local` | Backend base URL (default: `http://localhost:8000`) |

---

## Database Schema

Single table: `orders`

| Column | Type | Notes |
|---|---|---|
| `order_id` | `VARCHAR` | Primary key |
| `client_id` | `VARCHAR` | |
| `order_date` | `DATE` | |
| `delivery_date` | `DATE` | Nullable |
| `carrier` | `VARCHAR` | DHL, FedEx, UPS, etc. |
| `origin_city` | `VARCHAR` | |
| `destination_city` | `VARCHAR` | |
| `status` | `VARCHAR` | `delivered` · `delayed` · `in_transit` · `exception` |
| `sku` | `VARCHAR` | e.g. `PAPER-0197` |
| `product_category` | `VARCHAR` | e.g. `PAPER`, `CRAYON`, `BOOK` |
| `quantity` | `INTEGER` | |
| `unit_price_usd` | `NUMERIC` | |
| `order_value_usd` | `NUMERIC` | |
| `is_promo` | `BOOLEAN` | |
| `promo_discount_pct` | `NUMERIC` | |
| `region` | `VARCHAR` | |
| `warehouse` | `VARCHAR` | |

---

## Deployment

### Backend + Database → Render

#### Option A — Blueprint (one click)

1. Push your repo to GitHub.
2. Go to **render.com → New → Blueprint** and connect your repo.
3. Render reads `render.yaml` and creates:
   - A **PostgreSQL 16** managed database (`logistics-db`)
   - A **Python web service** (`logistics-backend`)
4. In the Render dashboard for `logistics-backend`, set the two manual env vars:
   - `GROQ_API_KEY` — your Groq API key
   - `FRONTEND_URL` — your Vercel URL (set this after the frontend is deployed; use `*` temporarily)
5. Trigger a manual deploy. On first start the service runs:
   ```
   alembic upgrade head → python -m db.seed → uvicorn
   ```
   The CSV at `product/mock_logistics_data.csv` is available because Render checks out the full repo.

#### Option B — Manual setup

1. **Create a PostgreSQL database**
   - Render dashboard → **New → PostgreSQL** → name it `logistics-db`, plan Free.
   - Copy the **Internal Database URL** — you'll need it in step 3.

2. **Create a Web Service**
   - Render dashboard → **New → Web Service** → connect your repo.
   - Settings:
     | Field | Value |
     |---|---|
     | Language | Python |
     | Root Directory | `backend` |
     | Build Command | `pip install -r requirements.txt` |
     | Start Command | `alembic upgrade head && python -m db.seed && uvicorn main:app --host 0.0.0.0 --port $PORT` |
     | Health Check Path | `/health` |

3. **Set environment variables** in the web service:
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | Internal connection string from step 1 |
   | `GROQ_API_KEY` | Your Groq API key |
   | `FRONTEND_URL` | Your Vercel URL (add after frontend is deployed) |
   | `PYTHON_VERSION` | `3.11.0` |

4. Click **Deploy**. First deploy takes ~2 min (pip install + migration + seed).

5. Note your backend URL — it will look like `https://logistics-backend.onrender.com`.

---

### Frontend → Vercel

1. Go to **vercel.com → New Project** and import your GitHub repo.

2. In the **Configure Project** screen:
   | Field | Value |
   |---|---|
   | Framework Preset | Next.js (auto-detected) |
   | Root Directory | `frontend` |

3. Add environment variable:
   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://logistics-backend.onrender.com` (your Render URL from above) |

4. Click **Deploy**. Vercel builds Next.js and publishes to a `.vercel.app` URL.

5. Go back to Render → `logistics-backend` → Environment → update `FRONTEND_URL` to your Vercel URL (e.g. `https://logistics-ai.vercel.app`), then redeploy.

---

### Post-deployment checklist

- [ ] `https://your-backend.onrender.com/health` returns `{"status":"ok"}`
- [ ] `https://your-backend.onrender.com/api/dashboard/kpis` returns KPI data
- [ ] Dashboard page loads KPI cards and charts
- [ ] Ask AI answers a question end-to-end

> **Render free tier note:** Free web services spin down after 15 minutes of inactivity. The first request after a cold start can take ~30 seconds. Upgrade to the Starter plan ($7/mo) to keep the service always-on.

---

## Troubleshooting

**Backend crashes on startup with `INSERT ON CONFLICT` error**
The seed file was fixed to use `pg_insert(...).on_conflict_do_nothing()`. Run `docker compose down -v && docker compose up` to rebuild from scratch.

**`422 Unprocessable Entity` on `/api/ask`**
Make sure you are sending `{ "question": "...", "history": [] }` — the `history` field is required (can be an empty array).

**AI returns `needs_clarification: true` every time**
Check that `GROQ_API_KEY` is set correctly in your `.env`. The backend logs will show a Groq auth error if the key is missing or invalid.

**Frontend can't reach the backend**
Ensure `NEXT_PUBLIC_API_URL` points to the correct backend URL. In Docker Compose this is set automatically to `http://localhost:8000`.
