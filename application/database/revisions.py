"""
All database tables get automaticlly registered here, that should be migrated with alembic revisions.
Run `alembic upgrade head` or `cc makemigrations` after registering new models.
"""

from importlib import import_module
from ..common.imports import get_all_revision_paths

for rp in get_all_revision_paths():
    try:
        import_module(rp)
    except ImportError:
        pass
