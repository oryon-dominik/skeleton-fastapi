from typing import Generator

from sqlmodel import Session
from .sqlmodel import ENGINE

from fastapi import Depends


def get_session() -> Generator:
    with Session(ENGINE) as session:
        yield session


ActiveSession = Depends(get_session)
