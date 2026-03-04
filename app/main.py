from fastapi import FastAPI
from . import models
from .database import engine
from .routes import user,resume,auth,job
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
app.include_router(auth.router)
app.include_router(job.router)


@app.get("/")
def root():
    return {"message": "Hello World"}