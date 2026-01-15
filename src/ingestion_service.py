#!/usr/bin/env python3
"""
EFMD CV Ingestion Service
=========================
Connects Careersorter CV parsing to EFMD Supabase database.
Handles all three CV types: Faculty, Student, Alumni

Flow:
1. CV uploaded via Careersorter link
2. Claude extracts structured data using EFMD prompts
3. Gemini generates embedding
4. CV scored against EFMD criteria
5. Data stored in appropriate table
6. Selection optimizer updates recommendations
"""

import os
import json
from datetime import datetime
from typing import Optional, Literal
from dotenv import load_dotenv

load_dotenv()

# Import our modules
from cv_scoring import (
    score_faculty_cv, score_student_cv, score_alumni_cv,
    SelectionOptimizer, FacultyScore, StudentScore, AlumniScore
)

# These would be imported from your existing Careersorter infrastructure
# from careersorter.parser import parse_cv_with_claude
# from careersorter.embeddings import generate_embedding

try:
    from supabase import create_client, Client
    import anthropic
    import google.generativeai as genai
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    print(f"Warning: Missing dependency - {e}")


# ============================================================
# CONFIGURATION
# ============================================================

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://bkhvztyvfkqzqqtoxxxi.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

CV_TYPE = Literal['faculty', 'student', 'alumni']


# ============================================================
# PROMPTS (imported from prompts module in production)
# ============================================================

from prompts.cv_extraction_prompts import (
    FACULTY_EXTRACTION_PROMPT,
    STUDENT_EXTRACTION_PROMPT, 
    ALUMNI_EXTRACTION_PROMPT
)


# ============================================================
# SERVICES
# ============================================================

class EFMDIngestionService:
    """
    Main service for ingesting CVs into EFMD database.
    """
    
    def __init__(self):
        if not HAS_DEPS:
            raise RuntimeError("Missing dependencies. Install: supabase anthropic google-generativeai")
        
        # Initialize clients
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
        
        self.optimizer = SelectionOptimizer()
    
    # --------------------------------------------------------
    # CV PARSING
    # --------------------------------------------------------
    
    def parse_cv(self, cv_text: str, cv_type: CV_TYPE) -> dict:
        """
        Parse CV text using Claude with type-specific prompt.
        """
        prompts = {
            'faculty': FACULTY_EXTRACTION_PROMPT,
            'student': STUDENT_EXTRACTION_PROMPT,
            'alumni': ALUMNI_EXTRACTION_PROMPT
        }
        
        prompt = prompts[cv_type]
        
        message = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n---\nCV TEXT:\n{cv_text}"
                }
            ]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text
        
        # Try to parse JSON
        try:
            # Handle potential markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse CV response: {e}")
            return {'error': str(e), 'raw_response': response_text}
    
    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding using Gemini."""
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="semantic_similarity"
        )
        return result['embedding']
    
    # --------------------------------------------------------
    # FACULTY CV INGESTION
    # --------------------------------------------------------
    
    def ingest_faculty_cv(self,
                          cv_text: str,
                          institution_id: str,
                          pdf_url: str = None) -> dict:
        """
        Full pipeline for faculty CV ingestion.
        
        Returns:
            {
                'success': bool,
                'faculty_id': str,
                'score': FacultyScore,
                'parsed_data': dict
            }
        """
        # 1. Parse CV
        parsed = self.parse_cv(cv_text, 'faculty')
        if 'error' in parsed:
            return {'success': False, 'error': parsed['error']}
        
        # 2. Get institution country for scoring
        inst = self.supabase.table('institutions').select('country').eq('id', institution_id).single().execute()
        institution_country = inst.data.get('country') if inst.data else None
        
        # 3. Score CV
        score = score_faculty_cv(parsed, institution_country)
        
        # 4. Generate embedding
        summary_text = parsed.get('cv_summary', '') or f"{parsed.get('full_name', '')} - {parsed.get('current_position', {}).get('title', '')}"
        embedding = self.generate_embedding(summary_text)
        
        # 5. Prepare database record
        record = {
            'institution_id': institution_id,
            'full_name': parsed.get('full_name'),
            'email': parsed.get('email'),
            
            # Position
            'current_title': parsed.get('current_position', {}).get('title'),
            'department': parsed.get('current_position', {}).get('department'),
            'employment_type': parsed.get('current_position', {}).get('employment_type'),
            'fte_percentage': parsed.get('current_position', {}).get('fte_percentage'),
            
            # Qualifications
            'highest_degree': parsed.get('highest_degree', {}).get('degree'),
            'degree_field': parsed.get('highest_degree', {}).get('field'),
            'degree_institution': parsed.get('highest_degree', {}).get('institution'),
            'degree_year': parsed.get('highest_degree', {}).get('year'),
            'is_academically_qualified': 'has_doctorate' in score.breakdown,
            
            # Research
            'research_areas': parsed.get('research_areas', []),
            'publications': parsed.get('publications_last_5_years'),
            'publication_count_5yr': parsed.get('publications_last_5_years', {}).get('total', 0),
            'peer_reviewed_count_5yr': parsed.get('publications_last_5_years', {}).get('peer_reviewed_journals', 0),
            
            # International
            'international_education': parsed.get('international_experience', {}).get('visiting_positions'),
            'international_experience_years': parsed.get('international_experience', {}).get('total_years_abroad'),
            'languages': parsed.get('languages'),
            
            # Industry
            'industry_experience_years': parsed.get('industry_experience', {}).get('total_years'),
            'consulting_active': parsed.get('industry_experience', {}).get('current_consulting'),
            'current_industry_roles': parsed.get('industry_experience', {}).get('industry_roles'),
            
            # ERS
            'ers_research': parsed.get('ers_activities', {}).get('has_ers_research'),
            'ers_teaching': parsed.get('ers_activities', {}).get('has_ers_teaching'),
            
            # CV data
            'cv_text': cv_text[:50000],  # Limit size
            'cv_summary': parsed.get('cv_summary'),
            'embedding': embedding,
            'pdf_url': pdf_url,
            
            # Scoring
            'efmd_score': score.total_score,
            'include_recommended': score.recommend_include,
            'inclusion_reasons': score.inclusion_reasons,
            'exclusion_risks': score.exclusion_risks,
            'score_breakdown': score.breakdown,
        }
        
        # 6. Insert into database
        result = self.supabase.table('faculty_cvs').insert(record).execute()
        
        return {
            'success': True,
            'faculty_id': result.data[0]['id'],
            'score': score,
            'parsed_data': parsed
        }
    
    # --------------------------------------------------------
    # STUDENT CV INGESTION
    # --------------------------------------------------------
    
    def ingest_student_cv(self,
                          cv_text: str,
                          programme_id: str,
                          cohort_year: int = None,
                          pdf_url: str = None) -> dict:
        """
        Full pipeline for student CV ingestion.
        """
        # 1. Parse CV
        parsed = self.parse_cv(cv_text, 'student')
        if 'error' in parsed:
            return {'success': False, 'error': parsed['error']}
        
        # 2. Get programme's institution country
        prog = self.supabase.table('programmes').select('institution_id').eq('id', programme_id).single().execute()
        if prog.data:
            inst = self.supabase.table('institutions').select('country').eq('id', prog.data['institution_id']).single().execute()
            institution_country = inst.data.get('country') if inst.data else None
        else:
            institution_country = None
        
        # 3. Get existing selection for diversity calculation
        existing = self.supabase.table('student_cvs').select('nationality, gender').eq('programme_id', programme_id).eq('include_recommended', True).execute()
        existing_nationalities = [s['nationality'] for s in existing.data if s.get('nationality')]
        gender_counts = {'male': 0, 'female': 0}
        for s in existing.data:
            if s.get('gender'):
                g = s['gender'].lower()
                if 'female' in g:
                    gender_counts['female'] += 1
                elif 'male' in g:
                    gender_counts['male'] += 1
        
        # 4. Score CV
        score = score_student_cv(
            parsed, 
            institution_country,
            existing_nationalities,
            gender_counts
        )
        
        # 5. Generate embedding
        summary_text = parsed.get('cv_summary', '') or f"{parsed.get('full_name', '')} - student"
        embedding = self.generate_embedding(summary_text)
        
        # 6. Prepare record
        demographics = parsed.get('demographics', {})
        prior_edu = parsed.get('prior_education', {}).get('highest_degree', {})
        work = parsed.get('work_experience', {})
        
        record = {
            'programme_id': programme_id,
            'full_name': parsed.get('full_name'),
            'email': parsed.get('email'),
            
            # Demographics
            'gender': demographics.get('gender'),
            'nationality': demographics.get('nationality'),
            'age_at_entry': demographics.get('age'),
            
            # Prior education
            'prior_degree': prior_edu.get('degree_type'),
            'prior_degree_field': prior_edu.get('field'),
            'prior_institution': prior_edu.get('institution'),
            'prior_institution_country': prior_edu.get('country'),
            
            # Work experience
            'work_experience_years': work.get('total_years'),
            'work_experience_details': work.get('positions'),
            
            # Status
            'cohort_year': cohort_year or datetime.now().year,
            'status': 'Active',
            
            # Skills & languages
            'skills': parsed.get('skills', []),
            'languages': parsed.get('languages'),
            
            # CV data
            'cv_text': cv_text[:50000],
            'cv_summary': parsed.get('cv_summary'),
            'embedding': embedding,
            'pdf_url': pdf_url,
            
            # Scoring
            'efmd_score': score.total_score,
            'include_recommended': score.recommend_include,
            'inclusion_reasons': score.inclusion_reasons,
            'exclusion_risks': score.exclusion_risks,
            'score_breakdown': score.breakdown,
        }
        
        result = self.supabase.table('student_cvs').insert(record).execute()
        
        return {
            'success': True,
            'student_id': result.data[0]['id'],
            'score': score,
            'parsed_data': parsed
        }
    
    # --------------------------------------------------------
    # ALUMNI CV INGESTION
    # --------------------------------------------------------
    
    def ingest_alumni_cv(self,
                         cv_text: str,
                         programme_id: str,
                         graduation_year: int = None,
                         pdf_url: str = None) -> dict:
        """
        Full pipeline for alumni CV ingestion.
        """
        # 1. Parse CV
        parsed = self.parse_cv(cv_text, 'alumni')
        if 'error' in parsed:
            return {'success': False, 'error': parsed['error']}
        
        # 2. Get institution country
        prog = self.supabase.table('programmes').select('institution_id').eq('id', programme_id).single().execute()
        if prog.data:
            inst = self.supabase.table('institutions').select('country').eq('id', prog.data['institution_id']).single().execute()
            institution_country = inst.data.get('country') if inst.data else None
        else:
            institution_country = None
        
        # 3. Score CV
        score = score_alumni_cv(parsed, institution_country)
        
        # 4. Generate embedding
        current = parsed.get('current_employment', {})
        summary_text = parsed.get('cv_summary', '') or f"{parsed.get('full_name', '')} - {current.get('employer', '')} {current.get('job_title', '')}"
        embedding = self.generate_embedding(summary_text)
        
        # 5. Prepare record
        first_job = parsed.get('first_job_after_graduation', {})
        career = parsed.get('career_progression', {})
        intl = parsed.get('international_career', {})
        
        record = {
            'programme_id': programme_id,
            'full_name': parsed.get('full_name'),
            'email': parsed.get('email'),
            'linkedin_url': parsed.get('linkedin_url'),
            
            # Graduation
            'graduation_year': graduation_year or parsed.get('graduation', {}).get('year'),
            
            # Employment
            'employed': current.get('is_employed', False),
            'months_to_employment': first_job.get('months_to_employment'),
            
            # Current position
            'current_employer': current.get('employer'),
            'current_job_title': current.get('job_title'),
            'current_industry': current.get('industry'),
            'current_country': current.get('country'),
            'career_level': current.get('seniority_level'),
            
            # Career progression
            'positions_since_graduation': career.get('positions_since_graduation'),
            
            # International
            'working_abroad': current.get('is_international') or intl.get('currently_abroad'),
            
            # CV data
            'cv_text': cv_text[:50000],
            'cv_summary': parsed.get('cv_summary'),
            'embedding': embedding,
            'pdf_url': pdf_url,
            
            # Scoring
            'efmd_score': score.total_score,
            'include_recommended': score.recommend_include,
            'inclusion_reasons': score.inclusion_reasons,
            'exclusion_risks': score.exclusion_risks,
            'score_breakdown': score.breakdown,
        }
        
        result = self.supabase.table('alumni_cvs').insert(record).execute()
        
        return {
            'success': True,
            'alumni_id': result.data[0]['id'],
            'score': score,
            'parsed_data': parsed
        }
    
    # --------------------------------------------------------
    # COLLECTION STATUS
    # --------------------------------------------------------
    
    def get_collection_status(self, programme_id: str) -> dict:
        """
        Get CV collection progress for a programme.
        """
        # Get programme and institution
        prog = self.supabase.table('programmes').select('*, institutions(*)').eq('id', programme_id).single().execute()
        
        if not prog.data:
            return {'error': 'Programme not found'}
        
        institution_id = prog.data['institution_id']
        
        # Count CVs
        faculty = self.supabase.table('faculty_cvs').select('id, efmd_score, include_recommended').eq('institution_id', institution_id).execute()
        students = self.supabase.table('student_cvs').select('id, efmd_score, include_recommended').eq('programme_id', programme_id).execute()
        alumni = self.supabase.table('alumni_cvs').select('id, efmd_score, include_recommended').eq('programme_id', programme_id).execute()
        
        return {
            'programme': prog.data['programme_name'],
            'institution': prog.data['institutions']['name'] if prog.data.get('institutions') else 'Unknown',
            
            'faculty': {
                'total': len(faculty.data),
                'recommended': sum(1 for f in faculty.data if f.get('include_recommended')),
                'avg_score': round(sum(f.get('efmd_score', 0) for f in faculty.data) / len(faculty.data), 1) if faculty.data else 0,
                'target': 25,
                'status': 'complete' if len(faculty.data) >= 25 else 'in_progress'
            },
            
            'students': {
                'total': len(students.data),
                'recommended': sum(1 for s in students.data if s.get('include_recommended')),
                'avg_score': round(sum(s.get('efmd_score', 0) for s in students.data) / len(students.data), 1) if students.data else 0,
                'target': 50,
                'status': 'complete' if len(students.data) >= 50 else 'in_progress'
            },
            
            'alumni': {
                'total': len(alumni.data),
                'recommended': sum(1 for a in alumni.data if a.get('include_recommended')),
                'avg_score': round(sum(a.get('efmd_score', 0) for a in alumni.data) / len(alumni.data), 1) if alumni.data else 0,
                'target': 40,
                'status': 'complete' if len(alumni.data) >= 40 else 'in_progress'
            }
        }
    
    # --------------------------------------------------------
    # SELECTION REPORT
    # --------------------------------------------------------
    
    def generate_selection_report(self, programme_id: str) -> dict:
        """
        Generate optimized selection report showing:
        - Who to include vs exclude
        - Impact on EFMD metrics
        - Recommendations
        """
        prog = self.supabase.table('programmes').select('*, institutions(*)').eq('id', programme_id).single().execute()
        
        if not prog.data:
            return {'error': 'Programme not found'}
        
        institution_id = prog.data['institution_id']
        institution_country = prog.data.get('institutions', {}).get('country')
        
        self.optimizer.institution_country = institution_country
        
        # Get all CVs with full data
        faculty = self.supabase.table('faculty_cvs').select('*').eq('institution_id', institution_id).execute()
        alumni = self.supabase.table('alumni_cvs').select('*').eq('programme_id', programme_id).execute()
        
        # Run optimization
        faculty_selection = self.optimizer.optimize_faculty_selection(
            [json.loads(f['score_breakdown']) if isinstance(f.get('score_breakdown'), str) else f for f in faculty.data],
            target_count=25
        ) if faculty.data else {}
        
        alumni_selection = self.optimizer.optimize_alumni_selection(
            alumni.data,
            target_count=30
        ) if alumni.data else {}
        
        return {
            'programme': prog.data['programme_name'],
            'institution': prog.data['institutions']['name'] if prog.data.get('institutions') else 'Unknown',
            'generated_at': datetime.now().isoformat(),
            
            'faculty_selection': faculty_selection,
            'alumni_selection': alumni_selection,
            
            'summary': {
                'faculty_improvement': faculty_selection.get('comparison', {}).get('improvement', {}),
                'alumni_improvement': alumni_selection.get('comparison', {}).get('improvement', {}),
            }
        }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    print("EFMD CV Ingestion Service")
    print("=" * 50)
    print("\nThis service connects to Supabase and processes CVs.")
    print("\nUsage in code:")
    print("  service = EFMDIngestionService()")
    print("  result = service.ingest_faculty_cv(cv_text, institution_id)")
    print("  status = service.get_collection_status(programme_id)")
