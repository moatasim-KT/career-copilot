"""
CrewAI Agents Package

This package contains all the specialized CrewAI agents for job application tracking,
risk assessment, negotiation, and communication.
"""

from .base_agent import BaseContractAgent
from .contract_analyzer_agent import ContractAnalyzerAgent
from .risk_assessment_agent import RiskAssessmentAgent
from .legal_precedent_agent import LegalPrecedentAgent
from .negotiation_agent import NegotiationAgent
from .communication_agent import CommunicationAgent

__all__ = [
    "BaseContractAgent",
    "ContractAnalyzerAgent", 
    "RiskAssessmentAgent",
    "LegalPrecedentAgent",
    "NegotiationAgent",
    "CommunicationAgent",
]