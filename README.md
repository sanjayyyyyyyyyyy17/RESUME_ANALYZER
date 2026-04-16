# 🤖 AI Resume Analyzer

An AI-powered resume analysis API built with **FastAPI** and **Google Gemini (gemini-1.5-flash)**. Upload a resume (PDF or image) and get back a structured JSON score with strengths, weak areas, and a final verdict — tailored for university internship screening focused on entrepreneurship and innovation.

---

## ✨ Features

- Accepts **PDF, JPG, JPEG, PNG** resume uploads
- Two-step Gemini pipeline: **OCR extraction → structured analysis**
- Returns a JSON score breakdown across 6 categories
- Student-friendly, moderately lenient scoring
- Clear error responses for unsupported files or API issues

---

## 🔑 Getting a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your key — you'll need it in the next step

---

## ⚙️ Setup Instructions

### 1. Clone / navigate to the project

```bash
cd RESUME_ANALYSER
```

### 2. Create and activate a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your real key:

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## 🚀 Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at: **http://127.0.0.1:8000**

Interactive docs (Swagger UI): **http://127.0.0.1:8000/docs**

---

## 📡 API Endpoints

### `GET /`
Health check — returns `{"status": "ok"}`.

### `POST /analyze`
Upload a resume file and receive a structured analysis.

**Accepted file types:** `application/pdf`, `image/jpeg`, `image/png`

---

## 🧪 Sample cURL Command

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "accept: application/json" \
  -F "file=@/path/to/your/resume.pdf"
```

Replace `/path/to/your/resume.pdf` with the actual path to your file.

---

## 📤 Sample Response

```json
{
  "overall_score": 82,
  "breakdown": {
    "technical_skills": { "score": 26, "max": 30 },
    "projects":         { "score": 21, "max": 25 },
    "innovation":       { "score": 16, "max": 20 },
    "experience_academics": { "score": 9, "max": 10 },
    "resume_clarity":   { "score": 7,  "max": 10 },
    "leadership":       { "score": 3,  "max": 5  }
  },
  "strengths": [
    "Strong hands-on project portfolio",
    "Experience with modern ML frameworks",
    "Clear evidence of product thinking"
  ],
  "weak_areas": [
    "Limited leadership or team initiative examples",
    "Could highlight entrepreneurial projects more explicitly"
  ],
  "selection_chances": "High",
  "selection_reason": "Strong technical execution with demonstrated product-building ability.",
  "final_verdict": "This candidate shows real technical depth and a portfolio of shipped projects. With some emphasis on entrepreneurial framing, they would be an excellent fit for an innovation-focused internship."
}
```

---

## ❌ Error Response

```json
{
  "error": "Unsupported file type 'application/msword'. Accepted formats: PDF, JPG, JPEG, PNG."
}
```

---

## 📁 Project Structure

```
RESUME_ANALYSER/
├── main.py           # FastAPI application & Gemini pipeline
├── .env              # Your secret API key (never commit this)
├── .env.example      # Template for environment variables
├── requirements.txt  # Python dependencies
├── .gitignore        # Ignores .env and artifacts
└── README.md         # This file
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| AI model | Google Gemini 1.5 Flash |
| AI SDK | google-generativeai |
| File uploads | python-multipart |
| Env management | python-dotenv |
# RESUME_ANALYZER
