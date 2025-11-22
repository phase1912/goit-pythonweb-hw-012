from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Email settings
    mail_username: str = "noreply@example.com"
    mail_password: str = ""
    mail_from: str = "noreply@example.com"
    mail_port: int = 1025
    mail_server: str = "localhost"
    mail_from_name: str = "Contacts API"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    mail_use_credentials: bool = True
    mail_validate_certs: bool = True

    # Application URL
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Cloudinary settings
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

