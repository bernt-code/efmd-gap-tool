"""
EFMD OX Report Requirements Mapping

Maps all 26 sections + tables to:
- What data is needed
- Where to find it (scrape vs upload vs manual)
- Search patterns for web scraping
"""

OX_SECTIONS = {
    # =========================================================================
    # SECTION 1-5: BASIC INSTITUTION INFO
    # =========================================================================
    "1": {
        "name": "Institution name, address, website",
        "fields": {
            "institution_name": {
                "required": True,
                "source": "scrape",
                "search_pages": ["about", "home", "contact"],
                "patterns": ["h1", "title", "og:site_name", "schema.org/Organization"],
            },
            "parent_institution": {
                "required": False,
                "source": "scrape",
                "search_pages": ["about"],
                "patterns": ["university", "parent", "part of"],
            },
            "address": {
                "required": True,
                "source": "scrape",
                "search_pages": ["contact", "about", "footer"],
                "patterns": ["address", "location", "visit us", "schema.org/PostalAddress"],
            },
            "website": {
                "required": True,
                "source": "auto",
                "note": "From school URL input",
            },
        },
    },
    "2": {
        "name": "Programme to be assessed",
        "fields": {
            "programme_title": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "program", "masters", "mba", "bachelor"],
                "patterns": ["h1", "programme name", "degree"],
            },
            "programme_type": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme"],
                "patterns": ["bachelor", "master", "mba", "doctoral", "executive"],
            },
            "online_delivery": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "admission"],
                "patterns": ["online", "blended", "face-to-face", "on-campus"],
            },
        },
    },
    "3": {
        "name": "EFMD membership status",
        "fields": {
            "membership_type": {
                "required": True,
                "source": "manual",
                "options": ["Full member", "Affiliated member"],
            },
            "membership_date": {
                "required": False,
                "source": "manual",
            },
        },
    },
    "4": {
        "name": "Head of institution",
        "fields": {
            "head_name": {
                "required": True,
                "source": "scrape",
                "search_pages": ["leadership", "dean", "management", "about", "team"],
                "patterns": ["dean", "director", "head of school", "principal"],
            },
            "head_title": {
                "required": True,
                "source": "scrape",
                "search_pages": ["leadership", "dean"],
                "patterns": ["dean", "director", "title"],
            },
            "head_email": {
                "required": True,
                "source": "scrape",
                "search_pages": ["leadership", "contact", "staff"],
                "patterns": ["email", "mailto:"],
            },
            "head_phone": {
                "required": True,
                "source": "scrape",
                "search_pages": ["leadership", "contact"],
                "patterns": ["tel:", "phone", "+"],
            },
        },
    },
    "5": {
        "name": "Project leader contact",
        "fields": {
            "leader_name": {"required": True, "source": "manual"},
            "leader_title": {"required": True, "source": "manual"},
            "leader_email": {"required": True, "source": "manual"},
            "leader_phone": {"required": True, "source": "manual"},
        },
    },

    # =========================================================================
    # SECTION 6: PROGRAMME DETAILS + TABLE 1
    # =========================================================================
    "6": {
        "name": "Basic programme details",
        "fields": {
            "programme_description": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "about-programme", "overview"],
                "patterns": ["description", "overview", "about the programme"],
            },
        },
    },
    "table_1": {
        "name": "Basic Programme Information",
        "fields": {
            "first_graduation_year": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "about", "history"],
                "patterns": ["established", "since", "founded", "first cohort"],
            },
            "graduates_t1": {"required": True, "source": "manual"},
            "graduates_t2": {"required": True, "source": "manual"},
            "graduates_t3": {"required": True, "source": "manual"},
            "duration_ft_months": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "admission"],
                "patterns": ["duration", "length", "months", "years", "semesters"],
            },
            "duration_pt_months": {
                "required": False,
                "source": "scrape",
                "search_pages": ["programme"],
                "patterns": ["part-time", "duration"],
            },
            "language_primary": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "admission"],
                "patterns": ["language of instruction", "taught in", "english", "finnish"],
            },
            "delivery_locations": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "campus", "location"],
                "patterns": ["campus", "location", "delivered at"],
            },
        },
    },
    "6.1": {
        "name": "Entry requirements",
        "fields": {
            "entry_requirements": {
                "required": True,
                "source": "scrape",
                "search_pages": ["admission", "apply", "requirements", "eligibility"],
                "patterns": ["requirements", "eligibility", "qualifications", "bachelor", "gmat", "ielts", "toefl"],
            },
        },
    },
    "6.2": {
        "name": "Programme aims/objectives",
        "fields": {
            "programme_aims": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "about", "objectives"],
                "patterns": ["aims", "objectives", "goals", "mission", "purpose"],
            },
        },
    },
    "6.3": {
        "name": "Programme ILOs",
        "fields": {
            "ilos": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "curriculum", "learning-outcomes"],
                "patterns": [
                    "learning outcomes", "ILO", "by the end of", "students will be able to",
                    "knowledge", "skills", "competencies", "graduates will"
                ],
            },
        },
    },
    "6.4": {
        "name": "Strategic concerns",
        "fields": {
            "strategic_concern_1": {
                "required": True,
                "source": "infer",
                "note": "Infer from Dean CV + school strategy page",
            },
            "strategic_concern_2": {"required": True, "source": "infer"},
            "strategic_concern_3": {"required": True, "source": "infer"},
        },
    },

    # =========================================================================
    # SECTION 7-8: STUDENT PROFILES + TABLES 2-4
    # =========================================================================
    "7": {
        "name": "Profile of applicants and student intakes",
        "fields": {},
    },
    "table_2": {
        "name": "Profile of Student Intake",
        "fields": {
            "applicants_t1": {"required": True, "source": "manual"},
            "applicants_t2": {"required": True, "source": "manual"},
            "applicants_t3": {"required": True, "source": "manual"},
            "offers_t1": {"required": True, "source": "manual"},
            "offers_t2": {"required": True, "source": "manual"},
            "offers_t3": {"required": True, "source": "manual"},
            "accepted_t1": {"required": True, "source": "manual"},
            "accepted_t2": {"required": True, "source": "manual"},
            "accepted_t3": {"required": True, "source": "manual"},
            "enrolled_t1": {"required": True, "source": "manual"},
            "enrolled_t2": {"required": True, "source": "manual"},
            "enrolled_t3": {"required": True, "source": "manual"},
            "avg_work_exp_t1": {"required": False, "source": "cvs"},
            "avg_work_exp_t2": {"required": False, "source": "cvs"},
            "avg_work_exp_t3": {"required": False, "source": "cvs"},
        },
    },
    "8": {
        "name": "Current student profile",
        "fields": {},
    },
    "table_3": {
        "name": "Profile of Current Student Enrolment",
        "fields": {
            "enrolled_all_years": {"required": True, "source": "cvs"},
            "female_count": {"required": True, "source": "cvs"},
            "female_pct": {"required": True, "source": "cvs"},
            "international_count": {"required": True, "source": "cvs"},
            "international_pct": {"required": True, "source": "cvs"},
            "nationalities_count": {"required": True, "source": "cvs"},
            "avg_age": {"required": True, "source": "cvs"},
        },
    },
    "table_3a": {
        "name": "Non-national Student Distribution",
        "fields": {
            "top_country_1": {"required": True, "source": "cvs"},
            "top_country_1_count": {"required": True, "source": "cvs"},
            "top_country_2": {"required": True, "source": "cvs"},
            "top_country_2_count": {"required": True, "source": "cvs"},
            "top_country_3": {"required": True, "source": "cvs"},
            "top_country_3_count": {"required": True, "source": "cvs"},
        },
    },
    "table_4": {
        "name": "Graduation Numbers",
        "fields": {
            "graduating_on_time_pct": {"required": True, "source": "cvs"},
            "female_graduates_pct": {"required": True, "source": "cvs"},
            "intl_graduates_pct": {"required": True, "source": "cvs"},
        },
    },

    # =========================================================================
    # SECTION 9-10: INTERNATIONALISATION + TABLE 5
    # =========================================================================
    "9": {
        "name": "Internationalisation overview",
        "fields": {
            "intl_strategy": {
                "required": True,
                "source": "scrape",
                "search_pages": ["international", "global", "partnerships", "exchange"],
                "patterns": ["international strategy", "global", "partnerships", "exchange partners"],
            },
            "partner_institutions": {
                "required": True,
                "source": "scrape",
                "search_pages": ["partners", "exchange", "international"],
                "patterns": ["partner", "agreement", "exchange", "university"],
            },
        },
    },
    "10": {
        "name": "Students' international experience",
        "fields": {},
    },
    "table_5": {
        "name": "International Student Mobility",
        "fields": {
            "outgoing_students_t1": {"required": True, "source": "manual"},
            "outgoing_students_t2": {"required": True, "source": "manual"},
            "outgoing_students_t3": {"required": True, "source": "manual"},
            "incoming_students_t1": {"required": True, "source": "manual"},
            "incoming_students_t2": {"required": True, "source": "manual"},
            "incoming_students_t3": {"required": True, "source": "manual"},
        },
    },

    # =========================================================================
    # SECTION 11-12: CURRICULUM + TABLE 6
    # =========================================================================
    "11": {
        "name": "Organisation of teaching and learning",
        "fields": {
            "teaching_organisation": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "curriculum", "schedule"],
                "patterns": ["schedule", "timetable", "block", "evening", "weekend", "full-time", "part-time"],
            },
        },
    },
    "12": {
        "name": "Curriculum rationale and structure",
        "fields": {
            "curriculum_rationale": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programme", "curriculum", "structure"],
                "patterns": ["curriculum", "structure", "design", "rationale"],
            },
        },
    },
    "table_6": {
        "name": "Course Structure",
        "fields": {
            "courses": {
                "required": True,
                "source": "scrape",
                "search_pages": ["curriculum", "courses", "modules", "programme-structure"],
                "patterns": ["course", "module", "credits", "ECTS", "hours"],
            },
        },
    },

    # =========================================================================
    # SECTION 13-15: MANAGEMENT, QA, DIGITAL
    # =========================================================================
    "13": {
        "name": "Programme management system",
        "fields": {
            "management_structure": {
                "required": True,
                "source": "document",
                "document_types": ["QA Manual", "Organisation Chart", "Governance"],
                "patterns": ["committee", "board", "decision-making", "governance"],
            },
        },
    },
    "14": {
        "name": "Quality assurance system",
        "fields": {
            "qa_system": {
                "required": True,
                "source": "document",
                "document_types": ["QA Manual", "Quality Policy"],
                "patterns": ["quality assurance", "evaluation", "feedback", "review"],
            },
        },
    },
    "15": {
        "name": "Digitalisation",
        "fields": {
            "digital_delivery": {
                "required": True,
                "source": "scrape",
                "search_pages": ["digital", "online", "learning", "facilities"],
                "patterns": ["digital", "online", "platform", "Moodle", "Canvas", "Blackboard"],
            },
            "digital_content": {
                "required": True,
                "source": "scrape",
                "search_pages": ["curriculum", "courses"],
                "patterns": ["digital", "technology", "AI", "analytics", "data"],
            },
            "digital_facilities": {
                "required": True,
                "source": "scrape",
                "search_pages": ["facilities", "campus", "labs"],
                "patterns": ["lab", "trading room", "computer", "Bloomberg", "facility"],
            },
        },
    },

    # =========================================================================
    # SECTION 16-17: PRACTICE & ERS
    # =========================================================================
    "16": {
        "name": "Links with world of practice",
        "fields": {
            "industry_partners": {
                "required": True,
                "source": "scrape",
                "search_pages": ["partners", "careers", "corporate", "industry"],
                "patterns": ["partner", "employer", "company", "corporate"],
            },
            "internship_info": {
                "required": True,
                "source": "scrape",
                "search_pages": ["internship", "practical", "careers"],
                "patterns": ["internship", "placement", "practical training", "work experience"],
            },
            "faculty_practice": {
                "required": True,
                "source": "cvs",
                "note": "From faculty CVs: consulting, boards, industry experience",
            },
        },
    },
    "17": {
        "name": "Ethics, Responsibility and Sustainability (ERS)",
        "fields": {
            "ers_policy": {
                "required": True,
                "source": "scrape",
                "search_pages": ["sustainability", "responsibility", "ethics", "csr", "esg"],
                "patterns": ["sustainability", "ethics", "responsibility", "CSR", "ESG", "PRME"],
            },
            "ers_courses": {
                "required": True,
                "source": "scrape",
                "search_pages": ["curriculum", "courses"],
                "patterns": ["ethics", "sustainability", "CSR", "responsibility"],
            },
            "ers_faculty": {
                "required": True,
                "source": "cvs",
                "note": "Faculty with ERS research/teaching from CVs",
            },
        },
    },

    # =========================================================================
    # SECTION 18-20: STUDENT DEVELOPMENT & CAREERS
    # =========================================================================
    "18": {
        "name": "Personal and professional development",
        "fields": {
            "career_services": {
                "required": True,
                "source": "scrape",
                "search_pages": ["careers", "career-services", "employability"],
                "patterns": ["career", "coaching", "mentoring", "development"],
            },
            "student_support": {
                "required": True,
                "source": "scrape",
                "search_pages": ["student-services", "support", "student-life"],
                "patterns": ["support", "counseling", "wellbeing", "clubs", "societies"],
            },
        },
    },
    "19": {
        "name": "Organisation of supervision",
        "fields": {
            "supervision_process": {
                "required": True,
                "source": "document",
                "document_types": ["Thesis Handbook", "Dissertation Guidelines"],
                "patterns": ["supervision", "thesis", "dissertation", "advisor"],
            },
        },
    },
    "20": {
        "name": "Graduate job placement",
        "fields": {
            "employment_rate": {
                "required": True,
                "source": "scrape",
                "search_pages": ["careers", "alumni", "outcomes", "employment"],
                "patterns": ["employment", "placement", "hired", "job", "%"],
            },
            "time_to_employment": {
                "required": True,
                "source": "scrape",
                "search_pages": ["careers", "outcomes"],
                "patterns": ["months", "weeks", "time to employment", "after graduation"],
            },
            "employers": {
                "required": True,
                "source": "scrape",
                "search_pages": ["careers", "alumni", "employers"],
                "patterns": ["employer", "company", "work at", "hired by"],
            },
            "alumni_outcomes": {
                "required": True,
                "source": "cvs",
                "note": "From alumni CVs: current positions, employers",
            },
        },
    },

    # =========================================================================
    # SECTION 21-22: INSTITUTIONAL & FINANCIALS + TABLE 7
    # =========================================================================
    "21": {
        "name": "Institutional details",
        "fields": {
            "institution_type": {
                "required": True,
                "source": "scrape",
                "search_pages": ["about", "history"],
                "patterns": ["public", "private", "university", "business school"],
            },
            "degree_authority": {
                "required": True,
                "source": "scrape",
                "search_pages": ["about", "accreditation"],
                "patterns": ["ministry", "accredited", "degree awarding", "recognized"],
            },
            "organisation_structure": {
                "required": True,
                "source": "document",
                "document_types": ["Organisation Chart", "Annual Report"],
            },
        },
    },
    "22": {
        "name": "Financial performance",
        "fields": {},
    },
    "table_7": {
        "name": "Financial Performance",
        "fields": {
            "revenue_5yr": {"required": True, "source": "document", "document_types": ["Annual Report"]},
            "expenditure_5yr": {"required": True, "source": "document", "document_types": ["Annual Report"]},
            "surplus_5yr": {"required": True, "source": "document", "document_types": ["Annual Report"]},
            "programme_revenue": {"required": True, "source": "manual"},
        },
    },

    # =========================================================================
    # SECTION 23-24: PROGRAMME PORTFOLIO & FACULTY + TABLES 8-9
    # =========================================================================
    "23": {
        "name": "Degree programme portfolio",
        "fields": {
            "portfolio_strategy": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programmes", "degrees", "study"],
                "patterns": ["programme", "degree", "bachelor", "master", "mba", "doctoral"],
            },
        },
    },
    "table_8": {
        "name": "Degree Programme Portfolio",
        "fields": {
            "all_programmes": {
                "required": True,
                "source": "scrape",
                "search_pages": ["programmes", "degrees", "study"],
                "patterns": ["bachelor", "master", "mba", "doctoral", "executive"],
            },
        },
    },
    "24": {
        "name": "Faculty",
        "fields": {},
    },
    "table_9": {
        "name": "Faculty",
        "fields": {
            "core_faculty_count": {"required": True, "source": "cvs"},
            "core_faculty_fte": {"required": True, "source": "cvs"},
            "full_professors": {"required": True, "source": "cvs"},
            "associate_professors": {"required": True, "source": "cvs"},
            "assistant_professors": {"required": True, "source": "cvs"},
            "female_faculty_pct": {"required": True, "source": "cvs"},
            "phd_rate": {"required": True, "source": "cvs"},
            "foreign_experience_pct": {"required": True, "source": "cvs"},
            "nationalities": {"required": True, "source": "cvs"},
            "adjunct_faculty": {"required": True, "source": "cvs"},
            "visiting_faculty": {"required": True, "source": "cvs"},
        },
    },

    # =========================================================================
    # SECTION 25: PUBLICATIONS + TABLES 10-11
    # =========================================================================
    "25": {
        "name": "Research contribution",
        "fields": {
            "research_overview": {
                "required": True,
                "source": "scrape",
                "search_pages": ["research", "faculty", "publications"],
                "patterns": ["research", "publication", "project", "grant"],
            },
        },
    },
    "table_10": {
        "name": "Publications",
        "fields": {
            "practice_articles": {"required": True, "source": "cvs"},
            "academic_articles": {"required": True, "source": "cvs"},
            "pedagogic_articles": {"required": True, "source": "cvs"},
            "case_studies": {"required": True, "source": "cvs"},
            "conference_papers_academic": {"required": True, "source": "cvs"},
            "conference_papers_professional": {"required": True, "source": "cvs"},
            "other_publications": {"required": True, "source": "cvs"},
        },
    },
    "table_11": {
        "name": "Top 10 Publications",
        "fields": {
            "publications_list": {
                "required": True,
                "source": "cvs",
                "count": 10,
            },
        },
    },

    # =========================================================================
    # SECTION 26: RECOGNITION
    # =========================================================================
    "26": {
        "name": "National and international recognition",
        "fields": {
            "rankings": {
                "required": True,
                "source": "scrape",
                "search_pages": ["rankings", "about", "accreditation"],
                "patterns": ["ranking", "ranked", "FT", "QS", "THE", "Bloomberg", "Economist"],
            },
            "accreditations": {
                "required": True,
                "source": "scrape",
                "search_pages": ["accreditation", "about", "quality"],
                "patterns": ["AACSB", "EQUIS", "AMBA", "EFMD", "accredited", "certified"],
            },
        },
    },
}


def get_scrape_fields():
    """Returns all fields that can be scraped from web"""
    scrape_fields = []
    for section_id, section in OX_SECTIONS.items():
        for field_id, field in section.get("fields", {}).items():
            if field.get("source") == "scrape":
                scrape_fields.append({
                    "section": section_id,
                    "section_name": section["name"],
                    "field": field_id,
                    "search_pages": field.get("search_pages", []),
                    "patterns": field.get("patterns", []),
                })
    return scrape_fields


def get_cv_fields():
    """Returns all fields that need CV uploads"""
    cv_fields = []
    for section_id, section in OX_SECTIONS.items():
        for field_id, field in section.get("fields", {}).items():
            if field.get("source") == "cvs":
                cv_fields.append({
                    "section": section_id,
                    "section_name": section["name"],
                    "field": field_id,
                })
    return cv_fields


def get_document_fields():
    """Returns all fields that need document uploads"""
    doc_fields = []
    for section_id, section in OX_SECTIONS.items():
        for field_id, field in section.get("fields", {}).items():
            if field.get("source") == "document":
                doc_fields.append({
                    "section": section_id,
                    "section_name": section["name"],
                    "field": field_id,
                    "document_types": field.get("document_types", []),
                })
    return doc_fields


def get_manual_fields():
    """Returns all fields that need manual input"""
    manual_fields = []
    for section_id, section in OX_SECTIONS.items():
        for field_id, field in section.get("fields", {}).items():
            if field.get("source") == "manual":
                manual_fields.append({
                    "section": section_id,
                    "section_name": section["name"],
                    "field": field_id,
                })
    return manual_fields


if __name__ == "__main__":
    print("=== SCRAPE FIELDS ===")
    scrape = get_scrape_fields()
    print(f"Total: {len(scrape)} fields")
    for f in scrape[:5]:
        print(f"  {f['section']}.{f['field']}: {f['patterns'][:3]}")
    
    print("\n=== CV FIELDS ===")
    cvs = get_cv_fields()
    print(f"Total: {len(cvs)} fields")
    
    print("\n=== DOCUMENT FIELDS ===")
    docs = get_document_fields()
    print(f"Total: {len(docs)} fields")
    
    print("\n=== MANUAL FIELDS ===")
    manual = get_manual_fields()
    print(f"Total: {len(manual)} fields")
