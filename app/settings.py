# app/settings.py
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Configurazione centrale dell’applicazione.
    Caricata da .env tramite Pydantic Settings.
    """

    # ============================================================
    # 🔵 DATABASE PRINCIPALE (Login, HR, Documenti generali)
    # ============================================================

    API_MYSQL_HOSTNAME: str = Field(..., validation_alias="API_MYSQL_HOSTNAME")
    API_MYSQL_PORT: int = Field(..., validation_alias="API_MYSQL_PORT")
    API_MYSQL_USERNAME: str = Field(..., validation_alias="API_MYSQL_USERNAME")
    API_MYSQL_PASSWORD: str = Field(..., validation_alias="API_MYSQL_PASSWORD")
    API_MYSQL_DB: str = Field(..., validation_alias="API_MYSQL_DB")

    # ============================================================
    # 🔵 DATABASE QUALITY (FoxPro → fox_staging)
    # ============================================================

    QUALITY_MYSQL_DB: str = Field(..., validation_alias="QUALITY_MYSQL_DB")

    # Se un domani cambi host/porta/utente, attivi questi:
    QUALITY_MYSQL_HOSTNAME: str | None = Field(None, validation_alias="QUALITY_MYSQL_HOSTNAME")
    QUALITY_MYSQL_PORT: int | None = Field(None, validation_alias="QUALITY_MYSQL_PORT")
    QUALITY_MYSQL_USERNAME: str | None = Field(None, validation_alias="QUALITY_MYSQL_USERNAME")
    QUALITY_MYSQL_PASSWORD: str | None = Field(None, validation_alias="QUALITY_MYSQL_PASSWORD")

    # ============================================================
    # 🔒 JWT
    # ============================================================

    SECRET_KEY_JWT: str = Field(..., validation_alias="SECRET_KEY_JWT")
    ALGORITHM_JWT: str = Field(..., validation_alias="ALGORITHM_JWT")

    # ============================================================
    # 📧 SMTP
    # ============================================================

    SMTP_HOST: str = Field("smtp.gmail.com", validation_alias="SMTP_HOST")
    SMTP_PORT: int = Field(587, validation_alias="SMTP_PORT")
    SMTP_USER: str = Field(..., validation_alias="SMTP_USER")
    SMTP_PASSWORD: str = Field(..., validation_alias="SMTP_PASSWORD")
    SMTP_FROM: str = Field(..., validation_alias="SMTP_FROM")
    SMTP_SENDER_NAME: str = Field("PLAX Notifiche", validation_alias="SMTP_SENDER_NAME")
    SMTP_TLS: bool = Field(True, validation_alias="SMTP_TLS")

    # ============================================================
    # 📂 Filesystem base per i documenti Qualità
    # ============================================================

    CERTS_BASE_DIR: str = Field(..., validation_alias="CERTS_BASE_DIR")

    # ============================================================
    # 🤖 Groq (AI suggestion service)
    # ============================================================

    GROQ_API_KEY: str = Field(..., validation_alias="GROQ_API_KEY")

    # ============================================================
    # 🗓 Scheduler email
    # ============================================================

    SCHEDULER_USE_DB_RECIPIENTS: int | None = Field(
        0, validation_alias="SCHEDULER_USE_DB_RECIPIENTS"
    )
    SCHEDULER_DEFAULT_TO: str | None = Field("", validation_alias="SCHEDULER_DEFAULT_TO")
    SCHEDULER_DEFAULT_CC: str | None = Field("", validation_alias="SCHEDULER_DEFAULT_CC")
    SCHEDULER_DEFAULT_BCC: str | None = Field("", validation_alias="SCHEDULER_DEFAULT_BCC")

    # ============================================================
    # 🔧 Manutenzioni
    # ============================================================

    MAINTENANCE_WITHIN: int | None = Field(7, validation_alias="MAINTENANCE_WITHIN")
    MAINTENANCE_THROTTLE: int | None = Field(7, validation_alias="MAINTENANCE_THROTTLE")

    # ============================================================
    # 🌍 Timezone
    # ============================================================

    TZ: str = Field("Europe/Rome", validation_alias="TZ")

    # ============================================================
    # ⚙️ Config generale
    # ============================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Restituisce singleton Settings, caricato una sola volta."""
    return Settings()
