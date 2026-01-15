"""
Clod_v2 - Main Entry Point
Single entry point for running the API server
"""

import uvicorn
from app.api import app


def main():
    """Run the Clod_v2 API server"""
    print("=" * 50)
    print("🚀 Starting Clod_v2 API Server")
    print("=" * 50)
    print()
    print("API Documentation:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc:      http://localhost:8000/redoc")
    print()
    print("Endpoints:")
    print("  POST /parse/resume      - Parse resume text")
    print("  POST /parse/resume/file - Parse resume file (PDF/DOCX)")
    print("  POST /parse/jd          - Parse job description")
    print("  POST /analyze           - Analyze resume vs JD")
    print("  POST /generate/latex    - Generate LaTeX code")
    print("  POST /process           - Full pipeline")
    print()
    print("=" * 50)
    
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()
