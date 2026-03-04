from app.models import Job,User
from fastapi import APIRouter,status,HTTPException,Depends
from app.database import get_db
from app.schemas import JobCreate,JobOut
from sqlalchemy.orm import Session
from app.oauth2 import get_current_user

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