from app.models import Job,User,Resume
from fastapi import APIRouter,status,HTTPException,Depends
from app.database import get_db
from app.schemas import JobCreate,JobOut
from sqlalchemy.orm import Session
from app.oauth2 import get_current_user
from typing import List
from app.matching.embedding import get_embedding, compute_similarity


router = APIRouter(
    prefix='/jobs',
    tags=['Jobs']
)

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=JobOut)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    
    existing_job = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.title == job.title
    ).first()

    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already posted a job with this title"
        )

    
    new_job = Job(**job.dict(), user_id=current_user.id)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job



def normalize(text: str):
    return text.lower().strip()

def tokenize(text: str):
    return set(normalize(text).split())

def smart_skill_match(resume_skills, job_skills):
    matched = set()

    for job_skill in job_skills:
        job_tokens = tokenize(job_skill)

        for resume_skill in resume_skills:
            resume_tokens = tokenize(resume_skill)

            if (
                job_skill.lower() in resume_skill.lower()
                or resume_skill.lower() in job_skill.lower()
                or job_tokens & resume_tokens
            ):
                matched.add(resume_skill)
                break

    return matched


@router.get("/{job_id}/ai-matches")
def get_ai_matches(job_id: int, db: Session = Depends(get_db)):

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Prepare job text
    job_text = f"""
    {job.title}
    {job.description or ""}
    {job.required_skills or ""}
    """

    job_embedding = get_embedding(job_text)

    # Convert job skills string → list
    if job.required_skills:
        job_skills = [s.strip() for s in job.required_skills.split(",")]
    else:
        job_skills = []

    resumes = db.query(Resume).filter(
        Resume.analysis_result.isnot(None)
    ).all()

    matches = []

    for resume in resumes:

        resume_text = resume.extracted_text
        resume_embedding = get_embedding(resume_text)

        similarity_score = compute_similarity(
            job_embedding,
            resume_embedding
        )

        # 🔥 Extract matched skills
        resume_skills = resume.analysis_result.get("skills", [])
        matched_skills = smart_skill_match(resume_skills, job_skills)

        matches.append({
            "resume_id": resume.id,
            "user_id": resume.user_id,
            "similarity_score": round(similarity_score * 100, 2),
            "skills_matched": list(matched_skills)
        })

    matches.sort(
        key=lambda x: x["similarity_score"],
        reverse=True
    )

    return {
        "job_id": job.id,
        "job_title": job.title,
        "total_resumes_checked": len(resumes),
        "ai_matches": matches[:10]
    }