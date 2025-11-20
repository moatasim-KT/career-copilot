# AI & Integration Services Architecture

> **Consolidated Guide**: AI components, prompt engineering, and job board integrations.
> - Formerly: `AI_COMPONENTS_REVIEW.md`, `PROMPT_ENGINEERING_GUIDE.md`, `job-services-architecture.md`

**Quick Links**: [[/architecture/README|Architecture Hub]] | [[/GETTING_STARTED#free-api-setup-optional|Free API Setup]] | [[/integrations/README|Integrations Hub]]

---

## Table of Contents

1. [AI/LLM Architecture](#aillm-architecture)
2. [Prompt Engineering](#prompt-engineering)
3. [Job Board Integrations](#job-board-integrations)
4. [Integration Patterns](#integration-patterns)

---

## AI/LLM Architecture

### Multi-Provider LLM Support

Career Copilot supports multiple LLM providers with automatic fallback:

**Supported Providers**:
- **Groq** (Primary, Free Tier) - 14,400 requests/day
- **OpenAI GPT-4/GPT-3.5** (Optional, Paid)
- **Anthropic Claude** (Optional, Paid)

### LLM Service Architecture

```python
# backend/app/services/llm_service.py
class LLMService:
    """Multi-provider LLM service with automatic fallback."""
    
    def __init__(self):
        self.groq_client = GroqClient() if GROQ_API_KEY else None
        self.openai_client = OpenAIClient() if OPENAI_API_KEY else None
        self.claude_client = ClaudeClient() if ANTHROPIC_API_KEY else None
        
    async def generate(self, prompt: str, provider: str = "auto"):
        """Generate completion with automatic fallback."""
        if provider == "auto":
            # Try providers in order: Groq → OpenAI → Claude
            for client in [self.groq_client, self.openai_client, self.claude_client]:
                if client:
                    try:
                        return await client.generate(prompt)
                    except Exception as e:
                        logger.warning(f"Provider failed: {e}, trying next...")
                        continue
        else:
            # Use specific provider
            return await self._get_provider(provider).generate(prompt)
```

### Provider Comparison

| Provider | Strengths | Optimal Tasks | Cost/1K Tokens |
|----------|-----------|---------------|----------------|
| **Groq Mixtral** | Ultra-fast inference | Real-time, communication | Free (14.4K/day) |
| **Groq Llama2** | Balanced performance | General tasks | Free (14.4K/day) |
| **GPT-4** | Complex reasoning | Analysis, risk assessment | $0.03 |
| **GPT-3.5 Turbo** | Speed, cost-efficiency | Simple tasks | $0.002 |
| **Claude 3** | Long context, safety | Document analysis | $0.015 |

### Quota Management

```python
# backend/app/services/quota_manager.py
class QuotaManager:
    """Manages API quotas and automatic fallback."""
    
    async def check_quota(self, provider: str) -> bool:
        """Check if provider has quota remaining."""
        usage = await self.get_usage(provider)
        limit = self.get_limit(provider)
        return usage < limit
    
    async def get_available_provider(self) -> str:
        """Get first available provider with quota."""
        for provider in ["groq", "openai", "anthropic"]:
            if await self.check_quota(provider):
                return provider
        raise QuotaExceededError("All providers exhausted")
```

---

## Prompt Engineering

### Core Principles

1. **Task-Aware Design** - Prompts tailored to specific use cases
2. **Token Budget Management** - Optimize for cost and quality
3. **Provider-Specific Optimization** - Leverage provider strengths
4. **Quality Assurance** - Validate outputs systematically

### Token Optimization Strategies

#### Conservative (Quality First)
- **Use Case**: Complex analysis, critical content
- **Techniques**: Whitespace removal only
- **Quality Retention**: 98-100%
- **Token Reduction**: 5-10%

#### Balanced (Default)
- **Use Case**: Most production scenarios
- **Techniques**: Whitespace removal, redundancy elimination, selective abbreviations
- **Quality Retention**: 85-95%
- **Token Reduction**: 15-25%

#### Aggressive (Cost First)
- **Use Case**: Simple tasks, high volume
- **Techniques**: Strong abbreviation, content summarization
- **Quality Retention**: 70-85%
- **Token Reduction**: 30-50%

### Prompt Templates

**Cover Letter Generation**:
```python
COVER_LETTER_PROMPT = """
Generate a professional cover letter for:

Job Title: {job_title}
Company: {company}
Job Description: {job_description}

Candidate Profile:
- Experience: {experience_level}
- Skills: {skills}
- Background: {background}

Requirements:
- Professional tone
- Highlight relevant experience
- Match job requirements
- 250-350 words
"""
```

**Resume Optimization**:
```python
RESUME_OPTIMIZATION_PROMPT = """
Analyze resume and suggest improvements:

Resume: {resume_text}
Target Job: {job_description}

Provide:
1. Keyword optimization suggestions
2. Skills to emphasize
3. Experience gaps to address
4. ATS compatibility score
"""
```

**Skill Gap Analysis**:
```python
SKILL_GAP_PROMPT = """
Compare candidate skills vs. job requirements:

Candidate Skills: {candidate_skills}
Job Requirements: {job_requirements}

Output JSON:
{
  "matching_skills": [],
  "missing_skills": [],
  "development_recommendations": [],
  "proficiency_gaps": {}
}
"""
```

---

## Job Board Integrations

### Integration Architecture

Career Copilot integrates with 12+ job boards through two methods:

1. **API Integrations** (5 free APIs)
2. **Web Scraping** (9 job boards)

### API Integrations

#### 1. Adzuna API
- **Coverage**: 22 countries
- **Limit**: 1,000 calls/month (free)
- **Data Quality**: Excellent
- **Setup**: [[/GETTING_STARTED#free-api-setup-optional|Getting Started Guide]]

```python
# backend/app/scrapers/job_boards/adzuna.py
class AdzunaAPI:
    async def search_jobs(
        self,
        query: str,
        location: str,
        country: str = "de"
    ) -> List[JobPosting]:
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": query,
            "where": location,
            "results_per_page": 50
        }
        # ... API call and parsing
```

#### 2. RapidAPI JSearch
- **Coverage**: Aggregates Google Jobs, LinkedIn, Indeed
- **Limit**: 1,000 requests/month (free)
- **Data Quality**: Very good
- **Setup**: [[/GETTING_STARTED#free-api-setup-optional|Getting Started Guide]]

#### 3-5. Public APIs (No Signup)
- **The Muse**: 500/hour, curated jobs
- **Remotive**: Unlimited, remote jobs only
- **RemoteOK**: Unlimited, 100k+ remote jobs

### Web Scraping

**Supported Job Boards**:
- LinkedIn (dynamic scraping)
- Indeed (pagination support)
- StepStone (Germany-focused)
- Monster (global coverage)
- Glassdoor (company-focused)
- WeWorkRemotely (remote jobs)
- AngelList (startups)
- Arbeitnow (Germany/Europe)
- Berlin Startup Jobs

**Scraping Architecture**:
```python
# backend/app/services/job_scraping_service.py
class JobScrapingService:
    def __init__(self):
        self.scrapers = {
            "linkedin": LinkedInScraper(),
            "indeed": IndeedScraper(),
            "stepstone": StepStoneScraper(),
            # ... other scrapers
        }
    
    async def scrape_all_sources(
        self,
        query: str,
        location: str,
        max_results: int = 100
    ) -> List[JobPosting]:
        """Scrape allconfigured job boards in parallel."""
        tasks = [
            scraper.search(query, location, max_results)
            for scraper in self.scrapers.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._deduplicate(results)
```

### Deduplication Strategy

**MinHash + Jaccard Similarity**:
```python
# backend/app/services/job_deduplication_service.py
class JobDeduplicationService:
    def calculate_similarity(
        self,
        job1: JobPosting,
        job2: JobPosting
    ) -> float:
        """Calculate similarity using MinHash + Jaccard."""
        # Combine title, company, location, description
        text1 = f"{job1.title} {job1.company} {job1.description}"
        text2 = f"{job2.title} {job2.company} {job2.description}"
        
        # Create MinHash signatures
        minhash1 = self._create_minhash(text1)
        minhash2 = self._create_minhash(text2)
        
        # Calculate Jaccard similarity
        return minhash1.jaccard(minhash2)
    
    def is_duplicate(
        self,
        job1: JobPosting,
        job2: JobPosting,
        threshold: float = 0.85
    ) -> bool:
        """Check if two jobs are duplicates."""
        similarity = self.calculate_similarity(job1, job2)
        return similarity >= threshold
```

---

## Integration Patterns

### Data Schema Mapping

See [[/integrations/DATA_SCHEMA_MAPPING|Data Schema Mapping]] for detailed field mapping between job boards.

**Standard Job Schema**:
```python
class JobPosting(BaseModel):
    title: str
    company: str
    location: str
    description: str
    url: str
    posted_date: Optional[datetime]
    salary_min: Optional[int]
    salary_max: Optional[int]
    employment_type: Optional[str]  # full-time, part-time, contract
    seniority_level: Optional[str]  # entry, mid, senior
    skills: List[str]
    source: str  # e.g., "linkedin", "adzuna"
    source_id: str  # Original ID from source
```

### Rate Limiting

```python
# backend/app/services/rate_limiter.py
class RateLimiter:
    async def check_rate_limit(self, source: str) -> bool:
        """Check if source can be queried."""
        key = f"rate_limit:{source}"
        count = await redis.get(key)
        limit = self.get_limit(source)
        
        if count and int(count) >= limit:
            return False
        
        await redis.incr(key)
        await redis.expire(key, 60)  # 1 minute window
        return True
```

### Error Handling

```python
class JobBoardError(Exception):
    """Base exception for job board errors."""
    pass

class RateLimitError(JobBoardError):
    """Rate limit exceeded."""
    pass

class AuthenticationError(JobBoardError):
    """API authentication failed."""
    pass

class ParseError(JobBoardError):
    """Failed to parse job data."""
    pass
```

---

## Related Documentation

- **Getting Started**: [[/GETTING_STARTED#free-api-setup-optional|Free API Setup]]
- **Architecture**: [[/architecture/README|Architecture Hub]]
- **Integrations**: [[/integrations/README|Integration Guides]]
- **Development**: [[/DEVELOPER_GUIDE|Developer Guide]]

---

**Last Updated**: November 2025
