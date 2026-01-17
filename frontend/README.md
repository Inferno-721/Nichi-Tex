# nichi-tex Frontend

Production-ready Next.js 14 frontend for the nichi-tex resume optimization system.

## Tech Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **TailwindCSS**
- **shadcn/ui** components
- **lucide-react** icons
- **axios** for API calls
- **react-hook-form** + **zod** for form validation

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn

### Installation

1. Install dependencies:

```bash
npm install
```

2. Create `.env.local` file:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

3. Run the development server:

```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── app/
│   ├── app/          # Main dashboard page
│   ├── globals.css   # Global styles
│   ├── layout.tsx    # Root layout
│   └── page.tsx      # Landing page
├── components/
│   ├── ui/           # shadcn/ui components
│   ├── FileUpload.tsx
│   └── HealthBadge.tsx
├── lib/
│   ├── api.ts        # API client
│   └── utils.ts      # Utility functions
└── package.json
```

## Features

- ✅ Landing page with hero section
- ✅ Dashboard with resume and JD parsing
- ✅ File upload (PDF/DOCX) with drag & drop
- ✅ Resume text input alternative
- ✅ Job description parsing
- ✅ Match analysis with scores and recommendations
- ✅ LaTeX resume generation
- ✅ Backend health status indicator
- ✅ Responsive design
- ✅ Toast notifications
- ✅ Loading states

## API Integration

All API calls are defined in `lib/api.ts` and connect to the FastAPI backend:

- `GET /health` - Health check
- `POST /parse/resume` - Parse resume (text or file)
- `POST /parse/jd` - Parse job description
- `POST /analyze` - Analyze resume vs JD match
- `POST /generate` - Generate LaTeX resume

## Build for Production

```bash
npm run build
npm start
```

## License

MIT
