from sqlalchemy.orm import relationship

from sqlalchemy import Column, String, text, Boolean, Index
from api.v1.models.base import BaseTableModel


class User(BaseTableModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, server_default=text("true"))
    is_admin = Column(Boolean, server_default=text("false"))
    is_verified = Column(Boolean, server_default=text("false"))
    ican_number = Column(String, unique=True, nullable=False)

    exam_sessions = relationship("UserExamSession", back_populates="user", cascade="all, delete-orphan")
    paper_credits = relationship("UserPaperCredit", back_populates="user", cascade="all, delete-orphan")


    def to_dict(self):
        obj_dict = super().to_dict()
        obj_dict.pop("password")
        return obj_dict

    def __str__(self):
        return self.email


