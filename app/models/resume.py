"""
Data models for Resume representation
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class PersonalInfo:
    """Personal information section of resume"""
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    location: str = ""
    portfolio: str = ""


@dataclass
class Education:
    """Education entry"""
    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = None
    achievements: List[str] = field(default_factory=list)


@dataclass
class Experience:
    """Work experience entry"""
    company: str = ""
    title: str = ""
    location: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    responsibilities: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)


@dataclass
class Project:
    """Project entry"""
    name: str = ""
    description: str = ""
    technologies: List[str] = field(default_factory=list)
    url: str = ""
    highlights: List[str] = field(default_factory=list)


@dataclass
class Skills:
    """Skills categorized by type"""
    technical: List[str] = field(default_factory=list)
    soft: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    
    def all_skills(self) -> List[str]:
        """Get all skills as a flat list"""
        return (
            self.technical + 
            self.soft + 
            self.tools + 
            self.languages + 
            self.frameworks
        )


@dataclass
class Resume:
    """Complete resume data structure"""
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    education: List[Education] = field(default_factory=list)
    experience: List[Experience] = field(default_factory=list)
    skills: Skills = field(default_factory=Skills)
    projects: List[Project] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    summary: str = ""
    raw_text: str = ""  # Original text for NLP processing
    
    def get_all_text(self) -> str:
        """Concatenate all text for NLP analysis"""
        texts = [self.summary, self.raw_text]
        
        for exp in self.experience:
            texts.extend(exp.responsibilities)
            texts.append(exp.title)
            
        for proj in self.projects:
            texts.append(proj.description)
            texts.extend(proj.highlights)
            
        texts.extend(self.skills.all_skills())
        
        return " ".join(filter(None, texts))
