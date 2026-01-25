"""
EFMD School Website Crawler

Crawls a business school website to extract data for the OX Report.
"""

import re
import json
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, field
from typing import Optional
from ox_requirements import OX_SECTIONS, get_scrape_fields

# These would be used with real network access
# import requests
# from bs4 import BeautifulSoup


@dataclass
class CrawlResult:
    """Result of crawling a school website"""
    school_url: str
    programme_url: Optional[str] = None
    pages_crawled: int = 0
    found_data: dict = field(default_factory=dict)
    missing_data: dict = field(default_factory=dict)
    partial_data: dict = field(default_factory=dict)
    coverage_pct: float = 0.0


# Keywords to find specific page types
PAGE_TYPE_KEYWORDS = {
    "about": ["about", "om-oss", "about-us", "who-we-are", "history"],
    "contact": ["contact", "kontakt", "reach-us", "find-us", "location"],
    "leadership": ["leadership", "dean", "management", "team", "staff", "people", "organization"],
    "programme": ["programme", "program", "masters", "master", "mba", "bachelor", "degree"],
    "curriculum": ["curriculum", "courses", "modules", "structure", "study-plan"],
    "admission": ["admission", "apply", "requirements", "eligibility", "how-to-apply"],
    "international": ["international", "global", "exchange", "partners", "mobility"],
    "careers": ["careers", "career", "employability", "alumni", "employment", "placement"],
    "research": ["research", "publications", "faculty-research"],
    "facilities": ["facilities", "campus", "labs", "infrastructure"],
    "rankings": ["rankings", "accreditation", "recognition", "quality"],
    "sustainability": ["sustainability", "responsibility", "ethics", "csr", "esg", "prme"],
    "student": ["student", "student-life", "student-services", "clubs"],
    "news": ["news", "press", "media", "announcements"],
}


def classify_page_type(url: str, title: str = "", content: str = "") -> list:
    """Classify what type of page this is based on URL and content"""
    url_lower = url.lower()
    title_lower = title.lower()
    
    types = []
    for page_type, keywords in PAGE_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in url_lower or kw in title_lower:
                types.append(page_type)
                break
    
    return types if types else ["other"]


def extract_institution_name(soup) -> Optional[str]:
    """Extract institution name from page"""
    # Try meta tags first
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        return og_site["content"]
    
    # Try schema.org
    schema = soup.find("script", type="application/ld+json")
    if schema:
        try:
            data = json.loads(schema.string)
            if isinstance(data, dict) and data.get("name"):
                return data["name"]
        except:
            pass
    
    # Try title tag
    title = soup.find("title")
    if title:
        # Usually "Page Name | Institution Name" or "Institution Name - Page"
        text = title.get_text()
        for sep in ["|", "-", "–", "—"]:
            if sep in text:
                parts = text.split(sep)
                # Return the longer part (usually the institution name)
                return max(parts, key=len).strip()
        return text.strip()
    
    return None


def extract_address(soup) -> Optional[str]:
    """Extract address from page"""
    # Look for schema.org PostalAddress
    schema = soup.find("script", type="application/ld+json")
    if schema:
        try:
            data = json.loads(schema.string)
            if isinstance(data, dict):
                addr = data.get("address", {})
                if isinstance(addr, dict):
                    parts = [
                        addr.get("streetAddress", ""),
                        addr.get("postalCode", ""),
                        addr.get("addressLocality", ""),
                        addr.get("addressCountry", ""),
                    ]
                    return ", ".join(p for p in parts if p)
        except:
            pass
    
    # Look for address tag or class
    address_el = soup.find("address")
    if address_el:
        return address_el.get_text(separator=" ").strip()
    
    # Look for common address patterns
    for cls in ["address", "contact-address", "location"]:
        el = soup.find(class_=re.compile(cls, re.I))
        if el:
            return el.get_text(separator=" ").strip()
    
    return None


def extract_dean_info(soup) -> dict:
    """Extract dean/head of institution info"""
    result = {}
    
    # Look for leadership sections
    leadership = soup.find(["section", "div"], class_=re.compile(r"leadership|dean|management", re.I))
    if not leadership:
        leadership = soup
    
    # Look for dean/director title
    dean_patterns = [
        r"dean[:\s]+([^,\n]+)",
        r"director[:\s]+([^,\n]+)",
        r"head of school[:\s]+([^,\n]+)",
    ]
    
    text = leadership.get_text()
    for pattern in dean_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            result["name"] = match.group(1).strip()
            break
    
    # Look for email
    email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", text)
    if email_match:
        result["email"] = email_match.group()
    
    # Look for phone
    phone_match = re.search(r"\+?[\d\s\-()]{10,}", text)
    if phone_match:
        result["phone"] = phone_match.group().strip()
    
    return result


def extract_programmes(soup) -> list:
    """Extract list of programmes offered"""
    programmes = []
    
    # Look for programme listings
    for link in soup.find_all("a", href=re.compile(r"programme|program|master|bachelor|mba", re.I)):
        text = link.get_text().strip()
        if text and len(text) > 5:
            programmes.append({
                "name": text,
                "url": link.get("href"),
            })
    
    return programmes


def extract_courses(soup) -> list:
    """Extract course/module list from curriculum page"""
    courses = []
    
    # Look for tables with courses
    tables = soup.find_all("table")
    for table in tables:
        headers = [th.get_text().strip().lower() for th in table.find_all("th")]
        if any(h in ["course", "module", "credits", "ects"] for h in headers):
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if cells:
                    course = {
                        "name": cells[0].get_text().strip(),
                    }
                    # Try to find credits
                    for i, cell in enumerate(cells[1:], 1):
                        text = cell.get_text().strip()
                        if re.match(r"\d+", text):
                            course["credits"] = text
                            break
                    courses.append(course)
    
    # Look for list items with course names
    if not courses:
        for ul in soup.find_all(["ul", "ol"], class_=re.compile(r"course|module|curriculum", re.I)):
            for li in ul.find_all("li"):
                text = li.get_text().strip()
                if text:
                    courses.append({"name": text})
    
    return courses


def extract_ilos(soup) -> list:
    """Extract Intended Learning Outcomes"""
    ilos = []
    
    # Look for ILO section
    ilo_section = soup.find(["section", "div"], class_=re.compile(r"learning.?outcome|ilo", re.I))
    if not ilo_section:
        # Look for headers
        for h in soup.find_all(["h2", "h3", "h4"]):
            if re.search(r"learning outcome|what you.?ll learn|graduate.?will", h.get_text(), re.I):
                ilo_section = h.find_next(["ul", "ol", "div"])
                break
    
    if ilo_section:
        # Extract from list
        for li in ilo_section.find_all("li"):
            text = li.get_text().strip()
            if text:
                ilos.append(text)
        
        # If no list items, look for paragraphs
        if not ilos:
            for p in ilo_section.find_all("p"):
                text = p.get_text().strip()
                if text and len(text) > 20:
                    ilos.append(text)
    
    return ilos


def extract_rankings(soup) -> list:
    """Extract rankings and accreditations"""
    rankings = []
    
    text = soup.get_text()
    
    # Look for FT ranking
    ft_match = re.search(r"financial times.*?(\d+)|(#\d+).*?financial times", text, re.I)
    if ft_match:
        rankings.append({"source": "Financial Times", "rank": ft_match.group(1) or ft_match.group(2)})
    
    # Look for QS ranking
    qs_match = re.search(r"qs.*?(\d+)|(#\d+).*?qs", text, re.I)
    if qs_match:
        rankings.append({"source": "QS", "rank": qs_match.group(1) or qs_match.group(2)})
    
    # Look for accreditations
    accred_patterns = ["AACSB", "EQUIS", "AMBA", "EFMD"]
    for acc in accred_patterns:
        if re.search(rf"\b{acc}\b", text, re.I):
            rankings.append({"type": "accreditation", "name": acc})
    
    return rankings


def extract_faculty_list(soup) -> list:
    """Extract faculty member names from staff page"""
    faculty = []
    
    # Look for staff cards/lists
    for card in soup.find_all(["div", "article"], class_=re.compile(r"staff|faculty|person|member|card", re.I)):
        name_el = card.find(["h2", "h3", "h4", "strong", "a"])
        if name_el:
            name = name_el.get_text().strip()
            if name and len(name.split()) >= 2:  # At least first and last name
                person = {"name": name}
                
                # Try to get title
                title_el = card.find(class_=re.compile(r"title|position|role", re.I))
                if title_el:
                    person["title"] = title_el.get_text().strip()
                
                faculty.append(person)
    
    return faculty


def extract_entry_requirements(soup) -> dict:
    """Extract admission requirements"""
    requirements = {}
    text = soup.get_text().lower()
    
    # Bachelor/degree requirement
    if "bachelor" in text:
        requirements["degree"] = "Bachelor's degree required"
    
    # Work experience
    exp_match = re.search(r"(\d+)\s*years?\s*(of\s*)?(work|professional)\s*experience", text)
    if exp_match:
        requirements["work_experience"] = f"{exp_match.group(1)} years"
    
    # Language requirements
    for test in ["ielts", "toefl", "cambridge"]:
        if test in text:
            score_match = re.search(rf"{test}[:\s]*(\d+\.?\d*)", text)
            if score_match:
                requirements[test.upper()] = score_match.group(1)
    
    # GMAT/GRE
    for test in ["gmat", "gre"]:
        if test in text:
            score_match = re.search(rf"{test}[:\s]*(\d+)", text)
            if score_match:
                requirements[test.upper()] = score_match.group(1)
    
    return requirements


def extract_employment_stats(soup) -> dict:
    """Extract employment/career statistics"""
    stats = {}
    text = soup.get_text()
    
    # Employment rate
    emp_match = re.search(r"(\d+)%\s*(of\s*)?(graduates?\s*)?(employed|found.*?job|hired)", text, re.I)
    if emp_match:
        stats["employment_rate"] = f"{emp_match.group(1)}%"
    
    # Time to employment
    time_match = re.search(r"within\s*(\d+)\s*(months?|weeks?)", text, re.I)
    if time_match:
        stats["time_to_employment"] = f"{time_match.group(1)} {time_match.group(2)}"
    
    # Average salary
    salary_match = re.search(r"(€|EUR|\$|USD)\s*(\d{2,3}[,.\d]*)", text)
    if salary_match:
        stats["average_salary"] = f"{salary_match.group(1)}{salary_match.group(2)}"
    
    return stats


def generate_coverage_report(found: dict, ox_sections: dict) -> dict:
    """Generate a report showing what was found vs what's missing"""
    report = {
        "found": [],
        "partial": [],
        "missing": [],
        "by_source": {
            "scrape": {"found": 0, "total": 0},
            "cvs": {"found": 0, "total": 0},
            "document": {"found": 0, "total": 0},
            "manual": {"found": 0, "total": 0},
        }
    }
    
    for section_id, section in ox_sections.items():
        for field_id, field_config in section.get("fields", {}).items():
            full_key = f"{section_id}.{field_id}"
            source = field_config.get("source", "unknown")
            
            if source in report["by_source"]:
                report["by_source"][source]["total"] += 1
            
            if full_key in found and found[full_key]:
                report["found"].append({
                    "key": full_key,
                    "section": section["name"],
                    "field": field_id,
                    "value": found[full_key],
                    "source": source,
                })
                if source in report["by_source"]:
                    report["by_source"][source]["found"] += 1
            else:
                report["missing"].append({
                    "key": full_key,
                    "section": section["name"],
                    "field": field_id,
                    "source": source,
                    "how_to_get": _get_how_to_get(field_config),
                })
    
    # Calculate coverage percentage
    total = len(report["found"]) + len(report["missing"])
    report["coverage_pct"] = round(len(report["found"]) / total * 100, 1) if total > 0 else 0
    
    return report


def _get_how_to_get(field_config: dict) -> str:
    """Generate hint for how to get missing data"""
    source = field_config.get("source")
    
    if source == "scrape":
        pages = field_config.get("search_pages", [])
        return f"Check website pages: {', '.join(pages)}"
    elif source == "cvs":
        return "Upload CVs (faculty/student/alumni)"
    elif source == "document":
        docs = field_config.get("document_types", [])
        return f"Upload document: {', '.join(docs)}"
    elif source == "manual":
        return "Input manually"
    elif source == "infer":
        return "Inferred from other data"
    else:
        return "Unknown source"


# =============================================================================
# MOCK CRAWLER FOR TESTING (without network)
# =============================================================================

def mock_crawl_vaasa() -> CrawlResult:
    """Mock crawl result for University of Vaasa for testing"""
    
    result = CrawlResult(
        school_url="https://www.uwasa.fi/en",
        programme_url="https://www.uwasa.fi/en/education/masters/finance",
        pages_crawled=15,
    )
    
    # Simulated data that would be found on Vaasa's website
    result.found_data = {
        # Section 1: Institution
        "1.institution_name": "University of Vaasa",
        "1.parent_institution": None,
        "1.address": "Wolffintie 34, 65200 Vaasa, Finland",
        "1.website": "https://www.uwasa.fi",
        
        # Section 2: Programme
        "2.programme_title": "Master's Programme in Finance",
        "2.programme_type": "Master",
        "2.online_delivery": "Face-to-face",
        
        # Section 4: Head
        "4.head_name": "Professor Annukka Jokipii",
        "4.head_title": "Dean, School of Accounting and Finance",
        "4.head_email": None,  # Not always public
        "4.head_phone": None,
        
        # Section 6: Programme basics
        "6.programme_description": "The Master's Programme in Finance provides students with in-depth knowledge of financial markets, investment analysis, and corporate finance.",
        "table_1.duration_ft_months": "24",
        "table_1.language_primary": "English (100%)",
        "table_1.delivery_locations": "Vaasa, Finland",
        
        # Section 6.1: Entry requirements
        "6.1.entry_requirements": "Bachelor's degree in business, economics or related field. IELTS 6.5 or equivalent.",
        
        # Section 6.2: Aims
        "6.2.programme_aims": "To educate financial professionals who can analyze and manage financial risks in international business environments.",
        
        # Section 6.3: ILOs - PARTIAL
        "6.3.ilos": [
            "Apply quantitative methods to financial analysis",
            "Evaluate investment opportunities and portfolio strategies",
            "Analyze corporate financial decisions",
        ],
        
        # Section 9: International
        "9.intl_strategy": "The programme has partnerships with over 100 universities worldwide.",
        "9.partner_institutions": ["Stockholm School of Economics", "Copenhagen Business School", "Erasmus University Rotterdam"],
        
        # Section 11: Teaching
        "11.teaching_organisation": "Full-time, semester-based with lectures, seminars and project work",
        
        # Section 12 + Table 6: Curriculum
        "12.curriculum_rationale": "The curriculum combines theoretical foundations with practical applications.",
        "table_6.courses": [
            {"name": "Financial Markets and Institutions", "credits": "5"},
            {"name": "Investment Analysis", "credits": "5"},
            {"name": "Corporate Finance", "credits": "5"},
            {"name": "Risk Management", "credits": "5"},
            {"name": "Financial Econometrics", "credits": "5"},
            {"name": "Master's Thesis", "credits": "30"},
        ],
        
        # Section 15: Digital
        "15.digital_delivery": "Moodle learning platform, video lectures",
        "15.digital_content": "Courses include Bloomberg terminal training, Excel financial modeling",
        "15.digital_facilities": "Bloomberg Lab, Computer labs",
        
        # Section 18: Student development
        "18.career_services": "Career services include CV workshops, employer events, internship placements",
        "18.student_support": "Student union, tutoring, counseling services",
        
        # Section 20: Employment
        "20.employment_rate": "92%",
        "20.time_to_employment": "3 months",
        "20.employers": ["Nordea", "OP Financial Group", "KPMG", "PwC"],
        
        # Section 21: Institution type
        "21.institution_type": "Public university",
        "21.degree_authority": "Finnish Ministry of Education",
        
        # Section 23 + Table 8: Portfolio
        "23.portfolio_strategy": "Focus on business, management, economics and technology",
        "table_8.all_programmes": [
            {"type": "Bachelor", "name": "Business Studies"},
            {"type": "Master", "name": "Finance"},
            {"type": "Master", "name": "Strategic Business Development"},
            {"type": "Doctoral", "name": "Accounting and Finance"},
        ],
        
        # Section 25: Research
        "25.research_overview": "Active research in financial markets, corporate governance, and sustainable finance",
        
        # Section 26: Rankings
        "26.rankings": ["Eduniversal Top 100 Business Schools"],
        "26.accreditations": ["AACSB"],
    }
    
    return result


def print_coverage_report(report: dict):
    """Print a nice coverage report"""
    print("=" * 70)
    print("OX REPORT DATA COVERAGE")
    print("=" * 70)
    
    print(f"\nOVERALL COVERAGE: {report['coverage_pct']}%")
    print()
    
    print("BY SOURCE:")
    for source, counts in report["by_source"].items():
        pct = round(counts["found"] / counts["total"] * 100) if counts["total"] > 0 else 0
        print(f"  {source:12} {counts['found']:2}/{counts['total']:2} ({pct}%)")
    
    print()
    print("=" * 70)
    print("✅ FOUND DATA")
    print("=" * 70)
    for item in report["found"][:20]:  # Show first 20
        value = str(item["value"])[:50] + "..." if len(str(item["value"])) > 50 else item["value"]
        print(f"  {item['key']:30} = {value}")
    if len(report["found"]) > 20:
        print(f"  ... and {len(report['found']) - 20} more")
    
    print()
    print("=" * 70)
    print("❌ MISSING DATA")
    print("=" * 70)
    for item in report["missing"][:20]:
        print(f"  {item['key']:30} → {item['how_to_get']}")
    if len(report["missing"]) > 20:
        print(f"  ... and {len(report['missing']) - 20} more")


if __name__ == "__main__":
    # Test with mock Vaasa data
    print("Testing crawler with University of Vaasa mock data...")
    print()
    
    crawl_result = mock_crawl_vaasa()
    
    report = generate_coverage_report(crawl_result.found_data, OX_SECTIONS)
    print_coverage_report(report)
