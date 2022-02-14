import inspect
import re
from typing import List

from pathlib import Path
from importlib import import_module


ROOT_DIR = Path(__file__).parent.parent.parent


def get_all_app_names() -> List[str]:
    """
    Return all apps that should be migrated with alembic revisions.
    """
    return [p.name for p in (ROOT_DIR / 'application' / 'apps').iterdir() if p.is_dir() and not p.name.startswith('__')]


def get_table_paths_for_module(module_path: str) -> list:
    """
    For one module_path return all dotnotated import paths for classes that should be migrated with alembic revisions.
    """
    try:
        module = import_module(module_path)
    except ModuleNotFoundError:
        return []

    return [
        f"{klass.__module__}.{name}"
        for name, klass in inspect.getmembers(module, inspect.isclass)
        if module_path == klass.__module__ and
            re.match(f"\Aclass\s{name}\((.*)table(.*)=(.*)True(.*)\)\:", inspect.getsource(klass))
    ]



def get_all_revision_paths() -> List[str]:
    """
    Return all dotnotated import paths for classes that should be migrated with alembic revisions.
    """
    matches = []
    for app in get_all_app_names():
        matches.extend(get_table_paths_for_module(f"application.apps.{app}.models"))
    return matches
