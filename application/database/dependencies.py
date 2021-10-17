from typing import Generator

from sqlmodel import Session, SQLModel
from .sqlmodel import ENGINE

from fastapi import Depends


def get_session() -> Generator:
    with Session(ENGINE) as session:
        yield session

def get_session_override() -> Generator:
    """
    Session for testing and development.
    """
    SQLModel.metadata.create_all(ENGINE)
    with Session(ENGINE) as session:
        yield session


ActiveSession = Depends(get_session)
