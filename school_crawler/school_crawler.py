"""
EFMD School Website Crawler
===========================

Crawls a school website and extracts ALL data relevant to OX Report.
Simple approach: crawl everything, extract what we find.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set
from collections import defaultdict


@dataclass
class CrawlResult:
    """All data extracted from a school website"""
    school_url: str
    pages_crawled: int = 0
    
    # Institution basics
    institution_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    
    # Leadership
    dean_name: Optional[str] = None
    dean_title: Optional[str] = None
    
    # Numbers
    total_students: Optional[int] = None
    international_students: Optional[int] = None
    international_students_pct: Optional[float] = None
    bachelor_students: Optional[int] = None
    master_students: Optional[int] = None
    doctoral_students: Optional[int] = None
    
    # Graduates
    bachelor_graduates: Optional[int] = None
    master_graduates: Optional[int] = None
    doctoral_graduates: Optional[int] = None
    
    # Applicants
    bachelor_applicants: Optional[int] = None
    master_applicants: Optional[int] = None
    
    # Personnel
    total_personnel: Optional[int] = None
    international_personnel_pct: Optional[float] = None
    nationalities_count: Optional[int] = None
    
    # Research
    publications_total: Optional[int] = None
    research_funding: Optional[str] = None
    
    # Employment
    employment_rate: Optional[float] = None
    
    # Accreditations
    accreditations: List[str] = field(default_factory=list)
    
    # Programmes found
    programmes: List[Dict] = field(default_factory=list)
    
    # Faculty found
    faculty: List[Dict] = field(default_factory=list)
    
    # Partners
    international_partners: List[str] = field(default_factory=list)
    
    # ERS/Sustainability
    sustainability_info: Optional[str] = None
    carbon_footprint: Optional[str] = None
    
    # Strategy
    strategy_text: Optional[str] = None
    research_focus_areas: List[str] = field(default_factory=list)
    
    # Raw page data for searching
    all_pages: Dict[str, str] = field(default_factory=dict)


class SchoolCrawler:
    """Crawls a school website and extracts EFMD-relevant data"""
    
    def __init__(self, base_url: str, max_pages: int = 100, delay: float = 0.5):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.delay = delay
        self.visited: Set[str] = set()
        self.result = CrawlResult(school_url=base_url)
        
        # Keywords to prioritize in crawl
        self.priority_keywords = [
            'about', 'university', 'school', 'faculty', 'staff', 'people',
            'research', 'publication', 'study', 'education', 'programme', 'program',
            'admission', 'apply', 'international', 'partner', 'exchange',
            'strategy', 'sustainability', 'responsibility', 'quality',
            'accreditation', 'ranking', 'career', 'alumni', 'news',
            'dean', 'leadership', 'management', 'organization', 'organisation',
            'contact', 'key-figures', 'facts', 'statistics'
        ]
    
    def crawl(self) -> CrawlResult:
        """Main crawl function"""
        print(f"Starting crawl of {self.base_url}")
        print(f"Max pages: {self.max_pages}")
        print("-" * 60)
        
        # Start with base URL and discover more
        to_visit = [self.base_url]
        
        while to_visit and len(self.visited) < self.max_pages:
            url = to_visit.pop(0)
            
            if url in self.visited:
                continue
            
            # Only crawl same domain
            if urlparse(url).netloc != self.domain:
                continue
            
            try:
                print(f"[{len(self.visited)+1}/{self.max_pages}] {url[:80]}...")
                
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; EFMDBot/1.0; +https://edtechsolutions.io)'
                })
                
                if response.status_code != 200:
                    continue
                
                self.visited.add(url)
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Store page content
                page_text = soup.get_text(separator=' ', strip=True)
                self.result.all_pages[url] = page_text
                
                # Extract data from this page
                self._extract_from_page(url, soup, page_text)
                
                # Find more links
                new_links = self._find_links(url, soup)
                
                # Prioritize important pages
                new_links = self._prioritize_links(new_links)
                
                for link in new_links:
                    if link not in self.visited and link not in to_visit:
                        to_visit.append(link)
                
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"  Error: {e}")
                continue
        
        self.result.pages_crawled = len(self.visited)
        print("-" * 60)
        print(f"Crawl complete. {self.result.pages_crawled} pages crawled.")
        
        return self.result
    
    def _find_links(self, current_url: str, soup: BeautifulSoup) -> List[str]:
        """Find all internal links on a page"""
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Convert relative to absolute
            full_url = urljoin(current_url, href)
            
            # Clean URL
            full_url = full_url.split('#')[0].split('?')[0].rstrip('/')
            
            # Only internal links
            if urlparse(full_url).netloc == self.domain:
                links.append(full_url)
        
        return list(set(links))
    
    def _prioritize_links(self, links: List[str]) -> List[str]:
        """Sort links by priority (important pages first)"""
        def priority(url):
            url_lower = url.lower()
            for i, kw in enumerate(self.priority_keywords):
                if kw in url_lower:
                    return i
            return 100
        
        return sorted(links, key=priority)
    
    def _extract_from_page(self, url: str, soup: BeautifulSoup, text: str):
        """Extract EFMD-relevant data from a page"""
        url_lower = url.lower()
        text_lower = text.lower()
        
        # Institution name (from title or header)
        if not self.result.institution_name:
            self._extract_institution_name(soup)
        
        # Address (from footer or contact page)
        if 'contact' in url_lower or not self.result.address:
            self._extract_address(soup, text)
        
        # Key figures page - goldmine!
        if any(kw in url_lower for kw in ['key-figures', 'facts', 'figures', 'statistics', 'growing', 'numbers']):
            self._extract_key_figures(text)
        
        # Leadership page
        if any(kw in url_lower for kw in ['dean', 'leadership', 'management', 'director']):
            self._extract_leadership(soup, text)
        
        # Staff/faculty pages
        if any(kw in url_lower for kw in ['staff', 'faculty', 'people', 'personnel', 'team']):
            self._extract_faculty(soup, url)
        
        # Research pages
        if 'research' in url_lower:
            self._extract_research_info(soup, text)
        
        # International/partners
        if any(kw in url_lower for kw in ['international', 'partner', 'exchange', 'cooperation']):
            self._extract_international(soup, text)
        
        # Strategy/sustainability
        if any(kw in url_lower for kw in ['strategy', 'sustainability', 'responsibility', 'values']):
            self._extract_strategy(soup, text)
        
        # Accreditations (check every page footer)
        self._extract_accreditations(soup, text)
        
        # Programmes
        if any(kw in url_lower for kw in ['programme', 'program', 'study', 'education', 'master', 'bachelor']):
            self._extract_programmes(soup, url)
    
    def _extract_institution_name(self, soup: BeautifulSoup):
        """Extract institution name"""
        # Try meta tags
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            self.result.institution_name = og_site['content']
            return
        
        # Try title
        title = soup.find('title')
        if title:
            text = title.get_text()
            # Usually "Page | Institution" or "Institution - Page"
            for sep in ['|', ' - ', ' – ']:
                if sep in text:
                    parts = text.split(sep)
                    # Institution name is usually the consistent part
                    self.result.institution_name = parts[-1].strip()
                    return
    
    def _extract_address(self, soup: BeautifulSoup, text: str):
        """Extract address"""
        # Look for postal code patterns (Finnish: 5 digits)
        match = re.search(r'([A-Za-z\s]+\s+\d+[^,]*,?\s*(?:FI-?)?\d{5}\s+[A-Za-z]+)', text)
        if match:
            self.result.address = match.group(1).strip()
        
        # Look for phone
        phone_match = re.search(r'\+\d{3}\s*\d+\s*\d+\s*\d+', text)
        if phone_match:
            self.result.phone = phone_match.group()
    
    def _extract_key_figures(self, text: str):
        """Extract key figures from text - numbers, stats, etc."""
        
        # Publications
        pub_match = re.search(r'(?:total\s+)?(?:number\s+of\s+)?publications\s+(?:was\s+)?(\d[\d,]+)', text, re.I)
        if pub_match:
            self.result.publications_total = int(pub_match.group(1).replace(',', ''))
        
        # Students
        student_match = re.search(r'(\d[\d,]+)\s+students', text, re.I)
        if student_match:
            num = int(student_match.group(1).replace(',', ''))
            if num > 1000:  # Likely total students
                self.result.total_students = num
        
        # International students
        intl_match = re.search(r'(\d[\d,]+)\s+international\s+(?:degree\s+)?students', text, re.I)
        if intl_match:
            self.result.international_students = int(intl_match.group(1).replace(',', ''))
        
        intl_pct_match = re.search(r'international[^.]*?(\d+)%', text, re.I)
        if intl_pct_match:
            self.result.international_students_pct = float(intl_pct_match.group(1))
        
        # Graduates - Master's
        master_grad_match = re.search(r'(\d[\d,]+)\s+(?:students\s+)?(?:completed\s+their\s+)?master', text, re.I)
        if master_grad_match:
            self.result.master_graduates = int(master_grad_match.group(1).replace(',', ''))
        
        # Graduates - Bachelor's
        bachelor_grad_match = re.search(r'(\d[\d,]+)\s+bachelor', text, re.I)
        if bachelor_grad_match:
            self.result.bachelor_graduates = int(bachelor_grad_match.group(1).replace(',', ''))
        
        # Graduates - Doctoral
        doctoral_grad_match = re.search(r'(\d[\d,]+)\s+doctor', text, re.I)
        if doctoral_grad_match:
            self.result.doctoral_graduates = int(doctoral_grad_match.group(1).replace(',', ''))
        
        # Applicants
        applicant_match = re.search(r'(\d[\d,]+)\s+applications?\s+(?:were\s+)?(?:received\s+)?(?:for\s+)?(?:bachelor|master)', text, re.I)
        if applicant_match:
            num = int(applicant_match.group(1).replace(',', ''))
            if 'bachelor' in text[applicant_match.start():applicant_match.end()+50].lower():
                self.result.bachelor_applicants = num
            elif 'master' in text[applicant_match.start():applicant_match.end()+50].lower():
                self.result.master_applicants = num
        
        # Personnel
        personnel_match = re.search(r'(?:number\s+of\s+)?personnel\s+(?:was\s+)?(\d[\d,]+)', text, re.I)
        if personnel_match:
            self.result.total_personnel = int(personnel_match.group(1).replace(',', ''))
        
        # International personnel percentage
        intl_personnel_match = re.search(r'international\s+personnel[^.]*?(\d+)\s*(?:percent|%)', text, re.I)
        if intl_personnel_match:
            self.result.international_personnel_pct = float(intl_personnel_match.group(1))
        
        # Nationalities
        nat_match = re.search(r'(\d+)\s+(?:different\s+)?nationalit', text, re.I)
        if nat_match:
            self.result.nationalities_count = int(nat_match.group(1))
        
        # Research funding
        funding_match = re.search(r'€\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?\s*(?:of\s+)?(?:competitive\s+)?research\s+funding', text, re.I)
        if funding_match:
            self.result.research_funding = funding_match.group(1)
        
        # Carbon footprint
        carbon_match = re.search(r'carbon\s+footprint[^.]*?([\d.]+)\s*(?:thousand\s+)?tonnes?', text, re.I)
        if carbon_match:
            self.result.carbon_footprint = carbon_match.group(1) + " thousand tonnes CO2"
    
    def _extract_leadership(self, soup: BeautifulSoup, text: str):
        """Extract dean/leadership info"""
        # Look for dean
        dean_match = re.search(r'dean[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
        if dean_match:
            self.result.dean_name = dean_match.group(1)
        
        # Look for patterns like "Prof. Name, Dean"
        prof_match = re.search(r'((?:Prof(?:essor)?\.?\s+)?[A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]+Dean', text)
        if prof_match:
            self.result.dean_name = prof_match.group(1)
            self.result.dean_title = "Dean"
    
    def _extract_faculty(self, soup: BeautifulSoup, url: str):
        """Extract faculty member info"""
        # Look for person cards
        for card in soup.find_all(['div', 'article', 'li'], class_=re.compile(r'person|staff|faculty|member|card', re.I)):
            person = {}
            
            # Name
            name_el = card.find(['h2', 'h3', 'h4', 'a', 'strong'])
            if name_el:
                name = name_el.get_text(strip=True)
                if name and len(name.split()) >= 2 and len(name) < 100:
                    person['name'] = name
            
            # Title
            title_el = card.find(class_=re.compile(r'title|position|role', re.I))
            if title_el:
                person['title'] = title_el.get_text(strip=True)
            
            # Email
            email_link = card.find('a', href=re.compile(r'mailto:'))
            if email_link:
                person['email'] = email_link['href'].replace('mailto:', '')
            
            if person.get('name'):
                self.result.faculty.append(person)
    
    def _extract_research_info(self, soup: BeautifulSoup, text: str):
        """Extract research focus areas"""
        # Look for research group names
        for h in soup.find_all(['h2', 'h3', 'h4']):
            h_text = h.get_text(strip=True)
            if any(kw in h_text.lower() for kw in ['group', 'focus', 'area', 'research']):
                if len(h_text) < 100:
                    self.result.research_focus_areas.append(h_text)
    
    def _extract_international(self, soup: BeautifulSoup, text: str):
        """Extract international partners"""
        # Look for university names (common patterns)
        uni_patterns = [
            r'University of [A-Z][a-z]+',
            r'[A-Z][a-z]+ University',
            r'[A-Z][a-z]+ Business School',
            r'[A-Z][a-z]+ School of [A-Z][a-z]+',
        ]
        
        for pattern in uni_patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                if m not in self.result.international_partners and 'Vaasa' not in m:
                    self.result.international_partners.append(m)
    
    def _extract_strategy(self, soup: BeautifulSoup, text: str):
        """Extract strategy and sustainability info"""
        # Look for strategy/vision text
        if 'strategy' in text.lower():
            # Find paragraphs mentioning strategy
            for p in soup.find_all('p'):
                p_text = p.get_text(strip=True)
                if 'strategy' in p_text.lower() and len(p_text) > 50:
                    self.result.strategy_text = p_text[:500]
                    break
        
        # Sustainability info
        if 'sustainability' in text.lower() or 'responsibility' in text.lower():
            self.result.sustainability_info = "Sustainability/responsibility content found"
    
    def _extract_accreditations(self, soup: BeautifulSoup, text: str):
        """Extract accreditation badges"""
        accred_keywords = ['AACSB', 'EQUIS', 'AMBA', 'EFMD', 'FINEEC', 'EPAS']
        
        for acc in accred_keywords:
            if acc in text and acc not in self.result.accreditations:
                self.result.accreditations.append(acc)
        
        # Also check image alt texts
        for img in soup.find_all('img', alt=True):
            alt = img['alt']
            for acc in accred_keywords:
                if acc in alt and acc not in self.result.accreditations:
                    self.result.accreditations.append(acc)
    
    def _extract_programmes(self, soup: BeautifulSoup, url: str):
        """Extract programme information"""
        # Look for programme links
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            text = a.get_text(strip=True)
            
            if any(kw in href for kw in ['master', 'bachelor', 'mba', 'programme', 'program']):
                if text and len(text) > 5 and len(text) < 100:
                    prog = {'name': text, 'url': urljoin(url, a['href'])}
                    if prog not in self.result.programmes:
                        self.result.programmes.append(prog)


def print_crawl_result(result: CrawlResult):
    """Pretty print the crawl results"""
    print("\n" + "=" * 70)
    print("CRAWL RESULTS: " + result.school_url)
    print("=" * 70)
    print(f"Pages crawled: {result.pages_crawled}")
    
    print("\n📍 INSTITUTION")
    print(f"  Name: {result.institution_name}")
    print(f"  Address: {result.address}")
    print(f"  Phone: {result.phone}")
    
    print("\n👔 LEADERSHIP")
    print(f"  Dean: {result.dean_name}")
    print(f"  Title: {result.dean_title}")
    
    print("\n📊 KEY FIGURES")
    print(f"  Total students: {result.total_students}")
    print(f"  International students: {result.international_students} ({result.international_students_pct}%)")
    print(f"  Master's graduates: {result.master_graduates}")
    print(f"  Bachelor's graduates: {result.bachelor_graduates}")
    print(f"  Doctoral graduates: {result.doctoral_graduates}")
    print(f"  Bachelor applicants: {result.bachelor_applicants}")
    print(f"  Master applicants: {result.master_applicants}")
    
    print("\n👥 PERSONNEL")
    print(f"  Total: {result.total_personnel}")
    print(f"  International %: {result.international_personnel_pct}%")
    print(f"  Nationalities: {result.nationalities_count}")
    
    print("\n📚 RESEARCH")
    print(f"  Publications: {result.publications_total}")
    print(f"  Funding: €{result.research_funding}")
    print(f"  Focus areas: {result.research_focus_areas[:5]}")
    
    print("\n🌍 INTERNATIONAL")
    print(f"  Partners found: {len(result.international_partners)}")
    if result.international_partners:
        print(f"  Examples: {result.international_partners[:5]}")
    
    print("\n🏆 ACCREDITATIONS")
    print(f"  {result.accreditations}")
    
    print("\n🌱 SUSTAINABILITY")
    print(f"  Info found: {result.sustainability_info}")
    print(f"  Carbon footprint: {result.carbon_footprint}")
    
    print("\n📋 PROGRAMMES FOUND")
    print(f"  Count: {len(result.programmes)}")
    for p in result.programmes[:10]:
        print(f"    - {p['name']}")
    
    print("\n👨‍🏫 FACULTY FOUND")
    print(f"  Count: {len(result.faculty)}")
    for f in result.faculty[:10]:
        print(f"    - {f.get('name', 'Unknown')}: {f.get('title', 'No title')}")


def calculate_efmd_readiness(result: CrawlResult) -> dict:
    """Calculate EFMD readiness score based on crawled data"""
    scores = {}
    
    # Publications (need evidence of research output)
    if result.publications_total:
        if result.publications_total > 500:
            scores['publications'] = {'score': 100, 'status': '✅', 'value': result.publications_total}
        elif result.publications_total > 200:
            scores['publications'] = {'score': 70, 'status': '✅', 'value': result.publications_total}
        else:
            scores['publications'] = {'score': 40, 'status': '⚠️', 'value': result.publications_total}
    else:
        scores['publications'] = {'score': 0, 'status': '❌', 'value': 'Not found'}
    
    # International dimension
    if result.international_personnel_pct:
        if result.international_personnel_pct > 20:
            scores['international_staff'] = {'score': 100, 'status': '✅', 'value': f"{result.international_personnel_pct}%"}
        elif result.international_personnel_pct > 10:
            scores['international_staff'] = {'score': 60, 'status': '⚠️', 'value': f"{result.international_personnel_pct}%"}
        else:
            scores['international_staff'] = {'score': 30, 'status': '⚠️', 'value': f"{result.international_personnel_pct}%"}
    else:
        scores['international_staff'] = {'score': 0, 'status': '❌', 'value': 'Not found'}
    
    # International students
    if result.international_students_pct:
        if result.international_students_pct > 15:
            scores['international_students'] = {'score': 100, 'status': '✅', 'value': f"{result.international_students_pct}%"}
        elif result.international_students_pct > 5:
            scores['international_students'] = {'score': 60, 'status': '⚠️', 'value': f"{result.international_students_pct}%"}
        else:
            scores['international_students'] = {'score': 30, 'status': '⚠️', 'value': f"{result.international_students_pct}%"}
    else:
        scores['international_students'] = {'score': 0, 'status': '❌', 'value': 'Not found'}
    
    # Accreditations (existing quality marks)
    if result.accreditations:
        if 'AACSB' in result.accreditations or 'EQUIS' in result.accreditations:
            scores['accreditations'] = {'score': 100, 'status': '✅', 'value': ', '.join(result.accreditations)}
        else:
            scores['accreditations'] = {'score': 50, 'status': '⚠️', 'value': ', '.join(result.accreditations)}
    else:
        scores['accreditations'] = {'score': 0, 'status': '❌', 'value': 'None found'}
    
    # Sustainability/ERS
    if result.sustainability_info or result.carbon_footprint:
        scores['ers'] = {'score': 80, 'status': '✅', 'value': 'Content found'}
    else:
        scores['ers'] = {'score': 0, 'status': '❌', 'value': 'Not found'}
    
    # Graduate numbers (programme maturity)
    if result.master_graduates:
        if result.master_graduates > 100:
            scores['graduates'] = {'score': 100, 'status': '✅', 'value': result.master_graduates}
        elif result.master_graduates > 30:
            scores['graduates'] = {'score': 70, 'status': '✅', 'value': result.master_graduates}
        else:
            scores['graduates'] = {'score': 40, 'status': '⚠️', 'value': result.master_graduates}
    else:
        scores['graduates'] = {'score': 0, 'status': '❌', 'value': 'Not found'}
    
    # Calculate overall
    total_score = sum(s['score'] for s in scores.values())
    max_score = len(scores) * 100
    overall_pct = round(total_score / max_score * 100)
    
    return {
        'overall_pct': overall_pct,
        'details': scores
    }


def print_readiness_report(result: CrawlResult, readiness: dict):
    """Print EFMD readiness report"""
    print("\n" + "=" * 70)
    print("EFMD ACCREDITATION READINESS ESTIMATE")
    print("=" * 70)
    
    print(f"\n🎯 OVERALL READINESS: {readiness['overall_pct']}%")
    print()
    
    for metric, data in readiness['details'].items():
        print(f"  {data['status']} {metric.replace('_', ' ').title():25} {str(data['value']):20} ({data['score']}%)")
    
    print("\n" + "-" * 70)
    if readiness['overall_pct'] >= 70:
        print("💚 HIGH POTENTIAL - This school looks ready for EFMD accreditation")
    elif readiness['overall_pct'] >= 50:
        print("💛 MEDIUM POTENTIAL - Some gaps to address, but achievable")
    else:
        print("🔴 NEEDS WORK - Significant gaps identified")


if __name__ == "__main__":
    # Test with University of Vaasa
    crawler = SchoolCrawler(
        base_url="https://www.uwasa.fi/en",
        max_pages=50,
        delay=0.5
    )
    
    result = crawler.crawl()
    print_crawl_result(result)
    
    readiness = calculate_efmd_readiness(result)
    print_readiness_report(result, readiness)
