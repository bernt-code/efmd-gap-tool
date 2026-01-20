"""
Bulk CV Upload Component for EFMD Gap Tool

Features:
- Drag & drop multiple PDF/DOCX files
- Progress bar during processing
- Success/failure summary
- Duplicate detection with skip/overwrite options
"""

import streamlit as st
import requests
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass
import time


@dataclass
class UploadResult:
    """Result of processing a single CV file."""
    filename: str
    success: bool
    message: str
    efmd_score: Optional[int] = None
    is_duplicate: bool = False
    duplicate_action: Optional[str] = None


def get_file_hash(file_content: bytes) -> str:
    """Generate MD5 hash of file content for duplicate detection."""
    return hashlib.md5(file_content).hexdigest()


def check_duplicate(
    api_url: str,
    upload_type: str,
    entity_id: str,
    file_hash: str,
    filename: str
) -> tuple:
    """Check if a CV with this hash already exists."""
    try:
        resp = requests.get(
            f"{api_url}/check-duplicate/{upload_type}/{entity_id}",
            params={"file_hash": file_hash, "filename": filename}
        )
        if resp.ok:
            data = resp.json()
            return data.get('is_duplicate', False), data.get('existing_id')
    except Exception:
        pass
    return False, None


def process_single_cv(
    api_url: str,
    upload_type: str,
    entity_id: str,
    file,
    duplicate_action: str = "skip",
    graduation_year: Optional[int] = None
) -> UploadResult:
    """Process a single CV file."""
    try:
        file_content = file.getvalue()
        file_hash = get_file_hash(file_content)
        
        # Check for duplicates
        is_duplicate, existing_id = check_duplicate(
            api_url, upload_type, entity_id, file_hash, file.name
        )
        
        if is_duplicate and duplicate_action == "skip":
            return UploadResult(
                filename=file.name,
                success=True,
                message="Duplicate - skipped",
                is_duplicate=True,
                duplicate_action="skipped"
            )
        
        # Build the API endpoint
        endpoint = f"{api_url}/upload/{upload_type}/{entity_id}"
        
        # Add query parameters
        params = {}
        if upload_type == "alumni" and graduation_year:
            params["graduation_year"] = graduation_year
        if is_duplicate and duplicate_action == "overwrite":
            params["overwrite"] = "true"
            params["existing_id"] = existing_id
        
        # Make the upload request
        files = {'file': (file.name, file_content)}
        resp = requests.post(endpoint, files=files, params=params)
        
        if resp.ok:
            result = resp.json()
            return UploadResult(
                filename=file.name,
                success=True,
                message=result.get('message', 'Uploaded successfully'),
                efmd_score=result.get('efmd_score'),
                is_duplicate=is_duplicate,
                duplicate_action="overwritten" if is_duplicate else None
            )
        else:
            return UploadResult(
                filename=file.name,
                success=False,
                message=f"Error: {resp.text[:100]}"
            )
            
    except Exception as e:
        return UploadResult(
            filename=file.name,
            success=False,
            message=f"Error: {str(e)[:100]}"
        )


def render_upload_summary(results: List[UploadResult]):
    """Render a summary of all upload results."""
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    skipped = [r for r in results if r.duplicate_action == "skipped"]
    overwritten = [r for r in results if r.duplicate_action == "overwritten"]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Successful", len(successful))
    with col2:
        st.metric("❌ Failed", len(failed))
    with col3:
        st.metric("⏭️ Skipped", len(skipped))
    with col4:
        st.metric("🔄 Overwritten", len(overwritten))
    
    # Detailed results
    if successful:
        with st.expander(f"✅ Successfully Processed ({len(successful)})", expanded=False):
            for r in successful:
                score_str = f" — Score: {r.efmd_score}/100" if r.efmd_score else ""
                dup_str = f" ({r.duplicate_action})" if r.duplicate_action else ""
                st.markdown(f"- **{r.filename}**{score_str}{dup_str}")
    
    if failed:
        with st.expander(f"❌ Failed ({len(failed)})", expanded=True):
            for r in failed:
                st.error(f"**{r.filename}**: {r.message}")


def render_bulk_upload(
    upload_type: str,
    entity_id: str,
    api_url: str,
    graduation_year: Optional[int] = None
):
    """
    Render the bulk upload interface.
    
    Args:
        upload_type: 'faculty', 'student', or 'alumni'
        entity_id: institution_id (for faculty) or programme_id (for student/alumni)
        api_url: Base API URL
        graduation_year: Required for alumni uploads
    """
    
    # Type-specific configuration
    type_config = {
        "faculty": {
            "title": "Faculty CVs",
            "icon": "👨‍🏫",
            "target": 25,
            "description": "Upload faculty CVs. We analyze: academic qualifications, research output, international experience, and industry connections."
        },
        "student": {
            "title": "Student CVs",
            "icon": "👨‍🎓",
            "target": 25,
            "description": "Upload current student CVs. We analyze: diversity, prior education quality, and work experience."
        },
        "alumni": {
            "title": "Alumni CVs",
            "icon": "🎯",
            "target": 25,
            "description": "Upload alumni CVs. We analyze: employment speed, employer quality, career progression, and salary indicators."
        }
    }
    
    config = type_config.get(upload_type, type_config["faculty"])
    
    st.markdown(f"""
    {config['description']}
    
    **Target:** {config['target']} CVs for EFMD submission
    """)
    
    # Initialize session state for this upload type
    state_key = f"bulk_upload_{upload_type}_results"
    if state_key not in st.session_state:
        st.session_state[state_key] = []
    
    # Duplicate handling option
    st.markdown("---")
    duplicate_action = st.radio(
        "If duplicate files are detected:",
        ["Skip duplicates", "Overwrite duplicates"],
        key=f"duplicate_action_{upload_type}",
        horizontal=True,
        help="Duplicates are detected by file content, not filename"
    )
    duplicate_action_value = "skip" if "Skip" in duplicate_action else "overwrite"
    
    # File uploader - accepts multiple files
    uploaded_files = st.file_uploader(
        "📁 Drag & drop CV files here (PDF or DOCX)",
        type=['pdf', 'docx'],
        accept_multiple_files=True,
        key=f"bulk_uploader_{upload_type}",
        help="You can select multiple files at once, or drag and drop a batch"
    )
    
    # Show file count and total size
    if uploaded_files:
        total_size = sum(f.size for f in uploaded_files)
        size_mb = total_size / (1024 * 1024)
        
        st.info(f"📊 **{len(uploaded_files)} files selected** ({size_mb:.1f} MB total)")
        
        # File list preview
        with st.expander("Preview selected files", expanded=False):
            for i, f in enumerate(uploaded_files, 1):
                file_size_kb = f.size / 1024
                st.markdown(f"{i}. {f.name} ({file_size_kb:.1f} KB)")
    
    # Process button
    col1, col2 = st.columns([1, 3])
    with col1:
        process_button = st.button(
            "🚀 Process All CVs",
            type="primary",
            disabled=not uploaded_files,
            key=f"process_bulk_{upload_type}"
        )
    
    # Processing logic
    if process_button and uploaded_files:
        results = []
        
        # Progress container
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### Processing...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            current_file_display = st.empty()
        
        total_files = len(uploaded_files)
        
        for i, file in enumerate(uploaded_files):
            # Update progress
            progress = (i + 1) / total_files
            progress_bar.progress(progress)
            status_text.markdown(f"**Processing {i + 1} of {total_files}** ({int(progress * 100)}%)")
            current_file_display.markdown(f"📄 Current: `{file.name}`")
            
            # Process the file
            result = process_single_cv(
                api_url=api_url,
                upload_type=upload_type,
                entity_id=entity_id,
                file=file,
                duplicate_action=duplicate_action_value,
                graduation_year=graduation_year
            )
            results.append(result)
            
            # Small delay to prevent overwhelming the API
            time.sleep(0.1)
        
        # Clear progress indicators
        progress_bar.progress(1.0)
        status_text.markdown("**✅ Complete!**")
        current_file_display.empty()
        
        # Store results in session state
        st.session_state[state_key] = results
        
        # Force rerun to show results
        st.rerun()
    
    # Display results from session state
    if st.session_state[state_key]:
        st.markdown("---")
        st.markdown("### 📊 Upload Results")
        render_upload_summary(st.session_state[state_key])
        
        # Clear results button
        if st.button("🗑️ Clear Results", key=f"clear_results_{upload_type}"):
            st.session_state[state_key] = []
            st.rerun()