from fastapi import FastAPI
import os
from app.routers import auth, training_sessions, training_activities, ai
from fastapi.middleware.cors import CORSMiddleware
from app.dependencies.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv 

load_dotenv()

environment = os.getenv("ENVIRONMENT")
frontent_url = os.getenv("FRONTEND_URL")

if environment == "Production":
    ALLOWED_ORIGINS = [frontent_url]
    
elif environment == "Development":
    ALLOWED_ORIGINS = [
        "http://localhost:3000", 
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

app.state.limiter = limiter

# 加入錯誤處理器：當超過限制時，回傳標準的 429 錯誤
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(training_sessions.router)
app.include_router(training_activities.router)
app.include_router(ai.router)

@app.get("/")
def root():
    return "Hello FastAPI!"
