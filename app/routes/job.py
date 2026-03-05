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

            # Flexible match:
            # partial OR token overlap
            if (
                job_skill.lower() in resume_skill.lower()
                or resume_skill.lower() in job_skill.lower()
                or job_tokens & resume_tokens  # word overlap
            ):
                matched.add(resume_skill)
                break

    return matched

def calculate_match_score(resume_analysis: dict, job_skills: list, job_title: str):
    score = 0
    skills_weight = 70
    experience_weight = 20
    education_weight = 10

    # Resume skills
    resume_skills = resume_analysis.get("skills", [])

    # Use smart matching instead of set intersection
    matched_skills = smart_skill_match(resume_skills, job_skills)

    # Skill Score
    skills_score = (
        (len(matched_skills) / len(job_skills) * skills_weight)
        if job_skills else 0
    )

    score += skills_score

    # ---------- Experience Matching ----------
    exp_score = 0
    for exp in resume_analysis.get("experience", []):
        role = (exp.get("role") or "").lower()

        if job_title.lower() in role or role in job_title.lower():
            exp_score += 10

    score += min(exp_score, experience_weight)

    # ---------- Education Matching ----------
    edu_score = 0
    for edu in resume_analysis.get("education", []):
        field = (edu.get("field") or "").lower()

        if "computer" in field or "cse" in field:
            edu_score += 5

    score += min(edu_score, education_weight)

    return round(score, 2), list(matched_skills)

@router.get("/{job_id}/matches")
def get_top_resumes(job_id: int, db: Session = Depends(get_db)):

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resumes = db.query(Resume).filter(
        Resume.analysis_result.isnot(None)
    ).all()

    matches = []

    # Convert required_skills string → list
    if job.required_skills:
        job_skills = [
            skill.strip()
            for skill in job.required_skills.split(",")
        ]
    else:
        job_skills = []

    for resume in resumes:
        score, skills_matched = calculate_match_score(
            resume.analysis_result,
            job_skills,
            job.title
        )

        if score > 0:
            matches.append({
                "resume_id": resume.id,
                "user_id": resume.user_id,
                "score": score,
                "skills_matched": skills_matched
            })

    matches.sort(key=lambda x: x["score"], reverse=True)

    return {
        "job_id": job.id,
        "job_title": job.title,
        "total_resumes_checked": len(resumes),
        "total_matches_found": len(matches),
        "matches": matches[:10]
    }