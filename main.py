import os
import base64
import json
import re
import logging
import io
import docx
from contextlib import asynccontextmanager

from google import genai
from google.genai import types, errors
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Form
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
from database import get_submissions_collection
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("resume_analyzer")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

HR_SECRET_KEY = os.getenv("HR_SECRET_KEY")

class DecisionRequest(BaseModel):
    status: str
    hr_remarks: str = ""

def verify_hr_key(x_hr_key: str = Header(None)):
    if not HR_SECRET_KEY:
        raise HTTPException(status_code=500, detail="HR_SECRET_KEY is not configured on the server.")
    if x_hr_key != HR_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid HR Credentials")
    return True

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-flash-latest"

# ---------------------------------------------------------------------------
# Allowed MIME types
# ---------------------------------------------------------------------------
ALLOWED_MIME_TYPES: dict[str, str] = {
    "application/pdf": "application/pdf",
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
}

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT = """
Extract all content from this resume. Return the following in plain text:
- Full name and contact details
- Education and academic background
- Technical skills and tools
- Projects and implementations (with descriptions if present)
- Work experience and internships
- Certifications, achievements, and extracurriculars
- Overall formatting and presentation quality observations
Return only the extracted content, nothing else.
""".strip()

ANALYSIS_PROMPT_TEMPLATE = """
Analyze the following resume content for an elite university internship focused on 
high-impact visionary entrepreneurship and technical innovation. 

YOUR GOAL: Identify "The Best of the Best." You are looking for the top 1% of talent. 
Be extremely critical, elitist, and rigorous. Do not give high scores for standard 
student resumes. Most candidates should score below 60.

Scoring Rigor:
- 0-40: Poor/Irrelevant
- 41-60: Standard student resume (Solid but common)
- 61-80: Exceptional student (High potential, likely to succeed)
- 81-100: ELITE (World-class potential, proven high-impact builder, first-principles thinker)

Weighted Criteria:
- Technical execution & product depth (35%): Did they build something real? Is it complex?
- Innovation & First-Principles Thinking (25%): Are they a visionary or just a follower?
- Competitive Achievement (20%): Tier-1 hackathons, Olympiads, prestigious internships.
- Entrepreneurial Hustle (15%): Startups, independent projects, high ownership roles.
- Leadership & Clarity (5%): Minimal weight, but must be professional.

Return your response ONLY as a valid JSON object with no extra text. Use this structure:

{{
  "overall_score": 88,
  "breakdown": {{
    "technical_skills": {{ "score": 32, "max": 35 }},
    "innovation": {{ "score": 22, "max": 25 }},
    "achievements": {{ "score": 18, "max": 20 }},
    "hustle": {{ "score": 13, "max": 15 }},
    "clarity_leadership": {{ "score": 3, "max": 5 }}
  }},
  "strengths": ["Critical Elite Strength 1", "..."],
  "weak_areas": ["Strict Observation 1", "..."],
  "selection_chances": "Highly Likely / Unlikely / Exceptional",
  "selection_reason": "One line elite justification",
  "recommended_status": "approved",
  "final_verdict": "3-4 lines of high-level, critical analysis of their potential for world-class impact."
}}

Decision Criteria for "recommended_status":
- "approved": ONLY if overall_score >= 85. This candidate represents the highest level of build-potential.
- "rejected": If overall_score < 85. 

Resume content:
{extracted_text}
""".strip()

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Resume Analyzer API starting up ✓")
    yield
    logger.info("Resume Analyzer API shutting down.")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Resume Analyzer",
    description="Analyzes resumes using Google Gemini and returns structured scoring JSON.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_mime(content_type: str) -> str:
    content_type = content_type.lower().strip()
    if content_type in ["application/pdf"]:
        return "application/pdf"
    if content_type in ["image/jpeg", "image/jpg"]:
        return "image/jpeg"
    if content_type in ["image/png"]:
        return "image/png"
    if content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if content_type in ["application/msword"]:
        # We handle .doc as best-effort text extraction via common libraries
        return "application/msword"
    
    raise HTTPException(
        status_code=415,
        detail=f"Unsupported file type: {content_type}. Please upload PDF, PNG, JPG, or DOCX."
    )


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts text from a .docx file using python-docx."""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = [para.text for para in doc.paragraphs]
        return "\n".join(full_text)
    except Exception as exc:
        logger.error("Failed to extract text from DOCX: %s", exc)
        return ""


def _extract_json(raw: str) -> dict:
    """
    Parse Gemini's text response as JSON.
    Tries direct parse, then strips markdown fences, then brute-force regex.
    """
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not parse Gemini response as JSON.\n"
        f"Raw output (first 500 chars):\n{raw[:500]}"
    )

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Resume Analyzer API is running."}


@app.post("/analyze", tags=["Analysis"])
async def analyze_resume(file: UploadFile = File(...)):
    """
    Accept a resume (PDF / jpg / jpeg / png), run the Gemini two-step pipeline,
    and return a structured JSON analysis.
    """
    # ── Validate MIME type ───────────────────────────────────────────────────
    content_type = (file.content_type or "").lower().strip()
    mime_type = _resolve_mime(content_type)   # raises 415 if invalid

    # ── Read file bytes ──────────────────────────────────────────────────────
    try:
        file_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(status_code=400, detail="Failed to read the uploaded file.")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.info(
        "Received '%s' (%s, %d bytes).",
        file.filename, mime_type, len(file_bytes),
    )

    # ── Base64 encode ────────────────────────────────────────────────────────
    encoded_data = base64.b64encode(file_bytes).decode("utf-8")

    # ── Gemini pipeline ──────────────────────────────────────────────────────
    try:
        # ── Step 1: OCR / Extraction ─────────────────────────────────────────
        if mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            logger.info("Step 1 – Extracting text from Word document locally …")
            extracted_text = _extract_text_from_docx(file_bytes)
            if not extracted_text:
                raise ValueError("Failed to extract any text from the Word document.")
        else:
            logger.info("Step 1 – Sending file to Gemini for OCR/extraction …")
            extraction_response = client.models.generate_content(
                model=MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(
                                data=base64.b64decode(encoded_data),
                                mime_type=mime_type,
                            ),
                            types.Part.from_text(text=EXTRACTION_PROMPT),
                        ],
                    )
                ],
            )
            extracted_text = extraction_response.text.strip()
            if not extracted_text:
                raise ValueError("Gemini returned empty text during the extraction step.")

        logger.info("Step 1 complete. Extracted %d characters.", len(extracted_text))

        # ── Step 2: Structured Analysis ──────────────────────────────────────
        logger.info("Step 2 – Sending extracted text for structured analysis …")

        analysis_prompt = ANALYSIS_PROMPT_TEMPLATE.format(extracted_text=extracted_text)

        analysis_response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=analysis_prompt)],
                )
            ],
        )

        raw_json = analysis_response.text.strip()
        logger.info("Step 2 complete. Parsing JSON …")

        result = _extract_json(raw_json)
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except ValueError as exc:
        logger.error("ValueError in pipeline: %s", exc)
        return JSONResponse(status_code=422, content={"error": str(exc)})
    except errors.APIError as exc:
        logger.error("Gemini API error: %s", exc)
        status_code = 500
        if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
            status_code = 429
        elif "403" in str(exc):
            status_code = 403
        
        return JSONResponse(
            status_code=status_code,
            content={"error": f"Gemini API error: {str(exc)}"}
        )
    except Exception as exc:
        logger.exception("Unexpected error during Gemini pipeline.")
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(exc)}"},
        )


@app.post("/submit", tags=["Student"])
async def submit_resume(
    student_name: str = Form(...),
    student_email: str = Form(...),
    phone: str = Form(...),
    college: str = Form(...),
    branch: str = Form(...),
    year_of_study: str = Form(...),
    file: UploadFile = File(...)
):
    """Student submits details and resume, runs OCR and Analysis."""
    content_type = (file.content_type or "").lower().strip()
    mime_type = _resolve_mime(content_type)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    encoded_data = base64.b64encode(file_bytes).decode("utf-8")

    try:
        if mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            logger.info("Extracting text from Word document locally …")
            extracted_text = _extract_text_from_docx(file_bytes)
            if not extracted_text:
                raise ValueError("Failed to extract any text from the Word document.")
        else:
            logger.info("Sending file to Gemini for OCR/extraction …")
            extraction_response = client.models.generate_content(
                model=MODEL,
                contents=[types.Content(role="user", parts=[
                    types.Part.from_bytes(data=base64.b64decode(encoded_data), mime_type=mime_type),
                    types.Part.from_text(text=EXTRACTION_PROMPT),
                ])]
            )
            extracted_text = extraction_response.text.strip()
            if not extracted_text:
                raise ValueError("Gemini returned empty text or failed to OCR.")

        logger.info("Step 1 complete. Extracted %d characters.", len(extracted_text))
        
        analysis_prompt = ANALYSIS_PROMPT_TEMPLATE.format(extracted_text=extracted_text)
        analysis_response = client.models.generate_content(
            model=MODEL,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=analysis_prompt)])]
        )
        result = _extract_json(analysis_response.text.strip())

        # AI Evaluation Automation
        ai_recommendation = result.get("recommended_status", "pending")
        if ai_recommendation not in ["approved", "rejected"]:
            ai_recommendation = "pending"
            
        ai_verdict = result.get("final_verdict", "No additional AI reasoning provided.")

        doc = {
            "student_name": student_name,
            "student_email": student_email,
            "phone": phone,
            "college": college,
            "branch": branch,
            "year_of_study": year_of_study,
            "resume_filename": file.filename,
            "ai_score": result.get("overall_score", 0),
            "ai_result": result,
            "status": ai_recommendation,
            "hr_remarks": f"AI Evaluation: {ai_verdict}",
            "submitted_at": datetime.utcnow(),
            "reviewed_at": datetime.utcnow() if ai_recommendation != "pending" else None
        }

        coll = get_submissions_collection()
        insert_res = coll.insert_one(doc)
        
        return {"submission_id": str(insert_res.inserted_id), "ai_result": result}
        
    except errors.APIError as exc:
        logger.error("Gemini API error: %s", exc)
        status_code = 500
        if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
            status_code = 429
        elif "403" in str(exc):
            status_code = 403
        raise HTTPException(status_code=status_code, detail=f"Gemini API error: {str(exc)}")
    except Exception as exc:
        logger.exception("Unexpected error during pipeline.")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(exc)}")


@app.get("/student/result/{submission_id}", tags=["Student"])
async def get_student_result(submission_id: str):
    """Retrieves student submission result."""
    try:
        obj_id = ObjectId(submission_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid submission ID format.")
    
    coll = get_submissions_collection()
    doc = coll.find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Submission not found.")
        
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/hr/submissions", tags=["HR"])
async def get_all_submissions(status: str = None, hr_auth: bool = Depends(verify_hr_key)):
    """HR Endpoint: get all submissions, optionally filtered by status."""
    coll = get_submissions_collection()
    query = {}
    if status:
        query["status"] = status
        
    docs = list(coll.find(query).sort("submitted_at", -1))
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@app.get("/hr/submission/{submission_id}", tags=["HR"])
async def get_hr_submission(submission_id: str, hr_auth: bool = Depends(verify_hr_key)):
    """HR Endpoint: get detail of one submission."""
    try:
        obj_id = ObjectId(submission_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid submission ID format.")
        
    coll = get_submissions_collection()
    doc = coll.find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Submission not found.")
        
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.patch("/hr/submission/{submission_id}/decision", tags=["HR"])
async def update_hr_decision(submission_id: str, decision: DecisionRequest, hr_auth: bool = Depends(verify_hr_key)):
    """HR Endpoint: update decision (approve/reject)."""
    try:
        obj_id = ObjectId(submission_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid submission ID format.")
        
    if decision.status not in ["approved", "rejected", "pending"]:
         raise HTTPException(status_code=400, detail="Invalid status value. Must be 'approved', 'rejected', or 'pending'.")

    coll = get_submissions_collection()
    update_data = {
        "status": decision.status,
        "hr_remarks": decision.hr_remarks,
        "reviewed_at": datetime.utcnow()
    }
    
    result = coll.update_one({"_id": obj_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found.")
        
    doc = coll.find_one({"_id": obj_id})
    doc["id"] = str(doc.pop("_id"))
    return doc
