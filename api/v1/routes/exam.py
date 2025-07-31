from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from api.db.database import get_db
from api.v1.models.user import User
from api.v1.models.exam import Paper, Exam, UserPaperCredit, UserExamSession
from api.v1.schemas.exam import QuestionResponse

from api.v1.schemas.exam import ExamSessionResponse, ExamSubmission

from api.v1.services.user import user_service

router = APIRouter(prefix="/exams", tags=["Exams"])

@router.get("/available")
def get_available_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    """
    Fetches a list of exams the current user is eligible to take based on their level.
    """

    passed_paper_credits = db.query(UserPaperCredit.paper_id).filter(
        UserPaperCredit.user_id == current_user.id
    ).all()
    passed_paper_ids = {pid for (pid,) in passed_paper_credits}

    foundation_papers_count = db.query(Paper).filter(Paper.level == 'Foundation').count()

    skills_papers_count = db.query(Paper).filter(Paper.level == 'Skills').count()

    passed_foundation_count = db.query(Paper).filter(
        Paper.id.in_(passed_paper_ids), Paper.level == 'Foundation'
    ).count()

    current_level = 'Foundation'
    if passed_foundation_count >= foundation_papers_count:
        current_level = 'Skills'

        passed_skills_count = db.query(Paper).filter(
            Paper.id.in_(passed_paper_ids), Paper.level == 'Skills'
        ).count()
        if passed_skills_count >= skills_papers_count:
            current_level = 'Professional'


    eligible_papers = db.query(Paper).filter(
        Paper.level == current_level,
        Paper.id.notin_(passed_paper_ids)
    ).all()
    eligible_paper_ids = [paper.id for paper in eligible_papers]

    available_exams = db.query(Exam).filter(
        Exam.paper_id.in_(eligible_paper_ids)
    ).all()
    
    return available_exams


@router.post("/{exam_id}/start", response_model=ExamSessionResponse)
def start_exam_session(
    exam_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    """
    Starts a new exam session for the user and returns the questions.
    """

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    existing_session = db.query(UserExamSession).filter(
        UserExamSession.user_id == current_user.id,
        UserExamSession.exam_id == exam_id,
        UserExamSession.end_time == None
    ).first()

    if existing_session:
        raise HTTPException(status_code=400, detail="You already have an active session for this exam.")
    
    new_session = UserExamSession(
        user_id=current_user.id,
        exam_id=exam_id,
        start_time=date.today()
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "session_id": new_session.id,
        "exam_title": exam.paper.title,
        "duration_minutes": exam.duration_minutes,
        "questions": exam.questions
    }


@router.post("/{session_id}/submit")
def submit_exam_answers(
    session_id: UUID,
    submission: ExamSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    """
    Submits a user's answers, grades them, and finalizes the session.
    """

    session = db.query(UserExamSession).filter(
        UserExamSession.id == session_id,
        UserExamSession.user_id == current_user.id,
        UserExamSession.end_time == None
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Active exam session not found.")
    
    correct_answers = {
        str(q.id): q.correct_answer for q in session.exam.questions
    }

    score = 0
    total_questions = len(session.exam.questions)

    for user_answer in submission.answers:
        question_id_str = str(user_answer.question_id)
        if question_id_str in correct_answers and user_answer.answer == correct_answers[question_id_str]:
            score += 1

    final_score = (score / total_questions) * 100 if total_questions > 0 else 0

    session.score = final_score
    session.end_time = date.today()
    session.submitted_answers = submission.model_dump_json()

    passed = final_score >= session.exam.pass_mark

    if passed:
        # Check if a credit already exists to avoid duplicates
        existing_credit = db.query(UserPaperCredit).filter(
            UserPaperCredit.user_id == current_user.id,
            UserPaperCredit.paper_id == session.exam.paper_id
        ).first()
        
        if not existing_credit:
            new_credit = UserPaperCredit(
                user_id=current_user.id,
                paper_id=session.exam.paper_id,
                passed=True,
                passed_date=date.today()
            )
            db.add(new_credit)
            
    db.commit()

    return {
        "message": "Exam submitted successfully!",
        "score": final_score,
        "passed": passed
    }