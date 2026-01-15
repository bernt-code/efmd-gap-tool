# EFMD CV Extraction Prompts
# ===========================
# These prompts are used with Claude to extract EFMD-relevant data from CVs

FACULTY_EXTRACTION_PROMPT = """
You are extracting data from a faculty CV for EFMD Programme Accreditation.
Extract ALL available information into this exact JSON structure.

CRITICAL FIELDS FOR EFMD (extract carefully):
- Doctoral degree details (for Table 9: % with doctorate)
- Publications in last 5 years (for Table 11: research output)
- International experience (for international dimension)
- Industry/consulting experience (for practice connection)
- Current teaching load (for Table 10)

Return valid JSON only, no markdown:

{
    "full_name": "string",
    "email": "string or null",
    "phone": "string or null",
    
    "current_position": {
        "title": "string (Professor, Associate Professor, Assistant Professor, Lecturer, etc.)",
        "department": "string or null",
        "institution": "string",
        "start_year": "number or null",
        "employment_type": "full-time | part-time | adjunct | visiting",
        "fte_percentage": "number 0-100, default 100 for full-time"
    },
    
    "highest_degree": {
        "degree": "PhD | DBA | DPhil | EdD | MBA | MSc | MA | BSc | BA | Other",
        "field": "string (e.g., Marketing, Finance, Management)",
        "institution": "string",
        "country": "string",
        "year": "number or null"
    },
    
    "all_degrees": [
        {
            "degree": "string",
            "field": "string",
            "institution": "string",
            "country": "string",
            "year": "number or null"
        }
    ],
    
    "publications_last_5_years": {
        "peer_reviewed_journals": "number",
        "practice_oriented_journals": "number (HBR, SMR, CMR, etc.)",
        "conference_papers": "number",
        "books_chapters": "number",
        "case_studies": "number",
        "total": "number",
        "notable_publications": ["list of 3-5 most significant titles"]
    },
    
    "research_areas": ["list of research specializations"],
    
    "teaching": {
        "courses": [
            {
                "name": "string",
                "level": "bachelor | master | mba | executive | phd",
                "recent": "boolean - taught in last 2 years"
            }
        ],
        "estimated_hours_per_year": "number or null"
    },
    
    "international_experience": {
        "has_international_degree": "boolean",
        "international_degree_countries": ["list of countries"],
        "worked_abroad": "boolean",
        "work_abroad_countries": ["list of countries"],
        "total_years_abroad": "number or null",
        "visiting_positions": [
            {
                "institution": "string",
                "country": "string",
                "year": "number"
            }
        ]
    },
    
    "languages": [
        {
            "language": "string",
            "proficiency": "native | fluent | professional | basic"
        }
    ],
    
    "industry_experience": {
        "total_years": "number",
        "current_consulting": "boolean",
        "board_memberships": ["list of current boards"],
        "industry_roles": [
            {
                "company": "string",
                "role": "string",
                "industry": "string",
                "years": "string (e.g., 2015-2020)"
            }
        ]
    },
    
    "ers_activities": {
        "has_ers_research": "boolean (ethics, responsibility, sustainability research)",
        "has_ers_teaching": "boolean (teaches ethics/sustainability courses)",
        "ers_keywords_found": ["list of relevant terms found in CV"],
        "sustainability_projects": ["any mentioned projects"]
    },
    
    "professional_activities": {
        "journal_editorial": ["list of editorial board memberships"],
        "association_memberships": ["list of professional associations"],
        "conference_organization": ["conferences organized/chaired"]
    },
    
    "cv_summary": "2-3 sentence summary highlighting EFMD-relevant strengths"
}

If a field cannot be determined from the CV, use null.
For counts, use 0 if clearly none, null if unclear.
"""

STUDENT_EXTRACTION_PROMPT = """
You are extracting data from a student CV for EFMD Programme Accreditation.
Extract ALL available information into this exact JSON structure.

CRITICAL FIELDS FOR EFMD:
- Nationality (for diversity metrics - Table 2)
- Prior degree and institution (for Table 3)
- Work experience (for student profile)
- Age (for demographic table)

Return valid JSON only, no markdown:

{
    "full_name": "string",
    "email": "string or null",
    
    "demographics": {
        "nationality": "string (country name)",
        "gender": "male | female | other | null",
        "date_of_birth": "YYYY-MM-DD or null",
        "age": "number or null (calculate if DOB given)"
    },
    
    "prior_education": {
        "highest_degree": {
            "degree": "Bachelor | Master | Other",
            "degree_type": "BSc | BA | BBA | MSc | MA | MBA | Other",
            "field": "string (e.g., Economics, Engineering, Business)",
            "institution": "string",
            "country": "string",
            "year": "number or null",
            "is_business_related": "boolean"
        },
        "all_degrees": [
            {
                "degree_type": "string",
                "field": "string",
                "institution": "string",
                "country": "string",
                "year": "number"
            }
        ]
    },
    
    "work_experience": {
        "total_years": "number",
        "has_management_experience": "boolean",
        "has_international_experience": "boolean",
        "positions": [
            {
                "title": "string",
                "company": "string",
                "industry": "string",
                "country": "string",
                "start_year": "number",
                "end_year": "number or null if current",
                "is_management": "boolean"
            }
        ]
    },
    
    "languages": [
        {
            "language": "string",
            "proficiency": "native | fluent | professional | basic"
        }
    ],
    
    "skills": ["list of technical and soft skills mentioned"],
    
    "international_exposure": {
        "countries_lived_in": ["list of countries"],
        "countries_worked_in": ["list of countries"],
        "exchange_programmes": ["any mentioned exchange/study abroad"]
    },
    
    "cv_summary": "1-2 sentence summary of student profile"
}

If a field cannot be determined from the CV, use null.
"""

ALUMNI_EXTRACTION_PROMPT = """
You are extracting data from an alumni CV for EFMD Programme Accreditation.
Extract ALL available information into this exact JSON structure.

CRITICAL FIELDS FOR EFMD (Table 4 - Graduate Employment):
- Current employment status
- Time from graduation to first job
- Current employer and job title
- Industry and country
- Career progression since graduation

Return valid JSON only, no markdown:

{
    "full_name": "string",
    "email": "string or null",
    "linkedin_url": "string or null",
    
    "graduation": {
        "year": "number",
        "programme": "string (if mentioned)",
        "institution": "string (if mentioned)"
    },
    
    "current_employment": {
        "is_employed": "boolean",
        "employer": "string",
        "job_title": "string",
        "industry": "string",
        "country": "string",
        "is_international": "boolean (working outside home country)",
        "start_date": "YYYY-MM or null",
        "seniority_level": "entry | mid | senior | executive"
    },
    
    "first_job_after_graduation": {
        "employer": "string",
        "job_title": "string",
        "start_date": "YYYY-MM or null",
        "months_to_employment": "number (months between graduation and start)"
    },
    
    "career_progression": {
        "positions_since_graduation": [
            {
                "employer": "string",
                "job_title": "string",
                "industry": "string",
                "country": "string",
                "start_year": "number",
                "end_year": "number or null",
                "seniority_level": "entry | mid | senior | executive"
            }
        ],
        "total_employers_since_graduation": "number",
        "promotions_visible": "number",
        "career_trajectory": "upward | lateral | unclear"
    },
    
    "salary_indication": {
        "disclosed": "boolean",
        "range": "string or null (e.g., 50000-70000 EUR)",
        "currency": "string or null"
    },
    
    "international_career": {
        "worked_abroad": "boolean",
        "countries_worked": ["list of countries"],
        "currently_abroad": "boolean"
    },
    
    "employer_prestige_indicators": {
        "is_fortune_500": "boolean",
        "is_big_4": "boolean (Deloitte, PwC, EY, KPMG)",
        "is_mbb": "boolean (McKinsey, BCG, Bain)",
        "is_major_bank": "boolean",
        "is_multinational": "boolean",
        "company_keywords": ["any prestige indicators found"]
    },
    
    "cv_summary": "1-2 sentence summary highlighting career success"
}

If a field cannot be determined from the CV, use null.
Pay special attention to employment dates to calculate time-to-employment.
"""
