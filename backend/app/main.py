from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import Base, engine
from .routers import analytics, auth, reservations, servers, usage, watch_requests
from .services.scheduler import start_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Canvas Lab Server Manager")

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(servers.router)
app.include_router(reservations.router)
app.include_router(watch_requests.router)
app.include_router(usage.router)
app.include_router(analytics.router)
app.include_router(auth.router)


@app.on_event("startup")
def on_startup() -> None:
    start_scheduler()


@app.get("/api/health")
def health():
    return {"status": "ok"}
