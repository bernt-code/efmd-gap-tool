"""
EFMD School Website Crawler
============================

Crawls any business school website and estimates EFMD accreditation readiness.

USAGE:
    python run_crawler.py https://www.uwasa.fi/en
    python run_crawler.py https://www.uwasa.fi/en --max-pages 100 --output vaasa_report.json

INSTALL:
    pip install requests beautifulsoup4 lxml

NOTES:
    - University of Vaasa is a BEST PRACTICE example (4 programme accreditations, EQUIS finalist)
    - Most schools will score LOWER than Vaasa
    - Use Vaasa as benchmark for what "ready" looks like
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import time
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Set
from datetime import datetime


@dataclass
class CrawlResult:
    """All data extracted from a school website"""
    school_url: str
    crawl_date: str = field(default_factory=lambda: datetime.now().isoformat())
    pages_crawled: int = 0
    
    # Institution basics
    institution_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Leadership
    dean_name: Optional[str] = None
    dean_title: Optional[str] = None
    dean_email: Optional[str] = None
    
    # Student numbers
    total_students: Optional[int] = None
    basic_degree_students: Optional[int] = None
    doctoral_students: Optional[int] = None
    international_students: Optional[int] = None
    international_students_pct: Optional[float] = None
    
    # Graduates (per year if found)
    bachelor_graduates: Optional[int] = None
    master_graduates: Optional[int] = None
    doctoral_graduates: Optional[int] = None
    
    # Applicants
    bachelor_applicants: Optional[int] = None
    master_applicants: Optional[int] = None
    international_applicants: Optional[int] = None
    
    # Personnel / Faculty
    total_personnel: Optional[int] = None
    teaching_research_staff: Optional[int] = None
    international_personnel_pct: Optional[float] = None
    international_teaching_pct: Optional[float] = None
    nationalities_count: Optional[int] = None
    
    # Research
    publications_total: Optional[int] = None
    publications_year: Optional[int] = None
    research_funding: Optional[str] = None
    research_funding_eur: Optional[float] = None
    
    # Employment outcomes
    employment_rate: Optional[float] = None
    employment_timeframe: Optional[str] = None
    
    # Accreditations
    accreditations: List[str] = field(default_factory=list)
    
    # Programmes found
    programmes: List[Dict] = field(default_factory=list)
    
    # Faculty members found
    faculty: List[Dict] = field(default_factory=list)
    
    # International partners
    international_partners: List[str] = field(default_factory=list)
    partner_networks: List[str] = field(default_factory=list)
    
    # ERS / Sustainability
    has_sustainability_content: bool = False
    sustainability_keywords_found: List[str] = field(default_factory=list)
    carbon_footprint: Optional[str] = None
    sdg_mentioned: bool = False
    
    # Strategy
    strategy_text: Optional[str] = None
    mission_text: Optional[str] = None
    vision_text: Optional[str] = None
    research_focus_areas: List[str] = field(default_factory=list)
    
    # Quality
    has_quality_assurance_content: bool = False
    
    # Digital
    learning_platforms_mentioned: List[str] = field(default_factory=list)
    
    # Raw data
    all_page_urls: List[str] = field(default_factory=list)


class SchoolCrawler:
    """Crawls a school website and extracts EFMD-relevant data"""
    
    def __init__(self, base_url: str, max_pages: int = 100, delay: float = 0.3, verbose: bool = True):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.delay = delay
        self.verbose = verbose
        self.visited: Set[str] = set()
        self.result = CrawlResult(school_url=base_url, website=base_url)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Priority keywords for crawl ordering
        self.priority_keywords = [
            'about', 'key-figures', 'facts', 'figures', 'statistics', 'numbers',
            'university', 'school', 'faculty', 'staff', 'people', 'personnel',
            'research', 'publication', 'study', 'education', 'programme', 'program',
            'admission', 'apply', 'international', 'partner', 'exchange', 'cooperation',
            'strategy', 'sustainability', 'responsibility', 'quality', 'accreditation',
            'ranking', 'career', 'alumni', 'employment', 'dean', 'leadership', 
            'management', 'organization', 'organisation', 'contact', 'master', 'bachelor'
        ]
        
        # ERS keywords
        self.ers_keywords = [
            'sustainability', 'sustainable', 'responsibility', 'responsible',
            'ethics', 'ethical', 'csr', 'esg', 'climate', 'carbon', 'environment',
            'social impact', 'sdg', 'prme', 'green', 'diversity', 'inclusion',
            'governance', 'stakeholder'
        ]
        
        # Accreditation keywords
        self.accred_keywords = ['AACSB', 'EQUIS', 'AMBA', 'EFMD', 'EPAS', 'FINEEC', 'FIBAA', 'CEEMAN']
        
        # Learning platforms
        self.platform_keywords = ['moodle', 'canvas', 'blackboard', 'brightspace', 'teams', 'zoom']
        
        # Partner network keywords
        self.network_keywords = ['CEMS', 'PIM', 'GBSN', 'AACSB', 'EFMD', 'NIBS', 'CEEMAN', 'AMBA']
    
    def log(self, msg: str):
        if self.verbose:
            print(msg)
    
    def crawl(self) -> CrawlResult:
        """Main crawl function"""
        self.log(f"\n{'='*70}")
        self.log(f"CRAWLING: {self.base_url}")
        self.log(f"Max pages: {self.max_pages}")
        self.log(f"{'='*70}\n")
        
        to_visit = [self.base_url]
        
        while to_visit and len(self.visited) < self.max_pages:
            url = to_visit.pop(0)
            
            if url in self.visited:
                continue
            
            if urlparse(url).netloc != self.domain:
                continue
            
            # Skip non-content URLs
            if any(skip in url.lower() for skip in ['.pdf', '.jpg', '.png', '.gif', 'mailto:', 'tel:', '.doc']):
                continue
            
            try:
                self.log(f"[{len(self.visited)+1:3}/{self.max_pages}] {url[:70]}...")
                
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                if 'text/html' not in response.headers.get('content-type', ''):
                    continue
                
                self.visited.add(url)
                self.result.all_page_urls.append(url)
                
                soup = BeautifulSoup(response.text, 'lxml')
                page_text = soup.get_text(separator=' ', strip=True)
                
                # Extract data from this page
                self._extract_from_page(url, soup, page_text)
                
                # Find more links
                new_links = self._find_links(url, soup)
                new_links = self._prioritize_links(new_links)
                
                for link in new_links:
                    if link not in self.visited and link not in to_visit:
                        to_visit.append(link)
                
                time.sleep(self.delay)
                
            except Exception as e:
                self.log(f"    Error: {str(e)[:50]}")
                continue
        
        self.result.pages_crawled = len(self.visited)
        
        self.log(f"\n{'='*70}")
        self.log(f"Crawl complete. {self.result.pages_crawled} pages crawled.")
        self.log(f"{'='*70}\n")
        
        return self.result
    
    def _find_links(self, current_url: str, soup: BeautifulSoup) -> List[str]:
        """Find all internal links"""
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(current_url, href)
            full_url = full_url.split('#')[0].split('?')[0].rstrip('/')
            
            if urlparse(full_url).netloc == self.domain:
                links.append(full_url)
        
        return list(set(links))
    
    def _prioritize_links(self, links: List[str]) -> List[str]:
        """Sort links - priority pages first"""
        def priority(url):
            url_lower = url.lower()
            for i, kw in enumerate(self.priority_keywords):
                if kw in url_lower:
                    return i
            return 100
        
        return sorted(links, key=priority)
    
    def _extract_from_page(self, url: str, soup: BeautifulSoup, text: str):
        """Extract all EFMD-relevant data from a page"""
        url_lower = url.lower()
        text_lower = text.lower()
        
        # Always check for these
        self._extract_accreditations(text)
        self._extract_ers_keywords(text_lower)
        self._extract_platforms(text_lower)
        self._extract_networks(text)
        
        # Institution name (from any page with title)
        if not self.result.institution_name:
            self._extract_institution_name(soup)
        
        # Key figures / statistics pages - GOLDMINE
        if any(kw in url_lower for kw in ['key-figures', 'facts', 'figures', 'statistics', 'numbers', 'growing']):
            self._extract_key_figures(text)
        
        # About pages
        if 'about' in url_lower:
            self._extract_about_info(soup, text)
        
        # Contact pages
        if 'contact' in url_lower:
            self._extract_contact(soup, text)
        
        # Leadership
        if any(kw in url_lower for kw in ['dean', 'leadership', 'management', 'director', 'board']):
            self._extract_leadership(soup, text)
        
        # Staff/faculty pages
        if any(kw in url_lower for kw in ['staff', 'faculty', 'people', 'personnel', 'team', 'employee']):
            self._extract_faculty_list(soup, url)
        
        # Research
        if 'research' in url_lower:
            self._extract_research(soup, text)
        
        # International
        if any(kw in url_lower for kw in ['international', 'partner', 'exchange', 'cooperation', 'global']):
            self._extract_international(soup, text)
        
        # Strategy
        if any(kw in url_lower for kw in ['strategy', 'mission', 'vision', 'values']):
            self._extract_strategy(soup, text)
        
        # Quality
        if any(kw in url_lower for kw in ['quality', 'accreditation', 'ranking']):
            self.result.has_quality_assurance_content = True
        
        # Programmes
        if any(kw in url_lower for kw in ['programme', 'program', 'master', 'bachelor', 'mba', 'study', 'education']):
            self._extract_programmes(soup, url)
        
        # Career/alumni
        if any(kw in url_lower for kw in ['career', 'alumni', 'employment', 'graduate']):
            self._extract_careers(text)
    
    def _extract_institution_name(self, soup: BeautifulSoup):
        """Extract institution name"""
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            self.result.institution_name = og_site['content']
            return
        
        title = soup.find('title')
        if title:
            text = title.get_text()
            for sep in ['|', ' - ', ' – ', ' — ']:
                if sep in text:
                    parts = text.split(sep)
                    self.result.institution_name = parts[-1].strip()
                    return
    
    def _extract_contact(self, soup: BeautifulSoup, text: str):
        """Extract address and phone"""
        # Address patterns
        addr_patterns = [
            r'([A-Za-z]+(?:intie|gatan|vägen|street|road|avenue)\s+\d+[^,\n]*(?:,\s*)?(?:FI-?)?\d{5}[^,\n]*)',
            r'(\d+\s+[A-Za-z\s]+(?:Street|Road|Avenue)[^,\n]*,[^,\n]*\d{5}[^,\n]*)',
        ]
        for pattern in addr_patterns:
            match = re.search(pattern, text, re.I)
            if match and not self.result.address:
                self.result.address = ' '.join(match.group(1).split())
                break
        
        # Phone
        phone_match = re.search(r'(\+\d{2,3}[\s\-]?\d[\d\s\-]{8,})', text)
        if phone_match and not self.result.phone:
            self.result.phone = phone_match.group(1).strip()
    
    def _extract_key_figures(self, text: str):
        """Extract numbers from key figures pages"""
        
        # Publications
        for pattern in [
            r'(?:total\s+)?(?:number\s+of\s+)?publications\s+(?:was\s+)?(\d[\d,]+)',
            r'(\d[\d,]+)\s+publications',
        ]:
            match = re.search(pattern, text, re.I)
            if match and not self.result.publications_total:
                self.result.publications_total = int(match.group(1).replace(',', ''))
                break
        
        # Total students
        for pattern in [
            r'(?:total\s+of\s+)?([\d,]+)\s+students',
            r'([\d,]+)\s+(?:degree\s+)?students',
        ]:
            match = re.search(pattern, text, re.I)
            if match:
                num = int(match.group(1).replace(',', ''))
                if num > 500 and not self.result.total_students:
                    self.result.total_students = num
                    break
        
        # International students
        match = re.search(r'([\d,]+)\s+international\s+(?:degree\s+)?students', text, re.I)
        if match:
            self.result.international_students = int(match.group(1).replace(',', ''))
        
        match = re.search(r'international[^.]*?(\d+)\s*%', text, re.I)
        if match and not self.result.international_students_pct:
            self.result.international_students_pct = float(match.group(1))
        
        # Graduates
        patterns = [
            (r'(\d[\d,]+)\s+(?:students\s+)?(?:completed\s+)?(?:their\s+)?master', 'master'),
            (r'(\d[\d,]+)\s+master.s?\s+degrees?', 'master'),
            (r'(\d[\d,]+)\s+bachelor.s?\s+degrees?', 'bachelor'),
            (r'(\d[\d,]+)\s+doctoral\s+degrees?', 'doctoral'),
        ]
        for pattern, degree_type in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                num = int(match.group(1).replace(',', ''))
                if degree_type == 'master' and not self.result.master_graduates:
                    self.result.master_graduates = num
                elif degree_type == 'bachelor' and not self.result.bachelor_graduates:
                    self.result.bachelor_graduates = num
                elif degree_type == 'doctoral' and not self.result.doctoral_graduates:
                    self.result.doctoral_graduates = num
        
        # Applicants
        match = re.search(r'([\d,]+)\s+applications?\s+(?:were\s+)?(?:received\s+)?(?:for\s+)?bachelor', text, re.I)
        if match:
            self.result.bachelor_applicants = int(match.group(1).replace(',', ''))
        
        match = re.search(r'([\d,]+)\s+applications?\s+(?:were\s+)?(?:received\s+)?(?:for\s+)?(?:finnish[^.]*)?master', text, re.I)
        if match:
            self.result.master_applicants = int(match.group(1).replace(',', ''))
        
        # Personnel
        match = re.search(r'(?:number\s+of\s+)?personnel\s+(?:was\s+)?([\d,]+)', text, re.I)
        if match:
            self.result.total_personnel = int(match.group(1).replace(',', ''))
        
        match = re.search(r'international\s+personnel[^.]*?(\d+)\s*(?:percent|%)', text, re.I)
        if match:
            self.result.international_personnel_pct = float(match.group(1))
        
        match = re.search(r'(\d+)\s+(?:different\s+)?nationalit', text, re.I)
        if match:
            self.result.nationalities_count = int(match.group(1))
        
        # Research funding
        match = re.search(r'€\s*([\d,]+(?:\.\d+)?)\s*(?:of\s+)?(?:competitive\s+)?(?:research\s+)?funding', text, re.I)
        if match:
            self.result.research_funding = match.group(1)
            try:
                self.result.research_funding_eur = float(match.group(1).replace(',', ''))
            except:
                pass
        
        # Carbon footprint
        match = re.search(r'carbon\s+footprint[^.]*?([\d.]+)\s*(?:thousand\s+)?tonnes?', text, re.I)
        if match:
            self.result.carbon_footprint = match.group(1) + " thousand tonnes CO2"
    
    def _extract_about_info(self, soup: BeautifulSoup, text: str):
        """Extract from about pages"""
        self._extract_contact(soup, text)
        self._extract_key_figures(text)
    
    def _extract_leadership(self, soup: BeautifulSoup, text: str):
        """Extract dean info"""
        patterns = [
            r'Dean[:\s]+(?:Prof(?:essor)?\.?\s+)?([A-Z][a-zäöå]+\s+[A-Z][a-zäöå]+)',
            r'((?:Prof(?:essor)?\.?\s+)?[A-Z][a-zäöå]+\s+[A-Z][a-zäöå]+)[,\s]+Dean',
            r'((?:Prof(?:essor)?\.?\s+)?[A-Z][a-zäöå]+\s+[A-Z][a-zäöå]+)[,\s]+Director',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match and not self.result.dean_name:
                self.result.dean_name = match.group(1)
                self.result.dean_title = "Dean"
                break
        
        # Email
        if self.result.dean_name:
            first_name = self.result.dean_name.split()[-1].lower()
            email_match = re.search(rf'{first_name}[^@]*@[\w.]+', text, re.I)
            if email_match:
                self.result.dean_email = email_match.group()
    
    def _extract_faculty_list(self, soup: BeautifulSoup, url: str):
        """Extract faculty members"""
        for card in soup.find_all(['div', 'article', 'li', 'tr'], class_=re.compile(r'person|staff|faculty|member|card|employee', re.I)):
            person = {}
            
            name_el = card.find(['h2', 'h3', 'h4', 'a', 'strong', 'td'])
            if name_el:
                name = name_el.get_text(strip=True)
                if name and 2 <= len(name.split()) <= 5 and len(name) < 60:
                    person['name'] = name
            
            title_el = card.find(class_=re.compile(r'title|position|role', re.I))
            if title_el:
                person['title'] = title_el.get_text(strip=True)[:100]
            
            email_link = card.find('a', href=re.compile(r'mailto:'))
            if email_link:
                person['email'] = email_link['href'].replace('mailto:', '').split('?')[0]
            
            if person.get('name') and person not in self.result.faculty:
                self.result.faculty.append(person)
    
    def _extract_research(self, soup: BeautifulSoup, text: str):
        """Extract research info"""
        self._extract_key_figures(text)
        
        # Research focus areas from headers
        for h in soup.find_all(['h2', 'h3', 'h4']):
            h_text = h.get_text(strip=True)
            if 10 < len(h_text) < 80:
                if h_text not in self.result.research_focus_areas:
                    self.result.research_focus_areas.append(h_text)
    
    def _extract_international(self, soup: BeautifulSoup, text: str):
        """Extract international partners"""
        uni_patterns = [
            r'University of [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?',
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)? University',
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)? Business School',
            r'[A-Z][A-Z]+\s+[A-Z][a-z]+ School',  # e.g. "MIT Sloan School"
        ]
        
        for pattern in uni_patterns:
            for match in re.finditer(pattern, text):
                name = match.group()
                if name not in self.result.international_partners:
                    if not any(skip in name for skip in [self.result.institution_name or '', 'University of the', 'University of a']):
                        self.result.international_partners.append(name)
    
    def _extract_strategy(self, soup: BeautifulSoup, text: str):
        """Extract strategy info"""
        # Mission
        mission_match = re.search(r'mission[:\s]+([^.]+\.)', text, re.I)
        if mission_match and not self.result.mission_text:
            self.result.mission_text = mission_match.group(1)[:300]
        
        # Vision
        vision_match = re.search(r'vision[:\s]+([^.]+\.)', text, re.I)
        if vision_match and not self.result.vision_text:
            self.result.vision_text = vision_match.group(1)[:300]
    
    def _extract_programmes(self, soup: BeautifulSoup, url: str):
        """Extract programme list"""
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            text = a.get_text(strip=True)
            
            if any(kw in href for kw in ['master', 'bachelor', 'mba', 'programme', 'program']):
                if text and 5 < len(text) < 100:
                    prog = {'name': text, 'url': urljoin(url, a['href'])}
                    if prog not in self.result.programmes:
                        self.result.programmes.append(prog)
    
    def _extract_careers(self, text: str):
        """Extract career/employment info"""
        # Employment rate
        match = re.search(r'(\d+)\s*%\s*(?:of\s+)?(?:graduates?\s+)?(?:are\s+)?(?:employed|find|found)', text, re.I)
        if match and not self.result.employment_rate:
            self.result.employment_rate = float(match.group(1))
        
        # Time to employment
        match = re.search(r'within\s+(\d+)\s*(months?|weeks?)', text, re.I)
        if match:
            self.result.employment_timeframe = f"{match.group(1)} {match.group(2)}"
    
    def _extract_accreditations(self, text: str):
        """Extract accreditations"""
        for acc in self.accred_keywords:
            if acc in text and acc not in self.result.accreditations:
                self.result.accreditations.append(acc)
    
    def _extract_ers_keywords(self, text_lower: str):
        """Extract ERS/sustainability keywords"""
        for kw in self.ers_keywords:
            if kw in text_lower:
                self.result.has_sustainability_content = True
                if kw not in self.result.sustainability_keywords_found:
                    self.result.sustainability_keywords_found.append(kw)
        
        if 'sdg' in text_lower or 'sustainable development goal' in text_lower:
            self.result.sdg_mentioned = True
    
    def _extract_platforms(self, text_lower: str):
        """Extract learning platforms"""
        for platform in self.platform_keywords:
            if platform in text_lower and platform not in self.result.learning_platforms_mentioned:
                self.result.learning_platforms_mentioned.append(platform)
    
    def _extract_networks(self, text: str):
        """Extract partner networks"""
        for network in self.network_keywords:
            if network in text and network not in self.result.partner_networks:
                self.result.partner_networks.append(network)


def calculate_efmd_readiness(result: CrawlResult) -> dict:
    """Calculate EFMD readiness score"""
    scores = {}
    max_points = 0
    earned_points = 0
    
    # 1. Publications (15 points)
    max_points += 15
    if result.publications_total:
        if result.publications_total > 500:
            scores['publications'] = {'score': 15, 'status': '✅', 'value': result.publications_total, 'note': 'Excellent research output'}
            earned_points += 15
        elif result.publications_total > 200:
            scores['publications'] = {'score': 10, 'status': '✅', 'value': result.publications_total, 'note': 'Good research output'}
            earned_points += 10
        else:
            scores['publications'] = {'score': 5, 'status': '⚠️', 'value': result.publications_total, 'note': 'Limited research output'}
            earned_points += 5
    else:
        scores['publications'] = {'score': 0, 'status': '❓', 'value': 'Not found', 'note': 'Could not find publication data'}
    
    # 2. International staff (15 points)
    max_points += 15
    if result.international_personnel_pct:
        if result.international_personnel_pct > 20:
            scores['international_staff'] = {'score': 15, 'status': '✅', 'value': f"{result.international_personnel_pct}%", 'note': 'Strong international faculty'}
            earned_points += 15
        elif result.international_personnel_pct > 10:
            scores['international_staff'] = {'score': 10, 'status': '⚠️', 'value': f"{result.international_personnel_pct}%", 'note': 'Moderate international presence'}
            earned_points += 10
        else:
            scores['international_staff'] = {'score': 5, 'status': '⚠️', 'value': f"{result.international_personnel_pct}%", 'note': 'Limited international faculty'}
            earned_points += 5
    else:
        scores['international_staff'] = {'score': 0, 'status': '❓', 'value': 'Not found', 'note': 'Could not find international staff data'}
    
    # 3. International students (15 points)
    max_points += 15
    if result.international_students_pct:
        if result.international_students_pct > 15:
            scores['international_students'] = {'score': 15, 'status': '✅', 'value': f"{result.international_students_pct}%", 'note': 'Strong international student body'}
            earned_points += 15
        elif result.international_students_pct > 5:
            scores['international_students'] = {'score': 10, 'status': '⚠️', 'value': f"{result.international_students_pct}%", 'note': 'Moderate international presence'}
            earned_points += 10
        else:
            scores['international_students'] = {'score': 5, 'status': '⚠️', 'value': f"{result.international_students_pct}%", 'note': 'Limited international students'}
            earned_points += 5
    else:
        scores['international_students'] = {'score': 0, 'status': '❓', 'value': 'Not found', 'note': 'Could not find international student data'}
    
    # 4. Existing accreditations (15 points)
    max_points += 15
    if result.accreditations:
        if any(a in result.accreditations for a in ['AACSB', 'EQUIS']):
            scores['accreditations'] = {'score': 15, 'status': '✅', 'value': ', '.join(result.accreditations), 'note': 'Major accreditation(s) held'}
            earned_points += 15
        elif any(a in result.accreditations for a in ['EFMD', 'AMBA', 'EPAS']):
            scores['accreditations'] = {'score': 12, 'status': '✅', 'value': ', '.join(result.accreditations), 'note': 'Accreditation(s) held'}
            earned_points += 12
        else:
            scores['accreditations'] = {'score': 8, 'status': '⚠️', 'value': ', '.join(result.accreditations), 'note': 'Some quality marks'}
            earned_points += 8
    else:
        scores['accreditations'] = {'score': 0, 'status': '❌', 'value': 'None found', 'note': 'No accreditations identified'}
    
    # 5. ERS / Sustainability (15 points)
    max_points += 15
    if result.has_sustainability_content:
        ers_count = len(result.sustainability_keywords_found)
        if ers_count >= 5 or result.sdg_mentioned:
            scores['ers'] = {'score': 15, 'status': '✅', 'value': f"{ers_count} keywords", 'note': 'Strong ERS presence'}
            earned_points += 15
        elif ers_count >= 2:
            scores['ers'] = {'score': 10, 'status': '⚠️', 'value': f"{ers_count} keywords", 'note': 'Some ERS content'}
            earned_points += 10
        else:
            scores['ers'] = {'score': 5, 'status': '⚠️', 'value': f"{ers_count} keywords", 'note': 'Limited ERS visibility'}
            earned_points += 5
    else:
        scores['ers'] = {'score': 0, 'status': '❌', 'value': 'Not found', 'note': 'No ERS content identified'}
    
    # 6. Programme maturity - graduates (15 points)
    max_points += 15
    if result.master_graduates:
        if result.master_graduates > 100:
            scores['graduates'] = {'score': 15, 'status': '✅', 'value': result.master_graduates, 'note': 'Mature programmes'}
            earned_points += 15
        elif result.master_graduates > 30:
            scores['graduates'] = {'score': 10, 'status': '✅', 'value': result.master_graduates, 'note': 'Established programmes'}
            earned_points += 10
        else:
            scores['graduates'] = {'score': 5, 'status': '⚠️', 'value': result.master_graduates, 'note': 'Newer programmes'}
            earned_points += 5
    else:
        scores['graduates'] = {'score': 0, 'status': '❓', 'value': 'Not found', 'note': 'Could not find graduate data'}
    
    # 7. Faculty data available (10 points)
    max_points += 10
    if len(result.faculty) > 20:
        scores['faculty_data'] = {'score': 10, 'status': '✅', 'value': f"{len(result.faculty)} found", 'note': 'Good faculty visibility'}
        earned_points += 10
    elif len(result.faculty) > 5:
        scores['faculty_data'] = {'score': 5, 'status': '⚠️', 'value': f"{len(result.faculty)} found", 'note': 'Some faculty listed'}
        earned_points += 5
    else:
        scores['faculty_data'] = {'score': 0, 'status': '❓', 'value': f"{len(result.faculty)} found", 'note': 'Limited faculty visibility'}
    
    overall_pct = round(earned_points / max_points * 100)
    
    return {
        'overall_pct': overall_pct,
        'earned_points': earned_points,
        'max_points': max_points,
        'details': scores
    }


def print_report(result: CrawlResult, readiness: dict):
    """Print full report"""
    
    print("\n" + "=" * 70)
    print(f"EFMD ACCREDITATION READINESS REPORT")
    print(f"School: {result.institution_name or result.school_url}")
    print(f"Crawled: {result.crawl_date[:10]}")
    print(f"Pages analyzed: {result.pages_crawled}")
    print("=" * 70)
    
    # Readiness score
    print(f"\n{'🎯 OVERALL READINESS SCORE: ' + str(readiness['overall_pct']) + '%':^70}")
    print(f"{'(' + str(readiness['earned_points']) + '/' + str(readiness['max_points']) + ' points)':^70}")
    
    if readiness['overall_pct'] >= 75:
        print(f"\n{'💚 HIGH POTENTIAL - Strong candidate for EFMD accreditation':^70}")
    elif readiness['overall_pct'] >= 50:
        print(f"\n{'💛 MEDIUM POTENTIAL - Some gaps to address':^70}")
    else:
        print(f"\n{'🔴 NEEDS DEVELOPMENT - Significant preparation needed':^70}")
    
    # Detailed scores
    print("\n" + "-" * 70)
    print("DETAILED ASSESSMENT:")
    print("-" * 70)
    for metric, data in readiness['details'].items():
        label = metric.replace('_', ' ').title()
        print(f"  {data['status']} {label:25} {str(data['value']):20} {data['note']}")
    
    # Key data found
    print("\n" + "-" * 70)
    print("KEY DATA EXTRACTED:")
    print("-" * 70)
    
    if result.institution_name:
        print(f"  Institution: {result.institution_name}")
    if result.address:
        print(f"  Address: {result.address}")
    if result.total_students:
        print(f"  Students: {result.total_students:,}")
    if result.total_personnel:
        print(f"  Personnel: {result.total_personnel}")
    if result.publications_total:
        print(f"  Publications: {result.publications_total}")
    if result.master_graduates:
        print(f"  Master's graduates: {result.master_graduates}")
    if result.accreditations:
        print(f"  Accreditations: {', '.join(result.accreditations)}")
    if result.research_focus_areas:
        print(f"  Research areas: {', '.join(result.research_focus_areas[:5])}")
    if result.international_partners:
        print(f"  Partners found: {len(result.international_partners)}")
    if result.faculty:
        print(f"  Faculty listed: {len(result.faculty)}")
    if result.programmes:
        print(f"  Programmes found: {len(result.programmes)}")
    
    # ERS
    if result.sustainability_keywords_found:
        print(f"\n  ERS keywords: {', '.join(result.sustainability_keywords_found[:8])}")
    if result.carbon_footprint:
        print(f"  Carbon footprint: {result.carbon_footprint}")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Crawl a business school website and estimate EFMD readiness')
    parser.add_argument('url', help='School website URL (e.g., https://www.uwasa.fi/en)')
    parser.add_argument('--max-pages', type=int, default=75, help='Maximum pages to crawl (default: 75)')
    parser.add_argument('--delay', type=float, default=0.3, help='Delay between requests in seconds (default: 0.3)')
    parser.add_argument('--output', help='Save results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress crawl progress output')
    
    args = parser.parse_args()
    
    crawler = SchoolCrawler(
        base_url=args.url,
        max_pages=args.max_pages,
        delay=args.delay,
        verbose=not args.quiet
    )
    
    result = crawler.crawl()
    readiness = calculate_efmd_readiness(result)
    
    print_report(result, readiness)
    
    if args.output:
        output_data = {
            'crawl_result': asdict(result),
            'readiness': readiness
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
