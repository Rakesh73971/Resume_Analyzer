import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Path,status
from sqlalchemy.orm import Session
import openai, json
import time
from app import models, database
from app.models import Resume
from app.oauth2 import get_current_user
from app.services.resume_parser import extract_text_from_pdf
from app.config import settings



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
openai.api_key = settings.openai_key

def call_openai_safe(prompt, model="gpt-3.5-turbo-16k", retries=5):
    """
    Call OpenAI with retries for API errors and rate limits
    """
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            return response['choices'][0]['message']['content']
        except openai.error.RateLimitError as e:
            print(f"Rate limit hit: {e}, backing off...")
            time.sleep(5 * (attempt + 1))  # exponential backoff
        except openai.error.APIError as e:  # handles 500/503 errors
            print(f"OpenAI API error: {e}, retrying...")
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"Unexpected error: {e}, retrying...")
            time.sleep(2 ** attempt)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="OpenAI server is unavailable, please try again later."
    )


@router.post("/{resume_id}/analyze")
def analyze_resume(
    resume_id: int = Path(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1️⃣ Fetch resume
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not resume.extracted_text:
        raise HTTPException(status_code=400, detail="No text to analyze")

    # 2️⃣ Prepare prompt
    prompt = f"""
    Extract structured information from this resume text in JSON format with keys:
    - skills: list of skills
    - experience: list of jobs with company, role, years
    - education: list of degrees with field and year

    Resume Text:
    {resume.extracted_text}
    Return only valid JSON.
    """

    # 3️⃣ Call OpenAI safely with retries
    result_text = call_openai_safe(prompt)

    # 4️⃣ Convert JSON string to dict
    try:
        analysis_result = json.loads(result_text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, 
            detail="Failed to parse AI response. Response was not valid JSON."
        )

    # 5️⃣ Save analysis to DB
    resume.analysis_result = analysis_result
    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume analyzed successfully",
        "analysis": analysis_result
    }