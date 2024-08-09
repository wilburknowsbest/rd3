from pydantic_settings import BaseSettings

from shared.settings import SharedSettings


class AppSettings(SharedSettings):
    service_name: str = "api"


settings = AppSettings()
