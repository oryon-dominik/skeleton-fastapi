import uuid
from typing import List
from sqlmodel import select, Session

from pydantic import EmailStr
from pydantic.error_wrappers import ValidationError

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.exc import ObjectDeletedError

from .models import User, UserCreate, UserUpdate
from .exceptions import bypass_email_validation_error
from .cryptography import hash_password


def get_user_by_email(session: Session, email: EmailStr) -> User | None:
    """
    Get user by email.
    """
    statement = select(User).where(User.email == email)
    users = session.exec(statement)
    try:
        user = users.one()
    except NoResultFound:
        return None
    return user


def get_user_by_uid(session: Session, uid: str) -> User | None:
    """
    Get user by uuid.
    """
    statement = select(User).where(User.uid == uid)
    users = session.exec(statement)
    try:
        user = users.one()
    except NoResultFound:
        return None
    return user


def get_users(session: Session) -> List[User]:
    """
    Get all users.
    """
    statement = select(User)
    users = session.exec(statement)
    return list(users)


def update_user(session: Session, user: UserUpdate) -> User:
    """
    Update user.
    """
    db_user = get_user_by_email(session=session, email=user.email)
    if db_user is None:
        raise NoResultFound(f"User with email {user.email} does not exist")

    # update
    for key, value in user.dict(exclude_none=True).items():
        setattr(db_user, key, value)

    # commit
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def update_user_password(session: Session, user: User, new_password: str) -> User:
    """
    Update user password.
    """
    # Hash the new-password before update
    hashed = hash_password(new_password)
    # Update the password
    user.password = hashed
    session.add(user)
    # Commit the session
    session.commit()
    session.refresh(user)
    return user

def create_user(session: Session, user: UserCreate) -> User:
    """
    Create a new user.
    """
    db_user = User.from_orm(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_or_create_user(session: Session, user: UserCreate) -> User:
    """
    Get the user by email or create her if the email does not exist.
    """
    try:
        user = create_user(session=session, user=user)
    except ValidationError as e:
        bypass_email_validation_error(e)
        user = get_user_by_email(session=session, email=user.email)

def delete_user(session: Session, user: User) -> bool:
    """
    Delete user.

    returns True if user was deleted, False if user was not found.
    """
    try:
        session.delete(user)
        session.commit()
    except ObjectDeletedError:
        session.rollback()
        return False
    return True
