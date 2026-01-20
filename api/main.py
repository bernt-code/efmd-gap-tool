#!/usr/bin/env python3
"""
EFMD CV Collection API
======================
FastAPI backend for EFMD Programme Accreditation data collection.

Three endpoints for CV upload:
- POST /upload/faculty/{institution_id}
- POST /upload/student/{programme_id}  
- POST /upload/alumni/{programme_id}

Plus search/selection endpoints:
- GET /faculty/{institution_id}/top - Get top 25 faculty for submission
- GET /alumni/{programme_id}/top - Get top 30 alumni for submission
- GET /programme/{id}/status - Collection status
- GET /programme/{id}/gap-report - Gap analysis
- GET /programme/{id}/improvement-report - Improvement plan
"""

import os
import json
import tempfile
from datetime import datetime
from typing import Optional, Literal

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# External services
import anthropic
import google.generativeai as genai
from supabase import create_client, Client

# PDF/DOCX extraction
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# ============================================================
# CONFIGURATION
# ============================================================

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://bkhvztyvfkqzqqtoxxxi.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="EFMD CV Collection API",
    description="Collect and analyze CVs for EFMD Programme Accreditation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# EXTRACTION PROMPTS
# ============================================================

FACULTY_PROMPT = """Extract from this faculty CV for EFMD accreditation. Return JSON only:

{
    "full_name": "string",
    "email": "string or null",
    "current_title": "Professor/Associate Professor/Assistant Professor/Lecturer/etc",
    "department": "string or null",
    "employment_type": "full-time/part-time/adjunct/visiting",
    "fte_percentage": "number 0-100",
    "highest_degree": "PhD/DBA/MBA/MSc/etc",
    "degree_field": "string",
    "degree_institution": "string",
    "degree_country": "string",
    "degree_year": "number",
    "publications_5yr_total": "number",
    "publications_peer_reviewed": "number",
    "research_areas": ["list"],
    "international_experience_years": "number",
    "worked_abroad_countries": ["list"],
    "industry_experience_years": "number",
    "consulting_active": "boolean",
    "board_memberships": ["list"],
    "ers_research": "boolean - ethics/sustainability research",
    "ers_teaching": "boolean - teaches ethics/sustainability",
    "languages": [{"language": "string", "proficiency": "native/fluent/professional/basic"}],
    "cv_summary": "2 sentence summary highlighting EFMD strengths"
}"""

STUDENT_PROMPT = """Extract from this student CV for EFMD accreditation. Return JSON only:

{
    "full_name": "string",
    "email": "string or null",
    "nationality": "string",
    "gender": "male/female/other/null",
    "age": "number or null",
    "prior_degree": "Bachelor/Master/etc",
    "prior_degree_field": "string",
    "prior_institution": "string",
    "prior_institution_country": "string",
    "work_experience_years": "number",
    "has_management_experience": "boolean",
    "has_international_experience": "boolean",
    "skills": ["list"],
    "languages": [{"language": "string", "proficiency": "native/fluent/professional/basic"}],
    "cv_summary": "1 sentence summary"
}"""

ALUMNI_PROMPT = """Extract from this alumni CV for EFMD accreditation. Return JSON only:

{
    "full_name": "string",
    "email": "string or null",
    "linkedin_url": "string or null",
    "graduation_year": "number",
    "is_employed": "boolean",
    "months_to_first_job": "number - months between graduation and first job",
    "current_employer": "string",
    "current_job_title": "string",
    "current_industry": "string",
    "current_country": "string",
    "seniority_level": "entry/mid/senior/executive",
    "is_fortune_500": "boolean",
    "is_big_4_mbb": "boolean - Deloitte/PwC/EY/KPMG/McKinsey/BCG/Bain",
    "is_multinational": "boolean",
    "working_abroad": "boolean - working outside home country",
    "career_progression": [{"employer": "string", "title": "string", "year": "number"}],
    "cv_summary": "1 sentence highlighting career success"
}"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from PDF or DOCX file."""
    content = file.file.read()
    return extract_text_from_bytes(content, file.filename)


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    """Extract text from file bytes."""
    filename = filename.lower()
    
    if filename.endswith('.pdf') and HAS_PYPDF:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            
            reader = pypdf.PdfReader(tmp.name)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            os.unlink(tmp.name)
            return text
    
    elif filename.endswith('.docx') and HAS_DOCX:
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            
            doc = Document(tmp.name)
            text = "\n".join([para.text for para in doc.paragraphs])
            
            os.unlink(tmp.name)
            return text
    
    elif filename.endswith('.txt'):
        return content.decode('utf-8')
    
    else:
        # Try to decode as text
        try:
            return content.decode('utf-8')
        except:
            raise HTTPException(400, "Unsupported file format. Use PDF, DOCX, or TXT.")


def parse_cv_with_claude(cv_text: str, prompt: str) -> dict:
    """Parse CV using Claude with better error handling."""
    response_text = ""
    try:
        message = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\n---\nCV TEXT:\n{cv_text[:15000]}"
            }]
        )
        
        response_text = message.content[0].text.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Handle empty response
        if not response_text:
            print("Warning: Claude returned empty response")
            return {"error": "Empty response from Claude"}
        
        return json.loads(response_text)
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response was: {response_text[:500] if response_text else 'empty'}")
        return {"error": f"Failed to parse Claude response: {str(e)}"}
    except Exception as e:
        print(f"Claude API error: {e}")
        return {"error": f"Claude API error: {str(e)}"}


def generate_embedding(text: str) -> list[float]:
    """Generate embedding using Gemini."""
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text[:8000],
        task_type="semantic_similarity"
    )
    return result['embedding']


def score_faculty(data: dict, institution_country: str = None) -> tuple[int, bool, list, list]:
    """Score faculty CV. Returns (score, recommend, reasons, risks)."""
    score = 0
    reasons = []
    risks = []
    
    # PhD (+20)
    degree = (data.get('highest_degree') or '').upper()
    if any(d in degree for d in ['PHD', 'DBA', 'DPHIL', 'DOCTOR']):
        score += 20
        reasons.append('Doctoral degree')
    else:
        risks.append('No doctoral degree')
    
    # Publications (+15 max)
    pubs = data.get('publications_5yr_total') or 0
    if pubs >= 5:
        score += 15
        reasons.append(f'{pubs} publications')
    elif pubs >= 2:
        score += 8
    
    # Peer reviewed (+10)
    peer = data.get('publications_peer_reviewed') or 0
    if peer >= 3:
        score += 10
        reasons.append('Strong peer-reviewed output')
    elif peer >= 1:
        score += 5
    
    # International (+15 max)
    intl_years = data.get('international_experience_years') or 0
    if intl_years >= 2:
        score += 10
        reasons.append('International experience')
    
    abroad = data.get('worked_abroad_countries') or []
    if len(abroad) >= 1:
        score += 5
    else:
        risks.append('No international exposure')
    
    # Industry (+10 max)
    industry = data.get('industry_experience_years') or 0
    if industry >= 3:
        score += 8
        reasons.append(f'{industry}yr industry experience')
    
    if data.get('consulting_active'):
        score += 4
        reasons.append('Active consulting')
    
    # ERS (+5)
    if data.get('ers_research') or data.get('ers_teaching'):
        score += 5
        reasons.append('ERS focus')
    
    recommend = score >= 45 or (score >= 30 and 'Doctoral' in str(reasons))
    
    return min(100, score), recommend, reasons, risks


def score_student(data: dict, institution_country: str = None) -> tuple[int, bool, list, list]:
    """Score student CV."""
    score = 0
    reasons = []
    risks = []
    
    # International (+20)
    nationality = data.get('nationality') or ''
    if nationality and institution_country and nationality.lower() != institution_country.lower():
        score += 20
        reasons.append(f'International ({nationality})')
    else:
        risks.append('Domestic student')
    
    # Work experience (+20 max)
    work = data.get('work_experience_years') or 0
    if work >= 5:
        score += 20
        reasons.append(f'{work}yr work experience')
    elif work >= 3:
        score += 15
    elif work >= 1:
        score += 8
    else:
        risks.append('No work experience')
    
    if data.get('has_management_experience'):
        score += 5
        reasons.append('Management experience')
    
    # Languages (+10)
    langs = data.get('languages') or []
    if len(langs) >= 3:
        score += 10
        reasons.append(f'{len(langs)} languages')
    elif len(langs) >= 2:
        score += 5
    
    recommend = score >= 35
    return min(100, score), recommend, reasons, risks


def score_alumni(data: dict) -> tuple[int, bool, list, list]:
    """Score alumni CV - focus on employment outcomes."""
    score = 0
    reasons = []
    risks = []
    
    # Employed (+15)
    if data.get('is_employed'):
        score += 15
        
        # Speed to employment (+15)
        months = data.get('months_to_first_job')
        if months is not None:
            if months <= 3:
                score += 15
                reasons.append('Employed within 3 months')
            elif months <= 6:
                score += 10
                reasons.append('Employed within 6 months')
            else:
                risks.append(f'{months} months to employment')
    else:
        risks.append('Unemployed')
        return 0, False, reasons, risks
    
    # Employer prestige (+20 max)
    if data.get('is_big_4_mbb'):
        score += 20
        reasons.append('Top-tier employer (Big4/MBB)')
    elif data.get('is_fortune_500'):
        score += 15
        reasons.append('Fortune 500')
    elif data.get('is_multinational'):
        score += 10
        reasons.append('Multinational')
    
    employer = data.get('current_employer')
    if employer:
        reasons.append(f'At {employer}')
    
    # Seniority (+15 max)
    level = (data.get('seniority_level') or '').lower()
    if level == 'executive':
        score += 15
        reasons.append('Executive level')
    elif level == 'senior':
        score += 12
        reasons.append('Senior level')
    elif level == 'mid':
        score += 6
    
    # International (+10)
    if data.get('working_abroad'):
        score += 10
        reasons.append('Working internationally')
    
    recommend = score >= 25
    return min(100, score), recommend, reasons, risks


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    return {"status": "EFMD CV Collection API running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# -------------------------------------------------------------
# CV UPLOAD ENDPOINTS
# -------------------------------------------------------------

@app.post("/upload/faculty/{institution_id}")
async def upload_faculty_cv(institution_id: str, file: UploadFile = File(...)):
    """
    Upload a faculty CV for EFMD data collection.
    
    The CV is parsed, scored, and stored. Top-scoring faculty
    will be recommended for the EFMD submission.
    
    IMPORTANT: The original PDF/DOCX is stored in Supabase Storage
    for Base Room preparation - EFMD reviewers need actual CVs!
    """
    # Verify institution exists
    inst = supabase.table('institutions').select('name, country').eq('id', institution_id).single().execute()
    if not inst.data:
        raise HTTPException(404, "Institution not found")
    
    # Store original file in Supabase Storage for Base Room
    file_content = await file.read()
    file_ext = file.filename.split('.')[-1].lower()
    storage_path = f"faculty/{institution_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    
    try:
        # Upload to Supabase Storage bucket 'cvs' (private)
        storage_result = supabase.storage.from_('cvs').upload(storage_path, file_content)
        # Store the path, not the URL - we'll generate signed URLs on demand
        pdf_url = storage_path  # Just store the path
    except Exception as e:
        # Storage might not be set up yet - continue without it
        pdf_url = None
        print(f"Storage upload failed: {e}")
    
    # Reset file position for text extraction
    await file.seek(0)
    
    institution_country = inst.data.get('country')
    
    # Extract text (file already read above)
    cv_text = extract_text_from_bytes(file_content, file.filename)
    
    # Parse with Claude
    parsed = parse_cv_with_claude(cv_text, FACULTY_PROMPT)
    
    # Score
    efmd_score, recommend, reasons, risks = score_faculty(parsed, institution_country)
    
    # Generate embedding
    summary = parsed.get('cv_summary') or f"{parsed.get('full_name', 'Unknown')} - {parsed.get('current_title', 'Faculty')}"
    embedding = generate_embedding(summary)
    
    # Store
    record = {
        'institution_id': institution_id,
        'full_name': parsed.get('full_name'),
        'email': parsed.get('email'),
        'current_title': parsed.get('current_title'),
        'department': parsed.get('department'),
        'employment_type': parsed.get('employment_type'),
        'fte_percentage': parsed.get('fte_percentage', 100),
        'highest_degree': parsed.get('highest_degree'),
        'degree_field': parsed.get('degree_field'),
        'degree_institution': parsed.get('degree_institution'),
        'degree_year': parsed.get('degree_year'),
        'publication_count_5yr': parsed.get('publications_5yr_total'),
        'peer_reviewed_count_5yr': parsed.get('publications_peer_reviewed'),
        'research_areas': parsed.get('research_areas'),
        'international_experience_years': parsed.get('international_experience_years'),
        'languages': parsed.get('languages'),
        'industry_experience_years': parsed.get('industry_experience_years'),
        'consulting_active': parsed.get('consulting_active'),
        'ers_research': parsed.get('ers_research'),
        'ers_teaching': parsed.get('ers_teaching'),
        'cv_text': cv_text[:50000],
        'cv_summary': summary,
        'embedding': embedding,
        'efmd_score': efmd_score,
        'include_recommended': recommend,
        'inclusion_reasons': reasons,
        'exclusion_risks': risks,
        'score_breakdown': {'reasons': reasons, 'risks': risks}
    }
    
    result = supabase.table('faculty_cvs').insert(record).execute()
    
    return {
        'success': True,
        'faculty_id': result.data[0]['id'],
        'name': parsed.get('full_name'),
        'efmd_score': efmd_score,
        'recommended': recommend,
        'strengths': reasons,
        'risks': risks,
        'message': f"CV processed. EFMD Score: {efmd_score}/100. {'Recommended for submission.' if recommend else 'May not be included in final selection.'}"
    }


@app.post("/upload/student/{programme_id}")
async def upload_student_cv(programme_id: str, file: UploadFile = File(...), cohort_year: int = None):
    """Upload a student CV."""
    # Verify programme and get institution
    prog = supabase.table('programmes').select('institution_id').eq('id', programme_id).single().execute()
    if not prog.data:
        raise HTTPException(404, "Programme not found")
    
    inst = supabase.table('institutions').select('country').eq('id', prog.data['institution_id']).single().execute()
    institution_country = inst.data.get('country') if inst.data else None
    
    # Extract and parse
    cv_text = extract_text_from_file(file)
    parsed = parse_cv_with_claude(cv_text, STUDENT_PROMPT)
    
    # Score
    efmd_score, recommend, reasons, risks = score_student(parsed, institution_country)
    
    # Embedding
    summary = parsed.get('cv_summary') or parsed.get('full_name', 'Student')
    embedding = generate_embedding(summary)
    
    # Store
    record = {
        'programme_id': programme_id,
        'full_name': parsed.get('full_name'),
        'email': parsed.get('email'),
        'gender': parsed.get('gender'),
        'nationality': parsed.get('nationality'),
        'age_at_entry': parsed.get('age'),
        'prior_degree': parsed.get('prior_degree'),
        'prior_degree_field': parsed.get('prior_degree_field'),
        'prior_institution': parsed.get('prior_institution'),
        'prior_institution_country': parsed.get('prior_institution_country'),
        'work_experience_years': parsed.get('work_experience_years'),
        'skills': parsed.get('skills'),
        'languages': parsed.get('languages'),
        'cohort_year': cohort_year or datetime.now().year,
        'status': 'Active',
        'cv_text': cv_text[:50000],
        'cv_summary': summary,
        'embedding': embedding,
        'efmd_score': efmd_score,
        'include_recommended': recommend,
        'inclusion_reasons': reasons,
        'exclusion_risks': risks,
    }
    
    result = supabase.table('student_cvs').insert(record).execute()
    
    return {
        'success': True,
        'student_id': result.data[0]['id'],
        'name': parsed.get('full_name'),
        'efmd_score': efmd_score,
        'recommended': recommend,
        'nationality': parsed.get('nationality'),
        'message': f"CV processed. EFMD Score: {efmd_score}/100."
    }


@app.post("/upload/alumni/{programme_id}")
async def upload_alumni_cv(programme_id: str, file: UploadFile = File(...), graduation_year: int = None):
    """Upload an alumni CV."""
    # Verify programme
    prog = supabase.table('programmes').select('id').eq('id', programme_id).single().execute()
    if not prog.data:
        raise HTTPException(404, "Programme not found")
    
    # Extract and parse
    cv_text = extract_text_from_file(file)
    parsed = parse_cv_with_claude(cv_text, ALUMNI_PROMPT)
    
    # Score
    efmd_score, recommend, reasons, risks = score_alumni(parsed)
    
    # Embedding
    summary = parsed.get('cv_summary') or f"{parsed.get('full_name', 'Alumni')} - {parsed.get('current_employer', '')}"
    embedding = generate_embedding(summary)
    
    # Store
    record = {
        'programme_id': programme_id,
        'full_name': parsed.get('full_name'),
        'email': parsed.get('email'),
        'linkedin_url': parsed.get('linkedin_url'),
        'graduation_year': graduation_year or parsed.get('graduation_year'),
        'employed': parsed.get('is_employed', False),
        'months_to_employment': parsed.get('months_to_first_job'),
        'current_employer': parsed.get('current_employer'),
        'current_job_title': parsed.get('current_job_title'),
        'current_industry': parsed.get('current_industry'),
        'current_country': parsed.get('current_country'),
        'career_level': parsed.get('seniority_level'),
        'working_abroad': parsed.get('working_abroad'),
        'positions_since_graduation': parsed.get('career_progression'),
        'cv_text': cv_text[:50000],
        'cv_summary': summary,
        'embedding': embedding,
        'efmd_score': efmd_score,
        'include_recommended': recommend,
        'inclusion_reasons': reasons,
        'exclusion_risks': risks,
    }
    
    result = supabase.table('alumni_cvs').insert(record).execute()
    
    return {
        'success': True,
        'alumni_id': result.data[0]['id'],
        'name': parsed.get('full_name'),
        'efmd_score': efmd_score,
        'recommended': recommend,
        'employer': parsed.get('current_employer'),
        'message': f"CV processed. EFMD Score: {efmd_score}/100."
    }


# -------------------------------------------------------------
# BASE ROOM PREPARATION - Download CVs for EFMD submission
# -------------------------------------------------------------

@app.get("/baseroom/faculty/{institution_id}")
async def get_faculty_baseroom_package(institution_id: str):
    """
    Get download links for top 25 faculty CVs for Base Room.
    
    Returns SIGNED URLs (expire in 1 hour) for secure download.
    These are the ACTUAL PDF/DOCX files for the EFMD Base Room.
    """
    # Get top 25 recommended faculty with PDF paths
    result = supabase.table('faculty_cvs').select(
        'id, full_name, current_title, highest_degree, efmd_score, pdf_url'
    ).eq('institution_id', institution_id).eq(
        'include_recommended', True
    ).order('efmd_score', desc=True).limit(25).execute()
    
    faculty = result.data or []
    
    # Generate signed URLs for those with PDFs
    faculty_with_urls = []
    missing = []
    
    for f in faculty:
        if f.get('pdf_url'):
            try:
                # Generate signed URL (expires in 1 hour)
                signed = supabase.storage.from_('cvs').create_signed_url(
                    f['pdf_url'], 
                    3600  # 1 hour expiry
                )
                faculty_with_urls.append({
                    'name': f['full_name'],
                    'title': f.get('current_title'),
                    'degree': f.get('highest_degree'),
                    'score': f['efmd_score'],
                    'download_url': signed.get('signedURL') or signed.get('signedUrl'),
                    'filename': f"Faculty_CV_{f['full_name'].replace(' ', '_')}.pdf",
                    'expires_in': '1 hour'
                })
            except Exception as e:
                missing.append({
                    'name': f['full_name'],
                    'id': f['id'],
                    'message': f'Error generating download link: {str(e)}'
                })
        else:
            missing.append({
                'name': f['full_name'],
                'id': f['id'],
                'message': 'CV file not uploaded - need to re-upload'
            })
    
    return {
        'ready_for_baseroom': len(faculty_with_urls),
        'missing_pdfs': len(missing),
        'faculty_cvs': faculty_with_urls,
        'missing': missing,
        'note': 'Download links expire in 1 hour for security',
        'instructions': 'Download all CVs and place in Base Room folder: Faculty/CVs/'
    }


@app.get("/baseroom/alumni/{programme_id}")
async def get_alumni_baseroom_package(programme_id: str):
    """
    Get download links for top 30 alumni CVs for Base Room.
    Returns SIGNED URLs (expire in 1 hour) for secure download.
    """
    result = supabase.table('alumni_cvs').select(
        'id, full_name, current_employer, current_job_title, efmd_score, pdf_url, linkedin_url'
    ).eq('programme_id', programme_id).eq(
        'include_recommended', True
    ).order('efmd_score', desc=True).limit(30).execute()
    
    alumni = result.data or []
    alumni_with_urls = []
    missing = []
    
    for a in alumni:
        if a.get('pdf_url'):
            try:
                signed = supabase.storage.from_('cvs').create_signed_url(
                    a['pdf_url'],
                    3600
                )
                alumni_with_urls.append({
                    'name': a['full_name'],
                    'employer': a.get('current_employer'),
                    'title': a.get('current_job_title'),
                    'score': a['efmd_score'],
                    'download_url': signed.get('signedURL') or signed.get('signedUrl'),
                    'linkedin': a.get('linkedin_url'),
                    'filename': f"Alumni_CV_{a['full_name'].replace(' ', '_')}.pdf",
                    'expires_in': '1 hour'
                })
            except:
                missing.append({'name': a['full_name'], 'id': a['id']})
        else:
            missing.append({'name': a['full_name'], 'id': a['id']})
    
    return {
        'ready_for_baseroom': len(alumni_with_urls),
        'alumni_cvs': alumni_with_urls,
        'missing': missing,
        'note': 'Download links expire in 1 hour for security',
        'instructions': 'Download all CVs and place in Base Room folder: Alumni/CVs/'
    }


@app.get("/baseroom/{programme_id}/checklist")
async def get_baseroom_checklist(programme_id: str):
    """
    Complete Base Room preparation checklist.
    
    Shows what's ready and what's missing for EFMD peer review visit.
    """
    prog = supabase.table('programmes').select('*, institutions(*)').eq('id', programme_id).single().execute()
    if not prog.data:
        raise HTTPException(404, "Programme not found")
    
    institution_id = prog.data['institution_id']
    
    # Count CVs with files
    faculty = supabase.table('faculty_cvs').select('id, pdf_url, include_recommended').eq('institution_id', institution_id).execute()
    alumni = supabase.table('alumni_cvs').select('id, pdf_url, include_recommended').eq('programme_id', programme_id).execute()
    students = supabase.table('student_cvs').select('id, pdf_url, include_recommended').eq('programme_id', programme_id).execute()
    
    faculty_data = faculty.data or []
    alumni_data = alumni.data or []
    student_data = students.data or []
    
    faculty_recommended = [f for f in faculty_data if f.get('include_recommended')]
    faculty_with_pdf = [f for f in faculty_recommended if f.get('pdf_url')]
    
    alumni_recommended = [a for a in alumni_data if a.get('include_recommended')]
    alumni_with_pdf = [a for a in alumni_recommended if a.get('pdf_url')]
    
    return {
        'programme': prog.data['programme_name'],
        'institution': prog.data.get('institutions', {}).get('name'),
        
        'baseroom_checklist': {
            'faculty_cvs': {
                'required': 25,
                'recommended': len(faculty_recommended),
                'with_pdf': len(faculty_with_pdf),
                'ready': len(faculty_with_pdf) >= 25,
                'action': None if len(faculty_with_pdf) >= 25 else f'Need {25 - len(faculty_with_pdf)} more faculty CV files'
            },
            'alumni_cvs': {
                'required': 30,
                'recommended': len(alumni_recommended),
                'with_pdf': len(alumni_with_pdf),
                'ready': len(alumni_with_pdf) >= 30,
                'action': None if len(alumni_with_pdf) >= 30 else f'Need {30 - len(alumni_with_pdf)} more alumni CV files'
            },
            'student_sample': {
                'collected': len(student_data),
                'note': 'Student CVs optional for Base Room - data extracted for Tables 2/3'
            }
        },
        
        'download_endpoints': {
            'faculty_package': f'/baseroom/faculty/{institution_id}',
            'alumni_package': f'/baseroom/alumni/{programme_id}'
        },
        
        'baseroom_folder_structure': [
            'Base Room/',
            '├── Faculty/',
            '│   ├── CVs/                    ← Download from /baseroom/faculty/{id}',
            '│   ├── Table_9_Statistics.xlsx',
            '│   ├── Table_10_Teaching.xlsx',
            '│   └── Table_11_Research.xlsx',
            '├── Students/',
            '│   ├── Table_2_Demographics.xlsx',
            '│   └── Table_3_Prior_Education.xlsx',
            '├── Alumni/',
            '│   ├── CVs/                    ← Download from /baseroom/alumni/{id}',
            '│   └── Table_4_Employment.xlsx',
            '├── Programme/',
            '│   ├── ILO_Matrix.xlsx',
            '│   ├── Curriculum_Overview.pdf',
            '│   └── Course_Descriptions/',
            '└── Quality_Assurance/',
                '    └── QA_Processes.pdf'
        ]
    }


# -------------------------------------------------------------
# SEARCH/SELECTION ENDPOINTS (Like Shortlist!)
# -------------------------------------------------------------

@app.get("/faculty/{institution_id}/top")
async def get_top_faculty(
    institution_id: str, 
    limit: int = Query(25, description="Number of faculty to return"),
    include_all: bool = Query(False, description="Include non-recommended")
):
    """
    Get top faculty for EFMD submission - cherry-picked for best scores.
    
    Returns the CVs that should go in the Base Room.
    """
    query = supabase.table('faculty_cvs').select(
        'id, full_name, email, current_title, highest_degree, '
        'publication_count_5yr, international_experience_years, '
        'efmd_score, include_recommended, inclusion_reasons, exclusion_risks, '
        'pdf_url'
    ).eq('institution_id', institution_id)
    
    if not include_all:
        query = query.eq('include_recommended', True)
    
    result = query.order('efmd_score', desc=True).limit(limit).execute()
    
    # Calculate aggregate stats
    data = result.data or []
    phd_count = sum(1 for f in data if f.get('highest_degree') and 'phd' in f.get('highest_degree', '').lower())
    intl_count = sum(1 for f in data if f.get('international_experience_years') and f.get('international_experience_years') > 0)
    
    return {
        'faculty': data,
        'count': len(data),
        'aggregate_stats': {
            'avg_score': round(sum(f.get('efmd_score', 0) for f in data) / len(data), 1) if data else 0,
            'phd_percentage': round(phd_count / len(data) * 100, 1) if data else 0,
            'international_percentage': round(intl_count / len(data) * 100, 1) if data else 0,
        },
        'ready_for_submission': len(data) >= 25
    }


@app.get("/alumni/{programme_id}/top")
async def get_top_alumni(
    programme_id: str,
    limit: int = Query(30, description="Number of alumni to return"),
    include_all: bool = Query(False, description="Include non-recommended")
):
    """
    Get top alumni for EFMD submission - best employment outcomes.
    """
    query = supabase.table('alumni_cvs').select(
        'id, full_name, email, graduation_year, employed, months_to_employment, '
        'current_employer, current_job_title, current_industry, career_level, '
        'working_abroad, efmd_score, include_recommended, inclusion_reasons, '
        'pdf_url, linkedin_url'
    ).eq('programme_id', programme_id)
    
    if not include_all:
        query = query.eq('include_recommended', True)
    
    result = query.order('efmd_score', desc=True).limit(limit).execute()
    
    data = result.data or []
    employed_count = sum(1 for a in data if a.get('employed'))
    fast_employed = sum(1 for a in data if a.get('months_to_employment') and a.get('months_to_employment') <= 3)
    intl_count = sum(1 for a in data if a.get('working_abroad'))
    
    return {
        'alumni': data,
        'count': len(data),
        'aggregate_stats': {
            'avg_score': round(sum(a.get('efmd_score', 0) for a in data) / len(data), 1) if data else 0,
            'employment_rate': round(employed_count / len(data) * 100, 1) if data else 0,
            'fast_employment_rate': round(fast_employed / len(data) * 100, 1) if data else 0,
            'working_abroad_rate': round(intl_count / len(data) * 100, 1) if data else 0,
        },
        'ready_for_submission': len(data) >= 30
    }


@app.get("/students/{programme_id}/diversity")
async def get_student_diversity(programme_id: str):
    """Get student diversity metrics for EFMD Table 2/3."""
    result = supabase.table('student_cvs').select(
        'nationality, gender, work_experience_years, prior_degree_field'
    ).eq('programme_id', programme_id).execute()
    
    data = result.data or []
    nationalities = list(set(s.get('nationality') for s in data if s.get('nationality')))
    
    return {
        'total_students': len(data),
        'nationalities_count': len(nationalities),
        'nationalities': nationalities,
        'gender_breakdown': {
            'male': sum(1 for s in data if s.get('gender') and 'male' in s.get('gender', '').lower() and 'female' not in s.get('gender', '').lower()),
            'female': sum(1 for s in data if s.get('gender') and 'female' in s.get('gender', '').lower()),
        },
        'avg_work_experience': round(sum(s.get('work_experience_years', 0) or 0 for s in data) / len(data), 1) if data else 0,
    }


# -------------------------------------------------------------
# STATUS AND REPORTS
# -------------------------------------------------------------

@app.get("/programme/{programme_id}/status")
async def get_programme_status(programme_id: str):
    """Get CV collection status for a programme."""
    prog = supabase.table('programmes').select('*, institutions(*)').eq('id', programme_id).single().execute()
    if not prog.data:
        raise HTTPException(404, "Programme not found")
    
    institution_id = prog.data['institution_id']
    
    faculty = supabase.table('faculty_cvs').select('id, efmd_score, include_recommended').eq('institution_id', institution_id).execute()
    students = supabase.table('student_cvs').select('id, efmd_score, include_recommended').eq('programme_id', programme_id).execute()
    alumni = supabase.table('alumni_cvs').select('id, efmd_score, include_recommended').eq('programme_id', programme_id).execute()
    ilos = supabase.table('programme_ilos').select('id').eq('programme_id', programme_id).execute()
    
    return {
        'programme': prog.data['programme_name'],
        'institution': prog.data.get('institutions', {}).get('name'),
        'faculty': {
            'collected': len(faculty.data or []),
            'recommended': sum(1 for f in (faculty.data or []) if f.get('include_recommended')),
            'target': 25,
            'complete': len(faculty.data or []) >= 25
        },
        'students': {
            'collected': len(students.data or []),
            'recommended': sum(1 for s in (students.data or []) if s.get('include_recommended')),
            'target': 25,
            'complete': len(students.data or []) >= 25
        },
        'alumni': {
            'collected': len(alumni.data or []),
            'recommended': sum(1 for a in (alumni.data or []) if a.get('include_recommended')),
            'target': 25,
            'complete': len(alumni.data or []) >= 25
        },
        'ilos': {
            'count': len(ilos.data or []),
            'target': 6,
            'complete': len(ilos.data or []) >= 5
        },
        'overall_ready': all([
            len(faculty.data or []) >= 25,
            len(students.data or []) >= 25,
            len(alumni.data or []) >= 25,
            len(ilos.data or []) >= 5
        ])
    }


@app.get("/programme/{programme_id}/gap-report", response_class=PlainTextResponse)
async def get_gap_report(programme_id: str):
    """Get gap analysis report as text."""
    from reports.report_generators import generate_gap_analysis_report
    return generate_gap_analysis_report(programme_id, supabase)


@app.get("/programme/{programme_id}/improvement-report", response_class=PlainTextResponse)
async def get_improvement_report(programme_id: str):
    """Get improvement process report as text."""
    from reports.report_generators import generate_improvement_report
    return generate_improvement_report(programme_id, supabase)


# -------------------------------------------------------------
# INSTITUTION/PROGRAMME MANAGEMENT
# -------------------------------------------------------------

class InstitutionCreate(BaseModel):
    name: str
    country: str
    city: str = None
    website: str = None

class ProgrammeCreate(BaseModel):
    institution_id: str
    programme_name: str
    degree_type: str = None
    primary_url: str = None


@app.post("/institutions")
async def create_institution(data: InstitutionCreate):
    """Create a new institution."""
    result = supabase.table('institutions').insert(data.dict()).execute()
    return {'success': True, 'institution': result.data[0]}


@app.post("/programmes")
async def create_programme(data: ProgrammeCreate):
    """Create a new programme."""
    result = supabase.table('programmes').insert(data.dict()).execute()
    return {'success': True, 'programme': result.data[0]}


@app.get("/institutions")
async def list_institutions():
    """List all institutions."""
    result = supabase.table('institutions').select('*').execute()
    return {'institutions': result.data}


@app.get("/programmes")
async def list_programmes(institution_id: str = None):
    """List programmes, optionally filtered by institution."""
    query = supabase.table('programmes').select('*, institutions(name)')
    if institution_id:
        query = query.eq('institution_id', institution_id)
    result = query.execute()
    return {'programmes': result.data}

# -------------------------------------------------------------
# SCRAPER ENDPOINT
# -------------------------------------------------------------

@app.post("/programme/{programme_id}/scrape")
async def scrape_programme(programme_id: str):
    """
    Scrape programme URL for ILOs and course data.
    """
    import sys
    
    # Get programme URL
    prog = supabase.table('programmes').select('*, institutions(name, country)').eq('id', programme_id).single().execute()
    if not prog.data:
        raise HTTPException(404, "Programme not found")
    
    url = prog.data.get('primary_url')
    if not url:
        raise HTTPException(400, "Programme has no URL set")
    
    institution = prog.data.get('institutions', {}).get('name', 'Unknown')
    programme_name = prog.data.get('programme_name', 'Unknown')
    
    # Add scraper to path
    scraper_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if scraper_path not in sys.path:
        sys.path.insert(0, scraper_path)
    
    try:
        from efmd_scraper_v2 import EFMDScraper
        
        scraper = EFMDScraper(use_embeddings=True, use_database=False)
        programme_data = scraper.scrape_programme(
            url=url,
            institution=institution,
            programme_name=programme_name,
            follow_variants=True
        )
        
        # Store ILOs
        ilos_stored = 0
        for ilo in programme_data.programme_ilos:
            try:
                ilo_record = {
                    'programme_id': programme_id,
                    'ilo_text': ilo.text,
                    'ksa_category': ilo.ksa_category,
                    'has_weak_verb': ilo.has_weak_verb,
                    'is_measurable': ilo.is_measurable,
                }
                supabase.table('programme_ilos').insert(ilo_record).execute()
                ilos_stored += 1
            except Exception as e:
                print(f"Error storing ILO: {e}")
        
        # Calculate simple readiness score
        ilo_count = len(programme_data.programme_ilos)
        readiness_score = min(100, ilo_count * 15)  # ~6-7 ILOs = 100%
        
        return {
            'success': True,
            'ilos_found': ilo_count,
            'ilos_stored': ilos_stored,
            'readiness_score': readiness_score,
            'pillar_coverage': {},
            'missing_pillars': [],
        }
        
    except ImportError as e:
        raise HTTPException(500, f"Scraper not available: {e}")
    except Exception as e:
        raise HTTPException(500, f"Scraping failed: {str(e)}")

     # ============================================================
# BULK UPLOAD - DUPLICATE CHECK ENDPOINTS
# ============================================================

@app.get("/check-duplicate/faculty/{institution_id}")
async def check_faculty_duplicate(
    institution_id: str,
    file_hash: str = Query(...),
    filename: str = Query(...)
):
    """Check if a faculty CV with this hash already exists."""
    try:
        # Check by file hash first
        result = supabase.table('faculty_cvs').select('id, full_name').eq(
            'institution_id', institution_id
        ).eq('file_hash', file_hash).execute()
        
        if result.data:
            return {
                "is_duplicate": True,
                "existing_id": result.data[0]['id'],
                "existing_filename": result.data[0]['full_name']
            }
        
        # Also check by filename
        result_by_name = supabase.table('faculty_cvs').select('id').eq(
            'institution_id', institution_id
        ).eq('full_name', filename).execute()
        
        if result_by_name.data:
            return {
                "is_duplicate": True,
                "existing_id": result_by_name.data[0]['id'],
                "existing_filename": filename
            }
        
        return {"is_duplicate": False, "existing_id": None}
        
    except Exception as e:
        print(f"Duplicate check error: {e}")
        return {"is_duplicate": False, "existing_id": None}


@app.get("/check-duplicate/student/{programme_id}")
async def check_student_duplicate(
    programme_id: str,
    file_hash: str = Query(...),
    filename: str = Query(...)
):
    """Check if a student CV with this hash already exists."""
    try:
        result = supabase.table('student_cvs').select('id, full_name').eq(
            'programme_id', programme_id
        ).eq('file_hash', file_hash).execute()
        
        if result.data:
            return {
                "is_duplicate": True,
                "existing_id": result.data[0]['id'],
                "existing_filename": result.data[0]['full_name']
            }
        
        result_by_name = supabase.table('student_cvs').select('id').eq(
            'programme_id', programme_id
        ).eq('full_name', filename).execute()
        
        if result_by_name.data:
            return {
                "is_duplicate": True,
                "existing_id": result_by_name.data[0]['id'],
                "existing_filename": filename
            }
        
        return {"is_duplicate": False, "existing_id": None}
        
    except Exception as e:
        print(f"Duplicate check error: {e}")
        return {"is_duplicate": False, "existing_id": None}


@app.get("/check-duplicate/alumni/{programme_id}")
async def check_alumni_duplicate(
    programme_id: str,
    file_hash: str = Query(...),
    filename: str = Query(...)
):
    """Check if an alumni CV with this hash already exists."""
    try:
        result = supabase.table('alumni_cvs').select('id, full_name').eq(
            'programme_id', programme_id
        ).eq('file_hash', file_hash).execute()
        
        if result.data:
            return {
                "is_duplicate": True,
                "existing_id": result.data[0]['id'],
                "existing_filename": result.data[0]['full_name']
            }
        
        result_by_name = supabase.table('alumni_cvs').select('id').eq(
            'programme_id', programme_id
        ).eq('full_name', filename).execute()
        
        if result_by_name.data:
            return {
                "is_duplicate": True,
                "existing_id": result_by_name.data[0]['id'],
                "existing_filename": filename
            }
        
        return {"is_duplicate": False, "existing_id": None}
        
    except Exception as e:
        print(f"Duplicate check error: {e}")
        return {"is_duplicate": False, "existing_id": None}   
# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
