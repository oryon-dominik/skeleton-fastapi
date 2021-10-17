from functools import lru_cache

from sqlmodel import create_engine, SQLModel
from sqlmodel.pool import StaticPool

from ..config import settings

# import all models here, so they are available in the metadata
from .revisions import *  # NOSONAR, noqa
METADATA = SQLModel.metadata


@lru_cache
def get_engine_kwargs() -> dict:
    kwargs = {
        "connect_args": settings.DATABASE_ARGS,
        "echo" : settings.DATABASE_ECHO,
    }
    if settings.TESTING:
        kwargs.update({"poolclass": StaticPool})
    return kwargs


def manually_create_all_tables():
    """
    Alembic (with migrations) is used to create tables.
    This method should only be invoked on pytest-runs.

    `alembic upgrade head`
    """
    class MigrationsShouldBeUsed(Exception):
        pass
    raise MigrationsShouldBeUsed("Alembic is used to create tables. (with migrations)")

ENGINE = create_engine(settings.DATABASE_URL, **get_engine_kwargs())
