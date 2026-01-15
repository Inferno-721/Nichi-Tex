"""
Data models for Match Analysis results
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class SkillMatch:
    """Individual skill matching result"""
    skill: str
    matched: bool
    similarity_score: float
    matched_with: Optional[str] = None  # The resume skill it matched with


@dataclass
class SectionScore:
    """Score for a specific resume section"""
    section_name: str
    score: float  # 0.0 to 1.0
    max_score: float = 1.0
    details: str = ""


@dataclass
class Recommendation:
    """Improvement recommendation"""
    category: str  # 'skill', 'experience', 'education', 'certification'
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    resources: List[str] = field(default_factory=list)


@dataclass
class MatchAnalysis:
    """Complete analysis result"""
    # Overall scores
    overall_score: float = 0.0  # 0 to 100
    
    # Section-wise scores
    skill_match_score: float = 0.0
    experience_match_score: float = 0.0
    education_match_score: float = 0.0
    
    # Detailed skill matching
    skill_matches: List[SkillMatch] = field(default_factory=list)
    
    # Section scores
    section_scores: List[SectionScore] = field(default_factory=list)
    
    # Gap analysis
    missing_skills: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[Recommendation] = field(default_factory=list)
    
    # Matched and unmatched
    matched_skills: List[str] = field(default_factory=list)
    
    # Summary
    summary: str = ""
    
    def get_score_percentage(self) -> str:
        """Get overall score as percentage string"""
        return f"{self.overall_score:.1f}%"
    
    def get_skill_gap_count(self) -> int:
        """Get number of missing skills"""
        return len(self.missing_skills)
    
    def get_match_summary(self) -> Dict[str, float]:
        """Get summary of all scores"""
        return {
            "overall": self.overall_score,
            "skills": self.skill_match_score,
            "experience": self.experience_match_score,
            "education": self.education_match_score
        }
