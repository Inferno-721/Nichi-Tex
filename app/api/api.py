"""
Clod_v2 API
FastAPI backend for resume analysis and LaTeX generation
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.main import Clod

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Clod_v2 API",
    description="Resume Analysis & LaTeX Generator API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Clod system
clod = None


@app.on_event("startup")
async def startup_event():
    global clod
    logger.info("Starting Clod_v2 API...")
    clod = Clod()
    logger.info("Clod_v2 API ready!")


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


# ========================
# API Endpoints
# ========================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
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
    try:
        if not text and not file:
            raise HTTPException(status_code=400, detail="Either 'text' or 'file' must be provided")
        
        if file:
            logger.info(f"Parsing resume from file: {file.filename}")
            
            # Save uploaded file temporarily
            temp_dir = PROJECT_ROOT / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / file.filename
            
            with open(temp_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            resume = clod.parse_resume(file_path=str(temp_path))
            temp_path.unlink()  # Clean up
        else:
            logger.info("Parsing resume from text")
            resume = clod.parse_resume(text=text)
        
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
    try:
        logger.info("Parsing job description")
        jd = clod.parse_job_description(text)
        
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
    Returns scores and recommendations.
    """
    try:
        logger.info("Analyzing resume-JD match")
        
        resume = clod.parse_resume(text=request.resume_text)
        jd = clod.parse_job_description(request.jd_text)
        analysis = clod.analyze(resume, jd)
        
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
            "summary": analysis.summary
        }
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
    try:
        logger.info(f"Generating LaTeX resume (format: {output_format})")
        
        resume = clod.parse_resume(text=resume_text)
        jd = clod.parse_job_description(jd_text)
        analysis = clod.analyze(resume, jd)
        latex_code = clod.generate_latex(resume, jd, analysis)
        
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
                "match_score": round(analysis.overall_score, 2),
                "missing_skills": analysis.missing_skills
            }
    except Exception as e:
        logger.error(f"Error generating LaTeX: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Run with: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
