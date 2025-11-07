"""
Update Moatasim's skills directly in the database
This bypasses the resume upload which is having model configuration issues
"""

import asyncio

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/career_copilot"

# Skills to add to your profile
NEW_SKILLS = [
	# Existing skills
	"Python",
	"Machine Learning",
	"Data Science",
	"FastAPI",
	"React",
	"TypeScript",
	"PostgreSQL",
	"Docker",
	"Kubernetes",
	"AWS",
	# Add your additional skills here from your resume
	"PyTorch",
	"TensorFlow",
	"Scikit-learn",
	"Pandas",
	"NumPy",
	"Natural Language Processing",
	"Computer Vision",
	"Deep Learning",
	"SQL",
	"Git",
	"CI/CD",
	"Agile",
	"REST APIs",
	"GraphQL",
	"Node.js",
	"JavaScript",
	"HTML/CSS",
	"MongoDB",
	"Redis",
	"Elasticsearch",
]


async def update_skills():
	"""Update Moatasim's skills in the database"""
	# Create async engine
	engine = create_async_engine(DATABASE_URL, echo=True)

	# Create async session
	async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

	async with async_session() as session:
		# Update user skills
		stmt = (
			update(None)  # We'll use raw SQL instead
		)

		# Use raw SQL to avoid model issues
		await session.execute(
			"""
            UPDATE users 
            SET skills = :skills, 
                experience_level = 'senior',
                updated_at = NOW()
            WHERE email = 'moatasimfarooque@gmail.com'
            """,
			{"skills": NEW_SKILLS},
		)

		await session.commit()
		print(f"✅ Successfully updated skills for moatasimfarooque@gmail.com")
		print(f"📊 Total skills: {len(NEW_SKILLS)}")
		print(f"🔧 Skills: {', '.join(NEW_SKILLS[:10])}...")

		# Verify update
		result = await session.execute(
			"""
            SELECT username, email, skills, experience_level 
            FROM users 
            WHERE email = 'moatasimfarooque@gmail.com'
            """
		)
		user = result.first()
		if user:
			print(f"\n✨ Current Profile:")
			print(f"   Username: {user[0]}")
			print(f"   Email: {user[1]}")
			print(f"   Skills: {len(user[2])} total")
			print(f"   Experience: {user[3]}")

	await engine.dispose()


if __name__ == "__main__":
	print("🚀 Updating Moatasim's skills...")
	asyncio.run(update_skills())
	print("\n✅ Update complete!")
	print("\n✅ Update complete!")
