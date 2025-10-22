"""
Interactive Analytics Dashboard for Career Copilot
Advanced analytics with interactive charts, drill-down capabilities, and export functionality
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import io
import base64


class InteractiveAnalyticsDashboard:
    """Interactive analytics dashboard with advanced visualizations"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def render_main_dashboard(self):
        """Render the main interactive analytics dashboard"""
        st.title("📊 Interactive Analytics Dashboard")
        st.markdown("Advanced analytics with interactive visualizations and drill-down capabilities")
        
        # Dashboard controls
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            timeframe = st.selectbox(
                "Analysis Period",
                options=["30d", "90d", "180d", "1y"],
                index=1,
                help="Select the time period for analysis"
            )
        
        with col2:
            analytics_type = st.selectbox(
                "Analytics Type",
                options=["Overview", "Success Rates", "Conversion Funnel", "Performance Benchmarks", "Market Trends"],
                help="Choose the type of analytics to display"
            )
        
        with col3:
            if st.button("🔄 Refresh Data", help="Reload analytics data"):
                st.cache_data.clear()
                st.rerun()
        
        with col4:
            if st.button("📊 Export Report", help="Export analytics report"):
                self._export_analytics_report(timeframe)
        
        st.divider()
        
        # Render selected analytics type
        if analytics_type == "Overview":
            self._render_overview_dashboard(timeframe)
        elif analytics_type == "Success Rates":
            self._render_success_rates_dashboard(timeframe)
        elif analytics_type == "Conversion Funnel":
            self._render_conversion_funnel_dashboard(timeframe)
        elif analytics_type == "Performance Benchmarks":
            self._render_performance_benchmarks_dashboard(timeframe)
        elif analytics_type == "Market Trends":
            self._render_market_trends_dashboard(timeframe)
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def _get_comprehensive_analytics(_self, timeframe: str) -> Dict[str, Any]:
        """Get comprehensive analytics data with caching"""
        try:
            days = {"30d": 30, "90d": 90, "180d": 180, "1y": 365}[timeframe]
            
            response = _self.api_client.session.get(
                f"{_self.api_client.base_url}/api/v1/analytics/comprehensive-dashboard",
                params={"days": days},
                headers=_self.api_client._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Failed to fetch analytics: {str(e)}"}
    
    @st.cache_data(ttl=300)
    def _get_market_analysis(_self, timeframe: str) -> Dict[str, Any]:
        """Get market analysis data with caching"""
        try:
            days = {"30d": 30, "90d": 90, "180d": 180, "1y": 365}[timeframe]
            
            response = _self.api_client.session.get(
                f"{_self.api_client.base_url}/api/v1/market-analysis/dashboard",
                headers=_self.api_client._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Failed to fetch market analysis: {str(e)}"}
    
    def _render_overview_dashboard(self, timeframe: str):
        """Render comprehensive overview dashboard"""
        with st.spinner("Loading comprehensive analytics..."):
            analytics = self._get_comprehensive_analytics(timeframe)
        
        if "error" in analytics:
            st.error(f"Failed to load analytics: {analytics['error']}")
            return
        
        # Executive Summary
        st.subheader("📈 Executive Summary")
        
        summary = analytics.get('executive_summary', {})
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Success Rate",
                f"{summary.get('overall_success_rate', 0):.1f}%",
                help="Percentage of applications that resulted in offers"
            )
        
        with col2:
            st.metric(
                "Applications",
                summary.get('total_applications', 0),
                help="Total applications submitted in the period"
            )
        
        with col3:
            st.metric(
                "Interview Rate",
                f"{summary.get('interview_rate', 0):.1f}%",
                help="Percentage of applications that led to interviews"
            )
        
        with col4:
            st.metric(
                "Performance Score",
                f"{summary.get('performance_score', 0):.0f}/100",
                help="Overall performance score vs market benchmarks"
            )
        
        with col5:
            market_position = summary.get('market_position', 'average').replace('_', ' ').title()
            st.metric(
                "Market Position",
                market_position,
                help="Your position relative to other job seekers"
            )
        
        # Interactive Charts
        st.subheader("📊 Performance Trends")
        
        # Weekly performance chart
        weekly_data = analytics.get('chart_data', {}).get('weekly_performance', [])
        if weekly_data:
            df_weekly = pd.DataFrame(weekly_data)
            
            fig = px.line(
                df_weekly,
                x='week',
                y=['interview_rate', 'success_rate'],
                title="Weekly Performance Trends",
                labels={'value': 'Rate (%)', 'week': 'Week'},
                color_discrete_map={'interview_rate': '#1f77b4', 'success_rate': '#ff7f0e'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Conversion Funnel
        st.subheader("🔄 Conversion Funnel")
        
        funnel_data = analytics.get('chart_data', {}).get('funnel_stages', [])
        if funnel_data:
            df_funnel = pd.DataFrame(funnel_data)
            
            fig = go.Figure(go.Funnel(
                y=df_funnel['stage'],
                x=df_funnel['count'],
                textinfo="value+percent initial",
                marker=dict(color=["deepskyblue", "lightsalmon", "tan", "teal", "silver"])
            ))
            fig.update_layout(title="Application Conversion Funnel", height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance Benchmarks
        st.subheader("🎯 Performance vs Market")
        
        benchmark_data = analytics.get('chart_data', {}).get('benchmark_comparison', [])
        if benchmark_data:
            df_benchmark = pd.DataFrame(benchmark_data)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Your Performance',
                x=df_benchmark['metric'],
                y=df_benchmark['user_value'],
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='Market Average',
                x=df_benchmark['metric'],
                y=df_benchmark['market_average'],
                marker_color='orange'
            ))
            
            fig.update_layout(
                title="Performance vs Market Benchmarks",
                barmode='group',
                height=400,
                yaxis_title="Rate (%)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Key Insights and Recommendations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💡 Key Insights")
            insights = analytics.get('key_insights', 'No insights available')
            st.info(insights)
        
        with col2:
            st.subheader("🎯 Top Recommendations")
            recommendations = analytics.get('top_recommendations', [])
            for i, rec in enumerate(recommendations[:5], 1):
                st.write(f"{i}. {rec}")
    
    def _render_success_rates_dashboard(self, timeframe: str):
        """Render detailed success rates dashboard"""
        st.subheader("📈 Detailed Success Rate Analysis")
        
        try:
            days = {"30d": 30, "90d": 90, "180d": 180, "1y": 365}[timeframe]
            
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/api/v1/analytics/success-rates",
                params={"days": days},
                headers=self.api_client._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                st.error(f"Failed to load success rates: HTTP {response.status_code}")
                return
            
            data = response.json()
            
            # Success Rate Metrics
            success_rates = data.get('success_rates', {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Application → Interview",
                    f"{success_rates.get('application_to_interview', 0):.1f}%"
                )
            
            with col2:
                st.metric(
                    "Interview → Offer",
                    f"{success_rates.get('interview_to_offer', 0):.1f}%"
                )
            
            with col3:
                st.metric(
                    "Overall Success",
                    f"{success_rates.get('overall_success', 0):.1f}%"
                )
            
            with col4:
                st.metric(
                    "Rejection Rate",
                    f"{success_rates.get('rejection_rate', 0):.1f}%"
                )
            
            # Weekly Performance Trends
            weekly_performance = data.get('weekly_performance', [])
            if weekly_performance:
                df = pd.DataFrame(weekly_performance)
                
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Interview Rate Trends', 'Success Rate Trends'),
                    vertical_spacing=0.1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df['week'],
                        y=df['interview_rate'],
                        mode='lines+markers',
                        name='Interview Rate',
                        line=dict(color='blue')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df['week'],
                        y=df['success_rate'],
                        mode='lines+markers',
                        name='Success Rate',
                        line=dict(color='green')
                    ),
                    row=2, col=1
                )
                
                fig.update_layout(height=600, title_text="Weekly Performance Trends")
                st.plotly_chart(fig, use_container_width=True)
            
            # Industry Performance
            industry_performance = data.get('industry_performance', {})
            if industry_performance:
                st.subheader("🏢 Performance by Industry")
                
                industries = list(industry_performance.keys())
                interview_rates = [industry_performance[ind]['interview_rate'] for ind in industries]
                success_rates = [industry_performance[ind]['success_rate'] for ind in industries]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Interview Rate',
                    x=industries,
                    y=interview_rates,
                    marker_color='lightblue'
                ))
                fig.add_trace(go.Bar(
                    name='Success Rate',
                    x=industries,
                    y=success_rates,
                    marker_color='lightgreen'
                ))
                
                fig.update_layout(
                    title="Performance by Industry",
                    barmode='group',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading success rates: {str(e)}")
    
    def _render_conversion_funnel_dashboard(self, timeframe: str):
        """Render conversion funnel analysis dashboard"""
        st.subheader("🔄 Conversion Funnel Analysis")
        
        try:
            days = {"30d": 30, "90d": 90, "180d": 180, "1y": 365}[timeframe]
            
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/api/v1/analytics/conversion-funnel",
                params={"days": days},
                headers=self.api_client._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                st.error(f"Failed to load conversion funnel: HTTP {response.status_code}")
                return
            
            data = response.json()
            
            # Funnel Visualization
            funnel_stages = data.get('funnel_stages', [])
            if funnel_stages:
                # Create funnel chart
                stages = [stage['stage'] for stage in funnel_stages]
                counts = [stage['count'] for stage in funnel_stages]
                conversion_rates = [stage['conversion_rate'] for stage in funnel_stages]
                
                fig = go.Figure(go.Funnel(
                    y=stages,
                    x=counts,
                    textinfo="value+percent initial+percent previous",
                    marker=dict(
                        color=["deepskyblue", "lightsalmon", "tan", "teal", "silver"],
                        line=dict(width=2, color="DarkSlateGrey")
                    ),
                    connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
                ))
                
                fig.update_layout(
                    title="Job Application Conversion Funnel",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Stage Details Table
                st.subheader("📊 Stage Details")
                
                df_stages = pd.DataFrame(funnel_stages)
                df_stages = df_stages[['stage', 'count', 'conversion_rate', 'stage_conversion_rate', 'average_duration_days']]
                df_stages.columns = ['Stage', 'Count', 'Overall Rate (%)', 'Stage Rate (%)', 'Avg Duration (days)']
                
                st.dataframe(df_stages, use_container_width=True)
            
            # Bottlenecks Analysis
            bottlenecks = data.get('bottlenecks', [])
            if bottlenecks:
                st.subheader("⚠️ Identified Bottlenecks")
                
                for bottleneck in bottlenecks:
                    st.warning(
                        f"**{bottleneck['stage']}**: {bottleneck['conversion_rate']:.1f}% conversion rate "
                        f"({bottleneck['improvement_potential']} improvement potential)"
                    )
            
            # Success Factors
            success_factors = data.get('success_factors', [])
            if success_factors:
                st.subheader("✅ Success Factors")
                for factor in success_factors:
                    st.success(f"• {factor}")
            
        except Exception as e:
            st.error(f"Error loading conversion funnel: {str(e)}")
    
    def _render_performance_benchmarks_dashboard(self, timeframe: str):
        """Render performance benchmarks dashboard"""
        st.subheader("🎯 Performance Benchmarks")
        
        try:
            days = {"30d": 30, "90d": 90, "180d": 180, "1y": 365}[timeframe]
            
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/api/v1/analytics/performance-benchmarks",
                params={"days": days},
                headers=self.api_client._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                st.error(f"Failed to load benchmarks: HTTP {response.status_code}")
                return
            
            data = response.json()
            
            # Overall Performance Score
            overall_score = data.get('overall_performance_score', 0)
            market_position = data.get('market_position', 'average').replace('_', ' ').title()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Overall Performance Score", f"{overall_score:.1f}/100")
            with col2:
                st.metric("Market Position", market_position)
            
            # Benchmarks Comparison
            benchmarks = data.get('benchmarks', [])
            if benchmarks:
                # Create comparison chart
                metrics = [b['metric'] for b in benchmarks]
                user_values = [b['user_value'] for b in benchmarks]
                market_averages = [b['market_average'] for b in benchmarks]
                percentile_ranks = [b['percentile_rank'] for b in benchmarks]
                
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Performance vs Market Average', 'Percentile Rankings'),
                    vertical_spacing=0.15
                )
                
                # Performance comparison
                fig.add_trace(
                    go.Bar(name='Your Performance', x=metrics, y=user_values, marker_color='lightblue'),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Bar(name='Market Average', x=metrics, y=market_averages, marker_color='orange'),
                    row=1, col=1
                )
                
                # Percentile rankings
                colors = ['green' if p >= 75 else 'orange' if p >= 50 else 'red' for p in percentile_ranks]
                fig.add_trace(
                    go.Bar(name='Percentile Rank', x=metrics, y=percentile_ranks, marker_color=colors),
                    row=2, col=1
                )
                
                fig.update_layout(height=700, title_text="Performance Benchmarks Analysis")
                fig.update_yaxes(title_text="Rate (%)", row=1, col=1)
                fig.update_yaxes(title_text="Percentile", row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed benchmarks table
                st.subheader("📊 Detailed Benchmarks")
                
                df_benchmarks = pd.DataFrame(benchmarks)
                df_benchmarks = df_benchmarks[['metric', 'user_value', 'market_average', 'percentile_rank', 'category']]
                df_benchmarks.columns = ['Metric', 'Your Value', 'Market Average', 'Percentile Rank', 'Category']
                
                # Color code the category column
                def color_category(val):
                    if val == 'excellent':
                        return 'background-color: lightgreen'
                    elif val == 'above_average':
                        return 'background-color: lightblue'
                    elif val == 'average':
                        return 'background-color: lightyellow'
                    else:
                        return 'background-color: lightcoral'
                
                styled_df = df_benchmarks.style.applymap(color_category, subset=['Category'])
                st.dataframe(styled_df, use_container_width=True)
            
            # Insights and Recommendations
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💡 Performance Insights")
                insights = data.get('insights', [])
                for insight in insights:
                    st.info(f"• {insight}")
            
            with col2:
                st.subheader("🎯 Recommendations")
                recommendations = data.get('recommendations', [])
                for rec in recommendations:
                    st.success(f"• {rec}")
            
        except Exception as e:
            st.error(f"Error loading performance benchmarks: {str(e)}")
    
    def _render_market_trends_dashboard(self, timeframe: str):
        """Render market trends dashboard"""
        st.subheader("📈 Market Trends Analysis")
        
        with st.spinner("Loading market analysis..."):
            market_data = self._get_market_analysis(timeframe)
        
        if "error" in market_data:
            st.error(f"Failed to load market analysis: {market_data['error']}")
            return
        
        # Market Summary
        summary = market_data.get('summary', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Jobs Analyzed", summary.get('total_jobs_analyzed', 0))
        
        with col2:
            st.metric("Market Growth", f"{summary.get('market_growth', 0):.1%}")
        
        with col3:
            st.metric("Avg Salary", f"${summary.get('avg_salary', 0):,}")
        
        with col4:
            st.metric("Active Alerts", summary.get('active_alerts', 0))
        
        # Salary Trends
        salary_trends = market_data.get('salary_trends', {})
        if salary_trends and 'chart_data' in salary_trends:
            st.subheader("💰 Salary Trends")
            
            chart_data = salary_trends['chart_data']
            
            # Monthly salary trends
            monthly_trend = chart_data.get('monthly_trend', [])
            if monthly_trend:
                df_monthly = pd.DataFrame(monthly_trend)
                
                fig = px.line(
                    df_monthly,
                    x='month',
                    y='salary',
                    title="Monthly Salary Trends",
                    labels={'salary': 'Average Salary ($)', 'month': 'Month'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Salary by location
            location_comparison = chart_data.get('location_comparison', [])
            if location_comparison:
                df_location = pd.DataFrame(location_comparison)
                
                fig = px.bar(
                    df_location,
                    x='location',
                    y='salary',
                    title="Average Salary by Location",
                    labels={'salary': 'Average Salary ($)', 'location': 'Location'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Job Market Patterns
        market_patterns = market_data.get('market_patterns', {})
        if market_patterns and 'chart_data' in market_patterns:
            st.subheader("📊 Job Market Patterns")
            
            chart_data = market_patterns['chart_data']
            
            # Jobs over time
            jobs_over_time = chart_data.get('jobs_over_time', [])
            if jobs_over_time:
                df_jobs = pd.DataFrame(jobs_over_time)
                
                fig = px.line(
                    df_jobs,
                    x='date',
                    y='count',
                    title="Job Postings Over Time",
                    labels={'count': 'Number of Jobs', 'date': 'Date'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Industry distribution
            industry_pie = chart_data.get('industry_pie', [])
            if industry_pie:
                df_industry = pd.DataFrame(industry_pie)
                
                fig = px.pie(
                    df_industry,
                    values='count',
                    names='industry',
                    title="Job Distribution by Industry"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Opportunity Alerts
        alerts = market_data.get('opportunity_alerts', [])
        if alerts:
            st.subheader("🚨 Market Opportunity Alerts")
            
            for alert in alerts:
                alert_type = alert.get('type', 'info')
                priority = alert.get('priority', 'medium')
                
                if priority == 'high':
                    st.error(f"**{alert['title']}**: {alert['message']}")
                elif priority == 'medium':
                    st.warning(f"**{alert['title']}**: {alert['message']}")
                else:
                    st.info(f"**{alert['title']}**: {alert['message']}")
                
                if 'action' in alert:
                    st.caption(f"💡 Action: {alert['action']}")
    
    def _export_analytics_report(self, timeframe: str):
        """Export analytics report as downloadable file"""
        try:
            # Get comprehensive analytics data
            analytics = self._get_comprehensive_analytics(timeframe)
            
            if "error" in analytics:
                st.error(f"Failed to export report: {analytics['error']}")
                return
            
            # Create report content
            report_content = {
                "report_generated": datetime.now().isoformat(),
                "timeframe": timeframe,
                "executive_summary": analytics.get('executive_summary', {}),
                "success_rates": analytics.get('success_rates', {}),
                "conversion_funnel": analytics.get('conversion_funnel', {}),
                "performance_benchmarks": analytics.get('performance_benchmarks', {}),
                "key_insights": analytics.get('key_insights', ''),
                "recommendations": analytics.get('top_recommendations', [])
            }
            
            # Convert to JSON
            report_json = json.dumps(report_content, indent=2)
            
            # Create download button
            st.download_button(
                label="📥 Download Analytics Report (JSON)",
                data=report_json,
                file_name=f"career_copilot_analytics_{timeframe}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
            
            # Also create a CSV summary
            summary_data = []
            exec_summary = analytics.get('executive_summary', {})
            
            for key, value in exec_summary.items():
                summary_data.append({
                    'Metric': key.replace('_', ' ').title(),
                    'Value': value
                })
            
            if summary_data:
                df_summary = pd.DataFrame(summary_data)
                csv = df_summary.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download Summary (CSV)",
                    data=csv,
                    file_name=f"career_copilot_summary_{timeframe}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            st.success("✅ Analytics report prepared for download!")
            
        except Exception as e:
            st.error(f"Failed to export report: {str(e)}")


def render_interactive_analytics_dashboard(api_client):
    """Main function to render the interactive analytics dashboard"""
    dashboard = InteractiveAnalyticsDashboard(api_client)
    dashboard.render_main_dashboard()