import logging
from datetime import timedelta
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

from fastapi import (
    Depends,
    status,
    APIRouter,
    Response,
    Request,
    HTTPException,
)
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Annotated

from api.utils.success_response import auth_response, success_response
from api.v1.models.user import User
from api.v1.schemas.user import (
    UserCreate, LoginRequest
)
from api.db.database import get_db
from api.v1.services.user import user_service


from api.core.config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])

limiter = Limiter(key_func=get_remote_address)
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=auth_response)
@limiter.limit("5/minute")
def register(
    request: Request,
    response: Response,
    user_schema: UserCreate,
    db: Session = Depends(get_db),
):
    """Endpoint for a user to register their account"""

    user = user_service.create(db=db, schema=user_schema)

    access_token = user_service.create_access_token(user_id=user.id)
    refresh_token = user_service.create_refresh_token(user_id=user.id)

    response = auth_response(
        status_code=201,
        message="User created successfully",
        access_token=access_token,
        data={
            "user": jsonable_encoder(
                user, exclude=["password", "updated_at"]
            )
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=30),
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response


@router.post("/login", status_code=status.HTTP_200_OK, response_model=auth_response)
@limiter.limit("5/minute")
def login(request: Request, login_request: LoginRequest, db:Session = Depends(get_db)):
    """Endpoint to log in a user"""

    user = user_service.authenticate_user(
        db=db, email=login_request.email, password=login_request.password
    )

    access_token = user_service.create_access_token(user_id=user.id)
    refresh_token = user_service.create_refresh_token(user_id=user.id)

    response = auth_response(
        status_code=200,
        message="Login successful",
        access_token=access_token,
        data={
            "user": jsonable_encoder(
                user, exclude=["password", "updated_at"]
            )
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=30),
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response

@router.post("/logout", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to log a user out of their account"""
    response = success_response(status_code=200, message="User logged put successfully")

    # Delete refresh token from cookies
    response.delete_cookie(key="refresh_token")

    return response


@router.post("/refresh-access-token", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")  # Limit to 5 requests per minute per IP
def refresh_access_token(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    """Get a new token for the user from cookie stored token"""

    # Get refresh token
    current_refresh_token = request.cookies.get("refresh_token")

    # Create new access and refresh tokens
    access_token, refresh_token = user_service.refresh_access_token(
        current_refresh_token=current_refresh_token
    )

    response = auth_response(
        status_code=200, message="Login successful", access_token=access_token
    )

    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=30),
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response


@router.post("/admin/login", status_code=status.HTTP_200_OK, response_model=auth_response)
@limiter.limit("5/minute")
def admin_login(request: Request, login_request: LoginRequest, db:Session = Depends(get_db)):
    """Endpoint to log in an administrator"""

    user = user_service.authenticate_user(
        db=db, email=login_request.email, password=login_request.password
    )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges"
        )

    access_token = user_service.create_access_token(user_id=user.id)
    refresh_token = user_service.create_refresh_token(user_id=user.id)

    response = auth_response(
        status_code=200,
        message="Admin login successful",
        access_token=access_token,
        data={
            "user": jsonable_encoder(user, exclude=["password", "updated_at"])
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=30),
        httponly=True,
        secure=True,
        samesite="none"
    )

    return response