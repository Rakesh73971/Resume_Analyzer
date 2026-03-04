from ..models import User
from fastapi import APIRouter,status,Depends
from ..schemas import UserCreate,UserOut
from ..database import get_db
from sqlalchemy.orm import Session
from .. import utils,models

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    hashed_password = utils.hash(user.password)

    new_user = models.User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone_number
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user