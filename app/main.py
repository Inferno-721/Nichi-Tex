"""
Clod_v2 - Main Orchestrator
Coordinates all services for resume analysis and LaTeX generation
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.analysis import MatchAnalysis
from app.services.resume_parser import ResumeParser
from app.services.jd_parser import JDParser
from app.services.nlp_matcher import NLPMatcher
from app.services.gap_analyzer import GapAnalyzer
from app.services.latex_generator import LaTeXGenerator

logger = get_logger(__name__)


class Clod:
    """
    Main orchestrator for the Clod_v2 resume optimization system.
    
    Provides a unified interface to:
    - Parse resumes from files or text
    - Parse job descriptions
    - Analyze match between resume and JD
    - Generate gap analysis and recommendations
    - Generate optimized LaTeX resume
    """
    
    def __init__(self):
        logger.info("Initializing Clod_v2 system")
        
        self.resume_parser = ResumeParser()
        self.jd_parser = JDParser()
        self.nlp_matcher = NLPMatcher()
        self.gap_analyzer = GapAnalyzer()
        self.latex_generator = LaTeXGenerator()
        
        logger.info("All services initialized successfully")
    
    def parse_resume(self, file_path: Optional[str] = None, text: Optional[str] = None) -> Resume:
        """
        Parse a resume from file or text.
        
        Args:
            file_path: Path to resume file (PDF or DOCX)
            text: Raw resume text
            
        Returns:
            Parsed Resume object
        """
        if file_path:
            logger.info(f"Parsing resume from file: {file_path}")
            return self.resume_parser.parse(file_path)
        elif text:
            logger.info("Parsing resume from text")
            return self.resume_parser.parse_text(text)
        else:
            raise ValueError("Either file_path or text must be provided")
    
    def parse_job_description(self, text: str) -> JobDescription:
        """
        Parse a job description from text.
        
        Args:
            text: Job description text
            
        Returns:
            Parsed JobDescription object
        """
        logger.info("Parsing job description")
        return self.jd_parser.parse(text)
    
    def analyze(self, resume: Resume, jd: JobDescription) -> MatchAnalysis:
        """
        Analyze match between resume and job description.
        
        Args:
            resume: Parsed Resume object
            jd: Parsed JobDescription object
            
        Returns:
            MatchAnalysis with scores and recommendations
        """
        logger.info("Starting resume-JD analysis")
        
        # Perform NLP matching
        analysis = self.nlp_matcher.analyze(resume, jd)
        
        # Generate recommendations
        recommendations = self.gap_analyzer.analyze(analysis)
        analysis.recommendations = recommendations
        
        logger.info(f"Analysis complete: {analysis.overall_score:.1f}% match")
        return analysis
    
    def generate_latex(
        self, 
        resume: Resume, 
        jd: Optional[JobDescription] = None,
        analysis: Optional[MatchAnalysis] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate LaTeX resume code.
        
        Args:
            resume: Parsed Resume object
            jd: Optional JobDescription for keyword optimization
            analysis: Optional MatchAnalysis for skill prioritization
            output_path: Optional path to save .tex file
            
        Returns:
            LaTeX code as string
        """
        logger.info("Generating LaTeX resume")
        
        latex_code = self.latex_generator.generate(resume, jd, analysis)
        
        if output_path:
            self.latex_generator.save_to_file(latex_code, output_path)
        
        return latex_code
    
    def process(
        self, 
        resume_path: Optional[str] = None,
        resume_text: Optional[str] = None,
        jd_text: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete end-to-end processing pipeline.
        
        Args:
            resume_path: Path to resume file
            resume_text: Raw resume text (alternative to file)
            jd_text: Job description text
            output_path: Path to save generated LaTeX
            
        Returns:
            Dictionary with all results
        """
        logger.info("Starting complete processing pipeline")
        
        # Parse resume
        resume = self.parse_resume(file_path=resume_path, text=resume_text)
        
        # Parse JD if provided
        jd = None
        analysis = None
        
        if jd_text:
            jd = self.parse_job_description(jd_text)
            analysis = self.analyze(resume, jd)
        
        # Generate LaTeX
        latex_code = self.generate_latex(resume, jd, analysis, output_path)
        
        results = {
            'resume': resume,
            'job_description': jd,
            'analysis': analysis,
            'latex_code': latex_code,
            'output_path': output_path
        }
        
        logger.info("Processing pipeline complete")
        return results
    
    def get_summary(self, analysis: MatchAnalysis) -> str:
        """Get a human-readable summary of the analysis."""
        lines = [
            f"Overall Match: {analysis.overall_score:.1f}%",
            f"Skills Match: {analysis.skill_match_score:.1f}%",
            f"Experience Match: {analysis.experience_match_score:.1f}%",
            f"Education Match: {analysis.education_match_score:.1f}%",
            "",
            f"Matched Skills: {len(analysis.matched_skills)}",
            f"Missing Skills: {len(analysis.missing_skills)}",
            "",
            "Missing Skills:",
        ]
        
        for skill in analysis.missing_skills[:10]:
            lines.append(f"  - {skill}")
        
        if analysis.recommendations:
            lines.append("")
            lines.append("Top Recommendations:")
            for rec in analysis.recommendations[:5]:
                lines.append(f"  [{rec.priority.upper()}] {rec.title}")
        
        return "\n".join(lines)


# Convenience function for quick usage
def quick_analyze(resume_path: str, jd_text: str) -> Dict[str, Any]:
    """
    Quick analysis function for simple use cases.
    
    Args:
        resume_path: Path to resume file
        jd_text: Job description text
        
    Returns:
        Analysis results dictionary
    """
    clod = Clod()
    return clod.process(resume_path=resume_path, jd_text=jd_text)
