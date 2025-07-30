from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from api.v1.models.exam import ExamLevel, ExamDiet, QuestionType

class PaperBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    level: ExamLevel


class PaperCreate(PaperBase):
    pass


class PaperResponse(PaperBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    paper_id: str
    diet: ExamDiet
    year: int = Field(..., gt=2020)
    duration_minutes: int = Field(default=180, gt=0)
    pass_mark: int = Field(default=50, ge=0, le=100)


class ExamCreate(ExamBase):
    pass


class ExamResponse(ExamBase):
    id: str
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
    id: str
    exam_id: str
    created_at: datetime

    class Config:
        from_attributes = True
