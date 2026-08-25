import asyncio
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from app.util.init_db import create_tables
from app.routers.auth import authRouter
from app.routers.admin import adminRouter
from app.routers.project import projectRouter
from app.util.protectRoute import get_current_user
from app.db.schema.user import UserOutput
from fastapi.middleware.cors import CORSMiddleware


async def _prewarm_embedding_model():
    """
    Fires a dummy embed_query call immediately on startup so the HuggingFace
    Inference API loads the model into memory before the first real user request.
    Without this, the first chat query pays a 20-40s cold-start penalty that
    (combined with other latency) pushes past Render's 57s proxy timeout.
    Non-fatal: if HuggingFace is unavailable, the server still starts normally.
    """
    try:
        from app.service.ingestion import embedding_model
        await asyncio.to_thread(embedding_model.embed_query, "warmup")
        print("[InsightAI] HuggingFace embedding model pre-warmed successfully.")
    except Exception as e:
        print(f"[InsightAI] Embedding pre-warm failed (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables and HNSW index
    create_tables()
    # Fire-and-forget: warm up the HuggingFace model in the background while
    # the server is already accepting health-check pings from Render/UptimeRobot.
    asyncio.create_task(_prewarm_embedding_model())
    yield
    # Cleanup on shutdown (none needed currently)


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authRouter, tags=["auth"], prefix="/auth")
app.include_router(adminRouter, tags=["admin"], prefix="/admin")
app.include_router(projectRouter, tags=["projects"], prefix="/projects")


@app.get("/health")
def health_check():
    return {"status": "Running..."}


@app.get("/protected")
def read_protected(user: UserOutput = Depends(get_current_user)):
    return {"message": f"Hello {user.first_name} {user.last_name}, you have accessed a protected route!"}