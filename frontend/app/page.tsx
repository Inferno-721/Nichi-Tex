import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Target, Zap, Code } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Navbar */}
      <nav className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Nichi-Tex ⚔️
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/app">
              <Button variant="ghost">Dashboard</Button>
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </nav>
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16 md:py-24">
        <div className="text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Nichi-Tex ⚔️
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto">
              Intelligent Resume Optimization & LaTeX Generation System
            </p>
            <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
              Like a Nichirin blade that adapts its color based on the wielder's unique traits, 
              <strong> nichi-tex</strong> forges resumes customized to your individual strengths.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link href="/app">
              <Button size="lg" className="text-lg px-8 py-6">
                Get Started
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader>
              <FileText className="h-10 w-10 text-blue-600 dark:text-blue-400 mb-2" />
              <CardTitle>Resume Parsing</CardTitle>
              <CardDescription>
                Extract structured data from PDF and DOCX resumes
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Target className="h-10 w-10 text-purple-600 dark:text-purple-400 mb-2" />
              <CardTitle>Job Description Analysis</CardTitle>
              <CardDescription>
                Parse JD requirements, skills, and qualifications
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Zap className="h-10 w-10 text-yellow-600 dark:text-yellow-400 mb-2" />
              <CardTitle>NLP-Based Matching</CardTitle>
              <CardDescription>
                Semantic similarity analysis using sentence transformers
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Code className="h-10 w-10 text-green-600 dark:text-green-400 mb-2" />
              <CardTitle>LaTeX Generation</CardTitle>
              <CardDescription>
                Generate professional, ATS-friendly LaTeX resumes
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  );
}
