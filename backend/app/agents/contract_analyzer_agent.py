"""
Enhanced Career Copilot Agent

This module implements the production-ready contract analyzer agent with:
- Multi-LLM provider support for intelligent routing
- Advanced contract structure analysis
- Contract comparison and diff analysis
- Result caching and optimization
- Comprehensive error handling and monitoring
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from crewai import Task

from ..core.exceptions import ErrorCategory, ErrorSeverity, ValidationError, WorkflowExecutionError
from ..core.langsmith_integration import trace_ai_operation
from ..services.document_processor import get_document_processor_service
from ..services.llm_manager import get_enhanced_llm_manager, TaskType, RoutingCriteria, LLMProvider
from ..services.contract_structure_analyzer import get_contract_structure_analyzer, ContractStructure
from ..services.llm_cache_manager import get_llm_cache_manager
from ..monitoring.metrics_collector import get_metrics_collector
from .base_agent import AgentCommunicationProtocol, BaseContractAgent
from ..core.retry_handler import with_retry, RetryConfig
from ..core.correlation_manager import log_with_correlation, correlation_context
from ..core.agent_cache_manager import AgentType

logger = logging.getLogger(__name__)
metrics_collector = get_metrics_collector()


class EnhancedContractAnalyzerAgent(BaseContractAgent):
    """
    Production-ready contract analyzer agent with multi-LLM support and advanced capabilities.
    
    Enhanced Responsibilities:
    - Multi-provider LLM analysis with intelligent routing
    - Advanced contract structure identification
    - Contract comparison and diff analysis
    - Intelligent caching and optimization
    - Comprehensive error handling and monitoring
    - Performance metrics collection
    """
    
    def __init__(
        self,
        communication_protocol: AgentCommunicationProtocol,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Enhanced Career Copilot Agent.
        
        Args:
            communication_protocol: Shared communication protocol
            config: Optional configuration parameters
        """
        super().__init__(
            agent_name="enhanced_contract_analyzer",
            role="Senior AI-Powered Contract Analysis Specialist",
            goal="Provide comprehensive job application tracking using multiple AI providers with advanced structure analysis, comparison capabilities, and optimized performance",
            backstory="""You are an advanced AI-powered legal analyst with expertise in leveraging multiple 
            AI models for comprehensive job application tracking. You combine traditional legal analysis with 
            cutting-edge AI capabilities to provide detailed contract structure analysis, clause identification, 
            risk assessment, and contract comparison. Your approach is methodical, leveraging the best AI 
            provider for each specific analysis task while maintaining high accuracy and performance through 
            intelligent caching and optimization.""",
            communication_protocol=communication_protocol,
            config=config
        )
        
        # Initialize services
        self._initialize_services()
        
        # Configuration
        self.config = config or {}
        self.enable_caching = self.config.get("enable_caching", True)
        self.enable_multi_llm = self.config.get("enable_multi_llm", True)
        self.enable_advanced_analysis = self.config.get("enable_advanced_analysis", True)
        self.cache_ttl = self.config.get("cache_ttl", 3600)  # 1 hour default
        
        # Analysis cache for contract comparisons
        self.analysis_cache = {}
        
        # Set task type for fallback manager
        self.task_type = "contract_analysis"
        self.required_capabilities = ["analysis", "reasoning", "complex_tasks"]
        
        # Set agent type for caching
        self.agent_type = AgentType.CONTRACT_ANALYZER
        
        logger.info("Enhanced Career Copilot Agent initialized with multi-LLM support")
    
    def _initialize_services(self):
        """Initialize all required services with error handling."""
        # Document processor service
        try:
            self.document_processor = get_document_processor_service()
        except Exception as e:
            logger.warning(f"Failed to initialize document processor: {e}")
            self.document_processor = None
        
        # Enhanced LLM manager
        try:
            self.llm_manager = get_enhanced_llm_manager()
        except Exception as e:
            logger.warning(f"Failed to initialize enhanced LLM manager: {e}")
            self.llm_manager = None
        
        # Contract structure analyzer
        try:
            self.structure_analyzer = get_contract_structure_analyzer()
        except Exception as e:
            logger.warning(f"Failed to initialize structure analyzer: {e}")
            self.structure_analyzer = None
        
        # LLM cache manager
        try:
            self.cache_manager = get_llm_cache_manager()
        except Exception as e:
            logger.warning(f"Failed to initialize cache manager: {e}")
            self.cache_manager = None
    
    @trace_ai_operation("enhanced_contract_analysis", "agent")
    async def execute_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute enhanced job application tracking task with multi-LLM support and caching.
        
        Args:
            task_input: Input containing contract_text, contract_filename, and optional parameters
            
        Returns:
            Dict[str, Any]: Comprehensive analysis results
        """
        start_time = datetime.now()
        
        # Validate input
        validation_errors = self.validate_input(
            task_input, 
            ["contract_text", "contract_filename"]
        )
        
        if validation_errors:
            raise ValidationError(f"Invalid input for job application tracking: {'; '.join(validation_errors)}")
        
        contract_text = task_input["contract_text"]
        contract_filename = task_input["contract_filename"]
        workflow_id = task_input.get("workflow_id", "unknown")
        analysis_type = task_input.get("analysis_type", "comprehensive")
        comparison_contract = task_input.get("comparison_contract")
        
        logger.info(f"Starting enhanced job application tracking for {contract_filename} (workflow: {workflow_id})")
        
        try:
            # Record metrics
            metrics_collector.increment_active_analyses()
            
            # Check cache first if enabled
            cached_result = None
            if self.enable_caching and self.cache_manager:
                cached_result = await self._get_cached_analysis(contract_text, analysis_type)
                if cached_result:
                    # Cache hit - record in metadata
                    pass
                    logger.info(f"Using cached analysis for {contract_filename}")
                    cached_result["workflow_id"] = workflow_id
                    cached_result["original_filename"] = contract_filename
                    return cached_result
            
            # Step 1: Preprocess contract text
            preprocessed_text = self._preprocess_contract_text(contract_text)
            
            # Step 2: Advanced structure analysis
            contract_structure = await self._advanced_structure_analysis(
                preprocessed_text, contract_filename
            )
            
            # Step 3: Multi-LLM clause analysis
            identified_clauses = await self._multi_llm_clause_analysis(
                preprocessed_text, contract_structure
            )
            
            # Step 4: Risk and compliance analysis
            risk_analysis = await self._analyze_risks_and_compliance(
                preprocessed_text, identified_clauses
            )
            
            # Step 5: Contract comparison if requested
            comparison_results = None
            if comparison_contract:
                comparison_results = await self._compare_contracts(
                    contract_text, comparison_contract, contract_filename
                )
            
            # Step 6: Generate comprehensive metadata
            analysis_metadata = self._generate_comprehensive_metadata(
                contract_text, contract_filename, contract_structure, 
                identified_clauses, risk_analysis, start_time
            )
            
            # Compile comprehensive results
            results = {
                "success": True,
                "contract_structure": contract_structure,
                "identified_clauses": identified_clauses,
                "risk_analysis": risk_analysis,
                "analysis_metadata": analysis_metadata,
                "preprocessed_text": preprocessed_text,
                "original_filename": contract_filename,
                "workflow_id": workflow_id,
                "analysis_type": analysis_type,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "llm_providers_used": self._get_providers_used(),
                "cache_status": "miss" if not cached_result else "hit"
            }
            
            # Add comparison results if available
            if comparison_results:
                results["comparison_results"] = comparison_results
            
            # Cache results if enabled
            if self.enable_caching and self.cache_manager:
                await self._cache_analysis_results(contract_text, analysis_type, results)
            
            # Record success metrics
            metrics_collector.record_contract_analysis(
                status="success",
                model_used=", ".join(getattr(self, '_providers_used', ['unknown'])),
                duration=results["processing_time"],
                risk_score=risk_analysis.get("risk_score", 0.0),
                contract_type=contract_structure.get("contract_type", "unknown"),
                clauses_count=len(identified_clauses)
            )
            
            logger.info(
                f"Enhanced job application tracking completed for {contract_filename}: "
                f"{len(identified_clauses)} clauses, "
                f"{len(risk_analysis.get('risk_indicators', []))} risks identified "
                f"in {results['processing_time']:.2f}s"
            )
            
            return results
            
        except Exception as e:
            # Record error metrics
            metrics_collector.record_contract_analysis(
                status="error",
                model_used="unknown",
                duration=(datetime.now() - start_time).total_seconds(),
                contract_type="unknown"
            )
            
            error_msg = f"Enhanced job application tracking failed for {contract_filename}: {e}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "contract_filename": contract_filename,
                "workflow_id": workflow_id,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "analysis_type": analysis_type
            }
    
    async def _get_cached_analysis(self, contract_text: str, analysis_type: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis results if available."""
        try:
            if not self.cache_manager:
                return None
            
            # Generate cache key
            cache_key = self._generate_cache_key(contract_text, analysis_type)
            
            # Check cache
            messages = [{"role": "user", "content": f"analyze_contract_{analysis_type}_{cache_key}"}]
            cached_response = await self.cache_manager.get_cached_response(
                messages, "contract_analysis", task_type=TaskType.CONTRACT_ANALYSIS
            )
            
            if cached_response and cached_response.get("cached"):
                return cached_response.get("analysis_results")
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get cached analysis: {e}")
            return None
    
    async def _cache_analysis_results(
        self, 
        contract_text: str, 
        analysis_type: str, 
        results: Dict[str, Any]
    ) -> bool:
        """Cache analysis results for future use."""
        try:
            if not self.cache_manager:
                return False
            
            # Generate cache key
            cache_key = self._generate_cache_key(contract_text, analysis_type)
            
            # Prepare cache response
            cache_response = {
                "content": "cached_analysis",
                "analysis_results": results,
                "cached_at": datetime.now().isoformat()
            }
            
            # Cache the response
            messages = [{"role": "user", "content": f"analyze_contract_{analysis_type}_{cache_key}"}]
            return await self.cache_manager.cache_response(
                messages, "contract_analysis", cache_response, 
                task_type=TaskType.CONTRACT_ANALYSIS
            )
            
        except Exception as e:
            logger.warning(f"Failed to cache analysis results: {e}")
            return False
    
    def _generate_cache_key(self, contract_text: str, analysis_type: str) -> str:
        """Generate a cache key for the job application tracking."""
        # Create a hash of the contract text and analysis type
        content_hash = hashlib.sha256(contract_text.encode()).hexdigest()
        return f"{analysis_type}_{content_hash[:16]}"
    
    def _get_providers_used(self) -> List[str]:
        """Get list of LLM providers used in the analysis."""
        # This would be populated during analysis
        return getattr(self, '_providers_used', [])
    
    def _preprocess_contract_text(self, contract_text: str) -> str:
        """
        Preprocess contract text for better analysis.
        
        Args:
            contract_text: Raw contract text
            
        Returns:
            str: Preprocessed contract text
        """
        try:
            # Basic text cleaning
            text = contract_text.strip()
            
            # Normalize whitespace
            import re
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            
            # Remove excessive formatting characters
            text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\{\}\-\"\'\n\r]', ' ', text)
            
            # Ensure proper sentence separation
            text = re.sub(r'\.([A-Z])', r'. \1', text)
            
            logger.debug(f"Preprocessed contract text: {len(text)} characters")
            
            return text
            
        except Exception as e:
            logger.warning(f"Text preprocessing failed, using original text: {e}")
            return contract_text
    
    async def _advanced_structure_analysis(
        self, 
        contract_text: str, 
        contract_filename: str
    ) -> Dict[str, Any]:
        """
        Perform advanced contract structure analysis using multiple approaches.
        
        Args:
            contract_text: Preprocessed contract text
            contract_filename: Original filename for context
            
        Returns:
            Dict[str, Any]: Comprehensive structure analysis results
        """
        try:
            structure_results = {}
            
            # Method 1: Use contract structure analyzer service
            if self.structure_analyzer:
                logger.debug("Running contract structure analyzer")
                structure_analysis = self.structure_analyzer.analyze_structure(contract_text)
                
                structure_results["analyzer_results"] = {
                    "contract_type": structure_analysis.document_type,
                    "main_sections": [
                        {
                            "title": section.title,
                            "type": section.section_type.value,
                            "content_length": len(section.content),
                            "section_number": section.section_number,
                            "confidence": getattr(section, 'confidence', 0.8)
                        } for section in structure_analysis.sections
                    ],
                    "parties": structure_analysis.parties,
                    "term_information": {
                        "effective_date": structure_analysis.effective_date,
                        "expiration_date": structure_analysis.expiration_date
                    },
                    "governing_law": structure_analysis.key_terms.get("governing_law", "Unknown"),
                    "confidence_score": structure_analysis.confidence_score,
                    "key_terms": structure_analysis.key_terms,
                    "analysis_metadata": structure_analysis.analysis_metadata
                }
            
            # Method 2: Multi-LLM AI-powered analysis
            if self.enable_multi_llm and self.llm_manager:
                logger.debug("Running multi-LLM structure analysis")
                ai_structure = await self._multi_llm_structure_analysis(contract_text)
                if ai_structure:
                    structure_results["ai_analysis"] = ai_structure
            
            # Method 3: Combine and enhance results
            combined_structure = self._combine_structure_analyses(
                structure_results, contract_text, contract_filename
            )
            
            return combined_structure
            
        except Exception as e:
            logger.error(f"Advanced structure analysis failed: {e}")
            # Fallback to basic analysis
            return await self._identify_contract_structure(contract_text)
    
    async def _multi_llm_structure_analysis(self, contract_text: str) -> Optional[Dict[str, Any]]:
        """
        Perform structure analysis using multiple LLM providers for enhanced accuracy.
        
        Args:
            contract_text: Contract text to analyze
            
        Returns:
            Optional[Dict[str, Any]]: Multi-LLM structure analysis results
        """
        try:
            # Limit text for LLM processing
            text_sample = contract_text[:8000] if len(contract_text) > 8000 else contract_text
            
            structure_prompt = f"""
            Analyze the following contract and provide a comprehensive structure analysis. 
            Return a JSON response with the following format:
            
            {{
                "contract_type": "specific type (e.g., Service Agreement, Employment Contract, NDA)",
                "document_classification": "classification based on content and structure",
                "main_sections": [
                    {{
                        "title": "section title",
                        "type": "section type",
                        "content_summary": "brief summary of section content",
                        "importance": "high/medium/low",
                        "word_count": estimated_word_count
                    }}
                ],
                "parties_analysis": {{
                    "primary_parties": ["party1", "party2"],
                    "party_roles": {{"party1": "role", "party2": "role"}},
                    "party_obligations": {{"party1": ["obligation1"], "party2": ["obligation2"]}}
                }},
                "contract_terms": {{
                    "effective_date": "date or null",
                    "expiration_date": "date or null",
                    "term_duration": "duration description",
                    "renewal_terms": "renewal information"
                }},
                "governing_framework": {{
                    "governing_law": "jurisdiction",
                    "dispute_resolution": "method",
                    "compliance_requirements": ["requirement1", "requirement2"]
                }},
                "document_quality": {{
                    "structure_clarity": "score 1-10",
                    "completeness": "score 1-10",
                    "legal_soundness": "score 1-10"
                }},
                "key_provisions_summary": ["provision1", "provision2"],
                "potential_issues": ["issue1", "issue2"],
                "confidence_assessment": 0.95
            }}
            
            Contract text:
            {text_sample}
            """
            
            # Try multiple providers for enhanced accuracy
            providers_to_try = [LLMProvider.OPENAI, LLMProvider.GROQ]
            if hasattr(self, '_providers_used'):
                self._providers_used = []
            else:
                self._providers_used = []
            
            best_result = None
            highest_confidence = 0.0
            
            for provider in providers_to_try:
                try:
                    # Get completion from specific provider
                    response = await self.llm_manager.get_completion(
                        prompt=structure_prompt,
                        task_type=TaskType.CONTRACT_ANALYSIS,
                        preferred_provider=provider.value,
                        temperature=0.1,
                        max_tokens=2000
                    )
                    
                    if response and response.content:
                        self._providers_used.append(provider.value)
                        
                        # Parse JSON response
                        parsed_result = self._parse_llm_structure_response(response.content)
                        
                        if parsed_result:
                            confidence = parsed_result.get("confidence_assessment", 0.0)
                            if confidence > highest_confidence:
                                highest_confidence = confidence
                                best_result = parsed_result
                                best_result["provider_used"] = provider.value
                                best_result["response_metadata"] = {
                                    "processing_time": response.processing_time,
                                    "token_usage": response.token_usage,
                                    "confidence_score": response.confidence_score
                                }
                
                except Exception as e:
                    logger.warning(f"Structure analysis failed with provider {provider.value}: {e}")
                    continue
            
            return best_result
            
        except Exception as e:
            logger.error(f"Multi-LLM structure analysis failed: {e}")
            return None
    
    def _parse_llm_structure_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Parse LLM structure analysis response."""
        try:
            # Try to extract JSON from the response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM structure response: {e}")
            return None
    
    def _combine_structure_analyses(
        self, 
        structure_results: Dict[str, Any], 
        contract_text: str, 
        contract_filename: str
    ) -> Dict[str, Any]:
        """
        Combine results from different structure analysis methods.
        
        Args:
            structure_results: Results from different analysis methods
            contract_text: Original contract text
            contract_filename: Contract filename
            
        Returns:
            Dict[str, Any]: Combined and enhanced structure analysis
        """
        combined = {
            "contract_type": "Unknown",
            "document_classification": "general_contract",
            "main_sections": [],
            "parties": [],
            "term_information": {},
            "governing_law": "Unknown",
            "confidence_score": 0.0,
            "analysis_methods_used": list(structure_results.keys()),
            "enhanced_metadata": {}
        }
        
        # Combine analyzer results
        if "analyzer_results" in structure_results:
            analyzer = structure_results["analyzer_results"]
            combined.update({
                "contract_type": analyzer.get("contract_type", "Unknown"),
                "main_sections": analyzer.get("main_sections", []),
                "parties": analyzer.get("parties", []),
                "term_information": analyzer.get("term_information", {}),
                "governing_law": analyzer.get("governing_law", "Unknown"),
                "confidence_score": analyzer.get("confidence_score", 0.0)
            })
        
        # Enhance with AI analysis
        if "ai_analysis" in structure_results:
            ai_analysis = structure_results["ai_analysis"]
            
            # Use AI classification if available
            if ai_analysis.get("document_classification"):
                combined["document_classification"] = ai_analysis["document_classification"]
            
            # Enhance parties information
            if ai_analysis.get("parties_analysis"):
                parties_analysis = ai_analysis["parties_analysis"]
                combined["enhanced_parties"] = {
                    "primary_parties": parties_analysis.get("primary_parties", []),
                    "party_roles": parties_analysis.get("party_roles", {}),
                    "party_obligations": parties_analysis.get("party_obligations", {})
                }
            
            # Add contract terms analysis
            if ai_analysis.get("contract_terms"):
                combined["enhanced_terms"] = ai_analysis["contract_terms"]
            
            # Add governing framework
            if ai_analysis.get("governing_framework"):
                combined["governing_framework"] = ai_analysis["governing_framework"]
            
            # Add document quality assessment
            if ai_analysis.get("document_quality"):
                combined["document_quality"] = ai_analysis["document_quality"]
            
            # Add key provisions and issues
            combined["key_provisions_summary"] = ai_analysis.get("key_provisions_summary", [])
            combined["potential_issues"] = ai_analysis.get("potential_issues", [])
            
            # Update confidence with AI assessment
            ai_confidence = ai_analysis.get("confidence_assessment", 0.0)
            combined["confidence_score"] = max(combined["confidence_score"], ai_confidence)
        
        # Add enhanced metadata
        combined["enhanced_metadata"] = {
            "analysis_timestamp": datetime.now().isoformat(),
            "contract_filename": contract_filename,
            "text_length": len(contract_text),
            "word_count": len(contract_text.split()),
            "analysis_completeness": len(structure_results),
            "providers_used": getattr(self, '_providers_used', [])
        }
        
        return combined
    
    async def _identify_contract_structure(self, contract_text: str) -> Dict[str, Any]:
        """
        Identify the overall structure of the contract.
        
        Args:
            contract_text: Preprocessed contract text
            
        Returns:
            Dict[str, Any]: Contract structure information
        """
        try:
            # First try using the enhanced LLM manager for AI-powered analysis
            if self.llm_manager:
                structure_info = await self._ai_powered_structure_analysis(contract_text)
                if structure_info:
                    return structure_info
            
            # Use the contract structure analyzer service for comprehensive analysis
            if self.document_processor and hasattr(self.document_processor, 'structure_analyzer'):
                structure_result = self.document_processor.structure_analyzer.analyze_structure(contract_text)
                
                # Convert ContractStructure to dict format
                structure_info = {
                    "contract_type": structure_result.document_type,
                    "main_sections": [
                        {
                            "title": section.title,
                            "type": section.section_type.value,
                            "content_length": len(section.content)
                        } for section in structure_result.sections
                    ],
                    "parties": structure_result.parties,
                    "term_information": {
                        "effective_date": structure_result.effective_date,
                        "expiration_date": structure_result.expiration_date
                    },
                    "governing_law": structure_result.key_terms.get("governing_law", "Unknown"),
                    "organization": "Structured" if len(structure_result.sections) > 3 else "Simple",
                    "confidence_score": structure_result.confidence_score,
                    "key_terms": structure_result.key_terms
                }
                
                return structure_info
            else:
                # Fallback to basic structure analysis
                return self._basic_structure_analysis(contract_text)
            
        except Exception as e:
            logger.error(f"Structure identification failed: {e}")
            
            # Fallback to basic structure analysis
            return self._basic_structure_analysis(contract_text)
    
    async def _multi_llm_clause_analysis(
        self, 
        contract_text: str, 
        contract_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Perform advanced clause analysis using multiple LLM providers and structure information.
        
        Args:
            contract_text: Preprocessed contract text
            contract_structure: Previously analyzed contract structure
            
        Returns:
            List[Dict[str, Any]]: Enhanced clause analysis results
        """
        try:
            clause_results = []
            
            # Method 1: Use structure analyzer for baseline clause extraction
            if self.structure_analyzer:
                logger.debug("Running structure analyzer clause extraction")
                structure_analysis = self.structure_analyzer.analyze_structure(contract_text)
                
                for i, clause in enumerate(structure_analysis.clauses):
                    clause_dict = {
                        "clause_text": clause.content,
                        "clause_type": clause.clause_type.value,
                        "clause_category": self._categorize_clause_type(clause.clause_type.value),
                        "clause_index": i + 1,
                        "key_provisions": clause.key_terms,
                        "risk_indicators": clause.risk_indicators,
                        "legal_significance": self._assess_significance_from_confidence(clause.confidence),
                        "confidence": clause.confidence,
                        "section_number": clause.section_number,
                        "start_position": clause.start_position,
                        "end_position": clause.end_position,
                        "analysis_method": "structure_analyzer"
                    }
                    clause_results.append(clause_dict)
            
            # Method 2: Multi-LLM enhanced clause analysis
            if self.enable_multi_llm and self.llm_manager:
                logger.debug("Running multi-LLM clause analysis")
                ai_clauses = await self._ai_powered_clause_extraction(contract_text, contract_structure)
                
                if ai_clauses:
                    # Merge AI-enhanced clauses with structure analyzer results
                    clause_results = self._merge_clause_analyses(clause_results, ai_clauses)
            
            # Method 3: Enhanced pattern-based extraction as fallback/supplement
            if not clause_results or len(clause_results) < 3:
                logger.debug("Running enhanced pattern-based clause extraction")
                pattern_clauses = self._enhanced_pattern_clause_extraction(contract_text)
                clause_results.extend(pattern_clauses)
            
            # Post-processing: Remove duplicates and enhance
            final_clauses = self._post_process_clauses(clause_results, contract_text)
            
            return final_clauses
            
        except Exception as e:
            logger.error(f"Multi-LLM clause analysis failed: {e}")
            # Fallback to original method
            return await self._extract_and_classify_clauses(contract_text)
    
    async def _ai_powered_clause_extraction(
        self, 
        contract_text: str, 
        contract_structure: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Use AI to extract and classify clauses with enhanced context.
        
        Args:
            contract_text: Contract text to analyze
            contract_structure: Structure context for better analysis
            
        Returns:
            Optional[List[Dict[str, Any]]]: AI-extracted clauses
        """
        try:
            # Prepare context from structure analysis
            context_info = {
                "contract_type": contract_structure.get("contract_type", "Unknown"),
                "parties": contract_structure.get("parties", []),
                "main_sections": [s.get("title", "") for s in contract_structure.get("main_sections", [])]
            }
            
            # Limit text for processing
            text_sample = contract_text[:12000] if len(contract_text) > 12000 else contract_text
            
            clause_prompt = f"""
            Analyze the following contract and extract all significant clauses. Use the provided context to enhance your analysis.
            
            Context:
            - Contract Type: {context_info['contract_type']}
            - Parties: {', '.join(context_info['parties'][:3])}
            - Main Sections: {', '.join(context_info['main_sections'][:5])}
            
            For each clause, provide a JSON object with the following structure:
            {{
                "clause_text": "full text of the clause",
                "clause_type": "specific type (payment_terms, termination, liability, etc.)",
                "clause_category": "broader category (financial, operational, risk_management, etc.)",
                "key_provisions": ["key provision 1", "key provision 2"],
                "parties_affected": ["party1", "party2"],
                "legal_significance": "high/medium/low",
                "risk_level": "high/medium/low",
                "risk_indicators": ["risk1", "risk2"],
                "compliance_requirements": ["requirement1", "requirement2"],
                "enforceability_assessment": "strong/moderate/weak",
                "related_clauses": ["clause_type1", "clause_type2"],
                "business_impact": "description of business impact",
                "negotiation_priority": "high/medium/low",
                "confidence": 0.95
            }}
            
            Return a JSON array of all identified clauses.
            
            Contract text:
            {text_sample}
            """
            
            # Try multiple providers for comprehensive analysis
            providers_to_try = [LLMProvider.OPENAI, LLMProvider.GROQ]
            all_clauses = []
            
            for provider in providers_to_try:
                try:
                    response = await self.llm_manager.get_completion(
                        prompt=clause_prompt,
                        task_type=TaskType.CONTRACT_ANALYSIS,
                        preferred_provider=provider.value,
                        temperature=0.1,
                        max_tokens=3000
                    )
                    
                    if response and response.content:
                        provider_clauses = self._parse_llm_clause_response(response.content, provider.value)
                        if provider_clauses:
                            all_clauses.extend(provider_clauses)
                
                except Exception as e:
                    logger.warning(f"Clause analysis failed with provider {provider.value}: {e}")
                    continue
            
            # Deduplicate and enhance clauses
            if all_clauses:
                return self._deduplicate_ai_clauses(all_clauses)
            
            return None
            
        except Exception as e:
            logger.error(f"AI-powered clause extraction failed: {e}")
            return None
    
    def _parse_llm_clause_response(self, response_content: str, provider: str) -> Optional[List[Dict[str, Any]]]:
        """Parse LLM clause analysis response."""
        try:
            # Try to extract JSON array from the response
            start_idx = response_content.find('[')
            end_idx = response_content.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                clauses = json.loads(json_str)
                
                # Enhance each clause with provider info
                for i, clause in enumerate(clauses):
                    if isinstance(clause, dict):
                        clause["clause_index"] = i + 1
                        clause["analysis_method"] = f"ai_{provider}"
                        clause["provider_used"] = provider
                
                return clauses
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM clause response from {provider}: {e}")
            return None
    
    def _deduplicate_ai_clauses(self, all_clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate clauses from AI analysis results."""
        unique_clauses = []
        seen_texts = set()
        
        for clause in all_clauses:
            # Use first 200 characters as uniqueness key
            clause_text = clause.get("clause_text", "")
            text_key = clause_text[:200].lower().strip()
            
            if text_key and text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_clauses.append(clause)
        
        return unique_clauses
    
    def _merge_clause_analyses(
        self, 
        structure_clauses: List[Dict[str, Any]], 
        ai_clauses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge clause results from structure analyzer and AI analysis.
        
        Args:
            structure_clauses: Clauses from structure analyzer
            ai_clauses: Clauses from AI analysis
            
        Returns:
            List[Dict[str, Any]]: Merged and enhanced clause results
        """
        merged_clauses = []
        
        # Start with structure analyzer clauses as baseline
        for struct_clause in structure_clauses:
            enhanced_clause = struct_clause.copy()
            
            # Try to find matching AI clause for enhancement
            matching_ai_clause = self._find_matching_ai_clause(struct_clause, ai_clauses)
            
            if matching_ai_clause:
                # Enhance with AI analysis
                enhanced_clause.update({
                    "enhanced_analysis": True,
                    "business_impact": matching_ai_clause.get("business_impact", ""),
                    "compliance_requirements": matching_ai_clause.get("compliance_requirements", []),
                    "enforceability_assessment": matching_ai_clause.get("enforceability_assessment", "moderate"),
                    "negotiation_priority": matching_ai_clause.get("negotiation_priority", "medium"),
                    "related_clauses": matching_ai_clause.get("related_clauses", []),
                    "ai_confidence": matching_ai_clause.get("confidence", 0.0)
                })
                
                # Update risk level if AI provides better assessment
                if matching_ai_clause.get("risk_level"):
                    enhanced_clause["risk_level"] = matching_ai_clause["risk_level"]
            
            merged_clauses.append(enhanced_clause)
        
        # Add unique AI clauses that weren't matched
        for ai_clause in ai_clauses:
            if not self._find_matching_structure_clause(ai_clause, structure_clauses):
                ai_clause["analysis_method"] = "ai_only"
                ai_clause["enhanced_analysis"] = True
                merged_clauses.append(ai_clause)
        
        return merged_clauses
    
    def _find_matching_ai_clause(
        self, 
        struct_clause: Dict[str, Any], 
        ai_clauses: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find matching AI clause for a structure analyzer clause."""
        struct_text = struct_clause.get("clause_text", "").lower()
        struct_type = struct_clause.get("clause_type", "")
        
        for ai_clause in ai_clauses:
            ai_text = ai_clause.get("clause_text", "").lower()
            ai_type = ai_clause.get("clause_type", "")
            
            # Check for text similarity (simple overlap check)
            if len(struct_text) > 50 and len(ai_text) > 50:
                overlap = len(set(struct_text.split()) & set(ai_text.split()))
                if overlap > min(len(struct_text.split()), len(ai_text.split())) * 0.3:
                    return ai_clause
            
            # Check for type match
            if struct_type == ai_type and len(struct_text) > 30 and len(ai_text) > 30:
                return ai_clause
        
        return None
    
    def _find_matching_structure_clause(
        self, 
        ai_clause: Dict[str, Any], 
        structure_clauses: List[Dict[str, Any]]
    ) -> bool:
        """Check if AI clause matches any structure analyzer clause."""
        return self._find_matching_ai_clause(ai_clause, structure_clauses) is not None
    
    def _enhanced_pattern_clause_extraction(self, contract_text: str) -> List[Dict[str, Any]]:
        """Enhanced pattern-based clause extraction with better classification."""
        # Use the existing enhanced pattern extraction but with additional enhancements
        base_clauses = self._basic_clause_extraction(contract_text)
        
        # Enhance each clause with additional analysis
        enhanced_clauses = []
        for clause in base_clauses:
            enhanced_clause = clause.copy()
            enhanced_clause.update({
                "analysis_method": "enhanced_pattern",
                "enhanced_analysis": False,
                "business_impact": self._assess_business_impact(clause),
                "negotiation_priority": self._assess_negotiation_priority(clause),
                "enforceability_assessment": "moderate"  # Default for pattern-based
            })
            enhanced_clauses.append(enhanced_clause)
        
        return enhanced_clauses
    
    def _assess_business_impact(self, clause: Dict[str, Any]) -> str:
        """Assess business impact of a clause."""
        clause_type = clause.get("clause_type", "")
        risk_indicators = clause.get("risk_indicators", [])
        
        high_impact_types = ["liability", "indemnification", "termination", "payment_terms"]
        
        if clause_type in high_impact_types or risk_indicators:
            return "High impact on business operations and risk exposure"
        elif clause_type in ["confidentiality", "intellectual_property"]:
            return "Moderate impact on business operations and IP protection"
        else:
            return "Low to moderate impact on business operations"
    
    def _assess_negotiation_priority(self, clause: Dict[str, Any]) -> str:
        """Assess negotiation priority for a clause."""
        clause_type = clause.get("clause_type", "")
        risk_indicators = clause.get("risk_indicators", [])
        legal_significance = clause.get("legal_significance", "medium")
        
        if legal_significance == "high" or risk_indicators:
            return "high"
        elif clause_type in ["payment_terms", "termination", "liability"]:
            return "high"
        elif clause_type in ["confidentiality", "intellectual_property"]:
            return "medium"
        else:
            return "low"
    
    def _post_process_clauses(
        self, 
        clause_results: List[Dict[str, Any]], 
        contract_text: str
    ) -> List[Dict[str, Any]]:
        """Post-process clause results to remove duplicates and enhance quality."""
        # Remove duplicates based on text similarity
        unique_clauses = []
        seen_signatures = set()
        
        for clause in clause_results:
            # Create a signature for the clause
            clause_text = clause.get("clause_text", "")
            clause_type = clause.get("clause_type", "")
            
            # Use first 100 characters + type as signature
            signature = f"{clause_type}_{clause_text[:100].lower().strip()}"
            
            if signature not in seen_signatures and len(clause_text) > 30:
                seen_signatures.add(signature)
                
                # Enhance clause with additional metadata
                clause["clause_id"] = hashlib.md5(signature.encode()).hexdigest()[:8]
                clause["text_length"] = len(clause_text)
                clause["word_count"] = len(clause_text.split())
                
                unique_clauses.append(clause)
        
        # Sort by position if available, otherwise by importance
        unique_clauses.sort(key=lambda x: (
            x.get("start_position", 999999),
            -len(x.get("risk_indicators", [])),
            x.get("clause_index", 999)
        ))
        
        # Limit to reasonable number and re-index
        final_clauses = unique_clauses[:50]  # Limit to 50 clauses
        for i, clause in enumerate(final_clauses):
            clause["final_index"] = i + 1
        
        return final_clauses
    
    def _categorize_clause_type(self, clause_type: str) -> str:
        """Categorize clause type into broader categories."""
        categories = {
            "payment_terms": "financial",
            "termination": "operational",
            "liability": "risk_management",
            "indemnification": "risk_management",
            "confidentiality": "information_protection",
            "intellectual_property": "ip_rights",
            "governing_law": "legal_framework",
            "dispute_resolution": "legal_framework",
            "scope_of_work": "operational",
            "force_majeure": "risk_management",
            "amendments": "legal_framework",
            "severability": "legal_framework"
        }
        return categories.get(clause_type, "general")
    
    def _assess_significance_from_confidence(self, confidence: float) -> str:
        """Assess legal significance from confidence score."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    async def _extract_and_classify_clauses(self, contract_text: str) -> List[Dict[str, Any]]:
        """
        Extract and classify individual clauses from the contract.
        
        Args:
            contract_text: Preprocessed contract text
            
        Returns:
            List[Dict[str, Any]]: List of identified and classified clauses
        """
        try:
            # First try using the enhanced LLM manager for AI-powered clause analysis
            if self.llm_manager:
                clauses = await self._ai_powered_clause_analysis(contract_text)
                if clauses:
                    return clauses
            
            # Use the contract structure analyzer service for comprehensive clause analysis
            if self.document_processor and hasattr(self.document_processor, 'structure_analyzer'):
                structure_result = self.document_processor.structure_analyzer.analyze_structure(contract_text)
                
                # Convert ContractClause objects to dict format
                clauses = []
                for i, clause in enumerate(structure_result.clauses):
                    clause_dict = {
                        "clause_text": clause.content,
                        "clause_type": clause.clause_type.value,
                        "clause_category": "provision",  # Default category
                        "clause_index": i + 1,
                        "key_provisions": clause.key_terms,
                        "parties_affected": [],  # Could be enhanced
                        "legal_significance": "high" if clause.confidence > 0.7 else "medium" if clause.confidence > 0.4 else "low",
                        "confidence": clause.confidence,
                        "risk_indicators": clause.risk_indicators,
                        "section_number": clause.section_number,
                        "start_position": clause.start_position,
                        "end_position": clause.end_position
                    }
                    clauses.append(clause_dict)
                
                # If no clauses found by structure analyzer, use enhanced extraction
                if not clauses:
                    logger.info("Structure analyzer found no clauses, using enhanced extraction")
                    clauses = self._basic_clause_extraction(contract_text)
                
                return clauses
            else:
                # Fallback to basic clause extraction
                return self._basic_clause_extraction(contract_text)
            
        except Exception as e:
            logger.error(f"Clause extraction failed: {e}")
            
            # Fallback to basic clause extraction
            return self._basic_clause_extraction(contract_text)
    
    async def _analyze_risks_and_compliance(
        self, 
        contract_text: str, 
        identified_clauses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze risks and compliance requirements in the contract.
        
        Args:
            contract_text: Contract text
            identified_clauses: Previously identified clauses
            
        Returns:
            Dict[str, Any]: Risk and compliance analysis results
        """
        try:
            risk_analysis = {
                "overall_risk_level": "medium",
                "risk_indicators": [],
                "compliance_requirements": [],
                "risk_mitigation_suggestions": [],
                "high_risk_clauses": [],
                "compliance_gaps": [],
                "risk_score": 0.0
            }
            
            # Collect risk indicators from clauses
            all_risk_indicators = []
            high_risk_clauses = []
            
            for clause in identified_clauses:
                clause_risks = clause.get("risk_indicators", [])
                all_risk_indicators.extend(clause_risks)
                
                # Identify high-risk clauses
                if (clause.get("risk_level") == "high" or 
                    clause.get("legal_significance") == "high" or 
                    len(clause_risks) > 0):
                    high_risk_clauses.append({
                        "clause_id": clause.get("clause_id", ""),
                        "clause_type": clause.get("clause_type", ""),
                        "risk_indicators": clause_risks,
                        "risk_level": clause.get("risk_level", "medium"),
                        "mitigation_priority": clause.get("negotiation_priority", "medium")
                    })
            
            # Analyze overall risk level
            unique_risks = list(set(all_risk_indicators))
            risk_analysis["risk_indicators"] = unique_risks
            risk_analysis["high_risk_clauses"] = high_risk_clauses
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(unique_risks, high_risk_clauses)
            risk_analysis["risk_score"] = risk_score
            
            # Determine overall risk level
            if risk_score >= 0.7:
                risk_analysis["overall_risk_level"] = "high"
            elif risk_score >= 0.4:
                risk_analysis["overall_risk_level"] = "medium"
            else:
                risk_analysis["overall_risk_level"] = "low"
            
            # AI-powered risk analysis if available
            if self.enable_multi_llm and self.llm_manager:
                ai_risk_analysis = await self._ai_powered_risk_analysis(contract_text, unique_risks)
                if ai_risk_analysis:
                    risk_analysis.update(ai_risk_analysis)
            
            # Generate risk mitigation suggestions
            risk_analysis["risk_mitigation_suggestions"] = self._generate_risk_mitigation_suggestions(
                unique_risks, high_risk_clauses
            )
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Risk and compliance analysis failed: {e}")
            return {
                "overall_risk_level": "unknown",
                "risk_indicators": [],
                "compliance_requirements": [],
                "risk_mitigation_suggestions": [],
                "high_risk_clauses": [],
                "error": str(e)
            }
    
    async def _ai_powered_risk_analysis(
        self, 
        contract_text: str, 
        identified_risks: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Use AI to perform advanced risk analysis."""
        try:
            text_sample = contract_text[:8000] if len(contract_text) > 8000 else contract_text
            
            risk_prompt = f"""
            Analyze the following contract for risks and compliance requirements. 
            Consider the already identified risks: {', '.join(identified_risks)}
            
            Provide a JSON response with:
            {{
                "additional_risks": ["risk1", "risk2"],
                "compliance_requirements": ["requirement1", "requirement2"],
                "regulatory_considerations": ["consideration1", "consideration2"],
                "industry_specific_risks": ["risk1", "risk2"],
                "financial_risks": ["risk1", "risk2"],
                "operational_risks": ["risk1", "risk2"],
                "legal_risks": ["risk1", "risk2"],
                "risk_mitigation_strategies": ["strategy1", "strategy2"],
                "compliance_gaps": ["gap1", "gap2"],
                "recommended_actions": ["action1", "action2"]
            }}
            
            Contract text:
            {text_sample}
            """
            
            response = await self.llm_manager.get_completion(
                prompt=risk_prompt,
                task_type=TaskType.RISK_ASSESSMENT,
                temperature=0.1,
                max_tokens=1500
            )
            
            if response and response.content:
                return self._parse_llm_risk_response(response.content)
            
            return None
            
        except Exception as e:
            logger.warning(f"AI-powered risk analysis failed: {e}")
            return None
    
    def _parse_llm_risk_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Parse LLM risk analysis response."""
        try:
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM risk response: {e}")
            return None
    
    def _calculate_risk_score(
        self, 
        risk_indicators: List[str], 
        high_risk_clauses: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall risk score."""
        base_score = 0.0
        
        # Score based on number of risk indicators
        risk_weight = {
            "unlimited_liability": 0.3,
            "broad_indemnification": 0.25,
            "automatic_renewal": 0.15,
            "broad_termination": 0.2,
            "exclusive_jurisdiction": 0.1,
            "liquidated_damages": 0.2
        }
        
        for risk in risk_indicators:
            base_score += risk_weight.get(risk, 0.1)
        
        # Score based on high-risk clauses
        high_risk_score = len(high_risk_clauses) * 0.1
        
        # Combine scores
        total_score = min(base_score + high_risk_score, 1.0)
        
        return round(total_score, 2)
    
    def _generate_risk_mitigation_suggestions(
        self, 
        risk_indicators: List[str], 
        high_risk_clauses: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate risk mitigation suggestions."""
        suggestions = []
        
        risk_mitigations = {
            "unlimited_liability": "Consider adding liability caps or limitations",
            "broad_indemnification": "Negotiate mutual indemnification or scope limitations",
            "automatic_renewal": "Add clear termination notice requirements",
            "broad_termination": "Negotiate termination for cause requirements",
            "exclusive_jurisdiction": "Consider alternative dispute resolution mechanisms",
            "liquidated_damages": "Review damage calculations for reasonableness"
        }
        
        for risk in risk_indicators:
            if risk in risk_mitigations:
                suggestions.append(risk_mitigations[risk])
        
        # Add general suggestions based on high-risk clauses
        if len(high_risk_clauses) > 3:
            suggestions.append("Consider comprehensive legal review due to multiple high-risk clauses")
        
        if any(clause.get("mitigation_priority") == "high" for clause in high_risk_clauses):
            suggestions.append("Prioritize negotiation of high-priority risk clauses")
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    async def _compare_contracts(
        self, 
        contract1_text: str, 
        contract2_text: str, 
        contract1_filename: str
    ) -> Dict[str, Any]:
        """
        Compare two contracts and identify differences.
        
        Args:
            contract1_text: First contract text
            contract2_text: Second contract text (can be text or filename)
            contract1_filename: Filename of first contract
            
        Returns:
            Dict[str, Any]: Contract comparison results
        """
        try:
            logger.info(f"Starting contract comparison for {contract1_filename}")
            
            # If contract2_text is a filename, we'd need to load it
            # For now, assume it's text content
            
            comparison_results = {
                "comparison_summary": {},
                "structural_differences": {},
                "clause_differences": {},
                "risk_comparison": {},
                "recommendations": []
            }
            
            # Analyze both contracts
            contract1_analysis = await self._quick_contract_analysis(contract1_text, "Contract 1")
            contract2_analysis = await self._quick_contract_analysis(contract2_text, "Contract 2")
            
            # Compare structures
            comparison_results["structural_differences"] = self._compare_contract_structures(
                contract1_analysis.get("contract_structure", {}),
                contract2_analysis.get("contract_structure", {})
            )
            
            # Compare clauses
            comparison_results["clause_differences"] = self._compare_contract_clauses(
                contract1_analysis.get("identified_clauses", []),
                contract2_analysis.get("identified_clauses", [])
            )
            
            # Compare risks
            comparison_results["risk_comparison"] = self._compare_contract_risks(
                contract1_analysis.get("risk_analysis", {}),
                contract2_analysis.get("risk_analysis", {})
            )
            
            # Generate comparison summary
            comparison_results["comparison_summary"] = self._generate_comparison_summary(
                comparison_results
            )
            
            # AI-powered comparison if available
            if self.enable_multi_llm and self.llm_manager:
                ai_comparison = await self._ai_powered_contract_comparison(
                    contract1_text, contract2_text
                )
                if ai_comparison:
                    comparison_results["ai_comparison"] = ai_comparison
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Contract comparison failed: {e}")
            return {
                "comparison_summary": {"error": str(e)},
                "structural_differences": {},
                "clause_differences": {},
                "risk_comparison": {},
                "recommendations": []
            }
    
    async def _quick_contract_analysis(self, contract_text: str, contract_name: str) -> Dict[str, Any]:
        """Perform quick analysis for contract comparison."""
        try:
            # Use cached analysis if available
            cache_key = self._generate_cache_key(contract_text, "quick_analysis")
            
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]
            
            # Perform basic analysis
            preprocessed_text = self._preprocess_contract_text(contract_text)
            
            # Quick structure analysis
            if self.structure_analyzer:
                structure_analysis = self.structure_analyzer.analyze_structure(preprocessed_text)
                contract_structure = {
                    "contract_type": structure_analysis.document_type,
                    "parties": structure_analysis.parties,
                    "sections_count": len(structure_analysis.sections),
                    "clauses_count": len(structure_analysis.clauses)
                }
                
                # Convert clauses
                identified_clauses = []
                for clause in structure_analysis.clauses:
                    identified_clauses.append({
                        "clause_type": clause.clause_type.value,
                        "risk_indicators": clause.risk_indicators,
                        "confidence": clause.confidence
                    })
            else:
                contract_structure = {}
                identified_clauses = []
            
            # Quick risk analysis
            risk_indicators = []
            for clause in identified_clauses:
                risk_indicators.extend(clause.get("risk_indicators", []))
            
            risk_analysis = {
                "risk_indicators": list(set(risk_indicators)),
                "risk_score": len(set(risk_indicators)) * 0.1
            }
            
            result = {
                "contract_structure": contract_structure,
                "identified_clauses": identified_clauses,
                "risk_analysis": risk_analysis
            }
            
            # Cache result
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Quick job application tracking failed for {contract_name}: {e}")
            return {
                "contract_structure": {},
                "identified_clauses": [],
                "risk_analysis": {}
            }
    
    def _compare_contract_structures(self, struct1: Dict[str, Any], struct2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare contract structures."""
        return {
            "contract_type_match": struct1.get("contract_type") == struct2.get("contract_type"),
            "parties_comparison": {
                "contract1_parties": struct1.get("parties", []),
                "contract2_parties": struct2.get("parties", []),
                "common_parties": list(set(struct1.get("parties", [])) & set(struct2.get("parties", [])))
            },
            "sections_comparison": {
                "contract1_sections": struct1.get("sections_count", 0),
                "contract2_sections": struct2.get("sections_count", 0),
                "difference": abs(struct1.get("sections_count", 0) - struct2.get("sections_count", 0))
            }
        }
    
    def _compare_contract_clauses(self, clauses1: List[Dict[str, Any]], clauses2: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare contract clauses."""
        types1 = set(clause.get("clause_type") for clause in clauses1)
        types2 = set(clause.get("clause_type") for clause in clauses2)
        
        return {
            "common_clause_types": list(types1 & types2),
            "unique_to_contract1": list(types1 - types2),
            "unique_to_contract2": list(types2 - types1),
            "clause_count_comparison": {
                "contract1": len(clauses1),
                "contract2": len(clauses2),
                "difference": abs(len(clauses1) - len(clauses2))
            }
        }
    
    def _compare_contract_risks(self, risk1: Dict[str, Any], risk2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare contract risks."""
        risks1 = set(risk1.get("risk_indicators", []))
        risks2 = set(risk2.get("risk_indicators", []))
        
        return {
            "common_risks": list(risks1 & risks2),
            "unique_to_contract1": list(risks1 - risks2),
            "unique_to_contract2": list(risks2 - risks1),
            "risk_score_comparison": {
                "contract1": risk1.get("risk_score", 0.0),
                "contract2": risk2.get("risk_score", 0.0),
                "difference": abs(risk1.get("risk_score", 0.0) - risk2.get("risk_score", 0.0))
            }
        }
    
    def _generate_comparison_summary(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison summary."""
        structural_diff = comparison_results.get("structural_differences", {})
        clause_diff = comparison_results.get("clause_differences", {})
        risk_diff = comparison_results.get("risk_comparison", {})
        
        return {
            "overall_similarity": "high" if (
                structural_diff.get("contract_type_match", False) and
                len(clause_diff.get("common_clause_types", [])) > 5
            ) else "medium" if len(clause_diff.get("common_clause_types", [])) > 2 else "low",
            "key_differences": len(clause_diff.get("unique_to_contract1", [])) + len(clause_diff.get("unique_to_contract2", [])),
            "risk_difference": risk_diff.get("risk_score_comparison", {}).get("difference", 0.0),
            "recommendation": "Detailed review recommended" if risk_diff.get("risk_score_comparison", {}).get("difference", 0.0) > 0.3 else "Standard review sufficient"
        }
    
    async def _ai_powered_contract_comparison(self, contract1: str, contract2: str) -> Optional[Dict[str, Any]]:
        """Use AI to perform detailed contract comparison."""
        try:
            # Limit text for processing
            text1_sample = contract1[:6000] if len(contract1) > 6000 else contract1
            text2_sample = contract2[:6000] if len(contract2) > 6000 else contract2
            
            comparison_prompt = f"""
            Compare these two contracts and provide a detailed analysis. Return JSON with:
            {{
                "key_differences": ["difference1", "difference2"],
                "similar_provisions": ["provision1", "provision2"],
                "risk_differences": ["risk1", "risk2"],
                "negotiation_recommendations": ["recommendation1", "recommendation2"],
                "preferred_contract": "contract1/contract2/neither",
                "reasoning": "explanation of preference",
                "critical_differences": ["critical1", "critical2"]
            }}
            
            Contract 1:
            {text1_sample}
            
            Contract 2:
            {text2_sample}
            """
            
            response = await self.llm_manager.get_completion(
                prompt=comparison_prompt,
                task_type=TaskType.CONTRACT_ANALYSIS,
                temperature=0.1,
                max_tokens=2000
            )
            
            if response and response.content:
                return self._parse_llm_comparison_response(response.content)
            
            return None
            
        except Exception as e:
            logger.warning(f"AI-powered contract comparison failed: {e}")
            return None
    
    def _parse_llm_comparison_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Parse LLM comparison response."""
        try:
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM comparison response: {e}")
            return None
    
    def _generate_comprehensive_metadata(
        self,
        contract_text: str,
        contract_filename: str,
        contract_structure: Dict[str, Any],
        identified_clauses: List[Dict[str, Any]],
        risk_analysis: Dict[str, Any],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive analysis metadata."""
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "contract_length": len(contract_text),
            "word_count": len(contract_text.split()),
            "clause_count": len(identified_clauses),
            "contract_type": contract_structure.get("contract_type", "Unknown"),
            "analysis_timestamp": datetime.now().isoformat(),
            "agent_version": "2.0.0",
            "confidence_score": contract_structure.get("confidence_score", 0.0),
            "sections_identified": len(contract_structure.get("main_sections", [])),
            "parties_identified": len(contract_structure.get("parties", [])),
            "processing_time": processing_time,
            "risk_score": risk_analysis.get("risk_score", 0.0),
            "overall_risk_level": risk_analysis.get("overall_risk_level", "medium"),
            "high_risk_clauses_count": len(risk_analysis.get("high_risk_clauses", [])),
            "analysis_methods_used": contract_structure.get("analysis_methods_used", []),
            "providers_used": getattr(self, '_providers_used', []),
            "cache_enabled": self.enable_caching,
            "multi_llm_enabled": self.enable_multi_llm,
            "advanced_analysis_enabled": self.enable_advanced_analysis,
            "processing_notes": [
                f"Identified {len(identified_clauses)} significant clauses",
                f"Contract type: {contract_structure.get('contract_type', 'Unknown')}",
                f"Risk level: {risk_analysis.get('overall_risk_level', 'medium')}",
                f"Processing time: {processing_time:.2f} seconds",
                f"Confidence score: {contract_structure.get('confidence_score', 0.0):.2f}",
                f"Providers used: {', '.join(getattr(self, '_providers_used', []))}"
            ]
        }
    
    def _parse_structure_result(self, structure_result: str) -> Dict[str, Any]:
        """Parse the structure analysis result from the agent"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(structure_result, str):
                # Look for JSON in the response
                start_idx = structure_result.find('{')
                end_idx = structure_result.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = structure_result[start_idx:end_idx]
                    return json.loads(json_str)
            
            # If parsing fails, create a basic structure
            return {
                "contract_type": "Unknown",
                "main_sections": [],
                "parties": [],
                "term_information": {},
                "governing_law": "Unknown",
                "organization": "Standard"
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse structure result: {e}")
            return self._basic_structure_analysis(structure_result)
    
    def _parse_clause_result(self, clause_result: str) -> List[Dict[str, Any]]:
        """Parse the clause extraction result from the agent"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(clause_result, str):
                # Look for JSON array in the response
                start_idx = clause_result.find('[')
                end_idx = clause_result.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = clause_result[start_idx:end_idx]
                    clauses = json.loads(json_str)
                    
                    # Validate and enhance clause data
                    validated_clauses = []
                    for i, clause in enumerate(clauses):
                        if isinstance(clause, dict) and "clause_text" in clause:
                            clause["clause_index"] = i + 1
                            validated_clauses.append(clause)
                    
                    return validated_clauses
            
            # If parsing fails, return empty list
            return []
            
        except Exception as e:
            logger.warning(f"Failed to parse clause result: {e}")
            return self._basic_clause_extraction(clause_result)
    
    def _basic_structure_analysis(self, contract_text: str) -> Dict[str, Any]:
        """Fallback basic structure analysis"""
        import re
        
        # Simple pattern matching for common contract elements
        structure = {
            "contract_type": "Unknown",
            "main_sections": [],
            "parties": [],
            "term_information": {},
            "governing_law": "Unknown",
            "organization": "Standard"
        }
        
        # Try to identify contract type
        contract_types = {
            "service agreement": r"service\s+agreement",
            "employment contract": r"employment\s+contract",
            "nda": r"non.?disclosure\s+agreement",
            "license agreement": r"license\s+agreement",
            "purchase agreement": r"purchase\s+agreement"
        }
        
        text_lower = contract_text.lower()
        for contract_type, pattern in contract_types.items():
            if re.search(pattern, text_lower):
                structure["contract_type"] = contract_type.title()
                break
        
        # Try to find parties
        party_patterns = [
            r"between\s+([^,\n]+)\s+and\s+([^,\n]+)",
            r"party\s+a[:\s]+([^,\n]+)",
            r"party\s+b[:\s]+([^,\n]+)"
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                structure["parties"].extend([match.strip() for match in matches[0] if isinstance(matches[0], tuple)])
                break
        
        return structure
    
    def _basic_clause_extraction(self, contract_text: str) -> List[Dict[str, Any]]:
        """Enhanced fallback clause extraction with better classification"""
        import re
        
        # Split text into sections and clauses more intelligently
        clauses = []
        
        # Enhanced clause keywords with more comprehensive patterns
        clause_patterns = {
            "payment_terms": [
                r"(?i)\d+\.\s*(PAYMENT.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(Client shall pay.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(.*payment.*invoice.*?)(?=\n\s*\d+\.|$)"
            ],
            "termination": [
                r"(?i)\d+\.\s*(TERMINATION.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(.*terminate.*agreement.*?)(?=\n\s*\d+\.|$)"
            ],
            "liability": [
                r"(?i)\d+\.\s*(LIABILITY.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(.*liability.*limited.*?)(?=\n\s*\d+\.|$)"
            ],
            "confidentiality": [
                r"(?i)\d+\.\s*(CONFIDENTIALITY.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(.*confidential.*proprietary.*?)(?=\n\s*\d+\.|$)"
            ],
            "intellectual_property": [
                r"(?i)\d+\.\s*(INTELLECTUAL PROPERTY.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(.*intellectual property.*?)(?=\n\s*\d+\.|$)"
            ],
            "governing_law": [
                r"(?i)\d+\.\s*(GOVERNING LAW.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(.*governed by.*laws.*?)(?=\n\s*\d+\.|$)"
            ],
            "scope_of_work": [
                r"(?i)\d+\.\s*(SCOPE.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(.*services.*described.*?)(?=\n\s*\d+\.|$)"
            ],
            "indemnification": [
                r"(?i)\d+\.\s*(INDEMNIFICATION.*?)(?=\n\s*\d+\.|$)",
                r"(?i)(.*indemnify.*hold harmless.*?)(?=\n\s*\d+\.|$)"
            ]
        }
        
        clause_index = 1
        
        # Extract clauses using patterns
        for clause_type, patterns in clause_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, contract_text, re.MULTILINE | re.DOTALL)
                for match in matches:
                    clause_text = match.group(1) if match.groups() else match.group(0)
                    clause_text = clause_text.strip()
                    
                    if len(clause_text) > 30:  # Only consider substantial clauses
                        # Extract key provisions
                        key_provisions = self._extract_key_provisions(clause_text, clause_type)
                        
                        # Identify risk indicators
                        risk_indicators = self._identify_clause_risks(clause_text)
                        
                        # Determine legal significance
                        significance = self._assess_legal_significance(clause_text, clause_type, risk_indicators)
                        
                        clause = {
                            "clause_text": clause_text,
                            "clause_type": clause_type,
                            "clause_category": self._categorize_clause(clause_type),
                            "clause_index": clause_index,
                            "key_provisions": key_provisions,
                            "parties_affected": self._identify_affected_parties(clause_text),
                            "legal_significance": significance,
                            "confidence": self._calculate_clause_confidence(clause_text, clause_type),
                            "risk_indicators": risk_indicators,
                            "section_number": self._extract_section_number(clause_text),
                            "start_position": match.start(),
                            "end_position": match.end()
                        }
                        
                        clauses.append(clause)
                        clause_index += 1
        
        # Remove duplicates and sort by position
        unique_clauses = []
        seen_texts = set()
        
        for clause in sorted(clauses, key=lambda x: x["start_position"]):
            # Use first 100 characters as uniqueness key
            text_key = clause["clause_text"][:100].lower().strip()
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_clauses.append(clause)
        
        return unique_clauses[:25]  # Limit to first 25 unique clauses
    
    def _extract_key_provisions(self, clause_text: str, clause_type: str) -> List[str]:
        """Extract key provisions from a clause based on its type"""
        provisions = []
        text_lower = clause_text.lower()
        
        if clause_type == "payment_terms":
            # Extract payment amounts, due dates, late fees
            import re
            amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', clause_text)
            days = re.findall(r'\d+\s*days?', text_lower)
            provisions.extend(amounts)
            provisions.extend(days)
            
        elif clause_type == "termination":
            # Extract notice periods, termination conditions
            import re
            notice_periods = re.findall(r'\d+\s*days?\s*(?:notice|written notice)', text_lower)
            provisions.extend(notice_periods)
            
        elif clause_type == "liability":
            # Extract liability limits, exclusions
            if "unlimited" in text_lower:
                provisions.append("unlimited liability")
            if "limited to" in text_lower:
                provisions.append("limited liability")
                
        elif clause_type == "confidentiality":
            # Extract confidentiality periods, scope
            import re
            periods = re.findall(r'\d+\s*years?', text_lower)
            provisions.extend(periods)
            
        return provisions[:5]  # Limit to 5 key provisions
    
    def _identify_clause_risks(self, clause_text: str) -> List[str]:
        """Identify risk indicators in a clause"""
        risks = []
        text_lower = clause_text.lower()
        
        risk_patterns = {
            "unlimited_liability": ["unlimited", "without limitation", "no cap"],
            "broad_indemnification": ["indemnify against all", "hold harmless from any"],
            "automatic_renewal": ["automatically renew", "auto-renew"],
            "broad_termination": ["terminate at any time", "terminate without cause"],
            "exclusive_jurisdiction": ["exclusive jurisdiction", "sole jurisdiction"],
            "liquidated_damages": ["liquidated damages", "penalty"]
        }
        
        for risk_type, patterns in risk_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                risks.append(risk_type)
        
        return risks
    
    def _assess_legal_significance(self, clause_text: str, clause_type: str, risk_indicators: List[str]) -> str:
        """Assess the legal significance of a clause"""
        # High significance clause types
        high_significance_types = ["liability", "indemnification", "termination", "governing_law"]
        
        # Check for risk indicators
        if risk_indicators:
            return "high"
        
        # Check clause type
        if clause_type in high_significance_types:
            return "high"
        
        # Check clause length and complexity
        if len(clause_text) > 500:
            return "medium"
        
        return "medium"
    
    def _categorize_clause(self, clause_type: str) -> str:
        """Categorize clause into broader categories"""
        categories = {
            "payment_terms": "financial",
            "termination": "operational",
            "liability": "risk_management",
            "confidentiality": "information_protection",
            "intellectual_property": "ip_rights",
            "governing_law": "legal_framework",
            "scope_of_work": "operational",
            "indemnification": "risk_management"
        }
        
        return categories.get(clause_type, "general")
    
    def _identify_affected_parties(self, clause_text: str) -> List[str]:
        """Identify which parties are affected by the clause"""
        parties = []
        text_lower = clause_text.lower()
        
        # Common party references
        party_terms = {
            "client": ["client", "customer", "buyer"],
            "provider": ["provider", "vendor", "seller", "consultant", "contractor"],
            "both_parties": ["both parties", "each party", "either party"]
        }
        
        for party_type, terms in party_terms.items():
            if any(term in text_lower for term in terms):
                parties.append(party_type)
        
        return parties[:3]  # Limit to 3 parties
    
    def _calculate_clause_confidence(self, clause_text: str, clause_type: str) -> float:
        """Calculate confidence score for clause classification"""
        # Base confidence
        confidence = 0.5
        
        # Keyword matching
        clause_keywords = {
            "payment_terms": ["payment", "pay", "fee", "invoice", "compensation"],
            "termination": ["terminate", "termination", "end", "expire"],
            "liability": ["liable", "liability", "damages", "limitation"],
            "confidentiality": ["confidential", "non-disclosure", "proprietary"],
            "intellectual_property": ["intellectual property", "copyright", "patent"],
            "governing_law": ["governing law", "jurisdiction", "court"]
        }
        
        keywords = clause_keywords.get(clause_type, [])
        text_lower = clause_text.lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        if matches > 0:
            confidence += min(0.3, matches * 0.1)
        
        # Length factor
        if len(clause_text) > 100:
            confidence += 0.1
        
        # Structure factor (numbered sections)
        import re
        if re.search(r'\d+\.\s*', clause_text):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _extract_section_number(self, clause_text: str) -> str:
        """Extract section number from clause text"""
        import re
        match = re.search(r'(\d+(?:\.\d+)*)\.\s*', clause_text)
        return match.group(1) if match else None
    
    def _generate_analysis_metadata(
        self,
        contract_text: str,
        contract_filename: str,
        contract_structure: Dict[str, Any],
        identified_clauses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate metadata about the analysis"""
        
        from datetime import datetime
        
        # Get analysis timestamp safely
        analysis_timestamp = datetime.utcnow().isoformat()
        if self.state.get("last_execution") and self.state["last_execution"].get("start_time"):
            analysis_timestamp = self.state["last_execution"]["start_time"].isoformat()
        
        return {
            "contract_length": len(contract_text),
            "word_count": len(contract_text.split()),
            "clause_count": len(identified_clauses),
            "contract_type": contract_structure.get("contract_type", "Unknown"),
            "analysis_timestamp": analysis_timestamp,
            "agent_version": "1.0.0",
            "confidence_score": contract_structure.get("confidence_score", 0.0),
            "sections_identified": len(contract_structure.get("main_sections", [])),
            "parties_identified": len(contract_structure.get("parties", [])),
            "processing_notes": [
                f"Identified {len(identified_clauses)} significant clauses",
                f"Contract type: {contract_structure.get('contract_type', 'Unknown')}",
                f"Document length: {len(contract_text)} characters",
                f"Confidence score: {contract_structure.get('confidence_score', 0.0):.2f}"
            ]
        }
    
    async def _ai_powered_structure_analysis(self, contract_text: str) -> Optional[Dict[str, Any]]:
        """
        Use enhanced LLM manager for AI-powered contract structure analysis.
        
        Args:
            contract_text: Contract text to analyze
            
        Returns:
            Optional[Dict[str, Any]]: Structure analysis results or None if failed
        """
        try:
            # Limit text length for LLM processing
            text_sample = contract_text[:8000] if len(contract_text) > 8000 else contract_text
            
            structure_prompt = f"""
            Analyze the following contract and identify its structure. Provide a JSON response with the following format:
            
            {{
                "contract_type": "type of contract (e.g., Service Agreement, Employment Contract, NDA)",
                "main_sections": [
                    {{
                        "title": "section title",
                        "type": "section type (e.g., terms, conditions, obligations)",
                        "content_length": estimated_character_count
                    }}
                ],
                "parties": ["party1", "party2"],
                "term_information": {{
                    "effective_date": "date or null",
                    "expiration_date": "date or null"
                }},
                "governing_law": "jurisdiction or Unknown",
                "organization": "Structured or Simple",
                "confidence_score": 0.0-1.0,
                "key_terms": {{
                    "payment_terms": "summary",
                    "termination_clause": "summary",
                    "liability_limits": "summary"
                }}
            }}
            
            Contract text:
            {text_sample}
            
            Provide only the JSON response, no additional text.
            """
            
            # Use enhanced LLM manager with job application tracking task type
            response = await self.llm_manager.get_completion(
                prompt=structure_prompt,
                task_type=TaskType.CONTRACT_ANALYSIS,
                routing_criteria=RoutingCriteria.QUALITY,
                max_retries=2
            )
            
            if response and response.content:
                # Parse JSON response
                import json
                try:
                    # Extract JSON from response
                    content = response.content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]
                    
                    structure_data = json.loads(content)
                    
                    # Validate required fields
                    required_fields = ["contract_type", "main_sections", "parties"]
                    if all(field in structure_data for field in required_fields):
                        logger.info(f"AI-powered structure analysis completed with confidence: {response.confidence_score:.2f}")
                        return structure_data
                    else:
                        logger.warning("AI structure analysis missing required fields")
                        return None
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse AI structure analysis JSON: {e}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"AI-powered structure analysis failed: {e}")
            return None
    
    async def _ai_powered_clause_analysis(self, contract_text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Use enhanced LLM manager for AI-powered clause extraction and classification.
        
        Args:
            contract_text: Contract text to analyze
            
        Returns:
            Optional[List[Dict[str, Any]]]: Clause analysis results or None if failed
        """
        try:
            # Limit text length for LLM processing
            text_sample = contract_text[:10000] if len(contract_text) > 10000 else contract_text
            
            clause_prompt = f"""
            Analyze the following contract and extract all significant clauses. For each clause, provide detailed classification and analysis. Return a JSON array with the following format:
            
            [
                {{
                    "clause_text": "full text of the clause",
                    "clause_type": "type (e.g., payment_terms, termination, liability, confidentiality, intellectual_property, governing_law, scope_of_work, indemnification)",
                    "clause_category": "category (e.g., financial, operational, risk_management, information_protection, ip_rights, legal_framework)",
                    "clause_index": 1,
                    "key_provisions": ["key provision 1", "key provision 2"],
                    "parties_affected": ["client", "provider", "both_parties"],
                    "legal_significance": "high/medium/low",
                    "confidence": 0.0-1.0,
                    "risk_indicators": ["risk1", "risk2"],
                    "section_number": "section number if available"
                }}
            ]
            
            Focus on identifying:
            1. Payment and financial terms
            2. Termination conditions
            3. Liability and indemnification clauses
            4. Confidentiality and non-disclosure provisions
            5. Intellectual property rights
            6. Governing law and jurisdiction
            7. Scope of work or services
            8. Risk factors and limitations
            
            Contract text:
            {text_sample}
            
            Provide only the JSON array response, no additional text.
            """
            
            # Use enhanced LLM manager with job application tracking task type
            response = await self.llm_manager.get_completion(
                prompt=clause_prompt,
                task_type=TaskType.CONTRACT_ANALYSIS,
                routing_criteria=RoutingCriteria.QUALITY,
                max_retries=2
            )
            
            if response and response.content:
                # Parse JSON response
                import json
                try:
                    # Extract JSON from response
                    content = response.content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]
                    
                    clauses_data = json.loads(content)
                    
                    # Validate and enhance clause data
                    if isinstance(clauses_data, list):
                        validated_clauses = []
                        for i, clause in enumerate(clauses_data):
                            if isinstance(clause, dict) and "clause_text" in clause:
                                # Ensure required fields
                                clause["clause_index"] = i + 1
                                clause.setdefault("confidence", 0.7)
                                clause.setdefault("key_provisions", [])
                                clause.setdefault("parties_affected", [])
                                clause.setdefault("risk_indicators", [])
                                clause.setdefault("legal_significance", "medium")
                                
                                # Add position information
                                clause["start_position"] = contract_text.find(clause["clause_text"][:50])
                                clause["end_position"] = clause["start_position"] + len(clause["clause_text"])
                                
                                validated_clauses.append(clause)
                        
                        logger.info(f"AI-powered clause analysis completed: {len(validated_clauses)} clauses identified")
                        return validated_clauses[:25]  # Limit to 25 clauses
                    else:
                        logger.warning("AI clause analysis did not return a list")
                        return None
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse AI clause analysis JSON: {e}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"AI-powered clause analysis failed: {e}")
            return None

# Compatibility alias for backward compatibility
ContractAnalyzerAgent = EnhancedContractAnalyzerAgent


# Global service instance
_contract_analyzer_agent: Optional[EnhancedContractAnalyzerAgent] = None


def get_contract_analyzer_agent(
    communication_protocol: Optional[AgentCommunicationProtocol] = None,
    config: Optional[Dict[str, Any]] = None
) -> EnhancedContractAnalyzerAgent:
    """
    Get or create the global enhanced contract analyzer agent instance.
    
    Args:
        communication_protocol: Optional communication protocol
        config: Optional configuration parameters
        
    Returns:
        EnhancedContractAnalyzerAgent: The global agent instance
    """
    global _contract_analyzer_agent
    
    if _contract_analyzer_agent is None:
        if communication_protocol is None:
            # Create a default communication protocol if none provided
            from .base_agent import AgentCommunicationProtocol
            communication_protocol = AgentCommunicationProtocol()
        
        _contract_analyzer_agent = EnhancedContractAnalyzerAgent(
            communication_protocol=communication_protocol,
            config=config
        )
    
    return _contract_analyzer_agent


def reset_contract_analyzer_agent():
    """Reset the global contract analyzer agent instance."""
    global _contract_analyzer_agent
    _contract_analyzer_agent = None