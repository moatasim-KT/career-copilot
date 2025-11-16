# Career Copilot User Guide

Welcome to Career Copilot! This guide will help you get the most out of your AI-powered career management platform.

## Related Documents

**For Users**:
- [[career-copilot/README|Project README]] - Project overview
- [[DEMO_VIDEO_GUIDE]] - Demo walkthrough

**For Developers**:
- [[DEVELOPER_GUIDE]] - Developer documentation
- [[LOCAL_SETUP]] - Local development setup
- [[FRONTEND_QUICK_START]] - Quick frontend setup

**Technical Reference**:
- [[docs/index|Documentation Hub]] - Documentation hub
- [[ARCHITECTURE]] - System architecture
- [[API]] - API reference
- [[COMMON_ISSUES]] - Common issues

## Table of Contents

- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Job Search & Discovery](#job-search--discovery)
- [Application Tracking](#application-tracking)
- [AI-Powered Tools](#ai-powered-tools)
- [Analytics & Insights](#analytics--insights)
- [Settings & Customization](#settings--customization)
- [Tips & Best Practices](#tips--best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### First Time Setup

When you first access Career Copilot, you'll be guided through an onboarding wizard:

1. **Welcome & Profile Setup**
   - Enter your name and email
   - Upload a profile photo (optional)
   - Add your current job title
   - Select your years of experience

2. **Skills & Expertise**
   - Select your skills from popular suggestions
   - Search and add custom skills
   - Set proficiency levels (optional)

3. **Resume Upload**
   - Drag and drop your resume (PDF or DOCX)
   - AI will automatically extract your skills and experience
   - Review and edit extracted information

4. **Job Preferences**
   - Select preferred job titles
   - Choose preferred locations or select "Remote"
   - Set salary expectations
   - Choose work arrangement (Remote, Hybrid, On-site)

5. **Feature Tour**
   - Interactive walkthrough of key features
   - Learn keyboard shortcuts
   - Discover the command palette (⌘K)

### Quick Navigation

**Keyboard Shortcuts:**
- `⌘K` or `Ctrl+K` - Open command palette
- `⌘D` or `Ctrl+D` - Toggle dark mode
- `⌘/` or `Ctrl+/` - Show keyboard shortcuts
- `Esc` - Close modals and dialogs

**Command Palette:**
Press `⌘K` to open the command palette for instant access to:
- Navigation (Dashboard, Jobs, Applications, etc.)
- Actions (Create Job, Create Application, etc.)
- Settings (Toggle theme, Open settings, etc.)
- Search (Jobs, Applications, Saved Searches)

## Dashboard Overview

The dashboard is your central hub for managing your job search.

### Key Sections

1. **Quick Stats**
   - Total applications
   - Active applications
   - Interviews scheduled
   - Offers received

2. **Application Status Chart**
   - Visual breakdown of application statuses
   - Click on segments to filter applications

3. **Recent Activity**
   - Latest application updates
   - New job recommendations
   - Upcoming interviews

4. **Job Recommendations**
   - AI-powered job matches based on your profile
   - Personalized recommendations
   - One-click apply

5. **Upcoming Interviews**
   - Calendar view of scheduled interviews
   - Interview preparation resources
   - Quick access to company research

### Customizing Your Dashboard

1. Click the **Edit Layout** button
2. Drag and drop widgets to rearrange
3. Hide/show widgets using the visibility toggle
4. Click **Reset Layout** to restore defaults


## Job Search & Discovery

### Basic Search

1. Navigate to **Jobs** from the sidebar
2. Use the search bar to find jobs by:
   - Job title
   - Company name
   - Location
   - Keywords

3. Apply filters:
   - **Location**: City, country, or remote
   - **Salary Range**: Min and max salary
   - **Experience Level**: Entry, Mid, Senior, Lead
   - **Work Type**: Remote, Hybrid, On-site
   - **Visa Sponsorship**: Available or not

### Advanced Search

For complex searches, use the Advanced Search feature:

1. Click **Advanced Search** button
2. Build queries with AND/OR logic
3. Add multiple conditions:
   - Field (e.g., "Salary")
   - Operator (e.g., "greater than")
   - Value (e.g., "80000")
4. Nest conditions for complex queries
5. Click **Apply Search**

### Saved Searches

Save frequently used searches:

1. Perform a search
2. Click **Save Search**
3. Enter a name for the search
4. Access saved searches from the dropdown
5. Get automatic alerts for new matching jobs

### Job Details

Click on any job to view:
- Full job description
- Company information
- Salary range and benefits
- Required skills and qualifications
- Application deadline
- Visa sponsorship status

**Actions:**
- **Save Job**: Add to your saved jobs list
- **Apply**: Create an application
- **Generate Resume**: Create a tailored resume for this job
- **Generate Cover Letter**: Create a personalized cover letter
- **Share**: Share job with others

### Smart Recommendations & Custom Lists

1. Open the **Recommendations** tab from the sidebar or Dashboard widget.
2. Filter by seniority, remote preference, salary band, or tech stack tags.
3. The AI assigns a `Match Score` (0–100). Hover to see why it fits—skills overlap, location match, or salary alignment.
4. Click **Add to List** to move a recommendation into a custom collection (e.g., “Dream Companies”, “High Priority”).
5. Dismiss irrelevant roles; the model learns your preferences over time.

### Market Pulse

- Visit **Jobs → Market Pulse** to review EU tech hiring trends and region-specific salary medians.
- Toggle between **Last 7 Days**, **30 Days**, or **Quarter** to understand trend velocity.
- Use the filters at the top-right to compare locations (Berlin vs. Remote EU) or industries (Fintech, AI, Climate Tech).
- Export the snapshot as CSV to share with mentors or include in personal reports.

## Application Tracking

### Creating an Application

1. **From a Job Listing:**
   - Click **Apply** on any job
   - Fill in application details
   - Upload resume and cover letter
   - Click **Submit Application**

2. **Manual Entry:**
   - Click **New Application**
   - Enter job details manually
   - Add application date and status
   - Save application

### Application Statuses

Track your applications through these stages:
- **Interested**: Job saved and under initial review before submitting
- **Applied**: Application submitted to the employer
- **Interview**: Interview scheduled or completed
- **Offer**: Job offer received
- **Accepted**: Offer accepted and onboarding in progress
- **Declined**: You declined an offer after considering it
- **Rejected**: Employer rejected the application

### Updating Application Status

**Individual Update:**
1. Click on an application
2. Click **Change Status**
3. Select new status
4. Add notes (optional)
5. Save changes

**Bulk Update:**
1. Select multiple applications using checkboxes
2. Click **Bulk Actions** at the bottom
3. Select **Change Status**
4. Choose new status
5. Confirm changes

### Kanban Board View

Switch to Kanban view for visual tracking:

1. Click **Kanban View** toggle
2. Drag and drop cards between columns
3. Status updates automatically
4. Organize by application stage

### Application Timeline

View your application history:
1. Click on an application
2. Navigate to **Timeline** tab
3. See all status changes and notes
4. Add timeline entries manually

### Importing Historical Applications

Bring past job search data into Career Copilot so analytics stay complete:

1. Go to **Data Import** from the sidebar or the **Applications** page overflow menu.
2. Upload a CSV or XLSX file that includes at least company, title, and status columns.
3. Map columns to the template preview; optional fields (salary, source, links) can be matched as well.
4. Enable **Auto-deduplicate** to prevent duplicates using our MinHash fingerprinting.
5. Preview the parsed rows and click **Import**. Progress appears in the Bulk Operations tray and notifications feed.

### Exporting Application Records

Share summaries with mentors or keep personal archives:

1. From **Applications**, **Analytics**, or **Settings → Data**, click **Export**.
2. Choose CSV, XLSX, or PDF. Filters currently applied carry over to the export.
3. Optionally password-protect PDF exports for external sharing.
4. Track export jobs in the Bulk Operations tray; files remain available for download for 24 hours.

### Reminders & Follow-ups

- Use the **Follow-up Date** field on each application to schedule nudges; reminders surface via notifications and email digests.
- Toggle **Auto reminders** in **Settings → Notifications** to receive smart suggestions (e.g., “follow up 7 days after interview”).
- Add timeline notes after every interview or recruiter sync so AI recommendations can surface context-aware guidance.


## AI-Powered Tools

### Content Generation Workspace

Open **Content Generation** from the sidebar to access all AI writing helpers in one place. The workspace lets you:
- Select a template (Cover Letter, Resume Tailoring, Outreach Email, Follow-up, Networking Ping).
- Provide context such as target job, tone, and key wins to highlight.
- Preview multiple drafts and pin your favorite before exporting to DOCX or copying to clipboard.
- View previous generations in the right-hand history rail so you can reuse content later.

### AI Resume Generation

Create tailored resumes for specific jobs:

1. Navigate to a job listing
2. Click **Generate Resume**
3. AI analyzes the job requirements
4. Resume is optimized with:
   - Relevant skills highlighted
   - Experience tailored to job
   - Keywords from job description
   - ATS-friendly formatting
5. Review and edit the generated resume
6. Download as PDF or DOCX

Tips:
- Use the **Focus Areas** toggle to emphasize leadership, technical depth, or cross-functional collaboration.
- Switch to another language (English, German, French, Spanish) from the toolbar if you are applying to multilingual roles.

### AI Cover Letter Generation

Create personalized cover letters:

1. Navigate to a job listing
2. Click **Generate Cover Letter**
3. AI creates a cover letter highlighting:
   - Your relevant experience
   - Why you're a good fit
   - Your enthusiasm for the role
4. Review and customize
5. Download or copy to clipboard

You can add interview notes or recruiter preferences before generating so the AI can reference specific talking points.

### AI Outreach Emails

1. From **Content Generation**, choose **Outreach / Email**.
2. Select the scenario (cold outreach, recruiter follow-up, thank you, negotiation) and desired tone.
3. Include optional data such as hiring manager name, timeline, or specific company wins.
4. Generate, edit inline with markdown, and sync to your clipboard.
5. Save the email to the application timeline for future reference.

### Skills Gap Analysis

Identify skills to develop:

1. Navigate to **Profile** > **Skills**
2. Click **Analyze Skills Gap**
3. AI compares your skills with:
   - Job market demands
   - Your target roles
   - Industry trends
4. Get recommendations for:
   - Skills to learn
   - Courses and resources
   - Priority order

### Interview Preparation

Prepare for interviews with AI assistance:

1. Navigate to an application
2. Click **Prepare for Interview**
3. Get AI-generated:
   - Common interview questions
   - Suggested answers based on your experience
   - Company research summary
   - Questions to ask the interviewer

### Interview Practice Simulator

1. Navigate to **Interview Practice** from the sidebar or the Applications page quick links.
2. Pick a template (Behavioral, System Design, Product Sense, Culture Add) or create your own question set.
3. Start a timed session; each prompt includes guidance on what reviewers expect.
4. Record audio or jot bullet responses, then let the AI provide feedback on clarity, structure, and confidence.
5. Save sessions to the application timeline to track improvement over time.

## Analytics & Insights

### Application Analytics

Track your job search performance:

1. **Application Status Distribution**
   - Pie chart showing status breakdown
   - Click segments to filter applications

2. **Application Timeline**
   - Line chart showing applications over time
   - Identify trends and patterns

3. **Success Rate Funnel**
   - Conversion rates at each stage
   - Applied → Screening → Interview → Offer

4. **Response Time Analysis**
   - Average time to hear back
   - By company, role, or industry

### Market Insights

Understand the job market:

1. **Salary Distribution**
   - Salary ranges for your target roles
   - Compare by location and experience

2. **Skills Demand**
   - Most in-demand skills
   - Compare with your skill set
   - Identify gaps and opportunities

3. **Company Insights**
   - Top hiring companies
   - Application success rates by company
   - Average interview process length

### Exporting Data

Export your data for external analysis:

1. Navigate to any data view
2. Click **Export** dropdown
3. Choose format:
   - **CSV**: For spreadsheet analysis
   - **PDF**: For reports and presentations
   - **JSON**: For data backup
4. Select data range
5. Download file


## Notifications & Collaboration

### Notification Center

- Open the bell icon in the top nav or navigate to **Notifications**.
- Use tabs to switch between **All**, **Applications**, **Recommendations**, and **System** events.
- Real-time updates stream through websockets; when offline, queued events sync the next time you connect.
- Mark items as read individually or select **Mark All Read**.

### Email & Push Alerts

1. Head to **Settings → Notifications**.
2. Enable browser push, mobile push (if using the companion PWA), or email digests.
3. Configure quiet hours so alerts pause during focus time.
4. Daily or weekly digest emails summarize job recommendations, approaching deadlines, and follow-up reminders.

### Activity Feed & Sharing

- The **Social Activity** view highlights shared resumes, referrals, and wins from your network.
- Share a job or application update via **Share → Copy Link**; recipients can open a sanitized snapshot without signing in.
- Collaborative comments stay attached to the application timeline so mentors can review progress.

## Settings & Customization

### Profile Settings

Manage your profile information:

1. Navigate to **Settings** > **Profile**
2. Update:
   - Personal information
   - Job title and experience
   - Skills and expertise
   - Bio and summary
3. Click **Save Changes**

### Appearance Settings

Customize the look and feel:

1. Navigate to **Settings** > **Appearance**
2. Choose:
   - **Theme**: Light, Dark, or System
   - **UI Density**: Comfortable or Compact
   - **Language**: Select your preferred language
   - **Font Size**: Adjust for accessibility
3. Changes apply immediately

### Notification Settings

Control how you receive notifications:

1. Navigate to **Settings** > **Notifications**
2. Configure per category:
   - Job Alerts
   - Application Updates
   - Recommendations
   - System Notifications
3. Set email preferences:
   - Immediate
   - Daily digest
   - Off
4. Enable/disable:
   - Browser push notifications
   - Sound notifications
   - Do Not Disturb schedule

### Privacy Settings

Manage your privacy preferences:

1. Navigate to **Settings** > **Privacy**
2. Configure:
   - Profile visibility
   - Search indexing
   - Data sharing preferences
   - Cookie preferences

### Account Settings

Manage your account:

1. Navigate to **Settings** > **Account**
2. Options:
   - Change password
   - Two-factor authentication (coming soon)
   - Connected accounts (LinkedIn, Google)
   - Active sessions
   - Log out all devices

### Data Management

Export or delete your data:

1. Navigate to **Settings** > **Data**
2. Options:
   - **Export All Data**: Download complete backup
   - **Delete Specific Data**: Remove applications, jobs, etc.
   - **Delete Account**: Permanently delete your account
     - Requires email confirmation
     - 30-day grace period before permanent deletion

### Data Sync & Offline Mode

1. Install the PWA (Chrome/Edge: **More Tools → Install App**) or add the site to your dock from Safari.
2. Toggle **Offline Mode** in **Settings → Data** to enable background sync and caching.
3. When offline, the app shows an **Offline** banner; you can continue adding notes or drafting applications.
4. Click **Sync Now** after reconnecting to push queued changes and refresh analytics.
5. Conflicts are highlighted in the timeline so you can choose which version to keep.

## Tips & Best Practices

### Job Search Tips

1. **Set Up Saved Searches**
   - Create searches for your target roles
   - Enable email alerts for new matches
   - Review daily for best results

2. **Use Advanced Filters**
   - Narrow down results with specific criteria
   - Save time by filtering out irrelevant jobs
   - Combine multiple filters for precision

3. **Leverage AI Tools**
   - Generate tailored resumes for each application
   - Use AI cover letters as a starting point
   - Customize AI-generated content to add personal touch

4. **Track Everything**
   - Log all applications, even informal ones
   - Add notes about each application
   - Set reminders for follow-ups

### Application Management Tips

1. **Update Status Promptly**
   - Keep application statuses current
   - Add notes about interviews and feedback
   - Track rejection reasons to improve

2. **Use Bulk Operations**
   - Update multiple applications at once
   - Archive old applications periodically
   - Export data for external tracking

3. **Review Analytics Regularly**
   - Identify patterns in your applications
   - Adjust strategy based on success rates
   - Focus on high-performing channels

4. **Follow Up Strategically**
   - Set reminders for follow-ups
   - Wait 1-2 weeks after applying
   - Be polite and professional

### Productivity Tips

1. **Master Keyboard Shortcuts**
   - Use `⌘K` for quick navigation
   - Learn common shortcuts
   - View all shortcuts with `⌘/`

2. **Customize Your Dashboard**
   - Arrange widgets for your workflow
   - Hide unused widgets
   - Focus on actionable metrics

3. **Use the Command Palette**
   - Fastest way to navigate
   - Search for jobs and applications
   - Execute actions quickly

4. **Enable Notifications**
   - Get instant updates on applications
   - Receive job recommendations
   - Never miss an interview

### Interview Preparation Tips

1. **Research the Company**
   - Use AI-generated company summaries
   - Review recent news and updates
   - Understand company culture

2. **Practice Common Questions**
   - Use AI-generated interview questions
   - Practice answers out loud
   - Prepare specific examples

3. **Prepare Questions**
   - Ask about role expectations
   - Inquire about team structure
   - Discuss growth opportunities

4. **Follow Up After Interviews**
   - Send thank-you email within 24 hours
   - Reference specific discussion points
   - Reiterate your interest


## Troubleshooting

### Common Issues

#### Can't Log In

1. Check your email and password
2. Try password reset if needed
3. Clear browser cache and cookies
4. Try a different browser
5. Contact support if issue persists

#### Jobs Not Loading

1. Check your internet connection
2. Refresh the page
3. Clear browser cache
4. Try disabling browser extensions
5. Check if API is accessible at `/api/health`

#### Application Not Saving

1. Check all required fields are filled
2. Ensure file uploads are under size limit
3. Check internet connection
4. Try again in a few minutes
5. Export data as backup

#### Notifications Not Working

1. Check notification settings
2. Enable browser notifications
3. Check Do Not Disturb settings
4. Verify email settings
5. Check spam folder for emails

#### Slow Performance

1. Clear browser cache
2. Close unnecessary tabs
3. Disable browser extensions
4. Check internet speed
5. Try a different browser

### Getting Help

If you encounter issues not covered here:

1. **Check Documentation**
   - [Installation Guide](setup/INSTALLATION.md)
   - [API Documentation](api/API.md)
   - [Troubleshooting Guide](troubleshooting/COMMON_ISSUES.md)

2. **Search Issues**
   - Check [GitHub Issues](https://github.com/moatasim-KT/career-copilot/issues)
   - Search for similar problems
   - Review closed issues for solutions

3. **Ask for Help**
   - Open a [GitHub Discussion](https://github.com/moatasim-KT/career-copilot/discussions)
   - Provide detailed information:
     - What you were trying to do
     - What happened instead
     - Error messages (if any)
     - Browser and OS information
     - Screenshots (if applicable)

4. **Report Bugs**
   - Open a [GitHub Issue](https://github.com/moatasim-KT/career-copilot/issues/new)
   - Use the bug report template
   - Include steps to reproduce
   - Attach relevant logs or screenshots

5. **Contact Support**
   - Email: moatasimfarooque@gmail.com
   - Include your user ID and issue details
   - Allow 24-48 hours for response

## Additional Resources

- [Developer Guide](DEVELOPER_GUIDE.md) - For technical details
- [API Documentation](api/API.md) - API reference
- [Deployment Guide](deployment/DEPLOYMENT.md) - Self-hosting instructions
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute

---

**Need more help?** Join our community or contact support at moatasimfarooque@gmail.com

Happy job hunting! 🚀
