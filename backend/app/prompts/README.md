# Prompt Templates Directory

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

This directory contains centralized prompt templates for Career Copilot's LLM integrations.

## Directory Structure

```
prompts/
├── __init__.py              # Prompt registry and management system
├── cover_letters/           # Cover letter generation templates
│   ├── professional_cover_letter.j2
│   ├── professional_cover_letter.json
│   ├── cover_letter_generator.j2       # NEW: Advanced cover letter with tone control
│   ├── cover_letter_generator.json
│   ├── creative_cover_letter.j2
│   └── creative_cover_letter.json
├── emails/                  # Email templates
│   ├── follow_up_email.j2
│   ├── follow_up_email.json
│   ├── email_template_generator.j2     # NEW: Multi-type email generator
│   ├── email_template_generator.json
│   ├── thank_you_email.j2
│   └── thank_you_email.json
├── resumes/                 # Resume-related templates
│   ├── resume_tailoring.j2             # NEW: Resume tailoring suggestions
│   ├── resume_tailoring.json
│   ├── tailoring_suggestions.j2
│   └── tailoring_suggestions.json
├── improvement/             # Content improvement templates
│   ├── content_improvement.j2          # NEW: Feedback-based content revision
│   └── content_improvement.json
├── analysis/                # Analysis and assessment templates
│   ├── contract_risk_analysis.j2
│   └── job_description_analysis.j2
└── README.md                # This file
```

## Template Format

### Jinja2 Template (.j2)
Templates use Jinja2 syntax for variable substitution and logic:

```jinja2
Dear {{ hiring_manager }},

I am applying for the {{ job_title }} position at {{ company }}.

{% if user_skills %}
My key skills include:
{% for skill in user_skills %}
- {{ skill }}
{% endfor %}
{% endif %}

Best regards,
{{ user_name }}
```

### Metadata JSON (.json)
Each template has a companion JSON file with metadata:

```json
{
  "name": "professional_cover_letter",
  "version": "1.0.0",
  "description": "Professional cover letter template",
  "input_variables": ["job_title", "company", "user_name", "user_skills"],
  "output_format": "text",
  "estimated_tokens": 400,
  "tags": ["cover_letter", "professional"],
  "model_recommendations": ["gpt-4", "claude-3-opus"]
}
```

## Usage

### Python API

```python
from backend.app.prompts import get_prompt_registry

# Get registry
registry = get_prompt_registry()

# Get a template
template = registry.get_template("professional_cover_letter", version="latest")

# Render with variables
prompt = template.render(
    job_title="Senior Software Engineer",
    company="TechCorp",
    user_name="John Doe",
    user_skills="Python, FastAPI, React",
    experience_level="5 years"
)

# Update usage stats
registry.update_usage_stats(
    name="professional_cover_letter",
    version="1.0.0",
    success=True,
    tokens_used=385
)
```

### List Templates

```python
# List all templates
all_templates = registry.list_templates()

# Filter by category
cover_letters = registry.list_templates(category=PromptCategory.COVER_LETTER)

# Filter by tags
professional_templates = registry.list_templates(tags=["professional"])
```

## Version Control

Templates support semantic versioning:

- **1.0.0**: Initial version
- **1.1.0**: Minor improvements (backward compatible)
- **2.0.0**: Major changes (may break compatibility)

To create a new version:

1. Copy the existing `.j2` and `.json` files
2. Update the `version` field in JSON
3. Make your changes
4. Test thoroughly before deploying

## A/B Testing

Templates support A/B testing through metadata:

```json
{
  "ab_test_group": "variant_a",
  "is_active": true,
  "performance_score": 0.85
}
```

Track performance metrics to compare variants and optimize prompts.

## Best Practices

1. **Variable Naming**: Use clear, descriptive variable names (`job_title` not `jt`)
2. **Defaults**: Provide sensible defaults in Jinja2 templates
3. **Validation**: Always validate input variables before rendering
4. **Token Estimation**: Keep `estimated_tokens` accurate for cost planning
5. **Documentation**: Add clear descriptions in JSON metadata
6. **Testing**: Test templates with various input combinations
7. **Versioning**: Increment versions for any content changes
8. **Model Recommendations**: Specify which models work best for each template

## Adding New Templates

1. Create a new category directory if needed (update `PromptCategory` enum in `__init__.py`)
2. Create the `.j2` template file with Jinja2 syntax
3. Create the companion `.json` metadata file
4. Test the template with the registry
5. Update this README if adding a new category

## Recently Added Templates (v2.0 Migration)

### 1. `cover_letter_generator` (v2.0.0)
**Location**: `cover_letters/cover_letter_generator.{j2,json}`  
**Purpose**: Advanced cover letter generation with tone control  
**Variables**: job_title, company, location, tech_stack, job_description, user_name, user_skills, experience_level, tone, custom_instructions  
**Tones**: professional, casual, enthusiastic  
**Features**: 
- Embedded tone_instructions dictionary for dynamic tone selection
- Optional custom_instructions field for user-specific guidance
- Truncates job_description to first 500 chars

**Usage**:
```python
from app.prompts import PromptRegistry

registry = PromptRegistry()
template = registry.get_template("cover_letter_generator")
prompt = template.render(
    job_title="Senior Backend Engineer",
    company="TechCorp",
    location="Berlin, Germany",
    tech_stack="Python, FastAPI, PostgreSQL, Docker",
    job_description="We are seeking an experienced backend engineer...",
    user_name="Alice Smith",
    user_skills="Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes",
    experience_level="5 years",
    tone="professional",  # or "casual", "enthusiastic"
    custom_instructions="Emphasize my experience with microservices"
)
```

### 2. `resume_tailoring` (v1.0.0)
**Location**: `resumes/resume_tailoring.{j2,json}`  
**Purpose**: Generate tailoring suggestions for resume sections  
**Variables**: job_title, company, tech_stack, job_description, resume_sections  
**Features**:
- Iterates over resume_sections dictionary
- Provides 4-point structured suggestions per section
- Truncates job_description to 300 chars

**Usage**:
```python
template = registry.get_template("resume_tailoring")
prompt = template.render(
    job_title="Full Stack Developer",
    company="StartupXYZ",
    tech_stack="React, Node.js, MongoDB",
    job_description="Looking for a full-stack developer with React and Node experience",
    resume_sections={
        "Experience": "Software Engineer at TechCorp (2020-2023)...",
        "Skills": "JavaScript, Python, React, Vue.js",
        "Projects": "Built an e-commerce platform with React and Node.js"
    }
)
```

### 3. `email_template_generator` (v1.0.0)
**Location**: `emails/email_template_generator.{j2,json}`  
**Purpose**: Generate professional emails for different scenarios  
**Variables**: email_type, job_title, company, user_name, custom_instructions  
**Email Types**: follow_up, thank_you, inquiry  
**Features**:
- Conditional instructions based on email_type
- Embedded template_instructions dictionary

**Usage**:
```python
template = registry.get_template("email_template_generator")
prompt = template.render(
    email_type="follow_up",  # or "thank_you", "inquiry"
    job_title="Data Scientist",
    company="AI Labs",
    user_name="Bob Johnson",
    custom_instructions="Mention the data pipeline project I discussed"
)
```

### 4. `content_improvement` (v1.0.0)
**Location**: `improvement/content_improvement.{j2,json}`  
**Purpose**: Improve existing content based on user feedback  
**Variables**: content_type, original_content, feedback  
**Features**:
- Simple feedback-based revision template
- Works for any content_type (cover_letter, resume, email, etc.)

**Usage**:
```python
template = registry.get_template("content_improvement")
prompt = template.render(
    content_type="cover_letter",
    original_content="Dear Hiring Manager, I am writing to apply...",
    feedback="Make it more enthusiastic and mention my passion for AI"
)
```

## Migration Pattern for Services

When migrating existing prompt code to use the registry:

1. **Create Templates**: Create `.j2` and `.json` files for the prompt
2. **Update Service Method**: Use `get_template().render()` pattern
3. **Add Fallback**: Keep original prompt as fallback method
4. **Test**: Verify template loads and renders correctly

**Example Migration**:
```python
# BEFORE: Hardcoded prompt
def _create_prompt(self, job: Job, user: User) -> str:
    return f"""
    Write a cover letter for {job.title} at {job.company}.
    User: {user.username}
    """

# AFTER: Using registry with fallback
def _create_prompt(self, job: Job, user: User) -> str:
    template = self.prompt_registry.get_template("my_template")
    if template:
        prompt = template.render(job_title=job.title, company=job.company, user_name=user.username)
    else:
        prompt = None
    
    return prompt if prompt else self._create_prompt_fallback(job, user)

def _create_prompt_fallback(self, job: Job, user: User) -> str:
    """Fallback if template not found"""
    return f"""
    Write a cover letter for {job.title} at {job.company}.
    User: {user.username}
    """
```

This pattern ensures:
- **Zero downtime**: Fallback to hardcoded prompt if template missing
- **Backward compatibility**: Existing code continues working
- **Gradual rollout**: Can deploy without requiring all templates exist
- **Easy testing**: Can test new templates without breaking production

## Monitoring

The registry tracks:
- **Usage count**: How often each template is used
- **Success rate**: Percentage of successful executions
- **Average tokens**: Actual token usage vs. estimates
- **Performance score**: Composite score for A/B testing

Access these metrics via:

```python
template = registry.get_template("my_template")
print(f"Usage: {template.metadata.usage_count}")
print(f"Success Rate: {template.metadata.success_rate:.2%}")
print(f"Avg Tokens: {template.metadata.average_tokens}")
```

## See Also

- [[PROMPT_ENGINEERING_GUIDE]] - Best practices for prompt design
- [[AI_COMPONENTS_REVIEW]] - Architecture documentation
- `backend/app/services/content_generator_service.py` - Legacy prompt usage
