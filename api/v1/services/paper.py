from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload
from uuid import UUID

from api.v1.models.exam import Paper

class PaperService:
    def fetch_all(self, db: Session):
        """Fetches all papers from the database."""
        return db.query(Paper).order_by(Paper.title).all()

    def fetch_one(self, db: Session, paper_id: UUID):
        """Fetches a single paper by its ID, eagerly loading related exams and credits."""
        
        paper = (
            db.query(Paper)
            .options(
                selectinload(Paper.exams),
                selectinload(Paper.user_credits)
            )
            .filter(Paper.id == paper_id)
            .first()
        )
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paper with ID {paper_id} not found."
            )
        return paper

paper_service = PaperService()