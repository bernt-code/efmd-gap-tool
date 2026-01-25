# EFMD School Website Crawler

Crawls any business school website and estimates EFMD accreditation readiness based on publicly available data.

## Quick Start

```bash
# Install dependencies
pip install requests beautifulsoup4 lxml

# Run crawler
python run_crawler.py https://www.uwasa.fi/en

# With options
python run_crawler.py https://www.uwasa.fi/en --max-pages 100 --output vaasa.json
```

## What It Does

1. **Crawls** the entire school website (respects robots, adds delays)
2. **Extracts** EFMD-relevant data:
   - Institution info (name, address, leadership)
   - Key figures (students, graduates, publications, personnel)
   - International dimension (% international staff/students, partners)
   - ERS/Sustainability content
   - Accreditations
   - Programmes offered
   - Faculty list
3. **Scores** readiness against EFMD criteria (0-100%)
4. **Reports** findings and gaps

## Output Example

```
======================================================================
EFMD ACCREDITATION READINESS REPORT
School: University of Vaasa
======================================================================

         🎯 OVERALL READINESS SCORE: 90%
              (86/95 points)

   💚 HIGH POTENTIAL - Strong candidate for EFMD accreditation

----------------------------------------------------------------------
DETAILED ASSESSMENT:
----------------------------------------------------------------------
  ✅ Publications              774                  Excellent research output
  ✅ International Staff       25.0%                Strong international faculty
  ⚠️ International Students    11.0%                Moderate international presence
  ✅ Accreditations            AACSB, EFMD, FINEEC  Major accreditation(s) held
  ✅ Ers                       8 keywords           Strong ERS presence
  ✅ Graduates                 712                  Mature programmes
```

## Benchmark: University of Vaasa

Vaasa is a **best practice** example:
- 4 EFMD programme accreditations
- AACSB accredited
- EQUIS finalist
- Strong international profile

Most schools will score **lower** than Vaasa. Use their score as the target.

## Files

- `run_crawler.py` - Main crawler with CLI
- `school_crawler.py` - Crawler class (can be imported)
- `ox_requirements.py` - EFMD OX Report field mappings
- `cv_training_guides.py` - What CVs should include for EFMD

## Use Cases

### 1. Self-Assessment
```bash
python run_crawler.py https://your-school.edu --output self_assessment.json
```

### 2. Lead Generation (for Edtech)
Crawl EFMD member schools to find high-potential prospects:
```bash
python run_crawler.py https://school1.edu --output school1.json --quiet
python run_crawler.py https://school2.edu --output school2.json --quiet
# ... compare scores
```

### 3. Gap Analysis
Run crawler, then check `readiness['details']` for specific gaps.

## Limitations

- Only extracts **publicly available** data
- Cannot access password-protected content
- Some numbers may be institution-wide (not programme-specific)
- Financial data rarely public
- CV-level data (faculty qualifications, publications) needs separate upload

## Next Steps After Crawling

1. **High score (70%+)**: Ready for EFMD. Collect CVs, refine programme data.
2. **Medium score (50-70%)**: Address gaps shown in report.
3. **Low score (<50%)**: Significant development needed before applying.

## Contact

Edtech Solutions  
bernt@edtechsolutions.io
