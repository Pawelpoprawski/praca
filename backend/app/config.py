from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    REDIS_URL: str = ""

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_CV_SIZE_MB: int = 5
    MAX_LOGO_SIZE_MB: int = 2

    # Email (Resend)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Praca w Szwajcarii <noreply@praca-w-szwajcarii.ch>"
    EMAIL_ENABLED: bool = False
    # Test mode: gdy ustawione, wszystkie aplikacje zewnetrzne ida na ten email zamiast na contact_email z oferty
    APPLICATION_TEST_RECIPIENT: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""

    # reCAPTCHA v3
    RECAPTCHA_SECRET_KEY: str = ""
    RECAPTCHA_SITE_KEY: str = ""
    RECAPTCHA_ENABLED: bool = False
    RECAPTCHA_SCORE_THRESHOLD: float = 0.5

    # Scraper
    JOBSPL_FEED_URL: str = "https://www.jobs.pl/88656df3de7b433d9f8eb25cef3d22f3e8f4c845"
    FACHPRACA_FEED_URL: str = "https://fachpraca.pl/xml/export/polacy-szwajcaria"
    ROLJOB_FEED_URL: str = "https://www.rol-jobhliwa.ch/export-offers.php"
    ADECCO_FEED_URL: str = "https://files.channable.com/brVVoxVpaiGpuaaqXafV3w==.xml"
    SCRAPER_ENABLED: bool = True
    SCRAPER_JOBSPL_HOUR: int = 6
    SCRAPER_JOBSPL_MINUTE: int = 0

    # Frontend
    FRONTEND_URL: str = "http://localhost:3002"

    # OAuth — Google
    GOOGLE_CLIENT_ID: str = "dummy-google-client-id"
    GOOGLE_CLIENT_SECRET: str = "dummy-google-client-secret"
    # OAuth — Facebook
    FACEBOOK_CLIENT_ID: str = "dummy-facebook-client-id"
    FACEBOOK_CLIENT_SECRET: str = "dummy-facebook-client-secret"
    # Wspolny base URL do callbackow (backend public URL)
    OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8002"

    # Admin
    FIRST_ADMIN_EMAIL: str = "admin@praca-w-szwajcarii.ch"
    FIRST_ADMIN_PASSWORD: str = "admin-zmien-po-pierwszym-logowaniu"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
