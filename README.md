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

## 📂 Bulk Processing (existing resumes)

If you have a folder of resumes (e.g., 300+ files), use the bulk processor to ingest them into the system:

```bash
python bulk_processor.py --path "/path/to/resumes" --delay 2
```
This script will:
1. Walk through the directory.
2. Extract student identity automatically from each file.
3. Score candidates based on entrepreneurial and technical merit.
4. Populate the HR dashboard for easy segregation.

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
