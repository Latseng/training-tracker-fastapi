from fastapi import FastAPI
from app.routers import auth
# from app.core.supabase_client import supabase
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/")
def root():
    return "Hello FastAPI!"

# @app.get("/test-connection")
# def test_connection():
#     try:
#         response = supabase.table("training").select("*").limit(1).execute()
#         return {
#             "status": "success",
#             "row_count": len(response.data),
#             "sample": response.data
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "detail": str(e)
#         }

if __name__ == "__main__":
    root()
