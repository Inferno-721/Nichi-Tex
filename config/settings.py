"""
Configuration settings for Clod_v2
All settings loaded from environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"
TEMPLATES_DIR = APP_DIR / "templates"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# NLP Model settings (local)
DEFAULT_MODEL = os.getenv("NLP_MODEL", "all-MiniLM-L6-v2")
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

# Resume parser settings
SUPPORTED_RESUME_FORMATS = [".pdf", ".docx"]
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

# LaTeX settings
LATEX_TEMPLATE_NAME = "resume_template.tex"

# Google Gemini API settings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
