"""
Simple script to update Moatasim's skills using psql
"""

import json
import subprocess

# Skills to add to your profile
SKILLS = [
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

# Create JSON string
skills_json = json.dumps(SKILLS)

# SQL command
sql = f"""
UPDATE users 
SET skills = '{skills_json}'::jsonb,
    experience_level = 'senior'
WHERE email = 'moatasimfarooque@gmail.com';

SELECT email, array_length(skills, 1) as skill_count, experience_level 
FROM users 
WHERE email = 'moatasimfarooque@gmail.com';
"""

print("🚀 Updating Moatasim's skills...")
print(f"📊 Adding {len(SKILLS)} skills...")

# Run psql command
result = subprocess.run(["psql", "-U", "postgres", "-d", "career_copilot", "-c", sql], capture_output=True, text=True, env={"PGPASSWORD": "postgres"})

if result.returncode == 0:
	print("✅ Skills updated successfully!")
	print("\nDatabase response:")
	print(result.stdout)
else:
	print("❌ Error updating skills:")
	print(result.stderr)
