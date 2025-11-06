from fastapi import FastAPI
from app.core.supabase_client import supabase

app = FastAPI()

@app.get("/")
def root():
    return "Hello FastAPI!"

@app.get("/test-connection")
def test_connection():
    try:
        response = supabase.table("training").select("*").limit(1).execute()
        return {
            "status": "success",
            "row_count": len(response.data),
            "sample": response.data
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }

if __name__ == "__main__":
    root()
