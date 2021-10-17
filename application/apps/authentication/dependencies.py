import uuid

from jose import JWTError, jwt
from fastapi import status, HTTPException, Depends, Security, Header
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import ValidationError, EmailStr
from sqlmodel import Session

from ...config import settings
from ...database.dependencies import ActiveSession

from .cryptography import verify_password
from .models import TokenPayload, User
from . import crud


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/token",
    scopes={  # required scopes/permissions for the user to access the API
        "users/whoami": "Read information about the current user."
    },
)


async def valid_authentication_header(authorization: str = Header(...)):
    """
    Check if the authorization header is valid.
    Valid headers look like this:
        {"Authorization": "Bearer THETOKEN"}
    """
    if authorization is None:
        raise HTTPException(status_code=400, detail="No authorization header provided")
    if not "bearer" in authorization.lower():
        raise HTTPException(status_code=401, detail="Invalid authorization header provided")


def get_user_from_db_by_email(session: Session, email: EmailStr) -> User | None:
    user = crud.get_user_by_email(session, email)
    return user


def authenticate_user(session: Session, username: str, password: str) -> User | None | bool:
    """
    Authenticate user by username and password with the database.

    return None if user not found
    return False if password is incorrect
    return user if credentials are valid
    """
    user = get_user_from_db_by_email(session=session, email=username)
    if user is None:
        return None
    if not verify_password(plain_password=password, hashed_password=user.password):
        return False
    return user


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    session: Session = ActiveSession,
):
    """
    Authenticate user by token.

    raise HTTPException if token is invalid.
    raise HTTPException if token is expired.
    raise HTTPException if scopes are not valid.

    return user if token is valid.
    """
    www_authenticate = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": www_authenticate},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    token_scopes = payload.get("scopes", [])

    try: # validate the token payload
        token_payload = TokenPayload(scopes=token_scopes, email=email)
    except ValidationError:
        raise credentials_exception

    user = get_user_from_db_by_email(session=session, email=token_payload.email)
    if user is None:
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in token_payload.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Insufficient privilege.",
                headers={"WWW-Authenticate": www_authenticate},
            )

    return user


async def get_current_active_user(current_user: User = Security(get_current_user, scopes=["users/whoami"])):
    """
    If the user in the token is active, the dependency will return the user.
    """
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive.")
    return current_user


AuthenticatedUser = Depends(get_current_active_user)
