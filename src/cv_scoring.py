#!/usr/bin/env python3
"""
EFMD CV Scoring & Selection Optimizer
=====================================
Scores CVs against EFMD criteria and recommends optimal selection.

The goal: Cherry-pick the best CVs to maximize EFMD scores while
maintaining a defensible, representative sample.
"""

from dataclasses import dataclass
from typing import Optional
import json


# ============================================================
# SCORING WEIGHTS - Tuned for EFMD criteria
# ============================================================

FACULTY_WEIGHTS = {
    # Qualifications (35 points max)
    'has_doctorate': 20,
    'doctorate_from_intl': 5,
    'doctorate_recent': 5,      # Last 15 years
    'has_masters': 5,
    
    # Research Output (25 points max)
    'publications_5yr_1_3': 5,
    'publications_5yr_4_6': 10,
    'publications_5yr_7_plus': 15,
    'peer_reviewed_any': 5,
    'peer_reviewed_3_plus': 10,
    
    # International (20 points max)
    'international_degree': 8,
    'worked_abroad': 8,
    'visiting_position': 4,
    
    # Practice Connection (15 points max)
    'industry_experience': 8,
    'current_consulting': 4,
    'board_membership': 3,
    
    # ERS (5 points max)
    'ers_research': 3,
    'ers_teaching': 2,
}

STUDENT_WEIGHTS = {
    # Diversity Value (30 points max)
    'non_domestic_nationality': 15,
    'rare_nationality': 10,      # Adds diversity
    'gender_balance_help': 5,    # If underrepresented gender
    
    # Prior Education (30 points max)
    'quality_prior_institution': 15,
    'relevant_prior_degree': 10,
    'international_prior_degree': 5,
    
    # Work Experience (25 points max)
    'work_exp_1_2_years': 8,
    'work_exp_3_5_years': 15,
    'work_exp_5_plus': 20,
    'management_experience': 5,
    
    # Languages (15 points max)
    'multilingual_2': 5,
    'multilingual_3_plus': 10,
    'english_fluent': 5,
}

ALUMNI_WEIGHTS = {
    # Employment Speed (25 points max)
    'employed': 10,
    'employed_within_3_months': 15,
    'employed_within_6_months': 10,
    
    # Employer Quality (30 points max)
    'fortune_500': 15,
    'big_4_mbb': 20,
    'multinational': 10,
    'major_bank': 12,
    'known_employer': 5,
    
    # Career Progression (25 points max)
    'senior_level': 15,
    'executive_level': 20,
    'visible_promotion': 10,
    
    # International (20 points max)
    'working_abroad': 15,
    'international_career': 5,
}


# ============================================================
# FACULTY SCORER
# ============================================================

@dataclass
class FacultyScore:
    total_score: int
    breakdown: dict
    inclusion_reasons: list[str]
    exclusion_risks: list[str]
    recommend_include: bool


def score_faculty_cv(cv_data: dict, institution_country: str = None) -> FacultyScore:
    """
    Score a faculty CV for EFMD selection.
    
    Args:
        cv_data: Parsed CV data (from Claude extraction)
        institution_country: Country of the institution (for international calc)
    
    Returns:
        FacultyScore with total, breakdown, and recommendation
    """
    score = 0
    breakdown = {}
    reasons = []
    risks = []
    
    # === QUALIFICATIONS ===
    highest = cv_data.get('highest_degree', {})
    degree = (highest.get('degree') or '').upper()
    
    if any(d in degree for d in ['PHD', 'DBA', 'DPHIL', 'DOCTOR', 'DR.']):
        score += FACULTY_WEIGHTS['has_doctorate']
        breakdown['has_doctorate'] = FACULTY_WEIGHTS['has_doctorate']
        reasons.append('Holds doctoral degree')
        
        # International doctorate
        degree_country = highest.get('country', '')
        if institution_country and degree_country and degree_country.lower() != institution_country.lower():
            score += FACULTY_WEIGHTS['doctorate_from_intl']
            breakdown['doctorate_from_intl'] = FACULTY_WEIGHTS['doctorate_from_intl']
            reasons.append(f'Doctorate from {degree_country}')
        
        # Recent doctorate
        degree_year = highest.get('year')
        if degree_year and degree_year >= 2010:
            score += FACULTY_WEIGHTS['doctorate_recent']
            breakdown['doctorate_recent'] = FACULTY_WEIGHTS['doctorate_recent']
    else:
        risks.append('No doctoral degree')
        if any(d in degree for d in ['MBA', 'MSC', 'MA', 'MASTER']):
            score += FACULTY_WEIGHTS['has_masters']
            breakdown['has_masters'] = FACULTY_WEIGHTS['has_masters']
    
    # === RESEARCH OUTPUT ===
    pubs = cv_data.get('publications_last_5_years', {})
    total_pubs = pubs.get('total', 0) or 0
    peer_reviewed = pubs.get('peer_reviewed_journals', 0) or 0
    
    if total_pubs >= 7:
        score += FACULTY_WEIGHTS['publications_5yr_7_plus']
        breakdown['publications'] = FACULTY_WEIGHTS['publications_5yr_7_plus']
        reasons.append(f'{total_pubs} publications in 5 years')
    elif total_pubs >= 4:
        score += FACULTY_WEIGHTS['publications_5yr_4_6']
        breakdown['publications'] = FACULTY_WEIGHTS['publications_5yr_4_6']
        reasons.append(f'{total_pubs} publications in 5 years')
    elif total_pubs >= 1:
        score += FACULTY_WEIGHTS['publications_5yr_1_3']
        breakdown['publications'] = FACULTY_WEIGHTS['publications_5yr_1_3']
    else:
        risks.append('No recent publications')
    
    if peer_reviewed >= 3:
        score += FACULTY_WEIGHTS['peer_reviewed_3_plus']
        breakdown['peer_reviewed'] = FACULTY_WEIGHTS['peer_reviewed_3_plus']
        reasons.append('Strong peer-reviewed output')
    elif peer_reviewed >= 1:
        score += FACULTY_WEIGHTS['peer_reviewed_any']
        breakdown['peer_reviewed'] = FACULTY_WEIGHTS['peer_reviewed_any']
    
    # === INTERNATIONAL ===
    intl = cv_data.get('international_experience', {})
    
    if intl.get('has_international_degree'):
        score += FACULTY_WEIGHTS['international_degree']
        breakdown['international_degree'] = FACULTY_WEIGHTS['international_degree']
        reasons.append('International degree')
    
    if intl.get('worked_abroad'):
        score += FACULTY_WEIGHTS['worked_abroad']
        breakdown['worked_abroad'] = FACULTY_WEIGHTS['worked_abroad']
        reasons.append('International work experience')
    
    if intl.get('visiting_positions'):
        score += FACULTY_WEIGHTS['visiting_position']
        breakdown['visiting_position'] = FACULTY_WEIGHTS['visiting_position']
    
    if not intl.get('has_international_degree') and not intl.get('worked_abroad'):
        risks.append('Limited international exposure')
    
    # === PRACTICE CONNECTION ===
    industry = cv_data.get('industry_experience', {})
    
    if (industry.get('total_years') or 0) > 2:
        score += FACULTY_WEIGHTS['industry_experience']
        breakdown['industry_experience'] = FACULTY_WEIGHTS['industry_experience']
        reasons.append(f"{industry.get('total_years')} years industry experience")
    
    if industry.get('current_consulting'):
        score += FACULTY_WEIGHTS['current_consulting']
        breakdown['current_consulting'] = FACULTY_WEIGHTS['current_consulting']
        reasons.append('Active consulting')
    
    if industry.get('board_memberships'):
        score += FACULTY_WEIGHTS['board_membership']
        breakdown['board_membership'] = FACULTY_WEIGHTS['board_membership']
    
    # === ERS ===
    ers = cv_data.get('ers_activities', {})
    
    if ers.get('has_ers_research'):
        score += FACULTY_WEIGHTS['ers_research']
        breakdown['ers_research'] = FACULTY_WEIGHTS['ers_research']
        reasons.append('ERS research focus')
    
    if ers.get('has_ers_teaching'):
        score += FACULTY_WEIGHTS['ers_teaching']
        breakdown['ers_teaching'] = FACULTY_WEIGHTS['ers_teaching']
    
    # === RECOMMENDATION ===
    # Recommend if score >= 50 or has critical strengths
    recommend = score >= 50 or (score >= 35 and 'has_doctorate' in breakdown)
    
    return FacultyScore(
        total_score=min(100, score),
        breakdown=breakdown,
        inclusion_reasons=reasons,
        exclusion_risks=risks,
        recommend_include=recommend
    )


# ============================================================
# STUDENT SCORER
# ============================================================

@dataclass
class StudentScore:
    total_score: int
    breakdown: dict
    inclusion_reasons: list[str]
    exclusion_risks: list[str]
    recommend_include: bool
    diversity_value: str  # 'high', 'medium', 'low'


def score_student_cv(cv_data: dict, 
                     institution_country: str = None,
                     existing_nationalities: list[str] = None,
                     gender_balance: dict = None) -> StudentScore:
    """
    Score a student CV for EFMD selection.
    
    Args:
        cv_data: Parsed CV data
        institution_country: For determining domestic vs international
        existing_nationalities: Already selected nationalities (for diversity)
        gender_balance: {'male': x, 'female': y} of current selection
    """
    score = 0
    breakdown = {}
    reasons = []
    risks = []
    diversity = 'medium'
    
    existing_nationalities = existing_nationalities or []
    gender_balance = gender_balance or {'male': 0, 'female': 0}
    
    # === DIVERSITY VALUE ===
    demographics = cv_data.get('demographics', {})
    nationality = demographics.get('nationality', '')
    gender = demographics.get('gender', '')
    
    # International student
    if nationality and institution_country:
        if nationality.lower() != institution_country.lower():
            score += FACULTY_WEIGHTS.get('non_domestic_nationality', 15)
            breakdown['international'] = 15
            reasons.append(f'International student ({nationality})')
            diversity = 'high'
            
            # Rare nationality bonus
            if nationality not in existing_nationalities:
                score += 10
                breakdown['rare_nationality'] = 10
                reasons.append('Adds new nationality to cohort')
    else:
        risks.append('Domestic student (less diversity value)')
    
    # Gender balance
    if gender:
        if gender.lower() == 'female' and gender_balance.get('male', 0) > gender_balance.get('female', 0) * 1.5:
            score += 5
            breakdown['gender_balance'] = 5
            reasons.append('Improves gender balance')
        elif gender.lower() == 'male' and gender_balance.get('female', 0) > gender_balance.get('male', 0) * 1.5:
            score += 5
            breakdown['gender_balance'] = 5
    
    # === PRIOR EDUCATION ===
    prior = cv_data.get('prior_education', {}).get('highest_degree', {})
    
    if prior.get('is_business_related'):
        score += 10
        breakdown['relevant_degree'] = 10
        reasons.append('Business-related prior degree')
    
    prior_country = prior.get('country', '')
    if prior_country and institution_country and prior_country.lower() != institution_country.lower():
        score += 5
        breakdown['international_prior'] = 5
        reasons.append(f'Prior degree from {prior_country}')
    
    # === WORK EXPERIENCE ===
    work = cv_data.get('work_experience', {})
    years = work.get('total_years', 0) or 0
    
    if years >= 5:
        score += 20
        breakdown['work_experience'] = 20
        reasons.append(f'{years} years work experience')
    elif years >= 3:
        score += 15
        breakdown['work_experience'] = 15
        reasons.append(f'{years} years work experience')
    elif years >= 1:
        score += 8
        breakdown['work_experience'] = 8
    else:
        risks.append('No work experience')
    
    if work.get('has_management_experience'):
        score += 5
        breakdown['management'] = 5
        reasons.append('Management experience')
    
    # === LANGUAGES ===
    languages = cv_data.get('languages', [])
    if len(languages) >= 3:
        score += 10
        breakdown['multilingual'] = 10
        reasons.append(f'Speaks {len(languages)} languages')
    elif len(languages) >= 2:
        score += 5
        breakdown['multilingual'] = 5
    
    # === RECOMMENDATION ===
    recommend = score >= 40 or diversity == 'high'
    
    return StudentScore(
        total_score=min(100, score),
        breakdown=breakdown,
        inclusion_reasons=reasons,
        exclusion_risks=risks,
        recommend_include=recommend,
        diversity_value=diversity
    )


# ============================================================
# ALUMNI SCORER
# ============================================================

@dataclass
class AlumniScore:
    total_score: int
    breakdown: dict
    inclusion_reasons: list[str]
    exclusion_risks: list[str]
    recommend_include: bool
    employment_speed: str  # 'fast', 'normal', 'slow', 'unemployed'


def score_alumni_cv(cv_data: dict, institution_country: str = None) -> AlumniScore:
    """
    Score an alumni CV for EFMD selection.
    Focus on employment outcomes - this is what EFMD cares about most.
    """
    score = 0
    breakdown = {}
    reasons = []
    risks = []
    employment_speed = 'normal'
    
    current = cv_data.get('current_employment', {})
    first_job = cv_data.get('first_job_after_graduation', {})
    career = cv_data.get('career_progression', {})
    prestige = cv_data.get('employer_prestige_indicators', {})
    intl = cv_data.get('international_career', {})
    
    # === EMPLOYMENT STATUS ===
    if current.get('is_employed'):
        score += 10
        breakdown['employed'] = 10
        
        # Time to employment
        months = first_job.get('months_to_employment')
        if months is not None:
            if months <= 3:
                score += 15
                breakdown['fast_employment'] = 15
                reasons.append('Employed within 3 months')
                employment_speed = 'fast'
            elif months <= 6:
                score += 10
                breakdown['fast_employment'] = 10
                reasons.append('Employed within 6 months')
                employment_speed = 'normal'
            else:
                employment_speed = 'slow'
                risks.append(f'Took {months} months to find employment')
    else:
        risks.append('Currently unemployed')
        employment_speed = 'unemployed'
    
    # === EMPLOYER QUALITY ===
    if prestige.get('is_mbb') or prestige.get('is_big_4'):
        score += 20
        breakdown['prestige_employer'] = 20
        reasons.append('Top-tier employer (MBB/Big4)')
    elif prestige.get('is_fortune_500'):
        score += 15
        breakdown['prestige_employer'] = 15
        reasons.append('Fortune 500 employer')
    elif prestige.get('is_major_bank'):
        score += 12
        breakdown['prestige_employer'] = 12
        reasons.append('Major financial institution')
    elif prestige.get('is_multinational'):
        score += 10
        breakdown['prestige_employer'] = 10
        reasons.append('Multinational employer')
    
    employer = current.get('employer', '')
    if employer:
        reasons.append(f'Currently at {employer}')
    
    # === CAREER PROGRESSION ===
    seniority = current.get('seniority_level', '').lower()
    
    if seniority == 'executive':
        score += 20
        breakdown['seniority'] = 20
        reasons.append('Executive level position')
    elif seniority == 'senior':
        score += 15
        breakdown['seniority'] = 15
        reasons.append('Senior level position')
    elif seniority == 'mid':
        score += 8
        breakdown['seniority'] = 8
    
    promotions = career.get('promotions_visible', 0)
    if promotions and promotions >= 2:
        score += 10
        breakdown['career_growth'] = 10
        reasons.append(f'{promotions} promotions since graduation')
    
    # === INTERNATIONAL ===
    if intl.get('currently_abroad') or current.get('is_international'):
        score += 15
        breakdown['international'] = 15
        reasons.append('Working internationally')
    elif intl.get('worked_abroad'):
        score += 5
        breakdown['international'] = 5
    
    # === RECOMMENDATION ===
    # Always recommend if employed at good company, unless slow employment
    recommend = (score >= 45) or (score >= 30 and employment_speed in ['fast', 'normal'])
    
    return AlumniScore(
        total_score=min(100, score),
        breakdown=breakdown,
        inclusion_reasons=reasons,
        exclusion_risks=risks,
        recommend_include=recommend,
        employment_speed=employment_speed
    )


# ============================================================
# SELECTION OPTIMIZER
# ============================================================

class SelectionOptimizer:
    """
    Optimizes CV selection to maximize EFMD metrics while
    maintaining representativeness.
    """
    
    def __init__(self, institution_country: str = None):
        self.institution_country = institution_country
    
    def optimize_faculty_selection(self, 
                                   faculty_list: list[dict], 
                                   target_count: int = 25,
                                   min_female_pct: float = 0.30,
                                   min_phd_pct: float = 0.70) -> dict:
        """
        Select optimal faculty subset.
        
        Returns:
            {
                'selected': [...],
                'alternates': [...],
                'metrics': {...},
                'comparison': {'all': {...}, 'selected': {...}}
            }
        """
        # Score all faculty
        scored = []
        for f in faculty_list:
            score = score_faculty_cv(f, self.institution_country)
            scored.append({
                'cv': f,
                'score': score,
                'name': f.get('full_name', 'Unknown')
            })
        
        # Sort by score
        scored.sort(key=lambda x: x['score'].total_score, reverse=True)
        
        # Initial selection: top scorers
        selected = []
        remaining = scored.copy()
        
        # First pass: take top scorers
        for item in scored[:target_count]:
            selected.append(item)
            remaining.remove(item)
        
        # Check constraints and swap if needed
        selected = self._balance_faculty_selection(
            selected, remaining, 
            min_female_pct, min_phd_pct
        )
        
        # Calculate metrics
        all_metrics = self._calc_faculty_metrics(scored)
        selected_metrics = self._calc_faculty_metrics(selected)
        
        return {
            'selected': [s['cv'] for s in selected[:target_count]],
            'selected_scores': [s['score'] for s in selected[:target_count]],
            'alternates': [s['cv'] for s in remaining[:5]],
            'metrics': selected_metrics,
            'comparison': {
                'all_faculty': all_metrics,
                'selected': selected_metrics,
                'improvement': {
                    'phd_pct': selected_metrics['phd_pct'] - all_metrics['phd_pct'],
                    'intl_pct': selected_metrics['international_pct'] - all_metrics['international_pct'],
                    'avg_publications': selected_metrics['avg_publications'] - all_metrics['avg_publications'],
                }
            }
        }
    
    def _balance_faculty_selection(self, selected, remaining, min_female, min_phd):
        """Swap to meet diversity requirements"""
        # This is simplified - real implementation would be more sophisticated
        return selected
    
    def _calc_faculty_metrics(self, faculty_list) -> dict:
        """Calculate aggregate metrics for a faculty list"""
        if not faculty_list:
            return {}
        
        total = len(faculty_list)
        phd_count = sum(1 for f in faculty_list 
                       if 'has_doctorate' in f['score'].breakdown)
        intl_count = sum(1 for f in faculty_list 
                        if 'international_degree' in f['score'].breakdown 
                        or 'worked_abroad' in f['score'].breakdown)
        
        return {
            'total': total,
            'phd_count': phd_count,
            'phd_pct': round(phd_count / total * 100, 1) if total else 0,
            'international_count': intl_count,
            'international_pct': round(intl_count / total * 100, 1) if total else 0,
            'avg_score': round(sum(f['score'].total_score for f in faculty_list) / total, 1) if total else 0,
            'avg_publications': 0,  # Would need to aggregate from CV data
        }
    
    def optimize_alumni_selection(self,
                                  alumni_list: list[dict],
                                  target_count: int = 30) -> dict:
        """
        Select optimal alumni subset - prioritize employment outcomes.
        """
        scored = []
        for a in alumni_list:
            score = score_alumni_cv(a, self.institution_country)
            scored.append({
                'cv': a,
                'score': score,
                'name': a.get('full_name', 'Unknown')
            })
        
        # Sort by score
        scored.sort(key=lambda x: x['score'].total_score, reverse=True)
        
        selected = scored[:target_count]
        remaining = scored[target_count:]
        
        # Calculate employment metrics
        all_metrics = self._calc_alumni_metrics(scored)
        selected_metrics = self._calc_alumni_metrics(selected)
        
        return {
            'selected': [s['cv'] for s in selected],
            'selected_scores': [s['score'] for s in selected],
            'alternates': [s['cv'] for s in remaining[:5]],
            'metrics': selected_metrics,
            'comparison': {
                'all_alumni': all_metrics,
                'selected': selected_metrics,
                'improvement': {
                    'employment_rate': selected_metrics['employment_rate'] - all_metrics['employment_rate'],
                    'avg_months_to_job': all_metrics['avg_months_to_job'] - selected_metrics['avg_months_to_job'],
                    'intl_pct': selected_metrics['working_abroad_pct'] - all_metrics['working_abroad_pct'],
                }
            }
        }
    
    def _calc_alumni_metrics(self, alumni_list) -> dict:
        if not alumni_list:
            return {}
        
        total = len(alumni_list)
        employed = sum(1 for a in alumni_list 
                      if a['score'].employment_speed != 'unemployed')
        fast_employed = sum(1 for a in alumni_list 
                          if a['score'].employment_speed == 'fast')
        intl = sum(1 for a in alumni_list 
                  if 'international' in a['score'].breakdown)
        
        return {
            'total': total,
            'employed': employed,
            'employment_rate': round(employed / total * 100, 1) if total else 0,
            'fast_employment_count': fast_employed,
            'fast_employment_pct': round(fast_employed / total * 100, 1) if total else 0,
            'working_abroad': intl,
            'working_abroad_pct': round(intl / total * 100, 1) if total else 0,
            'avg_score': round(sum(a['score'].total_score for a in alumni_list) / total, 1) if total else 0,
            'avg_months_to_job': 0,  # Would calculate from CV data
        }


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    # Demo with sample faculty CV
    sample_faculty = {
        'full_name': 'Dr. Maria Virtanen',
        'highest_degree': {
            'degree': 'PhD',
            'field': 'Marketing',
            'institution': 'Stockholm School of Economics',
            'country': 'Sweden',
            'year': 2012
        },
        'publications_last_5_years': {
            'total': 8,
            'peer_reviewed_journals': 5,
            'practice_oriented_journals': 2,
            'conference_papers': 1
        },
        'international_experience': {
            'has_international_degree': True,
            'worked_abroad': True,
            'work_abroad_countries': ['Sweden', 'USA']
        },
        'industry_experience': {
            'total_years': 4,
            'current_consulting': True,
            'board_memberships': ['TechStartup Oy']
        },
        'ers_activities': {
            'has_ers_research': False,
            'has_ers_teaching': False
        }
    }
    
    result = score_faculty_cv(sample_faculty, institution_country='Finland')
    
    print("=" * 60)
    print("FACULTY CV SCORING DEMO")
    print("=" * 60)
    print(f"\nName: {sample_faculty['full_name']}")
    print(f"\nTotal EFMD Score: {result.total_score}/100")
    print(f"Recommend Include: {'✅ YES' if result.recommend_include else '❌ NO'}")
    print(f"\nScore Breakdown:")
    for key, value in result.breakdown.items():
        print(f"  {key}: +{value}")
    print(f"\nStrengths:")
    for reason in result.inclusion_reasons:
        print(f"  ✓ {reason}")
    print(f"\nRisks:")
    for risk in result.exclusion_risks:
        print(f"  ⚠ {risk}")
