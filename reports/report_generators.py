#!/usr/bin/env python3
"""
EFMD Report Generators
======================
Generates the three core reports:
1. Data Collection Status Report
2. Gap Analysis Report  
3. Improvement Process Report
"""

import os
from datetime import datetime
from typing import Optional

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://bkhvztyvfkqzqqtoxxxi.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')


def generate_collection_status_report(programme_id: str, db: Client = None) -> str:
    """Report 1: Data collection progress."""
    if not db and HAS_SUPABASE and SUPABASE_KEY:
        db = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    if not db:
        return "Error: Database connection required"
    
    prog = db.table('programmes').select('*, institutions(*)').eq('id', programme_id).single().execute()
    if not prog.data:
        return "Error: Programme not found"
    
    institution_id = prog.data['institution_id']
    
    faculty = db.table('faculty_cvs').select('id, efmd_score, include_recommended').eq('institution_id', institution_id).execute()
    students = db.table('student_cvs').select('id, efmd_score, include_recommended').eq('programme_id', programme_id).execute()
    alumni = db.table('alumni_cvs').select('id, efmd_score, include_recommended').eq('programme_id', programme_id).execute()
    ilos = db.table('programme_ilos').select('id').eq('programme_id', programme_id).execute()
    
    def progress_bar(current, target, width=25):
        filled = int(width * min(current, target) / target) if target > 0 else 0
        bar = '█' * filled + '░' * (width - filled)
        pct = min(100, int(current / target * 100)) if target > 0 else 0
        status = '✅' if current >= target else '🔄'
        return f"{bar} {current}/{target} ({pct}%) {status}"
    
    lines = [
        "=" * 60,
        "DATA COLLECTION STATUS REPORT",
        "=" * 60,
        f"Programme: {prog.data['programme_name']}",
        f"Institution: {prog.data.get('institutions', {}).get('name', 'Unknown')}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "-" * 60,
        "COLLECTION PROGRESS",
        "-" * 60,
        f"  Faculty CVs:   {progress_bar(len(faculty.data or []), 25)}",
        f"  Student CVs:   {progress_bar(len(students.data or []), 50)}",
        f"  Alumni CVs:    {progress_bar(len(alumni.data or []), 40)}",
        f"  Programme ILOs: {progress_bar(len(ilos.data or []), 6)}",
        "",
    ]
    
    # Actions needed
    lines.append("-" * 60)
    lines.append("ACTIONS NEEDED")
    lines.append("-" * 60)
    
    if len(faculty.data or []) < 25:
        lines.append(f"  ⚠️ Collect {25 - len(faculty.data or [])} more faculty CVs")
    if len(students.data or []) < 50:
        lines.append(f"  ⚠️ Collect {50 - len(students.data or [])} more student CVs")
    if len(alumni.data or []) < 40:
        lines.append(f"  ⚠️ Collect {40 - len(alumni.data or [])} more alumni CVs")
    if len(ilos.data or []) < 5:
        lines.append(f"  ⚠️ Document programme ILOs (need 5-6)")
    
    if all([
        len(faculty.data or []) >= 25,
        len(students.data or []) >= 50,
        len(alumni.data or []) >= 40,
        len(ilos.data or []) >= 5
    ]):
        lines.append("  ✅ All data collection complete!")
    
    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def generate_gap_analysis_report(programme_id: str, db: Client = None) -> str:
    """Report 2: Full EFMD gap analysis."""
    if not db and HAS_SUPABASE and SUPABASE_KEY:
        db = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    if not db:
        return "Error: Database connection required"
    
    prog = db.table('programmes').select('*, institutions(*)').eq('id', programme_id).single().execute()
    if not prog.data:
        return "Error: Programme not found"
    
    gap = db.table('gap_analyses').select('*').eq('programme_id', programme_id).order('created_at', desc=True).limit(1).execute()
    ilos = db.table('programme_ilos').select('*').eq('programme_id', programme_id).execute()
    
    gap_data = gap.data[0] if gap.data else {}
    ilo_data = ilos.data or []
    readiness_score = gap_data.get('readiness_score', prog.data.get('readiness_score', 0)) or 0
    
    if readiness_score >= 80:
        status = "🟢 READY"
    elif readiness_score >= 60:
        status = "🟡 PARTIAL"
    elif readiness_score >= 40:
        status = "🟠 AT RISK"
    else:
        status = "🔴 NOT READY"
    
    lines = [
        "=" * 60,
        "EFMD GAP ANALYSIS REPORT",
        "=" * 60,
        f"Programme: {prog.data['programme_name']}",
        f"Institution: {prog.data.get('institutions', {}).get('name', 'Unknown')}",
        "",
        f"READINESS SCORE: {readiness_score}/100 — {status}",
        "",
    ]
    
    # Critical gaps
    critical_gaps = gap_data.get('critical_gaps', [])
    if critical_gaps:
        lines.append("-" * 60)
        lines.append("🚨 CRITICAL GAPS")
        lines.append("-" * 60)
        for g in critical_gaps:
            lines.append(f"  ❌ {g}")
        lines.append("")
    
    # ILO Analysis
    lines.append("-" * 60)
    lines.append("ILO ANALYSIS")
    lines.append("-" * 60)
    
    knowledge = sum(1 for i in ilo_data if i.get('ksa_category') == 'Knowledge')
    skills = sum(1 for i in ilo_data if i.get('ksa_category') == 'Skill')
    attitudes = sum(1 for i in ilo_data if i.get('ksa_category') == 'Attitude')
    weak = sum(1 for i in ilo_data if i.get('has_weak_verb'))
    
    lines.append(f"  ILO Count: {len(ilo_data)} (optimal: 5-6)")
    lines.append(f"  Knowledge: {'✅' if knowledge > 0 else '❌'} ({knowledge})")
    lines.append(f"  Skills: {'✅' if skills > 0 else '❌'} ({skills})")
    lines.append(f"  Attitudes: {'✅' if attitudes > 0 else '❌'} ({attitudes})")
    lines.append(f"  Weak verbs: {weak}")
    lines.append("")
    
    # Pillar coverage
    lines.append("-" * 60)
    lines.append("PILLAR COVERAGE")
    lines.append("-" * 60)
    
    pillar_coverage = gap_data.get('pillar_coverage', {})
    for pillar in ['International', 'Practice', 'ERS', 'Digital']:
        score = pillar_coverage.get(pillar, 0)
        if isinstance(score, (int, float)):
            pct = int(score * 100) if score <= 1 else int(score)
            icon = '✅' if pct >= 70 else ('🟡' if pct >= 50 else '❌')
        else:
            pct = 0
            icon = '❓'
        lines.append(f"  {pillar}: {icon} ({pct}%)")
    
    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def generate_improvement_report(programme_id: str, db: Client = None) -> str:
    """Report 3: Prioritized improvement plan."""
    if not db and HAS_SUPABASE and SUPABASE_KEY:
        db = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    if not db:
        return "Error: Database connection required"
    
    prog = db.table('programmes').select('*, institutions(*)').eq('id', programme_id).single().execute()
    if not prog.data:
        return "Error: Programme not found"
    
    gap = db.table('gap_analyses').select('*').eq('programme_id', programme_id).order('created_at', desc=True).limit(1).execute()
    ilos = db.table('programme_ilos').select('*').eq('programme_id', programme_id).execute()
    
    institution_id = prog.data['institution_id']
    faculty = db.table('faculty_cvs').select('id').eq('institution_id', institution_id).execute()
    alumni = db.table('alumni_cvs').select('id').eq('programme_id', programme_id).execute()
    
    gap_data = gap.data[0] if gap.data else {}
    ilo_data = ilos.data or []
    
    # Build actions
    actions = []
    
    # ILO issues
    if len(ilo_data) == 0:
        actions.append(('CRITICAL', 'Document Programme ILOs (5-6 covering K/S/A)', '2-4 weeks'))
    else:
        weak = sum(1 for i in ilo_data if i.get('has_weak_verb'))
        if weak > 0:
            actions.append(('HIGH', f'Rewrite {weak} ILOs with weak verbs', '1-2 weeks'))
        if len(ilo_data) > 8:
            actions.append(('MEDIUM', f'Consolidate {len(ilo_data)} ILOs to 5-6', '1-2 weeks'))
    
    # Pillar gaps
    pillar_coverage = gap_data.get('pillar_coverage', {})
    if pillar_coverage.get('ERS', 0) < 0.5:
        actions.append(('CRITICAL', 'Integrate ERS content into curriculum', '1 semester'))
    if pillar_coverage.get('International', 0) < 0.5:
        actions.append(('MEDIUM', 'Strengthen international dimension', '1-2 months'))
    
    # Data collection
    if len(faculty.data or []) < 25:
        actions.append(('HIGH', f'Collect {25 - len(faculty.data or [])} more faculty CVs', '2 weeks'))
    if len(alumni.data or []) < 40:
        actions.append(('HIGH', f'Collect {40 - len(alumni.data or [])} more alumni CVs', '3-4 weeks'))
    
    lines = [
        "=" * 60,
        "EFMD IMPROVEMENT PROCESS REPORT",
        "=" * 60,
        f"Programme: {prog.data['programme_name']}",
        f"Institution: {prog.data.get('institutions', {}).get('name', 'Unknown')}",
        "",
        f"Actions Required: {len(actions)}",
        f"Estimated Timeline: {gap_data.get('estimated_fix_months', 6)} months",
        "",
        "-" * 60,
        "PRIORITIZED ACTIONS",
        "-" * 60,
    ]
    
    for priority, action, effort in actions:
        icon = '🚨' if priority == 'CRITICAL' else ('⚠️' if priority == 'HIGH' else '📋')
        lines.append(f"  {icon} [{priority}] {action}")
        lines.append(f"      Effort: {effort}")
        lines.append("")
    
    if not actions:
        lines.append("  ✅ No major improvements needed!")
    
    lines.extend(["", "=" * 60])
    return "\n".join(lines)


if __name__ == "__main__":
    print("EFMD Report Generators")
    print("=" * 40)
    print("\nFunctions:")
    print("  generate_collection_status_report(programme_id)")
    print("  generate_gap_analysis_report(programme_id)")
    print("  generate_improvement_report(programme_id)")
