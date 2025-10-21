"""
Contract structure identification and clause parsing service.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set

from ..core.logging import get_logger

logger = get_logger(__name__)


class ClauseType(Enum):
    """Types of contract clauses."""
    PARTIES = "parties"
    DEFINITIONS = "definitions"
    SCOPE_OF_WORK = "scope_of_work"
    PAYMENT_TERMS = "payment_terms"
    TERMINATION = "termination"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"
    FORCE_MAJEURE = "force_majeure"
    AMENDMENTS = "amendments"
    SEVERABILITY = "severability"
    ENTIRE_AGREEMENT = "entire_agreement"
    SIGNATURES = "signatures"
    GENERAL = "general"


class SectionType(Enum):
    """Types of contract sections."""
    HEADER = "header"
    PREAMBLE = "preamble"
    RECITALS = "recitals"
    DEFINITIONS = "definitions"
    MAIN_BODY = "main_body"
    SCHEDULES = "schedules"
    EXHIBITS = "exhibits"
    SIGNATURES = "signatures"
    FOOTER = "footer"


@dataclass
class ContractClause:
    """Represents a contract clause."""
    clause_type: ClauseType
    title: str
    content: str
    section_number: Optional[str]
    start_position: int
    end_position: int
    confidence: float
    risk_indicators: List[str]
    key_terms: List[str]


@dataclass
class ContractSection:
    """Represents a contract section."""
    section_type: SectionType
    title: str
    content: str
    section_number: Optional[str]
    start_position: int
    end_position: int
    clauses: List[ContractClause]
    subsections: List['ContractSection']


@dataclass
class ContractStructure:
    """Complete contract structure analysis."""
    title: str
    parties: List[str]
    effective_date: Optional[str]
    expiration_date: Optional[str]
    sections: List[ContractSection]
    clauses: List[ContractClause]
    key_terms: Dict[str, str]
    document_type: str
    confidence_score: float
    analysis_metadata: Dict[str, any]


class ContractStructureAnalyzer:
    """Analyzes contract structure and identifies clauses."""
    
    # Section header patterns
    SECTION_PATTERNS = {
        SectionType.HEADER: [
            r"(?i)^(.*(?:agreement|contract|memorandum|terms).*?)(?:\n|$)",
            r"(?i)^(.*(?:between|by and between).*?)(?:\n|$)",
        ],
        SectionType.PREAMBLE: [
            r"(?i)(this\s+(?:agreement|contract|memorandum).*?(?:entered\s+into|made\s+and\s+entered).*?)(?=\n\s*(?:recitals|whereas|definitions|\d+\.))",
            r"(?i)(know\s+all\s+(?:men|persons).*?)(?=\n\s*(?:recitals|whereas|definitions|\d+\.))",
        ],
        SectionType.RECITALS: [
            r"(?i)((?:recitals|background|whereas).*?)(?=\n\s*(?:definitions|now\s+therefore|\d+\.))",
            r"(?i)(whereas.*?)(?=\n\s*(?:now\s+therefore|definitions|\d+\.))",
        ],
        SectionType.DEFINITIONS: [
            r"(?i)((?:definitions|defined\s+terms).*?)(?=\n\s*\d+\.)",
            r"(?i)(\d+\.\s*definitions.*?)(?=\n\s*\d+\.)",
        ],
        SectionType.SIGNATURES: [
            r"(?i)((?:signatures?|execution|in\s+witness\s+whereof).*?)$",
            r"(?i)(by:.*?(?:name|title|date).*?)$",
        ],
    }
    
    # Clause identification patterns
    CLAUSE_PATTERNS = {
        ClauseType.PARTIES: [
            r"(?i)(parties?.*?)(?=\n\s*(?:\d+\.|[a-z]\)|whereas|definitions))",
            r"(?i)(between.*?and.*?)(?=\n\s*(?:\d+\.|whereas|recitals))",
        ],
        ClauseType.PAYMENT_TERMS: [
            r"(?i)(\d+\.\s*(?:payment|compensation|fees?).*?)(?=\n\s*\d+\.)",
            r"(?i)(payment\s+terms.*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
            r"(?i)(invoic(?:e|ing).*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
        ClauseType.TERMINATION: [
            r"(?i)(\d+\.\s*(?:termination|expir(?:ation|y)|end).*?)(?=\n\s*\d+\.)",
            r"(?i)(terminat(?:e|ion).*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
        ClauseType.LIABILITY: [
            r"(?i)(\d+\.\s*(?:liability|limitation\s+of\s+liability).*?)(?=\n\s*\d+\.)",
            r"(?i)(liabilit(?:y|ies).*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
        ClauseType.INDEMNIFICATION: [
            r"(?i)(\d+\.\s*indemnif(?:ication|y).*?)(?=\n\s*\d+\.)",
            r"(?i)(indemnif(?:y|ication).*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
        ClauseType.CONFIDENTIALITY: [
            r"(?i)(\d+\.\s*(?:confidential(?:ity)?|non-disclosure).*?)(?=\n\s*\d+\.)",
            r"(?i)(confidential(?:ity)?.*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
        ClauseType.INTELLECTUAL_PROPERTY: [
            r"(?i)(\d+\.\s*(?:intellectual\s+property|ip\s+rights?).*?)(?=\n\s*\d+\.)",
            r"(?i)(intellectual\s+property.*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
        ClauseType.GOVERNING_LAW: [
            r"(?i)(\d+\.\s*(?:governing\s+law|applicable\s+law).*?)(?=\n\s*\d+\.)",
            r"(?i)(governing\s+law.*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
        ClauseType.DISPUTE_RESOLUTION: [
            r"(?i)(\d+\.\s*(?:dispute\s+resolution|arbitration|mediation).*?)(?=\n\s*\d+\.)",
            r"(?i)(dispute.*?resolution.*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
        ClauseType.FORCE_MAJEURE: [
            r"(?i)(\d+\.\s*force\s+majeure.*?)(?=\n\s*\d+\.)",
            r"(?i)(force\s+majeure.*?)(?=\n\s*(?:\d+\.|[a-z]\)))",
        ],
    }
    
    # Risk indicator patterns
    RISK_INDICATORS = {
        "unlimited_liability": [
            r"(?i)unlimited\s+liability",
            r"(?i)without\s+limitation",
            r"(?i)no\s+cap\s+on\s+damages",
        ],
        "broad_indemnification": [
            r"(?i)indemnify.*?against\s+all",
            r"(?i)hold\s+harmless.*?from\s+any",
            r"(?i)defend.*?against\s+any",
        ],
        "automatic_renewal": [
            r"(?i)automatically\s+renew",
            r"(?i)auto-renew",
            r"(?i)unless\s+terminated.*?renew",
        ],
        "broad_termination": [
            r"(?i)terminate.*?at\s+any\s+time",
            r"(?i)terminate.*?without\s+cause",
            r"(?i)terminate.*?for\s+convenience",
        ],
        "exclusive_jurisdiction": [
            r"(?i)exclusive\s+jurisdiction",
            r"(?i)sole\s+jurisdiction",
            r"(?i)submit\s+to.*?jurisdiction",
        ],
        "liquidated_damages": [
            r"(?i)liquidated\s+damages",
            r"(?i)penalty.*?breach",
            r"(?i)damages.*?predetermined",
        ],
    }
    
    # Key terms patterns
    KEY_TERMS_PATTERNS = {
        "effective_date": [
            r"(?i)effective\s+(?:date|as\s+of)\s*:?\s*([^\n]+)",
            r"(?i)commenc(?:e|ing)\s+(?:on|as\s+of)\s*:?\s*([^\n]+)",
        ],
        "expiration_date": [
            r"(?i)expir(?:e|ation)\s+(?:date|on)\s*:?\s*([^\n]+)",
            r"(?i)terminat(?:e|ion)\s+(?:date|on)\s*:?\s*([^\n]+)",
        ],
        "governing_law": [
            r"(?i)governed\s+by.*?laws?\s+of\s+([^\n,.]+)",
            r"(?i)subject\s+to.*?laws?\s+of\s+([^\n,.]+)",
        ],
        "payment_terms": [
            r"(?i)payment.*?within\s+(\d+\s+days?)",
            r"(?i)net\s+(\d+)",
            r"(?i)due.*?(\d+\s+days?)",
        ],
    }
    
    def __init__(self):
        """Initialize the contract structure analyzer."""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, any]:
        """Compile regex patterns for efficient matching."""
        compiled = {
            "sections": {},
            "clauses": {},
            "risks": {},
            "terms": {},
        }
        
        # Compile section patterns
        for section_type, patterns in self.SECTION_PATTERNS.items():
            compiled["sections"][section_type] = [re.compile(p, re.MULTILINE | re.DOTALL) for p in patterns]
        
        # Compile clause patterns
        for clause_type, patterns in self.CLAUSE_PATTERNS.items():
            compiled["clauses"][clause_type] = [re.compile(p, re.MULTILINE | re.DOTALL) for p in patterns]
        
        # Compile risk patterns
        for risk_type, patterns in self.RISK_INDICATORS.items():
            compiled["risks"][risk_type] = [re.compile(p, re.MULTILINE | re.DOTALL) for p in patterns]
        
        # Compile key terms patterns
        for term_type, patterns in self.KEY_TERMS_PATTERNS.items():
            compiled["terms"][term_type] = [re.compile(p, re.MULTILINE | re.DOTALL) for p in patterns]
        
        return compiled
    
    def analyze_structure(self, content: str) -> ContractStructure:
        """
        Analyze contract structure and identify clauses.
        
        Args:
            content: Contract text content
            
        Returns:
            ContractStructure with identified sections and clauses
        """
        logger.info("Starting contract structure analysis")
        
        # Initialize structure
        structure = ContractStructure(
            title="",
            parties=[],
            effective_date=None,
            expiration_date=None,
            sections=[],
            clauses=[],
            key_terms={},
            document_type="contract",
            confidence_score=0.0,
            analysis_metadata={}
        )
        
        try:
            # Clean and normalize content
            normalized_content = self._normalize_content(content)
            
            # Extract document title
            structure.title = self._extract_title(normalized_content)
            
            # Identify sections
            structure.sections = self._identify_sections(normalized_content)
            
            # Identify clauses
            structure.clauses = self._identify_clauses(normalized_content)
            
            # Extract parties
            structure.parties = self._extract_parties(normalized_content)
            
            # Extract key terms
            structure.key_terms = self._extract_key_terms(normalized_content)
            
            # Set dates from key terms
            structure.effective_date = structure.key_terms.get("effective_date")
            structure.expiration_date = structure.key_terms.get("expiration_date")
            
            # Determine document type
            structure.document_type = self._determine_document_type(normalized_content)
            
            # Calculate confidence score
            structure.confidence_score = self._calculate_confidence_score(structure)
            
            # Add analysis metadata
            structure.analysis_metadata = {
                "content_length": len(content),
                "sections_found": len(structure.sections),
                "clauses_found": len(structure.clauses),
                "parties_found": len(structure.parties),
                "key_terms_found": len(structure.key_terms),
            }
            
            logger.info(f"Contract structure analysis completed: {len(structure.sections)} sections, {len(structure.clauses)} clauses")
            return structure
            
        except Exception as e:
            logger.error(f"Error during contract structure analysis: {e}", exc_info=True)
            structure.analysis_metadata["error"] = str(e)
            return structure
    
    def _normalize_content(self, content: str) -> str:
        """Normalize contract content for analysis."""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Normalize section numbering
        content = re.sub(r'(?i)section\s+(\d+)\.?', r'\1.', content)
        content = re.sub(r'(?i)article\s+(\d+)\.?', r'\1.', content)
        
        # Normalize bullet points
        content = re.sub(r'^\s*[•·▪▫]\s*', '- ', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def _extract_title(self, content: str) -> str:
        """Extract document title."""
        lines = content.split('\n')
        
        # Look for title in first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like a title
            if (len(line) > 10 and 
                any(keyword in line.lower() for keyword in ['agreement', 'contract', 'memorandum', 'terms']) and
                not line.lower().startswith('this')):
                return line
        
        # Fallback to first non-empty line
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 5:
                return line
        
        return "Untitled Contract"
    
    def _identify_sections(self, content: str) -> List[ContractSection]:
        """Identify contract sections."""
        sections = []
        
        for section_type, patterns in self.compiled_patterns["sections"].items():
            for pattern in patterns:
                matches = pattern.finditer(content)
                
                for match in matches:
                    section = ContractSection(
                        section_type=section_type,
                        title=self._extract_section_title(match.group(1)),
                        content=match.group(1),
                        section_number=None,
                        start_position=match.start(),
                        end_position=match.end(),
                        clauses=[],
                        subsections=[]
                    )
                    sections.append(section)
        
        # Sort sections by position
        sections.sort(key=lambda s: s.start_position)
        
        # Remove overlapping sections
        sections = self._remove_overlapping_sections(sections)
        
        return sections
    
    def _identify_clauses(self, content: str) -> List[ContractClause]:
        """Identify contract clauses."""
        clauses = []
        
        for clause_type, patterns in self.compiled_patterns["clauses"].items():
            for pattern in patterns:
                matches = pattern.finditer(content)
                
                for match in matches:
                    clause_content = match.group(1)
                    
                    # Extract risk indicators
                    risk_indicators = self._identify_risk_indicators(clause_content)
                    
                    # Extract key terms
                    key_terms = self._extract_clause_key_terms(clause_content, clause_type)
                    
                    # Calculate confidence
                    confidence = self._calculate_clause_confidence(clause_content, clause_type)
                    
                    clause = ContractClause(
                        clause_type=clause_type,
                        title=self._extract_clause_title(clause_content),
                        content=clause_content,
                        section_number=self._extract_section_number(clause_content),
                        start_position=match.start(),
                        end_position=match.end(),
                        confidence=confidence,
                        risk_indicators=risk_indicators,
                        key_terms=key_terms
                    )
                    clauses.append(clause)
        
        # Sort clauses by position
        clauses.sort(key=lambda c: c.start_position)
        
        # Remove overlapping clauses
        clauses = self._remove_overlapping_clauses(clauses)
        
        return clauses
    
    def _extract_parties(self, content: str) -> List[str]:
        """Extract contract parties."""
        parties = []
        
        # Look for party patterns
        party_patterns = [
            r"(?i)between\s+(.*?)\s+(?:and|&)\s+(.*?)(?:\n|,|\()",
            r"(?i)by\s+and\s+between\s+(.*?)\s+(?:and|&)\s+(.*?)(?:\n|,|\()",
            r"(?i)party\s+(?:of\s+the\s+)?first\s+part[:\s]+(.*?)(?:\n|,|\()",
            r"(?i)party\s+(?:of\s+the\s+)?second\s+part[:\s]+(.*?)(?:\n|,|\()",
        ]
        
        for pattern in party_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                for group in match.groups():
                    if group:
                        party = self._clean_party_name(group.strip())
                        if party and party not in parties:
                            parties.append(party)
        
        return parties[:10]  # Limit to reasonable number
    
    def _extract_key_terms(self, content: str) -> Dict[str, str]:
        """Extract key contract terms."""
        key_terms = {}
        
        for term_type, patterns in self.compiled_patterns["terms"].items():
            for pattern in patterns:
                match = pattern.search(content)
                if match and match.group(1):
                    key_terms[term_type] = match.group(1).strip()
                    break  # Use first match
        
        return key_terms
    
    def _identify_risk_indicators(self, content: str) -> List[str]:
        """Identify risk indicators in clause content."""
        risks = []
        
        for risk_type, patterns in self.compiled_patterns["risks"].items():
            for pattern in patterns:
                if pattern.search(content):
                    risks.append(risk_type)
                    break  # Avoid duplicates
        
        return risks
    
    def _extract_clause_key_terms(self, content: str, clause_type: ClauseType) -> List[str]:
        """Extract key terms from clause content."""
        key_terms = []
        
        # Define clause-specific term patterns
        term_patterns = {
            ClauseType.PAYMENT_TERMS: [
                r"(?i)(\d+\s+days?)",
                r"(?i)(net\s+\d+)",
                r"(?i)(\$[\d,]+(?:\.\d{2})?)",
            ],
            ClauseType.TERMINATION: [
                r"(?i)(\d+\s+days?\s+notice)",
                r"(?i)(without\s+cause)",
                r"(?i)(for\s+convenience)",
            ],
            ClauseType.LIABILITY: [
                r"(?i)(unlimited)",
                r"(?i)(limited\s+to\s+\$[\d,]+)",
                r"(?i)(consequential\s+damages)",
            ],
        }
        
        patterns = term_patterns.get(clause_type, [])
        for pattern in patterns:
            matches = re.findall(pattern, content)
            key_terms.extend(matches)
        
        return key_terms[:5]  # Limit to reasonable number
    
    def _calculate_clause_confidence(self, content: str, clause_type: ClauseType) -> float:
        """Calculate confidence score for clause identification."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on keyword matches
        keywords = {
            ClauseType.PAYMENT_TERMS: ["payment", "invoice", "fee", "compensation"],
            ClauseType.TERMINATION: ["terminate", "expir", "end", "cancel"],
            ClauseType.LIABILITY: ["liable", "liability", "damages", "loss"],
            ClauseType.CONFIDENTIALITY: ["confidential", "non-disclosure", "proprietary"],
        }
        
        clause_keywords = keywords.get(clause_type, [])
        content_lower = content.lower()
        
        for keyword in clause_keywords:
            if keyword in content_lower:
                confidence += 0.1
        
        # Increase confidence for structured content
        if re.search(r'\d+\.', content):  # Numbered sections
            confidence += 0.1
        
        if len(content) > 100:  # Substantial content
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _determine_document_type(self, content: str) -> str:
        """Determine the type of contract document."""
        content_lower = content.lower()
        
        type_indicators = {
            "service_agreement": ["service", "services", "consulting", "professional"],
            "employment_agreement": ["employment", "employee", "employer", "job"],
            "nda": ["non-disclosure", "confidentiality", "proprietary"],
            "license_agreement": ["license", "licensing", "intellectual property"],
            "purchase_agreement": ["purchase", "sale", "buy", "sell"],
            "lease_agreement": ["lease", "rent", "rental", "tenant"],
        }
        
        for doc_type, indicators in type_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                return doc_type
        
        return "general_contract"
    
    def _calculate_confidence_score(self, structure: ContractStructure) -> float:
        """Calculate overall confidence score for structure analysis."""
        score = 0.0
        
        # Base score for having content
        if structure.sections or structure.clauses:
            score += 0.3
        
        # Score for identified sections
        if structure.sections:
            score += min(0.2, len(structure.sections) * 0.05)
        
        # Score for identified clauses
        if structure.clauses:
            score += min(0.3, len(structure.clauses) * 0.03)
        
        # Score for identified parties
        if structure.parties:
            score += min(0.1, len(structure.parties) * 0.05)
        
        # Score for key terms
        if structure.key_terms:
            score += min(0.1, len(structure.key_terms) * 0.02)
        
        return min(score, 1.0)
    
    def _extract_section_title(self, content: str) -> str:
        """Extract title from section content."""
        lines = content.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # Clean up the title
        title = re.sub(r'^\d+\.\s*', '', first_line)  # Remove numbering
        title = re.sub(r'^(section|article)\s+\d+\s*[:\-]?\s*', '', title, flags=re.IGNORECASE)
        
        return title[:100] if title else "Untitled Section"
    
    def _extract_clause_title(self, content: str) -> str:
        """Extract title from clause content."""
        lines = content.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # Clean up the title
        title = re.sub(r'^\d+\.\s*', '', first_line)  # Remove numbering
        
        return title[:100] if title else "Untitled Clause"
    
    def _extract_section_number(self, content: str) -> Optional[str]:
        """Extract section number from content."""
        match = re.match(r'^(\d+(?:\.\d+)*)', content.strip())
        return match.group(1) if match else None
    
    def _clean_party_name(self, name: str) -> str:
        """Clean and normalize party name."""
        # Remove common legal suffixes and prefixes
        name = re.sub(r'\b(?:inc|corp|llc|ltd|co|company|corporation|incorporated|limited)\b\.?', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(?:a|an|the)\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[,\(\)"\']', '', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()
    
    def _remove_overlapping_sections(self, sections: List[ContractSection]) -> List[ContractSection]:
        """Remove overlapping sections, keeping the most specific ones."""
        if not sections:
            return sections
        
        # Sort by start position
        sections.sort(key=lambda s: s.start_position)
        
        filtered = [sections[0]]
        
        for section in sections[1:]:
            last_section = filtered[-1]
            
            # Check for overlap
            if section.start_position < last_section.end_position:
                # Keep the longer/more specific section
                if len(section.content) > len(last_section.content):
                    filtered[-1] = section
            else:
                filtered.append(section)
        
        return filtered
    
    def _remove_overlapping_clauses(self, clauses: List[ContractClause]) -> List[ContractClause]:
        """Remove overlapping clauses, keeping the most confident ones."""
        if not clauses:
            return clauses
        
        # Sort by start position
        clauses.sort(key=lambda c: c.start_position)
        
        filtered = [clauses[0]]
        
        for clause in clauses[1:]:
            last_clause = filtered[-1]
            
            # Check for overlap
            if clause.start_position < last_clause.end_position:
                # Keep the clause with higher confidence
                if clause.confidence > last_clause.confidence:
                    filtered[-1] = clause
            else:
                filtered.append(clause)
        
        return filtered


# Global service instance
_contract_structure_analyzer: Optional[ContractStructureAnalyzer] = None


def get_contract_structure_analyzer() -> ContractStructureAnalyzer:
    """Get or create the global contract structure analyzer instance."""
    global _contract_structure_analyzer
    
    if _contract_structure_analyzer is None:
        _contract_structure_analyzer = ContractStructureAnalyzer()
    
    return _contract_structure_analyzer