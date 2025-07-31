from uuid import UUID
from typing import Any, Optional
import datetime as dt
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from passlib.context import CryptContext

from api.utils.db_validators import check_model_existence

from api.core.services import Service
from api.db.database import get_db
from api.core.config import settings
from api.v1.models.user import User
from api.v1.schemas import user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService(Service):

    def fetch_all(
        self,
        db: Session,
        page: int,
        per_page: int,
        **query_params: Optional[Any],
    ):
        """
        Fetch all users
        Args:
            db: database Session object
            page: page number
            per_page: max number of users in a page
            query_params: params to filter by
        """
        per_page = min(per_page, 10)

        # Enable filter by query parameter
        filters = []
        if all(query_params):
            # Validate boolean query parameters
            for param, value in query_params.items():
                if value is not None and not isinstance(value, bool):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid value for '{param}'. Must be a boolean.",
                    )
                if value == None:
                    continue
                if hasattr(User, param):
                    filters.append(getattr(User, param) == value)
        query = db.query(User)
        total_users = query.count()
        if filters:
            query = query.filter(*filters)
            total_users = query.count()

        all_users: list = (
            query.order_by(desc(User.created_at))
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all()
        )

        return self.all_users_response(all_users, total_users, page, per_page)
    

    def all_users_response(
        self, users: list, total_users: int, page: int, per_page: int
    ):
        """
        Generates a response for all users
        Args:
            users: a list containing user objects
            total_users: total number of users
        """
        if not users or len(users) == 0:
            return user.AllUsersResponse(
                message="No User(s) for this query",
                status="success",
                status_code=200,
                page=page,
                per_page=per_page,
                total=0,
                data=[],
            )
        all_users = [
            user.UserData.model_validate(usr, from_attributes=True)
            for usr in users
        ]
        return user.AllUsersResponse(
            message="Users successfully retrieved",
            status="success",
            status_code=200,
            page=page,
            per_page=per_page,
            total=total_users,
            data=all_users,
        )

    def fetch(self, db: Session, id):
        """Fetches a user by their id"""

        user = check_model_existence(db, User, id)

        # return user if user is not active
        return user


    def create(self, db: Session, schema: user.UserCreate):
        if db.query(User).filter(User.email == schema.email).first():
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists",
            )

        if db.query(User).filter(User.ican_number == schema.ican_number).first():
            raise HTTPException(
                status_code=400,
                detail="User with this ican_number already exists",
            )

        
        schema.password = self.hash_password(password=schema.password)

        user = User(**schema.model_dump())
        db.add(user)
        db.commit()
        db.refresh(user)

        return user
    
    def delete(
        self,
        db: Session,
        id: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        """Function to soft delete a user"""

        # Get user by id if provided, otherwise fetch user access token
        if id:
            user = check_model_existence(db, User, id)
        elif access_token:
            user = self.get_current_user(access_token, db)
        else:
            raise HTTPException(
                status_code=400, detail="User ID or access token required"
            )

        user.is_active = True
        db.commit()

    def update(
        self, db: Session, current_user: User, schema: user.UserUpdate, id=None
    ):
        """Function to update a User"""

        target_id = id if id is not None else current_user.id
        
        user_to_update = self.fetch(db=db, id=target_id)
        
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User to update not found.")
        
        # An admin could update anyone's.
        if not current_user.is_admin and current_user.id != user_to_update.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this user.")
            
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "email":
                continue
            setattr(user_to_update, key, value)
        
        db.commit()
        db.refresh(user_to_update)
        return user_to_update

    def hash_password(self, password: str) -> str:
        """Function to hash a password"""

        hashed_password = pwd_context.hash(secret=password)
        return hashed_password
    
    def create_access_token(self, user_id: UUID) -> str:
        """Function to create access token"""

        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        data = {"user_id": str(user_id), "exp": expires, "type": "access"}
        encoded_jwt = jwt.encode(data, settings.SECRET_KEY, settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, user_id: UUID) -> str:
        """Function to create access token"""

        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            days=settings.JWT_REFRESH_EXPIRY
        )
        data = {"user_id": str(user_id), "exp": expires, "type": "refresh"}
        encoded_jwt = jwt.encode(data, settings.SECRET_KEY, settings.ALGORITHM)
        return encoded_jwt

    def verify_access_token(self, access_token: str, credentials_exception):
        """Funtcion to decode and verify access token"""

        try:
            payload = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id = payload.get("user_id")
            token_type = payload.get("type")

            if user_id is None:
                raise credentials_exception

            if token_type == "refresh":
                raise HTTPException(
                    detail="Refresh token not allowed", status_code=400
                )

            token_data = user.TokenData(id=user_id)

        except JWTError as err:
            print(err)
            raise credentials_exception

        return token_data

    def verify_refresh_token(self, refresh_token: str, credentials_exception):
        """Funtcion to decode and verify refresh token"""

        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id = payload.get("user_id")
            token_type = payload.get("type")

            if user_id is None:
                raise credentials_exception

            if token_type == "access":
                raise HTTPException(
                    detail="Access token not allowed", status_code=400
                )

            token_data = user.TokenData(id=user_id)

        except JWTError:
            raise credentials_exception

        return token_data

    def refresh_access_token(self, current_refresh_token: str):
        """Function to generate new access token and rotate refresh token"""

        credentials_exception = HTTPException(
            status_code=401, detail="Refresh token expired"
        )

        token = self.verify_refresh_token(
            current_refresh_token, credentials_exception
        )

        if token:
            access = self.create_access_token(user_id=token.id)
            refresh = self.create_refresh_token(user_id=token.id)

            return access, refresh

    def authenticate_user(self, db: Session, email: str, password: str):
        """Function to authenticate a user"""

        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=400, detail="Invalid user credentials"
            )

        if not self.verify_password(password, user.password):
            raise HTTPException(
                status_code=400, detail="Invalid user credentials"
            )

        return user
    
    def hash_password(self, password: str) -> str:
        """Function to hash a password"""

        hashed_password = pwd_context.hash(secret=password)
        return hashed_password

    def verify_password(self, password: str, hash: str) -> bool:
        """Function to verify a hashed password"""

        return pwd_context.verify(secret=password, hash=hash)


    def get_current_user(
        self,
        access_token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
    ) -> User:
        """Function to get current logged in user"""

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        token = self.verify_access_token(access_token, credentials_exception)
        if not token:
             raise credentials_exception
        user = db.query(User).filter(User.id == token.id).first()
        if not user:
            raise credentials_exception
        return user

    def get_current_admin_user(self, current_user: User) -> User:
        """
        Verifies if a given user object is an admin.
        Raises a 403 Forbidden error if the user is not an admin.
        """
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have adequate permissions"
            )
        return current_user


user_service = UserService()