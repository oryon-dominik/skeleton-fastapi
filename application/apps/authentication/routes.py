from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlmodel import Session

from ...config import settings, validators
from ...database.dependencies import ActiveSession

from .dependencies import AuthenticatedUser, authenticate_user
from .cryptography import create_access_token, JWTAccessToken

from .models import User, Token, UserRead, NewPassword
from . import crud


protected_router = APIRouter(
    prefix="",
    tags=["authentication"],
)
public_router = APIRouter(
    prefix="",
    tags=["authentication"],
)


@protected_router.get("/whoami", tags=["authentication"], response_model=UserRead)
async def display_authenticated_user(current_user: User = AuthenticatedUser):
    """Display the current authenticated user's information."""
    return current_user


@protected_router.patch("/whoami/password", tags=["authentication"], response_model=UserRead)
async def change_password(patch: NewPassword, current_user: User = AuthenticatedUser, session: Session = ActiveSession):
    """Change user's password: send a body with 'password' & 'confirmation'."""
    # Check if the passwords match
    if not patch.password == patch.confirmation:
        raise HTTPException(status_code=409, detail="Passwords do not match")
    user = crud.update_user_password(session=session, user=current_user, new_password=patch.password)
    return user


@public_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = ActiveSession):
    """
    OAuth2 compatible token login, get an access token for future requests.

    raises HTTPException(401) if user could not be found.  
    raises HTTPException(401) if user could not be authenticated.  
    raises HTTPException(401) if user disabled.  
    """
    username = form_data.username
    user = authenticate_user(session=session, username=username, password=form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User matching '{username}' not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect password for User '{username}'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Useraccount for '{username}' is disabled.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # scopes have been validated
    scopes: list = validators.dissassemble_comma_seperated_lists_of_strings(user.scopes)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token: JWTAccessToken = create_access_token(
        subject={
            "sub": user.email,
            "scopes": scopes,
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
