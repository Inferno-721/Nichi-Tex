"""
Data models for Job Description representation
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass 
class JobDescription:
    """Parsed job description structure"""
    title: str = ""
    company: str = ""
    location: str = ""
    job_type: str = ""  # Full-time, Part-time, Contract, etc.
    
    # Requirements
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    required_experience_years: Optional[int] = None
    required_education: str = ""
    
    # Job details
    responsibilities: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    
    # Raw content
    raw_text: str = ""
    
    # Keywords for ATS optimization
    keywords: List[str] = field(default_factory=list)
    
    def get_all_required_skills(self) -> List[str]:
        """Get all required skills"""
        return self.required_skills
    
    def get_all_skills(self) -> List[str]:
        """Get all skills (required + preferred)"""
        return self.required_skills + self.preferred_skills
    
    def get_searchable_text(self) -> str:
        """Get all text for NLP analysis"""
        texts = [
            self.title,
            self.raw_text,
            " ".join(self.required_skills),
            " ".join(self.preferred_skills),
            " ".join(self.responsibilities)
        ]
        return " ".join(filter(None, texts))
