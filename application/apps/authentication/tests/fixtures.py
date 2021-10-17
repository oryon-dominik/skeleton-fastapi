from ....config import settings
from ....common.exceptions import CreateFixturesInTestmodeOnly

from .. import crud
from ..models import UserCreate

def create_mocked_users(session):
    if not settings.TESTING:
        raise CreateFixturesInTestmodeOnly("Mocked user fixtures should be created in testmode only.")
    new_users = [
        crud.get_or_create_user(session=session, user=UserCreate(**user))
        for user in user_fixtures.values()
    ]
    return new_users


user_fixtures = {  # using emails as primary username keys
    "alice@acid.net": {
        "name": "Alice Wonderson",
        "email": "alice@acid.net",
        "password": "bar",
        "disabled": False,
        "scopes": "users/whoami"
    },
    "foo@bar.baz": {
        "name": "Foo Bar Baz",
        "email": "foo@bar.baz",
        "password": "bar",
        "disabled": False,
        "scopes": "users/whoami"
    },
    "inactive@bar.baz": {
        "name": "Inactive Foo Bar Baz",
        "email": "inactive@bar.baz",
        "password": "bar",
        # omitting "disabled": True, as this should be the default
        "scopes": "users/whoami"
    },
    "unscoped@bar.baz": {
        "name": "Unscoped Foo Bar Baz",
        "email": "unscoped@bar.baz",
        "password": "bar",
        "disabled": False,
        # omitting "scopes": "unauthorized", as these should be the defaults
    },
}
