import os
from supabase import create_client, Client
from dotenv import load_dotenv 

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_publishable_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
supabase_secret_key = os.getenv("SUPABASE_SECRET_KEY")

if not supabase_url:
    raise ValueError("❌ 錯誤: 在 .env 檔案中找不到 'SUPABASE_URL'")

if not supabase_publishable_key:
    raise ValueError("❌ 錯誤: 在 .env 檔案中找不到 'SUPABASE_PUBLISHABLE_KEY'")

if not supabase_secret_key:
    raise ValueError("❌ 錯誤: 在 .env 檔案中找不到 'SUPABASE_SECRET_KEY' (或 SUPABASE_SERVICE_KEY)")

try:
    supabase_client: Client = create_client(supabase_url, supabase_publishable_key)
    supabase_admin: Client = create_client(supabase_url, supabase_secret_key)
except Exception as e:
    raise RuntimeError(f"❌ 初始化 Supabase Client 失敗: {e}")

def get_supabase_client() -> Client:
    return supabase_client

def get_supabase_admin() -> Client:
    return supabase_admin