from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 設置環境變數的名稱，如果找不到，則使用後面的預設值
    ENVIRONMENT: str = "Development"
    
    # CORS 允許的前端來源
    FRONTEND_URL: str = "http://localhost:3000"
    
    # 您的 Supabase URL 和 Key
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # 告訴 Pydantic 讀取 .env 檔案
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore" # 忽略 .env 中模型未定義的變數
    )

# 初始化設定實例
settings = Settings()