from typing import List, ClassVar

from decouple import config
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    JWT_SECRET_KEY: str = config('JWT_SECRET_KEY' , cast= str)
    JWT_REFRESH_SECRET_KEY: str = config('JWT_REFRESH_SECRET_KEY', cast=str)
    ALGORITHM: ClassVar[str] = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    PROJECT_NAME: str = "Whatsapp Ai barber"


    POSTGRES_CONNECTION_STRING: str = config('POSTGRES_CONNECTION_STRING', cast = str)
    POSTGRES_PREFIX: str = config('POSTGRES_PREFIX', cast = str)
    POSTGRES_PASSWORD: str = config('POSTGRES_PASSWORD', cast = str)
    POSTGRES_USER: str = config('POSTGRES_USER', cast = str)
    POSTGRES_HOST: str = config('POSTGRES_HOST', cast = str)
    POSTGRES_DB: str = config('POSTGRES_DB', cast = str)
    POSTGRES_DB_API: str = config('POSTGRES_DB_API', cast=str)

    REDIS_URL: str = config('REDIS_URL' , cast= str)
    BUFFER_KEY_SUFIX: str = config('BUFFER_KEY_SUFIX' , cast= str)
    DEBOUNCE_SECONDS: int = config('DEBOUNCE_SECONDS' , cast= int)
    BUFFER_TTL: int = config('BUFFER_TTL' , cast= int)

    WHATSAPP_PROVIDER: str = config('WHATSAPP_PROVIDER', cast=str)
    TENANT_NAME: str = config('TENANT_NAME', cast=str)
    TENANT_ID: str = config('TENANT_ID', cast = str)
    DATABASE_URL: str = config('DATABASE_URL', cast = str)
    CACHE_REDIS_URI: str = config('CACHE_REDIS_URI', cast = str)
    COLLECTION_NAME: str = config('COLLECTION_NAME', cast = str)
# Admin (optional). If set, /admin/ingest requires X-API-Key
# ADMIN_API_KEY=troque-isto

    LOG_LEVEL: str = config('LOG_LEVEL', cast = str)
    OPENAI_API_KEY: str = config('OPENAI_API_KEY', cast = str)
    GOOGLE_API_KEY: str = config('GOOGLE_API_KEY', cast = str)
    OPENAI_MODEL_NAME: str = config('OPENAI_MODEL_NAME', cast = str)
    OPENAI_MODEL_TEMPERATURE: int = config('OPENAI_MODEL_TEMPERATURE', cast = str)

    EVOLUTION_API_URL: str = config('EVOLUTION_API_URL', cast = str)
    EVOLUTION_INSTANCE_NAME: str = config('EVOLUTION_INSTANCE_NAME', cast = str)
    AUTHENTICATION_API_KEY: str = config('AUTHENTICATION_API_KEY', cast = str)
    CONFIG_SESSION_PHONE_VERSION: str = config('CONFIG_SESSION_PHONE_VERSION', cast = str)

    META_PHONE_NUMBER_ID: str = config('META_PHONE_NUMBER_ID', cast = str)  # -> ID do número na Meta Cloud
    META_VERIFY_TOKEN: str = config('META_VERIFY_TOKEN', cast = str) # -> token de acesso
    META_API_VERSION: str = config('META_API_VERSION', cast = str)


    DATABASE_ENABLED: str = config('DATABASE_ENABLED', cast = str)
    DATABASE_PROVIDER: str = config('DATABASE_PROVIDER', cast = str)
    DATABASE_CONNECTION_URI: str = config('DATABASE_CONNECTION_URI', cast = str)
    DATABASE_CONNECTION_CLIENT_NAME: str = config('DATABASE_CONNECTION_CLIENT_NAME', cast = str)
    DATABASE_SAVE_DATA_INSTANCE: bool = config('DATABASE_SAVE_DATA_INSTANCE', cast = bool)
    DATABASE_SAVE_DATA_NEW_MESSAGE: bool = config('DATABASE_SAVE_DATA_NEW_MESSAGE', cast = bool)
    DATABASE_SAVE_MESSAGE_UPDATE: bool = config('DATABASE_SAVE_MESSAGE_UPDATE', cast = bool)
    DATABASE_SAVE_DATA_CONTACTS: bool = config('DATABASE_SAVE_DATA_CONTACTS', cast = bool)
    DATABASE_SAVE_DATA_CHATS: bool = config('DATABASE_SAVE_DATA_CHATS', cast = bool)
    DATABASE_SAVE_DATA_LABELS: bool = config('DATABASE_SAVE_DATA_LABELS', cast = bool)
    DATABASE_SAVE_DATA_HISTORIC: bool = config('DATABASE_SAVE_DATA_HISTORIC', cast = bool)

    CACHE_REDIS_ENABLED: str = config('CACHE_REDIS_ENABLED', cast = str)

    CACHE_REDIS_PREFIX_KEY: str = config('CACHE_REDIS_PREFIX_KEY', cast = str)
    CACHE_REDIS_SAVE_INSTANCES: str = config('CACHE_REDIS_SAVE_INSTANCES', cast = str)
    CACHE_LOCAL_ENABLED: str = config('CACHE_LOCAL_ENABLED', cast = str)



settings = Settings()