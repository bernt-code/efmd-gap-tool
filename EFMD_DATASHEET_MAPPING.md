# EFMD 16-Page Datasheet: Complete Data Source Mapping

## Your 3 Goals:
1. **Identify** how much of the 16-page report data we can gather automatically
2. **Generate** complete gap report
3. **Generate** improvement process report

---

## THE 16-PAGE DATASHEET: Every Section Mapped

### SECTION 1-5: BASIC INFORMATION (~2 pages)
**Source: Manual Entry (Programme Admin)**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| Institution name, address, website | ❌ Manual | Admin form |
| Programme title, type | ❌ Manual | Admin form |
| EFMD membership status | ❌ Manual | Admin form |
| Head of institution contact | ❌ Manual | Admin form |
| Project leader contact | ❌ Manual | Admin form |

**Coverage: 0% automated — but this is just header info, takes 5 minutes**

---

### SECTION 6: PROGRAMME INFORMATION - TABLE 1 (~1 page)
**Source: Programme Scraper + Manual**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| Year first graduates | 🟡 Partial | Scraper (if on website) |
| Number of graduates (3 years) | ❌ Manual | Admissions office |
| Programme length (months) | ✅ Yes | Scraper |
| Languages of delivery | ✅ Yes | Scraper |
| Campus locations | ✅ Yes | Scraper |
| Delivery modes (FT/PT/Online %) | 🟡 Partial | Scraper |
| Collaborative partners | 🟡 Partial | Scraper |

**Coverage: ~50% automated**

---

### SECTION 6.1-6.4: PROGRAMME DETAILS (~2 pages)
**Source: Programme Scraper**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| Entry requirements | ✅ Yes | Scraper |
| Programme aims/objectives | ✅ Yes | Scraper |
| **Programme ILOs (K/S/A)** | ✅ Yes | Scraper ⭐ CRITICAL |
| Curriculum structure | ✅ Yes | Scraper |
| Course list with ECTS | ✅ Yes | Scraper |
| Strategic issues (3) | ❌ Manual | Admin reflection |

**Coverage: ~80% automated**

---

### SECTION 7: STUDENT INTAKE - TABLE 2 (~1 page)
**Source: Student CVs + Admissions Data**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| Applicants (3 years) | ❌ Manual | Admissions office |
| Offers made | ❌ Manual | Admissions office |
| Offers accepted | ❌ Manual | Admissions office |
| Enrolled students | ❌ Manual | Admissions office |
| **Gender breakdown** | ✅ Yes | Student CVs |
| **Nationality breakdown** | ✅ Yes | Student CVs |
| **Age distribution** | ✅ Yes | Student CVs |
| **Work experience (years)** | ✅ Yes | Student CVs |

**Coverage: ~50% automated (demographics from CVs, counts from admissions)**

---

### SECTION 8: PRIOR EDUCATION - TABLE 3 (~1 page)
**Source: Student CVs**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| **Prior degree type** | ✅ Yes | Student CVs |
| **Prior degree field** | ✅ Yes | Student CVs |
| **Prior institution** | ✅ Yes | Student CVs |
| **Prior institution country** | ✅ Yes | Student CVs |
| Business vs non-business background % | ✅ Yes | Student CVs (computed) |

**Coverage: ~90% automated from Student CVs ⭐**

---

### SECTION 9: GRADUATE EMPLOYMENT - TABLE 4 (~1.5 pages)
**Source: Alumni CVs**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| **Employment rate** | ✅ Yes | Alumni CVs |
| **Time to employment (months)** | ✅ Yes | Alumni CVs |
| **Employer names** | ✅ Yes | Alumni CVs |
| **Job titles** | ✅ Yes | Alumni CVs |
| **Industries** | ✅ Yes | Alumni CVs |
| **Countries** | ✅ Yes | Alumni CVs |
| **Salary ranges** | 🟡 Partial | Alumni CVs (if disclosed) |
| Employed in same org as before | ✅ Yes | Alumni CVs (computed) |
| Working internationally | ✅ Yes | Alumni CVs (computed) |

**Coverage: ~85% automated from Alumni CVs ⭐**

---

### SECTION 10: COHORT PROGRESSION - TABLE 5 (~1 page)
**Source: Student CVs + Admissions**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| Starting cohort size | ❌ Manual | Admissions |
| Still enrolled | 🟡 Partial | Student CV status |
| Graduated | 🟡 Partial | Alumni CV count |
| Withdrawn | ❌ Manual | Admissions |
| Completion rate % | 🟡 Partial | Computed if we have data |

**Coverage: ~40% automated**

---

### SECTION 11-14: FACULTY - TABLES 9, 10, 11, 12 (~4 pages)
**Source: Faculty CVs ⭐ BIGGEST WIN**

#### TABLE 9: Faculty Statistics
| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| **Core faculty count** | ✅ Yes | Faculty CVs |
| **FTE calculation** | ✅ Yes | Faculty CVs (% time) |
| **Rank breakdown (Prof/Assoc/Asst)** | ✅ Yes | Faculty CVs |
| **Gender breakdown** | ✅ Yes | Faculty CVs |
| **Doctorate holders %** | ✅ Yes | Faculty CVs |
| **Doctorate institutions** | ✅ Yes | Faculty CVs |
| **International experience %** | ✅ Yes | Faculty CVs |
| **Nationalities count** | ✅ Yes | Faculty CVs |
| Faculty hired last 3 years | ✅ Yes | Faculty CVs |
| Adjunct/visiting count | ✅ Yes | Faculty CVs |

**Coverage: ~95% automated from Faculty CVs ⭐⭐**

#### TABLE 10: Teaching Allocation
| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| **Courses taught per faculty** | ✅ Yes | Faculty CVs |
| **Teaching hours** | 🟡 Partial | Faculty CVs |
| Core vs adjunct teaching % | ✅ Yes | Computed |

**Coverage: ~80% automated**

#### TABLE 11: Research Output
| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| **Publications (peer-reviewed)** | ✅ Yes | Faculty CVs |
| **Publications (practice-oriented)** | ✅ Yes | Faculty CVs |
| **Conference papers** | ✅ Yes | Faculty CVs |
| **Books/chapters** | ✅ Yes | Faculty CVs |
| **Cases published** | ✅ Yes | Faculty CVs |

**Coverage: ~95% automated from Faculty CVs ⭐⭐**

#### TABLE 12: Practice-Oriented Research
| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| **Consulting activities** | ✅ Yes | Faculty CVs |
| **Industry partnerships** | ✅ Yes | Faculty CVs |
| **Board memberships** | ✅ Yes | Faculty CVs |
| Executive education delivery | 🟡 Partial | Faculty CVs |

**Coverage: ~75% automated**

---

### SECTION 15-18: RESOURCES & QUALITY (~2 pages)
**Source: Manual + Scraper**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| Facilities description | 🟡 Partial | Scraper |
| IT resources | 🟡 Partial | Scraper |
| Library resources | 🟡 Partial | Scraper |
| Quality assurance processes | ❌ Manual | Admin docs |
| Advisory board composition | ❌ Manual | Admin |

**Coverage: ~30% automated**

---

### SECTION 19-20: INTERNATIONAL & CONNECTIONS (~1.5 pages)
**Source: Scraper + CVs**

| Field | Auto-Collect? | Source |
|-------|---------------|--------|
| Exchange partnerships | 🟡 Partial | Scraper |
| **International faculty %** | ✅ Yes | Faculty CVs |
| **International students %** | ✅ Yes | Student CVs |
| Corporate partnerships | 🟡 Partial | Scraper |
| Advisory board | ❌ Manual | Admin |

**Coverage: ~50% automated**

---

## SUMMARY: AUTOMATION POTENTIAL

| Data Source | Pages Covered | Auto % | Method |
|-------------|---------------|--------|--------|
| **Faculty CVs** | ~4 pages | **90%** | CV Parser (Careersorter) |
| **Student CVs** | ~2 pages | **85%** | CV Parser |
| **Alumni CVs** | ~1.5 pages | **85%** | CV Parser |
| **Programme Scraper** | ~3 pages | **70%** | Web scraper |
| **Manual Entry** | ~5.5 pages | 0% | Admin forms |

### TOTAL: ~65-70% of datasheet fields can be auto-collected

---

## THE THREE REPORTS YOU NEED

### REPORT 1: Data Collection Status
"Here's what we have vs what EFMD needs"
- For each table: X of Y fields populated
- Missing data highlighted
- Action items: "Collect 15 more alumni CVs"

### REPORT 2: Gap Analysis
"Here's your readiness score and gaps"
- ILO quality analysis
- Pillar coverage (Int'l, Practice, ERS, Digital)
- Eligibility gate pass/fail
- Risk areas for peer review

### REPORT 3: Improvement Process
"Here's what to fix and how long it takes"
- Prioritized action items
- Timeline estimates
- Resources needed
- Suggested milestones

---

## DATA FLOW ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA COLLECTION LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Faculty CVs ──► CV Parser ──► faculty_cvs table               │
│  (Careersorter)     │         (Tables 9,10,11,12)              │
│                     │                                           │
│  Student CVs ──► CV Parser ──► student_cvs table               │
│  (Careersorter)     │         (Tables 2,3,5)                   │
│                     │                                           │
│  Alumni CVs ───► CV Parser ──► alumni_cvs table                │
│  (Careersorter)     │         (Table 4)                        │
│                     │                                           │
│  Programme URL ─► Scraper ───► programmes + ILOs tables        │
│                     │         (Table 1, Section 6)             │
│                     │                                           │
│  Manual Entry ──► Forms ─────► institutions table              │
│                               (Sections 1-5, misc)             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                     ANALYSIS LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  All Data ──► Gap Analyzer ──► gap_analyses table              │
│                   │                                             │
│                   ├──► REPORT 1: Data Status                   │
│                   ├──► REPORT 2: Gap Analysis                  │
│                   └──► REPORT 3: Improvement Plan              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## WHAT WE'VE BUILT SO FAR

| Component | Status | Covers |
|-----------|--------|--------|
| Supabase schema | ✅ Done | All tables defined |
| EFMD requirements | ✅ Done | 40 requirements seeded |
| Programme scraper | ✅ Done | ILOs, courses, structure |
| Gap analyzer | ✅ Done | Score, pillars, issues |
| Faculty CV parser | 🟡 Exists in Shortlist | Needs EFMD field mapping |
| Student CV parser | 🟡 Exists in Shortlist | Needs EFMD field mapping |
| Alumni CV parser | 🔴 Not built | Similar to Student |
| Report generators | 🔴 Not built | PDF output needed |
| Data status dashboard | 🔴 Not built | Shows collection progress |

---

## NEXT STEPS (Prioritized)

1. **Connect scraper to Supabase** — Test on real programme
2. **Map Careersorter CV fields to EFMD tables** — What's already extractable?
3. **Build Report 2 (Gap Analysis) PDF** — For dean demo
4. **Build Report 1 (Data Status)** — Shows what's missing
5. **Build Report 3 (Improvement Plan)** — Action items
