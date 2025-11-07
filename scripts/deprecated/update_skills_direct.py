"""
Update Moatasim's skills using asyncpg
"""

import asyncio
import json

import asyncpg

SKILLS = [
	"Python",
	"JavaScript",
	"TypeScript",
	"SQL",
	"Bash",
	"Machine Learning",
	"Data Science",
	"Deep Learning",
	"Natural Language Processing",
	"Computer Vision",
	"PyTorch",
	"TensorFlow",
	"Scikit-learn",
	"Pandas",
	"NumPy",
	"Data Analysis",
	"FastAPI",
	"React",
	"Node.js",
	"REST APIs",
	"GraphQL",
	"HTML/CSS",
	"PostgreSQL",
	"MongoDB",
	"Redis",
	"Elasticsearch",
	"AWS",
	"Azure",
	"GCP",
	"Docker",
	"Kubernetes",
	"CI/CD",
	"Linux",
	"Git",
	"Agile",
	"Microservices",
	"API Development",
]


async def update_skills():
	conn = await asyncpg.connect(user="moatasimfarooque", database="career_copilot", host="localhost", port=5432)
	try:
		print(f"🚀 Updating skills ({len(SKILLS)} total)...")
		await conn.execute(
			"UPDATE users SET skills = $1::jsonb, experience_level = 'senior' WHERE email = 'moatasimfarooque@gmail.com'", json.dumps(SKILLS)
		)
		user = await conn.fetchrow("SELECT username, email FROM users WHERE email = 'moatasimfarooque@gmail.com'")
		skills_json = await conn.fetchval("SELECT skills FROM users WHERE email = 'moatasimfarooque@gmail.com'")
		skills_list = json.loads(skills_json)
		print(f"✅ Updated! Username: {user['username']}, Skills: {len(skills_list)}")
		print(f"🔧 First 10: {', '.join(skills_list[:10])}")
	finally:
		await conn.close()


if __name__ == "__main__":
	asyncio.run(update_skills())
	asyncio.run(update_skills())
