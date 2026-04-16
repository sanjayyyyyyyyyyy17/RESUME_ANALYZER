# 🤖 AI Resume Platform

A full-stack AI resume analysis platform built with **FastAPI**, **Dash**, and **Google Gemini (gemini-flash-latest)**. It automates the evaluation of resumes, extracts student identity data, and provides an HR dashboard for candidate segregation and decision-making.

---

## ✨ Features

- **Multi-modal Analysis**: Process **PDF, DOCX, JPG, PNG** resumes.
- **Auto Identity Extraction**: Gemini automatically extracts student **Name, Email, College, and Phone** from the resume.
- **Two-step Gemini Pipeline**: OCR extraction followed by structured innovation-focused scoring.
- **HR Dashboard**: A Dash-based interface to filter, review, and approve/reject candidates.
- **Bulk Processor**: A CLI utility to process hundreds of existing resumes from a directory.
- **MongoDB Persistence**: All submissions and AI results are stored for tracking.

---

## 🔑 Getting Started

### 1. Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create and copy your API Key.

### 2. Setup
```bash
git clone <repo-url>
cd RESUME_ANALYSER

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Running the App
The platform consists of a backend and a frontend:

**Backend (API):**
```bash
uvicorn main:app --reload
```
*API docs available at `http://127.0.0.1:8000/docs`*

**Frontend (Dashboard):**
```bash
python frontend.py
```
*Portals available at `http://127.0.0.1:8050`*

---

## 📂 Bulk Processing (Folder Analysis)

The system supports analyzing resumes in bulk from a local directory. This is ideal if you have hundreds of resumes to process at once.

```bash
# Run the bulk processor on a folder
python bulk_processor.py --path "/path/to/resumes/folder" --delay 2
```

**What this does:**
1. **Scans the directory** for PDF, DOCX, and image files.
2. **Auto-extracts identity** (Name, Email, etc.) using AI OCR.
3. **Applies high-rigor scoring** based on the same criteria as the web portal.
4. **Saves results to MongoDB**, making them immediately available in the HR Dashboard.


---

## 📡 Portals

- **Student Portal (`/`)**: Upload resume and fill personal details.
- **Check Result (`/student-result`)**: Check AI decision using Submission ID.
- **HR Dashboard (`/hr`)**: View all candidates, filter by status, and override AI decisions.

---

## 🛠 Tech Stack

- **AI Model**: Google Gemini 1.5 Flash
- **Backend Framework**: FastAPI
- **Database**: MongoDB (pymongo)
- **Frontend / HR Dashboard**: Dash (Plotly), Dash Bootstrap Components
- **OCR & Extraction**: google-genai, python-docx
