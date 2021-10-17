import secrets
import uuid
import logging

from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from jose import jwt

from ...config import settings


log = logging.getLogger('application')

pwd_context = CryptContext(
    schemes=["bcrypt"],
    bcrypt__default_rounds=13,
    deprecated="auto",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        verified = pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        log.exception("Password in the database is not a valid hash.")
        verified = False
    return verified


def dummy_verify():
    """
    Helper that is called when user wasn’t found, in order to simulate time it would take to hash a password.
    Protection against timing attacks.
    """
    return pwd_context.dummy_verify()


def hash_password(password: str) -> str:
    """
    Get a password hash with a random salt.
    
    Uses salt_chars=passlib.utils.binary.HASH64_CHARS.
    """
    return pwd_context.hash(password)


def compare_hashed_passwords(hashed_password: str, another_hashed_password: str) -> bool:
    """Compare two hashed passwords with compare digest, to obfuscate timing-attacks."""
    return secrets.compare_digest(hashed_password, another_hashed_password)


def create_access_token(subject: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JSON Web Token from subject (username .. ).
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict = subject.copy()
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def generate_uuid() -> str:
    return str(uuid.uuid4())


class JWTAccessToken(str):
    """
    String representation of the header, claims, and signature.
    Signed with ALGORITHMS.HS256.
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, access_token: str):
        """
        Hash the plaintext password.
        """
        if not isinstance(access_token, str):
            raise TypeError("Can only proecess access_token strings")
        # To keep type-annotations exact, return a JWTAccessToken instance
        return cls(access_token)


class HashedPassword(str):
    """
    Hash a plain_password.
    Use as SQLModel-Field.
    """

    @classmethod
    def __get_validators__(cls):
        """
        Yield one or more validators.

        Will be called in yield-order.

        > Inputs for a validator are the values returned from previous validation.
        """
        yield cls.validate

    @classmethod
    def validate(cls, plaintext_password: str):
        """
        Hash the plaintext password.
        """
        if not isinstance(plaintext_password, str):
            raise TypeError("Can only hash passwords from strings")
        hashed_password = hash_password(password=plaintext_password)
        # To keep type-annotations exact, return a HashedPassword instance
        return cls(hashed_password)
