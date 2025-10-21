"""
Task complexity analysis for intelligent LLM provider routing.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from datetime import datetime

from ..core.logging import get_logger

logger = get_logger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels for LLM routing."""
    SIMPLE = "simple"      # Route to cost-effective providers (Groq, GPT-3.5)
    MEDIUM = "medium"      # Route to balanced providers (GPT-3.5, Claude-3)
    COMPLEX = "complex"    # Route to high-capability providers (GPT-4, Claude-3)


@dataclass
class ComplexityFactors:
    """Factors that contribute to task complexity."""
    text_length: int
    technical_terms: int
    legal_concepts: int
    analysis_depth: int
    reasoning_required: int
    json_output: bool
    multi_step: bool
    context_length: int
    
    def calculate_score(self) -> float:
        """Calculate overall complexity score (0.0 to 1.0)."""
        # Weighted scoring system
        score = 0.0
        
        # Text length factor (0-0.2)
        if self.text_length > 5000:
            score += 0.2
        elif self.text_length > 2000:
            score += 0.15
        elif self.text_length > 1000:
            score += 0.1
        elif self.text_length > 500:
            score += 0.05
        
        # Technical terms factor (0-0.2)
        if self.technical_terms > 10:
            score += 0.2
        elif self.technical_terms > 5:
            score += 0.15
        elif self.technical_terms > 2:
            score += 0.1
        elif self.technical_terms > 0:
            score += 0.05
        
        # Legal concepts factor (0-0.2)
        if self.legal_concepts > 8:
            score += 0.2
        elif self.legal_concepts > 4:
            score += 0.15
        elif self.legal_concepts > 2:
            score += 0.1
        elif self.legal_concepts > 0:
            score += 0.05
        
        # Analysis depth factor (0-0.15)
        if self.analysis_depth > 3:
            score += 0.15
        elif self.analysis_depth > 2:
            score += 0.1
        elif self.analysis_depth > 1:
            score += 0.05
        
        # Reasoning required factor (0-0.15)
        if self.reasoning_required > 3:
            score += 0.15
        elif self.reasoning_required > 2:
            score += 0.1
        elif self.reasoning_required > 1:
            score += 0.05
        
        # JSON output factor (0-0.05)
        if self.json_output:
            score += 0.05
        
        # Multi-step factor (0-0.05)
        if self.multi_step:
            score += 0.05
        
        # Context length factor (0-0.08)
        if self.context_length > 10000:
            score += 0.08
        elif self.context_length > 5000:
            score += 0.05
        elif self.context_length > 2000:
            score += 0.03
        
        return min(score, 1.0)


class TaskComplexityAnalyzer:
    """Analyzes task complexity to determine appropriate LLM routing."""
    
    def __init__(self):
        """Initialize complexity analyzer."""
        self.technical_terms = self._load_technical_terms()
        self.legal_concepts = self._load_legal_concepts()
        self.analysis_keywords = self._load_analysis_keywords()
        self.reasoning_keywords = self._load_reasoning_keywords()
    
    def _load_technical_terms(self) -> Set[str]:
        """Load technical terms that indicate complexity."""
        return {
            # Contract-specific terms
            "indemnification", "liability", "breach", "termination", "arbitration",
            "jurisdiction", "governing law", "force majeure", "confidentiality",
            "intellectual property", "non-disclosure", "non-compete", "severability",
            "assignment", "sublicense", "warranty", "representation", "covenant",
            "escrow", "liquidated damages", "specific performance", "injunctive relief",
            
            # Business terms
            "revenue", "profit", "equity", "valuation", "merger", "acquisition",
            "due diligence", "compliance", "regulatory", "fiduciary", "stakeholder",
            "shareholder", "board of directors", "corporate governance", "securities",
            
            # Technical/IT terms
            "software", "algorithm", "database", "api", "integration", "security",
            "encryption", "authentication", "authorization", "data protection",
            "gdpr", "hipaa", "sox", "pci", "iso", "certification", "audit"
        }
    
    def _load_legal_concepts(self) -> Set[str]:
        """Load legal concepts that indicate complexity."""
        return {
            # Legal procedures
            "litigation", "mediation", "arbitration", "discovery", "deposition",
            "subpoena", "injunction", "restraining order", "summary judgment",
            "class action", "settlement", "damages", "remedy", "relief",
            
            # Legal principles
            "precedent", "statute of limitations", "burden of proof", "standard of care",
            "reasonable person", "good faith", "fair dealing", "unconscionable",
            "material breach", "substantial performance", "frustration of purpose",
            
            # Contract law
            "consideration", "offer", "acceptance", "capacity", "legality",
            "mutual assent", "meeting of minds", "parol evidence", "integration",
            "modification", "novation", "accord and satisfaction", "rescission",
            
            # Regulatory
            "antitrust", "competition", "monopoly", "price fixing", "market share",
            "consumer protection", "environmental", "employment law", "discrimination",
            "harassment", "wrongful termination", "collective bargaining"
        }
    
    def _load_analysis_keywords(self) -> Set[str]:
        """Load keywords that indicate analysis depth."""
        return {
            "analyze", "evaluate", "assess", "examine", "review", "investigate",
            "determine", "identify", "compare", "contrast", "summarize", "extract",
            "categorize", "classify", "prioritize", "rank", "score", "rate",
            "recommend", "suggest", "advise", "propose", "optimize", "improve"
        }
    
    def _load_reasoning_keywords(self) -> Set[str]:
        """Load keywords that indicate reasoning requirements."""
        return {
            "because", "therefore", "consequently", "as a result", "due to",
            "given that", "considering", "taking into account", "based on",
            "reasoning", "rationale", "justification", "explanation", "logic",
            "inference", "conclusion", "deduction", "implication", "causation",
            "correlation", "relationship", "pattern", "trend", "insight"
        }
    
    def analyze_task_complexity(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> TaskComplexity:
        """
        Analyze task complexity based on prompt and context.
        
        Args:
            prompt: The task prompt/instruction
            context: Additional context (e.g., document content)
            task_type: Type of task (e.g., "contract_analysis", "negotiation")
            
        Returns:
            TaskComplexity level
        """
        factors = self._extract_complexity_factors(prompt, context, task_type)
        complexity_score = factors.calculate_score()
        
        # Map score to complexity level
        if complexity_score >= 0.5:
            complexity = TaskComplexity.COMPLEX
        elif complexity_score >= 0.2:
            complexity = TaskComplexity.MEDIUM
        else:
            complexity = TaskComplexity.SIMPLE
        
        logger.info(
            f"Task complexity analysis: score={complexity_score:.3f}, "
            f"level={complexity.value}, factors={factors}"
        )
        
        return complexity
    
    def _extract_complexity_factors(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> ComplexityFactors:
        """Extract complexity factors from prompt and context."""
        full_text = prompt
        if context:
            full_text += " " + context
        
        full_text_lower = full_text.lower()
        
        # Text length
        text_length = len(full_text)
        
        # Count technical terms
        technical_terms = sum(1 for term in self.technical_terms 
                            if term in full_text_lower)
        
        # Count legal concepts
        legal_concepts = sum(1 for concept in self.legal_concepts 
                           if concept in full_text_lower)
        
        # Analysis depth indicators
        analysis_depth = sum(1 for keyword in self.analysis_keywords 
                           if keyword in full_text_lower)
        
        # Reasoning requirements
        reasoning_required = sum(1 for keyword in self.reasoning_keywords 
                               if keyword in full_text_lower)
        
        # JSON output requirement
        json_output = any(keyword in full_text_lower for keyword in [
            "json", "structured", "format", "schema", "object", "array"
        ])
        
        # Multi-step task indicators
        multi_step = any(keyword in full_text_lower for keyword in [
            "first", "then", "next", "finally", "step", "phase", "stage",
            "subsequently", "afterwards", "following", "proceed"
        ])
        
        # Context length
        context_length = len(context) if context else 0
        
        # Task type complexity boost
        if task_type in ["contract_analysis", "legal_precedent", "risk_assessment"]:
            analysis_depth += 1
            legal_concepts += 2
        elif task_type in ["negotiation", "communication"]:
            reasoning_required += 1
        
        return ComplexityFactors(
            text_length=text_length,
            technical_terms=technical_terms,
            legal_concepts=legal_concepts,
            analysis_depth=analysis_depth,
            reasoning_required=reasoning_required,
            json_output=json_output,
            multi_step=multi_step,
            context_length=context_length
        )
    
    def get_recommended_providers(self, complexity: TaskComplexity) -> List[str]:
        """Get recommended providers for given complexity level."""
        if complexity == TaskComplexity.SIMPLE:
            return ["groq", "gpt-3.5-turbo", "claude-3-haiku"]
        elif complexity == TaskComplexity.MEDIUM:
            return ["gpt-3.5-turbo", "claude-3-sonnet", "gpt-4"]
        else:  # COMPLEX
            return ["gpt-4", "claude-3-opus", "gpt-4-turbo"]
    
    def estimate_cost_multiplier(self, complexity: TaskComplexity) -> float:
        """Estimate cost multiplier based on complexity."""
        if complexity == TaskComplexity.SIMPLE:
            return 1.0  # Base cost
        elif complexity == TaskComplexity.MEDIUM:
            return 2.5  # 2.5x more expensive
        else:  # COMPLEX
            return 15.0  # 15x more expensive (GPT-4 vs GPT-3.5)


# Global analyzer instance
_complexity_analyzer = None


def get_complexity_analyzer() -> TaskComplexityAnalyzer:
    """Get global task complexity analyzer instance."""
    global _complexity_analyzer
    if _complexity_analyzer is None:
        _complexity_analyzer = TaskComplexityAnalyzer()
    return _complexity_analyzer