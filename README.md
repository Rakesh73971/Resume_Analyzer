
# 🧠 AI Resume Analyzer Backend

An **AI-powered resume analysis and job matching backend** built with **FastAPI**.
This system allows candidates to upload resumes and companies to post jobs. The platform **extracts structured data from resumes using AI (Gemini/OpenAI)** and **matches candidates to jobs based on skills, experience, and education**.

---

# 🚀 Features

### 🔐 Authentication

* JWT-based authentication
* Secure login system
* User authorization for APIs

### 📄 Resume Management

* Upload resumes (PDF)
* Extract text from resumes
* Store extracted text in database

### 🤖 AI Resume Analysis

Uses **LLM (Gemini/OpenAI)** to extract structured data:

* Skills
* Work experience
* Education

Example AI Output:

```json
{
  "skills": ["Python", "FastAPI", "Docker"],
  "experience": [
    {
      "company": "ResoluteAI Software",
      "role": "Backend Developer",
      "years": "Dec 2025 - Present"
    }
  ],
  "education": [
    {
      "degree": "B.Tech",
      "field": "CSE",
      "year": "2022 - 2026"
    }
  ]
}
```

---

# 🧑‍💼 Job Posting

Companies can:

* Create job posts
* Define required skills
* Specify experience requirements
* Define education requirements

Example Job:

```json
{
  "title": "Python Developer",
  "required_skills": ["Python", "FastAPI", "Docker"],
  "min_experience_years": 1,
  "required_degree": "B.Tech",
  "required_field": "CSE"
}
```

---

# 🎯 Resume Matching System

The system matches resumes with jobs and calculates a **match score**.

### Matching Criteria

| Criteria   | Weight |
| ---------- | ------ |
| Skills     | 70%    |
| Experience | 20%    |
| Education  | 10%    |

Example Result:

```json
{
  "job_id": 2,
  "job_title": "Python Developer",
  "matches": [
    {
      "resume_id": 1,
      "user_id": 1,
      "score": 65.0,
      "skills_matched": [
        "python",
        "fastapi",
        "docker",
        "git"
      ]
    }
  ]
}
```

This allows companies to **rank candidates automatically**.

---

# 🛠 Tech Stack

### Backend

* **Python**
* **FastAPI**

### Database

* **PostgreSQL**
* **SQLAlchemy ORM**
* **Alembic (Migrations)**

### Authentication

* **JWT Authentication**
* **OAuth2 Password Flow**

### AI Integration

* **Google Gemini API** (Resume Analysis)
* Optional: **OpenAI**

### File Handling

* PDF resume uploads
* Text extraction using Python libraries


# ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/resume-analyzer.git
cd resume-analyzer
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Setup Environment Variables

Create `.env`

```
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_NAME=resume_analyzer
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=password

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

GEMINI_API_KEY=your_gemini_api_key
```

---

### 5️⃣ Run Migrations

```bash
alembic upgrade head
```

---

### 6️⃣ Start Server

```bash
uvicorn app.main:app --reload
```

API Docs:

```
http://127.0.0.1:8000/docs
```

---

# 📡 API Endpoints

## Authentication

```
POST /login
```

Login user and return JWT token.

---

## Resume APIs

Upload resume

```
POST /resumes/upload
```

Analyze resume using AI

```
POST /resumes/{resume_id}/analyze
```

---

## Job APIs

Create job

```
POST /jobs/
```

Get job matches

```
GET /jobs/{job_id}/matches
```

Returns ranked candidate resumes.

---

# 🧠 AI Workflow

```
Resume Upload
      │
      ▼
Extract Text from PDF
      │
      ▼
Send text to Gemini/OpenAI
      │
      ▼
Extract structured data
(skills, experience, education)
      │
      ▼
Store in database
      │
      ▼
Match resumes with job requirements
```

---

# 📊 Future Improvements

* Semantic skill matching using **embeddings**
* Vector database (**Pinecone / FAISS**)
* Resume ranking using **AI scoring**
* Job recommendation for candidates
* Admin dashboard
* Frontend (React / Next.js)

---

# 👨‍💻 Author

**Rakesh N**

Backend Developer (Python / FastAPI)

Skills:

* Python
* FastAPI
* Django
* PostgreSQL
* Docker
* AI integrations
