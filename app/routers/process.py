from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.inquiries import Inquiry
from ..schemas import ProcessRequest, InquiryResponse
from ..services.llm_service import process_inquiry_with_llm

router = APIRouter(
    prefix="/process",
    tags=["process"]
)

@router.post("/", response_model=InquiryResponse)
def process_inquiry(request: ProcessRequest, db: Session = Depends(get_db)):
    # 1. Process with LLM
    llm_result = process_inquiry_with_llm(request.user_message)
    
    # 2. Save to DB
    db_inquiry = Inquiry(
        user_message=request.user_message,
        ai_category=llm_result.get("category"),
        urgency=llm_result.get("urgency"),
        ai_reply=llm_result.get("reply")
    )
    db.add(db_inquiry)
    db.commit()
    db.refresh(db_inquiry)
    
    return db_inquiry
