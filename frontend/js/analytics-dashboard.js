/**
 * Analytics Dashboard for Career Co-Pilot
 * Handles skill gap analysis, progress tracking, and recommendation visualization
 */

class AnalyticsDashboard {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.charts = {};
        this.skillGapData = null;
        this.progressData = null;
        this.recommendationData = null;
        
        // Chart.js configuration
        this.chartDefaults = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            }
        };
        
        this.init();
    }
    
    async init() {
        // Load Chart.js if not already loaded
        if (typeof Chart === 'undefined') {
            await this.loadChartJS();
        }
        
        // Load analytics data
        await this.loadAnalyticsData();
        
        // Initialize charts
        this.initializeCharts();
        
        console.log('Analytics Dashboard initialized');
    }
    
    async loadChartJS() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    async loadAnalyticsData() {
        try {
            // Load skill gap analysis
            this.skillGapData = await this.apiClient.getSkillGapAnalysis();
            
            // Load dashboard analytics
            this.progressData = await this.apiClient.getAnalyticsDashboard();
            
            // Load recommendations (if available)
            try {
                this.recommendationData = await this.apiClient.request('/recommendations');
            } catch (error) {
                console.warn('Recommendations not available:', error.message);
                this.recommendationData = null;
            }
            
        } catch (error) {
            console.warn('Analytics data not available, using mock data:', error.message);
            this.loadMockData();
        }
    }
    
    loadMockData() {
        // Mock skill gap data
        this.skillGapData = {
            user_skills: ['JavaScript', 'Python', 'React', 'HTML', 'CSS'],
            missing_skills: [
                { skill: 'TypeScript', frequency: 85, priority: 'high', market_demand: 92 },
                { skill: 'Node.js', frequency: 78, priority: 'high', market_demand: 88 },
                { skill: 'AWS', frequency: 72, priority: 'medium', market_demand: 95 },
                { skill: 'Docker', frequency: 65, priority: 'medium', market_demand: 82 },
                { skill: 'GraphQL', frequency: 45, priority: 'low', market_demand: 75 }
            ],
            skill_coverage: 0.65,
            market_insights: {
                jobs_analyzed: 150,
                top_market_skills: ['JavaScript', 'Python', 'TypeScript', 'React', 'AWS'],
                skill_diversity: 45
            }
        };
        
        // Mock progress data
        this.progressData = {
            total_applications: 25,
            applications_this_month: 8,
            response_rate: 0.24,
            interview_rate: 0.12,
            monthly_progress: [
                { month: 'Jan', applications: 5, responses: 1, interviews: 0 },
                { month: 'Feb', applications: 8, responses: 2, interviews: 1 },
                { month: 'Mar', applications: 12, responses: 3, interviews: 2 }
            ],
            status_distribution: {
                'not_applied': 45,
                'applied': 25,
                'phone_screen': 8,
                'interview_scheduled': 5,
                'interviewed': 3,
                'offer_received': 1,
                'rejected': 13
            }
        };
        
        // Mock recommendation data
        this.recommendationData = [
            {
                id: 1,
                title: 'Senior Frontend Developer',
                company: 'TechCorp',
                match_score: 0.92,
                reasons: ['Strong React skills', 'JavaScript expertise', 'Frontend focus'],
                missing_skills: ['TypeScript', 'Testing frameworks']
            },
            {
                id: 2,
                title: 'Full Stack Engineer',
                company: 'StartupXYZ',
                match_score: 0.85,
                reasons: ['Python experience', 'Full stack background'],
                missing_skills: ['AWS', 'Docker', 'Microservices']
            }
        ];
    }
    
    initializeCharts() {
        this.createSkillGapChart();
        this.createProgressChart();
        this.createStatusDistributionChart();
        this.createSkillCoverageChart();
        this.renderRecommendations();
    }
    
    createSkillGapChart() {
        const canvas = document.getElementById('skill-gap-chart');
        if (!canvas || !this.skillGapData) return;
        
        const ctx = canvas.getContext('2d');
        const skillGaps = this.skillGapData.missing_skills.slice(0, 8); // Top 8 gaps
        
        this.charts.skillGap = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: skillGaps.map(gap => gap.skill),
                datasets: [{
                    label: 'Market Demand (%)',
                    data: skillGaps.map(gap => gap.market_demand),
                    backgroundColor: skillGaps.map(gap => 
                        gap.priority === 'high' ? '#ef4444' :
                        gap.priority === 'medium' ? '#f59e0b' : '#10b981'
                    ),
                    borderColor: skillGaps.map(gap => 
                        gap.priority === 'high' ? '#dc2626' :
                        gap.priority === 'medium' ? '#d97706' : '#059669'
                    ),
                    borderWidth: 1
                }]
            },
            options: {
                ...this.chartDefaults,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Market Demand (%)'
                        }
                    }
                },
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Top Skill Gaps by Market Demand'
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const gap = skillGaps[context.dataIndex];
                                return [
                                    `Frequency: ${gap.frequency}%`,
                                    `Priority: ${gap.priority}`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }
    
    createProgressChart() {
        const canvas = document.getElementById('progress-chart');
        if (!canvas || !this.progressData) return;
        
        const ctx = canvas.getContext('2d');
        const monthlyData = this.progressData.monthly_progress;
        
        this.charts.progress = new Chart(ctx, {
            type: 'line',
            data: {
                labels: monthlyData.map(data => data.month),
                datasets: [
                    {
                        label: 'Applications',
                        data: monthlyData.map(data => data.applications),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Responses',
                        data: monthlyData.map(data => data.responses),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Interviews',
                        data: monthlyData.map(data => data.interviews),
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                ...this.chartDefaults,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    }
                },
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Application Progress Over Time'
                    }
                }
            }
        });
    }
    
    createStatusDistributionChart() {
        const canvas = document.getElementById('status-distribution-chart');
        if (!canvas || !this.progressData) return;
        
        const ctx = canvas.getContext('2d');
        const statusData = this.progressData.status_distribution;
        
        const colors = {
            'not_applied': '#6b7280',
            'applied': '#3b82f6',
            'phone_screen': '#8b5cf6',
            'interview_scheduled': '#f59e0b',
            'interviewed': '#10b981',
            'offer_received': '#059669',
            'rejected': '#ef4444'
        };
        
        this.charts.statusDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(statusData).map(status => 
                    status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
                ),
                datasets: [{
                    data: Object.values(statusData),
                    backgroundColor: Object.keys(statusData).map(status => colors[status]),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Application Status Distribution'
                    }
                }
            }
        });
    }
    
    createSkillCoverageChart() {
        const canvas = document.getElementById('skill-coverage-chart');
        if (!canvas || !this.skillGapData) return;
        
        const ctx = canvas.getContext('2d');
        const coverage = this.skillGapData.skill_coverage * 100;
        
        this.charts.skillCoverage = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Skills Covered', 'Skill Gaps'],
                datasets: [{
                    data: [coverage, 100 - coverage],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Overall Skill Coverage'
                    }
                }
            }
        });
    }
    
    renderRecommendations() {
        const container = document.getElementById('recommendations-container');
        if (!container || !this.recommendationData) return;
        
        container.innerHTML = '';
        
        this.recommendationData.forEach(recommendation => {
            const card = this.createRecommendationCard(recommendation);
            container.appendChild(card);
        });
    }
    
    createRecommendationCard(recommendation) {
        const card = document.createElement('div');
        card.className = 'bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700';
        
        const matchScore = Math.round(recommendation.match_score * 100);
        const scoreColor = matchScore >= 90 ? 'text-green-600' : 
                          matchScore >= 75 ? 'text-yellow-600' : 'text-red-600';
        
        card.innerHTML = `
            <div class="flex justify-between items-start mb-4">
                <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">${recommendation.title}</h3>
                    <p class="text-gray-600 dark:text-gray-400">${recommendation.company}</p>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-bold ${scoreColor}">${matchScore}%</div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">Match</div>
                </div>
            </div>
            
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Why this matches:</h4>
                <div class="flex flex-wrap gap-2">
                    ${recommendation.reasons.map(reason => 
                        `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">${reason}</span>`
                    ).join('')}
                </div>
            </div>
            
            ${recommendation.missing_skills && recommendation.missing_skills.length > 0 ? `
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Skills to develop:</h4>
                    <div class="flex flex-wrap gap-2">
                        ${recommendation.missing_skills.map(skill => 
                            `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">${skill}</span>`
                        ).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="flex gap-2">
                <button class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors" onclick="window.open('#', '_blank')">
                    View Job
                </button>
                <button class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" onclick="analytics.saveRecommendation(${recommendation.id})">
                    Save
                </button>
            </div>
        `;
        
        return card;
    }
    
    async saveRecommendation(recommendationId) {
        try {
            // This would save the recommendation as a job application
            const recommendation = this.recommendationData.find(r => r.id === recommendationId);
            if (!recommendation) return;
            
            const jobData = {
                company: recommendation.company,
                position: recommendation.title,
                status: 'wishlist',
                notes: `Recommended with ${Math.round(recommendation.match_score * 100)}% match`
            };
            
            await this.apiClient.createJob(jobData);
            ToastNotification.success('Recommendation saved to your job list!');
            
        } catch (error) {
            console.error('Failed to save recommendation:', error);
            ToastNotification.error('Failed to save recommendation');
        }
    }
    
    async refreshData() {
        await this.loadAnalyticsData();
        this.updateCharts();
        this.renderRecommendations();
    }
    
    updateCharts() {
        // Update skill gap chart
        if (this.charts.skillGap && this.skillGapData) {
            const skillGaps = this.skillGapData.missing_skills.slice(0, 8);
            this.charts.skillGap.data.labels = skillGaps.map(gap => gap.skill);
            this.charts.skillGap.data.datasets[0].data = skillGaps.map(gap => gap.market_demand);
            this.charts.skillGap.update();
        }
        
        // Update progress chart
        if (this.charts.progress && this.progressData) {
            const monthlyData = this.progressData.monthly_progress;
            this.charts.progress.data.labels = monthlyData.map(data => data.month);
            this.charts.progress.data.datasets[0].data = monthlyData.map(data => data.applications);
            this.charts.progress.data.datasets[1].data = monthlyData.map(data => data.responses);
            this.charts.progress.data.datasets[2].data = monthlyData.map(data => data.interviews);
            this.charts.progress.update();
        }
        
        // Update status distribution chart
        if (this.charts.statusDistribution && this.progressData) {
            this.charts.statusDistribution.data.datasets[0].data = Object.values(this.progressData.status_distribution);
            this.charts.statusDistribution.update();
        }
        
        // Update skill coverage chart
        if (this.charts.skillCoverage && this.skillGapData) {
            const coverage = this.skillGapData.skill_coverage * 100;
            this.charts.skillCoverage.data.datasets[0].data = [coverage, 100 - coverage];
            this.charts.skillCoverage.update();
        }
    }
    
    destroy() {
        // Destroy all charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Export for use in other modules
window.AnalyticsDashboard = AnalyticsDashboard;