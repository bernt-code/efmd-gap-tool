#!/usr/bin/env python3
"""
EFMD CV datapoints collection Portal
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
from bulk_upload import render_bulk_upload

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

if "mode" not in st.session_state:
    st.session_state.mode = "📊 Dashboard"

mode = st.sidebar.radio(
    "Select Mode",
    ["📊 Dashboard", "📄 Program data", "👨‍🏫 Faculty CV upload", "👨‍🎓 Students CV upload", "🎯 Alumni CV upload", "⚙️ Setup"],
    key="mode"
)
st.sidebar.markdown("---")
st.sidebar.markdown("**Collection Links**")
st.sidebar.markdown("Share these with your stakeholders:")

# Get active programme from session
if 'programme_id' in st.session_state and st.session_state.programme_id:
    prog_id = st.session_state.get("programme_id")

    if not prog_id:
        st.info("No programme selected. Please create or select a programme first.")
        st.stop()

    inst_id = st.session_state.get('institution_id', '')
    
    st.sidebar.code(f"Faculty:\n/faculty/{inst_id[:8]}...")
    st.sidebar.code(f"Students:\n/student/{prog_id[:8]}...")
    st.sidebar.code(f"Alumni:\n/alumni/{prog_id[:8]}...")


# ============================================================
# SETUP MODE
# ============================================================

if mode == "⚙️ Setup":
    st.title("⚙️ Setup Institution & Programme")
    st.session_state.show_baseroom = st.checkbox("Show Base Room Preparation (post-OX feature)", value=False)
    
    tab2, tab1 = st.tabs(["Select Existing", "Create New"])
    
    with tab1:
        st.subheader("Create Institution")
        
        col1, col2 = st.columns(2)
        with col1:
            inst_name = st.text_input("Institution Name", placeholder="University of Vaasa")
            inst_country = st.text_input("Country", placeholder="Finland")
        with col2:
            inst_city = st.text_input("City", placeholder="Vaasa")
            inst_website = st.text_input("Website", placeholder="https://www.uwasa.fi/en")
        
        if st.button("Create Institution", type="primary"):
            if not inst_name:
                st.error("Institution name is required")
            else:
                resp = requests.post(f"{API_URL}/institutions", json={
                    'name': inst_name,
                    'country': inst_country,
                    'city': inst_city,
                    'website': inst_website
                })
                if resp.ok:
                    data = resp.json()
                    st.success(f"✅ Institution created: {inst_name}")
                    st.session_state.institution_id = data['institution']['id']
                    st.session_state.institution_name = inst_name
                    
                    # Auto-crawl if website provided
                    if inst_website:
                        with st.spinner(f"🔍 Analyzing {inst_website}... (this takes 1-2 minutes)"):
                            crawl_resp = requests.post(f"{API_URL}/institution/{data['institution']['id']}/crawl?max_pages=75")
                            if crawl_resp.ok:
                                crawl_data = crawl_resp.json()
                                st.success(f"✅ Website analyzed! Readiness score: {crawl_data.get('readiness_score', 'N/A')}%")
                            else:
                                st.warning("Website analysis failed, but institution was created.")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.text}")
        
        st.markdown("---")
        st.subheader("Create Programme")
        st.info("👉 Create programmes in the **Programme Data** section after selecting an institution.")
    
    with tab2:
        st.subheader("Select Existing Institution & Programme")
        
        # Fetch institutions from API
        try:
            inst_resp = requests.get(f"{API_URL}/institutions")
            if inst_resp.ok:
                institutions = inst_resp.json().get('institutions', [])
                # Filter out empty institutions
                institutions = [i for i in institutions if i.get('name')]
            else:
                institutions = []
        except:
            institutions = []
        
        if not institutions:
            st.info("No institutions found. Create one first using the 'Create New' tab.")
        else:
            # Institution dropdown
            inst_options = {f"{i['name']} ({i.get('city', 'N/A')}, {i.get('country', 'N/A')})": i for i in institutions}
            selected_inst = st.selectbox("Select Institution", list(inst_options.keys()))
            
            if selected_inst:
                institution = inst_options[selected_inst]
                st.session_state.institution_id = institution['id']
                st.session_state.institution_name = institution['name']
                
                # ========== INSTITUTION SETTINGS ==========
                st.markdown("---")
                
                # Show website and crawl option
                website = institution.get('website', '')
                if website:
                    col_web1, col_web2 = st.columns([3, 1])
                    with col_web1:
                        st.text_input("Website", value=website, disabled=True, key="inst_website_display")
                    with col_web2:
                        if st.button("🔄 Crawl Website"):
                            with st.spinner(f"Analyzing {website}..."):
                                crawl_resp = requests.post(f"{API_URL}/institution/{institution['id']}/crawl?max_pages=75")
                                if crawl_resp.ok:
                                    st.success("✅ Website analyzed!")
                                    st.rerun()
                                else:
                                    st.error("Analysis failed")
                
               # ========== INSTITUTION DOCUMENT UPLOADS ==========
                st.markdown("---")
                st.subheader("📄 Institution Documents (Optional)")
                st.caption("Upload any documents with institutional data - annual reports, fact sheets, strategic plans, etc.")
                
                uploaded_docs = st.file_uploader(
                    "Drop files here",
                    type=['pdf', 'docx'],
                    accept_multiple_files=True,
                    key="inst_docs_upload"
                )
                
                if uploaded_docs:
                    if st.button(f"📤 Upload {len(uploaded_docs)} document(s)", type="secondary"):
                        success_count = 0
                        for doc in uploaded_docs:
                            files = {'file': (doc.name, doc.getvalue())}
                            resp = requests.post(
                                f"{API_URL}/institution/{institution['id']}/document",
                                files=files
                            )
                            if resp.ok:
                                success_count += 1
                        if success_count == len(uploaded_docs):
                            st.success(f"✅ Uploaded {success_count} document(s)!")
                        else:
                            st.warning(f"Uploaded {success_count}/{len(uploaded_docs)} documents")
                
                # ========== PROGRAMME SELECTION ==========
                st.markdown("---")
                st.subheader("🎓 Select Programme")
                
                # Fetch programmes for this institution
                try:
                    prog_resp = requests.get(f"{API_URL}/programmes", params={"institution_id": institution['id']})
                    if prog_resp.ok:
                        programmes = prog_resp.json().get('programmes', [])
                    else:
                        programmes = []
                except:
                    programmes = []
                
                if not programmes:
                    st.info("No programmes found for this institution. Create one in **Programme Data**.")
                else:
                    prog_options = {p['programme_name']: p for p in programmes}
                    selected_prog = st.selectbox("Select Programme", list(prog_options.keys()))
                    
                    if st.button("✅ Use This Programme", type="primary"):
                        prog = prog_options[selected_prog]
                        st.session_state.programme_id = prog['id']
                        st.session_state.programme_name = prog['programme_name']
                        st.success(f"Selected: {prog['programme_name']} at {institution['name']}")
                        st.rerun()          

# ============================================================
# DASHBOARD MODE
# ============================================================
elif mode == "📊 Dashboard":
    st.title("📊 EFMD Accreditation Dashboard")
    
    if 'programme_id' not in st.session_state:
        st.warning("⚠️ Please select a programme in Setup first")
        st.stop()
    
    import streamlit.components.v1 as components
    import os
    
    # Load HTML dashboard
    html_path = os.path.join(os.path.dirname(__file__), "static", "dashboard2.html")
    with open(html_path, "r") as f:
        dashboard_html = f.read()
    
    components.html(dashboard_html, height=3000, scrolling=True)
# ============================================================
# FACULTY UPLOAD MODE
# ============================================================

elif mode == "👨‍🏫 Faculty CV upload":
    st.title("👨‍🏫 Faculty CV Upload")
    
    if 'institution_id' not in st.session_state:
        st.warning("⚠️ Please select an institution in Setup first")
        st.stop()
    
    inst_id = st.session_state.institution_id
    
    # Tabs for bulk vs single upload
    tab_bulk, tab_single = st.tabs(["📁 Bulk Upload (25+ files)", "📄 Single Upload"])
    
    # BULK UPLOAD TAB
    with tab_bulk:
        render_bulk_upload(
            upload_type="faculty",
            entity_id=inst_id,
            api_url=API_URL
        )
    
    # SINGLE UPLOAD TAB (existing functionality)
    with tab_single:
        st.markdown("""
        Upload your CV to contribute to EFMD accreditation data collection.
        
        **Accepted formats:** PDF, DOCX, TXT
        
        Your CV will be analyzed for:
        - Academic qualifications
        - Research publications
        - International experience
        - Industry connections
        """)
        
        uploaded_file = st.file_uploader("Upload CV", type=['pdf', 'docx', 'txt'], key="faculty_single")
        
        if uploaded_file:
            if st.button("Process CV", type="primary", key="faculty_process"):
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

elif mode == "👨‍🎓 Students CV upload":
    st.title("👨‍🎓 Student CV Upload")
    
    if 'programme_id' not in st.session_state:
        st.warning("⚠️ Please select a programme in Setup first")
        st.stop()
    
    prog_id = st.session_state.get("programme_id")

    if not prog_id:
        st.info("No programme selected. Please create or select a programme first.")
        st.stop()

    
    # Tabs for bulk vs single upload
    tab_bulk, tab_single = st.tabs(["📁 Bulk Upload (25+ files)", "📄 Single Upload"])
    
    # BULK UPLOAD TAB
    with tab_bulk:
        render_bulk_upload(
            upload_type="student",
            entity_id=prog_id,
            api_url=API_URL
        )
    
    # SINGLE UPLOAD TAB
    with tab_single:
        st.markdown("""
        Upload your CV to contribute to EFMD accreditation data.
        
        We analyze:
        - Nationality and background
        - Prior education
        - Work experience
        - Language skills
        """)
        
        cohort_year = st.number_input("Cohort Year", min_value=2020, max_value=2030, value=datetime.now().year, key="student_cohort")
        
        uploaded_file = st.file_uploader("Upload CV", type=['pdf', 'docx', 'txt'], key="student_single")
        
        if uploaded_file:
            if st.button("Process CV", type="primary", key="student_process"):
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

elif mode == "🎯 Alumni CV upload":
    st.title("🎯 Alumni CV Upload")
    
    if 'programme_id' not in st.session_state:
        st.warning("⚠️ Please select a programme in Setup first")
        st.stop()
    
    prog_id = st.session_state.get("programme_id")

    if not prog_id:
        st.info("No programme selected. Please create or select a programme first.")
        st.stop()

    
    # Tabs for bulk vs single upload
    tab_bulk, tab_single = st.tabs(["📁 Bulk Upload (25+ files)", "📄 Single Upload"])
    
    # BULK UPLOAD TAB
    with tab_bulk:
        st.markdown("---")
        default_grad_year = st.number_input(
            "Default Graduation Year (applies to all files in batch)", 
            min_value=2015, 
            max_value=2030, 
            value=2023,
            key="alumni_bulk_grad_year",
            help="All CVs in this batch will be tagged with this graduation year. For mixed years, use single upload."
        )
        st.info(f"📅 All CVs will be tagged with graduation year: **{default_grad_year}**")
        
        render_bulk_upload(
            upload_type="alumni",
            entity_id=prog_id,
            api_url=API_URL,
            graduation_year=default_grad_year
        )
    
    # SINGLE UPLOAD TAB
    with tab_single:
        st.markdown("""
        Upload your CV to help demonstrate programme outcomes.
        
        We analyze:
        - Time to employment after graduation
        - Employer quality (MBB, Big 4, Fortune 500, etc.)
        - Career progression
        - Salary indicators
        """)
        
        graduation_year = st.number_input("Graduation Year", min_value=2015, max_value=2030, value=2023, key="alumni_single_grad")
        
        uploaded_file = st.file_uploader("Upload CV", type=['pdf', 'docx', 'txt'], key="alumni_single")
        
        if uploaded_file:
            if st.button("Process CV", type="primary", key="alumni_process"):
                with st.spinner("Analyzing CV..."):
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                    resp = requests.post(
                        f"{API_URL}/upload/alumni/{prog_id}?graduation_year={graduation_year}",
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

# ============================================================
# PROGRAMME DATA MODE
# ============================================================

elif mode == "📄 Program data":
    st.title("📄 Programme Data")
    
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
        Collect programme data for accreditation gap analysis.
        
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
        st.subheader("🌐 Programme URLs")
        st.caption("Add links to programme pages, course catalogs, study guides")
        
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
        uploaded_files = st.file_uploader("Choose files", type=["pdf", "docx"], accept_multiple_files=True)
        
        # Text paste option
        st.markdown("**Or paste text directly:**")
        pasted_text = st.text_area("Paste programme text here", height=150, placeholder="Copy and paste ILOs, course descriptions, or programme information from the school website...", key="pasted_text_area")
        if st.button("💾 Save text"):
            st.session_state.saved_pasted_text = pasted_text
            st.success("Text saved!")
        if pasted_text:
            st.caption(f"✓ {len(pasted_text)} characters ready for analysis")
        
        # Run Analysis Button
        if st.button("🔍 Analyze Programme", type="primary"):
            # Filter empty URLs
            urls = [u.strip() for u in st.session_state.scraper_urls if u.strip()]
            
            if not urls and not uploaded_files and not pasted_text:
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
                        
                        # Save pasted text to temp file
                        if pasted_text:
                            temp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w")
                            temp_txt.write(pasted_text)
                            temp_txt.close()
                            doc_paths.append(temp_txt.name)
                        
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

