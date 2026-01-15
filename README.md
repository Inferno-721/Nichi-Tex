# nichi-tex ⚔️

**Intelligent Resume Optimization & LaTeX Generation System**

> *Like a Nichirin blade from Demon Slayer that adapts its color based on the wielder's unique traits, **nichi-tex** forges resumes customized to your individual strengths.*

**nichi** = Inspired by **Nichirin blades** (日輪刀) — weapons that change color based on each user's unique characteristics  
**tex** = **LaTeX** — the gold standard for professional document typesetting

nichi-tex is a data-driven resume matching and LaTeX generation tool that analyzes your resume against job descriptions, identifies skill gaps, and generates optimized LaTeX resumes tailored for specific roles — just as each Nichirin blade is uniquely forged for its wielder.

---

## ✨ Features

- **📄 Resume Parsing** - Extract structured data from PDF and DOCX resumes
- **📋 Job Description Analysis** - Parse JD requirements, skills, and qualifications
- **🎯 NLP-Based Matching** - Semantic similarity analysis between resume and JD using sentence transformers
- **📊 Gap Analysis** - Identify missing skills and generate actionable recommendations
- **📝 LaTeX Generation** - Generate professional, ATS-friendly LaTeX resumes
- **🌐 RESTful API** - FastAPI-powered endpoints for seamless integration

---

## 🏗️ Architecture

```
nichi-tex/
├── app/
│   ├── api/           # FastAPI application
│   ├── models/        # Pydantic data models
│   │   ├── resume.py
│   │   ├── job_description.py
│   │   └── analysis.py
│   ├── services/      # Core business logic
│   │   ├── resume_parser.py
│   │   ├── jd_parser.py
│   │   ├── nlp_matcher.py
│   │   ├── gap_analyzer.py
│   │   └── latex_generator.py
│   └── utils/         # Utilities and helpers
├── config/            # Configuration settings
├── output/            # Generated LaTeX files
├── main.py            # API server entry point
├── demo.py            # Demo script
└── requirements.txt
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nichi-tex
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file with the following:
   ```env
   # Logging
   LOG_LEVEL=DEBUG
   
   # NLP Settings
   NLP_MODEL=all-MiniLM-L6-v2
   SIMILARITY_THRESHOLD=0.7
   
   # File Upload
   MAX_FILE_SIZE_MB=10
   
   # Optional: Google Gemini API
   GOOGLE_API_KEY=your-api-key
   GEMINI_MODEL=gemini-1.5-flash
   ```

---

## 📖 Usage

### Option 1: API Server

Start the FastAPI server:

```bash
python main.py
```

The server will start at `http://localhost:8000`

#### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/parse/resume` | Parse resume from text |
| `POST` | `/parse/resume/file` | Parse resume from file (PDF/DOCX) |
| `POST` | `/parse/jd` | Parse job description |
| `POST` | `/analyze` | Analyze resume vs job description |
| `POST` | `/generate/latex` | Generate LaTeX resume |
| `POST` | `/process` | Full end-to-end pipeline |

### Option 2: Python SDK

```python
from app.main import Clod

# Initialize
clod = Clod()

# Parse resume from file
resume = clod.parse_resume(file_path="path/to/resume.pdf")

# Or from text
resume = clod.parse_resume(text=resume_text)

# Parse job description
jd = clod.parse_job_description(jd_text)

# Analyze match
analysis = clod.analyze(resume, jd)

# Get summary
print(clod.get_summary(analysis))

# Generate LaTeX
latex_code = clod.generate_latex(resume, jd, analysis, output_path="output/resume.tex")
```

### Option 3: Demo Script

Run the demo with sample data:

```bash
python demo.py
```

---

## 📊 Analysis Output

The analysis provides:

- **Overall Match Score** - Weighted composite score
- **Skills Match** - Percentage of required skills matched
- **Experience Match** - Years and role alignment score
- **Education Match** - Degree and field alignment
- **Matched Skills** - Skills found in your resume
- **Missing Skills** - Skills to develop or highlight
- **Recommendations** - Prioritized improvement suggestions

---

## 🔧 Configuration

Configure via environment variables or `config/settings.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |
| `NLP_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity for skill matching |
| `MAX_FILE_SIZE_MB` | `10` | Maximum upload file size |
| `GOOGLE_API_KEY` | - | Google Gemini API key (optional) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model version |

---

## 📦 Dependencies

- **FastAPI** - Modern web framework for APIs
- **Uvicorn** - ASGI server
- **PyMuPDF** - PDF parsing
- **python-docx** - DOCX parsing
- **Sentence Transformers** - NLP embeddings
- **PyTorch** - ML backend
- **Pydantic** - Data validation
- **python-dotenv** - Environment management

---

## 📝 Supported Resume Formats

- PDF (`.pdf`)
- Microsoft Word (`.docx`)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- Sentence Transformers for semantic similarity
- FastAPI for the excellent web framework
- The open-source community

---

<p align="center">
  Made with ❤️ for job seekers everywhere
</p>
