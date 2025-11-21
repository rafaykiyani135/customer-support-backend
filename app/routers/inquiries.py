from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.inquiries import Inquiry
from ..schemas import InquiryResponse, InquiryCreate

router = APIRouter(
    prefix="/inquiries",
    tags=["inquiries"]
)

@router.post("/create", response_model=InquiryResponse)
def create_inquiry(inquiry: InquiryCreate, db: Session = Depends(get_db)):
    # This endpoint might be used if we just want to save without processing immediately,
    # or if we process elsewhere. For now, let's just save.
    db_inquiry = Inquiry(user_message=inquiry.user_message)
    db.add(db_inquiry)
    db.commit()
    db.refresh(db_inquiry)
    return db_inquiry

@router.get("/all", response_model=List[InquiryResponse])
def get_all_inquiries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Inquiry).order_by(Inquiry.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=InquiryResponse)
def get_inquiry(id: int, db: Session = Depends(get_db)):
    inquiry = db.query(Inquiry).filter(Inquiry.id == id).first()
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return inquiry

@router.delete("/{id}")
def delete_inquiry(id: int, db: Session = Depends(get_db)):
    inquiry = db.query(Inquiry).filter(Inquiry.id == id).first()
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    db.delete(inquiry)
    db.commit()
    return {"ok": True}

@router.delete("/reset/all")
def reset_database(db: Session = Depends(get_db)):
    """
    Deletes all inquiries from the database.
    """
    try:
        num_deleted = db.query(Inquiry).delete()
        db.commit()
        return {"message": f"Deleted {num_deleted} inquiries"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
