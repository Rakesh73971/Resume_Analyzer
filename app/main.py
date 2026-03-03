from fastapi import FastAPI
from . import models
from .database import engine
from .routes import user,resume
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(resume.router)


@app.get("/")
def root():
    return {"message": "Hello World"}