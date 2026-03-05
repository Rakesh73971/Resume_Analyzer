import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Path,status
from sqlalchemy.orm import Session
import json
import time
from app import models, database
from app.models import Resume
from app.oauth2 import get_current_user
from app.services.resume_parser import extract_text_from_pdf
from app.config import settings
import google.generativeai as genai
from google.api_core import exceptions
import json
import time




router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"]
)


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
    
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    
    extracted_text = extract_text_from_pdf(file_path)

    if not extracted_text or extracted_text.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF. Make sure the PDF contains selectable text."
        )

    
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


genai.configure(api_key=settings.gemini_key)

def call_gemini_safe(prompt, model_name="gemini-2.5-flash-lite", retries=5):
    """
    Call Gemini with retries for API errors and rate limits.
    Uses 'response_mime_type' to ensure valid JSON output.
    """
    
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={"response_mime_type": "application/json"}
    )

    for attempt in range(retries):
        try:
        
            response = model.generate_content(prompt)
            
           
            return response.text

        except exceptions.ResourceExhausted as e:
            print(f"Rate limit hit: {e}, backing off...")
            time.sleep(5 * (attempt + 1))  # Exponential backoff
        
        except exceptions.InternalServerError as e:
            print(f"Gemini API server error: {e}, retrying...")
            time.sleep(2 ** attempt)
            
        except Exception as e:
            print(f"Unexpected error calling Gemini: {e}")
            time.sleep(2 ** attempt)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Gemini service is currently unavailable."
    )

@router.post("/{resume_id}/analyze")
def analyze_resume(
    resume_id: int = Path(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not resume.extracted_text:
        raise HTTPException(status_code=400, detail="No text to analyze")

    
    prompt = f"""
    Extract structured information from this resume text into a JSON object.
    Required keys:
    - "skills": list of skills
    - "experience": list of objects with "company", "role", "years"
    - "education": list of objects with "degree", "field", "year"

    Resume Text:
    {resume.extracted_text}
    """

   
    result_text = call_gemini_safe(prompt, model_name="gemini-2.5-flash-lite")

    
    try:
        analysis_result = json.loads(result_text)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=500, 
            detail="Failed to parse Gemini response into valid JSON."
        )

    
    resume.analysis_result = analysis_result
    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume analyzed successfully with Gemini",
        "analysis": analysis_result
    }