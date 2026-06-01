"""
LaTeX Resume Generator Service
Generates ATS-optimized LaTeX code from resume data using custom RenderCV template
With controlled AI enhancement that maintains original tone and content.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.services.ai_client import get_ai_client
from app.models.resume import Resume, PersonalInfo, Education, Experience, Project, Skills
from app.models.job_description import JobDescription
from app.models.analysis import MatchAnalysis

logger = get_logger(__name__)


class LaTeXGenerator:
    """
    Generates professional LaTeX resume code optimized for ATS.
    Uses RenderCV-style template with controlled AI enhancement.
    """
    
    # LaTeX special characters that need escaping
    LATEX_SPECIAL_CHARS = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    
    def __init__(self, enable_ai_enhancement: bool = True):
        """
        Initialize LaTeX Generator

        Args:
            enable_ai_enhancement: Whether to enable AI enhancement (default: True)
        """
        logger.info("Initializing LaTeXGenerator")
        self.enable_ai = enable_ai_enhancement
        self.ai = get_ai_client() if enable_ai_enhancement else None
        # Cache of enhanced strings: original text -> improved text, populated
        # by a single batched AI call per generate(). Falls back to identity.
        self._enhanced: Dict[str, str] = {}

    @property
    def _ai_active(self) -> bool:
        return bool(self.enable_ai and self.ai is not None and self.ai.available)

    def _build_enhancement_map(
        self,
        resume: Resume,
        jd: Optional[JobDescription],
        analysis: Optional[MatchAnalysis],
    ) -> None:
        """Enhance every experience bullet and project description in ONE AI call.

        Populates ``self._enhanced`` mapping original->improved text. On any
        failure the map stays empty and callers transparently use the original
        text. This replaces the previous design that issued one API call per
        bullet (dozens of sequential calls per resume).
        """
        self._enhanced = {}
        if not self._ai_active:
            return

        # Collect all editable strings with stable ids.
        items: List[dict] = []
        for ei, exp in enumerate(resume.experience):
            for bi, bullet in enumerate(exp.responsibilities):
                if bullet and bullet.strip():
                    items.append({"id": f"e{ei}_{bi}", "text": bullet,
                                  "context": f"{exp.title} at {exp.company}"})
        for pi, proj in enumerate(resume.projects):
            if proj.description and proj.description.strip():
                items.append({"id": f"p{pi}", "text": proj.description,
                              "context": f"Project: {proj.name}"})

        if not items:
            return

        matched = (analysis.matched_skills[:8] if analysis and analysis.matched_skills else [])
        missing = (analysis.missing_skills[:5] if analysis and analysis.missing_skills else [])
        role = jd.title if jd and jd.title else "the target role"

        prompt = f"""You optimize resume bullet points and project descriptions for ATS
and readability for {role}.

STRICT RULES:
- PRESERVE every original fact, metric and achievement. Do NOT invent anything.
- Keep each item roughly the same length (1-2 lines).
- Start bullets with strong action verbs; remove filler/passive language.
- Naturally surface relevant skills where truthful: {', '.join(matched) or 'n/a'}.
- Relate to these target skills only if genuinely applicable: {', '.join(missing) or 'n/a'}.

Return a JSON object mapping each item's "id" to its improved text, e.g.
{{"e0_0": "improved text", "p0": "improved text"}}.
Return ONLY the items given; keep ids identical.

Items:
{json.dumps(items, ensure_ascii=False, indent=2)}"""

        result = self.ai.generate_json(prompt)
        if not isinstance(result, dict):
            logger.info("AI enhancement unavailable; using original resume text")
            return

        by_id = {it["id"]: it["text"] for it in items}
        for item_id, original in by_id.items():
            improved = result.get(item_id)
            if not isinstance(improved, str):
                continue
            improved = improved.strip().strip('"').strip("'").strip()
            # Reject hallucinated/over-long or truncated rewrites.
            if not improved or not (0.5 * len(original) <= len(improved) <= 1.6 * len(original)):
                continue
            self._enhanced[original] = improved

        logger.info(f"AI enhanced {len(self._enhanced)}/{len(items)} resume items in one call")

    def _enhance(self, text: str) -> str:
        """Return the AI-improved version of ``text`` if available, else original."""
        return self._enhanced.get(text, text)

    def escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters in text"""
        if not text:
            return ""
        
        for char, replacement in self.LATEX_SPECIAL_CHARS.items():
            text = text.replace(char, replacement)
        
        return text
    
    def generate(
        self, 
        resume: Resume, 
        jd: Optional[JobDescription] = None,
        analysis: Optional[MatchAnalysis] = None
    ) -> str:
        """
        Generate complete LaTeX resume code.
        
        Args:
            resume: Resume object with parsed data
            jd: Optional job description for keyword optimization
            analysis: Optional match analysis for prioritization
            
        Returns:
            Complete LaTeX code as string
        """
        logger.info("Generating LaTeX resume")

        # Enhance all bullets/descriptions in a single batched AI call (if enabled).
        self._build_enhancement_map(resume, jd, analysis)

        # Debug: Log what data we received
        logger.debug(f"Resume personal_info: {resume.personal_info}")
        logger.debug(f"Resume education count: {len(resume.education)}")
        logger.debug(f"Resume experience count: {len(resume.experience)}")
        logger.debug(f"Resume skills: {resume.skills.all_skills()}")
        logger.debug(f"Resume projects count: {len(resume.projects)}")
        logger.debug(f"Resume certifications count: {len(resume.certifications)}")
        
        # Build LaTeX sections
        header = self._generate_header(resume.personal_info)
        personal = self._generate_personal_section(resume.personal_info)
        education = self._generate_education_section(resume.education)
        experience = self._generate_experience_section(resume.experience, jd, analysis)
        skills = self._generate_skills_section(resume.skills, jd, analysis)
        projects = self._generate_projects_section(resume.projects, jd, analysis)
        certifications = self._generate_certifications_section(resume.certifications)
        achievements = self._generate_achievements_section(resume.achievements) if hasattr(resume, 'achievements') else ""
        footer = self._generate_footer()
        
        # Combine all sections
        latex_code = "\n".join([
            header,
            personal,
            education,
            experience,
            skills,
            projects,
            certifications,
            achievements,
            footer
        ])
        
        logger.info("LaTeX generation complete")
        return latex_code
    
    def _generate_header(self, info: PersonalInfo) -> str:
        """Generate LaTeX document header with packages"""
        name = self.escape_latex(info.name) or "Your Name"
        
        return rf"""\documentclass[10pt, letterpaper]{{article}}

% Packages:
\usepackage[
    ignoreheadfoot,
    top=1cm,
    bottom=1cm,
    left=2cm,
    right=2cm,
    footskip=1.0cm,
]{{geometry}}
\usepackage{{titlesec}}
\usepackage{{tabularx}}
\usepackage{{array}}
\usepackage[dvipsnames]{{xcolor}}
\definecolor{{primaryColor}}{{RGB}}{{0, 0, 0}}
\usepackage{{enumitem}}
\usepackage{{fontawesome5}}
\usepackage{{amsmath}}
\usepackage[
    pdftitle={{{name}'s CV}},
    pdfauthor={{{name}}},
    pdfcreator={{LaTeX with Clod_v2}},
    colorlinks=true,
    urlcolor=primaryColor
]{{hyperref}}
\usepackage[pscoord]{{eso-pic}}
\usepackage{{calc}}
\usepackage{{bookmark}}
\usepackage{{lastpage}}
\usepackage{{changepage}}
\usepackage{{paracol}}
\usepackage{{ifthen}}
\usepackage{{needspace}}
\usepackage{{iftex}}

% Ensure that generated pdf is machine readable/ATS parsable:
\ifPDFTeX
    \input{{glyphtounicode}}
    \pdfgentounicode=1
    \usepackage[T1]{{fontenc}}
    \usepackage[utf8]{{inputenc}}
    \usepackage{{lmodern}}
\fi

\usepackage{{charter}}

% Settings:
\raggedright
\AtBeginEnvironment{{adjustwidth}}{{\partopsep0pt}}
\pagestyle{{empty}}
\setcounter{{secnumdepth}}{{0}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\topskip}}{{0pt}}
\setlength{{\columnsep}}{{0.15cm}}
\pagenumbering{{gobble}}

\titleformat{{\section}}{{\needspace{{4\baselineskip}}\bfseries\large}}{{}}{{0pt}}{{}}[\vspace{{1pt}}\titlerule]

\titlespacing{{\section}}{{-1pt}}{{0.3cm}}{{0.2cm}}

\renewcommand\labelitemi{{$\vcenter{{\hbox{{\small$\bullet$}}}}$}}

\newenvironment{{highlights}}{{
    \begin{{itemize}}[
        topsep=0.10cm,
        parsep=0.10cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=0cm + 10pt
    ]
}}{{
    \end{{itemize}}
}}

\newenvironment{{highlightsforbulletentries}}{{
    \begin{{itemize}}[
        topsep=0.10cm,
        parsep=0.10cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=10pt
    ]
}}{{
    \end{{itemize}}
}}

\newenvironment{{onecolentry}}{{
    \begin{{adjustwidth}}{{0cm + 0.00001cm}}{{0cm + 0.00001cm}}
}}{{
    \end{{adjustwidth}}
}}

\newenvironment{{twocolentry}}[2][]{{
    \onecolentry
    \def\secondColumn{{#2}}
    \setcolumnwidth{{\fill, 5.5cm}}
    \begin{{paracol}}{{2}}
}}{{
    \switchcolumn \raggedleft \secondColumn
    \end{{paracol}}
    \endonecolentry
}}

\newenvironment{{header}}{{
    \setlength{{\topsep}}{{0pt}}\par\kern\topsep\centering\linespread{{1.5}}
}}{{
    \par\kern\topsep
}}

\let\hrefWithoutArrow\href

\begin{{document}}
    \newcommand{{\AND}}{{\unskip
        \cleaders\copy\ANDbox\hskip\wd\ANDbox
        \ignorespaces
    }}
    \newsavebox\ANDbox
    \sbox\ANDbox{{$|$}}
"""
    
    def _generate_personal_section(self, info: PersonalInfo) -> str:
        """Generate personal info header section"""
        name = self.escape_latex(info.name) or "Your Name"
        
        contact_items = []
        
        if info.email:
            contact_items.append(
                f"\\mbox{{\\hrefWithoutArrow{{mailto:{info.email}}}{{{self.escape_latex(info.email)}}}}}"
            )
        
        if info.phone:
            phone_clean = info.phone.replace(" ", "").replace("-", "")
            contact_items.append(
                f"\\mbox{{\\hrefWithoutArrow{{tel:{phone_clean}}}{{{self.escape_latex(info.phone)}}}}}"
            )
        
        if info.portfolio:
            portfolio_display = info.portfolio.replace('https://', '').replace('http://', '')
            contact_items.append(
                f"\\mbox{{\\hrefWithoutArrow{{{info.portfolio}}}{{{self.escape_latex(portfolio_display)}}}}}"
            )
        
        if info.linkedin:
            linkedin_url = info.linkedin if info.linkedin.startswith('http') else f"https://{info.linkedin}"
            linkedin_display = info.linkedin.replace('https://', '').replace('http://', '')
            contact_items.append(
                f"\\mbox{{\\hrefWithoutArrow{{{linkedin_url}}}{{{self.escape_latex(linkedin_display)}}}}}"
            )
        
        if info.github:
            github_url = info.github if info.github.startswith('http') else f"https://{info.github}"
            github_display = info.github.replace('https://', '').replace('http://', '')
            contact_items.append(
                f"\\mbox{{\\hrefWithoutArrow{{{github_url}}}{{{self.escape_latex(github_display)}}}}}"
            )
        
        # Join contact items with AND separator
        contact_separator = "%\n        \\kern 5.0 pt%\n        \\AND%\n        \\kern 5.0 pt%\n        "
        contact_line = contact_separator.join(contact_items) if contact_items else ""
        
        return f"""
    \\begin{{header}}
        \\fontsize{{25pt}}{{25pt}}\\selectfont {name}

        \\vspace{{5pt}}

        \\normalsize
        {contact_line}
    \\end{{header}}

    \\vspace{{5pt - 0.3cm}}
"""
    
    def _generate_education_section(self, education: List[Education]) -> str:
        """Generate education section"""
        if not education:
            return ""
        
        entries = []
        for edu in education:
            institution = self.escape_latex(edu.institution)
            degree = self.escape_latex(edu.degree)
            field = self.escape_latex(edu.field_of_study)
            
            degree_text = f"{degree}" if degree else ""
            if field:
                degree_text = f"{degree} in {field}" if degree else field
            
            date_range = ""
            if edu.start_date and edu.end_date:
                date_range = f"{edu.start_date} -- {edu.end_date}"
            elif edu.end_date:
                date_range = edu.end_date
            
            # Build highlights
            highlights = []
            if edu.gpa:
                # Infer the scale from the value (4.x, 5.x, or 10-point).
                scale = "10.0" if edu.gpa > 5 else ("5.0" if edu.gpa > 4 else "4.0")
                highlights.append(f"GPA: {edu.gpa}/{scale}")
            
            # Add coursework if available
            if hasattr(edu, 'coursework') and edu.coursework:
                coursework_str = ", ".join(edu.coursework[:5])  # Limit to 5 courses
                highlights.append(f"Coursework: {coursework_str}")
            
            highlights.extend(edu.achievements)
            
            highlights_tex = ""
            if highlights:
                items = "\n                ".join([f"\\item {self.escape_latex(h)}" for h in highlights])
                highlights_tex = f"""
        \\vspace{{0.10cm}}
        \\begin{{onecolentry}}
            \\begin{{highlights}}
                {items}
            \\end{{highlights}}
        \\end{{onecolentry}}"""
            
            entry = f"""
        \\begin{{twocolentry}}{{
            {date_range}
        }}
            \\textbf{{{institution}}}, {degree_text}
        \\end{{twocolentry}}{highlights_tex}"""
            entries.append(entry)
        
        entries_text = "\n".join(entries)
        
        return f"""
    \\section{{Education}}
{entries_text}
"""
    
    def _generate_experience_section(
        self, 
        experience: List[Experience],
        jd: Optional[JobDescription] = None,
        analysis: Optional[MatchAnalysis] = None
    ) -> str:
        """Generate work experience section with controlled AI enhancement"""
        if not experience:
            return ""
        
        logger.info(f"Generating experience section for {len(experience)} entries")
        entries = []
        
        for i, exp in enumerate(experience):
            title = self.escape_latex(exp.title)
            company = self.escape_latex(exp.company)
            location = self.escape_latex(exp.location)
            
            date_range = ""
            if exp.start_date:
                end = "present" if exp.is_current else (exp.end_date or "")
                date_range = f"{exp.start_date} -- {end}"
            
            company_line = f"{company}"
            if location:
                company_line = f"{company} -- {location}"
            
            # Build highlights from responsibilities - with controlled AI enhancement
            highlights_tex = ""
            if exp.responsibilities:
                enhanced_bullets = [
                    f"\\item {self.escape_latex(self._enhance(resp))}"
                    for resp in exp.responsibilities
                ]
                items = "\n                ".join(enhanced_bullets)
                highlights_tex = f"""
        \\vspace{{0.10cm}}
        \\begin{{onecolentry}}
            \\begin{{highlights}}
                {items}
            \\end{{highlights}}
        \\end{{onecolentry}}"""
            
            # Add spacing between entries
            spacing = "\\vspace{0.2cm}\n\n        " if i > 0 else ""
            
            entry = f"""{spacing}\\begin{{twocolentry}}{{
            {date_range}
        }}
            \\textbf{{{title}}}, {company_line}
        \\end{{twocolentry}}{highlights_tex}"""
            entries.append(entry)
        
        entries_text = "\n".join(entries)
        
        return f"""
    \\section{{Work Experience}}

        {entries_text}
"""
    
    def _generate_skills_section(
        self, 
        skills: Skills, 
        jd: Optional[JobDescription] = None,
        analysis: Optional[MatchAnalysis] = None
    ) -> str:
        """Generate skills section with intelligent categorization"""
        sections = []
        
        # Get all skills
        all_skills = skills.all_skills()
        
        # If we have JD analysis, prioritize matched skills
        if analysis and hasattr(analysis, 'matched_skills'):
            matched = set(analysis.matched_skills)
            # Reorder to put matched skills first within each category
            all_skills = sorted(all_skills, key=lambda x: x not in matched)
        
        # Languages/Programming
        if skills.languages:
            sections.append(f"\\textbf{{Languages:}} {self.escape_latex(', '.join(skills.languages))}")
        
        # Tools
        if skills.tools:
            sections.append(f"\\textbf{{Tools:}} {self.escape_latex(', '.join(skills.tools))}")
        
        # Frameworks
        if skills.frameworks:
            sections.append(f"\\textbf{{Frameworks:}} {self.escape_latex(', '.join(skills.frameworks))}")
        
        # Machine Learning & AI
        ml_keywords = ['machine learning', 'deep learning', 'ai', 'nlp', 'ml', 'generative', 'transformers', 'llm']
        ml_skills = [s for s in skills.technical if any(kw in s.lower() for kw in ml_keywords)]
        if ml_skills:
            sections.append(f"\\textbf{{Machine Learning \\& AI:}} {self.escape_latex(', '.join(ml_skills))}")
        
        # If no categorization worked, just list all
        if not sections and all_skills:
            sections.append(f"\\textbf{{Skills:}} {self.escape_latex(', '.join(all_skills))}")
        
        if not sections:
            return ""
        
        entries = "\n\n        \\vspace{0.1cm}\n\n        ".join([
            f"\\begin{{onecolentry}}\n            {s}\n        \\end{{onecolentry}}"
            for s in sections
        ])
        
        return f"""
    \\section{{Skills}}

        {entries}
"""
    
    def _generate_projects_section(
        self, 
        projects: List[Project],
        jd: Optional[JobDescription] = None,
        analysis: Optional[MatchAnalysis] = None
    ) -> str:
        """Generate projects section with controlled AI enhancement"""
        if not projects:
            return ""
        
        logger.info(f"Generating projects section for {len(projects)} projects")
        entries = []
        
        for i, proj in enumerate(projects):
            name = self.escape_latex(proj.name)
            
            url_part = ""
            if proj.url:
                url_display = proj.url.replace('https://', '').replace('http://', '')
                url_part = f"""\\href{{{proj.url}}}{{{url_display}}}"""
            
            # Build highlights - with controlled enhancement
            highlights = []
            
            # Use the batched-enhanced description if available, else original.
            if proj.description:
                highlights.append(self._enhance(proj.description))
            
            # Add other highlights as-is
            if proj.highlights:
                highlights.extend(proj.highlights)
            
            # Add tech stack
            if proj.technologies:
                tech_list = ', '.join(proj.technologies)
                highlights.append(f"\\textbf{{Tech Stack:}} {tech_list}")
            
            highlights_tex = ""
            if highlights:
                items = "\n                ".join([f"\\item {self.escape_latex(h)}" for h in highlights])
                highlights_tex = f"""
        \\vspace{{0.10cm}}
        \\begin{{onecolentry}}
            \\begin{{highlights}}
                {items}
            \\end{{highlights}}
        \\end{{onecolentry}}"""
            
            spacing = "\\vspace{0.2cm}\n\n        " if i > 0 else ""
            
            entry = f"""{spacing}\\begin{{twocolentry}}{{
            {url_part}
        }}
            \\textbf{{{name}}}
        \\end{{twocolentry}}{highlights_tex}"""
            entries.append(entry)
        
        entries_text = "\n".join(entries)
        
        return f"""
    \\section{{Projects}}

        {entries_text}
"""
    
    def _generate_certifications_section(self, certifications: List[str]) -> str:
        """Generate certifications section"""
        if not certifications:
            return ""
        
        items = "\n                ".join([f"\\item {self.escape_latex(cert)}" for cert in certifications])
        
        return f"""
    \\section{{Certifications}}

        \\begin{{onecolentry}}
            \\begin{{highlights}}
                {items}
            \\end{{highlights}}
        \\end{{onecolentry}}
"""
    
    def _generate_achievements_section(self, achievements: List[str]) -> str:
        """Generate achievements section"""
        if not achievements:
            return ""
        
        items = "\n                ".join([f"\\item {self.escape_latex(ach)}" for ach in achievements])
        
        return f"""
    \\section{{Achievements}}

        \\begin{{onecolentry}}
            \\begin{{highlights}}
                {items}
            \\end{{highlights}}
        \\end{{onecolentry}}
"""
    
    def _generate_footer(self) -> str:
        """Generate document footer"""
        return r"""
                    \end{document}
                    """
    
    def save_to_file(self, latex_code: str, output_path: str) -> str:
        """
        Save LaTeX code to a file.
        
        Args:
            latex_code: Generated LaTeX code
            output_path: Path to save the .tex file
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        
        # Ensure .tex extension
        if output_path.suffix != '.tex':
            output_path = output_path.with_suffix('.tex')
        
        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_code)
        
        logger.info(f"Saved LaTeX to: {output_path}")
        return str(output_path)