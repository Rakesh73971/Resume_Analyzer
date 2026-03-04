from .database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)

    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)

    role = Column(String, server_default="user")

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    resumes = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete"
    )
    jobs = relationship("Job", back_populates="company", cascade="all, delete")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    extracted_text = Column(Text, nullable=False)

    analysis_result = Column(JSON)  
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()")
    )
    user = relationship("User", back_populates="resumes")



class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, unique=True, nullable=False)
    description = Column(Text)
    required_skills = Column(Text, nullable=True)
    min_experience_years = Column(Integer, nullable=True)
    required_degree = Column(String, nullable=True)  
    required_field = Column(String, nullable=True)
    company_id = Column(Integer, nullable=True)