# EFMD Programme Accreditation Gap Analysis Tool

AI-powered data collection and gap analysis for EFMD Programme Accreditation.

## What It Does

### Three CV Collection Pipelines
Just like Shortlist - collect CVs, parse with Claude, store in Supabase:

| Pipeline | Target | Fills EFMD Tables |
|----------|--------|-------------------|
| `/upload/faculty/{institution_id}` | 25+ faculty | Tables 9, 10, 11, 12 |
| `/upload/student/{programme_id}` | 50+ students | Tables 2, 3, 5 |
| `/upload/alumni/{programme_id}` | 40+ alumni | Table 4 |

### Smart Selection (Cherry-Picking)
Every CV is scored against EFMD criteria. The system recommends the **optimal subset** for submission:

- **Faculty:** Maximize PhD rate, publications, international experience
- **Students:** Maximize nationality diversity, work experience
- **Alumni:** Maximize employment rate, employer prestige, career progression

### Three Reports
1. **Collection Status:** Progress bars, what's missing
2. **Gap Analysis:** Readiness score, pillar coverage, ILO issues
3. **Improvement Plan:** Prioritized actions, timeline to readiness

## Quick Start

```bash
# 1. Clone and setup
cd efmd-gap-tool
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
# Run sql/003_scoring_fields.sql in Supabase SQL Editor
# (001 and 002 already done)

# 4. Start the tool
chmod +x start.sh
./start.sh
```

## Environment Variables

```env
# Supabase
SUPABASE_URL=https://bkhvztyvfkqzqqtoxxxi.supabase.co
SUPABASE_KEY=your_service_role_key

# AI Services
ANTHROPIC_API_KEY=your_claude_key
GOOGLE_API_KEY=your_gemini_key
```

## API Endpoints

### CV Upload
```bash
# Faculty
curl -X POST "http://localhost:8002/upload/faculty/{institution_id}" \
  -F "file=@cv.pdf"

# Student
curl -X POST "http://localhost:8002/upload/student/{programme_id}" \
  -F "file=@cv.pdf"

# Alumni
curl -X POST "http://localhost:8002/upload/alumni/{programme_id}" \
  -F "file=@cv.pdf"
```

### Get Top Selections (for Base Room)
```bash
# Top 25 faculty for submission
GET /faculty/{institution_id}/top

# Top 30 alumni for submission  
GET /alumni/{programme_id}/top

# Student diversity metrics
GET /students/{programme_id}/diversity
```

### Status & Reports
```bash
GET /programme/{id}/status           # Collection progress
GET /programme/{id}/gap-report       # Gap analysis
GET /programme/{id}/improvement-report  # Action plan
```

## File Structure

```
efmd-gap-tool/
├── api/
│   └── main.py              # FastAPI backend
├── frontend/
│   └── app.py               # Streamlit UI
├── src/
│   ├── cv_scoring.py        # Scoring algorithms
│   └── ingestion_service.py # Full pipeline
├── prompts/
│   └── cv_extraction_prompts.py
├── reports/
│   └── report_generators.py
├── sql/
│   ├── 001_schema.sql       # ✅ Run in Supabase
│   ├── 002_seed_requirements.sql  # ✅ Run in Supabase
│   └── 003_scoring_fields.sql     # 🔴 Run this next!
├── efmd_scraper_v2.py       # Programme website scraper
├── requirements.txt
├── .env.example
├── start.sh
└── README.md
```

## Scoring Logic

### Faculty Score (0-100)
| Criteria | Points |
|----------|--------|
| Doctoral degree | +20 |
| 5+ publications (5yr) | +15 |
| 3+ peer-reviewed | +10 |
| International experience | +10 |
| Worked abroad | +5 |
| Industry experience | +8 |
| Active consulting | +4 |
| ERS research/teaching | +5 |

**Recommended threshold:** 45+ points

### Alumni Score (0-100)
| Criteria | Points |
|----------|--------|
| Employed | +15 |
| Job within 3 months | +15 |
| Job within 6 months | +10 |
| Big4/MBB employer | +20 |
| Fortune 500 | +15 |
| Multinational | +10 |
| Executive level | +15 |
| Senior level | +12 |
| Working abroad | +10 |

**Recommended threshold:** 40+ points

## Integration with Careersorter

This tool uses the same architecture as Shortlist:
- Same Claude parsing (different prompts)
- Same Gemini embeddings (768 dimensions)
- Same Supabase + pgvector

Faculty/Student/Alumni CVs collected here can feed into Careersorter's formatting engine if needed.

## Database Schema

### Core Tables
- `institutions` - Schools
- `programmes` - Degree programmes  
- `faculty_cvs` - Faculty data + scoring
- `student_cvs` - Student data + scoring
- `alumni_cvs` - Alumni data + scoring

### Analysis Tables
- `programme_ilos` - Scraped ILOs
- `programme_courses` - Course structure
- `efmd_requirements` - 40 EFMD criteria
- `gap_analyses` - Analysis results

## Roadmap

- [x] Supabase schema
- [x] CV scoring algorithms
- [x] FastAPI endpoints
- [x] Streamlit frontend
- [x] Three report generators
- [ ] PDF export for reports
- [ ] Fly.io deployment
- [ ] Batch CV import
- [ ] Email notifications for collection

## License

Proprietary - Allsorter/Edtech Solutions
