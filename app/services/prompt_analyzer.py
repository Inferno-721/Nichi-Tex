"""
Prompt-Based Analyzer Service
Uses AI with fine-tuned prompts for specific, actionable resume feedback
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.services.ai_client import get_ai_client
from app.models.analysis import MatchAnalysis
from config.prompts import ResumePrompts, ResumePrompt

logger = get_logger(__name__)


@dataclass
class EnhancedFeedback:
    """Enhanced feedback from prompt-based analysis"""
    flaws: str = ""
    impact_rewrite: str = ""
    ats_suggestions: str = ""
    professional_summary: str = ""
    experience_upgrade: str = ""
    format_recommendations: str = ""
    tailored_suggestions: str = ""
    cover_letter: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary, excluding empty fields"""
        return {k: v for k, v in {
            "flaws": self.flaws,
            "impact_rewrite": self.impact_rewrite,
            "ats_suggestions": self.ats_suggestions,
            "professional_summary": self.professional_summary,
            "experience_upgrade": self.experience_upgrade,
            "format_recommendations": self.format_recommendations,
            "tailored_suggestions": self.tailored_suggestions,
            "cover_letter": self.cover_letter,
        }.items() if v}


class PromptAnalyzer:
    """
    AI-powered resume analyzer using fine-tuned prompts.
    Integrates with existing analysis to provide specific, actionable feedback.
    """
    
    # Message shown when no usable AI key is configured.
    _UNAVAILABLE_MSG = (
        "AI analysis is unavailable. Set a valid GOOGLE_API_KEY in your .env "
        "to enable AI-powered feedback."
    )

    def __init__(self):
        logger.info("Initializing PromptAnalyzer")
        self.ai = get_ai_client()

    @property
    def available(self) -> bool:
        return self.ai.available

    # Cap feedback length: keeps responses focused and bounds latency.
    _MAX_FEEDBACK_TOKENS = 700
    _CONCISE_DIRECTIVE = (
        "\n\nIMPORTANT: Be concise and actionable. Use short bullet points, "
        "skip preamble, and keep the whole response under ~250 words."
    )

    def _call_ai(self, prompt: str) -> str:
        """Call AI model with prompt; return a safe string (never None)."""
        if not self.ai.available:
            logger.warning("AI model not available, returning fallback response")
            return self._UNAVAILABLE_MSG
        # generate_text returns the fallback ("") on any error -> normalise it.
        result = self.ai.generate_text(
            prompt + self._CONCISE_DIRECTIVE,
            fallback="",
            max_output_tokens=self._MAX_FEEDBACK_TOKENS,
        )
        return result or self._UNAVAILABLE_MSG
    
    def analyze_with_prompts(
        self,
        resume_text: str,
        jd_text: Optional[str] = None,
        target_role: Optional[str] = None,
        analysis: Optional[MatchAnalysis] = None,
        prompts_to_run: Optional[list] = None
    ) -> EnhancedFeedback:
        """
        Run relevant prompts based on analysis results.
        
        Args:
            resume_text: Raw resume text
            jd_text: Optional job description text
            target_role: Target role/industry
            analysis: Optional existing MatchAnalysis for smart prompt selection
            prompts_to_run: Specific prompts to run (if None, auto-selects based on analysis)
        
        Returns:
            EnhancedFeedback with AI-generated suggestions
        """
        logger.info("Running prompt-based analysis")
        feedback = EnhancedFeedback()

        # Short-circuit when AI is unavailable so we don't repeat the same
        # placeholder across every field.
        if not self.ai.available:
            feedback.flaws = self._UNAVAILABLE_MSG
            return feedback

        # Auto-select prompts based on analysis scores if not specified
        if prompts_to_run is None:
            prompts_to_run = self._select_prompts(analysis)
        
        industry_role = target_role or "the target industry"

        # Build the (name, filled_prompt) work list.
        jobs = []
        for prompt_name in prompts_to_run:
            prompt_config = ResumePrompts.get_by_name(prompt_name)
            if not prompt_config:
                continue
            filled_prompt = self._fill_prompt(
                prompt_config, resume_text, jd_text, industry_role, target_role
            )
            jobs.append((prompt_name, filled_prompt))

        # Run the independent prompts concurrently — they don't depend on each
        # other, so this turns N sequential round-trips into ~1 round-trip of
        # wall-clock time.
        if jobs:
            from concurrent.futures import ThreadPoolExecutor

            def _run(job):
                name, prompt = job
                logger.info(f"Running prompt: {name}")
                return name, self._call_ai(prompt)

            with ThreadPoolExecutor(max_workers=min(len(jobs), 6)) as pool:
                for name, result in pool.map(_run, jobs):
                    self._store_result(feedback, name, result)

        logger.info(f"Prompt analysis complete. Generated {len(jobs)} feedback sections.")
        return feedback
    
    def _select_prompts(self, analysis: Optional[MatchAnalysis]) -> list:
        """Auto-select prompts based on analysis scores"""
        prompts = []
        
        if analysis is None:
            # No analysis, run core prompts
            return ["spot_flaws", "craft_hook", "ats_optimize"]
        
        # Always run flaws detection and professional summary
        prompts.append("spot_flaws")
        prompts.append("craft_hook")
        
        # If skill match is low, suggest ATS optimization
        if analysis.skill_match_score < 70:
            prompts.append("ats_optimize")
        
        # If experience match is low, suggest experience upgrade
        if analysis.experience_match_score < 70:
            prompts.append("upgrade_experience")
        
        # If overall score is low, suggest tailored rewrite
        if analysis.overall_score < 60:
            prompts.append("rewrite_impact")
        
        return prompts
    
    def _fill_prompt(
        self,
        prompt_config: ResumePrompt,
        resume_text: str,
        jd_text: Optional[str],
        industry_role: str,
        target_role: Optional[str]
    ) -> str:
        """Fill prompt template with available data"""
        template = prompt_config.template
        
        # Common replacements
        replacements = {
            "{resume_content}": resume_text,
            "{industry_role}": industry_role,
            "{target_role}": target_role or industry_role,
            "{job_description}": jd_text or "Not provided",
            "{company_name}": "the company",
        }
        
        filled = template
        for key, value in replacements.items():
            filled = filled.replace(key, value)
        
        return filled
    
    def _store_result(self, feedback: EnhancedFeedback, prompt_name: str, result: str):
        """Store AI result in appropriate feedback field"""
        mapping = {
            "spot_flaws": "flaws",
            "rewrite_impact": "impact_rewrite",
            "ats_optimize": "ats_suggestions",
            "craft_hook": "professional_summary",
            "upgrade_experience": "experience_upgrade",
            "format_fix": "format_recommendations",
            "tailor_role": "tailored_suggestions",
            "cover_letter": "cover_letter",
        }
        
        field_name = mapping.get(prompt_name)
        if field_name:
            setattr(feedback, field_name, result)
    
    # Convenience methods for specific prompts
    def spot_flaws(self, resume_text: str, industry_role: str = "the target industry") -> str:
        """Run spot_flaws prompt"""
        feedback = self.analyze_with_prompts(
            resume_text, target_role=industry_role, prompts_to_run=["spot_flaws"]
        )
        return feedback.flaws
    
    def craft_summary(self, resume_text: str, target_role: str) -> str:
        """Generate professional summary hook"""
        feedback = self.analyze_with_prompts(
            resume_text, target_role=target_role, prompts_to_run=["craft_hook"]
        )
        return feedback.professional_summary
    
    def ats_optimize(self, resume_text: str, target_role: str) -> str:
        """Get ATS optimization suggestions"""
        feedback = self.analyze_with_prompts(
            resume_text, target_role=target_role, prompts_to_run=["ats_optimize"]
        )
        return feedback.ats_suggestions
    
    def tailor_for_job(self, resume_text: str, jd_text: str) -> str:
        """Tailor resume for specific job"""
        feedback = self.analyze_with_prompts(
            resume_text, jd_text=jd_text, prompts_to_run=["tailor_role"]
        )
        return feedback.tailored_suggestions
    
    def generate_cover_letter(self, resume_text: str, jd_text: str, company_name: str = "") -> str:
        """Generate cover letter"""
        feedback = self.analyze_with_prompts(
            resume_text, jd_text=jd_text, prompts_to_run=["cover_letter"]
        )
        return feedback.cover_letter
