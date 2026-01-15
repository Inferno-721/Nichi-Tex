"""
Gap Analyzer Service
Identifies skill gaps and provides learning recommendations
"""

import sys
from pathlib import Path
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.models.analysis import MatchAnalysis, Recommendation

logger = get_logger(__name__)


class GapAnalyzer:
    """
    Analyzes gaps between resume and job requirements.
    Provides prioritized recommendations for improvement.
    """
    
    # Learning resources by skill category
    LEARNING_RESOURCES = {
        'python': [
            'Python.org Official Tutorial',
            'Coursera: Python for Everybody',
            'Real Python tutorials'
        ],
        'sql': [
            'SQLZoo Interactive Tutorial',
            'LeetCode SQL Problems',
            'Mode Analytics SQL Tutorial'
        ],
        'machine learning': [
            'Coursera: Andrew Ng ML Course',
            'fast.ai Practical Deep Learning',
            'Kaggle Learn ML Courses'
        ],
        'data analysis': [
            'Kaggle Learn Data Visualization',
            'DataCamp Data Analyst Track',
            'Google Data Analytics Certificate'
        ],
        'aws': [
            'AWS Skill Builder',
            'AWS Certified Cloud Practitioner',
            'A Cloud Guru AWS Courses'
        ],
        'docker': [
            'Docker Official Documentation',
            'Docker Getting Started Guide',
            'Play with Docker Labs'
        ],
        'react': [
            'React Official Tutorial',
            'freeCodeCamp React Course',
            'Scrimba React Bootcamp'
        ],
        'tableau': [
            'Tableau eLearning',
            'Tableau Public Gallery',
            'Coursera: Data Visualization with Tableau'
        ],
        'default': [
            'LinkedIn Learning',
            'Coursera',
            'Udemy'
        ]
    }
    
    def __init__(self):
        logger.info("Initializing GapAnalyzer")
    
    def analyze(self, match_analysis: MatchAnalysis) -> List[Recommendation]:
        """
        Generate recommendations based on match analysis.
        
        Args:
            match_analysis: The MatchAnalysis from NLPMatcher
            
        Returns:
            List of prioritized recommendations
        """
        logger.info("Generating improvement recommendations")
        
        recommendations = []
        
        # 1. Skill gap recommendations
        skill_recs = self._generate_skill_recommendations(match_analysis)
        recommendations.extend(skill_recs)
        
        # 2. Keyword recommendations
        keyword_recs = self._generate_keyword_recommendations(match_analysis)
        recommendations.extend(keyword_recs)
        
        # 3. Experience recommendations
        if match_analysis.experience_match_score < 70:
            exp_rec = self._generate_experience_recommendation(match_analysis)
            if exp_rec:
                recommendations.append(exp_rec)
        
        # 4. Education recommendations
        if match_analysis.education_match_score < 70:
            edu_rec = self._generate_education_recommendation(match_analysis)
            if edu_rec:
                recommendations.append(edu_rec)
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 2))
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _generate_skill_recommendations(self, analysis: MatchAnalysis) -> List[Recommendation]:
        """Generate recommendations for missing skills"""
        recommendations = []
        
        for i, skill in enumerate(analysis.missing_skills):
            # Determine priority based on position (earlier skills are often more important)
            if i < 3:
                priority = 'high'
            elif i < 7:
                priority = 'medium'
            else:
                priority = 'low'
            
            # Get learning resources
            resources = self._get_resources_for_skill(skill)
            
            rec = Recommendation(
                category='skill',
                priority=priority,
                title=f"Learn {skill}",
                description=f"The job requires {skill} which is not evident in your resume. "
                           f"Consider acquiring this skill or highlighting existing experience.",
                resources=resources
            )
            recommendations.append(rec)
            
            logger.debug(f"Added skill recommendation: {skill} (priority: {priority})")
        
        return recommendations
    
    def _generate_keyword_recommendations(self, analysis: MatchAnalysis) -> List[Recommendation]:
        """Generate recommendations for missing ATS keywords"""
        if not analysis.missing_keywords:
            return []
        
        # Group keywords for a single recommendation
        top_keywords = analysis.missing_keywords[:10]
        
        rec = Recommendation(
            category='keyword',
            priority='medium',
            title="Add Missing ATS Keywords",
            description=f"Your resume is missing these important keywords from the job description: "
                       f"{', '.join(top_keywords)}. Consider naturally incorporating them into your resume.",
            resources=["Use these keywords in your skills section, experience bullets, and summary"]
        )
        
        logger.debug(f"Added keyword recommendation with {len(top_keywords)} keywords")
        return [rec]
    
    def _generate_experience_recommendation(self, analysis: MatchAnalysis) -> Recommendation:
        """Generate recommendation for experience gap"""
        score = analysis.experience_match_score
        
        if score < 40:
            priority = 'high'
            description = ("Your experience level appears significantly below requirements. "
                          "Consider highlighting relevant projects, internships, or freelance work.")
        else:
            priority = 'medium'
            description = ("Your experience is close to requirements. "
                          "Emphasize your most relevant roles and quantify achievements.")
        
        return Recommendation(
            category='experience',
            priority=priority,
            title="Strengthen Experience Section",
            description=description,
            resources=[
                "Add quantifiable achievements (e.g., 'Improved performance by 30%')",
                "Include relevant side projects and open source contributions",
                "Highlight leadership and initiative in current roles"
            ]
        )
    
    def _generate_education_recommendation(self, analysis: MatchAnalysis) -> Recommendation:
        """Generate recommendation for education gap"""
        return Recommendation(
            category='education',
            priority='low',
            title="Consider Additional Certifications",
            description=("If the job requires specific educational qualifications, "
                        "consider obtaining relevant certifications to strengthen your application."),
            resources=[
                "Google Professional Certificates",
                "AWS/Azure/GCP Cloud Certifications",
                "Professional certifications in your field"
            ]
        )
    
    def _get_resources_for_skill(self, skill: str) -> List[str]:
        """Get learning resources for a specific skill"""
        skill_lower = skill.lower()
        
        for key, resources in self.LEARNING_RESOURCES.items():
            if key in skill_lower or skill_lower in key:
                return resources
        
        return self.LEARNING_RESOURCES['default']
    
    def get_improvement_roadmap(self, recommendations: List[Recommendation]) -> Dict:
        """
        Generate a structured improvement roadmap.
        
        Args:
            recommendations: List of recommendations
            
        Returns:
            Structured roadmap dictionary
        """
        roadmap = {
            'immediate': [],  # High priority items
            'short_term': [],  # Medium priority (1-2 months)
            'long_term': []    # Low priority (3+ months)
        }
        
        for rec in recommendations:
            item = {
                'title': rec.title,
                'category': rec.category,
                'description': rec.description,
                'resources': rec.resources
            }
            
            if rec.priority == 'high':
                roadmap['immediate'].append(item)
            elif rec.priority == 'medium':
                roadmap['short_term'].append(item)
            else:
                roadmap['long_term'].append(item)
        
        logger.info(f"Created roadmap: {len(roadmap['immediate'])} immediate, "
                   f"{len(roadmap['short_term'])} short-term, "
                   f"{len(roadmap['long_term'])} long-term items")
        
        return roadmap
