from jose import jwt,JWTError
from datetime import timedelta,datetime
from fastapi import Depends,status,HTTPException
from sqlalchemy.orm import Session
from .schemas import TokenData
from . import database,models
from fastapi.security import OAuth2PasswordBearer
from .config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp':expire})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token:str,credentials_exception):
    try:
        payload = jwt.encode(token,SECRET_KEY,algorithm=[ALGORITHM])
        user_id:int = payload.get('user_id')
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=id)
        return token_data
    except JWTError:
        raise credentials_exception

        
def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='detail could not validate',
        headers={'WWW-Authenticate':'Bearer'}
    )

    token_data = verify_access_token(token,credentials_exception)

    user = db.query(models.User).filter(
        models.User.id == token_data.id
    ).first()

    if user is None:
        raise credentials_exception

    return user
