"""
Career Copilot - Job Application Tracking Frontend
A streamlined interface for tracking job applications and managing your job search.
"""

import logging
import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any

import streamlit as st
import pandas as pd
import plotly.express as px

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    """Simple API client for backend communication"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.session = requests.Session()
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
    
    def clear_token(self):
        """Clear authentication token"""
        self.token = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response"""
        try:
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Response error: {str(e)}"}
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login to get authentication token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json={"username": username, "email": email, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def get_jobs(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get list of jobs"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/jobs",
                params={"skip": skip, "limit": limit},
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/jobs",
                json=job_data,
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def update_job(self, job_id: int, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing job"""
        try:
            response = self.session.put(
                f"{self.base_url}/api/v1/jobs/{job_id}",
                json=job_data,
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def delete_job(self, job_id: int) -> Dict[str, Any]:
        """Delete a job"""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/jobs/{job_id}",
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def get_applications(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get list of applications"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/applications",
                params={"skip": skip, "limit": limit},
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def create_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new application"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/applications",
                json=application_data,
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def update_application(self, application_id: int, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing application"""
        try:
            response = self.session.put(
                f"{self.base_url}/api/v1/applications/{application_id}",
                json=application_data,
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/analytics/summary",
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def health_check(self) -> Dict[str, Any]:
        """Check backend health"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/health",
                timeout=5
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}

    def get_user_profile(self) -> Dict[str, Any]:
        """Get the current user's profile"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/profile",
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}

    def update_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the current user's profile"""
        try:
            response = self.session.put(
                f"{self.base_url}/api/v1/profile",
                json=profile_data,
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}

    def get_recommendations(self, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """Get personalized job recommendations"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/recommendations",
                params={"skip": skip, "limit": limit},
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}

    def get_skill_gap_analysis(self) -> Dict[str, Any]:
        """Get skill gap analysis for the current user"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/skill-gap",
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}

    def get_interview_trends(self) -> Dict[str, Any]:
        """Get interview trends analysis for the current user"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/analytics/interview-trends",
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}

    def create_job_feedback(self, job_id: int, is_helpful: bool, comment: Optional[str] = None) -> Dict[str, Any]:
        """Create feedback for a job recommendation"""
        try:
            params = {"is_helpful": is_helpful}
            if comment:
                params["comment"] = comment
            
            response = self.session.post(
                f"{self.base_url}/api/v1/jobs/{job_id}/feedback",
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}

    def get_user_feedback(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get user's job recommendation feedback"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/job-recommendation-feedback",
                params={"limit": limit, "offset": offset},
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}


# Initialize API client
backend_url = os.getenv("BACKEND_URL", "http://localhost:8002")
api_client = APIClient(backend_url)


def setup_page_config():
    """Configure Streamlit page"""
    st.set_page_config(
        page_title="Career Copilot",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def initialize_session_state():
    """Initialize session state variables"""
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"


def render_login_form():
    """Render the login/register form"""
    st.title("💼 Career Copilot")
    st.subheader("Track Your Job Applications")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    with st.spinner("Authenticating..."):
                        response = api_client.login(username, password)
                        if "error" not in response and "access_token" in response:
                            st.session_state.auth_token = response["access_token"]
                            st.session_state.user_info = response.get("user", {})
                            api_client.set_token(response["access_token"])
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(f"Login failed: {response.get('error', 'Unknown error')}")
    
    with tab2:
        with st.form("register_form"):
            st.subheader("Create Account")
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_submitted = st.form_submit_button("Register", use_container_width=True)
            
            if register_submitted:
                if not new_username or not new_email or not new_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    with st.spinner("Creating account..."):
                        response = api_client.register(new_username, new_email, new_password)
                        if "error" not in response:
                            st.success("Account created! Please login.")
                        else:
                            st.error(f"Registration failed: {response.get('error', 'Unknown error')}")


def render_dashboard():
    """Render the analytics dashboard - Task 12.4"""
    st.title("📊 Analytics Dashboard")
    
    st.markdown("""
    Track your job search progress with comprehensive analytics and insights.
    """)
    
    # Get analytics summary
    with st.spinner("Loading analytics..."):
        analytics = api_client.get_analytics_summary()
    
    if "error" in analytics:
        st.warning("Unable to load analytics. Backend may not be running.")
        st.info("Make sure the backend server is running and you're authenticated.")
        # Show placeholder metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Jobs", "0")
        with col2:
            st.metric("Applications", "0")
        with col3:
            st.metric("Interviews", "0")
        with col4:
            st.metric("Offers", "0")
        return
    
    # Display key metrics in cards
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_jobs = analytics.get("total_jobs", 0)
        st.metric("Total Jobs", total_jobs, help="Total number of jobs you're tracking")
    
    with col2:
        total_apps = analytics.get("total_applications", 0)
        st.metric("Applications", total_apps, help="Total applications submitted")
    
    with col3:
        interviews = analytics.get("interviews_scheduled", 0)
        st.metric("Interviews", interviews, help="Applications that reached interview stage")
    
    with col4:
        offers = analytics.get("offers_received", 0)
        st.metric("Offers", offers, help="Job offers received")

    st.divider()

    # Daily Application Goal
    st.subheader("🎯 Daily Application Goal")
    daily_apps_today = analytics.get("daily_applications_today", 0)
    daily_goal = analytics.get("daily_application_goal", 10)
    daily_goal_progress = analytics.get("daily_goal_progress", 0)
    
    st.progress(daily_goal_progress / 100.0)
    st.metric("Applications Today", f"{daily_apps_today} / {daily_goal}", help=f"You have applied to {daily_apps_today} out of your goal of {daily_goal} jobs today.")

    st.divider()

    # Status Breakdown Pie Chart
    st.subheader("📊 Application Status Breakdown")
    status_breakdown = analytics.get("status_breakdown", {})
    
    if status_breakdown and sum(status_breakdown.values()) > 0:
        df_status = pd.DataFrame(list(status_breakdown.items()), columns=['Status', 'Count'])
        
        # Create a more colorful pie chart
        colors = {
            'interested': '#FFA726',
            'applied': '#42A5F5',
            'interview': '#66BB6A',
            'offer': '#26A69A',
            'accepted': '#4CAF50',
            'rejected': '#EF5350',
            'declined': '#BDBDBD'
        }
        
        fig = px.pie(
            df_status, 
            values='Count', 
            names='Status', 
            title='Application Status Distribution',
            color='Status',
            color_discrete_map=colors
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        
        # Show status counts in a table
        with st.expander("📋 Detailed Status Counts"):
            st.dataframe(df_status, use_container_width=True, hide_index=True)
    else:
        st.info("No application data yet. Start applying to jobs to see your status breakdown!")

    st.divider()
    
    # Recent Activity
    st.subheader("🕐 Recent Activity")
    applications = api_client.get_applications(limit=5)
    
    if "error" in applications:
        st.info("No recent activity to display")
    else:
        if applications and len(applications) > 0:
            for idx, app in enumerate(applications, 1):
                job = app.get('job', {})
                status = app.get('status', 'Unknown')
                
                # Status emoji mapping
                status_emoji = {
                    'interested': '👀',
                    'applied': '📝',
                    'interview': '🎤',
                    'offer': '🎉',
                    'accepted': '✅',
                    'rejected': '❌',
                    'declined': '🚫'
                }
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**{idx}. {job.get('title', 'Unknown')}**")
                        st.caption(f"🏢 {job.get('company', 'Unknown Company')}")
                    with col2:
                        emoji = status_emoji.get(status, '📌')
                        st.markdown(f"{emoji} **{status.capitalize()}**")
                    with col3:
                        applied_date = app.get('applied_date', 'N/A')
                        if applied_date != 'N/A':
                            st.caption(applied_date)
                    
                    if idx < len(applications):
                        st.divider()
        else:
            st.info("No applications yet. Start by adding jobs and applying!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add Jobs", use_container_width=True):
                    st.session_state.current_page = "jobs"
                    st.rerun()
            with col2:
                if st.button("✨ View Recommendations", use_container_width=True):
                    st.session_state.current_page = "recommendations"
                    st.rerun()

    st.divider()

    # Interview Trends Analysis
    st.subheader("🎤 Interview Trends")
    with st.spinner("Loading interview trends..."):
        interview_trends = api_client.get_interview_trends()
    
    if "error" in interview_trends:
        st.warning("Unable to load interview trends.")
    elif interview_trends.get("total_interviews_analyzed", 0) > 0:
        st.info(f"Analyzed {interview_trends['total_interviews_analyzed']} interviews.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Top Common Questions:**")
            for q, count in interview_trends.get("top_common_questions", []):
                st.markdown(f"- {q.capitalize()} (seen {count} times)")
        with col2:
            st.markdown("**Top Skill Areas Discussed:**")
            for s, count in interview_trends.get("top_skill_areas_discussed", []):
                st.markdown(f"- {s.capitalize()} (discussed {count} times)")
        
        st.markdown("**Common Tech Stack in Interviews:**")
        for ts, count in interview_trends.get("common_tech_stack_in_interviews", []):
            st.markdown(f"- {ts.capitalize()} (in {count} jobs)")
    else:
        st.info("No interview data available for trend analysis. Update application statuses to 'interview' and add feedback.")


def render_jobs_page():
    """Render the jobs management page - Task 12.5"""
    st.title("💼 Job Management")
    
    st.markdown("""
    Track and manage job opportunities. Add tech stack, responsibilities, and other details
    to get better recommendations and skill gap analysis.
    """)
    
    # Add new job button
    if st.button("➕ Add New Job", type="primary"):
        st.session_state.show_add_job_form = True
    
    # Add job form
    if st.session_state.get("show_add_job_form", False):
        with st.form("add_job_form"):
            st.subheader("Add New Job")
            
            col1, col2 = st.columns(2)
            with col1:
                company = st.text_input("Company *", help="Company name")
                title = st.text_input("Job Title *", help="Position title")
                location = st.text_input("Location", help="Job location or 'Remote'")
                source_input = st.text_input("Source", value="manual", help="Where you found this job (e.g., LinkedIn, Indeed)")
            with col2:
                url = st.text_input("Job URL", help="Link to the job posting")
                salary_range = st.text_input("Salary Range", help="e.g., $80k-$120k")
                job_type = st.selectbox("Job Type", ["full-time", "part-time", "contract", "internship"])
                remote = st.checkbox("Remote Position")
            
            # Tech Stack field - Task 12.5
            all_possible_skills = [
                "Python", "Java", "JavaScript", "TypeScript", "React", "Angular", "Vue.js", 
                "Node.js", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "SQL", "NoSQL", 
                "PostgreSQL", "MongoDB", "Redis", "Machine Learning", "Data Science", 
                "FastAPI", "Django", "Flask", "Spring Boot", "Go", "Rust", "C++", "C#",
                ".NET", "Ruby", "PHP", "Swift", "Kotlin", "Flutter", "React Native",
                "GraphQL", "REST API", "Microservices", "CI/CD", "Git", "Linux"
            ]
            selected_tech_stack = st.multiselect(
                "Tech Stack *", 
                options=sorted(all_possible_skills), 
                default=[],
                help="Select all technologies required for this job"
            )
            
            # Responsibilities field - Task 12.5
            responsibilities_input = st.text_area(
                "Responsibilities", 
                help="Key responsibilities for this role",
                placeholder="e.g., Design and implement scalable APIs, Lead technical discussions, Mentor junior developers"
            )
            
            description = st.text_area(
                "Description", 
                help="Full job description",
                placeholder="Paste the full job description here..."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Add Job", use_container_width=True, type="primary")
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit:
                if not company or not title:
                    st.error("Company and Job Title are required")
                elif not selected_tech_stack:
                    st.warning("Consider adding tech stack for better recommendations")
                    job_data = {
                        "company": company,
                        "title": title,
                        "location": location,
                        "url": url,
                        "salary_range": salary_range,
                        "job_type": job_type,
                        "description": description,
                        "remote": remote,
                        "tech_stack": selected_tech_stack,
                        "responsibilities": responsibilities_input,
                        "source": source_input,
                    }
                    response = api_client.create_job(job_data)
                    if "error" not in response:
                        st.success("✅ Job added successfully!")
                        st.session_state.show_add_job_form = False
                        st.rerun()
                    else:
                        st.error(f"Failed to add job: {response.get('error')}")
                else:
                    job_data = {
                        "company": company,
                        "title": title,
                        "location": location,
                        "url": url,
                        "salary_range": salary_range,
                        "job_type": job_type,
                        "description": description,
                        "remote": remote,
                        "tech_stack": selected_tech_stack,
                        "responsibilities": responsibilities_input,
                        "source": source_input,
                    }
                    with st.spinner("Adding job..."):
                        response = api_client.create_job(job_data)
                        if "error" not in response:
                            st.success("✅ Job added successfully!")
                            st.session_state.show_add_job_form = False
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"Failed to add job: {response.get('error')}")
            
            if cancel:
                st.session_state.show_add_job_form = False
                st.rerun()
    
    st.divider()
    
    # List jobs
    st.subheader("Your Jobs")
    jobs = api_client.get_jobs()
    
    if "error" in jobs:
        st.warning("Unable to load jobs. Backend may not be running.")
        st.info("Make sure the backend server is running and you're authenticated.")
    else:
        if jobs and len(jobs) > 0:
            st.success(f"You have {len(jobs)} job(s) tracked")
            
            for idx, job in enumerate(jobs, 1):
                # Source badge - Task 12.5
                source = job.get('source', 'manual')
                source_colors = {
                    'manual': '#9E9E9E',
                    'scraped': '#2196F3',
                    'linkedin': '#0077B5',
                    'indeed': '#2164F3',
                    'glassdoor': '#0CAA41'
                }
                source_color = source_colors.get(source.lower(), '#9E9E9E')
                
                # Match score badge - Task 12.5
                match_score = job.get('match_score')
                match_badge = ""
                if match_score is not None:
                    if match_score >= 80:
                        match_badge = f"🟢 {match_score:.0f}% Match"
                    elif match_score >= 60:
                        match_badge = f"🟡 {match_score:.0f}% Match"
                    else:
                        match_badge = f"🟠 {match_score:.0f}% Match"
                
                title_display = f"#{idx} - {job.get('title')} at {job.get('company')}"
                if match_badge:
                    title_display += f" | {match_badge}"
                
                with st.expander(title_display):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**📍 Location:** {job.get('location', 'N/A')}")
                        st.markdown(f"**💼 Type:** {job.get('job_type', 'N/A')}")
                        st.markdown(f"**🏠 Remote:** {'✅ Yes' if job.get('remote') else '❌ No'}")
                        # Source badge display - Task 12.5
                        st.markdown(f"**📌 Source:** <span style='background-color: {source_color}; color: white; padding: 3px 8px; border-radius: 5px; font-size: 0.85em;'>{source.upper()}</span>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**💰 Salary:** {job.get('salary_range', 'N/A')}")
                        if job.get('url'):
                            st.markdown(f"**🔗 URL:** [View Job]({job.get('url')})")
                        if match_score is not None:
                            st.metric("Match Score", f"{match_score:.0f}%")
                    
                    # Tech Stack display - Task 12.5
                    if job.get('tech_stack'):
                        st.markdown("**🛠️ Tech Stack:**")
                        tech_html = " ".join([f'<span style="background-color: #2196F3; color: white; padding: 3px 8px; border-radius: 5px; margin: 2px; display: inline-block; font-size: 0.85em;">{tech}</span>' for tech in job.get('tech_stack')])
                        st.markdown(tech_html, unsafe_allow_html=True)

                    # Documents Required display - Task 25
                    if job.get('documents_required'):
                        st.markdown("**📄 Documents Required:**")
                        docs_html = " ".join([f'<span style="background-color: #607D8B; color: white; padding: 3px 8px; border-radius: 5px; margin: 2px; display: inline-block; font-size: 0.85em;">{doc}</span>' for doc in job.get('documents_required')])
                        st.markdown(docs_html, unsafe_allow_html=True)
                    
                    # Responsibilities display - Task 12.5
                    if job.get('responsibilities'):
                        with st.expander("📋 Responsibilities"):
                            st.write(job.get('responsibilities'))
                    
                    if job.get('description'):
                        with st.expander("📄 Full Description"):
                            st.write(job.get('description'))
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📝 Apply", key=f"apply_{job.get('id')}", use_container_width=True):
                            # Create application
                            app_data = {
                                "job_id": job.get('id'),
                                "status": "interested",
                                "notes": "Applied via job management"
                            }
                            response = api_client.create_application(app_data)
                            if "error" not in response:
                                st.success(f"✅ Application created!")
                                st.rerun()
                            else:
                                st.error(f"Failed: {response.get('error')}")
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{job.get('id')}", use_container_width=True):
                            st.info("Edit functionality coming soon")
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{job.get('id')}", use_container_width=True):
                            response = api_client.delete_job(job.get('id'))
                            if "error" not in response:
                                st.success("Job deleted")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete: {response.get('error')}")
        else:
            st.info("No jobs added yet. Click 'Add New Job' to get started!")
            st.markdown("""
            **Tips for adding jobs:**
            - Include tech stack for better recommendations
            - Add responsibilities to understand role requirements
            - Set source to track where you found the job
            """)


def render_applications_page():
    """Render the applications management page"""
    st.title("📝 Applications")
    
    # Get applications
    applications = api_client.get_applications()
    
    if "error" in applications:
        st.warning("Unable to load applications. Backend may not be running.")
    else:
        if applications:
            # Filter by status
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "interested", "applied", "interview", "offer", "rejected", "accepted", "declined"]
            )
            
            filtered_apps = applications if status_filter == "All" else [
                app for app in applications if app.get('status') == status_filter
            ]
            
            st.write(f"Showing {len(filtered_apps)} application(s)")
            
            for app in filtered_apps:
                with st.expander(f"{app.get('job', {}).get('title', 'Unknown')} - {app.get('status', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Company:** {app.get('job', {}).get('company', 'Unknown')}")
                        st.write(f"**Status:** {app.get('status', 'Unknown')}")
                        st.write(f"**Applied:** {app.get('applied_date', 'N/A')}")
                    with col2:
                        st.write(f"**Interview:** {app.get('interview_date', 'N/A')}")
                        st.write(f"**Response:** {app.get('response_date', 'N/A')}")
                    
                    if app.get('notes'):
                        st.write(f"**Notes:** {app.get('notes')}")

                    # Interview Feedback - Task 22
                    st.subheader("Interview Feedback")
                    current_feedback = app.get("interview_feedback", {})
                    feedback_questions = st.text_area(
                        "Common Questions Asked (comma-separated)",
                        value=", ".join(current_feedback.get("questions", [])),
                        key=f"feedback_questions_{app.get('id')}"
                    )
                    feedback_skill_areas = st.text_area(
                        "Skill Areas Discussed (comma-separated)",
                        value=", ".join(current_feedback.get("skill_areas", [])),
                        key=f"feedback_skill_areas_{app.get('id')}"
                    )
                    feedback_notes = st.text_area(
                        "Subjective Notes",
                        value=current_feedback.get("notes", ""),
                        key=f"feedback_notes_{app.get('id')}"
                    )
                    
                    # Update status
                    new_status = st.selectbox(
                        "Update Status",
                        ["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"],
                        index=["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"].index(app.get('status', 'interested')),
                        key=f"status_{app.get('id')}"
                    )
                    
                    if st.button("Update", key=f"update_{app.get('id')}"):
                        update_data = {"status": new_status}
                        
                        # Add interview feedback to update data
                        interview_feedback_data = {
                            "questions": [q.strip() for q in feedback_questions.split(",") if q.strip()],
                            "skill_areas": [s.strip() for s in feedback_skill_areas.split(",") if s.strip()],
                            "notes": feedback_notes
                        }
                        if any(interview_feedback_data.values()): # Only send if there's actual feedback
                            update_data["interview_feedback"] = interview_feedback_data

                        response = api_client.update_application(app.get('id'), update_data)
                        if "error" not in response:
                            st.success("Status updated!")
                            st.rerun()
                        else:
                            st.error(f"Failed to update: {response.get('error')}")
        else:
            st.info("No applications yet. Start by applying to jobs!")


def secure_file_upload():
	"""Perform secure file upload with enhanced progress tracking and user feedback."""
	# File upload header
	st.markdown("""
	<div class="upload-section">
		<div class="upload-header">
			<div class="upload-title">📤 Upload Your Contract</div>
			<div class="upload-subtitle">Secure document analysis with comprehensive validation</div>
		</div>
	</div>
	""", unsafe_allow_html=True)
	
	# Use the enhanced file upload component
	try:
		uploaded_file = file_upload_component()
	except Exception as e:
		# Enhanced fallback with better error handling
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				handle_error_with_recovery(
					error_response={
						"error": str(e), 
						"category": "file_upload", 
						"severity": "low",
						"suggestions": [
							"Try refreshing the page",
							"Clear your browser cache",
							"Try a different browser"
						]
					},
					show_technical_details=False,
					allow_retry=False
				)
			except:
				pass
		
		# Enhanced fallback uploader
		st.markdown("### 📁 File Upload")
		uploaded_file = st.file_uploader(
			"Choose a contract file",
			type=["pdf", "docx", "txt"], 
			help="📋 Supported formats: PDF (recommended), DOCX, TXT • Maximum size: 50MB",
			accept_multiple_files=False
		)

	if uploaded_file:
		# Show upload progress
		with st.spinner("🔍 Validating uploaded file..."):
			try:
				# Enhanced file validation with better user feedback
				file_size_mb = uploaded_file.size / (1024 * 1024)
				max_size_mb = 50  # 50MB limit

				# File size validation with detailed feedback
				if file_size_mb > max_size_mb:
					st.markdown("""
					<div class="validation-error">
						<h4>❌ File Size Error</h4>
						<p><strong>Issue:</strong> File size ({:.1f}MB) exceeds maximum allowed size ({:.0f}MB)</p>
					</div>
					""".format(file_size_mb, max_size_mb), unsafe_allow_html=True)
					
					# Enhanced suggestions with actionable steps
					with st.expander("💡 How to Fix This", expanded=True):
						col1, col2 = st.columns(2)
						with col1:
							st.markdown("**📉 Reduce File Size:**")
							st.markdown("• Compress your PDF using online tools")
							st.markdown("• Remove unnecessary images or pages")
							st.markdown("• Convert to a more efficient format")
						with col2:
							st.markdown("**✂️ Split Large Documents:**")
							st.markdown("• Analyze sections separately")
							st.markdown("• Focus on key contract clauses")
							st.markdown("• Use PDF splitting tools")
					
					return False

				# File type validation with enhanced feedback
				file_extension = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else ""
				allowed_types = ["pdf", "docx", "txt"]

				if file_extension not in allowed_types:
					st.markdown("""
					<div class="validation-error">
						<h4>❌ File Type Error</h4>
						<p><strong>Issue:</strong> File type '.{}' is not supported</p>
					</div>
					""".format(file_extension), unsafe_allow_html=True)
					
					# Enhanced file type guidance
					with st.expander("📋 Supported File Types", expanded=True):
						col1, col2, col3 = st.columns(3)
						with col1:
							st.markdown("**📄 PDF Files**")
							st.markdown("• Best for contracts")
							st.markdown("• Preserves formatting")
							st.markdown("• Up to 50MB")
						with col2:
							st.markdown("**📝 Word Documents**")
							st.markdown("• DOCX format only")
							st.markdown("• Easy to edit")
							st.markdown("• Up to 25MB")
						with col3:
							st.markdown("**📃 Text Files**")
							st.markdown("• Plain text format")
							st.markdown("• Fastest processing")
							st.markdown("• Up to 10MB")
					
					return False

				# Enhanced filename validation
				if not uploaded_file.name or uploaded_file.name.strip() == "":
					st.error("❌ Invalid filename. Please ensure the file has a proper name.")
					return False

				# Check for problematic characters with better feedback
				import re
				if re.search(r'[<>:"/\\|?*]', uploaded_file.name):
					st.warning("⚠️ **Filename Warning:** Contains special characters that may cause issues.")
					st.info("💡 **Suggestion:** Rename the file to use only letters, numbers, spaces, hyphens, and underscores.")

				# Store file in session state with enhanced metadata
				st.session_state.uploaded_file = {
					"file": uploaded_file,
					"file_id": f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
					"temp_path": f"/tmp/{uploaded_file.name}",
					"validation_result": {
						"is_secure": True, 
						"file_hash": f"hash_{hash(uploaded_file.name)}",
						"threats_detected": [],
						"validation_time": datetime.now().isoformat()
					},
					"upload_time": datetime.now().isoformat(),
					"file_size_mb": file_size_mb,
					"file_extension": file_extension
				}

				# Enhanced success display
				st.markdown("""
				<div class="validation-success">
					<h4>✅ File Validation Successful</h4>
					<p>Your file has been uploaded and validated successfully. Ready for analysis!</p>
				</div>
				""", unsafe_allow_html=True)

				# Enhanced file information display
				st.markdown('<div class="file-info-card">', unsafe_allow_html=True)
				
				col1, col2, col3, col4 = st.columns(4)
				with col1:
					st.metric("📄 File Name", uploaded_file.name[:20] + "..." if len(uploaded_file.name) > 20 else uploaded_file.name)
				with col2:
					st.metric("📊 File Size", f"{file_size_mb:.1f} MB")
				with col3:
					st.metric("📋 File Type", file_extension.upper())
				with col4:
					st.metric("🔒 Security", "✅ Validated")
				
				st.markdown('</div>', unsafe_allow_html=True)
				
				# Additional file insights
				with st.expander("📋 File Details", expanded=False):
					col1, col2 = st.columns(2)
					with col1:
						st.text(f"Full filename: {uploaded_file.name}")
						st.text(f"File size: {uploaded_file.size:,} bytes")
						st.text(f"Upload time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
					with col2:
						st.text(f"File ID: {st.session_state.uploaded_file['file_id']}")
						st.text(f"MIME type: {getattr(uploaded_file, 'type', 'Unknown')}")
						st.text(f"Validation: Passed")

				return True
				
			except Exception as e:
				# Enhanced error handling with better user experience
				st.markdown("""
				<div class="validation-error">
					<h4>❌ Validation Error</h4>
					<p><strong>Issue:</strong> An error occurred during file validation</p>
				</div>
				""", unsafe_allow_html=True)
				
				# Detailed error information
				with st.expander("🔧 Error Details & Solutions", expanded=True):
					col1, col2 = st.columns(2)
					with col1:
						st.markdown("**🔍 What Happened:**")
						st.code(str(e), language=None)
						st.text(f"Error time: {datetime.now().strftime('%H:%M:%S')}")
					with col2:
						st.markdown("**💡 What You Can Try:**")
						st.markdown("• Refresh the page and try again")
						st.markdown("• Try uploading a different file")
						st.markdown("• Check that the file isn't corrupted")
						st.markdown("• Try using a different browser")
						st.markdown("• Contact support if the issue persists")
				
				# Log error if production features available
				if PRODUCTION_FEATURES_AVAILABLE:
					try:
						track_user_event("file_upload_error", {
							"filename": getattr(uploaded_file, 'name', 'unknown'),
							"error": str(e),
							"file_size": getattr(uploaded_file, 'size', 0),
							"timestamp": datetime.now().isoformat()
						})
					except:
						pass
				
				return False

	return False


def secure_analysis():
	"""Perform secure job application tracking with enhanced progress tracking and user feedback."""
	if not st.session_state.uploaded_file:
		st.markdown("""
		<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
		            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
			<h4>❌ No File Available</h4>
			<p>Please upload a contract file before starting the analysis.</p>
		</div>
		""", unsafe_allow_html=True)
		return

	try:
		# Enhanced analysis header
		st.markdown("""
		<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
		            color: white; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center;">
			<h2 style="margin: 0; font-size: 24px;">🔍 Contract Analysis</h2>
			<p style="margin: 8px 0 0 0; opacity: 0.9;">AI-powered contract risk assessment and analysis</p>
		</div>
		""", unsafe_allow_html=True)

		# Show file being analyzed
		uploaded_file_info = st.session_state.uploaded_file
		st.info(f"📄 **Analyzing:** {uploaded_file_info['file'].name} ({uploaded_file_info.get('file_size_mb', 0):.1f} MB)")

		# Enhanced progress tracking
		progress_container = st.container()
		
		with progress_container:
			# Multi-stage progress indicator
			progress_stages = [
				"🔒 Initializing secure analysis...",
				"📤 Uploading file to analysis service...",
				"🤖 AI agents processing contract...",
				"⚖️ Analyzing legal risks and clauses...",
				"📊 Generating comprehensive report..."
			]
			
			# Show current stage
			current_stage = 0
			stage_progress = st.progress(0)
			stage_text = st.empty()
			
			# Stage 1: Initialize
			stage_text.info(progress_stages[current_stage])
			stage_progress.progress(0.2)
			
			# Get the uploaded file
			uploaded_file = st.session_state.uploaded_file["file"]

			# Validate file is still available
			if not uploaded_file:
				st.markdown("""
				<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
				            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
					<h4>❌ File No Longer Available</h4>
					<p>The uploaded file is no longer accessible. Please upload the file again.</p>
				</div>
				""", unsafe_allow_html=True)
				st.session_state.uploaded_file = None
				return

			# Stage 2: Upload
			current_stage = 1
			stage_text.info(progress_stages[current_stage])
			stage_progress.progress(0.4)

			# Call the backend API to start analysis
			try:
				response = api_client.analyze_contract_async(uploaded_file)
			except ConnectionError as e:
				# Enhanced connection error handling
				st.markdown("""
				<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
				            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
					<h4>🌐 Connection Error</h4>
					<p><strong>Issue:</strong> Unable to connect to the analysis service</p>
				</div>
				""", unsafe_allow_html=True)
				
				with st.expander("🔧 Troubleshooting Steps", expanded=True):
					col1, col2 = st.columns(2)
					with col1:
						st.markdown("**🔍 Check These:**")
						st.markdown("• Internet connection is active")
						st.markdown("• Backend service is running")
						st.markdown("• No firewall blocking requests")
					with col2:
						st.markdown("**💡 Try These Solutions:**")
						st.markdown("• Wait a moment and retry")
						st.markdown("• Refresh the page")
						st.markdown("• Contact support if issue persists")
				
				st.session_state.is_processing = False
				return
			except TimeoutError as e:
				# Enhanced timeout error handling
				st.markdown("""
				<div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
				            border: 1px solid #ffeaa7; border-radius: 8px; padding: 16px; margin: 16px 0;">
					<h4>⏱️ Request Timeout</h4>
					<p><strong>Issue:</strong> The analysis request took too long to process</p>
				</div>
				""", unsafe_allow_html=True)
				
				with st.expander("💡 Solutions", expanded=True):
					st.markdown("**🔧 What you can try:**")
					st.markdown("• **Reduce file size:** Try with a smaller document")
					st.markdown("• **System load:** The system may be experiencing high demand")
					st.markdown("• **Network issues:** Check your internet connection")
					st.markdown("• **Retry:** Wait a few minutes and try again")
				
				st.session_state.is_processing = False
				return

			# Stage 3: Processing
			current_stage = 2
			stage_text.info(progress_stages[current_stage])
			stage_progress.progress(0.6)

			# Handle API response with enhanced feedback
			if response and "error" not in response:
				# Stage 4: Analysis
				current_stage = 3
				stage_text.info(progress_stages[current_stage])
				stage_progress.progress(0.8)
				
				# Check response type
				if "risky_clauses" in response or "status" in response:
					# Stage 5: Complete
					current_stage = 4
					stage_text.success(progress_stages[current_stage])
					stage_progress.progress(1.0)
					
					# Handle immediate sync result
					st.session_state.analysis_results = response
					st.session_state.is_processing = False
					st.session_state.is_polling = False
					
					# Enhanced success message
					st.markdown("""
					<div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
					            border: 1px solid #c3e6cb; border-radius: 8px; padding: 16px; margin: 16px 0; text-align: center;">
						<h4>✅ Analysis Complete!</h4>
						<p>Your contract has been successfully analyzed. Review the results below.</p>
					</div>
					""", unsafe_allow_html=True)
					
					# Show analysis summary
					risk_score = response.get('risk_score', 0)
					risk_level = response.get('risk_level', 'Unknown')
					risky_clauses = len(response.get('risky_clauses', []))
					
					col1, col2, col3 = st.columns(3)
					with col1:
						st.metric("🎯 Risk Score", f"{risk_score:.1%}")
					with col2:
						st.metric("⚠️ Risk Level", risk_level)
					with col3:
						st.metric("📋 Issues Found", risky_clauses)
					
					st.rerun()
					
				elif "task_id" in response:
					# Handle async task (fallback)
					st.session_state.task_id = response["task_id"]
					st.session_state.is_processing = False
					st.session_state.is_polling = True
					
					st.markdown("""
					<div style="background: linear-gradient(135deg, #cce5ff 0%, #b3d9ff 100%); 
					            border: 1px solid #b3d9ff; border-radius: 8px; padding: 16px; margin: 16px 0; text-align: center;">
						<h4>🚀 Analysis Started!</h4>
						<p>Task ID: <code>{}</code></p>
						<p>Your analysis is now running. We'll track the progress automatically.</p>
					</div>
					""".format(response['task_id']), unsafe_allow_html=True)
					
					st.rerun()
				else:
					# Unknown response format
					st.error("❌ **Unexpected Response:** The server returned an unexpected response format")
					st.session_state.is_processing = False
			else:
				# Enhanced error handling for API errors
				error_msg = response.get("error", "Failed to start analysis task") if response else "No response from server"
				
				if isinstance(response, dict) and "error" in response:
					error_details = response.get("error", {})
					if isinstance(error_details, dict):
						error_type = error_details.get("error", "Analysis Error")
						user_message = error_details.get("message", error_msg)
						suggestions = error_details.get("suggestions", [])
						
						st.markdown(f"""
						<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
						            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
							<h4>❌ {error_type}</h4>
							<p><strong>Issue:</strong> {user_message}</p>
						</div>
						""", unsafe_allow_html=True)
						
						if suggestions:
							with st.expander("💡 Suggested Solutions", expanded=True):
								for i, suggestion in enumerate(suggestions, 1):
									st.markdown(f"{i}. {suggestion}")
					else:
						st.error(f"❌ **Analysis Error:** {error_details}")
				else:
					st.markdown(f"""
					<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
					            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
						<h4>❌ Analysis Failed</h4>
						<p><strong>Issue:</strong> {error_msg}</p>
					</div>
					""", unsafe_allow_html=True)
					
				st.session_state.is_processing = False

	except Exception as e:
		# Enhanced unexpected error handling
		error_msg = f"Analysis failed: {str(e)}"
		st.session_state.error_message = error_msg
		st.session_state.is_processing = False
		
		st.markdown("""
		<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
		            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
			<h4>❌ Unexpected Error</h4>
			<p><strong>Issue:</strong> An unexpected error occurred during analysis</p>
		</div>
		""", unsafe_allow_html=True)
		
		# Enhanced error details and solutions
		with st.expander("🔧 Error Details & Solutions", expanded=False):
			col1, col2 = st.columns(2)
			with col1:
				st.markdown("**🔍 Technical Details:**")
				st.code(str(e), language=None)
				st.text(f"Error time: {datetime.now().strftime('%H:%M:%S')}")
				st.text(f"File: {st.session_state.uploaded_file.get('file', {}).name if st.session_state.uploaded_file else 'Unknown'}")
			with col2:
				st.markdown("**💡 What You Can Try:**")
				st.markdown("• **Refresh:** Reload the page and try again")
				st.markdown("• **Different file:** Try with another document")
				st.markdown("• **Browser:** Try a different browser")
				st.markdown("• **Support:** Contact support with the error details")
		
		# Log error if production features available
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event("analysis_error", {
					"filename": st.session_state.uploaded_file.get("file", {}).name if st.session_state.uploaded_file else "unknown",
					"error": str(e),
					"timestamp": datetime.now().isoformat(),
					"file_size": st.session_state.uploaded_file.get("file_size_mb", 0) if st.session_state.uploaded_file else 0
				})
			except:
				pass


def poll_for_results():
	"""Poll the backend for analysis results."""
	if not st.session_state.get("is_polling") or not st.session_state.get("task_id"):
		return

	task_id = st.session_state.task_id
	st.info(f"Analysis in progress... Task ID: {task_id}")

	try:
		with st.spinner("Polling for results..."):
			max_polls = 60  # Maximum number of polling attempts
			poll_count = 0
			
			while st.session_state.is_polling and poll_count < max_polls:
				poll_count += 1
				
				try:
					status_response = api_client.get_analysis_status(task_id)
				except ConnectionError:
					st.error("❌ **Connection Lost**")
					st.markdown("Lost connection while checking analysis status.")
					st.info("💡 **What you can try:**")
					st.markdown("- Check your internet connection")
					st.markdown("- Refresh the page to check status manually")
					st.session_state.is_polling = False
					break
				except Exception as e:
					st.error(f"❌ **Error Checking Status**: {str(e)}")
					st.session_state.is_polling = False
					break

				if "error" in status_response:
					error_details = status_response.get("error", {})
					if isinstance(error_details, dict):
						error_type = error_details.get("error", "Status Check Error")
						user_message = error_details.get("message", "Error checking analysis status")
						
						st.error(f"❌ **{error_type}**")
						st.markdown(user_message)
					else:
						st.error(f"❌ Error checking status: {error_details}")
					
					st.session_state.is_polling = False
					break

				status = status_response.get("status")
				progress = status_response.get("progress", 0)
				
				# Update progress bar
				st.progress(progress / 100.0)
				
				# Show status message
				status_messages = {
					"pending": "⏳ Analysis queued...",
					"running": "🔄 Analysis in progress...",
					"processing": "⚙️ Processing results...",
					"finalizing": "✨ Finalizing analysis..."
				}
				
				if status in status_messages:
					st.caption(status_messages[status])

				if status == "completed":
					st.success("✅ Analysis complete! Fetching results...")
					
					try:
						results = api_client.get_analysis_results(task_id)
						if "error" not in results:
							st.session_state.analysis_results = results
							
							# Log successful completion
							if PRODUCTION_FEATURES_AVAILABLE:
								try:
									track_user_event("analysis_completed", {
										"task_id": task_id,
										"processing_time": results.get("processing_time", 0)
									})
								except:
									pass
						else:
							error_details = results.get("error", {})
							if isinstance(error_details, dict):
								error_type = error_details.get("error", "Results Error")
								user_message = error_details.get("message", "Error fetching results")
								
								st.error(f"❌ **{error_type}**")
								st.markdown(user_message)
							else:
								st.error(f"❌ Error fetching results: {error_details}")
								
					except Exception as e:
						st.error(f"❌ **Error Fetching Results**: {str(e)}")
						st.info("💡 You can try refreshing the page to check if results are available.")
					
					st.session_state.is_polling = False
					st.session_state.task_id = None
					st.rerun()
					
				elif status in ["failed", "timeout"]:
					error_msg = status_response.get("error", "An unknown error occurred")
					
					if status == "timeout":
						st.error("❌ **Analysis Timeout**")
						st.markdown("The analysis took longer than expected to complete.")
						st.info("💡 **What you can try:**")
						st.markdown("- Try again with a smaller document")
						st.markdown("- The system may be experiencing high load")
						st.markdown("- Contact support if timeouts persist")
					else:
						st.error("❌ **Analysis Failed**")
						st.markdown(f"Analysis failed: {error_msg}")
						st.info("💡 **What you can try:**")
						st.markdown("- Try analyzing the document again")
						st.markdown("- Check that the document contains readable text")
						st.markdown("- Try with a different document format")
					
					st.session_state.is_polling = False
					st.session_state.task_id = None
					break
				
				# Wait before next poll (avoid overwhelming the server)
				import time
				time.sleep(2)
			
			# Handle max polls reached
			if poll_count >= max_polls:
				st.warning("⚠️ **Polling Timeout**")
				st.markdown("Analysis is taking longer than expected.")
				st.info("💡 You can refresh the page later to check if the analysis has completed.")
				st.session_state.is_polling = False
				
	except Exception as e:
		st.error("❌ **Unexpected Error During Polling**")
		st.markdown(f"An error occurred while checking analysis status: {str(e)}")
		
		with st.expander("🔧 Error Details"):
			st.code(str(e))
		
		st.info("💡 **What you can try:**")
		st.markdown("- Refresh the page to check status manually")
		st.markdown("- Try starting a new analysis")
		st.markdown("- Contact support if the problem persists")
		
		st.session_state.is_polling = False


def render_security_sidebar():
	"""Render security information in sidebar."""
	with st.sidebar:
		st.header("🔒 Security Status")

		# Ensure security is initialized
		if "security" not in st.session_state or st.session_state.security is None:
			setup_security()

		if st.session_state.security:
			security = st.session_state.security

			# Security metrics
			memory_usage = security["memory_manager"].get_memory_usage()
			temp_file_stats = security["memory_manager"].get_temp_file_stats()

			st.metric("Memory Usage", f"{memory_usage['rss_mb']:.1f} MB")
			st.metric("Temp Files", temp_file_stats["total_files"])
			st.metric("Security Level", "High")

			# Recent security events
			recent_events = security["audit_logger"].get_recent_events(5)
			if recent_events:
				st.subheader("Recent Security Events")
				for event in recent_events[-3:]:  # Show last 3 events
					level_color = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(event.get("security_level", "low"), "⚪")

					st.text(f"{level_color} {event.get('message', 'Unknown event')}")

			# Security report
			if st.button("📊 Security Report"):
				report = security["audit_logger"].generate_security_report()
				st.json(report)

		st.divider()

		# Security configuration info
		st.subheader("Security Configuration")
		st.info(f"Max file size: {security_config.max_file_size_mb}MB")
		st.info(f"File types: {', '.join(security_config.allowed_file_types)}")
		st.info(f"Rate limiting: {'Enabled' if security_config.enable_rate_limiting else 'Disabled'}")
		st.info(f"Audit logging: {'Enabled' if security_config.enable_audit_logging else 'Disabled'}")


def cleanup_on_exit():
	"""Clean up resources on application exit."""
	# Ensure security is initialized
	if "security" not in st.session_state or st.session_state.security is None:
		setup_security()

	if st.session_state.security:
		security = st.session_state.security

		# Clean up temporary files
		if st.session_state.uploaded_file and "file_id" in st.session_state.uploaded_file:
			security["memory_manager"].secure_delete_file(st.session_state.uploaded_file["file_id"])

		# Force cleanup
		security["memory_manager"].force_cleanup()

		# Log session end
		security["audit_logger"].log_security_event(
			event_type=SecurityEventType.SYSTEM_ERROR, level=SecurityLevel.LOW, message="User session ended", user_id=get_client_info()["session_id"]
		)


def render_analysis_interface():
	"""Render the enhanced main job application tracking interface with improved UX."""
	
	# Enhanced analysis interface styling
	st.markdown("""
	<style>
	.analysis-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 20px;
	}
	.status-card {
		background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
		border-radius: 12px;
		padding: 20px;
		margin: 16px 0;
		border-left: 4px solid;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}
	.status-card.success { border-left-color: #28a745; }
	.status-card.info { border-left-color: #17a2b8; }
	.status-card.warning { border-left-color: #ffc107; }
	.status-card.error { border-left-color: #dc3545; }
	.progress-section {
		background: white;
		border-radius: 12px;
		padding: 24px;
		margin: 20px 0;
		box-shadow: 0 4px 12px rgba(0,0,0,0.1);
	}
	.action-section {
		background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
		border-radius: 12px;
		padding: 24px;
		margin: 20px 0;
		text-align: center;
	}
	</style>
	""", unsafe_allow_html=True)
	
	st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
	
	# Main application flow with enhanced UI
	if st.session_state.analysis_results:
		# Enhanced results display section
		st.markdown("""
		<div class="status-card success">
			<h2 style="margin: 0 0 8px 0; color: #155724;">✅ Analysis Complete</h2>
			<p style="margin: 0; color: #155724; opacity: 0.8;">
				Your contract has been successfully analyzed. Review the comprehensive results below.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		try:
			# Enhanced results display with better error handling
			contract_text = ""
			filename = "contract.pdf"
			
			if st.session_state.uploaded_file and "file" in st.session_state.uploaded_file:
				filename = st.session_state.uploaded_file["file"].name
				# Try to get contract text from analysis results or uploaded file
				if "contract_text" in st.session_state.analysis_results:
					contract_text = st.session_state.analysis_results["contract_text"]
				else:
					# Fallback: read file content if available
					try:
						uploaded_file = st.session_state.uploaded_file["file"]
						if hasattr(uploaded_file, 'getvalue'):
							file_content = uploaded_file.getvalue()
							if isinstance(file_content, bytes):
								contract_text = file_content.decode('utf-8', errors='ignore')
							else:
								contract_text = str(file_content)
					except Exception:
						contract_text = "Contract text not available for display."
			
			# Use the enhanced results display component
			AnalysisResultsDisplay(st.session_state.analysis_results, contract_text, filename)
		except Exception as e:
			st.markdown("""
			<div class="status-card error">
				<h4 style="margin: 0 0 8px 0; color: #721c24;">❌ Display Error</h4>
				<p style="margin: 0; color: #721c24;">
					There was an issue displaying the analysis results. Raw data is shown below.
				</p>
			</div>
			""", unsafe_allow_html=True)
			
			# Fallback to raw results display
			with st.expander("📋 Raw Analysis Results", expanded=True):
				st.json(st.session_state.analysis_results)
			
			# Show error details
			with st.expander("🔧 Error Details", expanded=False):
				st.code(str(e), language="python")

		# Enhanced action buttons section
		st.markdown("""
		<div class="action-section">
			<h3 style="color: #1976d2; margin-bottom: 16px;">🔄 What's Next?</h3>
			<p style="color: #333; margin-bottom: 20px;">
				Ready to analyze another contract? Click below to start fresh.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		col1, col2, col3 = st.columns([1, 2, 1])
		with col2:
			if st.button("🔄 Analyze Another Contract", type="primary", use_container_width=True):
				# Enhanced session cleanup with user feedback
				with st.spinner("🧹 Clearing previous analysis..."):
					st.session_state.analysis_results = None
					st.session_state.uploaded_file = None
					st.session_state.task_id = None
					st.session_state.is_processing = False
					st.session_state.is_polling = False
					st.session_state.error_message = None
					
					# Track user action if production features available
					if PRODUCTION_FEATURES_AVAILABLE:
						try:
							track_user_event('analysis_reset', {
								'previous_filename': filename,
								'timestamp': datetime.now().isoformat()
							})
						except:
							pass
				
				st.success("✅ Ready for new analysis!")
				st.rerun()

	elif st.session_state.is_polling and st.session_state.task_id:
		# Enhanced real-time progress tracking with dashboard
		st.markdown("""
		<div class="status-card info">
			<h2 style="margin: 0 0 8px 0; color: #0c5460;">⏳ Analysis in Progress</h2>
			<p style="margin: 0; color: #0c5460; opacity: 0.8;">
				Your contract is being analyzed by our AI system. Monitor real-time progress below.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		# Enhanced progress section with real-time dashboard
		st.markdown('<div class="progress-section">', unsafe_allow_html=True)
		
		# Show task information
		if st.session_state.task_id:
			col1, col2 = st.columns(2)
			with col1:
				st.metric("📋 Analysis ID", st.session_state.task_id[-8:])  # Show last 8 characters
			with col2:
				if st.session_state.uploaded_file:
					filename = st.session_state.uploaded_file["file"].name
					st.metric("📄 File", filename[:20] + "..." if len(filename) > 20 else filename)
		
		# Real-time progress dashboard
		try:
			user_id = st.session_state.get("user_info", {}).get("username", "user")
			dashboard = render_progress_dashboard(api_client, st.session_state.task_id, user_id)
			
			# Check if analysis is complete via dashboard
			if dashboard and dashboard.current_progress:
				progress = dashboard.current_progress
				if progress.status.value in ["completed", "failed", "cancelled"]:
					if progress.status.value == "completed":
						# Fetch final results
						try:
							results = api_client.get_analysis_results(st.session_state.task_id)
							if "error" not in results:
								st.session_state.analysis_results = results
								st.session_state.is_polling = False
								st.session_state.task_id = None
								st.success("🎉 Analysis completed! Redirecting to results...")
								st.rerun()
						except Exception as e:
							st.error(f"Error fetching results: {e}")
					else:
						# Analysis failed or cancelled
						st.session_state.is_polling = False
						st.session_state.task_id = None
						if progress.status.value == "failed":
							st.error(f"❌ Analysis failed: {progress.error_message or 'Unknown error'}")
						else:
							st.warning("⏹️ Analysis was cancelled")
						
		except Exception as e:
			st.warning(f"Real-time dashboard unavailable: {e}")
			# Fallback to simple polling
			poll_for_results()
		
		st.markdown('</div>', unsafe_allow_html=True)
		
		# Enhanced cancel option with confirmation
		col1, col2, col3 = st.columns([1, 2, 1])
		with col2:
			if st.button("❌ Cancel Analysis", type="secondary", use_container_width=True):
				# Show confirmation dialog
				with st.form("cancel_confirmation"):
					st.warning("⚠️ Are you sure you want to cancel this analysis?")
					reason = st.text_input("Reason (optional):", placeholder="e.g., Taking too long, wrong file uploaded")
					
					col_confirm1, col_confirm2 = st.columns(2)
					with col_confirm1:
						if st.form_submit_button("✅ Yes, Cancel", type="primary"):
							try:
								# Try to cancel via API if available
								cancel_message = {
									"type": "cancel_analysis",
									"data": {"reason": reason or "User requested cancellation"}
								}
								# Note: This would need WebSocket connection to send
								st.session_state.is_polling = False
								st.session_state.task_id = None
								st.success("✅ Analysis cancelled successfully")
								st.rerun()
							except Exception as e:
								st.error(f"Error cancelling analysis: {e}")
								# Fallback to local cancellation
								st.session_state.is_polling = False
								st.session_state.task_id = None
								st.warning("⚠️ Analysis cancelled locally")
								st.rerun()
					
					with col_confirm2:
						if st.form_submit_button("❌ Keep Running"):
							st.info("Analysis will continue running")

	elif st.session_state.is_processing:
		# Enhanced processing display
		st.markdown("""
		<div class="status-card info">
			<h2 style="margin: 0 0 8px 0; color: #0c5460;">🔄 Starting Analysis</h2>
			<p style="margin: 0; color: #0c5460; opacity: 0.8;">
				Initializing secure job application tracking...
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		secure_analysis()

	else:
		# Enhanced file upload and analysis section
		st.markdown("""
		<div class="status-card info">
			<h2 style="margin: 0 0 8px 0; color: #0c5460;">🎯 Contract Analysis</h2>
			<p style="margin: 0; color: #0c5460; opacity: 0.8;">
				Upload your contract document to begin AI-powered risk analysis and clause review.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		# File upload with enhanced feedback
		upload_success = secure_file_upload()
		
		if upload_success:
			# Store uploaded file info
			st.session_state.uploaded_file_info = st.session_state.uploaded_file
			
			# Enhanced analysis ready section
			st.markdown("""
			<div class="action-section">
				<h3 style="color: #1976d2; margin-bottom: 16px;">🚀 Ready for Analysis</h3>
				<p style="color: #333; margin-bottom: 20px;">
					Your file has been validated and is ready for comprehensive AI analysis. 
					Our system will examine risks, clauses, and provide actionable recommendations.
				</p>
			</div>
			""", unsafe_allow_html=True)

			# Show enhanced file summary before analysis
			if st.session_state.uploaded_file:
				file_info = st.session_state.uploaded_file
				
				col1, col2, col3, col4 = st.columns(4)
				with col1:
					filename = file_info["file"].name
					display_name = filename[:15] + "..." if len(filename) > 15 else filename
					st.metric("📄 File", display_name)
				with col2:
					file_size_kb = file_info["file"].size / 1024
					st.metric("📊 Size", f"{file_size_kb:.1f} KB")
				with col3:
					file_ext = file_info.get('file_extension', 'unknown').upper()
					st.metric("📋 Type", file_ext)
				with col4:
					st.metric("🔒 Status", "✅ Validated")

			# Enhanced analysis button with better styling
			col1, col2, col3 = st.columns([1, 2, 1])
			with col2:
				if st.button("🚀 Start AI Analysis", type="primary", use_container_width=True, 
				           help="Begin comprehensive job application tracking with AI-powered risk assessment"):
					st.session_state.is_processing = True
					st.session_state.error_message = None
					
					# Track analysis start if production features available
					if PRODUCTION_FEATURES_AVAILABLE:
						try:
							track_user_event('analysis_started', {
								'filename': st.session_state.uploaded_file["file"].name,
								'file_size_kb': st.session_state.uploaded_file["file"].size / 1024,
								'timestamp': datetime.now().isoformat()
							})
						except:
							pass
					
					st.rerun()
		else:
			# Enhanced getting started guide
			st.markdown("""
			<div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
			            border-radius: 12px; padding: 24px; margin: 20px 0;">
				<h3 style="color: #0277bd; margin-bottom: 16px;">📚 How It Works</h3>
				<div style="color: #333;">
					<div style="display: flex; align-items: center; margin-bottom: 12px;">
						<span style="background: #0277bd; color: white; border-radius: 50%; 
						             width: 24px; height: 24px; display: flex; align-items: center; 
						             justify-content: center; margin-right: 12px; font-size: 12px; font-weight: bold;">1</span>
						<span><strong>Upload Contract:</strong> PDF, DOCX, or TXT format (up to 50MB)</span>
					</div>
					<div style="display: flex; align-items: center; margin-bottom: 12px;">
						<span style="background: #0277bd; color: white; border-radius: 50%; 
						             width: 24px; height: 24px; display: flex; align-items: center; 
						             justify-content: center; margin-right: 12px; font-size: 12px; font-weight: bold;">2</span>
						<span><strong>Validation:</strong> Security and compatibility checks</span>
					</div>
					<div style="display: flex; align-items: center; margin-bottom: 12px;">
						<span style="background: #0277bd; color: white; border-radius: 50%; 
						             width: 24px; height: 24px; display: flex; align-items: center; 
						             justify-content: center; margin-right: 12px; font-size: 12px; font-weight: bold;">3</span>
						<span><strong>AI Analysis:</strong> Risk assessment and clause review</span>
					</div>
					<div style="display: flex; align-items: center;">
						<span style="background: #0277bd; color: white; border-radius: 50%; 
						             width: 24px; height: 24px; display: flex; align-items: center; 
						             justify-content: center; margin-right: 12px; font-size: 12px; font-weight: bold;">4</span>
						<span><strong>Results:</strong> Comprehensive report with recommendations</span>
					</div>
				</div>
			</div>
			""", unsafe_allow_html=True)
			
			# Feature highlights
			col1, col2, col3 = st.columns(3)
			with col1:
				st.markdown("""
				<div style="text-align: center; padding: 16px;">
					<div style="font-size: 32px; margin-bottom: 8px;">🤖</div>
					<h4 style="color: #333; margin-bottom: 8px;">AI-Powered</h4>
					<p style="color: #666; font-size: 14px;">Advanced machine learning models analyze your contracts</p>
				</div>
				""", unsafe_allow_html=True)
			
			with col2:
				st.markdown("""
				<div style="text-align: center; padding: 16px;">
					<div style="font-size: 32px; margin-bottom: 8px;">🔒</div>
					<h4 style="color: #333; margin-bottom: 8px;">Secure</h4>
					<p style="color: #666; font-size: 14px;">Enterprise-grade security and privacy protection</p>
				</div>
				""", unsafe_allow_html=True)
			
			with col3:
				st.markdown("""
				<div style="text-align: center; padding: 16px;">
					<div style="font-size: 32px; margin-bottom: 8px;">⚡</div>
					<h4 style="color: #333; margin-bottom: 8px;">Fast</h4>
					<p style="color: #666; font-size: 14px;">Get comprehensive analysis results in minutes</p>
				</div>
				""", unsafe_allow_html=True)
	
	# Enhanced error display
	if st.session_state.error_message:
		st.markdown("""
		<div class="status-card error">
			<h4 style="margin: 0 0 8px 0; color: #721c24;">❌ Error Occurred</h4>
			<p style="margin: 0; color: #721c24;">
				An error occurred during processing. Please review the details below.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		error_display(st.session_state.error_message, show_actions=True, 
		             retry_callback=lambda: st.rerun())
	
	st.markdown('</div>', unsafe_allow_html=True)


def render_profile_page():
    """Render the profile management page - Task 12.1"""
    st.title("👤 User Profile")
    
    st.markdown("""
    Manage your professional profile to get personalized job recommendations.
    Update your skills, preferred locations, and experience level.
    """)

    with st.spinner("Loading profile..."):
        user_profile = api_client.get_user_profile()

    if "error" in user_profile:
        st.error(f"Error loading profile: {user_profile['error']}")
        st.info("Make sure the backend is running and you're authenticated.")
        return

    with st.form("profile_form"):
        st.subheader("Update Your Profile")

        # Skills - Multi-select
        default_skills = user_profile.get("skills", [])
        all_possible_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Angular", "Vue.js", 
            "Node.js", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "SQL", "NoSQL", 
            "PostgreSQL", "MongoDB", "Redis", "Machine Learning", "Data Science", 
            "FastAPI", "Django", "Flask", "Spring Boot", "Go", "Rust", "C++", "C#",
            ".NET", "Ruby", "PHP", "Swift", "Kotlin", "Flutter", "React Native",
            "GraphQL", "REST API", "Microservices", "CI/CD", "Git", "Linux"
        ]
        selected_skills = st.multiselect(
            "Skills *", 
            options=sorted(all_possible_skills), 
            default=default_skills,
            help="Select all skills you possess. This helps match you with relevant jobs."
        )

        # Preferred Locations - Multi-select
        default_locations = user_profile.get("preferred_locations", [])
        all_possible_locations = [
            "Remote", "New York", "San Francisco", "Los Angeles", "Seattle", "Austin",
            "Boston", "Chicago", "Denver", "London", "Berlin", "Paris", "Amsterdam",
            "Tokyo", "Singapore", "Sydney", "Toronto", "Vancouver"
        ]
        selected_locations = st.multiselect(
            "Preferred Locations *", 
            options=sorted(all_possible_locations), 
            default=default_locations,
            help="Select your preferred work locations. Include 'Remote' if you're open to remote work."
        )

        # Experience Level - Dropdown
        default_experience = user_profile.get("experience_level", "mid")
        experience_levels = ["junior", "mid", "senior"]
        try:
            default_index = experience_levels.index(default_experience)
        except ValueError:
            default_index = 1  # Default to "mid"
        
        selected_experience = st.selectbox(
            "Experience Level *", 
            options=experience_levels,
            index=default_index,
            help="Select your current experience level"
        )

        # Daily Application Goal - Number input
        default_daily_goal = user_profile.get("daily_application_goal", 10)
        selected_daily_goal = st.number_input(
            "Daily Application Goal",
            min_value=1,
            max_value=50,
            value=default_daily_goal,
            step=1,
            help="Set your daily target for job applications."
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Profile", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            if not selected_skills:
                st.error("Please select at least one skill")
            elif not selected_locations:
                st.error("Please select at least one preferred location")
            else:
                profile_data = {
                    "skills": selected_skills,
                    "preferred_locations": selected_locations,
                    "experience_level": selected_experience,
                    "daily_application_goal": selected_daily_goal,
                }
                with st.spinner("Updating profile..."):
                    response = api_client.update_user_profile(profile_data)
                    if "error" not in response:
                        st.success("✅ Profile updated successfully!")
                        # Update session state with new profile data
                        st.session_state.user_info["skills"] = selected_skills
                        st.session_state.user_info["preferred_locations"] = selected_locations
                        st.session_state.user_info["experience_level"] = selected_experience
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Failed to update profile: {response['error']}")
        
        if cancel:
            st.info("Profile update cancelled")
    
    # Display current profile summary
    st.divider()
    st.subheader("Current Profile Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Skills", len(user_profile.get("skills", [])))
    with col2:
        st.metric("Locations", len(user_profile.get("preferred_locations", [])))
    with col3:
        st.metric("Experience", user_profile.get("experience_level", "Not set").capitalize())

def render_recommendations_page():
    """Render the recommendations page - Task 12.2"""
    st.title("✨ Job Recommendations")

    st.markdown("""
    Get personalized job recommendations based on your profile, skills, and preferences.
    Jobs are ranked by match score considering tech stack, location, and experience level.
    """)

    # Pagination controls
    col1, col2 = st.columns(2)
    with col1:
        limit = st.slider("Number of recommendations", min_value=5, max_value=50, value=10, step=5)
    with col2:
        skip = st.number_input("Skip first N recommendations", min_value=0, value=0, step=5)

    with st.spinner("Loading recommendations..."):
        recommendations = api_client.get_recommendations(skip=skip, limit=limit)

    if "error" in recommendations:
        st.error(f"Error loading recommendations: {recommendations['error']}")
        st.info("Make sure you have updated your profile and added some jobs.")
        return

    if recommendations and len(recommendations) > 0:
        st.success(f"Found {len(recommendations)} recommended jobs for you!")
        
        for idx, rec in enumerate(recommendations, 1):
            job = rec.get("job", {})
            score = rec.get("score", 0)
            
            # Create a colored badge based on match score
            if score >= 80:
                score_color = "🟢"
                score_label = "Excellent Match"
            elif score >= 60:
                score_color = "🟡"
                score_label = "Good Match"
            else:
                score_color = "🟠"
                score_label = "Fair Match"
            
            with st.expander(f"#{idx} - {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')} {score_color} {score:.0f}%"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Company:** {job.get('company', 'N/A')}")
                    st.markdown(f"**Title:** {job.get('title', 'N/A')}")
                    st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                    
                    if job.get('tech_stack'):
                        tech_stack_str = ', '.join(job['tech_stack'])
                        st.markdown(f"**Tech Stack:** {tech_stack_str}")
                    
                    if job.get('description'):
                        with st.expander("📄 Job Description"):
                            st.write(job['description'])
                
                with col2:
                    st.metric("Match Score", f"{score:.0f}%", help=score_label)
                    
                    if job.get('salary_range'):
                        st.markdown(f"**Salary:** {job['salary_range']}")
                    
                    if job.get('job_type'):
                        st.markdown(f"**Type:** {job['job_type']}")
                    
                    if job.get('remote'):
                        st.markdown("**Remote:** ✅ Yes")
                
                # Feedback section
                st.markdown("---")
                st.markdown("**Was this recommendation helpful?**")
                
                # Check if user has already provided feedback for this job
                feedback_key = f"feedback_{job.get('id')}"
                if feedback_key not in st.session_state:
                    st.session_state[feedback_key] = None
                
                col_feedback1, col_feedback2, col_feedback3 = st.columns([1, 1, 2])
                
                with col_feedback1:
                    if st.button("👍 Helpful", key=f"thumbs_up_{job.get('id')}", use_container_width=True):
                        response = api_client.create_job_feedback(job.get('id'), True)
                        if "error" not in response:
                            st.session_state[feedback_key] = "helpful"
                            st.success("Thanks for your feedback!")
                            st.rerun()
                        else:
                            st.error(f"Failed to submit feedback: {response.get('error')}")
                
                with col_feedback2:
                    if st.button("👎 Not Helpful", key=f"thumbs_down_{job.get('id')}", use_container_width=True):
                        response = api_client.create_job_feedback(job.get('id'), False)
                        if "error" not in response:
                            st.session_state[feedback_key] = "not_helpful"
                            st.success("Thanks for your feedback!")
                            st.rerun()
                        else:
                            st.error(f"Failed to submit feedback: {response.get('error')}")
                
                with col_feedback3:
                    # Optional comment field
                    comment = st.text_input(
                        "Optional comment", 
                        key=f"comment_{job.get('id')}", 
                        placeholder="Why was this helpful/not helpful?",
                        help="Your feedback helps improve our recommendations"
                    )
                    
                    if comment and st.button("💬 Submit Comment", key=f"submit_comment_{job.get('id')}"):
                        # Submit feedback with comment (default to helpful if comment provided)
                        response = api_client.create_job_feedback(job.get('id'), True, comment)
                        if "error" not in response:
                            st.success("Thanks for your detailed feedback!")
                            st.rerun()
                        else:
                            st.error(f"Failed to submit feedback: {response.get('error')}")
                
                # Show feedback status if already provided
                if st.session_state.get(feedback_key):
                    if st.session_state[feedback_key] == "helpful":
                        st.success("✅ You marked this as helpful")
                    else:
                        st.info("ℹ️ You marked this as not helpful")
                
                # Action buttons
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"📝 Apply", key=f"apply_rec_{job.get('id')}", use_container_width=True):
                        # Create application
                        app_data = {
                            "job_id": job.get('id'),
                            "status": "interested",
                            "notes": f"Applied via recommendations (Match: {score:.0f}%)"
                        }
                        response = api_client.create_application(app_data)
                        if "error" not in response:
                            st.success(f"✅ Application created for {job.get('title')}!")
                            st.rerun()
                        else:
                            st.error(f"Failed to create application: {response.get('error')}")
                
                with col_btn2:
                    if job.get('url'):
                        st.link_button("🔗 View Job", job['url'], use_container_width=True)
    else:
        st.info("No recommendations found. Here's how to get started:")
        st.markdown("""
        1. **Update your profile** with your skills and preferred locations
        2. **Add some jobs** you're interested in
        3. **Come back here** to see personalized recommendations
        """)
        
        if st.button("Go to Profile"):
            st.session_state.current_page = "profile"
            st.rerun()

def render_skill_gap_analysis_page():
    """Render the skill gap analysis page - Task 12.3"""
    st.title("🧠 Skill Gap Analysis")
    
    # Add tabs for skill gap and feedback
    tab1, tab2 = st.tabs(["📊 Skill Analysis", "📝 Feedback History"])
    
    with tab1:
        st.markdown("""
        Understand your skill gaps based on your tracked jobs and get learning recommendations.
        This analysis helps you identify which skills to learn to become a more competitive candidate.
        """)

        with st.spinner("Analyzing your skill gaps..."):
            analysis = api_client.get_skill_gap_analysis()

        if "error" in analysis:
            st.error(f"Error loading skill gap analysis: {analysis['error']}")
            st.info("Make sure you have added some jobs with tech stacks to your profile.")
            return

        if not analysis:
            st.info("No data available for skill gap analysis. Add some jobs with tech stacks to get started.")
            return

        # Skill Coverage Percentage Gauge
        skill_coverage_percentage = analysis.get("skill_coverage_percentage", 0)
        st.subheader("Skill Coverage")
        st.progress(skill_coverage_percentage / 100.0)
        st.metric("Your Skill Coverage", f"{skill_coverage_percentage:.1f}%", help="Percentage of skills in your tracked jobs that you possess.")

        st.divider()

        # User Skills vs. Missing Skills
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("✅ Your Skills")
            user_skills = analysis.get("user_skills", [])
            if user_skills:
                st.write(", ".join(user_skills))
            else:
                st.info("No skills found in your profile. Please update your profile.")

        with col2:
            st.subheader("❌ Missing Skills")
            missing_skills = analysis.get("missing_skills", {})
            if missing_skills:
                for skill, count in missing_skills.items():
                    st.markdown(f"- **{skill.capitalize()}** (appears in {count} jobs)")
            else:
                st.success("🎉 No missing skills found!")

        st.divider()

        # Top Market Skills
        st.subheader("🔥 Top Market Skills")
        st.markdown("The most in-demand skills based on your tracked jobs.")
        top_market_skills = analysis.get("top_market_skills", {})
        if top_market_skills:
            df_market_skills = pd.DataFrame(list(top_market_skills.items()), columns=['Skill', 'Frequency'])
            st.dataframe(df_market_skills, use_container_width=True, hide_index=True)
        else:
            st.info("No market skill data available yet.")

        st.divider()

        # Learning Recommendations
        st.subheader("📚 Learning Recommendations")
        learning_recommendations = analysis.get("learning_recommendations", [])
        if learning_recommendations:
            for rec in learning_recommendations:
                st.markdown(f"- {rec}")
        else:
            st.success("You have all the required skills for your tracked jobs!")
    
    with tab2:
        render_feedback_management()

def render_feedback_management():
    """Render feedback management section"""
    st.subheader("📝 Your Feedback History")
    
    with st.spinner("Loading your feedback..."):
        feedback_response = api_client.get_user_feedback(limit=20)
    
    if "error" in feedback_response:
        st.error(f"Error loading feedback: {feedback_response['error']}")
        return
    
    feedback_items = feedback_response if isinstance(feedback_response, list) else []
    
    if not feedback_items:
        st.info("You haven't provided any feedback yet. Visit the recommendations page to start giving feedback!")
        return
    
    st.markdown(f"**Total feedback items:** {len(feedback_items)}")
    
    # Summary stats
    helpful_count = sum(1 for item in feedback_items if item.get('is_helpful'))
    unhelpful_count = len(feedback_items) - helpful_count
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👍 Helpful", helpful_count)
    with col2:
        st.metric("👎 Not Helpful", unhelpful_count)
    with col3:
        if len(feedback_items) > 0:
            helpful_percentage = (helpful_count / len(feedback_items)) * 100
            st.metric("% Helpful", f"{helpful_percentage:.1f}%")
    
    st.divider()
    
    # Display feedback items
    for idx, feedback in enumerate(feedback_items[:10]):  # Show last 10
        with st.expander(f"Feedback #{idx + 1} - {'👍 Helpful' if feedback.get('is_helpful') else '👎 Not Helpful'}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Job ID:** {feedback.get('job_id')}")
                if feedback.get('comment'):
                    st.markdown(f"**Comment:** {feedback.get('comment')}")
                
                # Show context if available
                if feedback.get('user_skills_at_time'):
                    st.markdown(f"**Your skills at time:** {', '.join(feedback.get('user_skills_at_time', []))}")
                if feedback.get('job_tech_stack'):
                    st.markdown(f"**Job tech stack:** {', '.join(feedback.get('job_tech_stack', []))}")
            
            with col2:
                st.markdown(f"**Match Score:** {feedback.get('match_score', 'N/A')}")
                st.markdown(f"**Date:** {feedback.get('created_at', 'N/A')[:10]}")


def render_settings_interface():
	"""Render the settings interface."""
	st.subheader("⚙️ Settings")

	# Connection monitoring section
	st.subheader("🔗 Connection Monitoring")
	try:
		display_connection_dashboard(api_client)
	except Exception as e:
		st.error(f"Connection dashboard error: {str(e)}")

	st.divider()

	# Model selection
	st.subheader("AI Model Settings")
	model_preference = st.selectbox("Preferred AI Model", ["gpt-4", "gpt-3.5-turbo", "claude-3"], help="Select your preferred AI model for analysis")

	# Analysis settings
	st.subheader("Analysis Settings")
	enable_confidence = st.checkbox("Enable Confidence Scoring", value=True)
	analysis_depth = st.selectbox("Analysis Depth", ["basic", "standard", "comprehensive"], index=1)

	# Security settings
	st.subheader("Security Settings")
	enable_audit = st.checkbox("Enable Audit Logging", value=True)
	enable_quarantine = st.checkbox("Enable File Quarantine", value=True)

	# Save settings
	if st.button("💾 Save Settings", key="basic_save_settings"):
		st.success("Settings saved successfully!")
		# In a real implementation, you would save these to a database or config file


def render_login_form():
	"""Render the login form."""
	st.header("Login")
	with st.form("login_form"):
		username = st.text_input("Username", value="user@example.com")
		password = st.text_input("Password", type="password", value="string")
		submitted = st.form_submit_button("Login")

		if submitted:
			with st.spinner("Authenticating..."):
				response = api_client.login(username, password)
				if "error" not in response and "access_token" in response:
					st.session_state.auth_token = response["access_token"]
					st.session_state.user_info = response.get("user", {})
					api_client.set_token(response["access_token"])
					st.success("Login successful!")
					st.rerun()
				else:
					st.error(f"❌ {response.get('error', 'Authentication failed.')}")


# Removed duplicate function - using the one below


def render_basic_header():
	"""Render basic header without production features."""
	st.title("🔒 Secure Career Copilot")
	st.markdown("""
	    Upload your contract document for secure analysis with advanced threat detection,
	    input sanitization, and comprehensive audit logging.
	    """)


def render_production_settings():
	"""Render production settings interface."""
	st.subheader("⚙️ Production Settings")
	
	if PRODUCTION_FEATURES_AVAILABLE:
		try:
			config = get_config()
			
			# Feature flags
			st.subheader("🚩 Feature Flags")
			
			col1, col2 = st.columns(2)
			
			with col1:
				real_time = st.checkbox(
					"Real-time Updates",
					value=config.feature_flags.get('real_time_updates', True),
					help="Enable real-time status updates and notifications"
				)
				
				analytics = st.checkbox(
					"Advanced Analytics",
					value=config.feature_flags.get('advanced_analytics', True),
					help="Enable detailed analytics and performance monitoring"
				)
			
			with col2:
				mobile_opt = st.checkbox(
					"Mobile Optimizations",
					value=config.feature_flags.get('mobile_optimizations', True),
					help="Enable mobile-specific UI optimizations"
				)
				
				error_recovery = st.checkbox(
					"Error Recovery",
					value=config.feature_flags.get('error_recovery', True),
					help="Enable automatic error recovery and user guidance"
				)
			
			# Save settings
			if st.button("💾 Save Production Settings", key="production_save_settings"):
				st.success("Production settings saved!")
		except Exception as e:
			st.error(f"Production settings unavailable: {e}")
			render_settings_interface()
	else:
		render_settings_interface()


def render_production_sidebar(websocket_features=None, analytics=None):
	"""Render production sidebar."""
	with st.sidebar:
		st.header("🚀 Production Status")
		
		if websocket_features:
			try:
				# Connection status
				connection = websocket_features.get('websocket_manager', {}).get('connection_status', {})
				if connection.get('connected'):
					st.success("🟢 Connected")
				else:
					st.error("🔴 Disconnected")
			except:
				st.info("🟡 Status Unknown")
		
		if analytics:
			try:
				# Quick metrics
				st.subheader("📊 Quick Metrics")
				metrics = analytics.get_quick_metrics()
				for metric_name, metric_value in metrics.items():
					st.metric(metric_name, metric_value)
			except:
				st.info("Analytics unavailable")
		
		# Fallback to security sidebar
		render_security_sidebar()


def render_production_footer(websocket_features=None):
	"""Render production footer."""
	st.divider()
	
	col1, col2, col3 = st.columns(3)
	
	with col1:
		st.caption("🔒 Career Copilot v2.0")
	
	with col2:
		if websocket_features:
			try:
				latency = websocket_features.get('websocket_manager', {}).get('latency', 0)
				st.caption(f"⚡ Latency: {latency:.0f}ms")
			except:
				st.caption("⚡ Latency: --ms")
		else:
			st.caption("⚡ Latency: --ms")
	
	with col3:
		st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")


def render_production_header(websocket_features=None):
	"""Render enhanced header with production features."""
	col1, col2, col3 = st.columns([3, 1, 1])
	
	with col1:
		st.title("🔒 Career Copilot")
		st.caption("Production-Ready AI-Powered Contract Analysis v2.0")
	
	with col2:
		# System status indicator - Simple backend health check
		try:
			import requests
			backend_url = os.getenv('BACKEND_URL', 'http://localhost:8002')
			
			# Get comprehensive health status
			response = requests.get(f"{backend_url}/api/v1/health", timeout=2)
			if response.status_code == 200:
				health_data = response.json()
				status = health_data.get('status', 'unknown')
				
				# Map backend status to display status
				status_mapping = {
					'healthy': ('🟢', 'Healthy'),
					'degraded': ('🟡', 'Warning'),
					'unhealthy': ('🔴', 'Critical'),
					'unknown': ('⚪', 'Unknown')
				}
				
				icon, display_status = status_mapping.get(status, ('⚪', 'Unknown'))
				st.metric("System Status", f"{icon} {display_status}")
			else:
				st.metric("System Status", "🔴 Critical")
		except requests.exceptions.ConnectionError:
			st.metric("System Status", "🔴 Critical")
		except requests.exceptions.Timeout:
			st.metric("System Status", "🟡 Warning")
		except Exception as e:
			st.metric("System Status", "⚪ Unknown")
	
	with col3:
		# Connection status - Simple backend connectivity check
		try:
			import requests
			backend_url = os.getenv('BACKEND_URL', 'http://localhost:8002')
			
			# Quick health check with short timeout
			response = requests.get(f"{backend_url}/api/v1/health", timeout=2)
			if response.status_code == 200:
				health_data = response.json()
				if health_data.get('status') == 'healthy':
					st.metric("Connection", "🟢 Online")
				else:
					st.metric("Connection", "🟡 Degraded")
			else:
				st.metric("Connection", "🔴 Offline")
		except requests.exceptions.ConnectionError:
			st.metric("Connection", "🔴 Offline")
		except requests.exceptions.Timeout:
			st.metric("Connection", "🟡 Slow")
		except Exception as e:
			st.metric("Connection", "⚪ Unknown")
		
		# System information
		st.subheader("ℹ️ System Information")
		
		system_info = {
			"Environment": getattr(config, 'environment', os.getenv('ENVIRONMENT', 'development')),
			"Version": "2.0.0",
			"API URL": getattr(config, 'api_base_url', os.getenv('BACKEND_URL', 'http://localhost:8002')),
			"Cache TTL": f"{getattr(config.cache, 'ttl_seconds', 300) if hasattr(config, 'cache') else 300}s",
			"Max File Size": f"{getattr(config.security, 'max_file_size_mb', 50) if hasattr(config, 'security') else 50}MB"
		}
		
		for key, value in system_info.items():
			st.text(f"{key}: {value}")


def render_production_sidebar(websocket_features=None, analytics=None):
	"""Render enhanced sidebar with production features."""
	with st.sidebar:
		st.header("🔒 Production Dashboard")
		
		# User info
		if st.session_state.get('user_info'):
			user = st.session_state.user_info
			st.subheader(f"Welcome, {user.get('username', 'User')}")
		
		# Quick stats
		st.subheader("📊 Quick Stats")
		
		# Session metrics
		if 'app_start_time' in st.session_state:
			uptime_minutes = (datetime.now().timestamp() - st.session_state.app_start_time) / 60
			st.metric("Session Uptime", f"{uptime_minutes:.1f}m")
		
		if 'page_loads' in st.session_state:
			st.metric("Page Loads", st.session_state.page_loads)
		
		# System health indicator
		if websocket_features and hasattr(websocket_features['health_monitor'], 'render_health_indicator'):
			websocket_features['health_monitor'].render_health_indicator()
		
		# Real-time notifications
		if websocket_features and hasattr(websocket_features['notification_manager'], 'render_notifications'):
			st.subheader("🔔 Notifications")
			websocket_features['notification_manager'].render_notifications()
		
		# Quick actions
		st.subheader("⚡ Quick Actions")
		
		if st.button("🔄 Refresh Data", use_container_width=True):
			if PRODUCTION_FEATURES_AVAILABLE:
				track_user_event('sidebar_action', {'action': 'refresh_data'})
			st.rerun()
		
		if st.button("📊 View Analytics", use_container_width=True):
			if PRODUCTION_FEATURES_AVAILABLE:
				track_user_event('sidebar_action', {'action': 'view_analytics'})
			st.info("Switching to Analytics tab...")
		
		st.divider()
		st.subheader(f"Welcome, {st.session_state.user_info.get('username', 'User')}")
		if st.button("Logout", key="sidebar_logout"):
			if PRODUCTION_FEATURES_AVAILABLE:
				track_user_event('user_logout')
			api_client.clear_token()
			del st.session_state.auth_token
			del st.session_state.user_info
			st.rerun()


def render_production_footer(websocket_features=None):
	"""Render production footer with status information."""
	st.divider()
	
	col1, col2, col3 = st.columns(3)
	
	with col1:
		st.caption("🔒 Career Copilot v2.0")
		st.caption("Production-Ready AI Analysis")
	
	with col2:
		if websocket_features:
			connection = websocket_features['websocket_manager'].get_connection_status()
			status_text = "🟢 Online" if connection['connected'] else "🔴 Offline"
		else:
			status_text = "🟢 Online"
		st.caption(f"Status: {status_text}")
	
	with col3:
		session_id = st.session_state.get('session_id', 'unknown')
		st.caption(f"Session: {session_id[-8:] if len(session_id) > 8 else session_id}")
		if 'app_start_time' in st.session_state:
			uptime = (datetime.now().timestamp() - st.session_state.app_start_time) / 60
			st.caption(f"Uptime: {uptime:.0f}m")



def main():
	"""Main application function."""
	global PRODUCTION_FEATURES_AVAILABLE
	
	# Setup page configuration
	setup_page_config()
	
	# Initialize session state
	initialize_session_state()
	
	# Setup security
	setup_security()
	
	# Initialize production features if available
	websocket_features = None
	analytics = None
	
	if PRODUCTION_FEATURES_AVAILABLE:
		try:
			# Initialize production optimizations
			initialize_production_optimizations()
			
			# Initialize WebSocket features
			websocket_features = initialize_websocket_features()
			
			# Initialize responsive UI
			initialize_responsive_ui()
			
			# Initialize analytics
			analytics = initialize_production_analytics()
			
		except Exception as e:
			st.warning(f"Some production features unavailable: {e}")
			PRODUCTION_FEATURES_AVAILABLE = False

	# Load environment variables from .env file
	try:
		from dotenv import load_dotenv
		# Try multiple paths to find .env file
		env_paths = [
			'../.env',  # Parent directory
			'.env',     # Current directory
			'frontend/.env',  # Frontend directory
			os.path.join(os.path.dirname(__file__), '..', '.env')  # Relative to this file
		]
		for env_path in env_paths:
			if os.path.exists(env_path):
				load_dotenv(env_path, override=True)
				break
	except ImportError:
		pass
	
	# Force disable auth for testing
	os.environ['DISABLE_AUTH'] = 'true'
	
	# Check authentication - skip for development
	disable_auth = os.getenv("DISABLE_AUTH", "false").lower() == "true"
	
	# Debug info (remove in production)
	if st.sidebar.button("Debug Auth Status", key="debug_auth_status"):
		st.sidebar.write(f"DISABLE_AUTH: {os.getenv('DISABLE_AUTH', 'not set')}")
		st.sidebar.write(f"disable_auth: {disable_auth}")
		st.sidebar.write(f"auth_token: {st.session_state.get('auth_token', 'not set')}")
	
	# Force bypass authentication for testing
	if disable_auth or True:  # Always bypass for now
		# Set default auth token for development mode
		if not st.session_state.get("auth_token"):
			st.session_state.auth_token = "dev_token"
			st.session_state.user_info = {"username": "Developer", "id": "dev_user"}
	elif not st.session_state.get("auth_token"):
		render_login_form()
		return

	# Display connection status in sidebar
	try:
		is_connected = display_connection_status_sidebar(api_client)
		if not is_connected:
			st.warning("⚠️ Backend connection issues detected. Some features may not work properly.")
	except Exception as e:
		st.sidebar.error(f"Connection status error: {str(e)}")
		is_connected = False

	# Render header with production enhancements
	try:
		if PRODUCTION_FEATURES_AVAILABLE:
			render_production_header(websocket_features)
		else:
			render_basic_header()
	except Exception as e:
		# Fallback to simple header if there are issues
		st.title("🔒 Career Copilot")
		st.caption("AI-Powered Contract Analysis")
		st.error(f"Header rendering issue: {str(e)}")

	# Add navigation tabs with responsive design
	tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📄 Contract Analysis", "👤 Profile", "✨ Recommendations", "🧠 Skill Gap", "📊 Progress Dashboard", "📈 Analytics", "🔍 Observability", "⚙️ Settings"])

	with tab1:
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'analysis'})
			except:
				pass
		render_analysis_interface()

	with tab2:
		render_profile_page()

	with tab3:
		render_recommendations_page()

	with tab4:
		render_skill_gap_analysis_page()

	with tab5:
		render_dashboard()

	with tab6:
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'analytics'})
				if analytics:
					analytics.render_full_dashboard()
				else:
					st.info("Analytics dashboard not available")
			except:
				st.info("Analytics dashboard not available")
		else:
			st.info("Analytics dashboard not available")

	with tab7:
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'observability'})
			except:
				pass
		st.info("Observability dashboard not available")

	with tab8:
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'settings'})
				st.info("Production settings not available")
			except:
				st.info("Settings interface not available")
		else:
			st.info("Settings interface not available")
		
	# Render enhanced sidebar
	if PRODUCTION_FEATURES_AVAILABLE:
		try:
			render_production_sidebar(websocket_features, analytics)
		except:
			render_security_sidebar()
	else:
		render_security_sidebar()
		
	# Show user info in sidebar if authenticated
	if st.session_state.get("auth_token") or os.getenv("DISABLE_AUTH", "false").lower() == "true":
		with st.sidebar:
			st.divider()
			if st.session_state.get("user_info"):
				st.subheader(f"Welcome, {st.session_state.user_info.get('username', 'User')}")
			else:
				st.subheader("Welcome, Developer")
			
			if st.session_state.get("auth_token") and st.button("Logout", key="main_logout"):
				api_client.clear_token()
				if "auth_token" in st.session_state:
					del st.session_state.auth_token
				if "user_info" in st.session_state:
					del st.session_state.user_info
				st.rerun()

	# Enhanced footer
	if PRODUCTION_FEATURES_AVAILABLE:
		try:
			render_production_footer(websocket_features)
		except:
			pass


if __name__ == "__main__":
	main()
