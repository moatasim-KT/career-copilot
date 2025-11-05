# EU Job Scraper Role Targeting Guide

## Overview
All EU job scrapers are configured to search for **tech roles** with a focus on companies that hire international talent and offer visa sponsorship.

## 🎯 What Roles Are We Searching For?

### Data Science & Analytics (Primary Focus)
1. **Data Scientist**
   - Job titles: "Data Scientist", "Machine Learning Engineer", "ML Engineer", "Applied Scientist", "Research Scientist"
   - Keywords: data science, machine learning, ML, AI, statistics, python
   - Skills: Python, R, SQL, TensorFlow, PyTorch, Scikit-learn
   - Levels: Junior, Mid-level, Senior, Lead, Principal

2. **Data Analyst**
   - Job titles: "Data Analyst", "Business Intelligence Analyst", "Analytics Engineer", "BI Developer"
   - Keywords: data analysis, business intelligence, BI, analytics, SQL
   - Skills: SQL, Python, Tableau, Power BI, Excel, Data Visualization
   - Levels: Junior, Mid-level, Senior

3. **Data Engineer**
   - Job titles: "Data Engineer", "Big Data Engineer", "Data Platform Engineer", "ETL Developer"
   - Keywords: data engineering, ETL, big data, data pipeline, spark
   - Skills: Python, SQL, Spark, Airflow, Kafka, AWS, GCP
   - Levels: Junior, Mid-level, Senior, Lead

### Software Engineering
4. **Backend Engineer**
   - Job titles: "Backend Engineer", "Backend Developer", "Server-Side Engineer", "API Developer"
   - Keywords: backend, server-side, API, microservices, REST
   - Skills: Python, Java, Go, Node.js, PostgreSQL, MongoDB, Docker
   - Levels: Junior, Mid-level, Senior, Lead, Staff

5. **Frontend Engineer**
   - Job titles: "Frontend Engineer", "Frontend Developer", "UI Engineer", "React Developer"
   - Keywords: frontend, react, vue, angular, typescript, javascript
   - Skills: React, TypeScript, JavaScript, CSS, HTML, Next.js
   - Levels: Junior, Mid-level, Senior, Lead

6. **Full Stack Engineer**
   - Job titles: "Full Stack Engineer", "Full Stack Developer", "Fullstack Developer"
   - Keywords: full stack, fullstack, full-stack, web development
   - Skills: React, Node.js, Python, TypeScript, PostgreSQL, AWS
   - Levels: Mid-level, Senior, Lead

7. **Mobile Engineer**
   - Job titles: "Mobile Engineer", "iOS Developer", "Android Developer", "React Native Developer"
   - Keywords: mobile, iOS, android, react native, flutter
   - Skills: Swift, Kotlin, React Native, Flutter, Mobile Development
   - Levels: Junior, Mid-level, Senior, Lead

### AI & Machine Learning
8. **Machine Learning Engineer**
   - Job titles: "Machine Learning Engineer", "ML Engineer", "AI Engineer", "Deep Learning Engineer"
   - Keywords: machine learning, ML, AI, deep learning, neural networks
   - Skills: Python, TensorFlow, PyTorch, Keras, MLOps, Cloud ML
   - Levels: Mid-level, Senior, Lead, Staff

9. **AI Researcher**
   - Job titles: "AI Researcher", "Research Scientist", "ML Researcher", "Applied Scientist"
   - Keywords: research, AI, machine learning, NLP, computer vision
   - Skills: Python, PyTorch, TensorFlow, Research, Publications
   - Levels: PhD, Postdoc, Senior, Principal

10. **MLOps Engineer**
    - Job titles: "MLOps Engineer", "ML Platform Engineer", "ML Infrastructure Engineer"
    - Keywords: MLOps, ML infrastructure, ML platform, deployment
    - Skills: Python, Kubernetes, Docker, Kubeflow, MLflow, AWS/GCP
    - Levels: Mid-level, Senior, Lead

### DevOps & Infrastructure
11. **DevOps Engineer**
    - Job titles: "DevOps Engineer", "Site Reliability Engineer", "SRE", "Platform Engineer"
    - Keywords: DevOps, SRE, infrastructure, kubernetes, docker
    - Skills: Kubernetes, Docker, Terraform, AWS/GCP, CI/CD, Python
    - Levels: Junior, Mid-level, Senior, Lead, Staff

12. **Cloud Engineer**
    - Job titles: "Cloud Engineer", "Cloud Architect", "AWS Engineer", "Azure Engineer"
    - Keywords: cloud, AWS, Azure, GCP, cloud architecture
    - Skills: AWS, Azure, GCP, Terraform, CloudFormation, Kubernetes
    - Levels: Mid-level, Senior, Lead, Architect

### Product & Design
13. **Product Manager**
    - Job titles: "Product Manager", "Technical Product Manager", "Senior Product Manager"
    - Keywords: product management, product strategy, roadmap, user research
    - Skills: Product Strategy, Agile, Jira, SQL, Analytics
    - Levels: Associate, Mid-level, Senior, Lead, Director

14. **Product Designer**
    - Job titles: "Product Designer", "UX Designer", "UI/UX Designer", "Interaction Designer"
    - Keywords: product design, UX, UI, user experience, figma
    - Skills: Figma, Sketch, Adobe XD, User Research, Prototyping
    - Levels: Junior, Mid-level, Senior, Lead

### Security & QA
15. **Security Engineer**
    - Job titles: "Security Engineer", "Cybersecurity Engineer", "InfoSec Engineer", "Application Security Engineer"
    - Keywords: security, cybersecurity, infosec, penetration testing
    - Skills: Security, Penetration Testing, SIEM, Python, Vulnerability Assessment
    - Levels: Mid-level, Senior, Lead, Principal

16. **QA Engineer**
    - Job titles: "QA Engineer", "Test Engineer", "SDET", "Automation Engineer"
    - Keywords: QA, testing, automation, test automation, selenium
    - Skills: Selenium, Python, Java, Test Automation, CI/CD
    - Levels: Junior, Mid-level, Senior, Lead

---

## 📊 Scraper-Specific Role Configuration

### 1. RapidAPI JSearch (Indeed, LinkedIn, Glassdoor)
**Default Roles Searched:**
- Data Scientist
- ML Engineer
- Data Analyst
- Data Engineer
- Backend Engineer
- Full Stack Engineer
- DevOps Engineer

**Search Strategy:**
- Uses role title variations (e.g., "Data Scientist" OR "Machine Learning Engineer")
- Searches across 80+ EU cities in 15 countries
- Filters: FULLTIME employment, posted within last month
- Default country: Germany (can be changed per search)

**Example Queries:**
```
"Data Scientist in Berlin"
"ML Engineer in Amsterdam"
"Backend Engineer in Stockholm"
```

### 2. The Muse
**Role Categories Searched:**
1. Data Science
2. Data & Analytics
3. Engineering
4. Software Engineering
5. IT
6. Product Management
7. Design & UX
8. Research & Science
9. Analytics & Modeling
10. Machine Learning
11. Artificial Intelligence

**Search Strategy:**
- Auto-searches top 6 EU cities per request
- 28 EU locations configured
- Filters for tech categories
- Detects visa sponsorship mentions

**Example Multi-Location Search:**
Automatically searches: Berlin, Amsterdam, London, Paris, Stockholm, Dublin

### 3. Firecrawl (Company Career Pages)
**~100 Visa Sponsor Companies by Role:**

#### Data Science & ML Companies (40+):
- **Netherlands**: Booking.com (Data, ML, Analytics), Adyen (Data Science, ML)
- **Germany**: Zalando (Data Science, ML), N26 (Data, Analytics), AUTO1 (Data Engineering)
- **UK**: DeepMind (AI Research, ML), Babylon Health (Data Science, ML)
- **Sweden**: Spotify (Data Science, ML, Analytics)
- **Switzerland**: Google Zurich (AI, ML, Research), Meta (AI Research)
- **Ireland**: Meta Dublin (Data Science, Analytics)
- **France**: Criteo (Data Science, ML)

#### Software Engineering Companies (50+):
- **Netherlands**: Elastic, bunq, MessageBird, Catawiki (Backend, Frontend, Full-stack)
- **Germany**: Siemens, BMW, Celonis, FlixBus (Software Engineering)
- **UK**: Revolut, Monzo, Deliveroo, Octopus Energy (Backend, Frontend, Mobile)
- **Sweden**: King, Klarna, iZettle (Gaming, Backend, Frontend)
- **Denmark**: Unity, Zendesk (Game Development, Full-stack)
- **Finland**: Supercell, Wolt (Game Dev, Backend, Frontend)

#### Cloud & DevOps Companies (30+):
- **Switzerland**: Google, Meta, Microsoft, DigitalOcean (Cloud, Platform, SRE)
- **Netherlands**: Elastic (Cloud, DevOps, SRE)
- **Germany**: FlixBus, AUTO1 (DevOps, Cloud)
- **UK**: Thought Machine, Improbable (Cloud, Infrastructure)

**Scraping Method:**
- Directly crawls company career pages
- Extracts all job listings
- Filters by configured role keywords
- Each company tagged with specific roles they hire for

### 4. Adzuna
**Default Search:**
- Category: IT jobs (auto-detected for tech roles)
- Countries: 25+ EU countries
- Default: Germany

**Role Detection:**
- Automatically filters for IT/Tech categories
- Searches by keywords matching all 16 role types
- 50 results per page
- Posted within last 30 days

### 5. Arbeitnow
**Focused on German Tech Hubs:**
- Berlin, Munich, Hamburg, Frankfurt, Stuttgart, Cologne

**High-Demand Skills Detected:**
- Python, JavaScript, TypeScript, React, Node.js
- AWS, Kubernetes, Docker
- PostgreSQL, MongoDB
- Machine Learning, Data Science

**Role Filtering:**
- Filters for tech/engineering roles
- Prioritizes jobs mentioning relocation or visa support
- Targets international opportunities

---

## 🌍 Geographic Coverage

### Countries (15 EU):
1. **Germany** 🇩🇪 - Primary focus (Berlin, Munich, Hamburg, Frankfurt, Stuttgart, Cologne)
2. **Netherlands** 🇳🇱 - (Amsterdam, Rotterdam, Utrecht, Eindhoven)
3. **United Kingdom** 🇬🇧 - (London, Manchester, Edinburgh, Cambridge)
4. **Sweden** 🇸🇪 - (Stockholm, Gothenburg, Malmö)
5. **France** 🇫🇷 - (Paris, Lyon, Toulouse)
6. **Switzerland** 🇨🇭 - (Zurich, Geneva, Basel)
7. **Denmark** 🇩🇰 - (Copenhagen, Aarhus)
8. **Norway** 🇳🇴 - (Oslo, Bergen)
9. **Finland** 🇫🇮 - (Helsinki, Espoo)
10. **Spain** 🇪🇸 - (Madrid, Barcelona, Valencia)
11. **Portugal** 🇵🇹 - (Lisbon, Porto)
12. **Italy** 🇮🇹 - (Milan, Rome, Turin)
13. **Ireland** 🇮🇪 - (Dublin, Cork)
14. **Poland** 🇵🇱 - (Warsaw, Krakow, Wroclaw)
15. **Austria** 🇦🇹 - (Vienna)

### Cities (40+):
See full list in each scraper configuration.

---

## 🎓 Seniority Levels Targeted

All roles search across multiple levels:
- **Junior/Entry-level**: 0-2 years experience
- **Mid-level**: 2-5 years experience
- **Senior**: 5-8 years experience
- **Lead**: 8-12 years experience
- **Staff/Principal**: 12+ years experience
- **Director/VP**: Leadership roles

---

## 🔍 How to Use Role Targeting

### Option 1: Use Default Roles
All scrapers automatically search for the most common tech roles:
```python
# Uses default roles: data_scientist, ml_engineer, data_analyst, etc.
await scraper.scrape_jobs(keywords="", location="Berlin")
```

### Option 2: Specify Specific Roles
```python
from backend.app.services.scraping.job_roles import JobRoles

# Search for specific role
keywords = JobRoles.get_search_query("data_scientist", "Berlin")
await scraper.scrape_jobs(keywords=keywords, location="")
```

### Option 3: Search Multiple Roles
```python
from backend.app.services.scraping.job_roles import get_role_combo

# Get all data roles
data_roles = get_role_combo("data_roles")
# Returns: ["data_scientist", "data_analyst", "data_engineer", "ml_engineer"]

# Search for each role
for role in data_roles:
    query = JobRoles.get_search_query(role, "Amsterdam")
    await scraper.scrape_jobs(keywords=query, location="")
```

### Option 4: Custom Keywords
```python
# Still works with custom keywords
await scraper.scrape_jobs(
    keywords="Senior Python Developer",
    location="Stockholm"
)
```

---

## 📈 Expected Results

### Job Volume by Role (Estimated):
- **Data Scientist**: 5,000+ jobs across EU
- **Software Engineer**: 15,000+ jobs across EU
- **ML Engineer**: 3,000+ jobs across EU
- **DevOps Engineer**: 4,000+ jobs across EU
- **Product Manager**: 2,000+ jobs across EU

### Visa Sponsorship Coverage:
- **~100 companies** explicitly known to sponsor visas
- **300K+ jobs** from Arbeitnow (Germany focus)
- **470K+ jobs** total across all scrapers
- **28 EU locations** explicitly configured
- **15 countries** with known visa programs

---

## 🛠️ Configuration Files

### Role Definitions:
```
backend/app/services/scraping/job_roles.py
```

### Scraper Configurations:
```
backend/app/services/scraping/rapidapi_jsearch_scraper.py
backend/app/services/scraping/themuse_scraper.py
backend/app/services/scraping/firecrawl_scraper.py
backend/app/services/scraping/adzuna_scraper.py
backend/app/services/scraping/arbeitnow_scraper.py
```

---

## 🎯 Next Steps

### To Expand Role Coverage:
1. Add new roles to `job_roles.py`
2. Add role to scraper's `DEFAULT_ROLES` list
3. Test with: `python -m pytest tests/test_eu_visa_sponsorship.py`

### To Add New Companies (Firecrawl):
1. Open `firecrawl_scraper.py`
2. Add company to `target_companies` list
3. Specify country, roles, and career page URL
4. Run verification test

### To Add New Locations:
1. Open respective scraper file
2. Add location to country/city mapping
3. Test search with new location

---

## 📝 Summary

**What roles?** 16 tech role categories from Data Science to QA Engineering

**Where?** 15 EU countries, 40+ cities, ~100 visa sponsor companies

**How many jobs?** 470,000+ jobs accessible across all scrapers

**Visa sponsorship?** Focused on companies with known visa programs and international hiring

**Default search?** Data Science, ML, Software Engineering, DevOps (most in-demand)

**Customizable?** Yes - can search any role/location combination
