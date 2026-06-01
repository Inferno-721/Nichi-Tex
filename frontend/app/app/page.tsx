"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { HealthBadge } from "@/components/HealthBadge";
import { FileUpload } from "@/components/FileUpload";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useToast } from "@/components/ui/use-toast";
import {
  parseResumeFromText,
  parseResumeFromFile,
  parseJobDescription,
  analyzeMatch,
  generateLaTeX,
  type ParsedResumeData,
  type ParsedJDData,
  type AnalyzeResponse,
  type GenerateLaTeXResponse,
} from "@/lib/api";
import {
  Loader2,
  FileText,
  Briefcase,
  TrendingUp,
  Code,
  Copy,
  Download,
  User,
  GraduationCap,
  BriefcaseIcon,
  Award,
  FolderKanban,
} from "lucide-react";

export default function AppPage() {
  const { toast } = useToast();

  // State
  const [resumeText, setResumeText] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");

  const [parsedResume, setParsedResume] = useState<ParsedResumeData | null>(null);
  const [parsedJD, setParsedJD] = useState<ParsedJDData | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [latexCode, setLatexCode] = useState<string>("");

  const [loadingResume, setLoadingResume] = useState(false);
  const [loadingJD, setLoadingJD] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loadingLaTeX, setLoadingLaTeX] = useState(false);

  // Handlers
  const handleFileSelect = (file: File) => {
    setResumeFile(file);
    setResumeText(""); // Clear text if file is selected
  };

  const handleParseResume = async () => {
    if (!resumeText && !resumeFile) {
      toast({
        title: "Error",
        description: "Please provide resume text or upload a file",
        variant: "destructive",
      });
      return;
    }

    setLoadingResume(true);
    try {
      let response;
      if (resumeFile) {
        response = await parseResumeFromFile(resumeFile);
        // If file was used, we need to read it as text for analysis/generation
        // For now, we'll prompt user to also provide text, or we can reconstruct from parsed data
        // Store a reconstructed text version
        if (response.success && !resumeText) {
          // Reconstruct a text version from parsed data with section headers
          // Section headers are required for backend parser to properly detect sections
          const parts: string[] = [];

          // Personal info section
          parts.push(response.data.personal_info.name || '');
          parts.push(response.data.personal_info.email || '');
          parts.push(response.data.personal_info.phone || '');
          if (response.data.personal_info.linkedin) parts.push(response.data.personal_info.linkedin);
          if (response.data.personal_info.github) parts.push(response.data.personal_info.github);
          parts.push('');

          // Education section with header
          if (response.data.education.length > 0) {
            parts.push('Education');
            response.data.education.forEach(e => {
              parts.push(`${e.institution}`);
              parts.push(`${e.degree}${e.gpa ? ` - GPA: ${e.gpa}` : ''}`);
              parts.push('');
            });
          }

          // Experience section with header
          if (response.data.experience.length > 0) {
            parts.push('Experience');
            response.data.experience.forEach(e => {
              parts.push(`${e.title}`);
              parts.push(`${e.company}`);
              e.responsibilities.forEach(r => parts.push(`• ${r}`));
              parts.push('');
            });
          }

          // Skills section with header
          if (response.data.skills.length > 0) {
            parts.push('Skills');
            parts.push(response.data.skills.join(', '));
            parts.push('');
          }

          // Projects section with header
          if (response.data.projects.length > 0) {
            parts.push('Projects');
            response.data.projects.forEach(p => parts.push(p));
            parts.push('');
          }

          // Certifications section with header
          if (response.data.certifications.length > 0) {
            parts.push('Certifications');
            response.data.certifications.forEach(c => parts.push(`• ${c}`));
            parts.push('');
          }

          setResumeText(parts.join('\n'));
        }
      } else {
        response = await parseResumeFromText(resumeText);
      }

      if (response.success) {
        setParsedResume(response.data);
        toast({
          title: "Success",
          description: "Resume parsed successfully",
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || error.message || "Failed to parse resume",
        variant: "destructive",
      });
    } finally {
      setLoadingResume(false);
    }
  };

  const handleParseJD = async () => {
    if (!jdText.trim()) {
      toast({
        title: "Error",
        description: "Please enter job description text",
        variant: "destructive",
      });
      return;
    }

    setLoadingJD(true);
    try {
      const response = await parseJobDescription(jdText);
      if (response.success) {
        setParsedJD(response.data);
        toast({
          title: "Success",
          description: "Job description parsed successfully",
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || error.message || "Failed to parse job description",
        variant: "destructive",
      });
    } finally {
      setLoadingJD(false);
    }
  };

  const handleAnalyze = async () => {
    if (!parsedResume) {
      toast({
        title: "Error",
        description: "Please parse resume first",
        variant: "destructive",
      });
      return;
    }
    if (!parsedJD) {
      toast({
        title: "Error",
        description: "Please parse job description first",
        variant: "destructive",
      });
      return;
    }
    if (!resumeText.trim() && !resumeFile) {
      toast({
        title: "Error",
        description: "Resume text is required for analysis",
        variant: "destructive",
      });
      return;
    }

    setLoadingAnalysis(true);
    try {
      // Use the resume text (should be set after parsing)
      const resumeTextForAnalysis = resumeText || "";

      const response = await analyzeMatch({
        resume_text: resumeTextForAnalysis,
        jd_text: jdText,
      });

      if (response.success) {
        setAnalysis(response);
        toast({
          title: "Success",
          description: "Analysis completed successfully",
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || error.message || "Failed to analyze",
        variant: "destructive",
      });
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const handleGenerateLaTeX = async () => {
    if (!parsedResume) {
      toast({
        title: "Error",
        description: "Please parse resume first",
        variant: "destructive",
      });
      return;
    }
    if (!parsedJD) {
      toast({
        title: "Error",
        description: "Please parse job description first",
        variant: "destructive",
      });
      return;
    }
    if (!resumeText.trim() && !resumeFile) {
      toast({
        title: "Error",
        description: "Resume text is required for LaTeX generation",
        variant: "destructive",
      });
      return;
    }

    setLoadingLaTeX(true);
    try {
      // Use the resume text (should be set after parsing)
      const resumeTextForGeneration = resumeText || "";

      const response = await generateLaTeX({
        resume_text: resumeTextForGeneration,
        jd_text: jdText,
        output_format: "text",
      });

      if (response.success) {
        setLatexCode(response.latex_code);
        toast({
          title: "Success",
          description: "LaTeX resume generated successfully",
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || error.message || "Failed to generate LaTeX",
        variant: "destructive",
      });
    } finally {
      setLoadingLaTeX(false);
    }
  };

  const handleCopyLaTeX = () => {
    navigator.clipboard.writeText(latexCode);
    toast({
      title: "Copied",
      description: "LaTeX code copied to clipboard",
    });
  };

  const handleDownloadLaTeX = () => {
    const blob = new Blob([latexCode], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resume.tex";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      title: "Downloaded",
      description: "LaTeX file downloaded",
    });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <nav className="border-b bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            nichi-tex ⚔️
          </Link>
          <div className="flex items-center gap-4">
            <HealthBadge />
            <ThemeToggle />
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Inputs */}
          <div className="space-y-6">
            {/* Resume Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Resume
                </CardTitle>
                <CardDescription>
                  Upload a resume file or paste resume text
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <FileUpload onFileSelect={handleFileSelect} />
                <div className="text-center text-sm text-muted-foreground">OR</div>
                <div className="space-y-2">
                  <Label htmlFor="resume-text">Resume Text</Label>
                  <Textarea
                    id="resume-text"
                    placeholder="Paste your resume text here..."
                    value={resumeText}
                    onChange={(e) => {
                      setResumeText(e.target.value);
                      setResumeFile(null); // Clear file if text is entered
                    }}
                    rows={8}
                    disabled={!!resumeFile}
                  />
                </div>
                <Button
                  onClick={handleParseResume}
                  disabled={loadingResume || (!resumeText && !resumeFile)}
                  className="w-full"
                >
                  {loadingResume ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Parsing...
                    </>
                  ) : (
                    "Parse Resume"
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Job Description Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Briefcase className="h-5 w-5" />
                  Job Description
                </CardTitle>
                <CardDescription>
                  Paste the job description text
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="jd-text">Job Description Text</Label>
                  <Textarea
                    id="jd-text"
                    placeholder="Paste job description here..."
                    value={jdText}
                    onChange={(e) => setJdText(e.target.value)}
                    rows={8}
                  />
                </div>
                <Button
                  onClick={handleParseJD}
                  disabled={loadingJD || !jdText.trim()}
                  className="w-full"
                >
                  {loadingJD ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Parsing...
                    </>
                  ) : (
                    "Parse JD"
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="space-y-2">
              <Button
                onClick={handleAnalyze}
                disabled={loadingAnalysis || !parsedResume || !parsedJD || !resumeText.trim()}
                className="w-full"
                size="lg"
              >
                {loadingAnalysis ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Analyze Match
                  </>
                )}
              </Button>
              <Button
                onClick={handleGenerateLaTeX}
                disabled={loadingLaTeX || !parsedResume || !parsedJD || !resumeText.trim()}
                className="w-full"
                size="lg"
                variant="secondary"
              >
                {loadingLaTeX ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Code className="mr-2 h-4 w-4" />
                    Generate LaTeX Resume
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Right Column - Results */}
          <div>
            <Tabs defaultValue="resume" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="resume">Resume</TabsTrigger>
                <TabsTrigger value="jd">JD</TabsTrigger>
                <TabsTrigger value="analysis">Analysis</TabsTrigger>
                <TabsTrigger value="latex">LaTeX</TabsTrigger>
              </TabsList>

              {/* Parsed Resume Tab */}
              <TabsContent value="resume" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Parsed Resume</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {parsedResume ? (
                      <div className="space-y-6">
                        {/* Personal Info */}
                        <div>
                          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                            <User className="h-5 w-5" />
                            Personal Information
                          </h3>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="font-medium">Name:</span> {parsedResume.personal_info.name}
                            </div>
                            <div>
                              <span className="font-medium">Email:</span> {parsedResume.personal_info.email}
                            </div>
                            <div>
                              <span className="font-medium">Phone:</span> {parsedResume.personal_info.phone}
                            </div>
                            {parsedResume.personal_info.linkedin && (
                              <div>
                                <span className="font-medium">LinkedIn:</span> {parsedResume.personal_info.linkedin}
                              </div>
                            )}
                            {parsedResume.personal_info.github && (
                              <div>
                                <span className="font-medium">GitHub:</span> {parsedResume.personal_info.github}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Skills */}
                        {parsedResume.skills.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3">Skills</h3>
                            <div className="flex flex-wrap gap-2">
                              {parsedResume.skills.map((skill, idx) => (
                                <Badge key={idx} variant="secondary">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Education */}
                        {parsedResume.education.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                              <GraduationCap className="h-5 w-5" />
                              Education
                            </h3>
                            <div className="space-y-3">
                              {parsedResume.education.map((edu, idx) => (
                                <Card key={idx}>
                                  <CardContent className="pt-4">
                                    <div className="font-medium">{edu.degree}</div>
                                    <div className="text-sm text-muted-foreground">{edu.institution}</div>
                                    {edu.gpa && <div className="text-sm">GPA: {edu.gpa}</div>}
                                  </CardContent>
                                </Card>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Experience */}
                        {parsedResume.experience.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                              <BriefcaseIcon className="h-5 w-5" />
                              Experience
                            </h3>
                            <div className="space-y-3">
                              {parsedResume.experience.map((exp, idx) => (
                                <Card key={idx}>
                                  <CardContent className="pt-4">
                                    <div className="font-medium">{exp.title}</div>
                                    <div className="text-sm text-muted-foreground mb-2">{exp.company}</div>
                                    <ul className="text-sm space-y-1 list-disc list-inside">
                                      {exp.responsibilities.map((resp, rIdx) => (
                                        <li key={rIdx}>{resp}</li>
                                      ))}
                                    </ul>
                                  </CardContent>
                                </Card>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Projects */}
                        {parsedResume.projects.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                              <FolderKanban className="h-5 w-5" />
                              Projects
                            </h3>
                            <div className="flex flex-wrap gap-2">
                              {parsedResume.projects.map((project, idx) => (
                                <Badge key={idx} variant="outline">
                                  {project}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Certifications */}
                        {parsedResume.certifications.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                              <Award className="h-5 w-5" />
                              Certifications
                            </h3>
                            <div className="flex flex-wrap gap-2">
                              {parsedResume.certifications.map((cert, idx) => (
                                <Badge key={idx} variant="outline">
                                  {cert}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        Parse a resume to see results here
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Parsed JD Tab */}
              <TabsContent value="jd" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Parsed Job Description</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {parsedJD ? (
                      <div className="space-y-6">
                        <div>
                          <h3 className="text-lg font-semibold mb-2">{parsedJD.title}</h3>
                          <p className="text-muted-foreground">{parsedJD.company}</p>
                        </div>

                        <div>
                          <h3 className="text-lg font-semibold mb-3">Required Experience</h3>
                          <Badge variant="secondary">
                            {parsedJD.required_experience_years} years
                          </Badge>
                        </div>

                        {parsedJD.required_skills.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3">Required Skills</h3>
                            <div className="flex flex-wrap gap-2">
                              {parsedJD.required_skills.map((skill, idx) => (
                                <Badge key={idx} variant="default">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {parsedJD.preferred_skills.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3">Preferred Skills</h3>
                            <div className="flex flex-wrap gap-2">
                              {parsedJD.preferred_skills.map((skill, idx) => (
                                <Badge key={idx} variant="secondary">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {parsedJD.keywords.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3">Keywords</h3>
                            <div className="flex flex-wrap gap-2">
                              {parsedJD.keywords.map((keyword, idx) => (
                                <Badge key={idx} variant="outline">
                                  {keyword}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        Parse a job description to see results here
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Analysis Tab */}
              <TabsContent value="analysis" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Match Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysis ? (
                      <div className="space-y-6">
                        {/* Scores */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <Card>
                            <CardContent className="pt-6">
                              <div className="text-2xl font-bold text-primary">
                                {analysis.scores.overall}%
                              </div>
                              <div className="text-sm text-muted-foreground">Overall</div>
                            </CardContent>
                          </Card>
                          <Card>
                            <CardContent className="pt-6">
                              <div className="text-2xl font-bold">
                                {analysis.scores.skills}%
                              </div>
                              <div className="text-sm text-muted-foreground">Skills</div>
                            </CardContent>
                          </Card>
                          <Card>
                            <CardContent className="pt-6">
                              <div className="text-2xl font-bold">
                                {analysis.scores.experience}%
                              </div>
                              <div className="text-sm text-muted-foreground">Experience</div>
                            </CardContent>
                          </Card>
                          <Card>
                            <CardContent className="pt-6">
                              <div className="text-2xl font-bold">
                                {analysis.scores.education}%
                              </div>
                              <div className="text-sm text-muted-foreground">Education</div>
                            </CardContent>
                          </Card>
                        </div>

                        {/* Summary */}
                        {analysis.summary && (
                          <Card className="bg-primary/5 border-primary/20">
                            <CardContent className="pt-6">
                              <h3 className="font-semibold mb-2">Summary</h3>
                              <p className="text-sm">{analysis.summary}</p>
                            </CardContent>
                          </Card>
                        )}

                        {/* Matched Skills */}
                        {analysis.matched_skills.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3">Matched Skills</h3>
                            <div className="flex flex-wrap gap-2">
                              {analysis.matched_skills.map((skill, idx) => (
                                <Badge key={idx} variant="success">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Missing Skills */}
                        {analysis.missing_skills.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3">Missing Skills</h3>
                            <div className="flex flex-wrap gap-2">
                              {analysis.missing_skills.map((skill, idx) => (
                                <Badge key={idx} variant="destructive">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Recommendations */}
                        {analysis.recommendations.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold mb-3">Recommendations</h3>
                            <div className="space-y-3">
                              {analysis.recommendations.map((rec, idx) => (
                                <Card key={idx}>
                                  <CardContent className="pt-4">
                                    <div className="flex items-start justify-between mb-2">
                                      <div className="font-medium">{rec.title}</div>
                                      <Badge
                                        variant={
                                          rec.priority === "high"
                                            ? "destructive"
                                            : rec.priority === "medium"
                                              ? "warning"
                                              : "secondary"
                                        }
                                      >
                                        {rec.priority}
                                      </Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                      {rec.description}
                                    </p>
                                  </CardContent>
                                </Card>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        Run analysis to see results here
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* LaTeX Tab */}
              <TabsContent value="latex" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>LaTeX Output</span>
                      {latexCode && (
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleCopyLaTeX}
                          >
                            <Copy className="h-4 w-4 mr-2" />
                            Copy
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleDownloadLaTeX}
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        </div>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {latexCode ? (
                      <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-xs font-mono">
                        <code>{latexCode}</code>
                      </pre>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        Generate LaTeX resume to see output here
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}
