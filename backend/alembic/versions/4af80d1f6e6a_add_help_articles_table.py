"""add_help_articles_table

Revision ID: 4af80d1f6e6a
Revises: career_resources_001
Create Date: 2025-11-07 22:33:45.306391

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4af80d1f6e6a"
down_revision: Union[str, Sequence[str], None] = "career_resources_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Upgrade schema."""
	# Check if tables exist before creating
	conn = op.get_bind()
	inspector = sa.inspect(conn)
	existing_tables = inspector.get_table_names()

	if "help_articles" not in existing_tables:
		# Create help_articles table
		op.create_table(
			"help_articles",
			sa.Column("id", sa.Integer(), nullable=False),
			sa.Column("title", sa.String(length=255), nullable=False),
			sa.Column("slug", sa.String(length=255), nullable=False),
			sa.Column("content", sa.Text(), nullable=False),
			sa.Column("excerpt", sa.String(length=500), nullable=True),
			sa.Column("category", sa.String(length=100), nullable=False),
			sa.Column("tags", postgresql.JSON(astext_type=sa.Text()), nullable=True),
			sa.Column("meta_description", sa.String(length=500), nullable=True),
			sa.Column("search_keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True),
			sa.Column("is_published", sa.Boolean(), nullable=True),
			sa.Column("published_at", sa.DateTime(), nullable=True),
			sa.Column("view_count", sa.Integer(), nullable=True),
			sa.Column("helpful_votes", sa.Integer(), nullable=True),
			sa.Column("unhelpful_votes", sa.Integer(), nullable=True),
			sa.Column("created_at", sa.DateTime(), nullable=True),
			sa.Column("updated_at", sa.DateTime(), nullable=True),
			sa.PrimaryKeyConstraint("id"),
		)
		op.create_index(op.f("ix_help_articles_category"), "help_articles", ["category"], unique=False)
		op.create_index(op.f("ix_help_articles_created_at"), "help_articles", ["created_at"], unique=False)
		op.create_index(op.f("ix_help_articles_id"), "help_articles", ["id"], unique=False)
		op.create_index(op.f("ix_help_articles_is_published"), "help_articles", ["is_published"], unique=False)
		op.create_index(op.f("ix_help_articles_slug"), "help_articles", ["slug"], unique=True)

	if "help_article_votes" not in existing_tables:
		# Create help_article_votes table
		op.create_table(
			"help_article_votes",
			sa.Column("id", sa.Integer(), nullable=False),
			sa.Column("article_id", sa.Integer(), nullable=False),
			sa.Column("user_id", sa.Integer(), nullable=False),
			sa.Column("is_helpful", sa.Boolean(), nullable=False),
			sa.Column("created_at", sa.DateTime(), nullable=True),
			sa.ForeignKeyConstraint(
				["article_id"],
				["help_articles.id"],
			),
			sa.ForeignKeyConstraint(
				["user_id"],
				["users.id"],
			),
			sa.PrimaryKeyConstraint("id"),
		)
		op.create_index(op.f("ix_help_article_votes_article_id"), "help_article_votes", ["article_id"], unique=False)
		op.create_index(op.f("ix_help_article_votes_id"), "help_article_votes", ["id"], unique=False)
		op.create_index(op.f("ix_help_article_votes_user_id"), "help_article_votes", ["user_id"], unique=False)

	# Seed initial help articles
	op.execute("""
        INSERT INTO help_articles (title, slug, content, excerpt, category, tags, meta_description, is_published, published_at, view_count, helpful_votes, unhelpful_votes, created_at, updated_at)
        VALUES
        ('Getting Started with Career Copilot', 'getting-started', 
         'Welcome to Career Copilot! This comprehensive guide will help you get started with your job search journey.\n\nFirst, set up your profile with your skills, experience level, and preferred job locations. Upload your resume so we can better understand your background and match you with relevant opportunities.\n\nNext, explore the job board and use our AI-powered search to find positions that match your criteria. You can save interesting jobs and track your applications all in one place.\n\nDon''t forget to set up job alerts to get notified when new opportunities matching your preferences are posted!',
         'Learn how to set up your profile and start your job search with Career Copilot', 
         'getting_started', 
         '["beginner", "setup", "profile", "onboarding"]'::json,
         'Complete guide to getting started with Career Copilot job search platform',
         true, NOW(), 1523, 145, 12, NOW(), NOW()),
        
        ('How to Upload and Parse Your Resume', 'upload-resume',
         'Your resume is the foundation of your Career Copilot profile. Here''s how to upload and optimize it.\n\nSupported formats: PDF, DOCX, TXT. We recommend PDF for best parsing results.\n\nStep 1: Click the "Upload Resume" button in your profile section.\nStep 2: Select your resume file from your computer.\nStep 3: Our AI will automatically extract your skills, experience, education, and contact information.\nStep 4: Review the parsed information and make any necessary corrections.\nStep 5: Save your profile to start receiving personalized job recommendations.\n\nTips for best results:\n- Use a clean, well-formatted resume\n- Include clear section headers (Experience, Education, Skills)\n- List skills explicitly\n- Use standard date formats',
         'Step-by-step guide to uploading and parsing your resume for optimal job matching',
         'resume',
         '["resume", "upload", "parsing", "pdf", "profile"]'::json,
         'Learn how to upload your resume to Career Copilot and optimize parsing',
         true, NOW(), 2341, 234, 18, NOW(), NOW()),
        
        ('Setting Up Job Alerts', 'job-alerts',
         'Never miss a great opportunity with personalized job alerts.\n\nCareer Copilot can notify you when new jobs matching your criteria are posted. Here''s how to set it up:\n\n1. Navigate to Settings > Notifications\n2. Enable "Job Alerts"\n3. Choose your alert frequency (real-time, daily digest, weekly summary)\n4. Configure filters:\n   - Job titles or keywords\n   - Locations\n   - Experience level\n   - Salary range\n   - Remote work preferences\n5. Select notification channels (email, in-app, browser push)\n\nPro tips:\n- Start with broad criteria and refine based on results\n- Use the "exclude keywords" feature to filter out irrelevant jobs\n- Set up multiple alerts for different job types you''re interested in\n- Review and adjust your alerts regularly',
         'Configure personalized job alerts to never miss opportunities matching your criteria',
         'job_search',
         '["alerts", "notifications", "job search", "automation"]'::json,
         'Set up job alerts and notifications for new opportunities',
         true, NOW(), 1876, 198, 15, NOW(), NOW()),
        
        ('Preparing for Technical Interviews', 'technical-interviews',
         'Master technical interviews with our comprehensive preparation guide.\n\nTechnical interviews can be challenging, but with proper preparation, you can excel. Here''s your roadmap:\n\n**Before the Interview:**\n- Research the company and role thoroughly\n- Review job description and required skills\n- Practice coding problems on platforms like LeetCode, HackerRank\n- Prepare questions to ask the interviewer\n- Test your equipment for remote interviews\n\n**During the Interview:**\n- Think out loud - explain your reasoning\n- Ask clarifying questions\n- Start with a brute force solution, then optimize\n- Consider edge cases and error handling\n- Communicate clearly and professionally\n\n**Common Topics:**\n- Data structures (arrays, trees, graphs, hash tables)\n- Algorithms (sorting, searching, dynamic programming)\n- System design (for senior roles)\n- Time and space complexity analysis\n- Language-specific best practices\n\n**After the Interview:**\n- Send a thank you email within 24 hours\n- Reflect on your performance\n- Follow up appropriately\n\nUse Career Copilot''s interview practice feature to simulate real interviews!',
         'Comprehensive guide to mastering technical interviews and coding challenges',
         'interview',
         '["interview", "technical", "preparation", "coding", "algorithms"]'::json,
         'Prepare for technical interviews with expert tips and strategies',
         true, NOW(), 3421, 456, 22, NOW(), NOW()),
        
        ('Tracking Your Applications', 'track-applications',
         'Stay organized and follow up effectively by tracking all your job applications.\n\nCareer Copilot helps you manage your entire application pipeline:\n\n**Application Stages:**\n1. Applied - Submitted your application\n2. Screening - Under review by recruiter\n3. Phone Screen - Initial phone interview scheduled\n4. Technical Interview - Technical assessment stage\n5. Final Interview - Meeting with hiring manager/team\n6. Offer - Received job offer\n7. Rejected - Application not moving forward\n8. Accepted - Accepted the offer\n\n**Best Practices:**\n- Log every application immediately\n- Set reminders for follow-ups (1-2 weeks)\n- Keep notes on each company and role\n- Track interview feedback\n- Monitor your application-to-interview ratio\n- Analyze which sources yield best results\n\n**Dashboard Features:**\n- Visual pipeline view\n- Application statistics and insights\n- Timeline view for each application\n- Email integration for automatic tracking\n- Custom tags and notes\n\nRegularly review your dashboard to identify patterns and improve your strategy!',
         'Learn how to effectively manage and track all your job applications in one place',
         'applications',
         '["applications", "tracking", "organization", "pipeline", "dashboard"]'::json,
         'Track and manage your job applications with Career Copilot',
         true, NOW(), 2145, 276, 20, NOW(), NOW()),
        
        ('Building Your Professional Network', 'professional-networking',
         'Networking is crucial for career success. Here''s how to build meaningful professional connections.\n\n**Online Networking:**\n- Optimize your LinkedIn profile\n- Join industry-specific groups and communities\n- Engage with content (like, comment, share)\n- Share your own insights and experiences\n- Connect with professionals in your field\n- Attend virtual events and webinars\n\n**Offline Networking:**\n- Attend industry conferences and meetups\n- Join professional associations\n- Participate in hackathons and workshops\n- Volunteer for industry events\n- Alumni networks and reunions\n\n**Networking Tips:**\n- Be genuine and authentic\n- Offer value before asking for favors\n- Follow up after initial meetings\n- Maintain regular contact\n- Help others when possible\n- Have your elevator pitch ready\n\n**Career Copilot Integration:**\n- Import LinkedIn connections\n- Track networking interactions\n- Set networking goals\n- Get reminders to follow up\n\nRemember: Quality matters more than quantity. Focus on building genuine relationships!',
         'Build and maintain a strong professional network to advance your career',
         'networking',
         '["networking", "linkedin", "professional", "connections", "career growth"]'::json,
         'Learn how to build a strong professional network',
         true, NOW(), 1654, 187, 14, NOW(), NOW()),
        
        ('Salary Negotiation Strategies', 'salary-negotiation',
         'Negotiate your worth with confidence using these proven strategies.\n\n**Research Phase:**\n- Use salary comparison tools (Glassdoor, Levels.fyi, Payscale)\n- Consider total compensation (base, bonus, equity, benefits)\n- Factor in location and cost of living\n- Research company funding and growth stage\n- Know your minimum acceptable offer\n\n**Timing:**\n- Don''t discuss salary too early\n- Wait for an offer before negotiating\n- Take time to review offers (24-48 hours)\n\n**Negotiation Tactics:**\n- Express enthusiasm for the role first\n- Provide data-driven justification\n- Focus on value you bring\n- Be prepared to discuss specific numbers\n- Consider non-salary benefits\n- Stay professional and positive\n\n**What to Negotiate:**\n- Base salary\n- Signing bonus\n- Performance bonuses\n- Equity/stock options\n- Vacation time\n- Remote work flexibility\n- Professional development budget\n- Start date\n\n**Example Scripts:**\n"Based on my research and experience, I was expecting a range of $X-$Y. Can we explore options to get closer to that range?"\n\n"I''m very excited about this opportunity. The offer is competitive, but I was hoping we could discuss [specific aspect]."\n\nRemember: Most companies expect negotiation. Don''t leave money on the table!',
         'Master salary negotiation with expert strategies and proven tactics',
         'career_growth',
         '["salary", "negotiation", "compensation", "offer", "career"]'::json,
         'Learn how to effectively negotiate your salary and benefits',
         true, NOW(), 2987, 341, 19, NOW(), NOW()),
        
        ('Troubleshooting Common Issues', 'troubleshooting',
         'Quick solutions to common Career Copilot issues.\n\n**Resume Upload Issues:**\nProblem: Resume not parsing correctly\nSolution:\n- Ensure file is PDF or DOCX format\n- Check file size (max 10MB)\n- Use a simple, clean format\n- Manually edit parsed information\n\n**Job Search Issues:**\nProblem: Not finding relevant jobs\nSolution:\n- Broaden your search criteria\n- Update your skills and preferences\n- Check your location settings\n- Try different keyword combinations\n\n**Application Tracking:**\nProblem: Applications not syncing\nSolution:\n- Refresh the page\n- Check your internet connection\n- Clear browser cache\n- Re-authorize email integration\n\n**Notification Issues:**\nProblem: Not receiving job alerts\nSolution:\n- Check spam/junk folder\n- Verify email in settings\n- Ensure notifications are enabled\n- Check alert frequency settings\n\n**Account Issues:**\nProblem: Can''t log in\nSolution:\n- Reset your password\n- Clear cookies and cache\n- Try a different browser\n- Contact support if persistent\n\n**Still Having Issues?**\nContact support at support@careercopilot.ai or use the in-app chat. Include:\n- Description of the issue\n- Steps to reproduce\n- Screenshots if applicable\n- Browser and device information',
         'Find quick solutions to common Career Copilot platform issues',
         'troubleshooting',
         '["troubleshooting", "issues", "problems", "help", "support"]'::json,
         'Troubleshoot common issues with Career Copilot',
         true, NOW(), 876, 94, 28, NOW(), NOW())
    """)


def downgrade() -> None:
	"""Downgrade schema."""
	op.drop_index(op.f("ix_help_article_votes_user_id"), table_name="help_article_votes")
	op.drop_index(op.f("ix_help_article_votes_id"), table_name="help_article_votes")
	op.drop_index(op.f("ix_help_article_votes_article_id"), table_name="help_article_votes")
	op.drop_table("help_article_votes")
	op.drop_index(op.f("ix_help_articles_slug"), table_name="help_articles")
	op.drop_index(op.f("ix_help_articles_is_published"), table_name="help_articles")
	op.drop_index(op.f("ix_help_articles_id"), table_name="help_articles")
	op.drop_index(op.f("ix_help_articles_created_at"), table_name="help_articles")
	op.drop_index(op.f("ix_help_articles_category"), table_name="help_articles")
	op.drop_table("help_articles")
