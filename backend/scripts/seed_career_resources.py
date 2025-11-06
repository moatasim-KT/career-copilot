"""
Seed Career Resources

Populates the database with curated career development resources.
Run this script to initialize the career_resources table with high-quality learning materials.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging import get_logger
from app.models.career_resources import CareerResourceModel

logger = get_logger(__name__)


CURATED_RESOURCES = [
	# Python Resources
	{
		"id": "python_complete",
		"title": "Complete Python Developer in 2024",
		"description": "Master Python from basics to advanced topics including web development, data science, and automation",
		"type": "course",
		"provider": "Udemy",
		"url": "https://www.udemy.com/course/complete-python-developer/",
		"skills": ["Python", "Django", "Flask", "Data Science"],
		"difficulty": "beginner",
		"duration": "30 hours",
		"price": "$84.99",
		"rating": 4.7,
		"base_relevance_score": 95,
		"tags": ["web development", "automation", "backend"],
		"prerequisites": [],
		"learning_outcomes": ["Python fundamentals", "Web frameworks", "Data analysis", "Automation scripts"],
	},
	{
		"id": "python_docs",
		"title": "Official Python Documentation",
		"description": "The official comprehensive Python documentation and tutorials",
		"type": "article",
		"provider": "Python.org",
		"url": "https://docs.python.org/3/",
		"skills": ["Python"],
		"difficulty": "beginner",
		"duration": "ongoing",
		"price": "free",
		"rating": 4.9,
		"base_relevance_score": 90,
		"tags": ["documentation", "reference", "official"],
		"prerequisites": [],
		"learning_outcomes": ["Python syntax", "Standard library", "Best practices"],
	},
	# Machine Learning Resources
	{
		"id": "ml_coursera",
		"title": "Machine Learning Specialization",
		"description": "Andrew Ng's comprehensive ML course covering supervised learning, neural networks, and more",
		"type": "course",
		"provider": "Coursera",
		"url": "https://www.coursera.org/specializations/machine-learning-introduction",
		"skills": ["Machine Learning", "Python", "TensorFlow"],
		"difficulty": "intermediate",
		"duration": "3 months",
		"price": "$49/month",
		"rating": 4.9,
		"base_relevance_score": 98,
		"tags": ["ai", "deep learning", "neural networks"],
		"prerequisites": ["Python", "Linear Algebra", "Calculus"],
		"learning_outcomes": ["Supervised learning", "Neural networks", "ML algorithms", "Model deployment"],
	},
	{
		"id": "pytorch_tutorial",
		"title": "PyTorch Tutorials",
		"description": "Official PyTorch tutorials for deep learning",
		"type": "article",
		"provider": "PyTorch",
		"url": "https://pytorch.org/tutorials/",
		"skills": ["PyTorch", "Deep Learning", "AI"],
		"difficulty": "intermediate",
		"duration": "20 hours",
		"price": "free",
		"rating": 4.7,
		"base_relevance_score": 92,
		"tags": ["deep learning", "neural networks", "computer vision"],
		"prerequisites": ["Python", "Basic ML concepts"],
		"learning_outcomes": ["PyTorch fundamentals", "Neural network training", "Computer vision", "NLP"],
	},
	# Web Development Resources
	{
		"id": "react_complete",
		"title": "React - The Complete Guide",
		"description": "Deep dive into React including Hooks, Context, Redux, and Next.js",
		"type": "course",
		"provider": "Udemy",
		"url": "https://www.udemy.com/course/react-the-complete-guide/",
		"skills": ["React", "JavaScript", "TypeScript", "Next.js"],
		"difficulty": "intermediate",
		"duration": "48 hours",
		"price": "$84.99",
		"rating": 4.8,
		"base_relevance_score": 88,
		"tags": ["frontend", "spa", "web development"],
		"prerequisites": ["JavaScript", "HTML", "CSS"],
		"learning_outcomes": ["React components", "State management", "Hooks", "Next.js SSR"],
	},
	{
		"id": "typescript_handbook",
		"title": "TypeScript Handbook",
		"description": "Official TypeScript documentation and best practices",
		"type": "article",
		"provider": "TypeScript",
		"url": "https://www.typescriptlang.org/docs/handbook/intro.html",
		"skills": ["TypeScript", "JavaScript"],
		"difficulty": "intermediate",
		"duration": "10 hours",
		"price": "free",
		"rating": 4.8,
		"base_relevance_score": 85,
		"tags": ["type safety", "javascript", "documentation"],
		"prerequisites": ["JavaScript"],
		"learning_outcomes": ["Type systems", "Interfaces", "Generics", "Advanced types"],
	},
	# Cloud & DevOps
	{
		"id": "aws_certified",
		"title": "AWS Certified Solutions Architect",
		"description": "Prepare for AWS certification and master cloud architecture",
		"type": "certification",
		"provider": "AWS",
		"url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
		"skills": ["AWS", "Cloud Computing", "DevOps"],
		"difficulty": "intermediate",
		"duration": "3 months",
		"price": "$150 exam",
		"rating": 4.6,
		"base_relevance_score": 90,
		"tags": ["cloud", "architecture", "certification"],
		"prerequisites": ["Basic cloud concepts", "Networking basics"],
		"learning_outcomes": ["AWS services", "Cloud architecture", "Security", "Cost optimization"],
	},
	{
		"id": "kubernetes_course",
		"title": "Kubernetes for Developers",
		"description": "Learn container orchestration with Kubernetes",
		"type": "course",
		"provider": "Pluralsight",
		"url": "https://www.pluralsight.com/courses/kubernetes-developers-core-concepts",
		"skills": ["Kubernetes", "Docker", "DevOps"],
		"difficulty": "intermediate",
		"duration": "6 hours",
		"price": "$29/month",
		"rating": 4.5,
		"base_relevance_score": 87,
		"tags": ["containers", "orchestration", "devops"],
		"prerequisites": ["Docker basics", "Linux command line"],
		"learning_outcomes": ["Kubernetes architecture", "Deployments", "Services", "Configuration"],
	},
	# System Design
	{
		"id": "system_design_primer",
		"title": "System Design Primer",
		"description": "Comprehensive guide to system design interview preparation",
		"type": "article",
		"provider": "GitHub",
		"url": "https://github.com/donnemartin/system-design-primer",
		"skills": ["System Design", "Architecture", "Scalability"],
		"difficulty": "advanced",
		"duration": "40 hours",
		"price": "free",
		"rating": 5.0,
		"base_relevance_score": 95,
		"tags": ["system design", "scalability", "interview prep"],
		"prerequisites": ["Data structures", "Algorithms", "Databases"],
		"learning_outcomes": ["Scalability patterns", "System architecture", "Trade-offs", "Interview skills"],
	},
	{
		"id": "designing_data_intensive",
		"title": "Designing Data-Intensive Applications",
		"description": "The big ideas behind reliable, scalable, and maintainable systems",
		"type": "book",
		"provider": "O'Reilly",
		"url": "https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/",
		"skills": ["System Design", "Databases", "Distributed Systems"],
		"difficulty": "advanced",
		"duration": "4 weeks",
		"price": "$60",
		"rating": 4.9,
		"base_relevance_score": 92,
		"tags": ["databases", "distributed systems", "architecture"],
		"prerequisites": ["Programming experience", "Database basics"],
		"learning_outcomes": ["Data models", "Storage engines", "Distributed data", "Consistency"],
	},
	# Data Science
	{
		"id": "data_science_python",
		"title": "Python for Data Science and Machine Learning",
		"description": "Complete data science bootcamp with Python, Pandas, and Scikit-learn",
		"type": "course",
		"provider": "Udemy",
		"url": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/",
		"skills": ["Data Science", "Python", "Pandas", "NumPy", "Scikit-learn"],
		"difficulty": "intermediate",
		"duration": "25 hours",
		"price": "$84.99",
		"rating": 4.6,
		"base_relevance_score": 93,
		"tags": ["data analysis", "machine learning", "visualization"],
		"prerequisites": ["Python basics"],
		"learning_outcomes": ["Data analysis", "Visualization", "ML algorithms", "Pandas mastery"],
	},
	# Software Engineering Books
	{
		"id": "clean_code",
		"title": "Clean Code: A Handbook of Agile Software Craftsmanship",
		"description": "Essential book on writing maintainable, readable code",
		"type": "book",
		"provider": "Amazon",
		"url": "https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882",
		"skills": ["Software Engineering", "Best Practices", "Code Quality"],
		"difficulty": "intermediate",
		"duration": "2 weeks",
		"price": "$45",
		"rating": 4.7,
		"base_relevance_score": 88,
		"tags": ["clean code", "best practices", "refactoring"],
		"prerequisites": ["Programming experience"],
		"learning_outcomes": ["Code quality", "Naming conventions", "Function design", "Error handling"],
	},
	{
		"id": "cracking_coding",
		"title": "Cracking the Coding Interview",
		"description": "150+ programming questions and solutions for technical interviews",
		"type": "book",
		"provider": "Amazon",
		"url": "https://www.amazon.com/Cracking-Coding-Interview-Programming-Questions/dp/0984782850",
		"skills": ["Algorithms", "Data Structures", "Interview Prep"],
		"difficulty": "intermediate",
		"duration": "3 months",
		"price": "$49.95",
		"rating": 4.7,
		"base_relevance_score": 90,
		"tags": ["interview prep", "algorithms", "coding problems"],
		"prerequisites": ["Programming fundamentals"],
		"learning_outcomes": ["Algorithm design", "Problem solving", "Interview skills", "Data structures"],
	},
	# Tools & Version Control
	{
		"id": "git_tutorial",
		"title": "Pro Git Book",
		"description": "Comprehensive guide to Git version control",
		"type": "article",
		"provider": "Git",
		"url": "https://git-scm.com/book/en/v2",
		"skills": ["Git", "Version Control"],
		"difficulty": "beginner",
		"duration": "15 hours",
		"price": "free",
		"rating": 4.8,
		"base_relevance_score": 85,
		"tags": ["git", "version control", "collaboration"],
		"prerequisites": [],
		"learning_outcomes": ["Git fundamentals", "Branching strategies", "Collaboration workflows", "Advanced Git"],
	},
]


async def seed_resources():
	"""Seed the database with curated career resources."""
	# Use get_db to get a database session
	from app.core.database import get_db

	async for session in get_db():
		try:
			logger.info("Starting career resources seeding...")

			for resource_data in CURATED_RESOURCES:
				# Check if resource already exists
				existing = await session.get(CareerResourceModel, resource_data["id"])

				if existing:
					# Update existing resource
					for key, value in resource_data.items():
						setattr(existing, key, value)
					logger.info(f"Updated resource: {resource_data['id']}")
				else:
					# Create new resource
					resource = CareerResourceModel(**resource_data)
					session.add(resource)
					logger.info(f"Created resource: {resource_data['id']}")

			await session.commit()
			logger.info(f"Successfully seeded {len(CURATED_RESOURCES)} career resources")

		except Exception as e:
			await session.rollback()
			logger.error(f"Error seeding resources: {e}", exc_info=True)
			raise


if __name__ == "__main__":
	asyncio.run(seed_resources())
