from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InquiryBase(BaseModel):
    user_message: str

class InquiryCreate(InquiryBase):
    pass

class InquiryUpdate(BaseModel):
    ai_category: Optional[str] = None
    ai_reply: Optional[str] = None
    urgency: Optional[str] = None

class InquiryResponse(InquiryBase):
    id: int
    ai_category: Optional[str]
    ai_reply: Optional[str]
    urgency: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProcessRequest(BaseModel):
    user_message: str

class ProcessResponse(BaseModel):
    category: str
    urgency: str
    reply: str
