from email_validator import validate_email, EmailNotValidError
import dns.resolver
from datetime import datetime
from typing import (Optional, Union,
                    List, Annotated, Dict,
                    Literal)

from pydantic import (BaseModel, EmailStr,
                      field_validator, ConfigDict,
                      StringConstraints,
                      model_validator)
                      
from pydantic import Field  # Added this import

def validate_mx_record(domain: str):
    """
    Validate mx records for email
    """
    try:
        # Try to resolve the MX record for the domain
        mx_records = dns.resolver.resolve(domain, 'MX')
        return True if mx_records else False
    except dns.resolver.NoAnswer:
        return False
    except dns.resolver.NXDOMAIN:
        return False
    except Exception:
        return False
    

class UserUpdate(BaseModel):
    
    first_name : Optional[str] = None
    last_name : Optional[str] = None

class UserData(BaseModel):
    """
    Schema for users to be returned to superadmin
    """
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: str
    phone_number: str
    ican_number: str
    is_active: bool
    is_admin: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AllUsersResponse(BaseModel):
    """
    Schema for all users
    """
    message: str
    status_code: int
    status: str
    page: int
    per_page: int
    total: int
    data: Union[List[UserData], List[None]]

class UserBase(BaseModel):
    """Base user schema"""

    id: str
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime


class UserCreate(BaseModel):
    """Schema to create a user"""

    email: EmailStr
    password: Annotated[
        str, StringConstraints(
            min_length=8,
            max_length=64,
            strip_whitespace=True
        )
    ]
    """Added the confirm_password field to UserCreate Model"""
    confirm_password: Annotated[
        str, 
        StringConstraints(
            min_length=8,
            max_length=64,
            strip_whitespace=True
        ),
        Field(exclude=True)  # exclude confirm_password field
    ]
    first_name: Annotated[
        str, StringConstraints(
            min_length=3,
            max_length=30,
            strip_whitespace=True
        )
    ]
    last_name: Annotated[
        str, StringConstraints(
            min_length=3,
            max_length=30,
            strip_whitespace=True
        )
    ]
    phone_number: Annotated[
        str, StringConstraints(
            min_length=11,
            max_length=11,
            strip_whitespace=True
        )
    ]
    ican_number: Annotated[
        str, StringConstraints(
            min_length=3,
            max_length=30,
            strip_whitespace=True
        )
    ]

    @model_validator(mode='before')
    @classmethod
    def validate_password(cls, values: dict):
        """
        Validates passwords
        """
        password = values.get('password')
        confirm_password = values.get('confirm_password') # gets the confirm password
        email = values.get("email")

        # constraints for password
        if not any(c.islower() for c in password):
            raise ValueError("password must include at least one lowercase character")
        if not any(c.isupper() for c in password):
            raise ValueError("password must include at least one uppercase character")
        if not any(c.isdigit() for c in password):
            raise ValueError("password must include at least one digit")
        if not any(c in ['!','@','#','$','%','&','*','?','_','-'] for c in password):
            raise ValueError("password must include at least one special character")

        """Confirm Password Validation"""

        if not confirm_password:
            raise ValueError("Confirm password field is required")
        elif password != confirm_password:
            raise ValueError("Passwords do not match")
        
        try:
            email = validate_email(email, check_deliverability=True)
            if email.domain.count(".com") > 1:
                raise EmailNotValidError("Email address contains multiple '.com' endings.")
            if not validate_mx_record(email.domain):
                raise ValueError('The domain for this email is invalid or does not accept mail.')
        except EmailNotValidError as exc:
            # FIX: Convert the exception object to a string
            raise ValueError(str(exc))
        except Exception as exc:
            # FIX: Convert the exception object to a string
            raise ValueError(str(exc))
        
        return values

class Token(BaseModel):
    token: str


class TokenData(BaseModel):
    """Schema to structure token data"""

    id: Optional[str]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    @model_validator(mode='before')
    @classmethod
    def validate_password(cls, values: dict):
        """
        Validates passwords
        """
        if not isinstance(values, dict):
            return values
        password = values.get('password')
        email = values.get("email")

        # constraints for password
        if not any(c.islower() for c in password):
            raise ValueError("password must include at least one lowercase character")
        if not any(c.isupper() for c in password):
            raise ValueError("password must include at least one uppercase character")
        if not any(c.isdigit() for c in password):
            raise ValueError("password must include at least one digit")
        if not any(c in ['!','@','#','$','%','&','*','?','_','-'] for c in password):
            raise ValueError("password must include at least one special character")
        
        try:
            email_info = validate_email(email, check_deliverability=True)
            if email_info.domain.count(".com") > 1:
                raise EmailNotValidError("Email address contains multiple '.com' endings.")
            if not validate_mx_record(email_info.domain):
                raise ValueError('The domain for this email is invalid or does not accept mail.')
        except EmailNotValidError as exc:
            # FIX: Convert the exception object to a string
            raise ValueError(str(exc))
        except Exception as exc:
            # FIX: Convert the exception object to a string
            raise ValueError(str(exc))
        
        return values
