"""
Test the extraction logic with the page content we already fetched
"""

from school_crawler import CrawlResult, print_crawl_result, calculate_efmd_readiness, print_readiness_report
import re

# This is the text from the page we fetched earlier
PAGE_TEXT = """
A growing and internationalising university | University of Vaasa

A growing and internationalising university

This page compiles the key figures related to our university's research, education, personnel, and sustainability.

Research

Our research is internationally high-quality, responding global societal challenges and informing both policy and practice. We focus on sustainable business, energy and society. We want to engage our partners in industry and society in our research activities.

In 2024, the total number of publications was 774. This represents an increase compared to 2023, when there were a total of 756 publications.

In total, €6,322,937 of competitive research funding was spent in 2024. This represents a 9% increase from 2023. The amount of international competitive research funding increased by 16%, and the amount of other competitive research funding increased by 7% compared to 2023.

Education

In 2024, a total of 712 students completed their master's degrees, which was 25 percent more than the previous year and a record in the university's history. In addition, during the year 2024, the university awarded 526 bachelor's degrees and 22 doctoral degrees. The number of bachelor's degrees awarded increased by 6%.

In 2024, the University of Vaasa had a total of 6,419 students. The number of basic degree students was 6,109, and the number of doctoral students was 310. The number of international degree students increased. There were 621 international degree students, which is 11% of all basic degree students.

In 2025, 8007 applications were received for Bachelor's programmes, which is 9.3% more than last year. Finnish-language Master's programmes received 2682 applications, 29.3% more than last year.

Our graduates enjoy excellent employment opportunities, and employers hold degrees earned from the University of Vaasa in high regard.

Personnel

At the end of 2024, the number of personnel was 650.

The proportion of international personnel is 25 percent of the total personnel. The proportion of employed international personnel in teaching and research positions is approximately 36 percent. Our employees represent 47 different nationalities.

Sustainability and responsibility

Our dedication to sustainability runs deep, with a commitment to incorporating the social, economic and ecological dimensions of sustainability into all aspects of our work.

The carbon footprint refers to the climate emissions caused by human activity. In 2024, the University of Vaasa's carbon footprint was approximately 3.18 thousand tonnes of CO2 equivalent greenhouse gases.

Wolffintie 32
FI-65200 Vaasa PL 700
65101 Vaasa, Finland

+358 29 449 8000

AACSB accredited
EFMD Master Accredited
FINEEC audited
"""


def extract_from_text(text: str) -> CrawlResult:
    """Extract EFMD data from text"""
    result = CrawlResult(school_url="https://www.uwasa.fi/en")
    result.pages_crawled = 1
    
    # Institution name
    result.institution_name = "University of Vaasa"
    
    # Address
    addr_match = re.search(r'(Wolffintie\s+\d+[^+]+Finland)', text, re.S)
    if addr_match:
        result.address = ' '.join(addr_match.group(1).split())
    
    # Phone
    phone_match = re.search(r'\+\d{3}\s*\d+\s*\d+\s*\d+', text)
    if phone_match:
        result.phone = phone_match.group()
    
    # Publications
    pub_match = re.search(r'total number of publications was (\d+)', text, re.I)
    if pub_match:
        result.publications_total = int(pub_match.group(1))
    
    # Research funding
    funding_match = re.search(r'€([\d,]+)', text)
    if funding_match:
        result.research_funding = funding_match.group(1)
    
    # Master's graduates
    master_match = re.search(r'(\d+) students completed their master', text, re.I)
    if master_match:
        result.master_graduates = int(master_match.group(1))
    
    # Bachelor's graduates
    bachelor_match = re.search(r'(\d+) bachelor.s degrees', text, re.I)
    if bachelor_match:
        result.bachelor_graduates = int(bachelor_match.group(1))
    
    # Doctoral graduates
    doctoral_match = re.search(r'(\d+) doctoral degrees', text, re.I)
    if doctoral_match:
        result.doctoral_graduates = int(doctoral_match.group(1))
    
    # Total students
    students_match = re.search(r'total of ([\d,]+) students', text, re.I)
    if students_match:
        result.total_students = int(students_match.group(1).replace(',', ''))
    
    # International students
    intl_students_match = re.search(r'(\d+) international degree students', text, re.I)
    if intl_students_match:
        result.international_students = int(intl_students_match.group(1))
    
    intl_pct_match = re.search(r'(\d+)% of all basic degree students', text, re.I)
    if intl_pct_match:
        result.international_students_pct = float(intl_pct_match.group(1))
    
    # Applicants
    bachelor_app_match = re.search(r'(\d+) applications.*Bachelor', text, re.I)
    if bachelor_app_match:
        result.bachelor_applicants = int(bachelor_app_match.group(1))
    
    master_app_match = re.search(r'Master.*?(\d+) applications', text, re.I)
    if not master_app_match:
        master_app_match = re.search(r'(\d+) applications.*Master', text, re.I)
    if master_app_match:
        result.master_applicants = int(master_app_match.group(1))
    
    # Personnel
    personnel_match = re.search(r'number of personnel was (\d+)', text, re.I)
    if personnel_match:
        result.total_personnel = int(personnel_match.group(1))
    
    # International personnel
    intl_personnel_match = re.search(r'international personnel is (\d+) percent', text, re.I)
    if intl_personnel_match:
        result.international_personnel_pct = float(intl_personnel_match.group(1))
    
    # Nationalities
    nat_match = re.search(r'(\d+) different nationalities', text, re.I)
    if nat_match:
        result.nationalities_count = int(nat_match.group(1))
    
    # Carbon footprint
    carbon_match = re.search(r'carbon footprint was approximately ([\d.]+) thousand tonnes', text, re.I)
    if carbon_match:
        result.carbon_footprint = carbon_match.group(1) + " thousand tonnes CO2"
    
    # Sustainability
    if 'sustainability' in text.lower():
        result.sustainability_info = "Sustainability content found"
    
    # Accreditations
    for acc in ['AACSB', 'EFMD', 'EQUIS', 'AMBA', 'FINEEC']:
        if acc in text:
            result.accreditations.append(acc)
    
    # Research focus
    if 'sustainable business' in text.lower():
        result.research_focus_areas.append('Sustainable Business')
    if 'energy' in text.lower():
        result.research_focus_areas.append('Energy')
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("TESTING EXTRACTION FROM UNIVERSITY OF VAASA PAGE")
    print("=" * 70)
    
    result = extract_from_text(PAGE_TEXT)
    print_crawl_result(result)
    
    readiness = calculate_efmd_readiness(result)
    print_readiness_report(result, readiness)
