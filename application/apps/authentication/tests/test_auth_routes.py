import pytest
import httpx

from fastapi.testclient import TestClient

from ....main import app
from ....database.dependencies import get_session_override

from ..cryptography import verify_password

from ..dependencies import get_user_from_db_by_email
from ..models import UserRead
from .fixtures import create_mocked_users

client = TestClient(app)


@pytest.mark.usefixtures("user")
class TestAuthentication:
    token = None

    @pytest.fixture
    def password(self):
        """
        The password for all test-users.

        This fixture will only be available within the scope of TestGroup.
        Will be replaced after the password update with 'new_password'
        """
        return "bar"

    @pytest.fixture
    def new_password(self):
        "replaces the password after update"
        return "baz"

    @pytest.fixture(name="session", scope="class")
    def session_fixture(self):
        return next(get_session_override())

    @pytest.fixture(name="mock_users")
    def mock_users(self, session):
        return create_mocked_users(session=session)

    @pytest.fixture(name="async_client")
    @pytest.mark.asyncio
    async def async_client_fixture(self):
        # override the app dependencies and yield a client
        # app.dependency_overrides[get_session] = get_fixture_session_override
        async with httpx.AsyncClient(app=app, base_url="http://127.0.0.1:8000") as async_client:
            yield async_client
        app.dependency_overrides.clear()

    @pytest.fixture(name="sync_client")
    def sync_client_fixture(self):
        # override the app dependencies and yield a client
        # app.dependency_overrides[get_session] = get_fixture_session_override
        with httpx.Client(app=app, base_url="http://127.0.0.1:8000") as sync_client:
            yield sync_client
        app.dependency_overrides.clear()

    @pytest.fixture()
    def user(self, mock_users, session):
        """This fixture will only be available within the scope of TestGroup"""
        return get_user_from_db_by_email(session=session, email="foo@bar.baz")

    @pytest.fixture()
    def inactive_user(self, mock_users, session):
        """This fixture will only be available within the scope of TestGroup"""
        return get_user_from_db_by_email(session=session, email="inactive@bar.baz")

    @pytest.fixture()
    def unscoped_user(self, mock_users, session):
        """This fixture will only be available within the scope of TestGroup"""
        return get_user_from_db_by_email(session=session, email="unscoped@bar.baz")

    @pytest.fixture()
    async def valid_token(self, password, async_client: httpx.AsyncClient):
        # test_succesful_login_with_testuser
        response = await async_client.post("/api/token", data={"username": "foo@bar.baz", "password": password})
        assert response.status_code == 200
        assert response.json().get("access_token")
        return response.json()["access_token"]

    @pytest.fixture()
    async def valid_but_out_of_scope_token(self, password, async_client: httpx.AsyncClient):
        # test_succesful_login_with_testuser
        response = await async_client.post("/api/token", data={"username": "unscoped@bar.baz", "password": password})
        assert response.status_code == 200
        assert response.json().get("access_token")
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_inactive_user_denied_token(self, password, async_client: httpx.AsyncClient):
        response = await async_client.post("/api/token", data={"username": "inactive@bar.baz", "password": password})
        assert response.status_code == 401
        assert not response.json().get("access_token")
        assert response.json().get("detail") == "Useraccount for 'inactive@bar.baz' is disabled."

    @pytest.mark.asyncio
    async def test_user_out_of_scope_denied_route(self, valid_but_out_of_scope_token, async_client: httpx.AsyncClient):
        """authenticated, but not authorized"""
        response = await async_client.get("/api/whoami", headers={"Authorization": f"Bearer {valid_but_out_of_scope_token}"})
        assert response.status_code == 401
        assert not response.json().get("access_token")
        assert response.json().get("detail") == "Insufficient privilege."

    @pytest.mark.asyncio
    async def test_correct_token_is_valid(self, user, valid_token, async_client: httpx.AsyncClient):
        response = await async_client.get("/api/whoami", headers={"Authorization": f"Bearer {valid_token}"})
        assert response.status_code == 200
        # user-id is a str not a uuid-instance in the response
        user.uid = str(user.uid)
        user_read = UserRead(**user.dict())
        assert response.json() == user_read.dict()
        # user read excludes all sensitive information
        assert response.json() == user.dict(exclude={
            "password": True,
            "uid": True,
            "disabled": True,
            "superuser": True,
            "scopes": True
        })

    def test_password_matches_hash_from_test_db(self, user, password):
        assert verify_password(plain_password=password, hashed_password=user.password)

    @pytest.mark.asyncio
    async def test_no_header_no_auth(self, async_client: httpx.AsyncClient):
        response = await async_client.get("/api/whoami", headers={})
        assert response.status_code == 401
        assert response.json() == {'detail': 'Not authenticated'}

    @pytest.mark.asyncio
    async def test_wrong_header_no_auth(self, valid_token, async_client: httpx.AsyncClient):
        response = await async_client.get("/api/whoami", headers={"Something": f"Bearer {valid_token}"})
        assert response.status_code == 401
        assert response.json() == {'detail': 'Not authenticated'}

    @pytest.mark.asyncio
    async def test_invalid_bearer_no_auth(self, valid_token, async_client: httpx.AsyncClient):
        response = await async_client.get("/api/whoami", headers={"Authorization": f"Invalid {valid_token}"})
        assert response.status_code == 401
        assert response.json() == {'detail': 'Invalid authorization header provided'}

    @pytest.mark.asyncio
    async def test_invalid_token_no_auth(self, async_client: httpx.AsyncClient):
        response = await async_client.get("/api/whoami", headers={"Authorization": f"Bearer wrongtoken"})
        assert response.status_code == 401
        assert response.json() == {'detail': 'Could not validate credentials.'}

    @pytest.mark.asyncio
    async def test_update_password(self, user, valid_token, new_password, session, async_client: httpx.AsyncClient):
        """
        ! After running this test the user has a new password for all following tests
        """
        wrong_password_data = {"password": "new_password", "confirmation": "wrong"}
        response = await async_client.patch(
            "/api/whoami/password",
            headers={"Authorization": f"Bearer {valid_token}"},
            json=wrong_password_data
        )
        assert response.status_code == 409
        assert response.json() == {'detail': 'Passwords do not match'}

        correct_password_data = {"password": new_password, "confirmation": new_password}
        response = await async_client.patch(
            "/api/whoami/password",
            headers={"Authorization": f"Bearer {valid_token}"},
            json=correct_password_data
        )
        assert response.status_code == 200
        user_read = UserRead(**user.dict())
        assert response.json() == user_read.dict()

    @pytest.mark.asyncio
    async def test_old_password_fails_after_update(self, password, async_client: httpx.AsyncClient):
        """
        ! depends on test_update_password
        """
        # test old password fails now
        response = await async_client.post("/api/token", data={"username": "foo@bar.baz", "password": password})
        assert response.status_code == 401
        assert response.json() == {'detail': "Incorrect password for User 'foo@bar.baz'."}

    @pytest.mark.asyncio
    async def test_valid_token_for_new_password(self, password, new_password, async_client: httpx.AsyncClient):
        """
        ! depends on test_update_password
        """
        # test succesful_login with the new password
        response = await async_client.post("/api/token", data={"username": "foo@bar.baz", "password": new_password})
        assert response.status_code == 200
        assert response.json().get("access_token")
