"""
LaTeX Resume Generator Service
Generates ATS-optimized LaTeX code from resume data using custom RenderCV template
"""

import sys
import re
from pathlib import Path
from typing import List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from app.models.resume import Resume, PersonalInfo, Education, Experience, Project, Skills
from app.models.job_description import JobDescription
from app.models.analysis import MatchAnalysis

logger = get_logger(__name__)


class LaTeXGenerator:
    """
    Generates professional LaTeX resume code optimized for ATS.
    Uses RenderCV-style template.
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
    
    def __init__(self):
        logger.info("Initializing LaTeXGenerator")
    
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
        
        # Build LaTeX sections
        header = self._generate_header(resume.personal_info)
        personal = self._generate_personal_section(resume.personal_info)
        education = self._generate_education_section(resume.education)
        experience = self._generate_experience_section(resume.experience)
        skills = self._generate_skills_section(resume.skills, jd, analysis)
        projects = self._generate_projects_section(resume.projects)
        certifications = self._generate_certifications_section(resume.certifications)
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
                highlights.append(f"GPA: {edu.gpa}/10.0")
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
    
    def _generate_experience_section(self, experience: List[Experience]) -> str:
        """Generate work experience section"""
        if not experience:
            return ""
        
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
            
            # Build highlights from responsibilities
            highlights_tex = ""
            if exp.responsibilities:
                items = "\n                ".join([f"\\item {self.escape_latex(r)}" for r in exp.responsibilities[:6]])
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
        """Generate skills section"""
        sections = []
        
        # Languages/Programming
        if skills.languages or skills.technical:
            langs = skills.languages + [s for s in skills.technical if any(
                kw in s.lower() for kw in ['python', 'java', 'sql', 'c++', 'javascript', 'r', 'scala']
            )]
            if langs:
                sections.append(f"\\textbf{{Languages:}} {self.escape_latex(', '.join(langs))}")
        
        # Tools
        if skills.tools:
            sections.append(f"\\textbf{{Tools:}} {self.escape_latex(', '.join(skills.tools))}")
        
        # Frameworks
        if skills.frameworks:
            sections.append(f"\\textbf{{Frameworks:}} {self.escape_latex(', '.join(skills.frameworks))}")
        
        # Technical/ML skills
        ml_skills = [s for s in skills.technical if any(
            kw in s.lower() for kw in ['machine learning', 'deep learning', 'ai', 'nlp', 'ml', 'data']
        )]
        if ml_skills:
            sections.append(f"\\textbf{{Machine Learning \\& AI:}} {self.escape_latex(', '.join(ml_skills))}")
        
        # If no categorization worked, just list all
        if not sections:
            all_skills = skills.all_skills()
            if all_skills:
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
    
    def _generate_projects_section(self, projects: List[Project]) -> str:
        """Generate projects section"""
        if not projects:
            return ""
        
        entries = []
        for i, proj in enumerate(projects[:4]):
            name = self.escape_latex(proj.name)
            
            url_part = ""
            if proj.url:
                url_display = proj.url.replace('https://', '').replace('http://', '')
                url_part = f"""\\href{{{proj.url}}}{{github.com/{url_display}}}"""
            
            # Build highlights
            highlights = proj.highlights or ([proj.description] if proj.description else [])
            if proj.technologies:
                highlights.append(f"\\textbf{{Tech Stack:}} {', '.join(proj.technologies)}")
            
            highlights_tex = ""
            if highlights:
                items = "\n                ".join([f"\\item {self.escape_latex(h)}" for h in highlights[:4]])
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
        
        items = "\n                ".join([f"\\item {self.escape_latex(cert)}" for cert in certifications[:6]])
        
        return f"""
    \\section{{Certifications}}

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
