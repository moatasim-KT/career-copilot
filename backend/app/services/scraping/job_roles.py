"""
EU Job Scraper Role Definitions
Defines specific job roles to search for with relevant keywords and filters
"""

from typing import ClassVar, Dict, List


class JobRoles:
	"""
	Defines job roles for targeted EU job searches
	Each role includes:
	- Title variations
	- Keywords for search
	- Required skills
	- Seniority levels
	"""

	# Role categories with search keywords
	ROLES: ClassVar[Dict[str, Dict[str, any]]] = {
		# DATA SCIENCE & ANALYTICS
		"data_scientist": {
			"titles": [
				"Data Scientist",
				"Machine Learning Engineer",
				"ML Engineer",
				"Applied Scientist",
				"Research Scientist",
			],
			"keywords": ["data science", "machine learning", "ML", "AI", "statistics", "python"],
			"skills": ["Python", "R", "SQL", "TensorFlow", "PyTorch", "Scikit-learn"],
			"levels": ["Junior", "Mid-level", "Senior", "Lead", "Principal"],
		},
		"data_analyst": {
			"titles": [
				"Data Analyst",
				"Business Intelligence Analyst",
				"Analytics Engineer",
				"BI Developer",
			],
			"keywords": ["data analysis", "business intelligence", "BI", "analytics", "SQL"],
			"skills": ["SQL", "Python", "Tableau", "Power BI", "Excel", "Data Visualization"],
			"levels": ["Junior", "Mid-level", "Senior"],
		},
		"data_engineer": {
			"titles": [
				"Data Engineer",
				"Big Data Engineer",
				"Data Platform Engineer",
				"ETL Developer",
			],
			"keywords": ["data engineering", "ETL", "big data", "data pipeline", "spark"],
			"skills": ["Python", "SQL", "Spark", "Airflow", "Kafka", "AWS", "GCP"],
			"levels": ["Junior", "Mid-level", "Senior", "Lead"],
		},
		# SOFTWARE ENGINEERING
		"backend_engineer": {
			"titles": [
				"Backend Engineer",
				"Backend Developer",
				"Server-Side Engineer",
				"API Developer",
			],
			"keywords": ["backend", "server-side", "API", "microservices", "REST"],
			"skills": ["Python", "Java", "Go", "Node.js", "PostgreSQL", "MongoDB", "Docker"],
			"levels": ["Junior", "Mid-level", "Senior", "Lead", "Staff"],
		},
		"frontend_engineer": {
			"titles": [
				"Frontend Engineer",
				"Frontend Developer",
				"UI Engineer",
				"React Developer",
			],
			"keywords": ["frontend", "react", "vue", "angular", "typescript", "javascript"],
			"skills": ["React", "TypeScript", "JavaScript", "CSS", "HTML", "Next.js"],
			"levels": ["Junior", "Mid-level", "Senior", "Lead"],
		},
		"fullstack_engineer": {
			"titles": [
				"Full Stack Engineer",
				"Full Stack Developer",
				"Fullstack Developer",
			],
			"keywords": ["full stack", "fullstack", "full-stack", "web development"],
			"skills": ["React", "Node.js", "Python", "TypeScript", "PostgreSQL", "AWS"],
			"levels": ["Mid-level", "Senior", "Lead"],
		},
		"mobile_engineer": {
			"titles": [
				"Mobile Engineer",
				"iOS Developer",
				"Android Developer",
				"React Native Developer",
			],
			"keywords": ["mobile", "iOS", "android", "react native", "flutter"],
			"skills": ["Swift", "Kotlin", "React Native", "Flutter", "Mobile Development"],
			"levels": ["Junior", "Mid-level", "Senior", "Lead"],
		},
		# AI & MACHINE LEARNING
		"ml_engineer": {
			"titles": [
				"Machine Learning Engineer",
				"ML Engineer",
				"AI Engineer",
				"Deep Learning Engineer",
			],
			"keywords": ["machine learning", "ML", "AI", "deep learning", "neural networks"],
			"skills": ["Python", "TensorFlow", "PyTorch", "Keras", "MLOps", "Cloud ML"],
			"levels": ["Mid-level", "Senior", "Lead", "Staff"],
		},
		"ai_researcher": {
			"titles": [
				"AI Researcher",
				"Research Scientist",
				"ML Researcher",
				"Applied Scientist",
			],
			"keywords": ["research", "AI", "machine learning", "NLP", "computer vision"],
			"skills": ["Python", "PyTorch", "TensorFlow", "Research", "Publications"],
			"levels": ["PhD", "Postdoc", "Senior", "Principal"],
		},
		"mlops_engineer": {
			"titles": [
				"MLOps Engineer",
				"ML Platform Engineer",
				"ML Infrastructure Engineer",
			],
			"keywords": ["MLOps", "ML infrastructure", "ML platform", "deployment"],
			"skills": ["Python", "Kubernetes", "Docker", "Kubeflow", "MLflow", "AWS/GCP"],
			"levels": ["Mid-level", "Senior", "Lead"],
		},
		# DEVOPS & INFRASTRUCTURE
		"devops_engineer": {
			"titles": [
				"DevOps Engineer",
				"Site Reliability Engineer",
				"SRE",
				"Platform Engineer",
			],
			"keywords": ["DevOps", "SRE", "infrastructure", "kubernetes", "docker"],
			"skills": ["Kubernetes", "Docker", "Terraform", "AWS/GCP", "CI/CD", "Python"],
			"levels": ["Junior", "Mid-level", "Senior", "Lead", "Staff"],
		},
		"cloud_engineer": {
			"titles": [
				"Cloud Engineer",
				"Cloud Architect",
				"AWS Engineer",
				"Azure Engineer",
			],
			"keywords": ["cloud", "AWS", "Azure", "GCP", "cloud architecture"],
			"skills": ["AWS", "Azure", "GCP", "Terraform", "CloudFormation", "Kubernetes"],
			"levels": ["Mid-level", "Senior", "Lead", "Architect"],
		},
		# PRODUCT & DESIGN
		"product_manager": {
			"titles": [
				"Product Manager",
				"Technical Product Manager",
				"Senior Product Manager",
			],
			"keywords": ["product management", "product strategy", "roadmap", "user research"],
			"skills": ["Product Strategy", "Agile", "Jira", "SQL", "Analytics"],
			"levels": ["Associate", "Mid-level", "Senior", "Lead", "Director"],
		},
		"product_designer": {
			"titles": [
				"Product Designer",
				"UX Designer",
				"UI/UX Designer",
				"Interaction Designer",
			],
			"keywords": ["product design", "UX", "UI", "user experience", "figma"],
			"skills": ["Figma", "Sketch", "Adobe XD", "User Research", "Prototyping"],
			"levels": ["Junior", "Mid-level", "Senior", "Lead"],
		},
		# SECURITY
		"security_engineer": {
			"titles": [
				"Security Engineer",
				"Cybersecurity Engineer",
				"InfoSec Engineer",
				"Application Security Engineer",
			],
			"keywords": ["security", "cybersecurity", "infosec", "penetration testing"],
			"skills": ["Security", "Penetration Testing", "SIEM", "Python", "Vulnerability Assessment"],
			"levels": ["Mid-level", "Senior", "Lead", "Principal"],
		},
		# QA & TESTING
		"qa_engineer": {
			"titles": [
				"QA Engineer",
				"Test Engineer",
				"SDET",
				"Automation Engineer",
			],
			"keywords": ["QA", "testing", "automation", "test automation", "selenium"],
			"skills": ["Selenium", "Python", "Java", "Test Automation", "CI/CD"],
			"levels": ["Junior", "Mid-level", "Senior", "Lead"],
		},
	}

	@classmethod
	def get_role_keywords(cls, role: str) -> List[str]:
		"""Get keywords for a specific role"""
		if role in cls.ROLES:
			return cls.ROLES[role]["keywords"]
		return []

	@classmethod
	def get_role_titles(cls, role: str) -> List[str]:
		"""Get title variations for a specific role"""
		if role in cls.ROLES:
			return cls.ROLES[role]["titles"]
		return []

	@classmethod
	def get_all_roles(cls) -> List[str]:
		"""Get list of all role categories"""
		return list(cls.ROLES.keys())

	@classmethod
	def get_search_query(cls, role: str, location: str = "") -> str:
		"""Generate optimized search query for a role"""
		if role not in cls.ROLES:
			return role

		# Use the most common title variation
		title = cls.ROLES[role]["titles"][0]

		if location:
			return f"{title} {location}"
		return title

	@classmethod
	def matches_role(cls, job_title: str, role: str) -> bool:
		"""Check if a job title matches a role category"""
		if role not in cls.ROLES:
			return False

		job_title_lower = job_title.lower()

		# Check title variations
		for title in cls.ROLES[role]["titles"]:
			if title.lower() in job_title_lower:
				return True

		# Check keywords
		for keyword in cls.ROLES[role]["keywords"]:
			if keyword.lower() in job_title_lower:
				return True

		return False


# Predefined role combinations for common searches
ROLE_COMBOS = {
	"data_roles": ["data_scientist", "data_analyst", "data_engineer", "ml_engineer"],
	"engineering_roles": ["backend_engineer", "frontend_engineer", "fullstack_engineer", "mobile_engineer"],
	"ai_ml_roles": ["ml_engineer", "ai_researcher", "data_scientist", "mlops_engineer"],
	"infrastructure_roles": ["devops_engineer", "cloud_engineer", "platform_engineer"],
	"product_roles": ["product_manager", "product_designer"],
}


def get_role_combo(combo_name: str) -> List[str]:
	"""Get a predefined combination of roles"""
	return ROLE_COMBOS.get(combo_name, [])
