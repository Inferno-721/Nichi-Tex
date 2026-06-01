import axios from 'axios';

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health Check
export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
}

// Parse Resume
export interface PersonalInfo {
  name: string;
  email: string;
  phone: string;
  linkedin: string;
  github: string;
}

export interface Education {
  institution: string;
  degree: string;
  gpa: string | null;
}

export interface Experience {
  title: string;
  company: string;
  responsibilities: string[];
}

export interface ParsedResumeData {
  personal_info: PersonalInfo;
  education: Education[];
  experience: Experience[];
  skills: string[];
  projects: string[];
  certifications: string[];
}

export interface ParseResumeResponse {
  success: boolean;
  data: ParsedResumeData;
}

export async function parseResumeFromText(text: string): Promise<ParseResumeResponse> {
  const formData = new FormData();
  formData.append('text', text);
  
  const response = await api.post<ParseResumeResponse>('/parse/resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function parseResumeFromFile(file: File): Promise<ParseResumeResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<ParseResumeResponse>('/parse/resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

// Parse Job Description
export interface ParsedJDData {
  title: string;
  company: string;
  required_skills: string[];
  preferred_skills: string[];
  required_experience_years: number;
  keywords: string[];
}

export interface ParseJDResponse {
  success: boolean;
  data: ParsedJDData;
}

export async function parseJobDescription(text: string): Promise<ParseJDResponse> {
  const params = new URLSearchParams();
  params.append('text', text);
  
  const response = await api.post<ParseJDResponse>('/parse/jd', params.toString(), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
}

// Analyze
export interface AnalysisScores {
  overall: number;
  skills: number;
  experience: number;
  education: number;
}

export interface Recommendation {
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
}

// AI-powered enhanced feedback (present when a valid GOOGLE_API_KEY is configured).
// All fields are optional because the backend omits empty sections.
export interface EnhancedFeedback {
  flaws?: string;
  impact_rewrite?: string;
  ats_suggestions?: string;
  professional_summary?: string;
  experience_upgrade?: string;
  format_recommendations?: string;
  tailored_suggestions?: string;
  cover_letter?: string;
}

export interface AnalyzeResponse {
  success: boolean;
  scores: AnalysisScores;
  matched_skills: string[];
  missing_skills: string[];
  recommendations: Recommendation[];
  summary: string;
  enhanced_feedback?: EnhancedFeedback;
}

export interface AnalyzeRequest {
  resume_text: string;
  jd_text: string;
}

export async function analyzeMatch(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await api.post<AnalyzeResponse>('/analyze', request);
  return response.data;
}

// Generate LaTeX
export interface GenerateLaTeXResponse {
  success: boolean;
  latex_code: string;
  match_score: number;
  missing_skills: string[];
}

export interface GenerateLaTeXRequest {
  resume_text: string;
  jd_text: string;
  output_format?: string;
}

export async function generateLaTeX(request: GenerateLaTeXRequest): Promise<GenerateLaTeXResponse> {
  const params = new URLSearchParams();
  params.append('resume_text', request.resume_text);
  params.append('jd_text', request.jd_text);
  params.append('output_format', request.output_format || 'text');
  
  const response = await api.post<GenerateLaTeXResponse>('/generate', params.toString(), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
}
