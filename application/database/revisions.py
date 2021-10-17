"""
Register all database tables here, that should be migrated with alembic revisions.
Run `alembic upgrade head` or `cc makemigrations` after registering new models here.
"""

from ..apps.authentication.models import User
