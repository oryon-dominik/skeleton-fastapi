from typing import Optional

from fastapi import HTTPException

from ..config import settings


class CommonQueryParams:
    def __init__(self, q: Optional[str] = None, offset: int = 0, limit: int = 100):
        self.q = q
        self.offset = offset
        self.limit = offset


async def block_request_when_in_production(_settings=None):
    if _settings is None:
        _settings = settings
    if _settings.PRODUCTION:
        raise HTTPException(status_code=400, detail='This endpoint is not available in production')
    return _settings.DEBUG
