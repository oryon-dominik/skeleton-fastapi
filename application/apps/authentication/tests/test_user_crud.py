import pytest

from ....database.dependencies import get_session_override

from ..cryptography import verify_password
from ..models import UserCreate, UserUpdate
from .. import crud


@pytest.mark.usefixtures("user_data_alice")
class TestUserCRUD:

    @pytest.fixture(name="session", scope="class")
    def session_fixture(self):
        return next(get_session_override())

    @pytest.fixture(name="clean_db")
    def clean_db(self, session):
        # delete all users before testing
        users = crud.get_users(session)
        for _user in users:
            crud.delete_user(session, _user)
        users = crud.get_users(session)
        assert users == []

    @pytest.fixture(name="user_db_alice")
    def user_fixture(self, session, user_data_alice, clean_db):
        # create user alice
        alice = crud.create_user(session=session, user=UserCreate(**user_data_alice))
        return alice

    def test_create_user(self, user_db_alice, user_data_alice):
        # user creation was successful
        assert user_db_alice.email == user_data_alice["email"]
        assert user_db_alice.name == user_data_alice["name"]
        assert user_db_alice.disabled == user_data_alice["disabled"]
        assert user_db_alice.scopes == user_data_alice["scopes"]
        assert verify_password(user_data_alice["password"], user_db_alice.password)

    def test_read_user(self, session, user_db_alice, user_data_alice):
        # read user alice
        users = crud.get_users(session)
        assert users == [user_db_alice]
        user = crud.get_user_by_email(session=session, email=user_data_alice["email"])
        assert user == user_db_alice

    def test_update_user(self, session, user_data_alice):
        # update user alice
        updates = {"email": user_data_alice["email"], 'name': 'Alice Wonderdaughter', 'disabled': True}
        updated = crud.update_user(session=session, user=UserUpdate(**updates))
        assert updated.name == updates['name']
        assert updated.disabled == updates['disabled']

    def test_delete_user(self, session, user_db_alice):
        # delete user alice
        success = crud.delete_user(session, user_db_alice)
        assert success
        users = crud.get_users(session)
        assert users == []
