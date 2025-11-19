# Prompt Engineering Best Practices

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

**Status**: Production Guide  
**Last Updated**: 2025-06-10  
**Related**: [[LLM Service Architecture]], [[Token Optimization]], [[AI Components Review]]

## Overview

This guide documents comprehensive prompt engineering best practices for Career Copilot, covering token optimization, template patterns, cost efficiency, and quality assurance.

## Core Principles

### 1. **Task-Aware Prompt Design**
Career Copilot uses task-specific prompts aligned with business needs:

- **Contract Analysis**: Legal precedent-aware, risk-focused prompts
- **Negotiation**: Persuasive, outcome-oriented language
- **Communication**: Professional, concise, user-facing content
- **General**: Flexible, context-dependent prompts

### 2. **Token Budget Management**
All prompts must consider token economics:

```python
from backend.app.core.token_optimizer import TokenBudget, OptimizationStrategy

# Define budget per task type
budgets = {
    "contract_analysis": TokenBudget(
        max_prompt_tokens=3000,
        max_completion_tokens=1500,
        max_total_tokens=4500,
        reserved_tokens=100,
        emergency_threshold=0.9
    ),
    "communication": TokenBudget(
        max_prompt_tokens=500,
        max_completion_tokens=300,
        max_total_tokens=800,
        reserved_tokens=50
    )
}
```

### 3. **Provider-Specific Optimization**
Different LLM providers require tailored approaches:

| Provider          | Strengths                   | Optimal Tasks                      | Cost/Token |
| ----------------- | --------------------------- | ---------------------------------- | ---------- |
| **GPT-4**         | Complex reasoning, accuracy | Contract analysis, risk assessment | $0.00003   |
| **GPT-3.5 Turbo** | Speed, cost-efficiency      | Communication, simple tasks        | $0.000002  |
| **Groq Mixtral**  | Ultra-fast inference        | Real-time communication            | $0.0000002 |
| **Groq Llama2**   | Balanced performance        | General tasks, simple analysis     | $0.0000007 |

## Token Optimization Strategies

### Optimization Levels

Career Copilot implements 4 optimization strategies:

#### 1. **CONSERVATIVE** (Quality First)
- **Use Case**: Complex legal analysis, high-stakes negotiations
- **Techniques**: Whitespace removal only
- **Quality Retention**: 98-100%
- **Token Reduction**: 5-10%

```python
# Example: Contract risk assessment
optimizer.optimize_messages(
    messages=messages,
    budget=budget,
    strategy=OptimizationStrategy.CONSERVATIVE,
    preserve_quality=True
)
```

#### 2. **BALANCED** (Default)
- **Use Case**: Most production scenarios
- **Techniques**: Whitespace removal, redundancy elimination, selective abbreviations
- **Quality Retention**: 85-95%
- **Token Reduction**: 15-25%

```python
# Techniques applied:
# - Remove excessive whitespace: "Hello    world" → "Hello world"
# - Eliminate redundancy: "please note that it should be noted" → ""
# - Selective abbreviations: "application" → "app", "configuration" → "config"
```

#### 3. **AGGRESSIVE** (Cost Focused)
- **Use Case**: High-volume, low-criticality tasks
- **Techniques**: All balanced techniques + stop word removal + full abbreviations
- **Quality Retention**: 70-85%
- **Token Reduction**: 30-50%

```python
# Additional techniques:
# - Remove stop words: "the", "a", "an", "is" (context-aware)
# - Full abbreviation dictionary (see backend/app/core/token_optimizer.py)
```

#### 4. **ADAPTIVE** (Context-Aware)
- **Use Case**: Dynamic task complexity
- **Techniques**: Automatically selects strategy based on budget pressure
- **Quality Retention**: Variable (70-100%)
- **Token Reduction**: Variable (5-50%)

```python
# Automatically adjusts based on:
# - Budget utilization (>90% triggers aggressive)
# - Task complexity (complex tasks stay conservative)
# - Token budget emergency threshold
```

### Token Estimation

Approximate token counts (GPT models):
- **1 token** ≈ 4 characters
- **1 token** ≈ 0.75 words
- **1000 tokens** ≈ 750 words

```python
from backend.app.core.token_optimizer import get_token_optimizer

optimizer = get_token_optimizer()
token_count = optimizer.estimate_tokens("Your prompt text here")
# Returns rough token estimate
```

### Compression Techniques

#### Whitespace Removal
```python
# Before: "Hello    world.\n\n\nHow   are you?"
# After:  "Hello world. How are you?"
# Savings: ~20% in whitespace-heavy text
```

#### Redundancy Elimination
```python
# Patterns removed:
# - "please note that", "it should be noted that"
# - "as mentioned above/before/previously"
# - "in other words", "that is to say"
# - "furthermore", "moreover", "additionally"
# - "in conclusion", "to conclude", "in summary"

# Before: "Please note that, as mentioned above, it is important to note that..."
# After:  Direct content without filler
# Savings: 10-15% in formal text
```

#### Abbreviations
```python
# Safe abbreviations (applied in BALANCED mode):
abbreviations = {
    "application": "app",
    "configuration": "config",
    "development": "dev",
    "environment": "env",
    "performance": "perf"
}

# Legal domain abbreviations (CONSERVATIVE mode only):
legal_abbreviations = {
    "contract": "ctr",
    "agreement": "agr",
    "clause": "cl",
    "section": "sec"
}
```

## Prompt Templates

### Cover Letter Generation

**File**: `backend/app/services/content_generator_service.py`

```python
def _create_cover_letter_template_prompt(self, user: User, job: Job, tone: str) -> str:
    """
    Template with:
    - Job-specific personalization
    - User skill alignment
    - Company research hooks
    - Tone adaptation (professional/creative/enthusiastic)
    """
    template = PromptTemplate(
        input_variables=["job_title", "company", "user_skills", "experience_level"],
        template="""
        Write a {tone} cover letter for {job_title} at {company}.
        
        Candidate Profile:
        - Skills: {user_skills}
        - Experience: {experience_level}
        
        Requirements:
        - 3-4 paragraphs, 250-350 words
        - Highlight relevant skills
        - Show genuine interest in company mission
        - Include specific examples
        """
    )
```

**Best Practices**:
- ✅ Specify exact output length (tokens predictable)
- ✅ Use structured input variables
- ✅ Define clear requirements
- ❌ Avoid open-ended "write about..." prompts
- ❌ Don't include unnecessary context

### Resume Tailoring

```python
def _create_resume_tailoring_prompt(self, user: User, job: Job) -> str:
    """
    Analyze job posting and suggest resume optimizations:
    - ATS keyword alignment
    - Skill highlighting
    - Experience rephrasing
    """
    return f"""
    Job Posting: {job.title} at {job.company}
    Required Skills: {job.required_skills}
    
    Current Resume Highlights: {user.resume_summary}
    
    Provide 5 specific resume tailoring suggestions:
    1. ATS keywords to add
    2. Skills to emphasize
    3. Experience to reframe
    4. Metrics to include
    5. Sections to adjust
    
    Format: Numbered list, max 2 sentences per suggestion.
    """
```

### Email Templates

```python
def _create_email_template_prompt(self, user: User, job: Job, template_type: str) -> str:
    """
    Generate professional emails:
    - Follow-up emails
    - Thank you notes
    - Application inquiries
    """
    template_instructions = {
        "follow_up": "Polite application status inquiry, 3-4 sentences",
        "thank_you": "Post-interview gratitude, mention 2 specific points",
        "inquiry": "Pre-application company research, show genuine interest"
    }
    
    return f"""
    Email Type: {template_type}
    Purpose: {template_instructions[template_type]}
    
    Job: {job.title} at {job.company}
    Candidate: {user.username}
    
    Requirements:
    - Professional tone
    - Include subject line
    - 75-125 words body
    - Clear call-to-action
    """
```

## Provider-Specific Optimization

### Groq Optimization

**File**: `backend/app/services/groq_optimizer.py`

Groq models (Mixtral, Llama2) benefit from:

```python
class GROQRequestOptimizer:
    def optimize_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Groq-specific optimizations:
        - Remove excessive whitespace (critical for speed)
        - Intelligent truncation at 8000 chars (context window)
        - Add task-type markers for better routing
        """
        # Example: Add context markers
        if "analyze" in content.lower() and "contract" in content.lower():
            content = f"[CONTRACT ANALYSIS TASK] {content}"
        
        return optimized_messages
```

**Best Practices**:
- Keep system prompts under 500 tokens
- Use structured output formats (JSON, numbered lists)
- Avoid very long context (>8k tokens)
- Leverage Groq's speed for multi-iteration tasks

### OpenAI GPT Optimization

```python
# GPT-4: Complex reasoning
gpt4_prompt = """
Analyze this contract for legal risks. Consider:
1. Jurisdictional issues
2. Liability clauses
3. Termination conditions
4. Intellectual property rights

Provide structured JSON output with risk scores.
"""

# GPT-3.5 Turbo: Fast communication
gpt35_prompt = """
Write a follow-up email. Keep it under 100 words, professional tone.
Job: {job_title} at {company}
"""
```

## Cost Optimization

### Cost Hierarchy

```
GPT-4:       $0.03/1K tokens  → Complex analysis, legal review
GPT-3.5:     $0.002/1K tokens → Communication, simple tasks
Groq Mixtral: $0.0002/1K tokens → Real-time, high-volume
```

### Budget-Aware Prompt Design

```python
# HIGH COST TASK (use GPT-4, keep prompt tight)
def analyze_contract_risk(contract_text: str) -> str:
    # Don't include full contract, use summary
    summary = extract_key_clauses(contract_text)  # Reduce from 10k → 1k tokens
    
    prompt = f"""
    Key Contract Clauses: {summary}
    Analyze for: liability risks, termination rights, IP issues.
    Output: JSON with risk_score (0-100) and top_3_risks.
    """
    # Estimated: 1.5k tokens → $0.045 per request

# LOW COST TASK (use Groq, allow longer prompts)
def generate_follow_up_email(job: Job) -> str:
    prompt = f"""
    Write follow-up email for {job.title} at {job.company}.
    Applied 2 weeks ago. Polite, professional, 75 words.
    """
    # Estimated: 500 tokens → $0.0001 per request
```

### Caching Strategy

Career Copilot implements aggressive caching:

```python
# backend/app/services/llm_service.py
cache_key = f"ai_response:{model_type}:{task_complexity}:{hash(prompt)}"
cached_response = await cache_service.aget(cache_key)
if cached_response:
    return cached_response  # Save API cost
```

**Cache Hit Optimization**:
- Normalize prompts (remove whitespace variations)
- Use task-type prefixes for better hit rates
- Set TTL based on content volatility:
  - Cover letters: 1 hour (personalized)
  - Email templates: 24 hours (semi-generic)
  - Job analysis: 7 days (stable)

## Quality Assurance

### Confidence Scoring

```python
def _calculate_confidence(self, response, model_config: ModelConfig) -> float:
    """
    Estimate response quality:
    - GPT-4/Claude: 0.9 base confidence
    - GPT-3.5/Mixtral: 0.75 base confidence
    - Adjust for content length
    """
    base_confidence = 0.9 if "gpt-4" in model_config.model_name else 0.75
    
    # Penalize very short responses
    if len(response.content) < 50:
        base_confidence -= 0.1
    
    return min(1.0, base_confidence)
```

### Validation Patterns

```python
# Validate structured output
def validate_cover_letter(content: str) -> bool:
    checks = [
        len(content) >= 200,  # Minimum length
        len(content) <= 500,  # Maximum length
        content.count('\n') >= 2,  # Multiple paragraphs
        any(greeting in content.lower() for greeting in ["dear", "hello"]),
        "sincerely" in content.lower() or "regards" in content.lower()
    ]
    return all(checks)
```

## Monitoring & Iteration

### Key Metrics

Track these metrics per prompt template:

```python
# backend/app/services/llm_service.py - AIResponse includes:
{
    "token_usage": {"prompt_tokens": 500, "completion_tokens": 300},
    "cost": 0.024,
    "processing_time": 2.3,
    "confidence_score": 0.87,
    "model_used": "gpt-4",
    "complexity_used": "COMPLEX"
}
```

**Dashboard Goals**:
- Average cost per task type < $0.05
- Response time < 3 seconds (95th percentile)
- Confidence score > 0.80
- Token optimization reduction > 15%

### A/B Testing Prompts

```python
# Example: Test cover letter tones
prompts = {
    "control": "Write a professional cover letter...",
    "variant_a": "Write an enthusiastic, personalized cover letter...",
    "variant_b": "Write a data-driven cover letter highlighting metrics..."
}

# Track user engagement per variant
metrics = {
    "control": {"usage": 100, "success_rate": 0.75},
    "variant_a": {"usage": 100, "success_rate": 0.82},  # Winner
    "variant_b": {"usage": 100, "success_rate": 0.71}
}
```

## Implementation Checklist

When creating new prompts:

- [ ] Define clear task objective
- [ ] Specify exact output format (length, structure)
- [ ] Identify appropriate model (cost/quality tradeoff)
- [ ] Estimate token budget (prompt + completion)
- [ ] Apply token optimization strategy
- [ ] Add caching key
- [ ] Implement confidence scoring
- [ ] Add validation logic
- [ ] Set up cost monitoring
- [ ] Document example outputs

## References

- [[LLM Service Architecture]] - Provider abstraction and fallback
- [[Token Optimization]] - Deep dive into compression techniques
- [[Cost Tracking]] - Budget management and monitoring
- `backend/app/core/token_optimizer.py` - Core optimization implementation
- `backend/app/services/llm_service.py` - LLM service orchestration
- `backend/app/services/content_generator_service.py` - Production prompt examples
- `backend/app/services/groq_optimizer.py` - Provider-specific optimization

---

**Next Steps**: Implement A/B testing framework for prompt optimization, add semantic similarity checking for validation.
