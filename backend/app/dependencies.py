
import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
):
    secret_key = os.getenv("SECRET_KEY")
    expected_username = os.getenv("ADMIN_USERNAME")
    algorithm = os.getenv("ALGORITHM", "HS256")

    if (
        not secret_key
        or secret_key == "replace_with_a_long_random_secret_key"
        or not expected_username
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin security settings are not configured",
        )

    if algorithm != "HS256":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unsupported JWT algorithm configuration",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret_key,
            algorithms=["HS256"],
            options={"require": ["sub", "role", "exp"]},
        )

        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access only",
            )

        if payload.get("sub") != expected_username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid admin identity",
            )

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_participant(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
):
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")

    if (
        not secret_key
        or secret_key == "replace_with_a_long_random_secret_key"
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Participant security settings are not configured",
        )

    if algorithm != "HS256":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unsupported JWT algorithm configuration",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Participant authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret_key,
            algorithms=["HS256"],
            options={"require": ["sub", "role", "exp"]},
        )

        if payload.get("role") != "participant":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Participant access only",
            )

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired participant token",
            headers={"WWW-Authenticate": "Bearer"},
        )
