import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import dashboard, ask, forecast

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic migrations.
    # Run `alembic upgrade head` (or use docker-compose) before starting the app.
    yield


app = FastAPI(
    title="Logistics Analytics API",
    description="AI-powered logistics analytics backend with KPI registry and NL query support.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(ask.router)
app.include_router(forecast.router)


@app.get("/health")
def health():
    return {"status": "ok"}
