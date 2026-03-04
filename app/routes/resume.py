import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app import models, database
from app.models import Resume
from app.oauth2 import get_current_user
from app.services.resume_parser import extract_text_from_pdf

router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"]
)

# Directory for uploaded resumes
UPLOAD_DIR = "uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==============================
# Upload Resume
# ==============================
@router.post("/")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Generate unique filename to avoid conflicts
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text from PDF
    extracted_text = extract_text_from_pdf(file_path)

    if not extracted_text or extracted_text.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF. Make sure the PDF contains selectable text."
        )

    # Save to database
    new_resume = Resume(
        user_id=current_user.id,
        filename=unique_filename,
        file_path=file_path,
        extracted_text=extracted_text,
        analysis_result=None
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    return {
        "message": "Resume uploaded and text extracted successfully",
        "resume_id": new_resume.id
    }


# ==============================
# Analyze Resume
# ==============================
@router.post("/{resume_id}/analyze")
def analyze_resume(
    resume_id: int = Path(..., description="Resume ID"),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Secure query (ownership check inside filter)
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id,
        models.Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found or not authorized"
        )

    if not resume.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No extracted text available for analysis"
        )

    # Simple analysis logic
    text = resume.extracted_text

    analysis_result = {
        "word_count": len(text.split()),
        "char_count": len(text),
        "email_found": "@" in text,
        "has_numbers": any(char.isdigit() for char in text),
        "summary": "Basic resume analysis completed."
    }

    resume.analysis_result = analysis_result
    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume analyzed successfully",
        "analysis": analysis_result
    }