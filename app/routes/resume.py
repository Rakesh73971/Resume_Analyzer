import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Path
from app import models, database
from app.services.resume_parser import extract_text_from_pdf
from app.oauth2 import get_current_user


router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"]
)

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):


    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

   
    unique_filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    
    file_bytes = file.file.read()

    extracted_text = extract_text_from_pdf(file_bytes)

    if not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from PDF"
        )

    
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    
    new_resume = models.Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        extracted_text=extracted_text
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    return {
        "message": "Resume uploaded successfully",
        "resume_id": new_resume.id
    }


@router.post("/{resume_id}/analyze")
def analyze_resume(
    resume_id: int = Path(..., description="Resume ID"),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):


    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )


    if resume.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to analyze this resume"
        )


    if not resume.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No extracted text available"
        )


    analysis_result = {
        "word_count": len(resume.extracted_text.split()),
        "summary": "This is a basic resume analysis"
    }


    resume.analysis_result = analysis_result
    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume analyzed successfully",
        "analysis": analysis_result
    }