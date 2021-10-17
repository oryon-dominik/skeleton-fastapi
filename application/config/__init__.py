"""provide a consistens django-like API for all settings"""

from .base import get_settings, ROOT_DIR, Settings

settings = get_settings()
