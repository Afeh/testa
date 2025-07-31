from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from pydantic import UUID4

from api.v1.models.exam import ExamLevel, ExamDiet, QuestionType

class PaperBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    level: ExamLevel


class PaperCreate(PaperBase):
    pass


class PaperResponse(PaperBase):
    id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    paper_id: UUID4
    diet: ExamDiet
    year: int = Field(..., gt=2020)
    duration_minutes: int = Field(default=180, gt=0)
    pass_mark: int = Field(default=50, ge=0, le=100)


class ExamCreate(ExamBase):
    pass


class ExamResponse(ExamBase):
    id: UUID4
    created_at: datetime
    paper: PaperResponse

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: str


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: UUID4
    exam_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionForStudent(BaseModel):
    """A question schema that hides the correct answer."""
    id: UUID4
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ExamSessionResponse(BaseModel):
    session_id: UUID4
    exam_title: str
    duration_minutes: int
    questions: List[QuestionForStudent]

class UserAnswer(BaseModel):
    question_id: UUID4
    answer: str

class ExamSubmission(BaseModel):
    answers: List[UserAnswer]