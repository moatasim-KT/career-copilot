"""Seed help articles into the database"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from sqlalchemy import text

from app.core.database import get_db


async def seed_help_articles():
	"""Seed initial help articles"""

	async for session in get_db():
		# Check if articles already exist
		result = await session.execute(text("SELECT COUNT(*) FROM help_articles"))
		count = result.scalar()

		if count > 0:
			print(f"✓ Help articles table already has {count} articles")
			return

		print("Seeding help articles...")

		articles_sql = """
INSERT INTO help_articles (title, slug, content, excerpt, category, tags, meta_description, is_published, published_at, view_count, helpful_votes, unhelpful_votes, created_at, updated_at)
VALUES
('Getting Started with Career Copilot', 'getting-started', 
 'Welcome to Career Copilot! This comprehensive guide will help you get started with your job search journey.

First, set up your profile with your skills, experience level, and preferred job locations. Upload your resume so we can better understand your background and match you with relevant opportunities.

Next, explore the job board and use our AI-powered search to find positions that match your criteria. You can save interesting jobs and track your applications all in one place.

Don''t forget to set up job alerts to get notified when new opportunities matching your preferences are posted!',
 'Learn how to set up your profile and start your job search with Career Copilot', 
 'getting_started', 
 '["beginner", "setup", "profile", "onboarding"]'::json,
 'Complete guide to getting started with Career Copilot job search platform',
 true, NOW(), 0, 0, 0, NOW(), NOW()),

('How to Upload and Parse Your Resume', 'upload-resume',
 'Your resume is the foundation of your Career Copilot profile. Here''s how to upload and optimize it.

Supported formats: PDF, DOCX, TXT. We recommend PDF for best parsing results.

Step 1: Click the "Upload Resume" button in your profile section.
Step 2: Select your resume file from your computer.
Step 3: Our AI will automatically extract your skills, experience, education, and contact information.
Step 4: Review the parsed information and make any necessary corrections.
Step 5: Save your profile to start receiving personalized job recommendations.

Tips for best results:
- Use a clean, well-formatted resume
- Include clear section headers (Experience, Education, Skills)
- List skills explicitly
- Use standard date formats',
 'Step-by-step guide to uploading and parsing your resume for optimal job matching',
 'resume',
 '["resume", "upload", "parsing", "pdf", "profile"]'::json,
 'Learn how to upload your resume to Career Copilot and optimize parsing',
 true, NOW(), 0, 0, 0, NOW(), NOW()),

('Setting Up Job Alerts', 'job-alerts',
 'Never miss a great opportunity with personalized job alerts.

Career Copilot can notify you when new jobs matching your criteria are posted. Here''s how to set it up:

1. Navigate to Settings > Notifications
2. Enable "Job Alerts"
3. Choose your alert frequency (real-time, daily digest, weekly summary)
4. Configure filters:
   - Job titles or keywords
   - Locations
   - Experience level
   - Salary range
   - Remote work preferences
5. Select notification channels (email, in-app, browser push)

Pro tips:
- Start with broad criteria and refine based on results
- Use the "exclude keywords" feature to filter out irrelevant jobs
- Set up multiple alerts for different job types you''re interested in
- Review and adjust your alerts regularly',
 'Configure personalized job alerts to never miss opportunities matching your criteria',
 'job_search',
 '["alerts", "notifications", "job search", "automation"]'::json,
 'Set up job alerts and notifications for new opportunities',
 true, NOW(), 0, 0, 0, NOW(), NOW()),

('Preparing for Technical Interviews', 'technical-interviews',
 'Master technical interviews with our comprehensive preparation guide.

Technical interviews can be challenging, but with proper preparation, you can excel. Here''s your roadmap:

**Before the Interview:**
- Research the company and role thoroughly
- Review job description and required skills
- Practice coding problems on platforms like LeetCode, HackerRank
- Prepare questions to ask the interviewer
- Test your equipment for remote interviews

**During the Interview:**
- Think out loud - explain your reasoning
- Ask clarifying questions
- Start with a brute force solution, then optimize
- Consider edge cases and error handling
- Communicate clearly and professionally

**Common Topics:**
- Data structures (arrays, trees, graphs, hash tables)
- Algorithms (sorting, searching, dynamic programming)
- System design (for senior roles)
- Time and space complexity analysis
- Language-specific best practices

**After the Interview:**
- Send a thank you email within 24 hours
- Reflect on your performance
- Follow up appropriately

Use Career Copilot''s interview practice feature to simulate real interviews!',
 'Comprehensive guide to mastering technical interviews and coding challenges',
 'interview',
 '["interview", "technical", "preparation", "coding", "algorithms"]'::json,
 'Prepare for technical interviews with expert tips and strategies',
 true, NOW(), 0, 0, 0, NOW(), NOW()),

('Tracking Your Applications', 'track-applications',
 'Stay organized and follow up effectively by tracking all your job applications.

Career Copilot helps you manage your entire application pipeline:

**Application Stages:**
1. Applied - Submitted your application
2. Screening - Under review by recruiter
3. Phone Screen - Initial phone interview scheduled
4. Technical Interview - Technical assessment stage
5. Final Interview - Meeting with hiring manager/team
6. Offer - Received job offer
7. Rejected - Application not moving forward
8. Accepted - Accepted the offer

**Best Practices:**
- Log every application immediately
- Set reminders for follow-ups (1-2 weeks)
- Keep notes on each company and role
- Track interview feedback
- Monitor your application-to-interview ratio
- Analyze which sources yield best results

**Dashboard Features:**
- Visual pipeline view
- Application statistics and insights
- Timeline view for each application
- Email integration for automatic tracking
- Custom tags and notes

Regularly review your dashboard to identify patterns and improve your strategy!',
 'Learn how to effectively manage and track all your job applications in one place',
 'applications',
 '["applications", "tracking", "organization", "pipeline", "dashboard"]'::json,
 'Track and manage your job applications with Career Copilot',
 true, NOW(), 0, 0, 0, NOW(), NOW()),

('Building Your Professional Network', 'professional-networking',
 'Networking is crucial for career success. Here''s how to build meaningful professional connections.

**Online Networking:**
- Optimize your LinkedIn profile
- Join industry-specific groups and communities
- Engage with content (like, comment, share)
- Share your own insights and experiences
- Connect with professionals in your field
- Attend virtual events and webinars

**Offline Networking:**
- Attend industry conferences and meetups
- Join professional associations
- Participate in hackathons and workshops
- Volunteer for industry events
- Alumni networks and reunions

**Networking Tips:**
- Be genuine and authentic
- Offer value before asking for favors
- Follow up after initial meetings
- Maintain regular contact
- Help others when possible
- Have your elevator pitch ready

**Career Copilot Integration:**
- Import LinkedIn connections
- Track networking interactions
- Set networking goals
- Get reminders to follow up

Remember: Quality matters more than quantity. Focus on building genuine relationships!',
 'Build and maintain a strong professional network to advance your career',
 'networking',
 '["networking", "linkedin", "professional", "connections", "career growth"]'::json,
 'Learn how to build a strong professional network',
 true, NOW(), 0, 0, 0, NOW(), NOW()),

('Salary Negotiation Strategies', 'salary-negotiation',
 'Negotiate your worth with confidence using these proven strategies.

**Research Phase:**
- Use salary comparison tools (Glassdoor, Levels.fyi, Payscale)
- Consider total compensation (base, bonus, equity, benefits)
- Factor in location and cost of living
- Research company funding and growth stage
- Know your minimum acceptable offer

**Timing:**
- Don''t discuss salary too early
- Wait for an offer before negotiating
- Take time to review offers (24-48 hours)

**Negotiation Tactics:**
- Express enthusiasm for the role first
- Provide data-driven justification
- Focus on value you bring
- Be prepared to discuss specific numbers
- Consider non-salary benefits
- Stay professional and positive

**What to Negotiate:**
- Base salary
- Signing bonus
- Performance bonuses
- Equity/stock options
- Vacation time
- Remote work flexibility
- Professional development budget
- Start date

**Example Scripts:**
"Based on my research and experience, I was expecting a range of $X-$Y. Can we explore options to get closer to that range?"

"I''m very excited about this opportunity. The offer is competitive, but I was hoping we could discuss [specific aspect]."

Remember: Most companies expect negotiation. Don''t leave money on the table!',
 'Master salary negotiation with expert strategies and proven tactics',
 'career_growth',
 '["salary", "negotiation", "compensation", "offer", "career"]'::json,
 'Learn how to effectively negotiate your salary and benefits',
 true, NOW(), 0, 0, 0, NOW(), NOW()),

('Troubleshooting Common Issues', 'troubleshooting',
 'Quick solutions to common Career Copilot issues.

**Resume Upload Issues:**
Problem: Resume not parsing correctly
Solution:
- Ensure file is PDF or DOCX format
- Check file size (max 10MB)
- Use a simple, clean format
- Manually edit parsed information

**Job Search Issues:**
Problem: Not finding relevant jobs
Solution:
- Broaden your search criteria
- Update your skills and preferences
- Check your location settings
- Try different keyword combinations

**Application Tracking:**
Problem: Applications not syncing
Solution:
- Refresh the page
- Check your internet connection
- Clear browser cache
- Re-authorize email integration

**Notification Issues:**
Problem: Not receiving job alerts
Solution:
- Check spam/junk folder
- Verify email in settings
- Ensure notifications are enabled
- Check alert frequency settings

**Account Issues:**
Problem: Can''t log in
Solution:
- Reset your password
- Clear cookies and cache
- Try a different browser
- Contact support if persistent

**Still Having Issues?**
Contact support at support@careercopilot.ai or use the in-app chat. Include:
- Description of the issue
- Steps to reproduce
- Screenshots if applicable
- Browser and device information',
 'Find quick solutions to common Career Copilot platform issues',
 'troubleshooting',
 '["troubleshooting", "issues", "problems", "help", "support"]'::json,
 'Troubleshoot common issues with Career Copilot',
 true, NOW(), 0, 0, 0, NOW(), NOW())
"""

		await session.execute(text(articles_sql))
		await session.commit()

		# Get final count
		result = await session.execute(text("SELECT COUNT(*) FROM help_articles"))
		count = result.scalar()
		print(f"✓ Successfully seeded {count} help articles")


if __name__ == "__main__":
	asyncio.run(seed_help_articles())
