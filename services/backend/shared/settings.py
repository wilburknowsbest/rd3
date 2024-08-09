from pydantic_settings import BaseSettings

import logging


class SharedSettings(BaseSettings):
    app_port: int = 9000
    host: str = "0.0.0.0"
    env: str = 'local'
    log_level: int = logging.DEBUG

    enable_request_logging: bool = True
    enable_swagger: bool = True

    db_name: str = "dev_db"
    db_user: str = "dev_user"
    db_password: str = "password"
    db_host: str = "db.piccolo"
    db_port: int = 5432