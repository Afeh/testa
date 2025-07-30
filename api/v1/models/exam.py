import enum 
from sqlalchemy import (Column, String, ForeignKey, Integer, Date, Enum as SQLAlchemyEnum, Boolean, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB

from api.v1.models.base import BaseTableModel


class ExamLevel(str, enum.Enum):
    FOUNDATION = "Foundation"
    SKILLS = "Skills"
    PROFESSSIONAL = "Professional"

class QuestionType(str, enum.Enum):
    OBJECTIVE = "Objective"
    THEORY = "Theory"

class ExamDiet(str, enum.Enum):
    MARCH = "March"
    JULY = "JULY"
    NOVEMBER = "November"


class Paper(BaseTableModel):
    __tablename__ = 'papers'

    title = Column(String, nullable=False, unique=True)
    level = Column(SQLAlchemyEnum(ExamLevel), nullable=False)
    exams = relationship("Exam", back_populates="paper", cascade="all, delete-orphan")
    user_credits = relationship("UserPaperCredit", back_populates="paper", cascade="all, delete-orphan")


class Exam(BaseTableModel):
    __tablename__ = 'exams'

    paper_id = Column(UUID(as_uuid=True), ForeignKey('papers.id'), nullable=False)
    diet = Column(SQLAlchemyEnum(ExamDiet), nullable=False)
    year = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, default=180)
    total_score = Column(Integer, default=100)
    pass_mark = Column(Integer, default=50)

    paper = relationship("Paper", back_populates="exams")

    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")

    user_sessions = relationship("UserExamSession", back_populates="exam")


class Question(BaseTableModel):
    __tablename__ = 'questions'

    exam_id = Column(UUID(as_uuid=True), ForeignKey('exams.id'), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(SQLAlchemyEnum(QuestionType), nullable=False)

    options = Column(JSONB, nullable=True)
    correct_answer = Column(Text, nullable=False)

    exam = relationship("Exam", back_populates="questions")


class UserExamSession(BaseTableModel):
    __tablename__ = "user_exam_sessions"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey('exams.id'), nullable=False)
    score = Column(Integer, nullable=True)

    submitted_answers = Column(JSONB, nullable=True)

    start_time = Column(Date, nullable=False)
    end_time = Column(Date, nullable=True)

    user = relationship("User", back_populates="exam_sessions")
    exam = relationship("Exam", back_populates="user_sessions")


class UserPaperCredit(BaseTableModel):
    __tablename__ = "user_paper_credits"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    paper_id =  Column(UUID(as_uuid=True), ForeignKey('papers.id'), nullable=False)
    passed = Column(Boolean, default=True)

    passed_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="paper_credits")
    paper = relationship("Paper", back_populates="user_credits")

