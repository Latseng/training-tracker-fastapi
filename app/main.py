from fastapi import FastAPI
from app.routers import auth, training_sessions, training_activities
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

if settings.ENVIRONMENT == "Production":
    ALLOWED_ORIGINS = [settings.FRONTEND_URL]
    
elif settings.ENVIRONMENT == "Development":
    ALLOWED_ORIGINS = [
        settings.FRONTEND_URL, 
        "http://localhost", 
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(training_sessions.router)
app.include_router(training_activities.router)

@app.get("/")
def root():
    return "Hello FastAPI!"
