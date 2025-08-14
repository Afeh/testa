from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from api.db.database import get_db
from api.v1.schemas.exam import PaperResponse, PaperDetailResponse
from api.v1.services.paper import paper_service

router = APIRouter(prefix="/papers", tags=["Papers"])

@router.get("/", response_model=List[PaperResponse])
def get_all_papers(db: Session = Depends(get_db)):
    """
    Get a list of all available exam papers.
    This is a public endpoint.
    """
    papers = paper_service.fetch_all(db=db)
    return papers

@router.get("/{paper_id}", response_model=PaperDetailResponse)
def get_paper_by_id(paper_id: UUID, db: Session = Depends(get_db)):
    """
    Get a single exam paper by its unique ID.
    This is a public endpoint.
    """
    paper = paper_service.fetch_one(db=db, paper_id=paper_id)
    return paper