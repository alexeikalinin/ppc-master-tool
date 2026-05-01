from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase (optional for MVP without auth)
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""

    # Google Ads — all must be set to enable GKP integration
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_developer_token: str = ""
    google_ads_refresh_token: str = ""
    google_ads_customer_id: str = ""

    # Yandex Direct / Wordstat: либо готовый токен, либо OAuth для автообновления
    yandex_wordstat_token: str = ""           # OAuth access_token (Bearer) — для Wordstat API
    yandex_direct_token: str = ""             # OAuth token с scope direct:api — starmedia-agency
                                              # Если пусто — пробуем yandex_wordstat_token
    yandex_direct_token_warface: str = ""     # Прямой токен warface-astrum-lab
    yandex_client_id: str = ""               # для обновления токена по refresh_token
    yandex_client_secret: str = ""
    yandex_refresh_token: str = ""
    yandex_refresh_token_warface: str = ""

    # SerpAPI — enables real competitor search
    serpapi_key: str = ""

    # AI: один из ключей включает нейросеть в суммари и в чат-ассистента (ответы только по данным отчёта)
    anthropic_api_key: str = ""   # Claude (Anthropic)
    openai_api_key: str = ""     # OpenAI (GPT)
    xai_api_key: str = ""        # Grok (xAI), OpenAI-совместимый API
    ai_provider: str = ""        # явный выбор: anthropic | openai | xai (пусто = первый доступный)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
