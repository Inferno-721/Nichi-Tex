"""
Resume Parser Service
Extracts structured information from PDF and DOCX resume files
"""

import re
import sys
from pathlib import Path
from typing import Optional, List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.models.resume import (
    Resume, PersonalInfo, Education, Experience, Project, Skills
)

logger = get_logger(__name__)


class ResumeParser:
    """
    Parser to extract structured information from resume files.
    Supports PDF and DOCX formats.
    """
    
    # Common section headers in resumes
    SECTION_PATTERNS = {
        'education': r'(?i)(education|academic|qualification)',
        'experience': r'(?i)(experience|employment|work\s*history|professional)',
        'skills': r'(?i)(skills|technical\s*skills|competenc|technologies)',
        'projects': r'(?i)(projects|portfolio|work\s*samples)',
        'certifications': r'(?i)(certification|certificate|credential)',
        'summary': r'(?i)(summary|objective|profile|about)'
    }
    
    # Email pattern
    EMAIL_PATTERN = r'[\w\.-]+@[\w\.-]+\.\w+'
    
    # Phone pattern (various formats)
    PHONE_PATTERN = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    
    # LinkedIn pattern
    LINKEDIN_PATTERN = r'linkedin\.com/in/[\w-]+'
    
    # GitHub pattern
    GITHUB_PATTERN = r'github\.com/[\w-]+'
    
    def __init__(self):
        logger.info("Initializing ResumeParser")
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required libraries are available"""
        try:
            import fitz  # PyMuPDF
            logger.debug("PyMuPDF available for PDF parsing")
        except ImportError:
            logger.warning("PyMuPDF not installed. PDF parsing will be limited.")
        
        try:
            import docx
            logger.debug("python-docx available for DOCX parsing")
        except ImportError:
            logger.warning("python-docx not installed. DOCX parsing will be limited.")
    
    def parse(self, file_path: str) -> Resume:
        """
        Parse a resume file and extract structured information.
        
        Args:
            file_path: Path to the resume file (PDF or DOCX)
            
        Returns:
            Resume object with extracted information
        """
        file_path = Path(file_path)
        logger.info(f"Parsing resume: {file_path.name}")
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        # Extract raw text based on file type
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            raw_text = self._extract_pdf_text(file_path)
        elif extension == '.docx':
            raw_text = self._extract_docx_text(file_path)
        else:
            logger.error(f"Unsupported file format: {extension}")
            raise ValueError(f"Unsupported file format: {extension}")
        
        logger.debug(f"Extracted {len(raw_text)} characters from resume")
        
        # Parse the raw text into structured data
        resume = self._parse_text(raw_text)
        resume.raw_text = raw_text
        
        logger.info(f"Successfully parsed resume for: {resume.personal_info.name or 'Unknown'}")
        return resume
    
    def parse_text(self, text: str) -> Resume:
        """
        Parse resume from raw text.
        
        Args:
            text: Raw resume text
            
        Returns:
            Resume object with extracted information
        """
        logger.info("Parsing resume from text input")
        resume = self._parse_text(text)
        resume.raw_text = text
        return resume
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            import fitz  # PyMuPDF
            
            logger.debug(f"Extracting text from PDF: {file_path}")
            doc = fitz.open(file_path)
            text_parts = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                text_parts.append(text)
                logger.debug(f"Extracted {len(text)} chars from page {page_num + 1}")
            
            doc.close()
            return "\n".join(text_parts)
            
        except ImportError:
            logger.error("PyMuPDF not installed. Run: pip install pymupdf")
            raise ImportError("PyMuPDF required for PDF parsing. Install with: pip install pymupdf")
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            from docx import Document
            
            logger.debug(f"Extracting text from DOCX: {file_path}")
            doc = Document(file_path)
            text_parts = []
            
            for para in doc.paragraphs:
                text_parts.append(para.text)
            
            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text_parts.append(cell.text)
            
            return "\n".join(text_parts)
            
        except ImportError:
            logger.error("python-docx not installed. Run: pip install python-docx")
            raise ImportError("python-docx required for DOCX parsing. Install with: pip install python-docx")
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise
    
    def _parse_text(self, text: str) -> Resume:
        """Parse raw text into Resume structure"""
        resume = Resume()
        
        # Extract personal info
        resume.personal_info = self._extract_personal_info(text)
        
        # Split text into sections
        sections = self._split_into_sections(text)
        
        # Extract each section
        if 'education' in sections:
            resume.education = self._extract_education(sections['education'])
        
        if 'experience' in sections:
            resume.experience = self._extract_experience(sections['experience'])
        
        if 'skills' in sections:
            resume.skills = self._extract_skills(sections['skills'])
        
        if 'projects' in sections:
            resume.projects = self._extract_projects(sections['projects'])
        
        if 'certifications' in sections:
            resume.certifications = self._extract_certifications(sections['certifications'])
        
        if 'summary' in sections:
            resume.summary = sections['summary'].strip()
        
        return resume
    
    def _extract_personal_info(self, text: str) -> PersonalInfo:
        """Extract personal information from text"""
        info = PersonalInfo()
        
        # Extract email
        email_match = re.search(self.EMAIL_PATTERN, text)
        if email_match:
            info.email = email_match.group()
            logger.debug(f"Found email: {info.email}")
        
        # Extract phone
        phone_match = re.search(self.PHONE_PATTERN, text)
        if phone_match:
            info.phone = phone_match.group()
            logger.debug(f"Found phone: {info.phone}")
        
        # Extract LinkedIn
        linkedin_match = re.search(self.LINKEDIN_PATTERN, text, re.IGNORECASE)
        if linkedin_match:
            info.linkedin = f"https://{linkedin_match.group()}"
            logger.debug(f"Found LinkedIn: {info.linkedin}")
        
        # Extract GitHub
        github_match = re.search(self.GITHUB_PATTERN, text, re.IGNORECASE)
        if github_match:
            info.github = f"https://{github_match.group()}"
            logger.debug(f"Found GitHub: {info.github}")
        
        # Extract name (usually first line or before email)
        lines = text.strip().split('\n')
        if lines:
            # First non-empty line is often the name
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                if line and not re.search(self.EMAIL_PATTERN, line) and not re.search(self.PHONE_PATTERN, line):
                    # Simple heuristic: name is short and doesn't contain @
                    if len(line) < 50 and '@' not in line and 'http' not in line.lower():
                        info.name = line
                        logger.debug(f"Found name: {info.name}")
                        break
        
        return info
    
    def _split_into_sections(self, text: str) -> dict:
        """Split resume text into sections based on headers"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line is a section header
            found_section = None
            for section_name, pattern in self.SECTION_PATTERNS.items():
                if re.search(pattern, line_lower) and len(line_lower) < 50:
                    found_section = section_name
                    break
            
            if found_section:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = found_section
                current_content = []
                logger.debug(f"Found section: {current_section}")
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_education(self, text: str) -> List[Education]:
        """Extract education entries from education section"""
        education_list = []
        
        # Common degree patterns
        degree_patterns = [
            r'(?i)(B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|Bachelor|Master|Doctor)',
            r'(?i)(Computer Science|Engineering|Business|Data Science|Information Technology)'
        ]
        
        # Split by common separators or patterns
        entries = re.split(r'\n\s*\n', text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            edu = Education()
            
            # Try to extract degree
            for pattern in degree_patterns:
                match = re.search(pattern, entry)
                if match:
                    if not edu.degree:
                        edu.degree = match.group()
                    else:
                        edu.field_of_study = match.group()
            
            # Extract GPA if mentioned
            gpa_match = re.search(r'(?i)GPA[:\s]*(\d+\.?\d*)', entry)
            if gpa_match:
                try:
                    edu.gpa = float(gpa_match.group(1))
                except ValueError:
                    pass
            
            # Extract year/date
            year_match = re.search(r'(20\d{2}|19\d{2})', entry)
            if year_match:
                edu.end_date = year_match.group()
            
            # First line often contains institution name
            lines = entry.strip().split('\n')
            if lines:
                edu.institution = lines[0].strip()
            
            if edu.institution or edu.degree:
                education_list.append(edu)
                logger.debug(f"Found education: {edu.institution} - {edu.degree}")
        
        return education_list
    
    def _extract_experience(self, text: str) -> List[Experience]:
        """Extract work experience entries"""
        experience_list = []
        
        # Split by double newlines or patterns indicating new entries
        entries = re.split(r'\n\s*\n', text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            exp = Experience()
            lines = entry.strip().split('\n')
            
            if lines:
                # First line often contains job title or company
                first_line = lines[0].strip()
                exp.title = first_line
                
                # Look for company name
                if len(lines) > 1:
                    exp.company = lines[1].strip()
            
            # Extract dates
            date_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\w]*\s*\d{4})', entry, re.IGNORECASE)
            if date_match:
                exp.start_date = date_match.group()
            
            # Check for "Present" or "Current"
            if re.search(r'(?i)(present|current|now)', entry):
                exp.is_current = True
            
            # Extract bullet points as responsibilities
            bullets = re.findall(r'[•\-\*]\s*(.+)', entry)
            exp.responsibilities = bullets
            
            if exp.title or exp.company:
                experience_list.append(exp)
                logger.debug(f"Found experience: {exp.title} at {exp.company}")
        
        return experience_list
    
    def _extract_skills(self, text: str) -> Skills:
        """Extract skills from skills section"""
        skills = Skills()
        
        # Common technical skill keywords
        tech_keywords = [
            'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'r', 'scala',
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'data analysis', 'data visualization', 'tableau', 'power bi',
            'git', 'linux', 'agile', 'scrum', 'jira'
        ]
        
        # Soft skill keywords
        soft_keywords = [
            'leadership', 'communication', 'teamwork', 'problem-solving',
            'analytical', 'critical thinking', 'time management', 'adaptability'
        ]
        
        text_lower = text.lower()
        
        # Extract skills by matching keywords
        for skill in tech_keywords:
            if skill in text_lower:
                skills.technical.append(skill.title())
        
        for skill in soft_keywords:
            if skill in text_lower:
                skills.soft.append(skill.title())
        
        # Also extract comma or bullet separated items
        items = re.split(r'[,•\n]', text)
        for item in items:
            item = item.strip()
            if item and len(item) < 30 and item.lower() not in [s.lower() for s in skills.technical + skills.soft]:
                # Add as technical skill by default
                if len(item) > 2:
                    skills.technical.append(item)
        
        logger.debug(f"Found {len(skills.technical)} technical skills, {len(skills.soft)} soft skills")
        return skills
    
    def _extract_projects(self, text: str) -> List[Project]:
        """Extract projects from projects section"""
        projects = []
        
        # Split by double newlines
        entries = re.split(r'\n\s*\n', text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            proj = Project()
            lines = entry.strip().split('\n')
            
            if lines:
                proj.name = lines[0].strip()
                
                # Remaining lines as description
                if len(lines) > 1:
                    proj.description = '\n'.join(lines[1:]).strip()
            
            # Extract bullet points as highlights
            bullets = re.findall(r'[•\-\*]\s*(.+)', entry)
            proj.highlights = bullets
            
            # Extract technologies mentioned
            tech_match = re.search(r'(?i)(?:technologies?|tech\s*stack|built with)[:\s]*(.+)', entry)
            if tech_match:
                techs = re.split(r'[,;]', tech_match.group(1))
                proj.technologies = [t.strip() for t in techs if t.strip()]
            
            if proj.name:
                projects.append(proj)
                logger.debug(f"Found project: {proj.name}")
        
        return projects
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from certifications section"""
        certifications = []
        
        # Split by newlines
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove bullet points
            line = re.sub(r'^[•\-\*]\s*', '', line)
            if line and len(line) > 3:
                certifications.append(line)
        
        logger.debug(f"Found {len(certifications)} certifications")
        return certifications
