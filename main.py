from fastapi import FastAPI, Depends 
from contextlib import asynccontextmanager
from app.util.init_db import create_tables
from app.routers.auth import authRouter
from app.routers.admin import adminRouter
from app.routers.project import projectRouter
from app.util.protectRoute import get_current_user
from app.db.schema.user import UserOutput
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app:FastAPI):
    #initialize db at start 
    create_tables() #do things before app starts 
    yield 
    #do things after app stops

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Bearer token auth — credentials=True not needed
    allow_credentials=False,
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
def read_protected(user:UserOutput=Depends(get_current_user)):
    return {"message": f"Hello {user.first_name} {user.last_name}, you have accessed a protected route!"}