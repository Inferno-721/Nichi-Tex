"""
NLP Matching Service
Compares resume against job description using transformer models
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.analysis import MatchAnalysis, SkillMatch, SectionScore
from config.settings import DEFAULT_MODEL, SIMILARITY_THRESHOLD

logger = get_logger(__name__)


class NLPMatcher:
    """
    NLP-based matching service using sentence transformers.
    Computes semantic similarity between resume and job description.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize the NLP matcher.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name or DEFAULT_MODEL
        self.model = None
        self._initialized = False
        
        logger.info(f"Initializing NLPMatcher with model: {self.model_name}")
    
    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self._initialized:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self._initialized = True
            logger.info("Model loaded successfully")
            
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise ImportError(
                "sentence-transformers required. Install with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        self._load_model()
        
        from sentence_transformers import util
        
        embeddings = self.model.encode([text1, text2], convert_to_tensor=True)
        similarity = util.cos_sim(embeddings[0], embeddings[1])
        
        return float(similarity[0][0])
    
    def match_skills(
        self, 
        resume_skills: List[str], 
        jd_skills: List[str]
    ) -> Tuple[List[SkillMatch], float]:
        """
        Match resume skills against JD required skills using semantic similarity.
        Args:
            resume_skills: List of skills from resume
            jd_skills: List of skills from job description
        Returns:
            Tuple of (list of SkillMatch objects, overall skill match score)
        """
        self._load_model()
        
        if not jd_skills:
            logger.warning("No JD skills provided for matching")
            return [], 1.0
        
        if not resume_skills:
            logger.warning("No resume skills provided for matching")
            return [SkillMatch(skill=s, matched=False, similarity_score=0.0) for s in jd_skills], 0.0
        
        logger.info(f"Matching {len(resume_skills)} resume skills against {len(jd_skills)} JD skills")
        
        from sentence_transformers import util
        
        # Encode all skills
        resume_embeddings = self.model.encode(resume_skills, convert_to_tensor=True)
        jd_embeddings = self.model.encode(jd_skills, convert_to_tensor=True)
        
        # Compute similarity matrix
        similarity_matrix = util.cos_sim(jd_embeddings, resume_embeddings)
        
        skill_matches = []
        matched_count = 0
        
        for i, jd_skill in enumerate(jd_skills):
            # Find best match for this JD skill
            best_score = float(similarity_matrix[i].max())
            best_match_idx = int(similarity_matrix[i].argmax())
            
            matched = best_score >= SIMILARITY_THRESHOLD
            matched_with = resume_skills[best_match_idx] if matched else None
            
            if matched:
                matched_count += 1
                logger.debug(f"Skill match: '{jd_skill}' ~ '{matched_with}' (score: {best_score:.3f})")
            
            skill_matches.append(SkillMatch(
                skill=jd_skill,
                matched=matched,
                similarity_score=best_score,
                matched_with=matched_with
            ))
        
        overall_score = (matched_count / len(jd_skills)) * 100 if jd_skills else 0
        
        logger.info(f"Skill matching complete: {matched_count}/{len(jd_skills)} matched ({overall_score:.1f}%)")
        
        return skill_matches, overall_score
    
    def analyze(self, resume: Resume, jd: JobDescription) -> MatchAnalysis:
        """
        Perform full analysis of resume against job description.
        Args:
            resume: Parsed resume object
            jd: Parsed job description object
        Returns:
            MatchAnalysis object with all scores and recommendations
        """
        logger.info("Starting full resume-JD analysis")
        
        analysis = MatchAnalysis()
        
        # 1. Skill matching
        all_resume_skills = resume.skills.all_skills()
        skill_matches, skill_score = self.match_skills(
            all_resume_skills, 
            jd.required_skills
        )
        analysis.skill_matches = skill_matches
        analysis.skill_match_score = skill_score
        
        # Extract matched and missing skills
        analysis.matched_skills = [m.skill for m in skill_matches if m.matched]
        analysis.missing_skills = [m.skill for m in skill_matches if not m.matched]
        
        # 2. Experience matching
        analysis.experience_match_score = self._match_experience(resume, jd)
        
        # 3. Education matching
        analysis.education_match_score = self._match_education(resume, jd)
        
        # 4. Overall text similarity
        resume_text = resume.get_all_text()
        jd_text = jd.get_searchable_text()
        text_similarity = self.compute_similarity(resume_text, jd_text) * 100
        
        # 5. Calculate overall score (weighted average)
        weights = {
            'skills': 0.40,
            'experience': 0.25,
            'education': 0.15,
            'text_similarity': 0.20
        }
        
        analysis.overall_score = (
            analysis.skill_match_score * weights['skills'] +
            analysis.experience_match_score * weights['experience'] +
            analysis.education_match_score * weights['education'] +
            text_similarity * weights['text_similarity']
        )
        
        # 6. Section scores
        analysis.section_scores = [
            SectionScore("Skills", analysis.skill_match_score / 100, 1.0),
            SectionScore("Experience", analysis.experience_match_score / 100, 1.0),
            SectionScore("Education", analysis.education_match_score / 100, 1.0),
            SectionScore("Content Relevance", text_similarity / 100, 1.0),
        ]
        
        # 7. Missing keywords
        analysis.missing_keywords = self._find_missing_keywords(resume, jd)
        
        # 8. Generate summary
        analysis.summary = self._generate_summary(analysis)
        
        logger.info(f"Analysis complete. Overall score: {analysis.overall_score:.1f}%")
        
        return analysis
    
    def _match_experience(self, resume: Resume, jd: JobDescription) -> float:
        """Calculate experience match score"""
        if jd.required_experience_years is None:
            return 100.0  # No requirement specified
        
        # Calculate total years from resume
        total_years = 0
        for exp in resume.experience:
            # Simple estimation: each job counts as 1-2 years
            if exp.is_current:
                total_years += 2
            else:
                total_years += 1.5
        
        if total_years >= jd.required_experience_years:
            score = 100.0
        else:
            score = (total_years / jd.required_experience_years) * 100
        
        logger.debug(f"Experience match: {total_years:.1f} years vs {jd.required_experience_years} required = {score:.1f}%")
        return min(score, 100.0)
    
    def _match_education(self, resume: Resume, jd: JobDescription) -> float:
        """Calculate education match score"""
        if not jd.required_education:
            return 100.0  # No requirement specified
        
        if not resume.education:
            return 30.0  # Some base score even without listed education
        
        jd_edu_lower = jd.required_education.lower()
        
        # Check education levels
        edu_levels = {
            'phd': 100,
            'doctorate': 100,
            'master': 90,
            'mba': 85,
            'bachelor': 75,
            'associate': 60,
            'diploma': 50
        }
        
        resume_level = 50  # Default
        for edu in resume.education:
            degree_lower = edu.degree.lower()
            for level, score in edu_levels.items():
                if level in degree_lower:
                    resume_level = max(resume_level, score)
        
        # Check for field of study match
        field_bonus = 0
        for edu in resume.education:
            field_lower = edu.field_of_study.lower() + edu.degree.lower()
            if any(term in field_lower for term in ['computer', 'data', 'science', 'engineering', 'statistics', 'mathematics']):
                field_bonus = 10
                break
        
        score = min(resume_level + field_bonus, 100)
        logger.debug(f"Education match score: {score}%")
        
        return float(score)
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase and strip separators so 'Python 3', 'python-3' and
        'Python3' compare equal. Keeps alphanumerics only."""
        return re.sub(r'[\s\-_\./]+', '', text.lower())

    def _find_missing_keywords(self, resume: Resume, jd: JobDescription) -> List[str]:
        """Find JD keywords that are absent from the resume.

        Matching is tolerant of separator/version variations (e.g. 'Node.js'
        vs 'nodejs', 'CI/CD' vs 'ci cd') by comparing on a normalised form,
        backed by a plain substring check on the original text.
        """
        resume_text_lower = resume.get_all_text().lower()
        resume_text_norm = self._normalize(resume_text_lower)

        missing: List[str] = []
        seen_keywords = set()  # Track normalised keywords to avoid duplicates

        for keyword in jd.keywords:
            keyword_lower = keyword.lower().strip()
            if not keyword_lower:
                continue

            normalized = self._normalize(keyword_lower)
            if not normalized or normalized in seen_keywords:
                continue
            seen_keywords.add(normalized)

            # Present if either the raw substring or its normalised form appears.
            present = (
                keyword_lower in resume_text_lower
                or normalized in resume_text_norm
            )
            if not present:
                missing.append(keyword)

        logger.debug(f"Found {len(missing)} missing keywords")
        return missing[:20]  # Limit to top 20
    
    def _generate_summary(self, analysis: MatchAnalysis) -> str:
        """Generate a human-readable summary of the analysis"""
        score = analysis.overall_score
        
        if score >= 90:
            grade = "Excellent"
            message = "Your resume is very well aligned with this job description."
        elif score >= 75:
            grade = "Good"
            message = "Your resume shows strong alignment with some areas for improvement."
        elif score >= 60:
            grade = "Moderate"
            message = "Your resume has partial alignment. Consider addressing the skill gaps."
        elif score >= 40:
            grade = "Fair"
            message = "There are significant gaps between your resume and the job requirements."
        else:
            grade = "Low"
            message = "Your resume needs substantial updates to match this position."
        
        skill_gap = len(analysis.missing_skills)
        
        summary = f"{grade} Match ({score:.1f}%): {message}"
        if skill_gap > 0:
            summary += f" Missing {skill_gap} key skill(s)."
        
        return summary
