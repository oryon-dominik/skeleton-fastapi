"""Will get imported via __init__.py on module level"""
import os
import secrets
import logging

from functools import lru_cache
from typing import List
from pathlib import Path
from distutils.util import strtobool

from pydantic import BaseSettings, AnyHttpUrl, validator

from . import validators

ROOT_DIR = Path(__file__).parent.parent.parent
DEVELOP = strtobool(os.environ.get('DEBUG_FASTAPI_SKELETON', "False"))

@lru_cache()
def get_settings():
    """
    Get settings from config.
    @Least-recently-used cache decorator.
    -> Return the same value that was returned the first time, instead of computing it again.

    example params:
        params = dict(
            _env_file='develop.env',
            _env_file_encoding='utf-8',
            _secrets_dir='/var/run',
        )

    example endpoint:
        @app.get("/info")
        async def info(settings: settings.Settings = Depends(settings.get_settings)):
            return {"foo": settings.FOO}

    """
    dotenv = 'develop.env' if DEVELOP else 'production.env'
    params = dict(_env_file=ROOT_DIR / '.envs' / dotenv, _env_file_encoding='utf-8')
    return Settings(**params)


class Settings(BaseSettings):
    """
    Settings for the application.

    Use Typehints to ensure your IDE will moan, if the types get messed up.
    """

    PRODUCTION: bool = not DEVELOP
    DEBUG: bool = not PRODUCTION
    TESTING: bool = False  # set in pyproject.toml[tool.pytest.ini_options] via pytest-env

    API_URL_PREFIX: str = "/api"

    # -> https://blog.miguelgrinberg.com/post/the-new-way-to-generate-secure-tokens-in-python
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 60 minutes * 24 hours * 7 days = 7 days
    JWT_ALGORITHM: str = "HS256"

    ROOT_PATH: str = '/'
    SERVER_HOST: AnyHttpUrl

    DATABASE_URL: str
    if TESTING:
        DATABASE_URL = "sqlite:///:memory:?cache=shared"

    DATABASE_ARGS: dict = {"check_same_thread": False}  # sqlite specific
    DATABASE_ECHO: bool = False  # print raw SQL-statements to stdout, shouldn't be used in production

    # CORS_ORIGINS is a comma-seperated list of origins.
    # No brackets '[' and ']', no quotation-marks.
    # e.g: http://localhost,https://localhost:4200,http://local.dockertoolbox.tiangolo.com
    CORS_ORIGINS: str
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    @validator("CORS_ORIGINS", pre=False)
    def dissassemble_cors_origins(cls, v: str) -> List[AnyHttpUrl]:
        return validators.dissassemble_comma_seperated_lists_of_strings(v)

    TRUSTED_HOSTS: str
    @validator("TRUSTED_HOSTS", pre=False)
    def dissassemble_trusted_hosts(cls, v: str) -> List[str]:
        return validators.dissassemble_comma_seperated_lists_of_strings(v)

    # permissions
    VALID_SCOPES: List[str] = ["unauthorized", "users/whoami", "logs/read"]

    # logging
    LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO


    class Config:
        case_sensitive = True
        env_file_encoding = 'utf-8'
        env_file = ROOT_DIR / '.envs' / 'production.env'
        secrets_dir = ROOT_DIR / '.envs' / '.secrets'
