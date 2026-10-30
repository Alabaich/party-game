from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET: str
    R2_PUBLIC_BASE_URL: str
    CORS_ORIGINS: str = ""
    # PIN for host actions (start game, reveal places, accounts). Empty = no check.
    ADMIN_PIN: str = ""
    MAX_UPLOAD_MB: int = 300

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def r2_endpoint(self) -> str:
        return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"


settings = Settings()
