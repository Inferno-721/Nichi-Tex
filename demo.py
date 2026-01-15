"""
Demo script for Clod_v2
Demonstrates the complete pipeline with sample data
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import Clod


# Sample resume text for demonstration
SAMPLE_RESUME = """
John Doe
john.doe@email.com | (555) 123-4567
linkedin.com/in/johndoe | github.com/johndoe

SUMMARY
Experienced Data Scientist with 3+ years of experience in machine learning, 
data analysis, and building predictive models. Proficient in Python, SQL, 
and various ML frameworks.

EDUCATION
Bachelor of Science in Computer Science
State University | 2020
GPA: 3.7

EXPERIENCE

Data Scientist
Tech Corp | Jan 2021 - Present
• Developed machine learning models for customer churn prediction, achieving 85% accuracy
• Built ETL pipelines using Python and SQL to process 1M+ daily records
• Created interactive dashboards using Tableau for executive reporting
• Collaborated with cross-functional teams to implement data-driven solutions

Data Analyst Intern
StartUp Inc | Jun 2020 - Dec 2020
• Analyzed user behavior data to identify growth opportunities
• Automated reporting processes using Python, saving 10 hours weekly
• Performed A/B testing analysis for product features

SKILLS
Technical: Python, SQL, R, Machine Learning, Deep Learning, TensorFlow, Pandas, NumPy, Scikit-learn
Tools: Tableau, Git, Docker, AWS, Jupyter
Soft Skills: Communication, Problem-solving, Teamwork

PROJECTS

Customer Segmentation Engine
• Built clustering model using K-means to segment 100K customers
• Technologies: Python, Scikit-learn, Pandas

Sentiment Analysis System
• Developed NLP model for social media sentiment analysis
• Achieved 90% accuracy using BERT-based approach
• Technologies: Python, PyTorch, Transformers

CERTIFICATIONS
AWS Certified Cloud Practitioner
Google Data Analytics Professional Certificate
"""

# Sample Job Description
SAMPLE_JD = """
Senior Data Scientist
TechCorp Inc. | San Francisco, CA

About the Role:
We are looking for a Senior Data Scientist to join our growing team. You will work on 
cutting-edge machine learning projects and help drive data-driven decision making.

Requirements:
- 5+ years of experience in data science or machine learning
- Strong proficiency in Python and SQL
- Experience with deep learning frameworks (TensorFlow, PyTorch)
- Knowledge of cloud platforms (AWS, GCP, Azure)
- Experience with big data technologies (Spark, Hadoop)
- Strong statistical analysis and A/B testing skills
- Excellent communication skills

Preferred Qualifications:
- Master's or PhD in Computer Science, Statistics, or related field
- Experience with Kubernetes and Docker
- Knowledge of NLP and computer vision
- Experience with real-time ML systems

Responsibilities:
- Develop and deploy machine learning models at scale
- Design and implement data pipelines
- Collaborate with product teams to identify opportunities
- Mentor junior team members
- Present findings to stakeholders
"""


def main():
    """Run the demo"""
    print("=" * 60)
    print("Clod_v2 - Resume Optimization Demo")
    print("=" * 60)
    
    # Initialize the system
    print("\n[1/5] Initializing Clod_v2...")
    clod = Clod()
    
    # Parse resume
    print("\n[2/5] Parsing resume...")
    resume = clod.parse_resume(text=SAMPLE_RESUME)
    print(f"  Name: {resume.personal_info.name}")
    print(f"  Email: {resume.personal_info.email}")
    print(f"  Education: {len(resume.education)} entries")
    print(f"  Experience: {len(resume.experience)} entries")
    print(f"  Skills: {len(resume.skills.all_skills())} total")
    
    # Parse job description
    print("\n[3/5] Parsing job description...")
    jd = clod.parse_job_description(SAMPLE_JD)
    print(f"  Title: {jd.title}")
    print(f"  Required Skills: {len(jd.required_skills)}")
    print(f"  Experience Required: {jd.required_experience_years} years")
    
    # Analyze match
    print("\n[4/5] Analyzing match...")
    analysis = clod.analyze(resume, jd)
    
    print("\n" + "=" * 40)
    print("ANALYSIS RESULTS")
    print("=" * 40)
    print(clod.get_summary(analysis))
    
    # Generate LaTeX
    print("\n[5/5] Generating LaTeX resume...")
    output_path = PROJECT_ROOT / "output" / "resume.tex"
    output_path.parent.mkdir(exist_ok=True)
    
    latex_code = clod.generate_latex(resume, jd, analysis, str(output_path))
    
    print(f"\nLaTeX saved to: {output_path}")
    print(f"LaTeX code length: {len(latex_code)} characters")
    
    # Print first 500 chars of LaTeX for preview
    print("\n" + "=" * 40)
    print("LATEX PREVIEW (first 500 chars)")
    print("=" * 40)
    print(latex_code[:500] + "...")
    
    print("\n" + "=" * 60)
    print("Demo complete! Copy the .tex file to Overleaf to compile.")
    print("=" * 60)


if __name__ == "__main__":
    main()
