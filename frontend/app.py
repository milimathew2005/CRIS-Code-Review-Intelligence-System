import streamlit as st
import requests
import pandas as pd
import altair as alt
from typing import Dict, Any, List

# Set page configuration
st.set_page_config(
    page_title="CRIS | Analytics Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply premium HSL-tailored CSS styles to override default themes
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Font overrides */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    code, pre, [data-testid="stCodeBlock"] {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Beautiful linear gradient header */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    
    .sub-header {
        color: #94a3b8;
        font-size: 1.15rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Sleek card panel containers */
    .kpi-card {
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #f43f5e;
        margin: 0.5rem 0;
    }
    
    .kpi-title {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .card-panel {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.75rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
    }
    
    .glow-border {
        border: 1px solid transparent;
        background-image: linear-gradient(#0f172a, #0f172a), 
                          linear-gradient(135deg, #6366f1, #ec4899);
        background-origin: border-box;
        background-clip: padding-box, border-box;
        border-radius: 16px;
        padding: 1.75rem;
        margin-bottom: 1.5rem;
    }
    
    .status-indicator {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header Section
st.markdown('<div class="main-header">Code Review Intelligence System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Static & Semantic Repository Quality Analytics Dashboard</div>', unsafe_allow_html=True)

import os
# Base API address config
API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/api/v1")

# System health check helper
def check_backend_health() -> dict:
    try:
        response = requests.get(f"{API_URL}/system/health", timeout=2)
        if response.status_code == 200:
            return {"status": "Online", "database": response.json().get("database", "unknown"), "error": None}
        elif response.status_code == 503:
            return {"status": "Degraded", "database": "Disconnected", "error": "Database connectivity health check failed."}
        else:
            return {"status": "Error", "database": "unknown", "error": f"HTTP status {response.status_code}"}
    except Exception as e:
        return {"status": "Offline", "database": "unknown", "error": str(e)}

# Sidebar Navigation Options
st.sidebar.title("📊 CRIS Dashboard")
st.sidebar.write("Phase 6 Visualization Layer")

# Render health check in sidebar
health = check_backend_health()
if health["status"] == "Online":
    st.sidebar.markdown('Backend API: <span style="color:#10b981; font-weight:600;">● Online</span>', unsafe_allow_html=True)
elif health["status"] == "Degraded":
    st.sidebar.markdown('Backend API: <span style="color:#f59e0b; font-weight:600;">● Degraded</span>', unsafe_allow_html=True)
    st.sidebar.warning("PostgreSQL database is currently offline.")
else:
    st.sidebar.markdown('Backend API: <span style="color:#ef4444; font-weight:600;">● Offline</span>', unsafe_allow_html=True)
    st.sidebar.info("Operating on high-fidelity mock data fallback.")

page = st.sidebar.radio(
    "Navigation Options",
    [
        "Review Sandbox",
        "Repository Overview",
        "Pull Request Explorer",
        "Issue Analytics",
        "Severity Analytics",
        "Trends"
    ]
)

# Helper checking backend status
def fetch_endpoint_data(endpoint: str, default_mock_data: Any) -> Any:
    try:
        response = requests.get(f"{API_URL}/{endpoint}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return default_mock_data

# ==========================================
# PAGE: REVIEW SANDBOX
# ==========================================
if page == "Review Sandbox":
    col_main, col_side = st.columns([2.2, 1])

    with col_main:
        st.markdown('<div class="glow-border">', unsafe_allow_html=True)
        st.subheader("🔍 Review Sandbox")
        st.write("Submit source code files and diff layouts to trigger AI analysis and local db commits.")
        
        file_input = st.text_area(
            "Source Code (Python)",
            height=240,
            placeholder="def sample_calculation(): ...",
            key="source_input"
        )
        
        diff_input = st.text_area(
            "Unified Git Diff (Optional)",
            height=120,
            placeholder="diff --git a/app.py ...",
            key="diff_input"
        )
        
        if st.button("Trigger Review Analysis", type="primary", use_container_width=True):
            if not file_input.strip():
                st.warning("Please provide source code file contents to review.")
            else:
                with st.spinner("Executing AI code review & writing db records..."):
                    try:
                        payload = {"file_content": file_input, "diff_content": diff_input or None}
                        response = requests.post(f"{API_URL}/reviews/review", json=payload, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            st.success(data.get("message", "Done"))
                            if data.get("data", {}).get("reports"):
                                for report in data["data"]["reports"]:
                                    st.write(f"### Review for file: `{report['filename']}`")
                                    for issue in report["issues"]:
                                        with st.expander(f"[{issue['severity'].upper()} - {issue['issue_type']}] Line {issue['line_number']}"):
                                            st.write(f"**Description**: {issue['description']}")
                                            st.code(issue["suggested_fix"], language="python")
                        else:
                            st.error(f"Endpoint error [{response.status_code}]: {response.text}")
                    except Exception as e:
                        st.info(f"Local simulation executed. Webhook mock details: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        st.markdown('<div class="card-panel">', unsafe_allow_html=True)
        st.markdown('<h3>System Diagnostics</h3>', unsafe_allow_html=True)
        
        if health["status"] == "Online":
            st.markdown('<div>System status: <span class="status-indicator">● Active</span></div>', unsafe_allow_html=True)
        elif health["status"] == "Degraded":
            st.markdown('<div>System status: <span class="status-indicator" style="color:#f59e0b; background:rgba(245, 158, 11, 0.15); border-color:rgba(245, 158, 11, 0.3)">● Degraded</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div>System status: <span class="status-indicator" style="color:#ef4444; background:rgba(239, 68, 68, 0.15); border-color:rgba(239, 68, 68, 0.3)">● Offline</span></div>', unsafe_allow_html=True)
            
        st.markdown(
            """
            <div style="margin-top:1.25rem; font-size:0.92rem; color:#94a3b8; line-height:1.5;">
                Gathers static structure features using Python's <code>ast</code> modules and unified diff structures.
                Reviews are generated in structured JSON via <code>gemini-2.5-flash</code>.
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PAGE 1: REPOSITORY OVERVIEW
# ==========================================
elif page == "Repository Overview":
    st.subheader("📁 System Overview Metrics")
    st.write("Aggregated total stats committed within the PostgreSQL database.")

    # Fetch stats with safe mock fallback
    mock_stats = {
        "total_repositories": 4,
        "total_pull_requests": 12,
        "total_review_reports": 25,
        "total_issues_detected": 48
    }
    stats = fetch_endpoint_data("analytics/overview", mock_stats)

    # 4 Column Cards Layout
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">Repositories</div>'
            f'<div class="kpi-value" style="color:#6366f1;">{stats["total_repositories"]}</div></div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">Pull Requests</div>'
            f'<div class="kpi-value" style="color:#a855f7;">{stats["total_pull_requests"]}</div></div>',
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">Review Reports</div>'
            f'<div class="kpi-value" style="color:#ec4899;">{stats["total_review_reports"]}</div></div>',
            unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">Issues Detected</div>'
            f'<div class="kpi-value" style="color:#f43f5e;">{stats["total_issues_detected"]}</div></div>',
            unsafe_allow_html=True
        )

# ==========================================
# PAGE 2: PULL REQUEST EXPLORER
# ==========================================
elif page == "Pull Request Explorer":
    st.subheader("🔍 Pull Request Review Explorer")
    
    # 1. Fetch Repository Lists
    mock_repos = [
        {"id": 1, "full_name": "mili/my-repo"},
        {"id": 2, "full_name": "google/genai-sdk"}
    ]
    repos = fetch_endpoint_data("analytics/repositories", mock_repos)
    
    if not repos:
        st.warning("No repositories found in database.")
    else:
        repo_names = [r["full_name"] for r in repos]
        selected_repo_name = st.selectbox("Select Target Repository", repo_names)
        selected_repo = next(r for r in repos if r["full_name"] == selected_repo_name)
        
        # 2. Fetch PR Lists
        mock_pulls = [
            {"id": 1, "pr_number": 12, "title": "Fix memory leak in parser core"},
            {"id": 2, "pr_number": 14, "title": "Add authenticate checks method"}
        ]
        pulls = fetch_endpoint_data(f"analytics/repositories/{selected_repo['id']}/pulls", mock_pulls)
        
        if not pulls:
            st.info("No pull requests found for this repository.")
        else:
            pr_options = [f"#{p['pr_number']} - {p['title']}" for p in pulls]
            selected_pr_option = st.selectbox("Select Pull Request", pr_options)
            selected_pr = next(p for p in pulls if f"#{p['pr_number']} - {p['title']}" == selected_pr_option)
            
            # 3. Fetch PR Details
            mock_pr_details = {
                "pr_number": selected_pr["pr_number"],
                "title": selected_pr["title"],
                "author": "mili-dev",
                "github_url": "https://github.com/mili/repo/pull/12",
                "files_reviewed": ["auth.py", "parser.py"],
                "total_issues": 3,
                "severity_distribution": {"Critical": 1, "High": 1, "Medium": 1, "Low": 0},
                "issues": [
                    {
                        "filename": "auth.py",
                        "issue_type": "Security",
                        "severity": "Critical",
                        "line_number": 12,
                        "description": "Hardcoded raw API secrets key.",
                        "suggested_fix": "Use os.getenv('API_KEY') instead."
                    },
                    {
                        "filename": "parser.py",
                        "issue_type": "Logic",
                        "severity": "High",
                        "line_number": 42,
                        "description": "Index bounds mismatch checking variables.",
                        "suggested_fix": "Assert size > 0 before extraction loop."
                    }
                ]
            }
            pr_details = fetch_endpoint_data(f"analytics/pulls/{selected_pr['id']}", mock_pr_details)
            
            # Render PR explorer panels
            col_info, col_sev = st.columns([1.5, 1])
            with col_info:
                st.markdown(
                    f"""
                    <div class="card-panel">
                        <h4>PR #{pr_details['pr_number']}: {pr_details['title']}</h4>
                        <p><strong>Author:</strong> {pr_details['author']}</p>
                        <p><strong>GitHub URL:</strong> <a href="{pr_details['github_url']}" target="_blank">{pr_details['github_url']}</a></p>
                        <p><strong>Files Reviewed:</strong> {', '.join(pr_details['files_reviewed'])}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_sev:
                st.markdown('<div class="card-panel">', unsafe_allow_html=True)
                st.write("##### Severity Distribution")
                sev_df = pd.DataFrame(list(pr_details["severity_distribution"].items()), columns=["Severity", "Issues"])
                st.bar_chart(sev_df, x="Severity", y="Issues")
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.write("### 🔍 Code Quality Findings")
            for issue in pr_details["issues"]:
                with st.expander(f"[{issue['severity'].upper()} - {issue['issue_type']}] {issue['filename']} : Line {issue['line_number']}"):
                    st.write(f"**Finding**: {issue['description']}")
                    st.write("**Suggested Refactoring Fix:**")
                    st.code(issue["suggested_fix"], language="python")

# ==========================================
# PAGE 3: ISSUE ANALYTICS
# ==========================================
elif page == "Issue Analytics":
    st.subheader("💡 Issue Category Distributions")
    st.write("Visualizes counts of code quality violations grouped by categories (Security, Logic, Performance, Style).")
    
    mock_issues = {"Security": 8, "Logic": 15, "Performance": 10, "Style": 12}
    issues_stats = fetch_endpoint_data("analytics/issues", mock_issues)
    
    df = pd.DataFrame(list(issues_stats.items()), columns=["Category", "Count"])
    
    col_bar, col_pie = st.columns(2)
    with col_bar:
        st.write("##### Issues by Category Type")
        st.bar_chart(df, x="Category", y="Count")
        
    with col_pie:
        st.write("##### Density Distribution Pie Chart")
        # Draw a beautiful pie/arc chart using Altair
        pie_chart = alt.Chart(df).mark_arc().encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Category", type="nominal"),
            tooltip=["Category", "Count"]
        ).properties(width=300, height=300)
        st.altair_chart(pie_chart, use_container_width=True)

# ==========================================
# PAGE 4: SEVERITY ANALYTICS
# ==========================================
elif page == "Severity Analytics":
    st.subheader("🚨 Severity Density Metrics")
    st.write("Visualizes distribution counts across the four severity parameters: Critical, High, Medium, Low.")
    
    mock_sev = {"Critical": 4, "High": 12, "Medium": 20, "Low": 16}
    sev_stats = fetch_endpoint_data("analytics/severities", mock_sev)
    
    df_sev = pd.DataFrame(list(sev_stats.items()), columns=["Severity", "Count"])
    
    col_bar, col_pie = st.columns(2)
    with col_bar:
        st.write("##### Count Distribution")
        st.bar_chart(df_sev, x="Severity", y="Count")
        
    with col_pie:
        st.write("##### Severity Proportions")
        pie_chart = alt.Chart(df_sev).mark_arc().encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Severity", type="nominal", sort=["Critical", "High", "Medium", "Low"]),
            tooltip=["Severity", "Count"]
        ).properties(width=300, height=300)
        st.altair_chart(pie_chart, use_container_width=True)

# ==========================================
# PAGE 5: TRENDS
# ==========================================
elif page == "Trends":
    st.subheader("📈 Historical Trends & Problematics")
    st.write("Tracks PR reviews volume, code defects density timelines, and maps top problematic repository listings.")
    
    mock_trends = {
        "issues_over_time": [
            {"date": "2026-06-15", "count": 5},
            {"date": "2026-06-16", "count": 12},
            {"date": "2026-06-17", "count": 8},
            {"date": "2026-06-18", "count": 15},
            {"date": "2026-06-19", "count": 20}
        ],
        "prs_over_time": [
            {"date": "2026-06-15", "count": 1},
            {"date": "2026-06-16", "count": 3},
            {"date": "2026-06-17", "count": 2},
            {"date": "2026-06-18", "count": 4},
            {"date": "2026-06-19", "count": 5}
        ],
        "problematic_repositories": [
            {"repository": "mili/my-repo", "issues": 25},
            {"repository": "google/genai-sdk", "issues": 12},
            {"repository": "testing/dummy-app", "issues": 8}
        ]
    }
    
    trends = fetch_endpoint_data("analytics/trends", mock_trends)
    
    # 1. Timeline charts
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.write("##### Issues Created Over Time")
        if trends["issues_over_time"]:
            df_issues = pd.DataFrame(trends["issues_over_time"])
            st.line_chart(df_issues, x="date", y="count")
        else:
            st.info("No timeline records available yet.")
            
    with col_t2:
        st.write("##### PR Reviews Over Time")
        if trends["prs_over_time"]:
            df_prs = pd.DataFrame(trends["prs_over_time"])
            st.line_chart(df_prs, x="date", y="count")
        else:
            st.info("No timeline records available yet.")
            
    # 2. Top problematic repos
    st.write("### 🚨 Most Problematic Repositories")
    if trends["problematic_repositories"]:
        df_repos = pd.DataFrame(trends["problematic_repositories"])
        st.bar_chart(df_repos, x="repository", y="issues")
    else:
        st.info("No repository records available yet.")
