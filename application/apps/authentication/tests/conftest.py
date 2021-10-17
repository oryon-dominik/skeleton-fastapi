import pytest

from .fixtures import user_fixtures

@pytest.fixture
def user_data_alice() -> dict:
    return user_fixtures['alice@acid.net']
