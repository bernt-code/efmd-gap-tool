"""
EFMD OX Report - Data Source Summary

Shows realistic coverage by data source.
"""

from ox_requirements import OX_SECTIONS

def analyze_data_sources():
    """Analyze what percentage of data comes from each source"""
    
    sources = {
        "scrape": {"fields": [], "description": "Can be scraped from website"},
        "cvs": {"fields": [], "description": "Needs CV uploads"},
        "document": {"fields": [], "description": "Needs document uploads"},
        "manual": {"fields": [], "description": "School must input manually"},
        "infer": {"fields": [], "description": "Can be inferred from other data"},
        "auto": {"fields": [], "description": "Automatic (from URL)"},
    }
    
    for section_id, section in OX_SECTIONS.items():
        for field_id, field in section.get("fields", {}).items():
            source = field.get("source", "unknown")
            if source in sources:
                sources[source]["fields"].append({
                    "section": section_id,
                    "name": section["name"],
                    "field": field_id,
                    "required": field.get("required", True),
                })
    
    return sources


def print_summary():
    sources = analyze_data_sources()
    
    total_fields = sum(len(s["fields"]) for s in sources.values())
    
    print("=" * 70)
    print("EFMD OX REPORT - DATA SOURCE ANALYSIS")
    print("=" * 70)
    print()
    print(f"Total fields to fill: {total_fields}")
    print()
    
    print("DATA SOURCES BREAKDOWN:")
    print("-" * 70)
    
    for source, data in sources.items():
        count = len(data["fields"])
        pct = round(count / total_fields * 100, 1) if total_fields > 0 else 0
        print(f"\n{source.upper():12} {count:3} fields ({pct:5.1f}%) - {data['description']}")
        
        # Group by section
        by_section = {}
        for f in data["fields"]:
            sec = f["section"]
            if sec not in by_section:
                by_section[sec] = []
            by_section[sec].append(f["field"])
        
        for sec, fields in list(by_section.items())[:5]:
            print(f"             └─ {sec}: {', '.join(fields[:3])}" + ("..." if len(fields) > 3 else ""))
    
    print()
    print("=" * 70)
    print("REALISTIC COVERAGE ESTIMATE")
    print("=" * 70)
    
    scrape_pct = len(sources["scrape"]["fields"]) / total_fields * 100
    cvs_pct = len(sources["cvs"]["fields"]) / total_fields * 100
    doc_pct = len(sources["document"]["fields"]) / total_fields * 100
    auto_pct = len(sources["auto"]["fields"]) / total_fields * 100
    infer_pct = len(sources["infer"]["fields"]) / total_fields * 100
    manual_pct = len(sources["manual"]["fields"]) / total_fields * 100
    
    automated_total = scrape_pct + cvs_pct + doc_pct + auto_pct + infer_pct
    
    print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│ WHAT YOUR TOOL CAN AUTOMATE                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Website Scraping (school + programme URLs)     {scrape_pct:5.1f}%              │
│  CV Analysis (faculty + students + alumni)      {cvs_pct:5.1f}%              │
│  Document Extraction (handbooks, reports)       {doc_pct:5.1f}%               │
│  Auto-generated (from URLs)                     {auto_pct:5.1f}%               │
│  Inferred (from Dean CV, strategy)              {infer_pct:5.1f}%               │
│                                                ───────              │
│  TOTAL AUTOMATABLE                              {automated_total:5.1f}%              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ WHAT SCHOOL MUST INPUT MANUALLY                  {manual_pct:5.1f}%              │
│                                                                     │
│  • Contact details (project leader)                                 │
│  • EFMD membership info                                             │
│  • Confidential numbers (applicants, graduates, financials)         │
│  • Student mobility numbers                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
""")

    # Show what manual inputs are actually needed
    print("MANUAL INPUTS REQUIRED (what school types in):")
    print("-" * 70)
    
    manual_by_type = {
        "Contact info": [],
        "Admissions numbers": [],
        "Financial data": [],
        "Other numbers": [],
    }
    
    for f in sources["manual"]["fields"]:
        field = f["field"]
        if "email" in field or "phone" in field or "name" in field and "leader" in f["section"]:
            manual_by_type["Contact info"].append(f"{f['section']}.{field}")
        elif "applicant" in field or "offer" in field or "accept" in field or "enrol" in field:
            manual_by_type["Admissions numbers"].append(f"{f['section']}.{field}")
        elif "revenue" in field or "expenditure" in field or "surplus" in field:
            manual_by_type["Financial data"].append(f"{f['section']}.{field}")
        else:
            manual_by_type["Other numbers"].append(f"{f['section']}.{field}")
    
    for category, fields in manual_by_type.items():
        if fields:
            print(f"\n  {category}: ({len(fields)} fields)")
            for f in fields[:5]:
                print(f"    • {f}")
            if len(fields) > 5:
                print(f"    ... and {len(fields) - 5} more")


if __name__ == "__main__":
    print_summary()
