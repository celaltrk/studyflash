from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import tickets, team, ai, auth, users, outlook


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    from services.email_sync_service import email_poll_loop

    # Auto-seed if empty
    import services.db_service as db
    existing = db.count_tickets_total()
    if not existing.count or existing.count == 0:
        from seed import seed
        seed()

    # Start background email polling
    poll_task = asyncio.create_task(email_poll_loop())

    yield

    # Clean shutdown
    poll_task.cancel()
    try:
        await poll_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Studyflash Support Platform",
    description="Internal support ticket management with AI-powered triage",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(team.router)
app.include_router(ai.router)
app.include_router(users.router)
app.include_router(outlook.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "studyflash-support"}
