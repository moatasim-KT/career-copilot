/**
 * Responsive Dashboard JavaScript for Career Co-Pilot
 * Handles mobile/desktop responsive behavior and basic interactions
 */

class ResponsiveDashboard {
    constructor() {
        this.currentView = 'list'; // 'list' or 'grid'
        this.isMobile = window.innerWidth < 768;
        this.isTablet = window.innerWidth >= 768 && window.innerWidth < 1024;
        this.isDesktop = window.innerWidth >= 1024;
        
        this.jobs = []; // Will be populated from API
        this.filteredJobs = [];
        this.currentPage = 1;
        this.jobsPerPage = 10;
        
        this.filters = {
            search: '',
            status: '',
            location: '',
            company: '',
            source: ''
        };

        // Initialize API client
        this.apiClient = new APIClient();
        
        // Real-time update interval
        this.updateInterval = null;
        this.updateIntervalMs = 30000; // 30 seconds
        
        // WebSocket client for real-time updates (optional)
        this.wsClient = null;
        this.useWebSocket = true; // Can be configured
        
        // Analytics and profile managers
        this.analyticsDashboard = null;
        this.profileManager = null;
        
        // Current active section
        this.activeSection = 'jobs';
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupResponsiveHandlers();
        this.setupThemeToggle();
        this.setupMobileMenu();
        this.setupFilters();
        this.setupModals();
        this.setupViewToggle();
        this.setupNavigation();
        this.detectOfflineStatus();
        this.setupRealTimeUpdates();
        
        // Initialize analytics and profile managers
        this.initializeManagers();
        
        // Load initial data from API
        this.loadJobs();
        
        console.log('Career Co-Pilot Dashboard initialized');
    }
    
    setupEventListeners() {
        // Window resize handler
        window.addEventListener('resize', this.debounce(() => {
            this.handleResize();
        }, 250));
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });
        
        // Click outside to close dropdowns
        document.addEventListener('click', (e) => {
            this.handleClickOutside(e);
        });
    }
    
    setupResponsiveHandlers() {
        this.handleResize();
    }
    
    handleResize() {
        const oldIsMobile = this.isMobile;
        const oldIsTablet = this.isTablet;
        const oldIsDesktop = this.isDesktop;
        
        this.isMobile = window.innerWidth < 768;
        this.isTablet = window.innerWidth >= 768 && window.innerWidth < 1024;
        this.isDesktop = window.innerWidth >= 1024;
        
        // Handle responsive changes
        if (oldIsMobile !== this.isMobile) {
            this.handleMobileToggle();
        }
        
        // Adjust grid layout based on screen size
        this.adjustGridLayout();
        
        // Update jobs per page based on screen size
        this.updateJobsPerPage();
    }
    
    handleMobileToggle() {
        const mobileMenu = document.getElementById('mobile-menu');
        if (this.isMobile) {
            // Mobile-specific adjustments
            this.jobsPerPage = 5;
        } else {
            // Desktop-specific adjustments
            this.jobsPerPage = 10;
            if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                mobileMenu.classList.add('hidden');
            }
        }
        this.renderJobs();
    }
    
    adjustGridLayout() {
        const jobsContainer = document.getElementById('jobs-container');
        if (!jobsContainer) return;
        
        if (this.currentView === 'grid') {
            if (this.isMobile) {
                jobsContainer.className = 'grid grid-cols-1 gap-4';
            } else if (this.isTablet) {
                jobsContainer.className = 'grid grid-cols-2 gap-4';
            } else {
                jobsContainer.className = 'grid grid-cols-3 gap-4';
            }
        } else {
            jobsContainer.className = 'space-y-4';
        }
    }
    
    updateJobsPerPage() {
        if (this.isMobile) {
            this.jobsPerPage = 5;
        } else if (this.isTablet) {
            this.jobsPerPage = 8;
        } else {
            this.jobsPerPage = 10;
        }
    }
    
    setupThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        if (!themeToggle) return;
        
        // Check for saved theme preference or default to light mode
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.setTheme(newTheme);
        });
    }
    
    setTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem('theme', theme);
    }
    
    setupMobileMenu() {
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        
        if (!mobileMenuButton || !mobileMenu) return;
        
        mobileMenuButton.addEventListener('click', () => {
            const isHidden = mobileMenu.classList.contains('hidden');
            if (isHidden) {
                mobileMenu.classList.remove('hidden');
                mobileMenuButton.setAttribute('aria-expanded', 'true');
            } else {
                mobileMenu.classList.add('hidden');
                mobileMenuButton.setAttribute('aria-expanded', 'false');
            }
        });
    }
    
    setupFilters() {
        const filterToggleBtn = document.getElementById('filter-toggle-btn');
        const filtersPanel = document.getElementById('filters-panel');
        const applyFiltersBtn = document.getElementById('apply-filters-btn');
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        
        if (filterToggleBtn && filtersPanel) {
            filterToggleBtn.addEventListener('click', () => {
                const isHidden = filtersPanel.classList.contains('hidden');
                if (isHidden) {
                    filtersPanel.classList.remove('hidden');
                    filtersPanel.classList.add('filter-slide-in');
                } else {
                    filtersPanel.classList.add('hidden');
                }
            });
        }
        
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => {
                this.applyFilters();
            });
        }
        
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }
        
        // Setup filter inputs
        const filterInputs = [
            'search-input',
            'status-filter',
            'location-filter',
            'company-filter',
            'source-filter'
        ];
        
        filterInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', this.debounce(() => {
                    this.updateFilters();
                }, 300));
            }
        });
    }
    
    setupModals() {
        const addJobBtn = document.getElementById('add-job-btn');
        const emptyAddJobBtn = document.getElementById('empty-add-job-btn');
        const addJobModal = document.getElementById('add-job-modal');
        const cancelJobBtn = document.getElementById('cancel-job-btn');
        const saveJobBtn = document.getElementById('save-job-btn');
        
        if (addJobBtn && addJobModal) {
            addJobBtn.addEventListener('click', () => {
                this.showAddJobModal();
            });
        }
        
        if (emptyAddJobBtn && addJobModal) {
            emptyAddJobBtn.addEventListener('click', () => {
                this.showAddJobModal();
            });
        }
        
        if (cancelJobBtn && addJobModal) {
            cancelJobBtn.addEventListener('click', () => {
                this.hideAddJobModal();
            });
        }
        
        if (saveJobBtn) {
            saveJobBtn.addEventListener('click', () => {
                this.saveJob();
            });
        }
        
        // Close modal on backdrop click
        if (addJobModal) {
            addJobModal.addEventListener('click', (e) => {
                if (e.target === addJobModal) {
                    this.hideAddJobModal();
                }
            });
        }
    }
    
    setupViewToggle() {
        const listViewBtn = document.getElementById('list-view-btn');
        const gridViewBtn = document.getElementById('grid-view-btn');
        
        if (listViewBtn) {
            listViewBtn.addEventListener('click', () => {
                this.setView('list');
            });
        }
        
        if (gridViewBtn) {
            gridViewBtn.addEventListener('click', () => {
                this.setView('grid');
            });
        }
    }
    
    setupNavigation() {
        // Desktop navigation
        const navLinks = document.querySelectorAll('nav a[href^="#"]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });
        
        // Mobile navigation
        const mobileNavLinks = document.querySelectorAll('#mobile-menu a[href^="#"]');
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('href').substring(1);
                this.showSection(section);
                
                // Close mobile menu
                const mobileMenu = document.getElementById('mobile-menu');
                if (mobileMenu) {
                    mobileMenu.classList.add('hidden');
                }
            });
        });
    }
    
    showSection(sectionName) {
        // Hide all sections
        const sections = ['dashboard', 'jobs', 'analytics', 'profile'];
        sections.forEach(section => {
            const element = document.getElementById(`${section}-section`);
            if (element) {
                element.classList.add('hidden');
            }
        });
        
        // Show jobs section for dashboard
        if (sectionName === 'dashboard') {
            sectionName = 'jobs';
        }
        
        // Show requested section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            this.activeSection = sectionName;
        }
        
        // Update navigation active states
        this.updateNavigationState(sectionName);
        
        // Initialize section-specific functionality
        if (sectionName === 'analytics' && this.analyticsDashboard) {
            this.analyticsDashboard.refreshData();
        }
    }
    
    updateNavigationState(activeSection) {
        // Update desktop navigation
        const navLinks = document.querySelectorAll('nav a[href^="#"]');
        navLinks.forEach(link => {
            const section = link.getAttribute('href').substring(1);
            if (section === activeSection || (section === 'dashboard' && activeSection === 'jobs')) {
                link.classList.remove('text-gray-500', 'dark:text-gray-400');
                link.classList.add('text-gray-900', 'dark:text-white');
            } else {
                link.classList.remove('text-gray-900', 'dark:text-white');
                link.classList.add('text-gray-500', 'dark:text-gray-400');
            }
        });
        
        // Update mobile navigation
        const mobileNavLinks = document.querySelectorAll('#mobile-menu a[href^="#"]');
        mobileNavLinks.forEach(link => {
            const section = link.getAttribute('href').substring(1);
            if (section === activeSection || (section === 'dashboard' && activeSection === 'jobs')) {
                link.classList.remove('text-gray-500', 'dark:text-gray-400');
                link.classList.add('text-gray-900', 'dark:text-white');
            } else {
                link.classList.remove('text-gray-900', 'dark:text-white');
                link.classList.add('text-gray-500', 'dark:text-gray-400');
            }
        });
    }
    
    async initializeManagers() {
        try {
            // Initialize analytics dashboard
            this.analyticsDashboard = new AnalyticsDashboard(this.apiClient);
            
            // Initialize profile manager
            this.profileManager = new ProfileManager(this.apiClient);
            
            // Make managers globally available
            window.analytics = this.analyticsDashboard;
            window.profileManager = this.profileManager;
            
        } catch (error) {
            console.warn('Failed to initialize managers:', error.message);
        }
    }
    
    setView(view) {
        this.currentView = view;
        
        const listViewBtn = document.getElementById('list-view-btn');
        const gridViewBtn = document.getElementById('grid-view-btn');
        
        if (listViewBtn && gridViewBtn) {
            if (view === 'list') {
                listViewBtn.classList.add('bg-white', 'dark:bg-gray-800');
                listViewBtn.classList.remove('bg-gray-50', 'dark:bg-gray-700');
                gridViewBtn.classList.add('bg-gray-50', 'dark:bg-gray-700');
                gridViewBtn.classList.remove('bg-white', 'dark:bg-gray-800');
            } else {
                gridViewBtn.classList.add('bg-white', 'dark:bg-gray-800');
                gridViewBtn.classList.remove('bg-gray-50', 'dark:bg-gray-700');
                listViewBtn.classList.add('bg-gray-50', 'dark:bg-gray-700');
                listViewBtn.classList.remove('bg-white', 'dark:bg-gray-800');
            }
        }
        
        this.adjustGridLayout();
        this.renderJobs();
    }
    
    detectOfflineStatus() {
        const offlineIndicator = document.getElementById('offline-indicator');
        
        const updateOnlineStatus = () => {
            if (navigator.onLine) {
                if (offlineIndicator) {
                    offlineIndicator.classList.add('hidden');
                }
            } else {
                if (offlineIndicator) {
                    offlineIndicator.classList.remove('hidden');
                }
            }
        };
        
        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        
        // Initial check
        updateOnlineStatus();
    }
    
    async loadJobs() {
        try {
            this.showLoadingState();
            
            // Get jobs from API with current filters
            const filters = {
                status: this.filters.status || undefined,
                company: this.filters.company || undefined,
                skip: (this.currentPage - 1) * this.jobsPerPage,
                limit: this.jobsPerPage
            };

            const jobs = await this.apiClient.getJobs(filters);
            
            // Transform API data to match frontend format
            this.jobs = jobs.map(job => this.transformJobData(job));
            this.filteredJobs = [...this.jobs];
            
            this.hideLoadingState();
            this.renderJobs();
            await this.updateStats();
            
        } catch (error) {
            this.hideLoadingState();
            this.handleError('Failed to load jobs', error);
            
            // Fallback to sample data if API fails
            if (this.jobs.length === 0) {
                this.jobs = this.generateSampleJobs();
                this.filteredJobs = [...this.jobs];
                this.renderJobs();
                this.updateStats();
            }
        }
    }
    
    generateSampleJobs() {
        // Sample job data for demonstration
        return [
            {
                id: 1,
                title: 'Senior Frontend Developer',
                company: 'TechCorp Inc',
                location: 'San Francisco, CA',
                salary_min: 120000,
                salary_max: 160000,
                status: 'not_applied',
                source: 'scraped',
                date_posted: '2025-01-15',
                tech_stack: ['React', 'TypeScript', 'Node.js'],
                application_url: 'https://example.com/job/1',
                recommendation_score: 0.85,
                description: 'We are looking for a senior frontend developer to join our team...'
            },
            {
                id: 2,
                title: 'Full Stack Engineer',
                company: 'StartupXYZ',
                location: 'Remote',
                salary_min: 100000,
                salary_max: 140000,
                status: 'applied',
                source: 'manual',
                date_posted: '2025-01-14',
                date_applied: '2025-01-16',
                tech_stack: ['Python', 'Django', 'React'],
                application_url: 'https://example.com/job/2',
                recommendation_score: 0.92,
                description: 'Join our fast-growing startup as a full stack engineer...'
            },
            {
                id: 3,
                title: 'Software Engineer',
                company: 'BigTech Corp',
                location: 'Seattle, WA',
                salary_min: 140000,
                salary_max: 180000,
                status: 'phone_screen',
                source: 'api',
                date_posted: '2025-01-13',
                date_applied: '2025-01-15',
                tech_stack: ['Java', 'Spring', 'AWS'],
                recommendation_score: 0.78,
                description: 'We are seeking a talented software engineer...'
            }
        ];
    }
    
    showLoadingState() {
        const loadingState = document.getElementById('loading-state');
        const emptyState = document.getElementById('empty-state');
        const jobsContainer = document.getElementById('jobs-container');
        
        if (loadingState) loadingState.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        if (jobsContainer) jobsContainer.innerHTML = '';
    }
    
    hideLoadingState() {
        const loadingState = document.getElementById('loading-state');
        if (loadingState) loadingState.classList.add('hidden');
    }
    
    renderJobs() {
        const jobsContainer = document.getElementById('jobs-container');
        const emptyState = document.getElementById('empty-state');
        const jobsCountDisplay = document.getElementById('jobs-count-display');
        
        if (!jobsContainer) return;
        
        // Clear container
        jobsContainer.innerHTML = '';
        
        // Update jobs count
        if (jobsCountDisplay) {
            const count = this.filteredJobs.length;
            jobsCountDisplay.textContent = `${count} job${count !== 1 ? 's' : ''}`;
        }
        
        if (this.filteredJobs.length === 0) {
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }
        
        if (emptyState) emptyState.classList.add('hidden');
        
        // Calculate pagination
        const startIndex = (this.currentPage - 1) * this.jobsPerPage;
        const endIndex = startIndex + this.jobsPerPage;
        const jobsToShow = this.filteredJobs.slice(startIndex, endIndex);
        
        // Render jobs
        jobsToShow.forEach(job => {
            const jobElement = this.createJobCard(job);
            jobsContainer.appendChild(jobElement);
        });
        
        // Update pagination
        this.updatePagination();
        
        // Adjust layout
        this.adjustGridLayout();
    }
    
    createJobCard(job) {
        const templateId = this.currentView === 'grid' ? 'job-card-grid-template' : 'job-card-template';
        const template = document.getElementById(templateId);
        
        if (!template) {
            // Fallback to creating card manually
            return this.createJobCardManually(job);
        }
        
        const jobCard = template.content.cloneNode(true);
        const cardElement = jobCard.querySelector('.job-card, .job-card-grid');
        
        if (!cardElement) return this.createJobCardManually(job);
        
        // Set job ID
        cardElement.setAttribute('data-job-id', job.id);
        
        // Populate job data
        this.populateJobCard(jobCard, job);
        
        // Setup event listeners
        this.setupJobCardEvents(jobCard, job);
        
        return jobCard;
    }
    
    createJobCardManually(job) {
        // Fallback manual job card creation
        const jobCard = document.createElement('div');
        jobCard.className = 'job-card bg-white dark:bg-gray-800 shadow rounded-lg p-6 job-card-hover fade-in';
        jobCard.setAttribute('data-job-id', job.id);
        
        jobCard.innerHTML = `
            <div class="flex justify-between items-start mb-4">
                <div class="flex-1 min-w-0">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate">${job.title}</h3>
                    <p class="text-gray-600 dark:text-gray-400 font-medium truncate">${job.company}</p>
                </div>
                <div class="flex gap-2 ml-4">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${this.getStatusBadgeClass(job.status)}">
                        ${this.getStatusLabel(job.status)}
                    </span>
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium ${this.getSourceBadgeClass(job.source)}">
                        ${this.getSourceLabel(job.source)}
                    </span>
                </div>
            </div>
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-4">
                ${job.location ? `<div class="flex items-center"><svg class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg><span>${job.location}</span></div>` : ''}
                ${job.salary_min || job.salary_max ? `<div class="flex items-center"><svg class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2" /></svg><span>${this.formatSalary(job.salary_min, job.salary_max)}</span></div>` : ''}
                <div class="flex items-center"><svg class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg><span>Posted ${this.formatDate(job.date_posted)}</span></div>
            </div>
            <div class="flex gap-2">
                <button class="job-view-btn touch-friendly inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                    View Details
                </button>
                ${job.application_url ? `<button class="job-apply-btn touch-friendly inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">Apply</button>` : ''}
                ${job.status === 'not_applied' ? `<button class="job-mark-applied-btn touch-friendly inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">Mark Applied</button>` : ''}
            </div>
        `;
        
        // Setup event listeners
        this.setupJobCardEventsManual(jobCard, job);
        
        return jobCard;
    }
    
    populateJobCard(jobCard, job) {
        // Populate job title and company
        const titleElement = jobCard.querySelector('.job-title');
        const companyElement = jobCard.querySelector('.job-company');
        
        if (titleElement) titleElement.textContent = job.title;
        if (companyElement) companyElement.textContent = job.company;
        
        // Populate location
        const locationElement = jobCard.querySelector('.job-location');
        const locationTextElement = jobCard.querySelector('.job-location-text');
        if (job.location && locationTextElement) {
            locationTextElement.textContent = job.location;
            if (locationElement) locationElement.classList.remove('hidden');
        } else if (locationElement) {
            locationElement.classList.add('hidden');
        }
        
        // Populate salary
        const salaryElement = jobCard.querySelector('.job-salary');
        const salaryTextElement = jobCard.querySelector('.job-salary-text');
        if ((job.salary_min || job.salary_max) && salaryTextElement) {
            salaryTextElement.textContent = this.formatSalary(job.salary_min, job.salary_max);
            if (salaryElement) salaryElement.classList.remove('hidden');
        } else if (salaryElement) {
            salaryElement.classList.add('hidden');
        }
        
        // Populate dates
        const datePostedElement = jobCard.querySelector('.job-date-posted-text');
        if (datePostedElement && job.date_posted) {
            datePostedElement.textContent = `Posted ${this.formatDate(job.date_posted)}`;
        }
        
        const dateAppliedElement = jobCard.querySelector('.job-date-applied');
        const dateAppliedTextElement = jobCard.querySelector('.job-date-applied-text');
        if (job.date_applied && dateAppliedTextElement) {
            dateAppliedTextElement.textContent = `Applied ${this.formatDate(job.date_applied)}`;
            if (dateAppliedElement) dateAppliedElement.classList.remove('hidden');
        }
        
        // Populate status badge
        const statusBadge = jobCard.querySelector('.job-status-badge');
        if (statusBadge) {
            statusBadge.textContent = this.getStatusLabel(job.status);
            statusBadge.className = `job-status-badge inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${this.getStatusBadgeClass(job.status)}`;
        }
        
        // Populate source badge
        const sourceBadge = jobCard.querySelector('.job-source-badge');
        if (sourceBadge) {
            sourceBadge.textContent = this.getSourceLabel(job.source);
            sourceBadge.className = `job-source-badge inline-flex items-center px-2 py-1 rounded text-xs font-medium ${this.getSourceBadgeClass(job.source)}`;
        }
        
        // Populate recommendation score
        if (job.recommendation_score) {
            const scoreElement = jobCard.querySelector('.job-recommendation-score');
            const scoreBar = jobCard.querySelector('.job-score-bar');
            const scoreText = jobCard.querySelector('.job-score-text');
            
            if (scoreElement) scoreElement.classList.remove('hidden');
            if (scoreBar) scoreBar.style.width = `${job.recommendation_score * 100}%`;
            if (scoreText) scoreText.textContent = `${Math.round(job.recommendation_score * 100)}%`;
        }
        
        // Show/hide action buttons based on job status and URL
        const applyBtn = jobCard.querySelector('.job-apply-btn');
        const markAppliedBtn = jobCard.querySelector('.job-mark-applied-btn');
        
        if (job.application_url && applyBtn) {
            applyBtn.classList.remove('hidden');
        }
        
        if (job.status === 'not_applied' && markAppliedBtn) {
            markAppliedBtn.classList.remove('hidden');
        }
    }
    
    setupJobCardEvents(jobCard, job) {
        // View details button
        const viewBtn = jobCard.querySelector('.job-view-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', () => {
                this.viewJobDetails(job);
            });
        }
        
        // Apply button
        const applyBtn = jobCard.querySelector('.job-apply-btn');
        if (applyBtn && job.application_url) {
            applyBtn.addEventListener('click', () => {
                window.open(job.application_url, '_blank');
            });
        }
        
        // Mark applied button
        const markAppliedBtn = jobCard.querySelector('.job-mark-applied-btn');
        if (markAppliedBtn) {
            markAppliedBtn.addEventListener('click', () => {
                this.updateJobStatus(job.id, 'applied');
            });
        }
        
        // Menu button
        const menuBtn = jobCard.querySelector('.job-menu-btn');
        const menu = jobCard.querySelector('.job-menu');
        if (menuBtn && menu) {
            menuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                menu.classList.toggle('hidden');
            });
        }
        
        // Status update buttons
        const statusBtns = jobCard.querySelectorAll('.job-status-btn');
        statusBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const newStatus = btn.getAttribute('data-status');
                this.updateJobStatus(job.id, newStatus);
                if (menu) menu.classList.add('hidden');
            });
        });
        
        // Delete button
        const deleteBtn = jobCard.querySelector('.job-delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.deleteJob(job.id);
            });
        }
    }
    
    setupJobCardEventsManual(jobCard, job) {
        // Similar to setupJobCardEvents but for manually created cards
        const viewBtn = jobCard.querySelector('.job-view-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', () => {
                this.viewJobDetails(job);
            });
        }
        
        const applyBtn = jobCard.querySelector('.job-apply-btn');
        if (applyBtn && job.application_url) {
            applyBtn.addEventListener('click', () => {
                window.open(job.application_url, '_blank');
            });
        }
        
        const markAppliedBtn = jobCard.querySelector('.job-mark-applied-btn');
        if (markAppliedBtn) {
            markAppliedBtn.addEventListener('click', () => {
                this.updateJobStatus(job.id, 'applied');
            });
        }
    }
    
    /**
     * Update statistics from API or local data
     */
    async updateStats() {
        try {
            // Try to get stats from API first
            const apiStats = await this.apiClient.getStatistics();
            
            if (apiStats) {
                this.updateStatsFromAPI(apiStats);
            } else {
                this.updateStatsFromLocal();
            }
            
        } catch (error) {
            console.warn('Failed to get API stats, using local data:', error.message);
            this.updateStatsFromLocal();
        }
    }
    
    /**
     * Update stats from API response
     */
    updateStatsFromAPI(apiStats) {
        const totalJobsCount = document.getElementById('total-jobs-count');
        const appliedJobsCount = document.getElementById('applied-jobs-count');
        const inProgressJobsCount = document.getElementById('in-progress-jobs-count');
        const responseRate = document.getElementById('response-rate');
        
        if (totalJobsCount) totalJobsCount.textContent = apiStats.total || 0;
        
        // Map API status counts to frontend display
        const statusCounts = apiStats.by_status || {};
        const applied = (statusCounts.applied || 0) + (statusCounts.screening || 0);
        const inProgress = (statusCounts.interview || 0) + (statusCounts.offer || 0);
        
        if (appliedJobsCount) appliedJobsCount.textContent = applied;
        if (inProgressJobsCount) inProgressJobsCount.textContent = inProgress;
        if (responseRate) responseRate.textContent = `${Math.round(apiStats.response_rate * 100) || 0}%`;
    }
    
    /**
     * Update stats from local job data (fallback)
     */
    updateStatsFromLocal() {
        const totalJobsCount = document.getElementById('total-jobs-count');
        const appliedJobsCount = document.getElementById('applied-jobs-count');
        const inProgressJobsCount = document.getElementById('in-progress-jobs-count');
        const responseRate = document.getElementById('response-rate');
        
        const total = this.jobs.length;
        const applied = this.jobs.filter(job => job.status === 'applied').length;
        const inProgress = this.jobs.filter(job => 
            ['phone_screen', 'interview_scheduled', 'interviewed'].includes(job.status)
        ).length;
        const responses = this.jobs.filter(job => 
            ['phone_screen', 'interview_scheduled', 'interviewed', 'offer_received'].includes(job.status)
        ).length;
        
        const rate = applied > 0 ? Math.round((responses / applied) * 100) : 0;
        
        if (totalJobsCount) totalJobsCount.textContent = total;
        if (appliedJobsCount) appliedJobsCount.textContent = applied;
        if (inProgressJobsCount) inProgressJobsCount.textContent = inProgress;
        if (responseRate) responseRate.textContent = `${rate}%`;
    }

    /**
     * Setup real-time updates
     */
    setupRealTimeUpdates() {
        // Try WebSocket first, fallback to polling
        if (this.useWebSocket && window.WebSocketClient) {
            this.wsClient = new WebSocketClient(this);
            this.wsClient.connect();
        } else {
            // Fallback to periodic updates
            this.startRealTimeUpdates();
        }
        
        // Handle online/offline events
        window.addEventListener('online', () => {
            if (this.wsClient) {
                this.wsClient.connect();
            } else {
                this.startRealTimeUpdates();
            }
            this.loadJobs(); // Refresh data when coming back online
        });
        
        window.addEventListener('offline', () => {
            if (this.wsClient) {
                this.wsClient.disconnect();
            } else {
                this.stopRealTimeUpdates();
            }
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (this.wsClient) {
                    this.wsClient.disconnect();
                } else {
                    this.stopRealTimeUpdates();
                }
            } else {
                if (this.wsClient) {
                    this.wsClient.connect();
                } else {
                    this.startRealTimeUpdates();
                }
            }
        });
    }
    
    /**
     * Start real-time updates
     */
    startRealTimeUpdates() {
        if (this.updateInterval || !navigator.onLine) {
            return;
        }
        
        this.updateInterval = setInterval(async () => {
            try {
                // Only update if page is visible and online
                if (!document.hidden && navigator.onLine) {
                    await this.refreshData();
                }
            } catch (error) {
                console.warn('Real-time update failed:', error.message);
            }
        }, this.updateIntervalMs);
    }
    
    /**
     * Stop real-time updates
     */
    stopRealTimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    /**
     * Refresh data without showing loading state
     */
    async refreshData() {
        try {
            const filters = {
                status: this.filters.status || undefined,
                company: this.filters.company || undefined,
                skip: (this.currentPage - 1) * this.jobsPerPage,
                limit: this.jobsPerPage
            };

            const jobs = await this.apiClient.getJobs(filters);
            const transformedJobs = jobs.map(job => this.transformJobData(job));
            
            // Only update if data has changed
            if (JSON.stringify(transformedJobs) !== JSON.stringify(this.jobs)) {
                this.jobs = transformedJobs;
                this.filteredJobs = [...this.jobs];
                this.renderJobs();
                await this.updateStats();
            }
            
        } catch (error) {
            // Silently fail for background updates
            console.warn('Background refresh failed:', error.message);
        }
    }

    /**
     * Handle errors with user-friendly messages
     */
    handleError(message, error) {
        console.error(message, error);
        
        let userMessage = message;
        
        if (error instanceof APIError) {
            if (error.status === 404) {
                userMessage = 'The requested resource was not found';
            } else if (error.status === 403) {
                userMessage = 'You do not have permission to perform this action';
            } else if (error.status === 429) {
                userMessage = 'Too many requests. Please try again later';
            } else if (error.status >= 500) {
                userMessage = 'Server error. Please try again later';
            } else {
                userMessage = error.message || message;
            }
        } else if (!navigator.onLine) {
            userMessage = 'You are offline. Please check your internet connection';
        }
        
        ToastNotification.error(userMessage);
    }

    /**
     * Validate URL format
     */
    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }
    
    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    formatSalary(min, max) {
        if (min && max) {
            return `$${this.formatNumber(min)} - $${this.formatNumber(max)}`;
        } else if (min) {
            return `$${this.formatNumber(min)}+`;
        } else if (max) {
            return `Up to $${this.formatNumber(max)}`;
        }
        return '';
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return 'yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else if (diffDays < 30) {
            const weeks = Math.floor(diffDays / 7);
            return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    getStatusLabel(status) {
        const labels = {
            'not_applied': 'Not Applied',
            'applied': 'Applied',
            'phone_screen': 'Phone Screen',
            'interview_scheduled': 'Interview Scheduled',
            'interviewed': 'Interviewed',
            'offer_received': 'Offer Received',
            'rejected': 'Rejected'
        };
        return labels[status] || status;
    }
    
    getStatusBadgeClass(status) {
        const classes = {
            'not_applied': 'status-badge-not-applied',
            'applied': 'status-badge-applied',
            'phone_screen': 'status-badge-phone-screen',
            'interview_scheduled': 'status-badge-interview-scheduled',
            'interviewed': 'status-badge-interviewed',
            'offer_received': 'status-badge-offer-received',
            'rejected': 'status-badge-rejected'
        };
        return classes[status] || 'status-badge-not-applied';
    }
    
    getSourceLabel(source) {
        const labels = {
            'manual': 'Manual',
            'scraped': 'Scraped',
            'api': 'API',
            'rss': 'RSS',
            'referral': 'Referral'
        };
        return labels[source] || source;
    }
    
    getSourceBadgeClass(source) {
        const classes = {
            'manual': 'source-badge-manual',
            'scraped': 'source-badge-scraped',
            'api': 'source-badge-api',
            'rss': 'source-badge-rss',
            'referral': 'source-badge-referral'
        };
        return classes[source] || 'source-badge-manual';
    }
    
    /**
     * Transform API job data to frontend format
     */
    transformJobData(apiJob) {
        return {
            id: apiJob.id,
            title: apiJob.position,
            company: apiJob.company,
            location: apiJob.location,
            salary_min: apiJob.salary_min,
            salary_max: apiJob.salary_max,
            status: this.mapApiStatusToFrontend(apiJob.status),
            source: 'api', // All jobs from API
            date_posted: apiJob.created_at,
            date_applied: apiJob.applied_date,
            tech_stack: [], // Not available in current API
            application_url: apiJob.job_url,
            recommendation_score: 0.8, // Default score
            description: apiJob.description || '',
            notes: apiJob.notes || '',
            work_location: apiJob.work_location,
            job_type: apiJob.job_type
        };
    }

    /**
     * Map API status to frontend status
     */
    mapApiStatusToFrontend(apiStatus) {
        const statusMap = {
            'wishlist': 'not_applied',
            'applied': 'applied',
            'screening': 'phone_screen',
            'interview': 'interview_scheduled',
            'offer': 'offer_received',
            'accepted': 'offer_received',
            'rejected': 'rejected',
            'withdrawn': 'rejected'
        };
        return statusMap[apiStatus] || 'not_applied';
    }

    /**
     * Map frontend status to API status
     */
    mapFrontendStatusToApi(frontendStatus) {
        const statusMap = {
            'not_applied': 'wishlist',
            'applied': 'applied',
            'phone_screen': 'screening',
            'interview_scheduled': 'interview',
            'interviewed': 'interview',
            'offer_received': 'offer',
            'rejected': 'rejected'
        };
        return statusMap[frontendStatus] || 'wishlist';
    }

    /**
     * Apply filters to job list
     */
    async applyFilters() {
        try {
            // Update filters from form inputs
            this.updateFiltersFromInputs();
            
            // Reset to first page
            this.currentPage = 1;
            
            // Reload jobs with new filters
            await this.loadJobs();
            
            // Hide filters panel on mobile
            if (this.isMobile) {
                const filtersPanel = document.getElementById('filters-panel');
                if (filtersPanel) {
                    filtersPanel.classList.add('hidden');
                }
            }
            
            ToastNotification.success('Filters applied successfully');
            
        } catch (error) {
            this.handleError('Failed to apply filters', error);
        }
    }
    
    /**
     * Clear all filters
     */
    async clearFilters() {
        try {
            // Reset filter values
            this.filters = {
                search: '',
                status: '',
                location: '',
                company: '',
                source: ''
            };
            
            // Clear form inputs
            const filterInputs = [
                'search-input',
                'status-filter',
                'location-filter',
                'company-filter',
                'source-filter'
            ];
            
            filterInputs.forEach(inputId => {
                const input = document.getElementById(inputId);
                if (input) {
                    input.value = '';
                }
            });
            
            // Reset to first page
            this.currentPage = 1;
            
            // Reload jobs
            await this.loadJobs();
            
            ToastNotification.success('Filters cleared');
            
        } catch (error) {
            this.handleError('Failed to clear filters', error);
        }
    }
    
    /**
     * Update filters from form inputs (for real-time filtering)
     */
    updateFiltersFromInputs() {
        const searchInput = document.getElementById('search-input');
        const statusFilter = document.getElementById('status-filter');
        const locationFilter = document.getElementById('location-filter');
        const companyFilter = document.getElementById('company-filter');
        const sourceFilter = document.getElementById('source-filter');
        
        if (searchInput) this.filters.search = searchInput.value.trim();
        if (statusFilter) this.filters.status = statusFilter.value;
        if (locationFilter) this.filters.location = locationFilter.value.trim();
        if (companyFilter) this.filters.company = companyFilter.value.trim();
        if (sourceFilter) this.filters.source = sourceFilter.value;
    }

    /**
     * Update filters (called on input change)
     */
    updateFilters() {
        // For real-time filtering, we'll debounce this
        this.updateFiltersFromInputs();
        
        // Apply local filtering for immediate feedback
        this.applyLocalFilters();
    }

    /**
     * Apply filters locally for immediate feedback
     */
    applyLocalFilters() {
        let filtered = [...this.jobs];
        
        // Apply search filter
        if (this.filters.search) {
            const searchTerm = this.filters.search.toLowerCase();
            filtered = filtered.filter(job => 
                job.title.toLowerCase().includes(searchTerm) ||
                job.company.toLowerCase().includes(searchTerm) ||
                (job.description && job.description.toLowerCase().includes(searchTerm))
            );
        }
        
        // Apply status filter
        if (this.filters.status) {
            filtered = filtered.filter(job => job.status === this.filters.status);
        }
        
        // Apply location filter
        if (this.filters.location) {
            const locationTerm = this.filters.location.toLowerCase();
            filtered = filtered.filter(job => 
                job.location && job.location.toLowerCase().includes(locationTerm)
            );
        }
        
        // Apply company filter
        if (this.filters.company) {
            const companyTerm = this.filters.company.toLowerCase();
            filtered = filtered.filter(job => 
                job.company.toLowerCase().includes(companyTerm)
            );
        }
        
        this.filteredJobs = filtered;
        this.renderJobs();
    }
    
    showAddJobModal() {
        const modal = document.getElementById('add-job-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }
    
    hideAddJobModal() {
        const modal = document.getElementById('add-job-modal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }
    
    /**
     * Save new job from modal form
     */
    async saveJob() {
        try {
            const formData = this.getJobFormData();
            
            if (!this.validateJobForm(formData)) {
                return;
            }
            
            // Transform to API format
            const apiJobData = {
                company: formData.company,
                position: formData.title,
                job_url: formData.url || null,
                location: formData.location || null,
                salary_min: formData.salaryMin ? parseInt(formData.salaryMin) : null,
                salary_max: formData.salaryMax ? parseInt(formData.salaryMax) : null,
                description: formData.description || null,
                status: 'wishlist' // Default status
            };
            
            // Show loading state
            const saveBtn = document.getElementById('save-job-btn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = 'Saving...';
            saveBtn.disabled = true;
            
            // Create job via API
            const newJob = await this.apiClient.createJob(apiJobData);
            
            // Add to local jobs list
            const transformedJob = this.transformJobData(newJob);
            this.jobs.unshift(transformedJob);
            this.filteredJobs = [...this.jobs];
            
            // Update UI
            this.renderJobs();
            await this.updateStats();
            this.hideAddJobModal();
            this.clearJobForm();
            
            ToastNotification.success('Job added successfully!');
            
        } catch (error) {
            this.handleError('Failed to save job', error);
        } finally {
            // Reset button state
            const saveBtn = document.getElementById('save-job-btn');
            if (saveBtn) {
                saveBtn.textContent = 'Save Job';
                saveBtn.disabled = false;
            }
        }
    }
    
    /**
     * Get form data from add job modal
     */
    getJobFormData() {
        return {
            title: document.getElementById('job-title')?.value || '',
            company: document.getElementById('job-company')?.value || '',
            location: document.getElementById('job-location')?.value || '',
            url: document.getElementById('job-url')?.value || '',
            salaryMin: document.getElementById('job-salary-min')?.value || '',
            salaryMax: document.getElementById('job-salary-max')?.value || '',
            techStack: document.getElementById('job-tech-stack')?.value || '',
            description: document.getElementById('job-description')?.value || ''
        };
    }
    
    /**
     * Validate job form data
     */
    validateJobForm(formData) {
        const errors = [];
        
        if (!formData.title.trim()) {
            errors.push('Job title is required');
        }
        
        if (!formData.company.trim()) {
            errors.push('Company name is required');
        }
        
        if (formData.url && !this.isValidUrl(formData.url)) {
            errors.push('Please enter a valid URL');
        }
        
        if (formData.salaryMin && formData.salaryMax) {
            const min = parseInt(formData.salaryMin);
            const max = parseInt(formData.salaryMax);
            if (min > max) {
                errors.push('Minimum salary cannot be greater than maximum salary');
            }
        }
        
        if (errors.length > 0) {
            ToastNotification.error(errors.join('. '));
            return false;
        }
        
        return true;
    }
    
    /**
     * Clear job form
     */
    clearJobForm() {
        const formInputs = [
            'job-title',
            'job-company',
            'job-location',
            'job-url',
            'job-salary-min',
            'job-salary-max',
            'job-tech-stack',
            'job-description'
        ];
        
        formInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.value = '';
            }
        });
    }
    
    /**
     * View job details (placeholder for future modal/page)
     */
    viewJobDetails(job) {
        // For now, show job details in a simple alert
        // This could be enhanced with a detailed modal later
        const details = [
            `Title: ${job.title}`,
            `Company: ${job.company}`,
            `Location: ${job.location || 'Not specified'}`,
            `Status: ${this.getStatusLabel(job.status)}`,
            `Salary: ${this.formatSalary(job.salary_min, job.salary_max) || 'Not specified'}`,
            `Posted: ${this.formatDate(job.date_posted)}`,
            job.date_applied ? `Applied: ${this.formatDate(job.date_applied)}` : '',
            job.description ? `Description: ${job.description.substring(0, 200)}...` : ''
        ].filter(Boolean).join('\n');
        
        alert(details);
        
        // TODO: Implement proper job details modal
        console.log('Job details:', job);
    }
    
    /**
     * Update job status
     */
    async updateJobStatus(jobId, newStatus) {
        try {
            // Find job in local array
            const jobIndex = this.jobs.findIndex(job => job.id === jobId);
            if (jobIndex === -1) {
                throw new Error('Job not found');
            }
            
            const job = this.jobs[jobIndex];
            const oldStatus = job.status;
            
            // Optimistically update UI
            job.status = newStatus;
            if (newStatus === 'applied' && !job.date_applied) {
                job.date_applied = new Date().toISOString();
            }
            
            this.renderJobs();
            await this.updateStats();
            
            // Update via API
            const apiStatus = this.mapFrontendStatusToApi(newStatus);
            const updateData = { status: apiStatus };
            
            if (newStatus === 'applied' && !job.date_applied) {
                updateData.applied_date = new Date().toISOString();
            }
            
            await this.apiClient.updateJob(jobId, updateData);
            
            ToastNotification.success(`Job status updated to ${this.getStatusLabel(newStatus)}`);
            
        } catch (error) {
            // Revert optimistic update on error
            const jobIndex = this.jobs.findIndex(job => job.id === jobId);
            if (jobIndex !== -1) {
                this.jobs[jobIndex].status = oldStatus;
                this.renderJobs();
                await this.updateStats();
            }
            
            this.handleError('Failed to update job status', error);
        }
    }
    
    /**
     * Delete job
     */
    async deleteJob(jobId) {
        try {
            if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
                return;
            }
            
            // Find job in local array
            const jobIndex = this.jobs.findIndex(job => job.id === jobId);
            if (jobIndex === -1) {
                throw new Error('Job not found');
            }
            
            // Remove from local array (optimistic update)
            const deletedJob = this.jobs.splice(jobIndex, 1)[0];
            this.filteredJobs = this.filteredJobs.filter(job => job.id !== jobId);
            
            this.renderJobs();
            await this.updateStats();
            
            // Delete via API
            await this.apiClient.deleteJob(jobId);
            
            ToastNotification.success('Job deleted successfully');
            
        } catch (error) {
            // Revert optimistic update on error
            if (deletedJob) {
                this.jobs.splice(jobIndex, 0, deletedJob);
                this.filteredJobs = [...this.jobs];
                this.renderJobs();
                await this.updateStats();
            }
            
            this.handleError('Failed to delete job', error);
        }
    }
    
    /**
     * Update pagination controls
     */
    updatePagination() {
        const paginationContainer = document.getElementById('pagination-container');
        const pageStart = document.getElementById('page-start');
        const pageEnd = document.getElementById('page-end');
        const totalJobs = document.getElementById('total-jobs');
        const pageNumbers = document.getElementById('page-numbers');
        
        const totalItems = this.filteredJobs.length;
        const totalPages = Math.ceil(totalItems / this.jobsPerPage);
        
        if (totalPages <= 1) {
            if (paginationContainer) paginationContainer.classList.add('hidden');
            return;
        }
        
        if (paginationContainer) paginationContainer.classList.remove('hidden');
        
        // Update page info
        const start = (this.currentPage - 1) * this.jobsPerPage + 1;
        const end = Math.min(this.currentPage * this.jobsPerPage, totalItems);
        
        if (pageStart) pageStart.textContent = start;
        if (pageEnd) pageEnd.textContent = end;
        if (totalJobs) totalJobs.textContent = totalItems;
        
        // Update page numbers
        if (pageNumbers) {
            pageNumbers.innerHTML = '';
            
            const maxVisiblePages = 5;
            let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
            let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
            
            if (endPage - startPage + 1 < maxVisiblePages) {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }
            
            for (let i = startPage; i <= endPage; i++) {
                const pageBtn = document.createElement('button');
                pageBtn.className = `relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                    i === this.currentPage
                        ? 'z-10 bg-blue-50 dark:bg-blue-900 border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`;
                pageBtn.textContent = i;
                pageBtn.addEventListener('click', () => this.goToPage(i));
                pageNumbers.appendChild(pageBtn);
            }
        }
        
        // Update prev/next buttons
        this.updatePaginationButtons(totalPages);
    }
    
    /**
     * Update pagination button states
     */
    updatePaginationButtons(totalPages) {
        const prevBtns = [
            document.getElementById('prev-page-mobile'),
            document.getElementById('prev-page-desktop')
        ];
        const nextBtns = [
            document.getElementById('next-page-mobile'),
            document.getElementById('next-page-desktop')
        ];
        
        prevBtns.forEach(btn => {
            if (btn) {
                btn.disabled = this.currentPage <= 1;
                btn.onclick = () => this.goToPage(this.currentPage - 1);
            }
        });
        
        nextBtns.forEach(btn => {
            if (btn) {
                btn.disabled = this.currentPage >= totalPages;
                btn.onclick = () => this.goToPage(this.currentPage + 1);
            }
        });
    }
    
    /**
     * Go to specific page
     */
    async goToPage(page) {
        const totalPages = Math.ceil(this.filteredJobs.length / this.jobsPerPage);
        
        if (page < 1 || page > totalPages) {
            return;
        }
        
        this.currentPage = page;
        await this.loadJobs();
    }

    /**
     * Cleanup when dashboard is destroyed
     */
    destroy() {
        this.stopRealTimeUpdates();
        
        if (this.wsClient) {
            this.wsClient.disconnect();
        }
        
        // Cleanup managers
        if (this.analyticsDashboard) {
            this.analyticsDashboard.destroy();
        }
        
        // Remove event listeners
        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('online', this.startRealTimeUpdates);
        window.removeEventListener('offline', this.stopRealTimeUpdates);
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    }
    
    handleKeyboardNavigation(e) {
        // Basic keyboard navigation
        if (e.key === 'Escape') {
            // Close any open modals or dropdowns
            const modal = document.getElementById('add-job-modal');
            if (modal && !modal.classList.contains('hidden')) {
                this.hideAddJobModal();
            }
            
            // Close mobile menu
            const mobileMenu = document.getElementById('mobile-menu');
            if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                mobileMenu.classList.add('hidden');
            }
        }
    }
    
    handleClickOutside(e) {
        // Close dropdowns when clicking outside
        const menus = document.querySelectorAll('.job-menu');
        menus.forEach(menu => {
            if (!menu.contains(e.target) && !menu.classList.contains('hidden')) {
                menu.classList.add('hidden');
            }
        });
    }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ResponsiveDashboard();
});