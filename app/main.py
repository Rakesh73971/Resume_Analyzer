from fastapi import FastAPI
from . import models
from .database import engine
from .routes import user,resume,auth,job
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    _has_prom = True
except Exception:
    _has_prom = False


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


@app.get("/metrics")
def metrics():
    if not _has_prom:
        return Response(content=b"prometheus_client not installed", media_type="text/plain", status_code=501)
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)