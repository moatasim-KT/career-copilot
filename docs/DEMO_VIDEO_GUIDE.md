# Demo Video Creation Guide

**Quick Links**: [[career-copilot/README|Project README]] | [[docs/index|Documentation Hub]] | [[USER_GUIDE]] | [[DEVELOPER_GUIDE]]

**Related**:
- [[LOCAL_SETUP]] - Setup for demo recording
- [[FRONTEND_QUICK_START]] - Frontend demo
- [[PROJECT_STATUS]] - Current features to demo
- [[ARCHITECTURE]] - System architecture for technical demo

This guide provides instructions for recording demonstration videos for Career Copilot.

## Overview

Demo videos help users understand the application's features and how to use them effectively. We need two types of videos:

1. **Application Demo Video** (3-5 minutes) - Overview of key features
2. **Developer Setup Video** (5-10 minutes) - How to set up the development environment

## Equipment & Software

### Recording Software

**Recommended Options:**
- **macOS**: QuickTime Player (built-in) or ScreenFlow
- **Windows**: OBS Studio (free) or Camtasia
- **Linux**: SimpleScreenRecorder or OBS Studio
- **Cross-platform**: Loom (web-based, easy to use)

### Audio

- Use a good quality microphone (USB microphone recommended)
- Record in a quiet environment
- Test audio levels before recording

### Screen Resolution

- Record at 1920x1080 (1080p) for best quality
- Ensure UI elements are clearly visible
- Use zoom/highlight features for small details

## Application Demo Video Script

### Duration: 3-5 minutes

#### 1. Introduction (30 seconds)

```
"Welcome to Career Copilot, an AI-powered career management platform 
designed to streamline your job search process. In this demo, I'll show 
you the key features that make Career Copilot your ultimate job search companion."
```

**Show:**
- Landing page
- Quick overview of the interface

#### 2. Dashboard Overview (45 seconds)

```
"The dashboard gives you a complete overview of your job search progress. 
You can see your application statistics, upcoming interviews, and 
personalized job recommendations all in one place."
```

**Show:**
- Dashboard with stats
- Application status chart
- Recent activity
- Job recommendations

#### 3. Job Search & Discovery (60 seconds)

```
"Finding the right job is easy with our advanced search features. 
You can search across multiple job boards, apply filters, and save 
searches for future use. The command palette (⌘K) provides instant 
access to any feature."
```

**Show:**
- Job search interface
- Apply filters (location, salary, remote)
- Advanced search with AND/OR logic
- Save a search
- Command palette (⌘K)

#### 4. AI-Powered Tools (60 seconds)

```
"Career Copilot's AI features help you stand out. Generate tailored 
resumes and cover letters optimized for specific job postings. The AI 
analyzes job requirements and highlights your relevant experience."
```

**Show:**
- Select a job
- Click "Generate Resume"
- Show AI-generated resume
- Click "Generate Cover Letter"
- Show AI-generated cover letter

#### 5. Application Tracking (45 seconds)

```
"Track all your applications in one place. Update statuses, add notes, 
and visualize your progress with the Kanban board view. Bulk operations 
make managing multiple applications effortless."
```

**Show:**
- Applications list
- Update application status
- Switch to Kanban view
- Drag and drop card
- Bulk select and update

#### 6. Analytics & Insights (30 seconds)

```
"Gain insights into your job search with interactive analytics. Track 
your success rate, identify trends, and understand market demands."
```

**Show:**
- Analytics dashboard
- Application status chart
- Timeline chart
- Skills demand chart

#### 7. Closing (30 seconds)

```
"Career Copilot combines powerful AI tools with intuitive design to 
make your job search more efficient and successful. Get started today 
and take control of your career journey."
```

**Show:**
- Quick recap of features
- Call to action (GitHub link, website)

## Developer Setup Video Script

### Duration: 5-10 minutes

#### 1. Introduction (30 seconds)

```
"In this video, I'll walk you through setting up Career Copilot for 
local development. We'll cover both Docker and manual setup options."
```

#### 2. Prerequisites (60 seconds)

```
"Before we begin, make sure you have the following installed:
- Docker and Docker Compose (recommended)
- OR Python 3.11+, Node.js 18+, PostgreSQL 14+, and Redis 7+
- Git for cloning the repository
- A code editor like VS Code"
```

**Show:**
- Check versions: `docker --version`, `python --version`, `node --version`

#### 3. Clone Repository (30 seconds)

```
"First, clone the repository from GitHub."
```

**Show:**
```bash
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot
```

#### 4. Docker Setup (2 minutes)

```
"The easiest way to get started is with Docker. Copy the environment 
files and add your API keys."
```

**Show:**
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit .env files (show in editor)
# Add OPENAI_API_KEY or ANTHROPIC_API_KEY

docker-compose up -d
docker-compose exec backend alembic upgrade head
```

**Show:**
- Services starting
- Access frontend at http://localhost:3000
- Access backend at http://localhost:8000/docs

#### 5. Manual Setup - Backend (2 minutes)

```
"For manual setup, let's start with the backend."
```

**Show:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env
alembic upgrade head
uvicorn app.main:app --reload
```

#### 6. Manual Setup - Frontend (2 minutes)

```
"Now let's set up the frontend."
```

**Show:**
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local
npm run dev
```

#### 7. Verification (60 seconds)

```
"Let's verify everything is working correctly."
```

**Show:**
- Open http://localhost:3000
- Navigate through the app
- Check API docs at http://localhost:8000/docs
- Run a test API call

#### 8. Development Workflow (60 seconds)

```
"Here's a quick overview of the development workflow."
```

**Show:**
- Make a code change
- Hot reload demonstration
- Run tests: `pytest` and `npm test`
- Check linting: `npm run lint`

#### 9. Troubleshooting (60 seconds)

```
"If you encounter issues, check the troubleshooting guide in the docs. 
Common issues include port conflicts, missing environment variables, 
and database connection errors."
```

**Show:**
- Check logs: `docker-compose logs`
- Common error examples
- Link to troubleshooting guide

#### 10. Closing (30 seconds)

```
"You're now ready to start developing! Check out the contributing guide 
for code style guidelines and best practices. Happy coding!"
```

## Recording Tips

### Before Recording

1. **Prepare Your Environment**
   - Close unnecessary applications
   - Clear browser history and cache
   - Use a clean database with demo data
   - Disable notifications
   - Hide personal information

2. **Test Run**
   - Do a complete dry run
   - Time each section
   - Identify any issues

3. **Script**
   - Write a detailed script
   - Practice speaking naturally
   - Keep it conversational

### During Recording

1. **Speak Clearly**
   - Speak at a moderate pace
   - Pause between sections
   - Avoid filler words ("um", "uh")

2. **Mouse Movement**
   - Move mouse slowly and deliberately
   - Highlight important elements
   - Use cursor highlighting if available

3. **Pacing**
   - Don't rush
   - Allow time for viewers to see what you're doing
   - Pause after important actions

4. **Mistakes**
   - Don't worry about small mistakes
   - Pause and restart the section if needed
   - Edit out mistakes in post-production

### After Recording

1. **Edit**
   - Remove long pauses
   - Add transitions between sections
   - Add text overlays for important points
   - Add background music (optional, keep it subtle)

2. **Add Captions**
   - Add closed captions for accessibility
   - Use YouTube's auto-caption feature and edit
   - Or use a service like Rev.com

3. **Export**
   - Export at 1080p (1920x1080)
   - Use H.264 codec
   - Target bitrate: 8-10 Mbps

## Publishing

### YouTube

1. **Upload Video**
   - Title: "Career Copilot - Application Demo" or "Career Copilot - Developer Setup"
   - Description: Include links to GitHub, docs, and website
   - Tags: career management, job search, AI, open source

2. **Thumbnail**
   - Create custom thumbnail (1280x720)
   - Include app logo and title
   - Use high contrast colors

3. **Playlist**
   - Create "Career Copilot Tutorials" playlist
   - Add both videos

### Embedding

Add video links to documentation:

```markdown
## Demo Videos

### Application Demo
[![Application Demo](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)

### Developer Setup
[![Developer Setup](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)
```

## Video Checklist

### Application Demo Video
- [ ] Introduction and overview
- [ ] Dashboard walkthrough
- [ ] Job search demonstration
- [ ] AI tools demonstration
- [ ] Application tracking
- [ ] Analytics overview
- [ ] Closing and call to action
- [ ] Edited and polished
- [ ] Captions added
- [ ] Uploaded to YouTube
- [ ] Linked in README

### Developer Setup Video
- [ ] Introduction
- [ ] Prerequisites check
- [ ] Repository clone
- [ ] Docker setup
- [ ] Manual setup (backend)
- [ ] Manual setup (frontend)
- [ ] Verification
- [ ] Development workflow
- [ ] Troubleshooting tips
- [ ] Closing
- [ ] Edited and polished
- [ ] Captions added
- [ ] Uploaded to YouTube
- [ ] Linked in README and docs

## Resources

- **Screen Recording**: [OBS Studio](https://obsproject.com/), [Loom](https://www.loom.com/)
- **Video Editing**: [DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve) (free), [iMovie](https://www.apple.com/imovie/) (Mac)
- **Captions**: [YouTube Auto-Captions](https://support.google.com/youtube/answer/6373554), [Rev.com](https://www.rev.com/)
- **Thumbnails**: [Canva](https://www.canva.com/), [Figma](https://www.figma.com/)
- **Music**: [YouTube Audio Library](https://www.youtube.com/audiolibrary), [Incompetech](https://incompetech.com/)

## Contact

For questions about recording demo videos:
- Email: moatasimfarooque@gmail.com
- GitHub Issues: [Report issues](https://github.com/moatasim-KT/career-copilot/issues)

---

**Note**: Demo videos should be updated whenever major features are added or the UI significantly changes.
