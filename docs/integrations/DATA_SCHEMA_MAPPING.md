# Phase 3.3 - Data Schema Mapping Document

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

**Date**: November 17, 2025
**Version**: 1.0
**Status**: Planning Phase

---

## Overview

This document maps all new data fields from the 4 new job boards (XING, Welcome to the Jungle, AngelList, JobScout24) to the Career Copilot database schema. It includes field definitions, data types, transformation rules, and database migration scripts.

---

## New Database Fields Summary

| Field Name              | Type         | Source Boards    | Purpose                    |
| ----------------------- | ------------ | ---------------- | -------------------------- |
| `language_requirements` | TEXT[]       | XING, JobScout24 | Required languages for job |
| `experience_level`      | VARCHAR(50)  | XING, AngelList  | Junior, Mid, Senior, etc.  |
| `equity_range`          | VARCHAR(100) | AngelList        | Stock options range        |
| `tech_stack`            | TEXT[]       | WttJ, AngelList  | Technologies used          |
| `company_culture_tags`  | TEXT[]       | WttJ             | Culture keywords           |
| `funding_stage`         | VARCHAR(50)  | AngelList        | Seed, Series A, etc.       |
| `work_permit_info`      | TEXT         | JobScout24       | Visa/permit requirements   |
| `company_verified`      | BOOLEAN      | XING             | Official company account   |
| `company_videos`        | JSONB        | WttJ             | Video metadata             |
| `perks`                 | TEXT[]       | WttJ             | Benefits array             |
| `total_funding`         | BIGINT       | AngelList        | Total raised (USD cents)   |
| `investors`             | TEXT[]       | AngelList        | Investor names             |
| `workload_percentage`   | INTEGER      | JobScout24       | 80%, 100% (Swiss)          |
| `job_language`          | VARCHAR(5)   | All              | ISO 639-1 code             |

---

## Detailed Field Specifications

### 1. `language_requirements`

**Type**: `TEXT[]`
**Nullable**: Yes
**Default**: NULL
**Index**: No

**Purpose**: Store required languages for the job (e.g., "German (fluent)", "English (working)")

**Source Mapping**:
```yaml
XING:
  field: job.language_skills
  example: ["German (native)", "English (fluent)"]

JobScout24:
  field: job.languages
  example: ["Deutsch (fliessend)", "Englisch (Verhandlungssicher)"]
```

**Transformation Rules**:
```python
def normalize_language_requirements(languages: List[str]) -> List[str]:
    """Normalize language requirement strings."""
    normalized = []
    for lang in languages:
        # Extract language name and level
        # "German (fluent)" -> "German (Fluent)"
        normalized.append(lang.strip().title())
    return normalized
```

**Sample Values**:
- `["German (Native)", "English (Fluent)"]`
- `["French (Native)", "English (Working)"]`
- `["English (Fluent)"]`

---

### 2. `experience_level`

**Type**: `VARCHAR(50)`
**Nullable**: Yes
**Default**: NULL
**Index**: Yes (for filtering)

**Purpose**: Job seniority level

**Allowed Values**:
- `Internship`
- `Entry Level`
- `Junior`
- `Mid-Level`
- `Senior`
- `Lead`
- `Staff`
- `Principal`
- `Manager`
- `Director`
- `VP`
- `C-Level`

**Source Mapping**:
```yaml
XING:
  field: job.experience_level
  values: ["berufseinsteiger", "mit_berufserfahrung", "fuehrungskraft"]
  mapping:
    berufseinsteiger: "Entry Level"
    mit_berufserfahrung: "Mid-Level"
    fuehrungskraft: "Manager"

AngelList:
  field: job.experienceLevel
  values: ["intern", "junior", "mid", "senior", "lead", "staff"]
  mapping: Direct (capitalize)
```

**Transformation**:
```python
def map_experience_level(level: str, source: str) -> str:
    xing_map = {
        'berufseinsteiger': 'Entry Level',
        'mit_berufserfahrung': 'Mid-Level',
        'fuehrungskraft': 'Manager'
    }
    
    if source == 'XING':
        return xing_map.get(level.lower(), 'Mid-Level')
    elif source == 'AngelList':
        return level.replace('_', '-').title()
    
    return 'Mid-Level'  # Default
```

---

### 3. `equity_range`

**Type**: `VARCHAR(100)`
**Nullable**: Yes
**Default**: NULL
**Index**: No

**Purpose**: Stock options/equity compensation range

**Source Mapping**:
```yaml
AngelList:
  field: job.salaryRange.equity
  structure:
    min: 0.1
    max: 0.5
    type: "percentage"  # or "shares"
```

**Format**: 
- Percentage: `"0.1%-0.5%"`
- Shares: `"1,000-5,000 shares"`

**Transformation**:
```python
def format_equity_range(equity: dict) -> str:
    if not equity:
        return None
    
    equity_type = equity.get('type', 'percentage')
    min_equity = equity.get('min', 0)
    max_equity = equity.get('max', 0)
    
    if equity_type == 'percentage':
        return f"{min_equity}%-{max_equity}%"
    else:
        return f"{min_equity:,}-{max_equity:,} shares"
```

---

### 4. `tech_stack`

**Type**: `TEXT[]`
**Nullable**: Yes
**Default**: NULL
**Index**: GIN (for array search)

**Purpose**: Technologies/languages used at the company

**Source Mapping**:
```yaml
Welcome to the Jungle:
  field: job.technologies
  example: ["Python", "React", "AWS", "PostgreSQL"]

AngelList:
  field: company.techStack
  example: ["Ruby on Rails", "React", "Docker"]
```

**Normalization Rules**:
```python
TECH_NORMALIZATION = {
    'react.js': 'React',
    'reactjs': 'React',
    'node.js': 'Node.js',
    'nodejs': 'Node.js',
    'aws': 'AWS',
    'amazon web services': 'AWS',
    'postgres': 'PostgreSQL',
    'postgresql': 'PostgreSQL',
    'k8s': 'Kubernetes'
}

def normalize_tech_stack(technologies: List[str]) -> List[str]:
    normalized = []
    for tech in technologies:
        tech_lower = tech.lower().strip()
        normalized_tech = TECH_NORMALIZATION.get(tech_lower, tech)
        if normalized_tech not in normalized:
            normalized.append(normalized_tech)
    return normalized
```

**Sample Values**:
- `["Python", "Django", "React", "PostgreSQL", "AWS"]`
- `["Java", "Spring Boot", "Kubernetes", "MongoDB"]`

---

### 5. `company_culture_tags`

**Type**: `TEXT[]`
**Nullable**: Yes
**Default**: NULL
**Index**: GIN

**Purpose**: Company culture keywords

**Source Mapping**:
```yaml
Welcome to the Jungle:
  field: job.culture_tags
  example: ["Collaborative", "Innovative", "Remote-first"]
```

**Allowed Tags** (normalized):
- Work Style: `Remote-First`, `Hybrid`, `Office-Based`, `Flexible`
- Culture: `Collaborative`, `Innovative`, `Transparent`, `Inclusive`
- Values: `Mission-Driven`, `Fast-Paced`, `Work-Life Balance`
- Benefits: `Wellness`, `Learning`, `Equity`

---

### 6. `funding_stage`

**Type**: `VARCHAR(50)`
**Nullable**: Yes
**Default**: NULL
**Index**: Yes

**Purpose**: Startup funding stage

**Allowed Values**:
- `Bootstrapped`
- `Pre-Seed`
- `Seed`
- `Series A`
- `Series B`
- `Series C`
- `Series D+`
- `Acquired`
- `Public`

**Source Mapping**:
```yaml
AngelList:
  field: company.stage
  values: ["seed", "series_a", "series_b", "series_c", "series_d_+", "acquired", "public"]
  mapping:
    seed: "Seed"
    series_a: "Series A"
    series_b: "Series B"
```

---

### 7. `work_permit_info`

**Type**: `TEXT`
**Nullable**: Yes
**Default**: NULL

**Purpose**: Visa/work permit requirements

**Source Mapping**:
```yaml
JobScout24:
  field: job.work_permit
  examples:
    - "EU/EFTA work permit required"
    - "Valid Swiss work permit or EU passport"
    - "Sponsorship available"
```

---

### 8. `company_verified`

**Type**: `BOOLEAN`
**Nullable**: No
**Default**: FALSE

**Purpose**: Whether company account is verified

**Source Mapping**:
```yaml
XING:
  field: company.verified
  type: boolean
```

---

### 9. `company_videos`

**Type**: `JSONB`
**Nullable**: Yes
**Default**: NULL

**Purpose**: Store video metadata (URLs, types, durations)

**Structure**:
```json
[
  {
    "url": "https://...",
    "type": "office_tour",
    "duration": 120,
    "thumbnail": "https://..."
  },
  {
    "url": "https://...",
    "type": "team_interview",
    "duration": 90
  }
]
```

**Source Mapping**:
```yaml
Welcome to the Jungle:
  field: job.videos
  extract: url, type, duration (if available)
```

---

### 10. `perks`

**Type**: `TEXT[]`
**Nullable**: Yes
**Default**: NULL

**Purpose**: Job benefits/perks

**Source Mapping**:
```yaml
Welcome to the Jungle:
  field: job.perks
  example: ["Remote work", "Stock options", "Health insurance", "Learning budget"]
```

---

### 11. `total_funding`

**Type**: `BIGINT`
**Nullable**: Yes
**Default**: NULL

**Purpose**: Total funding raised by company (in USD cents)

**Source Mapping**:
```yaml
AngelList:
  field: company.totalRaised
  unit: USD
  storage: cents (multiply by 100)
```

**Example**:
- $50M raised → Store as `5000000000` (cents)

---

### 12. `investors`

**Type**: `TEXT[]`
**Nullable**: Yes
**Default**: NULL

**Purpose**: Company investors/VCs

**Source Mapping**:
```yaml
AngelList:
  field: company.investors
  example: ["Sequoia Capital", "Andreessen Horowitz", "Y Combinator"]
```

---

### 13. `workload_percentage`

**Type**: `INTEGER`
**Nullable**: Yes
**Default**: NULL

**Purpose**: Swiss workload percentage (80%, 100%)

**Source Mapping**:
```yaml
JobScout24:
  field: job.workload
  example: "80-100%"
  parse: Extract max value
```

---

### 14. `job_language`

**Type**: `VARCHAR(5)`
**Nullable**: Yes
**Default**: `'en'`
**Index**: Yes

**Purpose**: ISO 639-1 language code of job posting

**Allowed Values**: `en`, `de`, `fr`, `it`, `es`

**Detection**:
```python
from langdetect import detect

def detect_job_language(description: str) -> str:
    try:
        lang = detect(description)
        if lang in ['en', 'de', 'fr', 'it', 'es']:
            return lang
        return 'en'
    except:
        return 'en'
```

---

## Database Migration Scripts

### Migration 1: Core New Fields

```sql
-- Migration: 2025_11_17_add_phase_3_3_fields.sql

BEGIN;

-- Language and experience
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS language_requirements TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS experience_level VARCHAR(50);

-- Startup/equity fields
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS equity_range VARCHAR(100);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS funding_stage VARCHAR(50);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS total_funding BIGINT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS investors TEXT[];

-- Tech and culture
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS tech_stack TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_culture_tags TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS perks TEXT[];

-- Swiss-specific
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS work_permit_info TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS workload_percentage INTEGER;

-- Verification and media
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_videos JSONB;

-- Language tracking
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_language VARCHAR(5) DEFAULT 'en';

-- Add indexes for filtering
CREATE INDEX IF NOT EXISTS idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX IF NOT EXISTS idx_jobs_funding_stage ON jobs(funding_stage);
CREATE INDEX IF NOT EXISTS idx_jobs_job_language ON jobs(job_language);

-- Add GIN indexes for array fields
CREATE INDEX IF NOT EXISTS idx_jobs_tech_stack ON jobs USING GIN(tech_stack);
CREATE INDEX IF NOT EXISTS idx_jobs_culture_tags ON jobs USING GIN(company_culture_tags);
CREATE INDEX IF NOT EXISTS idx_jobs_language_reqs ON jobs USING GIN(language_requirements);

COMMIT;
```

### Migration 2: Add Constraints

```sql
-- Migration: 2025_11_17_add_phase_3_3_constraints.sql

BEGIN;

-- Experience level check
ALTER TABLE jobs ADD CONSTRAINT check_experience_level 
CHECK (experience_level IN (
    'Internship', 'Entry Level', 'Junior', 'Mid-Level', 
    'Senior', 'Lead', 'Staff', 'Principal', 
    'Manager', 'Director', 'VP', 'C-Level'
) OR experience_level IS NULL);

-- Funding stage check
ALTER TABLE jobs ADD CONSTRAINT check_funding_stage 
CHECK (funding_stage IN (
    'Bootstrapped', 'Pre-Seed', 'Seed', 
    'Series A', 'Series B', 'Series C', 'Series D+', 
    'Acquired', 'Public'
) OR funding_stage IS NULL);

-- Language code check
ALTER TABLE jobs ADD CONSTRAINT check_job_language 
CHECK (job_language IN ('en', 'de', 'fr', 'it', 'es'));

-- Workload percentage range
ALTER TABLE jobs ADD CONSTRAINT check_workload_percentage 
CHECK (workload_percentage >= 0 AND workload_percentage <= 100);

COMMIT;
```

---

## Field Population Strategy

### Priority 1: Always Fill (Required)
- `title`
- `company`
- `location`
- `description`
- `source`
- `posted_date`

### Priority 2: Fill if Available (High Value)
- `salary_range`
- `experience_level`
- `tech_stack`
- `equity_range` (AngelList)
- `work_permit_info` (JobScout24)

### Priority 3: Nice to Have
- `company_culture_tags`
- `perks`
- `company_videos`
- `investors`
- `funding_stage`

---

## Data Validation Rules

### 1. Tech Stack Validation
```python
def validate_tech_stack(tech_stack: List[str]) -> bool:
    # Max 20 technologies
    if len(tech_stack) > 20:
        return False
    
    # Each tech name max 50 chars
    for tech in tech_stack:
        if len(tech) > 50:
            return False
    
    return True
```

### 2. Equity Range Validation
```python
def validate_equity_range(equity: str) -> bool:
    # Must match pattern: "0.1%-0.5%" or "1,000-5,000 shares"
    import re
    percentage_pattern = r"^\d+(\.\d+)?%-\d+(\.\d+)?%$"
    shares_pattern = r"^[\d,]+-[\d,]+ shares$"
    
    return bool(re.match(percentage_pattern, equity) or 
                re.match(shares_pattern, equity))
```

### 3. Language Requirements Validation
```python
def validate_language_requirements(languages: List[str]) -> bool:
    # Max 5 languages
    if len(languages) > 5:
        return False
    
    # Each must have format: "Language (Level)"
    import re
    pattern = r"^[A-Z][a-z]+ \([A-Z][a-z]+\)$"
    
    for lang in languages:
        if not re.match(pattern, lang):
            return False
    
    return True
```

---

## Example: Complete Job Object

```json
{
  "id": 12345,
  "title": "Senior Full-Stack Engineer",
  "company": "TechStartup GmbH",
  "location": "Berlin, Germany",
  "description": "We are looking for...",
  "salary_range": "€70,000-€95,000",
  "source": "XING",
  "posted_date": "2025-11-15",
  
  // New Phase 3.3 fields
  "language_requirements": ["German (Fluent)", "English (Working)"],
  "experience_level": "Senior",
  "equity_range": null,
  "tech_stack": ["Python", "Django", "React", "PostgreSQL", "AWS"],
  "company_culture_tags": ["Remote-First", "Innovative"],
  "funding_stage": null,
  "work_permit_info": null,
  "company_verified": true,
  "company_videos": null,
  "perks": ["Home office budget", "Learning stipend"],
  "total_funding": null,
  "investors": null,
  "workload_percentage": null,
  "job_language": "de"
}
```

---

## Testing Strategy

### Unit Tests
```python
def test_normalize_tech_stack():
    input_tech = ["react.js", "Node.js", "aws", "PostgreSQL"]
    expected = ["React", "Node.js", "AWS", "PostgreSQL"]
    assert normalize_tech_stack(input_tech) == expected

def test_format_equity_range():
    equity = {"min": 0.1, "max": 0.5, "type": "percentage"}
    assert format_equity_range(equity) == "0.1%-0.5%"

def test_map_experience_level():
    assert map_experience_level("mit_berufserfahrung", "XING") == "Mid-Level"
    assert map_experience_level("senior", "AngelList") == "Senior"
```

---

## Rollback Plan

```sql
-- Rollback script if needed
BEGIN;

DROP INDEX IF EXISTS idx_jobs_experience_level;
DROP INDEX IF EXISTS idx_jobs_funding_stage;
DROP INDEX IF EXISTS idx_jobs_job_language;
DROP INDEX IF EXISTS idx_jobs_tech_stack;
DROP INDEX IF EXISTS idx_jobs_culture_tags;
DROP INDEX IF EXISTS idx_jobs_language_reqs;

ALTER TABLE jobs DROP CONSTRAINT IF EXISTS check_experience_level;
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS check_funding_stage;
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS check_job_language;
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS check_workload_percentage;

ALTER TABLE jobs DROP COLUMN IF EXISTS language_requirements;
ALTER TABLE jobs DROP COLUMN IF EXISTS experience_level;
ALTER TABLE jobs DROP COLUMN IF EXISTS equity_range;
ALTER TABLE jobs DROP COLUMN IF EXISTS funding_stage;
ALTER TABLE jobs DROP COLUMN IF EXISTS total_funding;
ALTER TABLE jobs DROP COLUMN IF EXISTS investors;
ALTER TABLE jobs DROP COLUMN IF EXISTS tech_stack;
ALTER TABLE jobs DROP COLUMN IF EXISTS company_culture_tags;
ALTER TABLE jobs DROP COLUMN IF EXISTS perks;
ALTER TABLE jobs DROP COLUMN IF EXISTS work_permit_info;
ALTER TABLE jobs DROP COLUMN IF EXISTS workload_percentage;
ALTER TABLE jobs DROP COLUMN IF EXISTS company_verified;
ALTER TABLE jobs DROP COLUMN IF EXISTS company_videos;
ALTER TABLE jobs DROP COLUMN IF EXISTS job_language;

COMMIT;
```

---

**Document Status**: ✅ Complete
**Last Updated**: November 17, 2025
**Next Steps**: Review and approve migrations, then implement in Week 2
