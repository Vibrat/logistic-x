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

## Troubleshooting

**Backend crashes on startup with `INSERT ON CONFLICT` error**
The seed file was fixed to use `pg_insert(...).on_conflict_do_nothing()`. Run `docker compose down -v && docker compose up` to rebuild from scratch.

**`422 Unprocessable Entity` on `/api/ask`**
Make sure you are sending `{ "question": "...", "history": [] }` — the `history` field is required (can be an empty array).

**AI returns `needs_clarification: true` every time**
Check that `GROQ_API_KEY` is set correctly in your `.env`. The backend logs will show a Groq auth error if the key is missing or invalid.

**Frontend can't reach the backend**
Ensure `NEXT_PUBLIC_API_URL` points to the correct backend URL. In Docker Compose this is set automatically to `http://localhost:8000`.
