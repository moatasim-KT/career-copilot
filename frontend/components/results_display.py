"""Enhanced Interactive Results Display Component with Tabbed Interface and Advanced Features"""
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import re
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass
from enum import Enum
import base64
import io

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

@dataclass
class RedlineSuggestion:
    """Redline suggestion data structure"""
    id: str
    clause_id: str
    original_text: str
    suggested_text: str
    reason: str
    risk_level: RiskLevel
    confidence: float
    status: str = "pending"  # pending, accepted, rejected
    
@dataclass
class ContractClause:
    """Contract clause data structure"""
    id: str
    title: str
    content: str
    risk_level: RiskLevel
    risk_score: float
    start_position: int
    end_position: int
    category: str
    issues: List[str]
    suggestions: List[str]

class InteractiveAnalysisResultsDisplay:
    """Enhanced interactive component for displaying job application tracking results with tabbed interface."""
    
    def __init__(self, results: Dict[str, Any], contract_text: str = "", filename: str = "contract.pdf", api_client=None):
        self.results = results
        self.contract_text = contract_text or self._extract_contract_text()
        self.filename = filename
        self.api_client = api_client
        self.contract_id = results.get('contract_id', results.get('analysis_id', 'unknown'))
        
        # Parse results into structured data
        self.clauses = self._parse_clauses()
        self.redlines = self._parse_redlines()
        self.precedents = self._parse_precedents()
        self.risk_summary = self._parse_risk_summary()
        
        # Initialize session state for interactive features
        self._initialize_session_state()
        
        self.render()
    
    def _initialize_session_state(self):
        """Initialize session state variables for interactive features."""
        session_keys = {
            'selected_clause': None,
            'redline_filter': "all",
            'show_comparison': False,
            'expanded_sections': {},
            'clause_highlights': True,
            'risk_filter': "All",
            'precedent_search': "",
            'comparison_mode': "side_by_side",
            'export_format': "PDF"
        }
        
        for key, default_value in session_keys.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _extract_contract_text(self) -> str:
        """Extract contract text from results if not provided."""
        return self.results.get('contract_text', 
                               self.results.get('original_text', 
                                              "Contract text not available for display"))
    
    def render(self):
        """Render the complete interactive analysis results with tabbed interface."""
        # Header with contract info
        self._render_header()
        
        # Create main tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", 
            "⚠️ Risks", 
            "✏️ Redlines", 
            "📚 Precedents"
        ])
        
        with tab1:
            self._render_overview_tab()
        
        with tab2:
            self._render_risks_tab()
        
        with tab3:
            self._render_redlines_tab()
        
        with tab4:
            self._render_precedents_tab()
    
    def _render_header(self):
        """Render the header section with contract information and quick actions."""
        st.markdown("""
        <style>
        .contract-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .header-title {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .header-subtitle {
            font-size: 16px;
            opacity: 0.9;
        }
        .risk-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin: 5px;
        }
        .risk-critical { background-color: #dc3545; }
        .risk-high { background-color: #fd7e14; }
        .risk-medium { background-color: #ffc107; color: #000; }
        .risk-low { background-color: #28a745; }
        </style>
        """, unsafe_allow_html=True)
        
        # Contract header
        risk_level = self.risk_summary.get('overall_risk', 'Medium')
        risk_score = self.risk_summary.get('risk_score', 0.5)
        
        st.markdown(f"""
        <div class="contract-header">
            <div class="header-title">📋 {self.filename}</div>
            <div class="header-subtitle">
                Contract Analysis Results • Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            risk_color = self._get_risk_color_hex(risk_level)
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: {risk_color}20; border-radius: 8px; border-left: 4px solid {risk_color};">
                <div style="font-size: 24px; font-weight: bold; color: {risk_color};">{risk_level}</div>
                <div style="font-size: 12px; color: #666;">Overall Risk</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #495057;">{risk_score:.1%}</div>
                <div style="font-size: 12px; color: #666;">Risk Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #495057;">{len(self.clauses)}</div>
                <div style="font-size: 12px; color: #666;">Clauses Analyzed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #495057;">{len(self.redlines)}</div>
                <div style="font-size: 12px; color: #666;">Redlines</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #495057;">{len(self.precedents)}</div>
                <div style="font-size: 12px; color: #666;">Precedents</div>
            </div>
            """, unsafe_allow_html=True)
    
    def _parse_clauses(self) -> List[ContractClause]:
        """Parse clauses from analysis results"""
        clauses = []
        clauses_data = self.results.get('clauses_analysis', [])
        
        for i, clause_data in enumerate(clauses_data):
            if isinstance(clause_data, dict):
                clause = ContractClause(
                    id=clause_data.get('id', f'clause_{i}'),
                    title=clause_data.get('title', f'Clause {i+1}'),
                    content=clause_data.get('content', ''),
                    risk_level=RiskLevel(clause_data.get('risk_level', 'Medium')),
                    risk_score=float(clause_data.get('risk_score', 0.5)),
                    start_position=int(clause_data.get('start_position', 0)),
                    end_position=int(clause_data.get('end_position', 0)),
                    category=clause_data.get('category', 'General'),
                    issues=clause_data.get('issues', []),
                    suggestions=clause_data.get('suggestions', [])
                )
                clauses.append(clause)
        
        return clauses
    
    def _parse_redlines(self) -> List[RedlineSuggestion]:
        """Parse redline suggestions from analysis results"""
        redlines = []
        redlines_data = self.results.get('redline_suggestions', [])
        
        for i, redline_data in enumerate(redlines_data):
            if isinstance(redline_data, dict):
                redline = RedlineSuggestion(
                    id=redline_data.get('id', f'redline_{i}'),
                    clause_id=redline_data.get('clause_id', ''),
                    original_text=redline_data.get('original_text', ''),
                    suggested_text=redline_data.get('suggested_text', ''),
                    reason=redline_data.get('reason', ''),
                    risk_level=RiskLevel(redline_data.get('risk_level', 'Medium')),
                    confidence=float(redline_data.get('confidence', 0.5)),
                    status=redline_data.get('status', 'pending')
                )
                redlines.append(redline)
        
        return redlines
    
    def _parse_precedents(self) -> List[Dict]:
        """Parse precedents from analysis results"""
        precedents = []
        
        # Try different possible keys for precedents data
        precedents_data = (
            self.results.get('precedents', []) or 
            self.results.get('legal_precedents', []) or
            self.results.get('similar_cases', [])
        )
        
        for i, precedent_data in enumerate(precedents_data):
            if isinstance(precedent_data, dict):
                # Ensure required fields exist
                precedent = {
                    'id': precedent_data.get('id', f'precedent_{i}'),
                    'case_name': precedent_data.get('case_name', precedent_data.get('title', f'Case {i+1}')),
                    'summary': precedent_data.get('summary', precedent_data.get('description', '')),
                    'relevance_score': float(precedent_data.get('relevance_score', precedent_data.get('similarity_score', 0.5))),
                    'jurisdiction': precedent_data.get('jurisdiction', 'Unknown'),
                    'date': precedent_data.get('date', precedent_data.get('year', 'Unknown')),
                    'outcome': precedent_data.get('outcome', 'unknown'),
                    'relevant_text': precedent_data.get('relevant_text', precedent_data.get('excerpt', '')),
                    'key_takeaways': precedent_data.get('key_takeaways', precedent_data.get('takeaways', [])),
                    'implications': precedent_data.get('implications', ''),
                    'citation': precedent_data.get('citation', ''),
                    'court': precedent_data.get('court', '')
                }
                precedents.append(precedent)
            elif isinstance(precedent_data, str):
                # Handle simple string precedents
                precedents.append({
                    'id': f'precedent_{i}',
                    'case_name': precedent_data,
                    'summary': precedent_data,
                    'relevance_score': 0.5,
                    'jurisdiction': 'Unknown',
                    'date': 'Unknown',
                    'outcome': 'unknown',
                    'relevant_text': '',
                    'key_takeaways': [],
                    'implications': '',
                    'citation': '',
                    'court': ''
                })
        
        return precedents
    
    def _parse_risk_summary(self) -> Dict[str, Any]:
        """Parse risk summary from analysis results"""
        return {
            'overall_risk': self.results.get('risk_level', 'Medium'),
            'risk_score': float(self.results.get('risk_score', 0.5)),
            'confidence': float(self.results.get('confidence_score', 0.8)),
            'risk_factors': self.results.get('risk_factors', []),
            'risk_distribution': self._calculate_risk_distribution()
        }
    
    def _calculate_risk_distribution(self) -> Dict[str, int]:
        """Calculate risk distribution across clauses"""
        distribution = {level.value: 0 for level in RiskLevel}
        
        for clause in self.clauses:
            distribution[clause.risk_level.value] += 1
        
        return distribution
    
    def _render_overview_tab(self):
        """Render the overview tab with summary information and visualizations."""
        # Executive Summary
        st.subheader("📋 Executive Summary")
        
        summary_text = self.results.get('summary', 'This contract has been analyzed for potential risks and issues.')
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff;">
            <p style="margin: 0; font-size: 16px; line-height: 1.6;">{summary_text}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Risk Distribution Visualization
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Risk Distribution")
            
            if self.risk_summary['risk_distribution']:
                # Create pie chart
                fig = px.pie(
                    values=list(self.risk_summary['risk_distribution'].values()),
                    names=list(self.risk_summary['risk_distribution'].keys()),
                    color_discrete_map={
                        'Low': '#28a745',
                        'Medium': '#ffc107', 
                        'High': '#fd7e14',
                        'Critical': '#dc3545'
                    },
                    title="Clause Risk Levels"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(showlegend=True, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No risk distribution data available")
        
        with col2:
            st.subheader("🎯 Key Metrics")
            
            # Key metrics cards
            metrics = [
                ("Processing Time", f"{self.results.get('processing_time', 0):.1f}s"),
                ("Confidence Score", f"{self.risk_summary.get('confidence', 0.8):.1%}"),
                ("Issues Found", str(len(self.results.get('risky_clauses', [])))),
                ("Recommendations", str(len(self.results.get('recommendations', []))))
            ]
            
            for metric_name, metric_value in metrics:
                st.markdown(f"""
                <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 24px; font-weight: bold; color: #495057;">{metric_value}</div>
                    <div style="font-size: 14px; color: #6c757d;">{metric_name}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Key Findings Section
        st.subheader("🔍 Key Findings")
        
        risky_clauses = self.results.get('risky_clauses', [])
        if risky_clauses:
            for i, clause in enumerate(risky_clauses[:3]):  # Show top 3
                risk_level = clause.get('risk_level', 'Medium')
                risk_color = self._get_risk_color_hex(risk_level)
                
                with st.expander(f"{self._get_risk_color(risk_level)} {clause.get('clause', f'Finding {i+1}')} - {risk_level} Risk"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write("**Description:**")
                        st.write(clause.get('description', 'No description available'))
                        
                        if clause.get('suggestion'):
                            st.write("**Recommendation:**")
                            st.info(clause.get('suggestion'))
                    
                    with col2:
                        st.markdown(f"""
                        <div style="text-align: center; padding: 10px; background: {risk_color}20; border-radius: 8px;">
                            <div style="font-size: 18px; font-weight: bold; color: {risk_color};">{risk_level}</div>
                            <div style="font-size: 12px; color: #666;">Risk Level</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No specific risk findings identified in this contract.")
        
        # Quick Actions
        st.markdown("---")
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 View High Risk Items", use_container_width=True):
                st.session_state.risk_filter = "High"
                st.switch_page("Risks")
        
        with col2:
            if st.button("✏️ Review Redlines", use_container_width=True):
                st.session_state.redline_filter = "all"
                st.switch_page("Redlines")
        
        with col3:
            if st.button("📚 Check Precedents", use_container_width=True):
                st.switch_page("Precedents")
        
        with col4:
            if st.button("📄 Export Report", use_container_width=True):
                self._export_comprehensive_report()
    
    def _render_risks_tab(self):
        """Render the risks tab with color-coded risk levels and expandable sections."""
        # Risk filter controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            risk_filter = st.selectbox(
                "🔍 Filter by Risk Level",
                ["All", "Critical", "High", "Medium", "Low"],
                index=0,
                key="risk_level_filter"
            )
        
        with col2:
            sort_by = st.selectbox(
                "📊 Sort by",
                ["Risk Level", "Risk Score", "Clause Name"],
                key="risk_sort_by"
            )
        
        with col3:
            show_details = st.checkbox("Show Details", value=True)
        
        st.markdown("---")
        
        # Risk Summary Cards
        st.subheader("📊 Risk Summary")
        
        risk_counts = self._calculate_risk_counts()
        col1, col2, col3, col4 = st.columns(4)
        
        risk_levels = [("Critical", "#dc3545"), ("High", "#fd7e14"), ("Medium", "#ffc107"), ("Low", "#28a745")]
        
        for i, (level, color) in enumerate(risk_levels):
            count = risk_counts.get(level, 0)
            with [col1, col2, col3, col4][i]:
                st.markdown(f"""
                <div style="background: {color}20; border: 1px solid {color}; border-radius: 8px; padding: 15px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: {color};">{count}</div>
                    <div style="font-size: 14px; color: #666;">{level} Risk</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Detailed Risk Analysis
        st.subheader("⚠️ Detailed Risk Analysis")
        
        risky_clauses = self.results.get('risky_clauses', [])
        if not risky_clauses:
            st.info("No specific risk items identified in this contract.")
            return
        
        # Filter and sort clauses
        filtered_clauses = self._filter_and_sort_risks(risky_clauses, risk_filter, sort_by)
        
        if not filtered_clauses:
            st.warning(f"No clauses found with {risk_filter} risk level.")
            return
        
        # Display risk items
        for i, clause in enumerate(filtered_clauses):
            risk_level = clause.get('risk_level', 'Medium')
            risk_color = self._get_risk_color_hex(risk_level)
            risk_emoji = self._get_risk_color(risk_level)
            
            # Expandable risk item
            section_key = f"risk_section_{i}"
            is_expanded = st.session_state.expanded_sections.get(section_key, False)
            
            # Risk item header
            col1, col2 = st.columns([10, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: {risk_color}15; border-left: 4px solid {risk_color}; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <span style="font-size: 18px; font-weight: bold;">{risk_emoji} {clause.get('clause', f'Risk Item {i+1}')}</span>
                            <span style="background: {risk_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px;">{risk_level}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("👁️" if not is_expanded else "👁️‍🗨️", key=f"toggle_{section_key}", help="Toggle details"):
                    st.session_state.expanded_sections[section_key] = not is_expanded
                    st.rerun()
            
            # Expandable content
            if is_expanded or show_details:
                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid {risk_color}40; border-radius: 8px; padding: 20px; margin: 0 0 20px 0;">
                    """, unsafe_allow_html=True)
                    
                    # Risk details in columns
                    detail_col1, detail_col2 = st.columns([2, 1])
                    
                    with detail_col1:
                        st.markdown("**📝 Description:**")
                        description = clause.get('description', 'No description available')
                        st.markdown(f"<p style='color: #495057; line-height: 1.6;'>{description}</p>", unsafe_allow_html=True)
                        
                        if clause.get('suggestion'):
                            st.markdown("**💡 Recommendation:**")
                            st.info(clause.get('suggestion'))
                        
                        # Show clause text if available
                        if clause.get('clause_text'):
                            with st.expander("📄 View Clause Text"):
                                st.code(clause.get('clause_text'), language=None)
                    
                    with detail_col2:
                        # Risk metrics
                        st.markdown("**📊 Risk Metrics:**")
                        
                        # Risk score if available
                        if 'risk_score' in clause:
                            risk_score = float(clause['risk_score'])
                            st.metric("Risk Score", f"{risk_score:.2f}/1.0")
                        
                        # Confidence if available
                        if 'confidence' in clause:
                            confidence = float(clause['confidence'])
                            st.metric("Confidence", f"{confidence:.1%}")
                        
                        # Category if available
                        if 'category' in clause:
                            st.markdown(f"**Category:** {clause['category']}")
                        
                        # Impact level if available
                        if 'impact' in clause:
                            impact_color = self._get_impact_color(clause['impact'])
                            st.markdown(f"**Impact:** <span style='color: {impact_color}; font-weight: bold;'>{clause['impact']}</span>", unsafe_allow_html=True)
                    
                    # Action buttons
                    st.markdown("**⚡ Actions:**")
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button(f"🔍 Highlight in Contract", key=f"highlight_{i}"):
                            st.session_state.selected_clause = clause.get('clause_id', i)
                            st.info("Clause highlighted! Switch to Contract View to see it.")
                    
                    with action_col2:
                        if st.button(f"✏️ Create Redline", key=f"redline_{i}"):
                            st.session_state.create_redline_for = clause.get('clause_id', i)
                            st.info("Redline creation initiated!")
                    
                    with action_col3:
                        if st.button(f"📚 Find Precedents", key=f"precedent_{i}"):
                            st.session_state.precedent_search = clause.get('clause', '')
                            st.info("Searching for similar precedents...")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        
        # Risk mitigation suggestions
        if len(filtered_clauses) > 0:
            st.markdown("---")
            st.subheader("🛡️ Risk Mitigation Strategies")
            
            mitigation_strategies = self._generate_mitigation_strategies(filtered_clauses)
            for strategy in mitigation_strategies:
                st.markdown(f"• **{strategy['title']}:** {strategy['description']}")
    
    def _calculate_risk_counts(self) -> Dict[str, int]:
        """Calculate count of items by risk level."""
        counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        risky_clauses = self.results.get('risky_clauses', [])
        for clause in risky_clauses:
            risk_level = clause.get('risk_level', 'Medium')
            if risk_level in counts:
                counts[risk_level] += 1
        
        return counts
    
    def _filter_and_sort_risks(self, clauses: List[Dict], risk_filter: str, sort_by: str) -> List[Dict]:
        """Filter and sort risk clauses."""
        # Filter by risk level
        if risk_filter != "All":
            clauses = [c for c in clauses if c.get('risk_level') == risk_filter]
        
        # Sort clauses
        if sort_by == "Risk Level":
            risk_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            clauses.sort(key=lambda x: risk_order.get(x.get('risk_level', 'Medium'), 2))
        elif sort_by == "Risk Score":
            clauses.sort(key=lambda x: float(x.get('risk_score', 0.5)), reverse=True)
        elif sort_by == "Clause Name":
            clauses.sort(key=lambda x: x.get('clause', ''))
        
        return clauses
    
    def _get_impact_color(self, impact: str) -> str:
        """Get color for impact level."""
        impact_colors = {
            'High': '#dc3545',
            'Medium': '#ffc107',
            'Low': '#28a745'
        }
        return impact_colors.get(impact, '#6c757d')
    
    def _generate_mitigation_strategies(self, clauses: List[Dict]) -> List[Dict]:
        """Generate risk mitigation strategies based on identified risks."""
        strategies = []
        
        # Count risk types
        risk_types = {}
        for clause in clauses:
            category = clause.get('category', 'General')
            risk_types[category] = risk_types.get(category, 0) + 1
        
        # Generate strategies based on common risk types
        if risk_types.get('Liability', 0) > 0:
            strategies.append({
                'title': 'Liability Management',
                'description': 'Consider adding mutual liability caps and carve-outs for specific scenarios.'
            })
        
        if risk_types.get('Termination', 0) > 0:
            strategies.append({
                'title': 'Termination Protection',
                'description': 'Ensure adequate notice periods and termination procedures are clearly defined.'
            })
        
        if risk_types.get('Intellectual Property', 0) > 0:
            strategies.append({
                'title': 'IP Protection',
                'description': 'Strengthen intellectual property clauses with clear ownership and indemnification terms.'
            })
        
        # Default strategy if no specific risks identified
        if not strategies:
            strategies.append({
                'title': 'General Risk Management',
                'description': 'Regular contract reviews and legal consultation are recommended for ongoing risk management.'
            })
        
        return strategies
    
    def _render_redlines_tab(self):
        """Render the redlines tab with side-by-side comparison and interactive editing."""
        # Redline controls
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_filter = st.selectbox(
                "📋 Filter by Status",
                ["All", "Pending", "Accepted", "Rejected"],
                key="redline_status_filter"
            )
        
        with col2:
            risk_filter = st.selectbox(
                "⚠️ Filter by Risk Level",
                ["All", "Critical", "High", "Medium", "Low"],
                key="redline_risk_filter"
            )
        
        with col3:
            sort_by = st.selectbox(
                "📊 Sort by",
                ["Risk Level", "Confidence", "Status", "Position"],
                key="redline_sort"
            )
        
        with col4:
            comparison_mode = st.selectbox(
                "👁️ View Mode",
                ["Side by Side", "Overlay", "List View"],
                key="comparison_mode"
            )
        
        st.markdown("---")
        
        # Get redline suggestions from results
        redline_suggestions = self.results.get('redline_suggestions', [])
        if not redline_suggestions:
            st.info("No redline suggestions available for this contract.")
            return
        
        # Filter and sort redlines
        filtered_redlines = self._filter_and_sort_redlines(redline_suggestions, status_filter, risk_filter, sort_by)
        
        if not filtered_redlines:
            st.warning(f"No redlines found matching the selected filters.")
            return
        
        # Redline statistics
        st.subheader("📊 Redline Statistics")
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        total_redlines = len(redline_suggestions)
        accepted_count = len([r for r in redline_suggestions if r.get('status') == 'accepted'])
        rejected_count = len([r for r in redline_suggestions if r.get('status') == 'rejected'])
        pending_count = total_redlines - accepted_count - rejected_count
        
        with stats_col1:
            st.metric("Total Redlines", total_redlines)
        with stats_col2:
            st.metric("✅ Accepted", accepted_count)
        with stats_col3:
            st.metric("❌ Rejected", rejected_count)
        with stats_col4:
            st.metric("⏳ Pending", pending_count)
        
        # Bulk actions
        st.subheader("⚡ Bulk Actions")
        bulk_col1, bulk_col2, bulk_col3, bulk_col4 = st.columns(4)
        
        with bulk_col1:
            if st.button("✅ Accept All High Risk", use_container_width=True):
                self._bulk_action_redlines(redline_suggestions, "accept", "High")
        
        with bulk_col2:
            if st.button("❌ Reject All Low Risk", use_container_width=True):
                self._bulk_action_redlines(redline_suggestions, "reject", "Low")
        
        with bulk_col3:
            if st.button("🔄 Reset All to Pending", use_container_width=True):
                self._bulk_action_redlines(redline_suggestions, "reset", "All")
        
        with bulk_col4:
            if st.button("📄 Export Redlines", use_container_width=True):
                self._export_redlines_report(filtered_redlines)
        
        st.markdown("---")
        
        # Display redlines based on view mode
        st.subheader(f"✏️ Redline Suggestions ({len(filtered_redlines)})")
        
        if comparison_mode == "Side by Side":
            self._render_side_by_side_redlines(filtered_redlines)
        elif comparison_mode == "Overlay":
            self._render_overlay_redlines(filtered_redlines)
        else:  # List View
            self._render_list_redlines(filtered_redlines)
    
    def _render_side_by_side_redlines(self, redlines: List[Dict]):
        """Render redlines in side-by-side comparison mode."""
        for i, redline in enumerate(redlines):
            risk_level = redline.get('risk_level', 'Medium')
            risk_color = self._get_risk_color_hex(risk_level)
            risk_emoji = self._get_risk_color(risk_level)
            status = redline.get('status', 'pending')
            
            # Redline header
            st.markdown(f"""
            <div style="background: {risk_color}15; border-left: 4px solid {risk_color}; padding: 15px; margin: 20px 0 10px 0; border-radius: 0 8px 8px 0;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <span style="font-size: 18px; font-weight: bold;">{risk_emoji} Redline {i+1}</span>
                        <span style="background: {risk_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px;">{risk_level}</span>
                        <span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">{status.title()}</span>
                    </div>
                    <div style="font-size: 14px; color: #666;">
                        Confidence: {redline.get('confidence', 0.8):.1%}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Reason for redline
            if redline.get('reason'):
                st.markdown(f"**💡 Reason:** {redline.get('reason')}")
            
            # Side-by-side comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📄 Original Text**")
                original_text = redline.get('original_text', 'Original text not available')
                st.markdown(f"""
                <div style="background: #fff5f5; border: 1px solid #fed7d7; border-radius: 8px; padding: 15px; min-height: 120px;">
                    <div style="color: #c53030; line-height: 1.6;">{original_text}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**✏️ Suggested Text**")
                suggested_text = redline.get('suggested_text', 'Suggested text not available')
                st.markdown(f"""
                <div style="background: #f0fff4; border: 1px solid #9ae6b4; border-radius: 8px; padding: 15px; min-height: 120px;">
                    <div style="color: #2f855a; line-height: 1.6;">{suggested_text}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Action buttons
            action_col1, action_col2, action_col3, action_col4 = st.columns(4)
            
            with action_col1:
                if st.button("✅ Accept", key=f"accept_redline_{i}", use_container_width=True):
                    redline['status'] = 'accepted'
                    st.success("Redline accepted!")
                    st.rerun()
            
            with action_col2:
                if st.button("❌ Reject", key=f"reject_redline_{i}", use_container_width=True):
                    redline['status'] = 'rejected'
                    st.success("Redline rejected!")
                    st.rerun()
            
            with action_col3:
                if st.button("✏️ Edit", key=f"edit_redline_{i}", use_container_width=True):
                    self._show_redline_editor(redline, i)
            
            with action_col4:
                if st.button("💬 Comment", key=f"comment_redline_{i}", use_container_width=True):
                    self._show_redline_comments(redline, i)
            
            st.markdown("---")
    
    def _render_overlay_redlines(self, redlines: List[Dict]):
        """Render redlines in overlay mode showing changes inline."""
        st.markdown("**📄 Contract with Redline Overlays**")
        
        # Create a version of the contract text with overlays
        contract_with_overlays = self.contract_text
        
        for i, redline in enumerate(redlines):
            original_text = redline.get('original_text', '')
            suggested_text = redline.get('suggested_text', '')
            status = redline.get('status', 'pending')
            
            if original_text in contract_with_overlays:
                if status == 'accepted':
                    # Show accepted changes
                    overlay_html = f'<span style="background-color: #d4edda; text-decoration: line-through; color: #721c24;">{original_text}</span> <span style="background-color: #d1ecf1; color: #0c5460; font-weight: bold;">{suggested_text}</span>'
                elif status == 'rejected':
                    # Show rejected changes (keep original)
                    overlay_html = f'<span style="background-color: #f8d7da; color: #721c24;">{original_text}</span>'
                else:
                    # Show pending changes
                    overlay_html = f'<span style="background-color: #fff3cd; color: #856404; border-bottom: 2px dashed #ffc107;">{original_text}</span> <span style="background-color: #cce5ff; color: #004085; font-style: italic;">→ {suggested_text}</span>'
                
                contract_with_overlays = contract_with_overlays.replace(original_text, overlay_html)
        
        # Display the contract with overlays
        st.markdown(f"""
        <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; max-height: 600px; overflow-y: auto;">
            <div style="font-family: 'Courier New', monospace; line-height: 1.8; color: #333;">
                {contract_with_overlays.replace(chr(10), '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Legend
        st.markdown("**Legend:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<span style="background-color: #d4edda; padding: 2px 6px; border-radius: 4px;">✅ Accepted Changes</span>', unsafe_allow_html=True)
        with col2:
            st.markdown('<span style="background-color: #f8d7da; padding: 2px 6px; border-radius: 4px;">❌ Rejected Changes</span>', unsafe_allow_html=True)
        with col3:
            st.markdown('<span style="background-color: #fff3cd; padding: 2px 6px; border-radius: 4px;">⏳ Pending Changes</span>', unsafe_allow_html=True)
    
    def _render_list_redlines(self, redlines: List[Dict]):
        """Render redlines in simple list view."""
        for i, redline in enumerate(redlines):
            risk_level = redline.get('risk_level', 'Medium')
            risk_emoji = self._get_risk_color(risk_level)
            status = redline.get('status', 'pending')
            
            with st.expander(f"{risk_emoji} Redline {i+1} - {risk_level} Risk ({status.title()})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if redline.get('reason'):
                        st.markdown(f"**💡 Reason:** {redline.get('reason')}")
                    
                    st.markdown("**Original Text:**")
                    st.text_area(
                        "Original",
                        redline.get('original_text', ''),
                        height=80,
                        disabled=True,
                        key=f"list_original_{i}"
                    )
                    
                    st.markdown("**Suggested Text:**")
                    st.text_area(
                        "Suggested",
                        redline.get('suggested_text', ''),
                        height=80,
                        key=f"list_suggested_{i}"
                    )
                
                with col2:
                    st.markdown("**Details:**")
                    st.metric("Risk Level", risk_level)
                    st.metric("Confidence", f"{redline.get('confidence', 0.8):.1%}")
                    st.metric("Status", status.title())
                    
                    # Quick actions
                    if st.button("✅ Accept", key=f"list_accept_{i}"):
                        redline['status'] = 'accepted'
                        st.rerun()
                    
                    if st.button("❌ Reject", key=f"list_reject_{i}"):
                        redline['status'] = 'rejected'
                        st.rerun()
    
    def _filter_and_sort_redlines(self, redlines: List[Dict], status_filter: str, risk_filter: str, sort_by: str) -> List[Dict]:
        """Filter and sort redline suggestions."""
        filtered = redlines.copy()
        
        # Filter by status
        if status_filter != "All":
            filtered = [r for r in filtered if r.get('status', 'pending') == status_filter.lower()]
        
        # Filter by risk level
        if risk_filter != "All":
            filtered = [r for r in filtered if r.get('risk_level') == risk_filter]
        
        # Sort redlines
        if sort_by == "Risk Level":
            risk_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            filtered.sort(key=lambda x: risk_order.get(x.get('risk_level', 'Medium'), 2))
        elif sort_by == "Confidence":
            filtered.sort(key=lambda x: float(x.get('confidence', 0.5)), reverse=True)
        elif sort_by == "Status":
            filtered.sort(key=lambda x: x.get('status', 'pending'))
        elif sort_by == "Position":
            filtered.sort(key=lambda x: int(x.get('position', 0)))
        
        return filtered
    
    def _bulk_action_redlines(self, redlines: List[Dict], action: str, risk_level: str):
        """Perform bulk action on redlines."""
        target_redlines = redlines
        if risk_level != "All":
            target_redlines = [r for r in redlines if r.get('risk_level') == risk_level]
        
        success_count = 0
        for redline in target_redlines:
            if action == "accept":
                redline['status'] = "accepted"
                success_count += 1
            elif action == "reject":
                redline['status'] = "rejected"
                success_count += 1
            elif action == "reset":
                redline['status'] = "pending"
                success_count += 1
        
        if success_count > 0:
            st.success(f"Successfully {action}ed {success_count} redlines")
            st.rerun()
    
    def _show_redline_editor(self, redline: Dict, index: int):
        """Show inline editor for redline."""
        with st.form(f"edit_redline_form_{index}"):
            st.markdown("**✏️ Edit Redline Suggestion**")
            
            new_suggested_text = st.text_area(
                "Suggested Text",
                value=redline.get('suggested_text', ''),
                height=100
            )
            
            new_reason = st.text_area(
                "Reason",
                value=redline.get('reason', ''),
                height=60
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    redline['suggested_text'] = new_suggested_text
                    redline['reason'] = new_reason
                    st.success("Changes saved!")
                    st.rerun()
            
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.rerun()
    
    def _show_redline_comments(self, redline: Dict, index: int):
        """Show comments interface for redline."""
        with st.form(f"comment_redline_form_{index}"):
            st.markdown("**💬 Add Comment**")
            
            comment = st.text_area("Comment", height=80, placeholder="Add your comment about this redline...")
            
            if st.form_submit_button("💬 Add Comment", use_container_width=True):
                # In a real implementation, this would save to backend
                if 'comments' not in redline:
                    redline['comments'] = []
                redline['comments'].append({
                    'text': comment,
                    'timestamp': datetime.now().isoformat(),
                    'author': 'Current User'
                })
                st.success("Comment added!")
                st.rerun()
    
    def _render_redline_item(self, redline: RedlineSuggestion, index: int):
        """Render individual redline suggestion"""
        risk_color = self._get_risk_color(redline.risk_level.value)
        status_color = {
            'pending': '🟡',
            'accepted': '✅',
            'rejected': '❌'
        }.get(redline.status, '❓')
        
        with st.expander(
            f"{status_color} {risk_color} Redline {index + 1} - {redline.risk_level.value} Risk (Confidence: {redline.confidence:.1%})"
        ):
            # Reason
            st.write(f"**Reason:** {redline.reason}")
            
            # Text comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Original Text:**")
                st.text_area(
                    "Original",
                    redline.original_text,
                    height=100,
                    disabled=True,
                    key=f"original_{redline.id}"
                )
            
            with col2:
                st.write("**Suggested Text:**")
                st.text_area(
                    "Suggested",
                    redline.suggested_text,
                    height=100,
                    key=f"suggested_{redline.id}"
                )
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Accept", key=f"accept_{redline.id}"):
                    self._handle_redline_action(redline.id, "accept")
            
            with col2:
                if st.button("❌ Reject", key=f"reject_{redline.id}"):
                    self._handle_redline_action(redline.id, "reject")
            
            with col3:
                if st.button("✏️ Edit", key=f"edit_{redline.id}"):
                    self._handle_redline_edit(redline.id)
            
            with col4:
                if st.button("💬 Comment", key=f"comment_{redline.id}"):
                    self._handle_redline_comment(redline.id)
    
    def _render_precedents_tab(self):
        """Render the precedents tab with search and comparison features."""
        st.subheader("📚 Legal Precedents & Similar Cases")
        
        # Search and filter controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Search Precedents",
                value=st.session_state.get('precedent_search', ''),
                placeholder="Enter keywords, clause types, or legal concepts...",
                key="precedent_search_input"
            )
        
        with col2:
            jurisdiction_filter = st.selectbox(
                "⚖️ Jurisdiction",
                ["All", "Federal", "State", "International"],
                key="jurisdiction_filter"
            )
        
        with col3:
            relevance_threshold = st.slider(
                "📊 Min Relevance",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                key="relevance_threshold"
            )
        
        st.markdown("---")
        
        # Get precedents from results
        precedents = self.precedents
        if not precedents:
            st.info("No legal precedents found for this contract. This could mean:")
            st.markdown("• The contract contains standard, low-risk clauses")
            st.markdown("• The precedent database needs to be updated")
            st.markdown("• The contract uses unique or novel language")
            
            # Offer to search manually
            if st.button("🔍 Search Precedent Database Manually"):
                self._manual_precedent_search(search_query)
            return
        
        # Filter precedents based on search and filters
        filtered_precedents = self._filter_precedents(precedents, search_query, jurisdiction_filter, relevance_threshold)
        
        if not filtered_precedents:
            st.warning("No precedents match your search criteria. Try adjusting the filters or search terms.")
            return
        
        # Precedent statistics
        st.subheader("📊 Precedent Overview")
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            st.metric("Total Found", len(filtered_precedents))
        
        with stats_col2:
            avg_relevance = sum(p.get('relevance_score', 0) for p in filtered_precedents) / len(filtered_precedents)
            st.metric("Avg Relevance", f"{avg_relevance:.1%}")
        
        with stats_col3:
            recent_count = len([p for p in filtered_precedents if self._is_recent_case(p.get('date'))])
            st.metric("Recent Cases", recent_count)
        
        with stats_col4:
            favorable_count = len([p for p in filtered_precedents if p.get('outcome') == 'favorable'])
            st.metric("Favorable Outcomes", favorable_count)
        
        st.markdown("---")
        
        # Display precedents
        st.subheader(f"📚 Relevant Precedents ({len(filtered_precedents)})")
        
        for i, precedent in enumerate(filtered_precedents):
            self._render_precedent_item(precedent, i)
    
    def _render_precedent_item(self, precedent: Dict, index: int):
        """Render individual precedent item."""
        relevance_score = precedent.get('relevance_score', 0.5)
        case_name = precedent.get('case_name', f'Case {index + 1}')
        jurisdiction = precedent.get('jurisdiction', 'Unknown')
        date = precedent.get('date', 'Unknown')
        outcome = precedent.get('outcome', 'unknown')
        
        # Color coding for relevance
        if relevance_score >= 0.8:
            relevance_color = "#28a745"
            relevance_label = "High"
        elif relevance_score >= 0.6:
            relevance_color = "#ffc107"
            relevance_label = "Medium"
        else:
            relevance_color = "#6c757d"
            relevance_label = "Low"
        
        # Outcome color
        outcome_colors = {
            'favorable': '#28a745',
            'unfavorable': '#dc3545',
            'mixed': '#ffc107',
            'unknown': '#6c757d'
        }
        outcome_color = outcome_colors.get(outcome, '#6c757d')
        
        with st.expander(f"📚 {case_name} - {relevance_label} Relevance ({relevance_score:.1%})"):
            # Case header information
            header_col1, header_col2, header_col3 = st.columns(3)
            
            with header_col1:
                st.markdown(f"**⚖️ Jurisdiction:** {jurisdiction}")
                st.markdown(f"**📅 Date:** {date}")
            
            with header_col2:
                st.markdown(f"**📊 Relevance:** <span style='color: {relevance_color}; font-weight: bold;'>{relevance_score:.1%}</span>", unsafe_allow_html=True)
                st.markdown(f"**🎯 Outcome:** <span style='color: {outcome_color}; font-weight: bold;'>{outcome.title()}</span>", unsafe_allow_html=True)
            
            with header_col3:
                if 'citation' in precedent:
                    st.markdown(f"**📖 Citation:** {precedent['citation']}")
                if 'court' in precedent:
                    st.markdown(f"**🏛️ Court:** {precedent['court']}")
            
            # Case summary and relevant text
            if precedent.get('summary'):
                st.markdown("**📝 Case Summary:**")
                st.markdown(f"<div style='background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;'>{precedent['summary']}</div>", unsafe_allow_html=True)
            
            if precedent.get('relevant_text'):
                st.markdown("**🔍 Relevant Excerpt:**")
                st.markdown(f"<div style='background: #fff3cd; padding: 15px; border-radius: 8px; font-style: italic;'>\"{precedent['relevant_text']}\"</div>", unsafe_allow_html=True)
            
            # Key takeaways and implications
            if precedent.get('key_takeaways'):
                st.markdown("**💡 Key Takeaways:**")
                for takeaway in precedent['key_takeaways']:
                    st.markdown(f"• {takeaway}")
            
            if precedent.get('implications'):
                st.markdown("**⚠️ Implications for Your Contract:**")
                st.info(precedent['implications'])
            
            # Action buttons
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button(f"📄 View Full Case", key=f"view_case_{index}"):
                    self._show_full_case_details(precedent)
            
            with action_col2:
                if st.button(f"🔗 Compare with Contract", key=f"compare_case_{index}"):
                    self._compare_with_contract(precedent)
            
            with action_col3:
                if st.button(f"📋 Add to Report", key=f"add_to_report_{index}"):
                    self._add_precedent_to_report(precedent)
                    st.success("Added to report!")
    
    def _filter_precedents(self, precedents: List[Dict], search_query: str, jurisdiction_filter: str, relevance_threshold: float) -> List[Dict]:
        """Filter precedents based on search criteria."""
        filtered = precedents.copy()
        
        # Filter by search query
        if search_query:
            search_terms = search_query.lower().split()
            filtered = [
                p for p in filtered
                if any(
                    term in p.get('case_name', '').lower() or
                    term in p.get('summary', '').lower() or
                    term in p.get('relevant_text', '').lower() or
                    term in ' '.join(p.get('key_takeaways', [])).lower()
                    for term in search_terms
                )
            ]
        
        # Filter by jurisdiction
        if jurisdiction_filter != "All":
            filtered = [p for p in filtered if p.get('jurisdiction', '').lower() == jurisdiction_filter.lower()]
        
        # Filter by relevance threshold
        filtered = [p for p in filtered if p.get('relevance_score', 0) >= relevance_threshold]
        
        # Sort by relevance score (highest first)
        filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return filtered
    
    def _is_recent_case(self, date_str: str) -> bool:
        """Check if a case is recent (within last 5 years)."""
        if not date_str or date_str == 'Unknown':
            return False
        
        try:
            # Simple year extraction - in a real implementation, use proper date parsing
            year = int(date_str.split()[-1]) if date_str.split()[-1].isdigit() else 0
            current_year = datetime.now().year
            return (current_year - year) <= 5
        except:
            return False
    
    def _manual_precedent_search(self, query: str):
        """Perform manual precedent search."""
        st.info(f"Searching precedent database for: '{query}'")
        # In a real implementation, this would call the backend API
        st.warning("Manual precedent search feature is not yet implemented.")
    
    def _show_full_case_details(self, precedent: Dict):
        """Show full case details in a modal or new section."""
        st.info("Full case details would be displayed here. This feature requires integration with legal databases.")
    
    def _compare_with_contract(self, precedent: Dict):
        """Compare precedent with current contract."""
        st.info("Contract comparison feature would highlight similar clauses and differences.")
    
    def _add_precedent_to_report(self, precedent: Dict):
        """Add precedent to the analysis report."""
        # In a real implementation, this would add to a report compilation
        if 'report_precedents' not in st.session_state:
            st.session_state.report_precedents = []
        
        st.session_state.report_precedents.append(precedent)
    
    def _render_single_contract_view(self, highlight_risks: bool, show_redlines: bool):
        """Render single contract view"""
        contract_html = self._generate_contract_html(self.contract_text, highlight_risks, show_redlines)
        
        st.components.v1.html(
            f"""
            <div style="height: 600px; overflow-y: auto; border: 1px solid #ddd; padding: 20px; background: white;">
                {contract_html}
            </div>
            """,
            height=650
        )
    
    def _render_split_contract_view(self, highlight_risks: bool, show_redlines: bool):
        """Render split contract view (original vs revised)"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Original Contract**")
            original_html = self._generate_contract_html(self.contract_text, highlight_risks, False)
            st.components.v1.html(
                f"""
                <div style="height: 500px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; background: white;">
                    {original_html}
                </div>
                """,
                height=550
            )
        
        with col2:
            st.write("**Revised Contract (with accepted redlines)**")
            revised_text = self._apply_accepted_redlines(self.contract_text)
            revised_html = self._generate_contract_html(revised_text, highlight_risks, show_redlines)
            st.components.v1.html(
                f"""
                <div style="height: 500px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; background: white;">
                    {revised_html}
                </div>
                """,
                height=550
            )
    
    def _render_analytics(self):
        """Render analytics and insights"""
        st.subheader("📈 Contract Analytics")
        
        # Risk trends
        if len(self.clauses) > 1:
            st.subheader("Risk Score Distribution")
            
            risk_scores = [clause.risk_score for clause in self.clauses]
            clause_names = [clause.title for clause in self.clauses]
            
            fig = go.Figure(data=go.Bar(
                x=clause_names,
                y=risk_scores,
                marker_color=[self._get_risk_color_hex(clause.risk_level.value) for clause in self.clauses]
            ))
            fig.update_layout(
                title="Risk Scores by Clause",
                xaxis_title="Clauses",
                yaxis_title="Risk Score",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Redline statistics
        if self.redlines:
            st.subheader("Redline Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Status distribution
                status_counts = {}
                for redline in self.redlines:
                    status_counts[redline.status] = status_counts.get(redline.status, 0) + 1
                
                fig = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    title="Redline Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Confidence distribution
                confidence_scores = [redline.confidence for redline in self.redlines]
                
                fig = go.Figure(data=go.Histogram(x=confidence_scores, nbinsx=10))
                fig.update_layout(
                    title="Redline Confidence Distribution",
                    xaxis_title="Confidence Score",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Export analytics
        st.subheader("Export Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export Risk Report", use_container_width=True):
                self._export_risk_report()
        
        with col2:
            if st.button("📋 Export Redline Summary", use_container_width=True):
                self._export_redline_summary()
        
        with col3:
            if st.button("📈 Export Full Analytics", use_container_width=True):
                self._export_full_analytics()
    
    def _get_risk_color(self, risk_level: str) -> str:
        """Get emoji for risk level"""
        return {
            'Low': '🟢',
            'Medium': '🟡', 
            'High': '🔴',
            'Critical': '🚨'
        }.get(risk_level, '⚪')
    
    def _get_risk_color_hex(self, risk_level: str) -> str:
        """Get hex color for risk level"""
        return {
            'Low': '#28a745',
            'Medium': '#ffc107', 
            'High': '#fd7e14',
            'Critical': '#dc3545'
        }.get(risk_level, '#6c757d')
    
    def _filter_redlines(self, status_filter: str, risk_filter: str) -> List[RedlineSuggestion]:
        """Filter redlines based on status and risk level"""
        filtered = self.redlines
        
        if status_filter != "All":
            filtered = [r for r in filtered if r.status == status_filter.lower()]
        
        if risk_filter != "All":
            filtered = [r for r in filtered if r.risk_level.value == risk_filter]
        
        return filtered
    
    def _bulk_action_redlines(self, action: str, risk_level: str):
        """Perform bulk action on redlines"""
        if not self.api_client:
            st.warning("API client not available for bulk actions")
            return
        
        target_redlines = self.redlines
        if risk_level != "All":
            target_redlines = [r for r in self.redlines if r.risk_level.value == risk_level]
        
        success_count = 0
        for redline in target_redlines:
            try:
                if action == "accept":
                    response = self.api_client.accept_redline(self.contract_id, redline.id)
                    if 'error' not in response:
                        redline.status = "accepted"
                        success_count += 1
                elif action == "reject":
                    response = self.api_client.reject_redline(self.contract_id, redline.id)
                    if 'error' not in response:
                        redline.status = "rejected"
                        success_count += 1
                elif action == "reset":
                    redline.status = "pending"
                    success_count += 1
            except Exception as e:
                st.error(f"Error processing redline {redline.id}: {e}")
        
        if success_count > 0:
            st.success(f"Successfully processed {success_count} redlines")
            st.rerun()
    
    def _handle_redline_action(self, redline_id: str, action: str):
        """Handle individual redline action"""
        if not self.api_client:
            st.warning("API client not available")
            return
        
        try:
            if action == "accept":
                response = self.api_client.accept_redline(self.contract_id, redline_id)
            elif action == "reject":
                response = self.api_client.reject_redline(self.contract_id, redline_id)
            else:
                return
            
            if 'error' not in response:
                # Update local state
                for redline in self.redlines:
                    if redline.id == redline_id:
                        redline.status = action + "ed"
                        break
                
                st.success(f"Redline {action}ed successfully")
                st.rerun()
            else:
                st.error(f"Error: {response['error']}")
                
        except Exception as e:
            st.error(f"Error processing redline: {e}")
    
    def _handle_redline_edit(self, redline_id: str):
        """Handle redline editing"""
        redline = next((r for r in self.redlines if r.id == redline_id), None)
        if not redline:
            return
        
        with st.form(f"edit_redline_{redline_id}"):
            st.write("**Edit Redline Suggestion**")
            
            new_text = st.text_area(
                "Suggested Text",
                value=redline.suggested_text,
                height=100
            )
            
            new_reason = st.text_area(
                "Reason",
                value=redline.reason,
                height=60
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Changes"):
                    redline.suggested_text = new_text
                    redline.reason = new_reason
                    st.success("Changes saved locally")
                    st.rerun()
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.rerun()
    
    def _handle_redline_comment(self, redline_id: str):
        """Handle redline commenting"""
        with st.form(f"comment_redline_{redline_id}"):
            st.write("**Add Comment**")
            
            comment = st.text_area("Comment", height=80)
            
            if st.form_submit_button("💬 Add Comment"):
                # In a real implementation, this would save to backend
                st.success("Comment added (local only)")
                st.rerun()
    
    def _generate_contract_html(self, text: str, highlight_risks: bool, show_redlines: bool) -> str:
        """Generate HTML for contract display with highlighting"""
        html = text.replace('\n', '<br>')
        
        if highlight_risks:
            # Highlight high-risk clauses
            for clause in self.clauses:
                if clause.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    color = self._get_risk_color_hex(clause.risk_level.value)
                    if clause.content in text:
                        html = html.replace(
                            clause.content,
                            f'<span style="background-color: {color}20; border-left: 3px solid {color}; padding: 2px 5px;">{clause.content}</span>'
                        )
        
        if show_redlines:
            # Show redline overlays
            for redline in self.redlines:
                if redline.status == "accepted" and redline.original_text in html:
                    html = html.replace(
                        redline.original_text,
                        f'<span style="background-color: #28a74520; text-decoration: line-through;">{redline.original_text}</span>'
                        f'<span style="background-color: #28a74530; font-weight: bold;"> {redline.suggested_text}</span>'
                    )
        
        return f'<div style="font-family: monospace; line-height: 1.6; color: #333;">{html}</div>'
    
    def _apply_accepted_redlines(self, text: str) -> str:
        """Apply accepted redlines to generate revised contract"""
        revised_text = text
        
        for redline in self.redlines:
            if redline.status == "accepted":
                revised_text = revised_text.replace(redline.original_text, redline.suggested_text)
        
        return revised_text
    
    def _export_risk_report(self):
        """Export risk analysis report"""
        report_data = {
            'contract_id': self.contract_id,
            'filename': self.filename,
            'overall_risk': self.risk_summary['overall_risk'],
            'risk_score': self.risk_summary['risk_score'],
            'confidence': self.risk_summary['confidence'],
            'risk_distribution': self.risk_summary['risk_distribution'],
            'high_risk_clauses': [
                {
                    'title': clause.title,
                    'risk_level': clause.risk_level.value,
                    'risk_score': clause.risk_score,
                    'issues': clause.issues
                }
                for clause in self.clauses 
                if clause.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            ],
            'generated_at': datetime.now().isoformat()
        }
        
        report_json = json.dumps(report_data, indent=2)
        st.download_button(
            label="📊 Download Risk Report",
            data=report_json,
            file_name=f"{self.filename}_risk_report.json",
            mime="application/json"
        )
    
    def _export_redline_summary(self):
        """Export redline summary"""
        summary_data = {
            'contract_id': self.contract_id,
            'filename': self.filename,
            'total_redlines': len(self.redlines),
            'accepted_redlines': len([r for r in self.redlines if r.status == "accepted"]),
            'rejected_redlines': len([r for r in self.redlines if r.status == "rejected"]),
            'pending_redlines': len([r for r in self.redlines if r.status == "pending"]),
            'redlines': [
                {
                    'id': redline.id,
                    'risk_level': redline.risk_level.value,
                    'confidence': redline.confidence,
                    'status': redline.status,
                    'reason': redline.reason,
                    'original_text': redline.original_text[:100] + "..." if len(redline.original_text) > 100 else redline.original_text,
                    'suggested_text': redline.suggested_text[:100] + "..." if len(redline.suggested_text) > 100 else redline.suggested_text
                }
                for redline in self.redlines
            ],
            'generated_at': datetime.now().isoformat()
        }
        
        summary_json = json.dumps(summary_data, indent=2)
        st.download_button(
            label="📋 Download Redline Summary",
            data=summary_json,
            file_name=f"{self.filename}_redline_summary.json",
            mime="application/json"
        )
    
    def _export_full_analytics(self):
        """Export full analytics report"""
        analytics_data = {
            'contract_analysis': {
                'contract_id': self.contract_id,
                'filename': self.filename,
                'analysis_timestamp': datetime.now().isoformat(),
                'risk_summary': self.risk_summary,
                'clauses': [
                    {
                        'id': clause.id,
                        'title': clause.title,
                        'risk_level': clause.risk_level.value,
                        'risk_score': clause.risk_score,
                        'category': clause.category,
                        'issues_count': len(clause.issues),
                        'suggestions_count': len(clause.suggestions)
                    }
                    for clause in self.clauses
                ],
                'redlines': [
                    {
                        'id': redline.id,
                        'risk_level': redline.risk_level.value,
                        'confidence': redline.confidence,
                        'status': redline.status
                    }
                    for redline in self.redlines
                ]
            }
        }
        
        analytics_json = json.dumps(analytics_data, indent=2)
        st.download_button(
            label="📈 Download Full Analytics",
            data=analytics_json,
            file_name=f"{self.filename}_full_analytics.json",
            mime="application/json"
        )

# Legacy class for backward compatibility
class AnalysisResultsDisplay:
    """Legacy component for displaying job application tracking results."""
    
    def __init__(self, results, contract_text="", filename="contract.pdf"):
        self.results = results
        self.contract_text = contract_text
        self.filename = filename
        self.render()
    
    def render(self):
        """Render the complete analysis results."""
        st.header("📋 Analysis Results")
        
        # Summary section
        self._render_summary()
        
        # Risk assessment
        self._render_risk_assessment()
        
        # Key findings
        self._render_key_findings()
        
        # Detailed analysis
        self._render_detailed_analysis()
        
        # Contract text (if available)
        if self.contract_text:
            self._render_contract_text()
        
        # Export options
        self._render_export_options()
    
    def _render_summary(self):
        """Render analysis summary."""
        st.subheader("📊 Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_level = self.results.get('risk_level', 'Unknown')
            risk_color = {
                'Low': '🟢',
                'Medium': '🟡', 
                'High': '🔴',
                'Critical': '🚨'
            }.get(risk_level, '⚪')
            st.metric("Risk Level", f"{risk_color} {risk_level}")
        
        with col2:
            confidence = self.results.get('confidence_score', 0)
            st.metric("Confidence", f"{confidence:.1f}%")
        
        with col3:
            issues_found = len(self.results.get('issues', []))
            st.metric("Issues Found", issues_found)
        
        with col4:
            analysis_time = self.results.get('analysis_time', 'N/A')
            st.metric("Analysis Time", analysis_time)
    
    def _render_risk_assessment(self):
        """Render risk assessment section."""
        st.subheader("⚠️ Risk Assessment")
        
        risk_factors = self.results.get('risk_factors', [])
        
        if risk_factors:
            for factor in risk_factors:
                severity = factor.get('severity', 'Medium')
                color = {
                    'Low': 'success',
                    'Medium': 'warning',
                    'High': 'error'
                }.get(severity, 'info')
                
                with st.container():
                    if color == 'error':
                        st.error(f"🔴 **{factor.get('title', 'Risk Factor')}**")
                    elif color == 'warning':
                        st.warning(f"🟡 **{factor.get('title', 'Risk Factor')}**")
                    else:
                        st.success(f"🟢 **{factor.get('title', 'Risk Factor')}**")
                    
                    st.write(factor.get('description', 'No description available'))
                    
                    if 'recommendation' in factor:
                        st.info(f"💡 **Recommendation:** {factor['recommendation']}")
        else:
            st.info("No specific risk factors identified.")
    
    def _render_key_findings(self):
        """Render key findings section."""
        st.subheader("🔍 Key Findings")
        
        findings = self.results.get('key_findings', [])
        
        if findings:
            for i, finding in enumerate(findings, 1):
                with st.expander(f"Finding {i}: {finding.get('title', 'Untitled')}"):
                    st.write(finding.get('description', 'No description available'))
                    
                    if 'location' in finding:
                        st.caption(f"📍 Location: {finding['location']}")
                    
                    if 'impact' in finding:
                        st.write(f"**Impact:** {finding['impact']}")
                    
                    if 'suggestion' in finding:
                        st.success(f"💡 **Suggestion:** {finding['suggestion']}")
        else:
            st.info("No key findings to display.")
    
    def _render_detailed_analysis(self):
        """Render detailed analysis section."""
        st.subheader("📝 Detailed Analysis")
        
        # Clauses analysis
        clauses = self.results.get('clauses_analysis', [])
        if clauses:
            st.write("**Contract Clauses Analysis:**")
            
            clauses_df = pd.DataFrame(clauses)
            if not clauses_df.empty:
                st.dataframe(clauses_df, use_container_width=True)
        
        # Terms analysis
        terms = self.results.get('terms_analysis', {})
        if terms:
            st.write("**Terms Analysis:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Favorable Terms:**")
                favorable = terms.get('favorable', [])
                for term in favorable:
                    st.success(f"✅ {term}")
            
            with col2:
                st.write("**Concerning Terms:**")
                concerning = terms.get('concerning', [])
                for term in concerning:
                    st.error(f"❌ {term}")
        
        # Compliance check
        compliance = self.results.get('compliance_check', {})
        if compliance:
            st.write("**Compliance Analysis:**")
            
            for standard, status in compliance.items():
                if status.get('compliant', False):
                    st.success(f"✅ {standard}: Compliant")
                else:
                    st.error(f"❌ {standard}: Non-compliant")
                    if 'issues' in status:
                        for issue in status['issues']:
                            st.write(f"  • {issue}")
    
    def _render_contract_text(self):
        """Render contract text section."""
        with st.expander("📄 Contract Text", expanded=False):
            st.text_area(
                "Full Contract Content",
                value=self.contract_text,
                height=300,
                disabled=True
            )
    
    def _render_export_options(self):
        """Render export options."""
        st.subheader("📤 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export as JSON", use_container_width=True):
                json_str = json.dumps(self.results, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"{self.filename}_analysis.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📋 Export as CSV", use_container_width=True):
                # Convert results to CSV format
                csv_data = self._convert_to_csv()
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"{self.filename}_analysis.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("📄 Generate Report", use_container_width=True):
                report = self._generate_report()
                st.download_button(
                    label="Download Report",
                    data=report,
                    file_name=f"{self.filename}_report.txt",
                    mime="text/plain"
                )
    
    def _convert_to_csv(self):
        """Convert results to CSV format."""
        # Simple CSV conversion
        csv_lines = ["Field,Value"]
        csv_lines.append(f"Filename,{self.filename}")
        csv_lines.append(f"Risk Level,{self.results.get('risk_level', 'Unknown')}")
        csv_lines.append(f"Confidence Score,{self.results.get('confidence_score', 0)}")
        csv_lines.append(f"Analysis Time,{self.results.get('analysis_time', 'N/A')}")
        csv_lines.append(f"Issues Found,{len(self.results.get('issues', []))}")
        
        return "\n".join(csv_lines)
    
    def _generate_report(self):
        """Generate a text report."""
        report_lines = [
            f"CONTRACT ANALYSIS REPORT",
            f"=" * 50,
            f"",
            f"File: {self.filename}",
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"SUMMARY",
            f"-" * 20,
            f"Risk Level: {self.results.get('risk_level', 'Unknown')}",
            f"Confidence Score: {self.results.get('confidence_score', 0):.1f}%",
            f"Issues Found: {len(self.results.get('issues', []))}",
            f"Analysis Time: {self.results.get('analysis_time', 'N/A')}",
            f"",
        ]
        
        # Add risk factors
        risk_factors = self.results.get('risk_factors', [])
        if risk_factors:
            report_lines.extend([
                f"RISK FACTORS",
                f"-" * 20,
            ])
            for factor in risk_factors:
                report_lines.extend([
                    f"• {factor.get('title', 'Untitled')} ({factor.get('severity', 'Medium')})",
                    f"  {factor.get('description', 'No description')}",
                    f""
                ])
        
        # Add key findings
        findings = self.results.get('key_findings', [])
        if findings:
            report_lines.extend([
                f"KEY FINDINGS",
                f"-" * 20,
            ])
            for i, finding in enumerate(findings, 1):
                report_lines.extend([
                    f"{i}. {finding.get('title', 'Untitled')}",
                    f"   {finding.get('description', 'No description')}",
                    f""
                ])
        
        return "\n".join(report_lines)
    
    def _export_comprehensive_report(self):
        """Export comprehensive analysis report in multiple formats."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export as JSON", use_container_width=True):
                self._export_json_report()
        
        with col2:
            if st.button("📄 Export as PDF", use_container_width=True):
                self._export_pdf_report()
        
        with col3:
            if st.button("📋 Export as CSV", use_container_width=True):
                self._export_csv_report()
    
    def _export_json_report(self):
        """Export complete analysis as JSON."""
        report_data = {
            'contract_analysis': {
                'contract_id': self.contract_id,
                'filename': self.filename,
                'analysis_date': datetime.now().isoformat(),
                'risk_summary': self.risk_summary,
                'risky_clauses': self.results.get('risky_clauses', []),
                'redline_suggestions': self.results.get('redline_suggestions', []),
                'precedents': self.precedents,
                'recommendations': self.results.get('recommendations', []),
                'processing_time': self.results.get('processing_time', 0),
                'confidence_score': self.results.get('confidence_score', 0.8)
            }
        }
        
        json_str = json.dumps(report_data, indent=2)
        st.download_button(
            label="📊 Download JSON Report",
            data=json_str,
            file_name=f"{self.filename}_analysis_report.json",
            mime="application/json"
        )
    
    def _export_pdf_report(self):
        """Export analysis as PDF report."""
        # Generate HTML report that can be converted to PDF
        html_report = self._generate_html_report()
        
        st.download_button(
            label="📄 Download HTML Report (Print as PDF)",
            data=html_report,
            file_name=f"{self.filename}_analysis_report.html",
            mime="text/html"
        )
        
        st.info("💡 Tip: Open the downloaded HTML file in your browser and use 'Print to PDF' for a formatted PDF report.")
    
    def _export_csv_report(self):
        """Export analysis data as CSV."""
        # Create CSV data for risks
        csv_data = []
        csv_data.append(["Type", "Item", "Risk Level", "Description", "Recommendation"])
        
        # Add risky clauses
        for clause in self.results.get('risky_clauses', []):
            csv_data.append([
                "Risk",
                clause.get('clause', 'Unknown'),
                clause.get('risk_level', 'Medium'),
                clause.get('description', ''),
                clause.get('suggestion', '')
            ])
        
        # Add redlines
        for redline in self.results.get('redline_suggestions', []):
            csv_data.append([
                "Redline",
                redline.get('original_text', '')[:50] + "...",
                redline.get('risk_level', 'Medium'),
                redline.get('reason', ''),
                redline.get('suggested_text', '')[:50] + "..."
            ])
        
        # Convert to CSV string
        csv_string = "\n".join([",".join([f'"{cell}"' for cell in row]) for row in csv_data])
        
        st.download_button(
            label="📋 Download CSV Report",
            data=csv_string,
            file_name=f"{self.filename}_analysis_data.csv",
            mime="text/csv"
        )
    
    def _generate_html_report(self) -> str:
        """Generate HTML report for PDF export."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contract Analysis Report - {self.filename}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ background: #667eea; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .risk-critical {{ color: #dc3545; font-weight: bold; }}
                .risk-high {{ color: #fd7e14; font-weight: bold; }}
                .risk-medium {{ color: #ffc107; font-weight: bold; }}
                .risk-low {{ color: #28a745; font-weight: bold; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Contract Analysis Report</h1>
                <p><strong>File:</strong> {self.filename}</p>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="metric">
                    <strong>Overall Risk:</strong> <span class="risk-{self.risk_summary.get('overall_risk', 'medium').lower()}">{self.risk_summary.get('overall_risk', 'Medium')}</span>
                </div>
                <div class="metric">
                    <strong>Risk Score:</strong> {self.risk_summary.get('risk_score', 0.5):.1%}
                </div>
                <div class="metric">
                    <strong>Confidence:</strong> {self.risk_summary.get('confidence', 0.8):.1%}
                </div>
                <p>{self.results.get('summary', 'This contract has been analyzed for potential risks and issues.')}</p>
            </div>
            
            <div class="section">
                <h2>Risk Analysis</h2>
                <table>
                    <tr>
                        <th>Clause</th>
                        <th>Risk Level</th>
                        <th>Description</th>
                        <th>Recommendation</th>
                    </tr>
        """
        
        # Add risky clauses to table
        for clause in self.results.get('risky_clauses', []):
            risk_level = clause.get('risk_level', 'Medium')
            html += f"""
                    <tr>
                        <td>{clause.get('clause', 'Unknown')}</td>
                        <td><span class="risk-{risk_level.lower()}">{risk_level}</span></td>
                        <td>{clause.get('description', '')}</td>
                        <td>{clause.get('suggestion', '')}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Redline Suggestions</h2>
                <table>
                    <tr>
                        <th>Original Text</th>
                        <th>Suggested Text</th>
                        <th>Reason</th>
                        <th>Risk Level</th>
                    </tr>
        """
        
        # Add redlines to table
        for redline in self.results.get('redline_suggestions', []):
            risk_level = redline.get('risk_level', 'Medium')
            html += f"""
                    <tr>
                        <td>{redline.get('original_text', '')[:100]}...</td>
                        <td>{redline.get('suggested_text', '')[:100]}...</td>
                        <td>{redline.get('reason', '')}</td>
                        <td><span class="risk-{risk_level.lower()}">{risk_level}</span></td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
        """
        
        # Add recommendations
        for rec in self.results.get('recommendations', []):
            html += f"<li>{rec}</li>"
        
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _export_redlines_report(self, redlines: List[Dict]):
        """Export redlines as a separate report."""
        redlines_data = {
            'contract_id': self.contract_id,
            'filename': self.filename,
            'export_date': datetime.now().isoformat(),
            'total_redlines': len(redlines),
            'redlines': redlines
        }
        
        json_str = json.dumps(redlines_data, indent=2)
        st.download_button(
            label="📄 Download Redlines Report",
            data=json_str,
            file_name=f"{self.filename}_redlines.json",
            mime="application/json"
        )

# Backward compatibility - keep the original class name
class AnalysisResultsDisplay:
    """Backward compatibility wrapper for the enhanced interactive results display."""
    
    def __init__(self, results: Dict[str, Any], contract_text: str = "", filename: str = "contract.pdf"):
        # Create the interactive display
        self.interactive_display = InteractiveAnalysisResultsDisplay(
            results=results,
            contract_text=contract_text,
            filename=filename
        )
    
    def render(self):
        """Render the results display."""
        return self.interactive_display.render()