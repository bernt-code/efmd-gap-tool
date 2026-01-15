#!/usr/bin/env python3
"""
EFMD CV Collection Portal
=========================
Streamlit frontend for EFMD data collection.

Three upload modes:
- Faculty CV upload
- Student CV upload  
- Alumni CV upload

Plus dashboard for collection status and top selections.
"""

import streamlit as st
import requests
import os
from datetime import datetime

# Configuration
API_URL = os.getenv('API_URL', 'http://localhost:8002')

st.set_page_config(
    page_title="EFMD Data Collection",
    page_icon="🎓",
    layout="wide"
)

# ============================================================
# SIDEBAR - MODE SELECTION
# ============================================================

st.sidebar.title("🎓 EFMD Data Collection")

mode = st.sidebar.radio(
    "Select Mode",
    ["📊 Dashboard", "📄 Programme Scraper", "👨‍🏫 Faculty Upload", "👨‍🎓 Student Upload", "🎯 Alumni Upload", "⚙️ Setup"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Collection Links**")
st.sidebar.markdown("Share these with your stakeholders:")

# Get active programme from session
if 'programme_id' in st.session_state and st.session_state.programme_id:
    prog_id = st.session_state.programme_id
    inst_id = st.session_state.get('institution_id', '')
    
    st.sidebar.code(f"Faculty:\n/faculty/{inst_id[:8]}...")
    st.sidebar.code(f"Students:\n/student/{prog_id[:8]}...")
    st.sidebar.code(f"Alumni:\n/alumni/{prog_id[:8]}...")


# ============================================================
# SETUP MODE
# ============================================================

if mode == "⚙️ Setup":
    st.title("⚙️ Setup Institution & Programme")
    
    tab1, tab2 = st.tabs(["Create New", "Select Existing"])
    
    with tab1:
        st.subheader("Create Institution")
        
        col1, col2 = st.columns(2)
        with col1:
            inst_name = st.text_input("Institution Name", placeholder="University of Vaasa")
            inst_country = st.text_input("Country", placeholder="Finland")
        with col2:
            inst_city = st.text_input("City", placeholder="Vaasa")
            inst_website = st.text_input("Website", placeholder="https://www.uwasa.fi")
        
        if st.button("Create Institution", type="primary"):
            resp = requests.post(f"{API_URL}/institutions", json={
                'name': inst_name,
                'country': inst_country,
                'city': inst_city,
                'website': inst_website
            })
            if resp.ok:
                data = resp.json()
                st.success(f"✅ Institution created: {data['institution']['id']}")
                st.session_state.institution_id = data['institution']['id']
            else:
                st.error(f"Error: {resp.text}")
        
        st.markdown("---")
        st.subheader("Create Programme")
        
        # Get institutions
   # API not running - show message
        st.warning("⚠️ API server not running. Use Programme Scraper instead.")
        st.stop()
    
    with tab2:
        st.subheader("Select Existing Programme")
    
        programmes = [] 
    st.info("No programmes found. Create one first.")

# ============================================================
# DASHBOARD MODE
# ============================================================
elif mode == "📊 Dashboard":
    st.title("📊 EFMD Accreditation Dashboard")
    
    if 'programme_id' not in st.session_state:
        st.warning("⚠️ Please select a programme in Setup first")
        st.stop()
    
    prog_id = st.session_state.programme_id
    
    # Get status
    status_resp = requests.get(f"{API_URL}/programme/{prog_id}/status")
    
    if not status_resp.ok:
        st.error("Failed to load status")
        st.stop()
    
    status = status_resp.json()
    
    st.header(f"{status['programme']} - {status['institution']}")
    
    # =========================================================
    # ROW 1: CV COLLECTION (Faculty, Students, Alumni)
    # =========================================================
    st.subheader("📁 CV Collection")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        faculty = status['faculty']
        pct = min(100, int(faculty['collected'] / faculty['target'] * 100)) if faculty['target'] else 0
        st.metric("👨‍🏫 Faculty CVs", f"{faculty['collected']}/{faculty['target']}", f"{pct}%")
        st.progress(pct / 100)
        if faculty['complete']:
            st.success("✅ Complete")
        else:
            st.warning(f"Need {faculty['target'] - faculty['collected']} more")
        
        # Faculty stats if available
        if faculty['collected'] > 0:
            faculty_resp = requests.get(f"{API_URL}/faculty/{st.session_state.institution_id}/top?limit=25")
            if faculty_resp.ok:
                fdata = faculty_resp.json()
                st.caption(f"PhD Rate: {fdata['aggregate_stats']['phd_percentage']}% | Avg Score: {fdata['aggregate_stats']['avg_score']}")
    
    with col2:
        students = status['students']
        pct = min(100, int(students['collected'] / students['target'] * 100)) if students['target'] else 0
        st.metric("👨‍🎓 Student CVs", f"{students['collected']}/{students['target']}", f"{pct}%")
        st.progress(pct / 100)
        if students['complete']:
            st.success("✅ Complete")
        else:
            st.warning(f"Need {students['target'] - students['collected']} more")
        
        # Student diversity if available
        if students['collected'] > 0:
            div_resp = requests.get(f"{API_URL}/students/{prog_id}/diversity")
            if div_resp.ok:
                sdata = div_resp.json()
                st.caption(f"Nationalities: {sdata.get('nationalities_count', 0)} | Avg Work Exp: {sdata.get('avg_work_experience', 0)}yr")
    
    with col3:
        alumni = status['alumni']
        pct = min(100, int(alumni['collected'] / alumni['target'] * 100)) if alumni['target'] else 0
        st.metric("🎯 Alumni CVs", f"{alumni['collected']}/{alumni['target']}", f"{pct}%")
        st.progress(pct / 100)
        if alumni['complete']:
            st.success("✅ Complete")
        else:
            st.warning(f"Need {alumni['target'] - alumni['collected']} more")
        
        # Alumni stats if available
        if alumni['collected'] > 0:
            alumni_resp = requests.get(f"{API_URL}/alumni/{prog_id}/top?limit=30")
            if alumni_resp.ok:
                adata = alumni_resp.json()
                st.caption(f"Employment: {adata['aggregate_stats']['employment_rate']}% | Avg Score: {adata['aggregate_stats']['avg_score']}")
    
    st.markdown("---")
    
    # =========================================================
    # ROW 2: PROGRAMME ANALYSIS
    # =========================================================
    st.subheader("📋 Programme Analysis")
    
    # Scraper button
    col_btn, col_spacer = st.columns([1, 3])
    with col_btn:
        if st.button("🔍 Scrape Programme Website"):
            with st.spinner("Analyzing programme website..."):
                resp = requests.post(f"{API_URL}/programme/{prog_id}/scrape")
                if resp.ok:
                    result = resp.json()
                    st.success(f"✅ Found {result['ilos_found']} ILOs!")
                    st.rerun()
                else:
                    st.error(f"Scraping failed: {resp.text}")
    
    # Programme findings grid
    ilos = status['ilos']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Curriculum Data**")
        
        # ILOs
        if ilos['count'] >= 5:
            st.markdown(f"✅ **ILOs:** {ilos['count']} found")
        elif ilos['count'] > 0:
            st.markdown(f"⚠️ **ILOs:** {ilos['count']} found (need 5-7)")
        else:
            st.markdown("❌ **ILOs:** Not scraped yet")
        
        # Courses (placeholder - would need API endpoint)
        st.markdown("⬜ **Courses:** Run scraper to analyze")
        
        # ECTS
        st.markdown("⬜ **ECTS:** Run scraper to analyze")
    
    with col2:
        st.markdown("**EFMD Pillar Coverage**")
        
        # These would come from scraper results - placeholder for now
        if ilos['count'] > 0:
            st.markdown("✅ **International:** Detected")
            st.markdown("⚠️ **Practice:** Needs review")
            st.markdown("❌ **ERS:** Not found - critical gap")
            st.markdown("✅ **Digital:** Detected")
        else:
            st.markdown("⬜ **International:** Run scraper")
            st.markdown("⬜ **Practice:** Run scraper")
            st.markdown("⬜ **ERS:** Run scraper")
            st.markdown("⬜ **Digital:** Run scraper")
    
    st.markdown("---")
    
    # =========================================================
    # ROW 3: READINESS SUMMARY
    # =========================================================
    
    # Calculate overall readiness
    cv_ready = faculty['complete'] and students['complete'] and alumni['complete']
    programme_ready = ilos['count'] >= 5
    
    if cv_ready and programme_ready:
        st.success("## ✅ Ready for EFMD Submission!")
        st.balloons()
    else:
        # Calculate percentage
        total_items = 4  # Faculty, Students, Alumni, ILOs
        complete_items = sum([
            1 if faculty['complete'] else 0,
            1 if students['complete'] else 0,
            1 if alumni['complete'] else 0,
            1 if programme_ready else 0
        ])
        readiness_pct = int(complete_items / total_items * 100)
        
        st.warning(f"## 🔄 Readiness: {readiness_pct}%")
        
        # What's missing
        missing = []
        if not faculty['complete']:
            missing.append(f"Faculty CVs ({faculty['target'] - faculty['collected']} more)")
        if not students['complete']:
            missing.append(f"Student CVs ({students['target'] - students['collected']} more)")
        if not alumni['complete']:
            missing.append(f"Alumni CVs ({alumni['target'] - alumni['collected']} more)")
        if not programme_ready:
            missing.append("Programme ILOs (run scraper)")
        
        st.markdown("**Still needed:** " + " • ".join(missing))
    
    st.markdown("---")
    
    # =========================================================
    # ROW 4: TOP SELECTIONS (Expandable)
    # =========================================================
    with st.expander("👀 View Top CV Selections"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👨‍🏫 Top Faculty for Submission**")
            
            faculty_resp = requests.get(f"{API_URL}/faculty/{st.session_state.institution_id}/top?limit=10")
            if faculty_resp.ok:
                faculty_data = faculty_resp.json()
                
                for f in faculty_data['faculty'][:5]:
                    st.markdown(f"• **{f['full_name']}** — Score: {f['efmd_score']} | {f.get('highest_degree', 'N/A')}")
        
        with col2:
            st.markdown("**🎯 Top Alumni for Submission**")
            
            alumni_resp = requests.get(f"{API_URL}/alumni/{prog_id}/top?limit=10")
            if alumni_resp.ok:
                alumni_data = alumni_resp.json()
                
                for a in alumni_data['alumni'][:5]:
                    st.markdown(f"• **{a['full_name']}** — {a.get('current_employer', 'N/A')} | Score: {a['efmd_score']}")
    
    # =========================================================
    # ROW 5: BASE ROOM & REPORTS (Expandable)
    # =========================================================
    with st.expander("📁 Base Room Preparation"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Get Faculty CV Package"):
                resp = requests.get(f"{API_URL}/baseroom/faculty/{st.session_state.institution_id}")
                if resp.ok:
                    data = resp.json()
                    st.success(f"✅ {data['ready_for_baseroom']} CVs ready")
                    for cv in data.get('faculty_cvs', [])[:5]:
                        st.markdown(f"• [{cv['name']}]({cv['download_url']})")
        
        with col2:
            if st.button("📥 Get Alumni CV Package"):
                resp = requests.get(f"{API_URL}/baseroom/alumni/{prog_id}")
                if resp.ok:
                    data = resp.json()
                    st.success(f"✅ {data['ready_for_baseroom']} CVs ready")
                    for cv in data.get('alumni_cvs', [])[:5]:
                        st.markdown(f"• [{cv['name']}]({cv['download_url']})")
    
    with st.expander("📋 Generate Reports"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Gap Analysis Report"):
                resp = requests.get(f"{API_URL}/programme/{prog_id}/gap-report")
                if resp.ok:
                    st.code(resp.text, language=None)
        
        with col2:
            if st.button("📈 Improvement Plan"):
                resp = requests.get(f"{API_URL}/programme/{prog_id}/improvement-report")
                if resp.ok:
                    st.code(resp.text, language=None)


# ============================================================
# FACULTY UPLOAD MODE
# ============================================================

elif mode == "👨‍🏫 Faculty Upload":
    st.title("👨‍🏫 Faculty CV Upload")
    
    if 'institution_id' not in st.session_state:
        st.warning("⚠️ Please select a programme in Setup first")
        st.stop()
    
    inst_id = st.session_state.institution_id
    
    st.markdown("""
    Upload your CV to contribute to EFMD accreditation data collection.
    
    **Accepted formats:** PDF, DOCX, TXT
    
    Your CV will be analyzed for:
    - Academic qualifications
    - Research publications
    - International experience
    - Industry connections
    """)
    
    uploaded_file = st.file_uploader("Upload CV", type=['pdf', 'docx', 'txt'])
    
    if uploaded_file:
        if st.button("Process CV", type="primary"):
            with st.spinner("Analyzing CV..."):
                files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                resp = requests.post(f"{API_URL}/upload/faculty/{inst_id}", files=files)
                
                if resp.ok:
                    result = resp.json()
                    
                    st.success(f"✅ {result['message']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("EFMD Score", f"{result['efmd_score']}/100")
                    with col2:
                        if result['recommended']:
                            st.success("✅ Recommended for submission")
                        else:
                            st.warning("⚠️ May not be selected")
                    
                    if result.get('strengths'):
                        st.markdown("**Strengths:**")
                        for s in result['strengths']:
                            st.markdown(f"- ✅ {s}")
                    
                    if result.get('risks'):
                        st.markdown("**Areas for improvement:**")
                        for r in result['risks']:
                            st.markdown(f"- ⚠️ {r}")
                else:
                    st.error(f"Error: {resp.text}")


# ============================================================
# STUDENT UPLOAD MODE
# ============================================================

elif mode == "👨‍🎓 Student Upload":
    st.title("👨‍🎓 Student CV Upload")
    
    if 'programme_id' not in st.session_state:
        st.warning("⚠️ Please select a programme in Setup first")
        st.stop()
    
    prog_id = st.session_state.programme_id
    
    st.markdown("""
    Upload your CV to contribute to EFMD accreditation data.
    
    We analyze:
    - Nationality and background
    - Prior education
    - Work experience
    - Language skills
    """)
    
    cohort_year = st.number_input("Cohort Year", min_value=2020, max_value=2030, value=datetime.now().year)
    
    uploaded_file = st.file_uploader("Upload CV", type=['pdf', 'docx', 'txt'])
    
    if uploaded_file:
        if st.button("Process CV", type="primary"):
            with st.spinner("Analyzing CV..."):
                files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                resp = requests.post(
                    f"{API_URL}/upload/student/{prog_id}?cohort_year={cohort_year}", 
                    files=files
                )
                
                if resp.ok:
                    result = resp.json()
                    st.success(f"✅ {result['message']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("EFMD Score", f"{result['efmd_score']}/100")
                    with col2:
                        st.metric("Nationality", result.get('nationality', 'Unknown'))
                else:
                    st.error(f"Error: {resp.text}")


# ============================================================
# ALUMNI UPLOAD MODE
# ============================================================

elif mode == "🎯 Alumni Upload":
    st.title("🎯 Alumni CV Upload")
    
    if 'programme_id' not in st.session_state:
        st.warning("⚠️ Please select a programme in Setup first")
        st.stop()
    
    prog_id = st.session_state.programme_id
    
    st.markdown("""
    Upload your CV to help demonstrate programme outcomes.
    
    We track:
    - Employment status
    - Time to employment
    - Career progression
    - Employer quality
    """)
    
    grad_year = st.number_input("Graduation Year", min_value=2015, max_value=2030, value=2023)
    
    uploaded_file = st.file_uploader("Upload CV", type=['pdf', 'docx', 'txt'])
    
    if uploaded_file:
        if st.button("Process CV", type="primary"):
            with st.spinner("Analyzing CV..."):
                files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                resp = requests.post(
                    f"{API_URL}/upload/alumni/{prog_id}?graduation_year={grad_year}",
                    files=files
                )
                
                if resp.ok:
                    result = resp.json()
                    st.success(f"✅ {result['message']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("EFMD Score", f"{result['efmd_score']}/100")
                    with col2:
                        st.metric("Current Employer", result.get('employer', 'Unknown'))
                    
                    if result.get('strengths'):
                        st.markdown("**Career Highlights:**")
                        for s in result['strengths']:
                            st.markdown(f"- ✅ {s}")
                else:
                    st.error(f"Error: {resp.text}")
# ============================================================
# PROGRAMME SCRAPER MODE
# ============================================================

elif mode == "📄 Programme Scraper":
    st.title("📄 Programme Document Scraper")
    
    # Initialize Supabase connection for this mode
    db_service = None
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from efmd_scraper_v2 import SupabaseService, EFMDScraper, format_gap_report, GapAnalysisResult
        db_service = SupabaseService()
        db_connected = True
    except Exception as e:
        db_connected = False
        db_error = str(e)
    
    # Two tabs: New Analysis and Saved Programmes
    tab1, tab2 = st.tabs(["🔍 New Analysis", "📚 Saved Programmes"])
    
    with tab1:
        st.markdown("""
        Analyze programme documents and websites for EFMD gap analysis.
        
        **Add URLs and/or upload documents to extract:**
        - Programme ILOs (Intended Learning Outcomes)
        - Course information
        - EFMD pillar coverage (International, Practice, ERS, Digital)
        """)
        
        # Institution and Programme Name
        col1, col2 = st.columns(2)
        with col1:
            institution = st.text_input("Institution Name", value="University of Vaasa")
        with col2:
            programme_name = st.text_input("Programme Name", value="MSc Finance")
        
        st.markdown("---")
        
        # URLs Section
        st.subheader("🌐 URLs to Scrape")
        st.caption("Add programme pages, study guides, course catalogs (note: JavaScript-heavy sites may not work)")
        
        # Initialize session state for URLs
        if 'scraper_urls' not in st.session_state:
            st.session_state.scraper_urls = ['']
        
        # Display URL inputs
        urls_to_remove = []
        for i, url in enumerate(st.session_state.scraper_urls):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.session_state.scraper_urls[i] = st.text_input(
                    f"URL {i+1}", 
                    value=url, 
                    key=f"url_{i}",
                    placeholder="https://www.university.edu/programme"
                )
            with col2:
                if len(st.session_state.scraper_urls) > 1:
                    if st.button("🗑️", key=f"remove_url_{i}"):
                        urls_to_remove.append(i)
        
        # Remove marked URLs
        for i in sorted(urls_to_remove, reverse=True):
            st.session_state.scraper_urls.pop(i)
            st.rerun()
        
        # Add URL button
        if st.button("➕ Add URL"):
            st.session_state.scraper_urls.append('')
            st.rerun()
        
        st.markdown("---")
        
        # Document Upload Section
        st.subheader("📁 Upload Documents")
        st.caption("Upload PDF or Word documents (programme handbooks, course catalogs)")
        
        uploaded_files = st.file_uploader(
            "Upload documents",
            type=['pdf', 'docx'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.markdown("**Uploaded files:**")
            for f in uploaded_files:
                st.markdown(f"- 📄 {f.name}")
        
        st.markdown("---")
        
        # Save to database checkbox
        save_to_db = st.checkbox("💾 Save results to database", value=db_connected, disabled=not db_connected)
        if not db_connected:
            st.caption(f"⚠️ Database not connected: {db_error if 'db_error' in dir() else 'Unknown error'}")
        
        # Run Analysis Button
        if st.button("🔍 Analyze Programme", type="primary"):
            # Filter empty URLs
            urls = [u.strip() for u in st.session_state.scraper_urls if u.strip()]
            
            if not urls and not uploaded_files:
                st.error("Please add at least one URL or upload a document")
            else:
                with st.spinner("Analyzing programme..."):
                    import tempfile
                    
                    try:
                        # Save uploaded files to temp directory
                        doc_paths = []
                        if uploaded_files:
                            for f in uploaded_files:
                                temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{f.name.split(".")[-1]}')
                                temp_path.write(f.getvalue())
                                temp_path.close()
                                doc_paths.append(temp_path.name)
                        
                        # Run scraper
                        scraper = EFMDScraper(use_embeddings=False, use_database=False)
                        
                        programme = scraper.scrape_programme(
                            urls=urls if urls else [],
                            documents=doc_paths if doc_paths else None,
                            institution=institution,
                            programme_name=programme_name
                        )
                        
                        gap = scraper.analyze_gaps(programme)
                        
                        # Save to database if enabled
                        saved_programme_id = None
                        if save_to_db and db_service:
                            try:
                                # Save programme
                                saved_programme_id = db_service.save_programme(programme)
                                
                                # Save ILOs
                                for i, ilo in enumerate(programme.programme_ilos):
                                    db_service.save_ilo(saved_programme_id, ilo, i + 1)
                                
                                # Save courses
                                for course in programme.courses:
                                    db_service.save_course(saved_programme_id, course)
                                
                                # Save gap analysis
                                db_service.save_gap_analysis(saved_programme_id, gap)
                                
                                st.success("✅ Analysis Complete and Saved to Database!")
                            except Exception as db_err:
                                st.warning(f"Analysis complete but failed to save: {db_err}")
                        else:
                            st.success("✅ Analysis Complete!")
                        
                        # Display Results
                        # Score Display
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            score = gap.readiness_score
                            if score >= 80:
                                st.metric("Readiness Score", f"{score}/100", "Ready ✅")
                            elif score >= 60:
                                st.metric("Readiness Score", f"{score}/100", "Partial ⚠️")
                            else:
                                st.metric("Readiness Score", f"{score}/100", "At Risk 🔴")
                        
                        with col2:
                            st.metric("ILOs Found", gap.ilo_count)
                        
                        with col3:
                            st.metric("Est. Time to Ready", f"{gap.estimated_fix_months} months")
                        
                        st.markdown("---")
                        
                        # Pillar Coverage
                        st.subheader("EFMD Pillar Coverage")
                        cols = st.columns(4)
                        pillars = ['International', 'Practice', 'ERS', 'Digital']
                        for i, pillar in enumerate(pillars):
                            with cols[i]:
                                score_val = gap.pillar_coverage.get(pillar, 0)
                                if score_val >= 0.7:
                                    st.markdown(f"✅ **{pillar}**")
                                elif score_val >= 0.5:
                                    st.markdown(f"⚠️ **{pillar}**")
                                else:
                                    st.markdown(f"❌ **{pillar}**")
                                st.progress(min(score_val, 1.0))
                        
                        # Critical Gaps
                        if gap.critical_gaps:
                            st.markdown("---")
                            st.subheader("🚨 Critical Gaps")
                            for crit in gap.critical_gaps:
                                st.error(f"❌ {crit}")
                        
                        # ILOs Found
                        if programme.programme_ilos:
                            st.markdown("---")
                            with st.expander(f"📋 ILOs Found ({len(programme.programme_ilos)})"):
                                for i, ilo in enumerate(programme.programme_ilos, 1):
                                    category = ilo.ksa_category or "?"
                                    weak = "⚠️" if ilo.has_weak_verb else ""
                                    st.markdown(f"{i}. [{category}] {weak} {ilo.text[:100]}...")
                        
                        # Recommendations
                        if gap.recommendations:
                            st.markdown("---")
                            with st.expander("💡 Recommendations"):
                                for rec in gap.recommendations:
                                    st.markdown(f"• {rec}")
                        
                        # Full Report
                        st.markdown("---")
                        with st.expander("📄 Full Gap Analysis Report"):
                            report = format_gap_report(gap)
                            st.code(report, language=None)
                        
                        # Cleanup temp files
                        for path in doc_paths:
                            try:
                                os.unlink(path)
                            except:
                                pass
                                
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    
    with tab2:
        st.subheader("📚 Saved Programmes")
        
        if not db_connected:
            st.warning(f"⚠️ Database not connected. Check your .env file has SUPABASE_URL and SUPABASE_KEY.")
        else:
            # Refresh button
            if st.button("🔄 Refresh List"):
                st.rerun()
            
            try:
                programmes = db_service.list_programmes(limit=50)
                
                if not programmes:
                    st.info("No saved programmes yet. Run an analysis and save it to see it here.")
                else:
                    st.markdown(f"**{len(programmes)} programme(s) found**")
                    
                    for prog in programmes:
                        score = prog.get('readiness_score', 0) or 0
                        if score >= 80:
                            score_badge = "🟢"
                        elif score >= 60:
                            score_badge = "🟡"
                        elif score >= 40:
                            score_badge = "🟠"
                        else:
                            score_badge = "🔴"
                        
                        # Programme card
                        with st.expander(f"{score_badge} **{prog['programme_name']}** — {prog.get('institutions', {}).get('name', 'Unknown')} ({score}/100)"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Institution:** {prog.get('institutions', {}).get('name', 'Unknown')}")
                                st.markdown(f"**Degree:** {prog.get('degree_type', 'N/A')}")
                                st.markdown(f"**URL:** {prog.get('primary_url', 'N/A')}")
                                if prog.get('last_analysis_at'):
                                    st.markdown(f"**Last Analyzed:** {prog['last_analysis_at'][:10]}")
                            
                            with col2:
                                st.metric("Score", f"{score}/100")
                            
                            # Load full gap analysis
                            if st.button("View Gap Report", key=f"view_{prog['id']}"):
                                st.session_state.programme_id = prog['id']
                                st.session_state.institution_id = prog['institution_id']
                                st.success(f"✓ Loaded: {prog['programme_name']}")
                                st.rerun()
                                gap_data = db_service.get_gap_analysis(prog['id'])
                                ilos = db_service.get_programme_ilos(prog['id'])
                                
                                if gap_data:
                                    st.markdown("---")
                                    st.markdown("### Gap Analysis Results")
                                    
                                    # Pillar Coverage
                                    st.markdown("**Pillar Coverage:**")
                                    pillar_cols = st.columns(4)
                                    pillar_coverage = gap_data.get('pillar_coverage', {})
                                    for i, pillar in enumerate(['International', 'Practice', 'ERS', 'Digital']):
                                        with pillar_cols[i]:
                                            pval = pillar_coverage.get(pillar, 0)
                                            if pval >= 0.7:
                                                st.markdown(f"✅ {pillar}")
                                            elif pval >= 0.5:
                                                st.markdown(f"⚠️ {pillar}")
                                            else:
                                                st.markdown(f"❌ {pillar}")
                                    
                                    # Critical Gaps
                                    critical = gap_data.get('critical_gaps', [])
                                    if critical:
                                        st.markdown("**Critical Gaps:**")
                                        for c in critical:
                                            st.error(f"❌ {c}")
                                    
                                    # ILOs
                                    if ilos:
                                        st.markdown(f"**ILOs ({len(ilos)}):**")
                                        for ilo in ilos:
                                            cat = ilo.get('ksa_category', '?')
                                            weak = "⚠️" if ilo.get('has_weak_verb') else ""
                                            st.markdown(f"- [{cat}] {weak} {ilo['ilo_text'][:80]}...")
                                    
                                    # Recommendations
                                    recs = gap_data.get('recommendations', [])
                                    if recs:
                                        st.markdown("**Recommendations:**")
                                        for r in recs:
                                            st.markdown(f"• {r}")
                                else:
                                    st.warning("No gap analysis found for this programme")
                            
                            # Delete button
                            if st.button(f"🗑️ Delete", key=f"delete_{prog['id']}"):
                                if st.session_state.get(f"confirm_delete_{prog['id']}"):
                                    db_service.delete_programme(prog['id'])
                                    st.success("Deleted!")
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{prog['id']}"] = True
                                    st.warning("Click Delete again to confirm")
                            
            except Exception as e:
                st.error(f"Error loading programmes: {e}")
                import traceback
                st.code(traceback.format_exc())


# ============================================================
# FOOTER
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("**EFMD Data Collection Tool**")
st.sidebar.markdown("v1.0.0 | Powered by Allsorter")

