"""
Resume Improvement Prompts Configuration

These prompts are designed to fine-tune AI responses for resume analysis,
ensuring clear, actionable, and specific feedback instead of vague responses.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResumePrompt:
    """Individual prompt configuration"""
    name: str
    description: str
    template: str
    requires_jd: bool = False  # Whether this prompt needs a job description


class ResumePrompts:
    """
    Collection of 8 fine-tuned prompts for resume improvement.
    Each prompt is designed to generate specific, actionable feedback.
    """
    
    # 1. Spot the Flaws - Identify weaknesses
    SPOT_FLAWS = ResumePrompt(
        name="spot_flaws",
        description="Identify weak areas, overused buzzwords, and missing metrics",
        template="""Act as a recruiter for {industry_role}. Review the resume below and highlight:
1. Weak areas that need improvement
2. Overused buzzwords that should be replaced
3. Missing metrics and quantifiable achievements
4. Vague statements that lack specificity

Be brutally honest and specific. For each issue identified, explain WHY it's a problem and suggest a concrete fix.

Resume:
{resume_content}""",
        requires_jd=False
    )
    
    # 2. Rewrite for Impact - Make it results-driven
    REWRITE_IMPACT = ResumePrompt(
        name="rewrite_impact",
        description="Rewrite to be results-driven and compelling",
        template="""Rewrite this resume to sound more results-driven, quantifiable, and compelling for {target_role}.

Focus on:
- Achievements over duties (use the CAR method: Challenge, Action, Result)
- Quantifiable outcomes (percentages, dollar amounts, time saved, etc.)
- Strong action verbs that demonstrate impact
- Removing passive language and filler words

Provide the rewritten version with clear before/after comparisons for key sections.

Resume:
{resume_content}""",
        requires_jd=False
    )
    
    # 3. ATS Boost - Optimize for tracking systems
    ATS_OPTIMIZE = ResumePrompt(
        name="ats_optimize",
        description="Optimize for Applicant Tracking Systems",
        template="""Update this resume to be fully optimized for Applicant Tracking Systems (ATS) for the role of {target_role}.

Requirements:
1. Identify and naturally incorporate industry-specific keywords
2. Use standard section headers (Experience, Education, Skills, etc.)
3. Avoid tables, graphics, headers/footers that ATS cannot parse
4. Use standard fonts and formatting
5. Include both spelled-out terms and acronyms where applicable
6. Match key phrases from common job descriptions for this role

Provide:
- A list of critical keywords to include
- Suggested rewrites for each section
- ATS compatibility score (1-10) with justification

Resume:
{resume_content}""",
        requires_jd=False
    )
    
    # 4. Craft My Hook - Professional summary
    CRAFT_HOOK = ResumePrompt(
        name="craft_hook",
        description="Create a powerful 3-line professional summary",
        template="""Write a powerful, 3-line professional summary that hooks a recruiter in under 10 seconds.

Guidelines:
- Line 1: Who you are (title + years of experience + core expertise)
- Line 2: Your biggest achievement or unique value proposition
- Line 3: What you bring to the table / career goal

The summary must:
- Be specific, not generic
- Include at least one quantifiable achievement
- Use power words that convey confidence
- Avoid clichés like "hard-working," "team player," "results-oriented"

Provide 3 variations to choose from, each with a different angle.

Resume:
{resume_content}

Target Role: {target_role}""",
        requires_jd=False
    )
    
    # 5. Upgrade Experience - Enhance work history
    UPGRADE_EXPERIENCE = ResumePrompt(
        name="upgrade_experience",
        description="Rephrase experience to highlight impact and results",
        template="""Rephrase the experience section to highlight impact, results, and transferable skills.

For each position:
1. Start with a strong action verb (Led, Spearheaded, Transformed, etc.)
2. Include specific metrics (%, $, time, quantity)
3. Show progression and growth
4. Highlight transferable skills relevant to the target role
5. Use the STAR method (Situation, Task, Action, Result) where applicable

Format each bullet point as: [Action Verb] + [What you did] + [Result/Impact]

Provide the upgraded version with explanations for major changes.

Resume:
{resume_content}

Target Role: {target_role}""",
        requires_jd=False
    )
    
    # 6. Format Fix - Clean structure
    FORMAT_FIX = ResumePrompt(
        name="format_fix",
        description="Suggest a clean, modern, ATS-friendly format",
        template="""Suggest a clean, modern resume format that works for both humans and ATS.

Requirements:
- No graphics, icons, or images
- No multi-column layouts
- No tables or text boxes
- Clear visual hierarchy
- Consistent spacing and alignment
- Standard, readable fonts (Arial, Calibri, Times New Roman)
- 10-12pt font size for body, 14-16pt for headers
- 0.5-1 inch margins

Provide:
1. Recommended section order
2. Formatting specifications for each section
3. Spacing guidelines
4. A text-based ASCII template showing the structure
5. Common formatting mistakes to avoid

Current Resume:
{resume_content}""",
        requires_jd=False
    )
    
    # 7. Tailor for Role - Job-specific customization
    TAILOR_ROLE = ResumePrompt(
        name="tailor_role",
        description="Tailor resume for a specific job description",
        template="""Tailor this resume to fit the specific job description provided.

Analysis Required:
1. Identify key requirements from the JD
2. Match resume content to JD requirements
3. Highlight gaps between resume and JD
4. Reword sections to mirror the JD language
5. Prioritize most relevant experiences

Deliverables:
- Keyword match analysis (found vs missing)
- Specific rewrites for each section
- Recommended additions or removals
- Match score percentage with breakdown

Resume:
{resume_content}

Job Description:
{job_description}""",
        requires_jd=True
    )
    
    # 8. Standout Cover Letter - Compelling letter
    COVER_LETTER = ResumePrompt(
        name="cover_letter",
        description="Write a compelling cover letter under 200 words",
        template="""Write a compelling cover letter based on the resume and job description.

Requirements:
- Under 200 words
- Personal and enthusiastic tone (not generic)
- Clear connection between experience and job requirements
- Specific example of a relevant achievement
- Strong opening hook
- Confident closing with call to action

Structure:
- Paragraph 1 (2-3 sentences): Hook + why this specific company/role
- Paragraph 2 (3-4 sentences): Relevant achievement + how it connects to JD
- Paragraph 3 (2-3 sentences): Enthusiasm + next steps

Resume:
{resume_content}

Job Description:
{job_description}

Company Name: {company_name}""",
        requires_jd=True
    )
    
    @classmethod
    def get_all_prompts(cls) -> list:
        """Return all prompt configurations"""
        return [
            cls.SPOT_FLAWS,
            cls.REWRITE_IMPACT,
            cls.ATS_OPTIMIZE,
            cls.CRAFT_HOOK,
            cls.UPGRADE_EXPERIENCE,
            cls.FORMAT_FIX,
            cls.TAILOR_ROLE,
            cls.COVER_LETTER,
        ]
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional[ResumePrompt]:
        """Get a specific prompt by name"""
        prompt_map = {
            "spot_flaws": cls.SPOT_FLAWS,
            "rewrite_impact": cls.REWRITE_IMPACT,
            "ats_optimize": cls.ATS_OPTIMIZE,
            "craft_hook": cls.CRAFT_HOOK,
            "upgrade_experience": cls.UPGRADE_EXPERIENCE,
            "format_fix": cls.FORMAT_FIX,
            "tailor_role": cls.TAILOR_ROLE,
            "cover_letter": cls.COVER_LETTER,
        }
        return prompt_map.get(name.lower())
    
    @classmethod
    def get_prompts_requiring_jd(cls) -> list:
        """Return prompts that require a job description"""
        return [p for p in cls.get_all_prompts() if p.requires_jd]
    
    @classmethod
    def get_standalone_prompts(cls) -> list:
        """Return prompts that work without a job description"""
        return [p for p in cls.get_all_prompts() if not p.requires_jd]
