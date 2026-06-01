"""
Job Description Parser Service
Extracts structured requirements from job descriptions
"""

import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.services.ai_client import get_ai_client
from app.models.job_description import JobDescription

logger = get_logger(__name__)


class _JDSchema(BaseModel):
    """Schema for LLM structured extraction of a job description."""
    title: str = ""
    company: str = ""
    location: str = ""
    job_type: str = ""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    required_experience_years: Optional[int] = None
    required_education: str = ""
    responsibilities: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class JDParser:
    """
    Parser to extract structured requirements from job descriptions.
    """
    
    # Section patterns for JD
    SECTION_PATTERNS = {
        'requirements': r'(?i)(requirements?|qualifications?|what we.re looking for)',
        'responsibilities': r'(?i)(responsibilities|duties|what you.ll do|role)',
        'preferred': r'(?i)(preferred|nice to have|bonus|plus)',
        'benefits': r'(?i)(benefits?|perks|what we offer)',
        'about': r'(?i)(about|company|who we are)'
    }
    
    # Common skill patterns
    SKILL_PATTERNS = {
        'programming': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'ruby', 'php', 'scala', 'kotlin', 'swift', 'r', 'matlab', 'sql'
        ],
        'frameworks': [
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring',
            'express', 'fastapi', 'tensorflow', 'pytorch', 'keras', '.net'
        ],
        'data': [
            'pandas', 'numpy', 'scikit-learn', 'spark', 'hadoop', 'kafka',
            'airflow', 'dbt', 'tableau', 'power bi', 'looker', 'excel'
        ],
        'cloud': [
            'aws', 'azure', 'gcp', 'google cloud', 'ec2', 's3', 'lambda',
            'kubernetes', 'docker', 'terraform', 'jenkins', 'ci/cd'
        ],
        'databases': [
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb', 'oracle', 'sql server', 'snowflake'
        ],
        'concepts': [
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'data analysis', 'data science', 'statistics', 'a/b testing',
            'agile', 'scrum', 'rest api', 'microservices', 'etl'
        ]
    }
    
    # Experience level patterns
    EXPERIENCE_PATTERNS = [
        (r'(\d+)\+?\s*(?:years?|yrs?)', lambda m: int(m.group(1))),
        (r'(?i)(entry.level|junior|fresher)', lambda m: 0),
        (r'(?i)(mid.?level|intermediate)', lambda m: 3),
        (r'(?i)(senior|lead|principal)', lambda m: 5),
    ]
    
    # Education patterns
    EDUCATION_PATTERNS = [
        r"(?i)(bachelor'?s?|b\.?s\.?|b\.?a\.?)",
        r"(?i)(master'?s?|m\.?s\.?|m\.?a\.?|mba)",
        r"(?i)(ph\.?d\.?|doctorate)",
        r"(?i)(computer science|data science|engineering|mathematics|statistics)"
    ]
    
    def __init__(self, use_ai: bool = True):
        logger.info("Initializing JDParser")
        self.use_ai = use_ai
        self.ai = get_ai_client() if use_ai else None

    def parse(self, text: str) -> JobDescription:
        """Parse job description text into structured format.

        Tries LLM extraction first, falling back to the offline regex parser.
        """
        if not text or not text.strip():
            raise ValueError("Job description text is empty")

        logger.info("Parsing job description")

        if self.use_ai and self.ai is not None and self.ai.available:
            jd = self._llm_extract(text)
            if jd is not None:
                logger.info(f"Parsed JD via AI: {jd.title} at {jd.company}")
                return jd
            logger.info("AI JD extraction unavailable/failed; using regex fallback")

        return self._regex_parse(text)

    def _llm_extract(self, text: str) -> Optional[JobDescription]:
        prompt = f"""Extract the job description below into the provided JSON schema.
Rules:
- Copy information verbatim; do not invent requirements.
- required_skills: hard skills/technologies explicitly required.
- preferred_skills: "nice to have"/preferred items (must not duplicate required_skills).
- required_experience_years: integer years if stated, else null.
- keywords: important ATS terms (skills, tools, role-specific nouns).
- Leave fields empty if not present.

Job description:
\"\"\"
{text}
\"\"\""""
        parsed = self.ai.generate_json(prompt, schema=_JDSchema)
        if parsed is None:
            return None
        try:
            return JobDescription(
                title=parsed.title, company=parsed.company, location=parsed.location,
                job_type=parsed.job_type,
                required_skills=list(parsed.required_skills),
                preferred_skills=[s for s in parsed.preferred_skills
                                  if s not in parsed.required_skills],
                required_experience_years=parsed.required_experience_years,
                required_education=parsed.required_education,
                responsibilities=list(parsed.responsibilities),
                benefits=list(parsed.benefits),
                keywords=list(parsed.keywords) or list(parsed.required_skills),
                raw_text=text,
            )
        except Exception as e:
            logger.warning(f"Failed to convert AI JD output: {e}")
            return None

    def _regex_parse(self, text: str) -> JobDescription:
        jd = JobDescription()
        jd.raw_text = text
        
        # Extract title and company
        jd.title, jd.company = self._extract_title_company(text)
        
        # Split into sections
        sections = self._split_into_sections(text)
        
        # Extract requirements and skills
        requirements_text = sections.get('requirements', '')
        jd.required_skills = self._extract_skills(requirements_text + ' ' + text)
        
        # Extract preferred skills
        preferred_text = sections.get('preferred', '')
        jd.preferred_skills = self._extract_skills(preferred_text, exclude=jd.required_skills)
        
        # Extract experience requirements
        jd.required_experience_years = self._extract_experience_level(text)
        
        # Extract education requirements
        jd.required_education = self._extract_education_requirement(text)
        
        # Extract responsibilities
        responsibilities_text = sections.get('responsibilities', '')
        jd.responsibilities = self._extract_bullet_points(responsibilities_text)
        
        # Extract benefits
        benefits_text = sections.get('benefits', '')
        jd.benefits = self._extract_bullet_points(benefits_text)
        
        # Extract all keywords for ATS
        jd.keywords = self._extract_keywords(text)
        
        logger.info(f"Parsed JD: {jd.title} at {jd.company}")
        logger.info(f"Found {len(jd.required_skills)} required skills, {len(jd.preferred_skills)} preferred skills")
        
        return jd
    
    def _extract_title_company(self, text: str) -> Tuple[str, str]:
        """Extract job title and company name"""
        title = ""
        company = ""
        
        # Common job title patterns
        title_patterns = [
            r'(?i)(software engineer|data scientist|data analyst|business analyst|'
            r'product manager|frontend|backend|full.?stack|devops|machine learning|'
            r'ml engineer|data engineer|senior|junior|lead|principal)',
        ]
        
        lines = text.strip().split('\n')
        
        # First few lines often contain title
        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
                
            for pattern in title_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    title = line
                    break
            
            if title:
                break
        
        # Company name: only look in the header block (first ~4 lines) to avoid
        # false positives like "...deploy models at scale" deeper in the JD.
        header = "\n".join(lines[:4])
        company_patterns = [
            r'(?i)(?:^|\n)\s*(?:company|organization)[:\s]+(.+?)(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:at|@)\s+([A-Z][\w.& ]+?)(?:\n|$)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, header)
            if match:
                company = match.group(1).strip()
                break

        # Otherwise, the line right after the title often holds "Company | Location".
        if not company and title:
            for i, line in enumerate(lines[:4]):
                if line.strip() == title and i + 1 < len(lines):
                    candidate = re.split(r'\s*[|,]\s*', lines[i + 1].strip())[0].strip()
                    if candidate and len(candidate) < 60:
                        company = candidate
                    break

        # If no title found, use first non-empty line
        if not title and lines:
            title = lines[0].strip()
        
        logger.debug(f"Extracted title: {title}, company: {company}")
        return title, company
    
    def _split_into_sections(self, text: str) -> dict:
        """Split JD text into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Check if this line is a section header
            found_section = None
            for section_name, pattern in self.SECTION_PATTERNS.items():
                if re.search(pattern, line_lower) and len(line_stripped) < 60:
                    found_section = section_name
                    break
            
            if found_section:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = found_section
                current_content = []
                logger.debug(f"Found JD section: {current_section}")
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_skills(self, text: str, exclude: List[str] = None) -> List[str]:
        """Extract skills from text"""
        if exclude is None:
            exclude = []
        
        exclude_lower = [s.lower() for s in exclude]
        found_skills = []
        text_lower = text.lower()
        
        # Check for known skill patterns
        for category, skills in self.SKILL_PATTERNS.items():
            for skill in skills:
                if skill.lower() in text_lower and skill.lower() not in exclude_lower:
                    if skill not in found_skills:
                        found_skills.append(skill)
        
        logger.debug(f"Extracted {len(found_skills)} skills")
        return found_skills
    
    def _extract_experience_level(self, text: str) -> Optional[int]:
        """Extract required years of experience"""
        for pattern, extractor in self.EXPERIENCE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                years = extractor(match)
                logger.debug(f"Found experience requirement: {years} years")
                return years
        
        return None
    
    def _extract_education_requirement(self, text: str) -> str:
        """Extract education requirements"""
        educations = []
        
        for pattern in self.EDUCATION_PATTERNS:
            matches = re.findall(pattern, text)
            educations.extend(matches)
        
        if educations:
            result = ', '.join(set(educations))
            logger.debug(f"Found education requirement: {result}")
            return result
        
        return ""
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points or list items from text"""
        items = []
        
        # Match various bullet point formats
        bullet_pattern = r'[•\-\*◦▪]\s*(.+)'
        matches = re.findall(bullet_pattern, text)
        items.extend(matches)
        
        # Also get numbered items
        numbered_pattern = r'\d+[\.\)]\s*(.+)'
        matches = re.findall(numbered_pattern, text)
        items.extend(matches)
        
        # Clean up items
        items = [item.strip() for item in items if item.strip() and len(item) > 10]
        
        return items
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract all important keywords for ATS optimization"""
        keywords = set()
        text_lower = text.lower()
        
        # Add all found skills
        for category, skills in self.SKILL_PATTERNS.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    keywords.add(skill)
        
        # Add common action verbs that should be in resume
        action_verbs = [
            'developed', 'designed', 'implemented', 'managed', 'led',
            'created', 'built', 'analyzed', 'improved', 'optimized',
            'collaborated', 'delivered', 'achieved', 'launched'
        ]
        
        for verb in action_verbs:
            if verb in text_lower:
                keywords.add(verb)
        
        # Extract capitalized words (often important terms)
        cap_words = re.findall(r'\b[A-Z][A-Za-z]+\b', text)
        for word in cap_words:
            if len(word) > 2:
                keywords.add(word)
        
        logger.debug(f"Extracted {len(keywords)} keywords for ATS")
        return list(keywords)
