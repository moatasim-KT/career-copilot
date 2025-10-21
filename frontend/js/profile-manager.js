/**
 * User Profile and Settings Manager for Career Co-Pilot
 * Handles user profile editing, preferences, and settings management
 */

class ProfileManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.userProfile = null;
        this.userSettings = null;
        this.isDirty = false;
        
        this.init();
    }
    
    async init() {
        await this.loadUserData();
        this.setupEventListeners();
        this.renderProfile();
        this.renderSettings();
        
        console.log('Profile Manager initialized');
    }
    
    async loadUserData() {
        try {
            // Try to load user profile from API
            this.userProfile = await this.apiClient.request('/user/profile');
            this.userSettings = await this.apiClient.request('/user/settings');
            
        } catch (error) {
            console.warn('User data not available from API, using defaults:', error.message);
            this.loadDefaultData();
        }
    }
    
    loadDefaultData() {
        // Default user profile
        this.userProfile = {
            id: 'default_user',
            name: 'Job Seeker',
            email: 'user@example.com',
            skills: ['JavaScript', 'Python', 'React', 'HTML', 'CSS'],
            experience_level: 'mid',
            preferred_locations: ['San Francisco, CA', 'Remote'],
            preferred_job_types: ['full-time', 'contract'],
            salary_range: {
                min: 80000,
                max: 120000
            },
            bio: 'Passionate software developer with experience in web technologies.',
            linkedin_url: '',
            github_url: '',
            portfolio_url: ''
        };
        
        // Default user settings
        this.userSettings = {
            email_notifications: true,
            notification_frequency: 'daily',
            notification_time: '08:00',
            job_alert_keywords: ['developer', 'engineer', 'programmer'],
            auto_apply_enabled: false,
            theme: 'light',
            language: 'en',
            timezone: 'America/Los_Angeles'
        };
    }
    
    setupEventListeners() {
        // Profile form submission
        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveProfile();
            });
        }
        
        // Settings form submission
        const settingsForm = document.getElementById('settings-form');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }
        
        // Skills management
        const addSkillBtn = document.getElementById('add-skill-btn');
        if (addSkillBtn) {
            addSkillBtn.addEventListener('click', () => {
                this.showAddSkillModal();
            });
        }
        
        // Location management
        const addLocationBtn = document.getElementById('add-location-btn');
        if (addLocationBtn) {
            addLocationBtn.addEventListener('click', () => {
                this.showAddLocationModal();
            });
        }
        
        // Form change detection
        this.setupChangeDetection();
    }
    
    setupChangeDetection() {
        const forms = ['profile-form', 'settings-form'];
        
        forms.forEach(formId => {
            const form = document.getElementById(formId);
            if (form) {
                const inputs = form.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    input.addEventListener('change', () => {
                        this.isDirty = true;
                        this.showUnsavedChanges();
                    });
                });
            }
        });
    }
    
    renderProfile() {
        if (!this.userProfile) return;
        
        // Basic profile information
        this.setInputValue('profile-name', this.userProfile.name);
        this.setInputValue('profile-email', this.userProfile.email);
        this.setInputValue('profile-bio', this.userProfile.bio);
        this.setInputValue('profile-linkedin', this.userProfile.linkedin_url);
        this.setInputValue('profile-github', this.userProfile.github_url);
        this.setInputValue('profile-portfolio', this.userProfile.portfolio_url);
        
        // Experience level
        this.setSelectValue('profile-experience-level', this.userProfile.experience_level);
        
        // Salary range
        this.setInputValue('profile-salary-min', this.userProfile.salary_range?.min);
        this.setInputValue('profile-salary-max', this.userProfile.salary_range?.max);
        
        // Skills
        this.renderSkills();
        
        // Preferred locations
        this.renderLocations();
        
        // Job types
        this.renderJobTypes();
    }
    
    renderSettings() {
        if (!this.userSettings) return;
        
        // Notification settings
        this.setCheckboxValue('settings-email-notifications', this.userSettings.email_notifications);
        this.setSelectValue('settings-notification-frequency', this.userSettings.notification_frequency);
        this.setInputValue('settings-notification-time', this.userSettings.notification_time);
        
        // Job alert settings
        this.setInputValue('settings-job-keywords', this.userSettings.job_alert_keywords?.join(', '));
        this.setCheckboxValue('settings-auto-apply', this.userSettings.auto_apply_enabled);
        
        // Appearance settings
        this.setSelectValue('settings-theme', this.userSettings.theme);
        this.setSelectValue('settings-language', this.userSettings.language);
        this.setSelectValue('settings-timezone', this.userSettings.timezone);
    }
    
    renderSkills() {
        const container = document.getElementById('skills-container');
        if (!container || !this.userProfile.skills) return;
        
        container.innerHTML = '';
        
        this.userProfile.skills.forEach(skill => {
            const skillTag = this.createSkillTag(skill);
            container.appendChild(skillTag);
        });
    }
    
    createSkillTag(skill) {
        const tag = document.createElement('div');
        tag.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
        
        tag.innerHTML = `
            <span>${skill}</span>
            <button type="button" class="ml-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200" onclick="profileManager.removeSkill('${skill}')">
                <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
            </button>
        `;
        
        return tag;
    }
    
    renderLocations() {
        const container = document.getElementById('locations-container');
        if (!container || !this.userProfile.preferred_locations) return;
        
        container.innerHTML = '';
        
        this.userProfile.preferred_locations.forEach(location => {
            const locationTag = this.createLocationTag(location);
            container.appendChild(locationTag);
        });
    }
    
    createLocationTag(location) {
        const tag = document.createElement('div');
        tag.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
        
        tag.innerHTML = `
            <span>${location}</span>
            <button type="button" class="ml-2 text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-200" onclick="profileManager.removeLocation('${location}')">
                <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
            </button>
        `;
        
        return tag;
    }
    
    renderJobTypes() {
        const container = document.getElementById('job-types-container');
        if (!container) return;
        
        const jobTypes = ['full-time', 'part-time', 'contract', 'freelance', 'internship'];
        const userJobTypes = this.userProfile.preferred_job_types || [];
        
        container.innerHTML = '';
        
        jobTypes.forEach(type => {
            const checkbox = document.createElement('label');
            checkbox.className = 'inline-flex items-center';
            
            const isChecked = userJobTypes.includes(type);
            
            checkbox.innerHTML = `
                <input type="checkbox" class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50" 
                       value="${type}" ${isChecked ? 'checked' : ''} onchange="profileManager.updateJobTypes()">
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">${type.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
            `;
            
            container.appendChild(checkbox);
        });
    }
    
    showAddSkillModal() {
        const modal = document.getElementById('add-skill-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('new-skill-input')?.focus();
        }
    }
    
    hideAddSkillModal() {
        const modal = document.getElementById('add-skill-modal');
        if (modal) {
            modal.classList.add('hidden');
            document.getElementById('new-skill-input').value = '';
        }
    }
    
    addSkill() {
        const input = document.getElementById('new-skill-input');
        if (!input) return;
        
        const skill = input.value.trim();
        if (!skill) return;
        
        if (this.userProfile.skills.includes(skill)) {
            ToastNotification.warning('Skill already exists');
            return;
        }
        
        this.userProfile.skills.push(skill);
        this.renderSkills();
        this.hideAddSkillModal();
        this.isDirty = true;
        this.showUnsavedChanges();
        
        ToastNotification.success(`Added skill: ${skill}`);
    }
    
    removeSkill(skill) {
        const index = this.userProfile.skills.indexOf(skill);
        if (index > -1) {
            this.userProfile.skills.splice(index, 1);
            this.renderSkills();
            this.isDirty = true;
            this.showUnsavedChanges();
            
            ToastNotification.success(`Removed skill: ${skill}`);
        }
    }
    
    showAddLocationModal() {
        const modal = document.getElementById('add-location-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('new-location-input')?.focus();
        }
    }
    
    hideAddLocationModal() {
        const modal = document.getElementById('add-location-modal');
        if (modal) {
            modal.classList.add('hidden');
            document.getElementById('new-location-input').value = '';
        }
    }
    
    addLocation() {
        const input = document.getElementById('new-location-input');
        if (!input) return;
        
        const location = input.value.trim();
        if (!location) return;
        
        if (this.userProfile.preferred_locations.includes(location)) {
            ToastNotification.warning('Location already exists');
            return;
        }
        
        this.userProfile.preferred_locations.push(location);
        this.renderLocations();
        this.hideAddLocationModal();
        this.isDirty = true;
        this.showUnsavedChanges();
        
        ToastNotification.success(`Added location: ${location}`);
    }
    
    removeLocation(location) {
        const index = this.userProfile.preferred_locations.indexOf(location);
        if (index > -1) {
            this.userProfile.preferred_locations.splice(index, 1);
            this.renderLocations();
            this.isDirty = true;
            this.showUnsavedChanges();
            
            ToastNotification.success(`Removed location: ${location}`);
        }
    }
    
    updateJobTypes() {
        const checkboxes = document.querySelectorAll('#job-types-container input[type="checkbox"]');
        const selectedTypes = [];
        
        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                selectedTypes.push(checkbox.value);
            }
        });
        
        this.userProfile.preferred_job_types = selectedTypes;
        this.isDirty = true;
        this.showUnsavedChanges();
    }
    
    async saveProfile() {
        try {
            // Collect form data
            const formData = this.collectProfileFormData();
            
            // Validate form data
            if (!this.validateProfileData(formData)) {
                return;
            }
            
            // Update user profile
            Object.assign(this.userProfile, formData);
            
            // Show loading state
            const saveBtn = document.getElementById('save-profile-btn');
            const originalText = saveBtn?.textContent;
            if (saveBtn) {
                saveBtn.textContent = 'Saving...';
                saveBtn.disabled = true;
            }
            
            // Save to API
            try {
                await this.apiClient.request('/user/profile', {
                    method: 'PUT',
                    body: JSON.stringify(this.userProfile)
                });
            } catch (error) {
                console.warn('API save failed, saving locally:', error.message);
                this.saveToLocalStorage();
            }
            
            this.isDirty = false;
            this.hideUnsavedChanges();
            ToastNotification.success('Profile saved successfully!');
            
        } catch (error) {
            console.error('Failed to save profile:', error);
            ToastNotification.error('Failed to save profile');
        } finally {
            // Reset button state
            const saveBtn = document.getElementById('save-profile-btn');
            if (saveBtn && originalText) {
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
            }
        }
    }
    
    async saveSettings() {
        try {
            // Collect form data
            const formData = this.collectSettingsFormData();
            
            // Update user settings
            Object.assign(this.userSettings, formData);
            
            // Show loading state
            const saveBtn = document.getElementById('save-settings-btn');
            const originalText = saveBtn?.textContent;
            if (saveBtn) {
                saveBtn.textContent = 'Saving...';
                saveBtn.disabled = true;
            }
            
            // Save to API
            try {
                await this.apiClient.request('/user/settings', {
                    method: 'PUT',
                    body: JSON.stringify(this.userSettings)
                });
            } catch (error) {
                console.warn('API save failed, saving locally:', error.message);
                this.saveToLocalStorage();
            }
            
            // Apply theme change immediately
            if (formData.theme) {
                this.applyTheme(formData.theme);
            }
            
            this.isDirty = false;
            this.hideUnsavedChanges();
            ToastNotification.success('Settings saved successfully!');
            
        } catch (error) {
            console.error('Failed to save settings:', error);
            ToastNotification.error('Failed to save settings');
        } finally {
            // Reset button state
            const saveBtn = document.getElementById('save-settings-btn');
            if (saveBtn && originalText) {
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
            }
        }
    }
    
    collectProfileFormData() {
        return {
            name: this.getInputValue('profile-name'),
            email: this.getInputValue('profile-email'),
            bio: this.getInputValue('profile-bio'),
            linkedin_url: this.getInputValue('profile-linkedin'),
            github_url: this.getInputValue('profile-github'),
            portfolio_url: this.getInputValue('profile-portfolio'),
            experience_level: this.getSelectValue('profile-experience-level'),
            salary_range: {
                min: parseInt(this.getInputValue('profile-salary-min')) || null,
                max: parseInt(this.getInputValue('profile-salary-max')) || null
            }
        };
    }
    
    collectSettingsFormData() {
        const keywords = this.getInputValue('settings-job-keywords');
        
        return {
            email_notifications: this.getCheckboxValue('settings-email-notifications'),
            notification_frequency: this.getSelectValue('settings-notification-frequency'),
            notification_time: this.getInputValue('settings-notification-time'),
            job_alert_keywords: keywords ? keywords.split(',').map(k => k.trim()) : [],
            auto_apply_enabled: this.getCheckboxValue('settings-auto-apply'),
            theme: this.getSelectValue('settings-theme'),
            language: this.getSelectValue('settings-language'),
            timezone: this.getSelectValue('settings-timezone')
        };
    }
    
    validateProfileData(data) {
        const errors = [];
        
        if (!data.name?.trim()) {
            errors.push('Name is required');
        }
        
        if (!data.email?.trim()) {
            errors.push('Email is required');
        } else if (!this.isValidEmail(data.email)) {
            errors.push('Please enter a valid email address');
        }
        
        if (data.salary_range.min && data.salary_range.max && data.salary_range.min > data.salary_range.max) {
            errors.push('Minimum salary cannot be greater than maximum salary');
        }
        
        if (errors.length > 0) {
            ToastNotification.error(errors.join('. '));
            return false;
        }
        
        return true;
    }
    
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem('theme', theme);
    }
    
    saveToLocalStorage() {
        localStorage.setItem('userProfile', JSON.stringify(this.userProfile));
        localStorage.setItem('userSettings', JSON.stringify(this.userSettings));
    }
    
    loadFromLocalStorage() {
        const profile = localStorage.getItem('userProfile');
        const settings = localStorage.getItem('userSettings');
        
        if (profile) {
            this.userProfile = JSON.parse(profile);
        }
        
        if (settings) {
            this.userSettings = JSON.parse(settings);
        }
    }
    
    showUnsavedChanges() {
        const indicator = document.getElementById('unsaved-changes-indicator');
        if (indicator) {
            indicator.classList.remove('hidden');
        }
    }
    
    hideUnsavedChanges() {
        const indicator = document.getElementById('unsaved-changes-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    }
    
    // Utility methods for form handling
    setInputValue(id, value) {
        const input = document.getElementById(id);
        if (input && value !== undefined && value !== null) {
            input.value = value;
        }
    }
    
    getInputValue(id) {
        const input = document.getElementById(id);
        return input ? input.value : '';
    }
    
    setSelectValue(id, value) {
        const select = document.getElementById(id);
        if (select && value !== undefined && value !== null) {
            select.value = value;
        }
    }
    
    getSelectValue(id) {
        const select = document.getElementById(id);
        return select ? select.value : '';
    }
    
    setCheckboxValue(id, value) {
        const checkbox = document.getElementById(id);
        if (checkbox && value !== undefined && value !== null) {
            checkbox.checked = value;
        }
    }
    
    getCheckboxValue(id) {
        const checkbox = document.getElementById(id);
        return checkbox ? checkbox.checked : false;
    }
}

// Export for use in other modules
window.ProfileManager = ProfileManager;