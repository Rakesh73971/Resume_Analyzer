from app.models import Job,User,Resume
from fastapi import APIRouter,status,HTTPException,Depends
from app.database import get_db
from app.schemas import JobCreate,JobOut
from sqlalchemy.orm import Session
from app.oauth2 import get_current_user
from typing import List

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

    # Prevent duplicate job title for the same company
    existing_job = db.query(Job).filter(
        Job.company_id == current_user.id,
        Job.title == job.title
    ).first()

    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already posted a job with this title"
        )

    # Save job
    new_job = Job(**job.dict(), company_id=current_user.id)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


def calculate_match_score(resume_analysis: dict, job_skills: list, job_title: str):
    score = 0
    skills_weight = 70
    experience_weight = 20
    education_weight = 10

    # 1️⃣ Skills match
    resume_skills = [s.lower().strip() for s in resume_analysis.get("skills", [])]
    job_skills_set = set(s.lower().strip() for s in job_skills)
    matched_skills = set(resume_skills) & job_skills_set
    skills_score = (len(matched_skills) / len(job_skills_set) * skills_weight) if job_skills_set else 0
    score += skills_score

    # 2️⃣ Experience match
    exp_score = 0
    for exp in resume_analysis.get("experience", []):
        role = (exp.get("role") or "").lower()
        years = exp.get("years") or 0
        if role in job_title.lower():
            exp_score += min(years, 5) * 4  # max 20 points
    score += min(exp_score, experience_weight)

    # 3️⃣ Education match
    edu_score = 0
    for edu in resume_analysis.get("education", []):
        degree = (edu.get("degree") or "").lower()
        field = (edu.get("field") or "").lower()
        if "cse" in field or "computer" in field:
            edu_score += 5
    score += min(edu_score, education_weight)

    return round(score, 2), list(matched_skills)

@router.get("/{job_id}/matches")
def get_top_resumes(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    
    resumes = db.query(Resume).all()
    matches = []

    job_skills = job.required_skills if job.required_skills else []

    for resume in resumes:
        if resume.analysis_result and "skills" in resume.analysis_result:
            score, skills_matched = calculate_match_score(
                resume.analysis_result, job_skills, job.title
            )
            matches.append({
                "resume_id": resume.id,
                "user_id": resume.user_id,
                "score": score,
                "skills_matched": skills_matched
            })

    matches.sort(key=lambda x: x["score"], reverse=True)


    top_matches = matches[:10]

    return {
        "job_id": job.id,
        "job_title": job.title,
        "matches": top_matches
    }