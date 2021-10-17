import uuid
from typing import List, Optional
from pydantic import EmailStr, BaseModel
from sqlmodel import Field, SQLModel, Relationship
from pydantic import validator

from ...config import settings
from ...config import validators

from .cryptography import HashedPassword, JWTAccessToken, generate_uuid
from .exceptions import EmailDoesExist


class Token(SQLModel):
    """
    Token Model representing the token in authentication-process
    """
    access_token: JWTAccessToken
    token_type: str

    @validator("token_type")
    @classmethod
    def validate_token_type(cls, value):
        """Validate if the token-type is bearer."""
        if not value == "bearer":
            raise ValueError(f"Invalid token-type: {value}")
        return value


class TokenPayload(SQLModel):
    """
    Token Payload used for validating the token ingredients (the payload) have the correct types.
    """
    email: EmailStr
    scopes: List[str] = []

    @validator("scopes")
    @classmethod
    def validate_scopes(cls, scopes):
        """Validate if the scope is valid."""
        if not all([scope in settings.VALID_SCOPES for scope in scopes]):
            raise ValueError(f'Scopes {scopes} not in VALID_SCOPES')
        return scopes


class NewPassword(SQLModel):
    password: str
    confirmation: str


class UserBase(SQLModel):
    """
    Base class for every User-Model.
    All users have an email, and a name.

    Full names are preferred over the separation into first and last names due to internationalization.

    SQLModels have orm_mode = True by default.
    """
    email: EmailStr = Field(default=None)
    name: Optional[str] = Field(default=None)


class User(UserBase, table=True):
    """
    User Model representing a user in the database.
    
    uid > str: (UUID4), auto-generated uuid (as str repr).
    password > Str, will be hashed upon creation. Never save the password in plaintext. ;-)
    scopes > Comma seperated list of routes allowed for this user. Example: "users/whoami"
    disabled > Boolean, if the user has been activated or blocked.
    superuser > Boolean, if the user is a superuser.

    """
    uid: Optional[str] = Field(default_factory=generate_uuid, primary_key=True, index=True)
    password: Optional[HashedPassword]
    scopes: Optional[str] = "unauthorized"
    disabled: Optional[bool] = True
    superuser: Optional[bool] = False

    @validator("email")  # TODO: validate through unique constraint on database level
    @classmethod
    def validate_email_is_unique(cls, email):
        """Validate if the email is unique."""
        # lazy imports
        from . import crud
        from ...database.dependencies import get_session
        # generate a new sesison
        session = next(get_session())
        existing_users = crud.get_users(session)
        existing_emails = [u.email for u in existing_users]
        if email in existing_emails:
            raise EmailDoesExist(f"User with email {email} already exists")
        return email

    @validator("scopes")
    @classmethod
    def validate_scopes(cls, value):
        """Validate if the scope is valid."""
        scopes = validators.dissassemble_comma_seperated_lists_of_strings(value)
        if not all([scope in settings.VALID_SCOPES for scope in scopes if scopes]):
            raise ValueError(f'Scope {value} not in VALID_SCOPES')
        return value


# -- User CRUD Models----------------------------------------------------------
class UserCreate(UserBase):
    """
    Model used to retrieve the data be posted on routes.
    
    It works like this:
    
        user_to_be_created = UserCreate(
            email,
            name,
            password,
            Optional[scopes],
            Optional[disabled],
            Optional[superuser]
        )

    That instance will be validated by the view and then auto-converting its types.

    To add the UserCreate instance to the database, convert it to a User instance.
    -> db_user = User.from_orm(user_to_be_created)
    """
    password: str
    scopes: Optional[str] = ""
    disabled: Optional[bool] = True
    superuser: Optional[bool] = False


class UserRead(UserBase):
    """
    UserRead is used as a response model for the routes.
    A UserRead instance only reveals the name and email of a user.
    """
    pass


class UserUpdate(SQLModel):
    """
    Update a User's fields.
    Duplicated code, because on update ALL fields are optional.

    See User & UserBase Model for explanation of the field's details.
    The conversion works the same, as in the create-model.
    -> db_user = User.from_orm(user_to_be_updated)
    """
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    scopes: Optional[str] = None
    disabled: Optional[bool] = None
    superuser: Optional[bool] = None
