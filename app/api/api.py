"""
Clod_v2 API
FastAPI backend for resume analysis and LaTeX generation
"""

import asyncio
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.main import Clod
from app.services.ai_client import get_ai_client
from config.settings import MAX_FILE_SIZE_MB, SUPPORTED_RESUME_FORMATS

logger = get_logger(__name__)

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Shared system instance, created on startup.
clod: Optional[Clod] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the Clod system once, when the server starts."""
    global clod
    logger.info("Starting Clod_v2 API...")
    try:
        clod = Clod()
        logger.info("Clod_v2 API ready!")
    except Exception as e:
        # Don't crash the whole server; endpoints will report 503 instead.
        logger.error(f"Failed to initialise Clod system: {e}")
        clod = None
    yield
    logger.info("Shutting down Clod_v2 API")


# Initialize FastAPI app
app = FastAPI(
    title="Clod_v2 API",
    description="Resume Analysis & LaTeX Generator API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_clod() -> Clod:
    """Return the initialised Clod instance or raise 503 if unavailable."""
    if clod is None:
        raise HTTPException(
            status_code=503,
            detail="Service is initialising or failed to start. Try again shortly.",
        )
    return clod


# ========================
# Request/Response Models
# ========================

class AnalyzeRequest(BaseModel):
    """Request model for analysis"""
    resume_text: str = Field(..., description="Resume text")
    jd_text: str = Field(..., description="Job description text")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
    ai_enabled: bool = False
    ai_status: dict = Field(default_factory=dict)


# ========================
# API Endpoints
# ========================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint. Reports whether the AI layer is configured."""
    ai = get_ai_client()
    return HealthResponse(
        status="healthy" if clod is not None else "initializing",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        ai_enabled=ai.available,
        ai_status=ai.status(),
    )


@app.post("/parse/resume")
async def parse_resume(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Parse resume from text OR file upload.
    
    - Send `text` form field for text input
    - Send `file` for PDF/DOCX upload
    """
    service = get_clod()
    try:
        if not text and not file:
            raise HTTPException(status_code=400, detail="Either 'text' or 'file' must be provided")

        if file:
            logger.info(f"Parsing resume from file: {file.filename}")

            # Validate extension against the allowed list.
            suffix = Path(file.filename or "").suffix.lower()
            if suffix not in SUPPORTED_RESUME_FORMATS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type '{suffix}'. "
                           f"Allowed: {', '.join(SUPPORTED_RESUME_FORMATS)}",
                )

            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            if len(content) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Max size is {MAX_FILE_SIZE_MB} MB.",
                )

            # Write to a sanitized, unique temp path (avoids path traversal).
            temp_dir = PROJECT_ROOT / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / f"{uuid.uuid4().hex}{suffix}"
            try:
                with open(temp_path, "wb") as f:
                    f.write(content)
                resume = service.parse_resume(file_path=str(temp_path))
            finally:
                temp_path.unlink(missing_ok=True)  # Always clean up
        else:
            logger.info("Parsing resume from text")
            resume = service.parse_resume(text=text)

        return {
            "success": True,
            "data": {
                "personal_info": {
                    "name": resume.personal_info.name,
                    "email": resume.personal_info.email,
                    "phone": resume.personal_info.phone,
                    "linkedin": resume.personal_info.linkedin,
                    "github": resume.personal_info.github
                },
                "education": [
                    {
                        "institution": edu.institution,
                        "degree": edu.degree,
                        "gpa": edu.gpa
                    }
                    for edu in resume.education
                ],
                "experience": [
                    {
                        "title": exp.title,
                        "company": exp.company,
                        "responsibilities": exp.responsibilities
                    }
                    for exp in resume.experience
                ],
                "skills": resume.skills.all_skills(),
                "projects": [proj.name for proj in resume.projects],
                "certifications": resume.certifications
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/parse/jd")
async def parse_job_description(text: str = Form(...)):
    """
    Parse job description text.
    """
    service = get_clod()
    try:
        logger.info("Parsing job description")
        jd = service.parse_job_description(text)
        
        return {
            "success": True,
            "data": {
                "title": jd.title,
                "company": jd.company,
                "required_skills": jd.required_skills,
                "preferred_skills": jd.preferred_skills,
                "required_experience_years": jd.required_experience_years,
                "keywords": jd.keywords[:20]
            }
        }
    except Exception as e:
        logger.error(f"Error parsing JD: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze")
async def analyze_match(request: AnalyzeRequest):
    """
    Analyze match between resume and job description.
    Returns scores, recommendations, and AI-powered enhanced feedback.
    """
    service = get_clod()
    try:
        logger.info("Analyzing resume-JD match")

        if not request.resume_text.strip() or not request.jd_text.strip():
            raise HTTPException(status_code=400, detail="resume_text and jd_text are required")

        # Parse resume and JD concurrently (independent AI calls).
        resume, jd = await asyncio.gather(
            asyncio.to_thread(service.parse_resume, text=request.resume_text),
            asyncio.to_thread(service.parse_job_description, request.jd_text),
        )
        analysis = service.analyze(resume, jd)

        # Get AI-powered enhanced feedback using prompts
        logger.info("Generating AI-powered enhanced feedback")
        target_role = jd.title if jd.title else "the target role"
        enhanced_feedback = service.prompt_analyzer.analyze_with_prompts(
            resume_text=request.resume_text,
            jd_text=request.jd_text,
            target_role=target_role,
            analysis=analysis
        )
        
        return {
            "success": True,
            "scores": {
                "overall": round(analysis.overall_score, 2),
                "skills": round(analysis.skill_match_score, 2),
                "experience": round(analysis.experience_match_score, 2),
                "education": round(analysis.education_match_score, 2)
            },
            "matched_skills": analysis.matched_skills,
            "missing_skills": analysis.missing_skills,
            "recommendations": [
                {
                    "priority": rec.priority,
                    "title": rec.title,
                    "description": rec.description
                }
                for rec in analysis.recommendations[:5]
            ],
            "summary": analysis.summary,
            # AI-powered enhanced feedback
            "enhanced_feedback": enhanced_feedback.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing match: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/generate")
async def generate_latex(
    resume_text: str = Form(...),
    jd_text: str = Form(...),
    output_format: str = Form("text")  # "text" or "file"
):
    """
    Generate optimized LaTeX resume.
    
    - `output_format`: "text" returns JSON with latex_code, "file" returns downloadable .tex file
    """
    service = get_clod()
    try:
        logger.info(f"Generating LaTeX resume (format: {output_format})")

        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="resume_text is required")

        # Debug: Log input length
        logger.debug(f"Resume text length: {len(resume_text)} chars")

        if jd_text.strip():
            # Parse resume and JD concurrently (independent AI calls).
            resume, jd = await asyncio.gather(
                asyncio.to_thread(service.parse_resume, text=resume_text),
                asyncio.to_thread(service.parse_job_description, jd_text),
            )
            analysis = service.analyze(resume, jd)
        else:
            resume = service.parse_resume(text=resume_text)
            jd = None
            analysis = None
        latex_code = service.generate_latex(resume, jd, analysis)
        
        if output_format == "file":
            from fastapi.responses import Response
            
            return Response(
                content=latex_code,
                media_type="application/x-tex",
                headers={
                    "Content-Disposition": "attachment; filename=resume.tex"
                }
            )
        else:
            return {
                "success": True,
                "latex_code": latex_code,
                "match_score": round(analysis.overall_score, 2) if analysis else None,
                "missing_skills": analysis.missing_skills if analysis else []
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating LaTeX: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Run with: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
