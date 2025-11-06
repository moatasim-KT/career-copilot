"""
Single User Configuration

Constants and utilities for single-user (Moatasim) system.
All authentication-dependent code should import from here.
"""

# Single user constants
MOATASIM_USER_ID = 1
MOATASIM_NAME = "Moatasim"
MOATASIM_EMAIL = "moatasim@career-copilot.com"
MOATASIM_USERNAME = "moatasim"

# User skills and preferences
MOATASIM_SKILLS = [
	"Python",
	"FastAPI",
	"React",
	"TypeScript",
	"PostgreSQL",
	"Docker",
	"AWS",
	"Machine Learning",
	"Data Science",
	"System Design",
	"Node.js",
	"Next.js",
]

MOATASIM_EXPERIENCE_LEVEL = "senior"

MOATASIM_CAREER_GOALS = [
	"Full Stack Development",
	"AI/ML Engineering",
	"System Design",
	"Cloud Architecture",
]


class SingleUser:
	"""Simple user class for single-user system operations"""

	def __init__(self):
		self.id = MOATASIM_USER_ID
		self.name = MOATASIM_NAME
		self.email = MOATASIM_EMAIL
		self.username = MOATASIM_USERNAME
		self.skills = MOATASIM_SKILLS
		self.experience_level = MOATASIM_EXPERIENCE_LEVEL
		self.career_goals = MOATASIM_CAREER_GOALS
		# Common attributes for compatibility
		self.is_superuser = True
		self.is_active = True


def get_single_user() -> SingleUser:
	"""Get the single user instance for the system"""
	return SingleUser()
