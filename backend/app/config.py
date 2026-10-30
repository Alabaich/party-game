from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET: str
    R2_PUBLIC_BASE_URL: str
    CORS_ORIGINS: str = ""
    # Signs admin session cookies. Empty = random per process (sessions reset on restart).
    SECRET_KEY: str = ""
    # Code required to register a host account. Empty = only the very first account may register.
    ADMIN_INVITE_CODE: str = ""
    COOKIE_SECURE: bool = True
    MAX_UPLOAD_MB: int = 300

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def r2_endpoint(self) -> str:
        return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"


settings = Settings()
