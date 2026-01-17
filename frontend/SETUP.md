# Frontend Setup Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.local.example .env.local
   ```
   Then edit `.env.local` and set your backend API URL (default: `http://localhost:8000`)

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Make sure your backend is running

Before using the frontend, ensure your FastAPI backend is running:

```bash
# In the project root
python main.py
# or
uvicorn app.api.api:app --reload
```

The backend should be accessible at `http://localhost:8000`

## Features

- ✅ Landing page at `/`
- ✅ Dashboard at `/app`
- ✅ Resume parsing (file upload or text)
- ✅ Job description parsing
- ✅ Match analysis
- ✅ LaTeX generation
- ✅ Backend health monitoring

## Troubleshooting

### Backend connection issues

- Check that the backend is running on the port specified in `.env.local`
- Verify CORS is enabled in the backend (should be configured in `app/api/api.py`)
- Check browser console for errors

### File upload issues

- Ensure file is PDF or DOCX format
- File size must be less than 10MB
- Check browser console for detailed error messages
