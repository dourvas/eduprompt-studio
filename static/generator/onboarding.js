/**
 * EduPrompt Studio - Onboarding Modal
 * Research data collection for International Hellenic University
 */

class OnboardingModal {
    constructor() {
        this.timer = null;
        this.modalShown = false;
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;
        
        document.addEventListener('DOMContentLoaded', () => {
            this.createModal();
            this.setupEventListeners();
            this.checkShouldShow();
        });
        
        this.initialized = true;
    }

    createModal() {
        const modalHTML = `
            <div id="onboardingModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden">
                <div class="bg-white rounded-xl p-6 max-w-md mx-4 shadow-2xl transform transition-all duration-300 scale-95 modal-content" id="modalContent">
                    
                    <!-- Header -->
                    <div class="text-center mb-6">
                        <div class="university-icon w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                            <span class="text-white text-2xl">🎓</span>
                        </div>
                        <h3 class="text-xl font-semibold text-gray-800 mb-2">Welcome to EduPrompt Studio!</h3>
                        <p class="text-gray-600 text-sm mb-3">Help us understand our users' profile (10 seconds)</p>
                        
                        <!-- Research Badge -->
                        <div class="research-badge rounded-lg p-3 mb-4">
                            <div class="flex items-center justify-center space-x-2 mb-1">
                                <span class="text-blue-600 text-sm">🏛️</span>
                                <span class="text-blue-800 font-medium text-sm">University Research</span>
                            </div>
                            <p class="text-blue-700 text-xs leading-relaxed">
                                Part of a doctoral dissertation at <strong>International Hellenic University</strong><br>
                                on AI teacher training and professional development
                            </p>
                        </div>
                    </div>

                    <!-- Form -->
                    <form id="onboardingForm" class="space-y-5">
                        
                        <!-- Question 1: AI Experience -->
                        <div class="space-y-3">
                            <label class="block text-sm font-medium text-gray-700">
                                How much experience do you have with AI tools?
                            </label>
                            <div class="space-y-2">
                                ${this.createRadioOption('ai_experience', 'none', 'No experience')}
                                ${this.createRadioOption('ai_experience', 'basic', 'Basic (e.g., ChatGPT)')}
                                ${this.createRadioOption('ai_experience', 'intermediate', 'Intermediate')}
                                ${this.createRadioOption('ai_experience', 'advanced', 'Advanced')}
                            </div>
                        </div>

                        <!-- Question 2: Teaching Experience -->
                        <div class="space-y-3">
                            <label class="block text-sm font-medium text-gray-700">
                                How many years have you been teaching?
                            </label>
                            <div class="grid grid-cols-2 gap-3 radio-grid">
                                ${this.createRadioOption('teaching_years', '0-5', '0-5 years', 'col-span-1')}
                                ${this.createRadioOption('teaching_years', '6-15', '6-15 years', 'col-span-1')}
                                ${this.createRadioOption('teaching_years', '16-25', '16-25 years', 'col-span-1')}
                                ${this.createRadioOption('teaching_years', '25+', '25+ years', 'col-span-1')}
                            </div>
                        </div>

                    </form>

                    <!-- Buttons -->
                    <div class="flex space-x-3 mt-6">
                        <button type="button" class="btn-skip flex-1 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg text-sm">
                            Skip
                        </button>
                        <button type="button" class="btn-continue flex-1 px-4 py-2 text-white rounded-lg text-sm font-medium">
                            Continue
                        </button>
                    </div>

                    <!-- Privacy note -->
                    <p class="text-xs text-gray-500 text-center mt-4">
                        Data is used anonymously for research purposes<br>
                        in accordance with academic research ethics standards
                    </p>

                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    createRadioOption(name, value, label, extraClasses = '') {
        return `
            <label class="radio-option flex items-center p-3 border border-gray-200 rounded-lg cursor-pointer ${extraClasses}">
                <input type="radio" name="${name}" value="${value}" class="onboarding-radio mr-3">
                <span class="text-sm">${label}</span>
            </label>
        `;
    }

    setupEventListeners() {
        // Skip button
        document.querySelector('.btn-skip').addEventListener('click', () => {
            this.skip();
        });

        // Continue button
        document.querySelector('.btn-continue').addEventListener('click', () => {
            this.submit();
        });

        // Click outside to close
        document.getElementById('onboardingModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.close();
            }
        });

        // Clear timer on user interaction
        document.addEventListener('click', () => {
            if (this.timer && !this.modalShown) {
                clearTimeout(this.timer);
                this.timer = null;
            }
        }, { once: true });
    }

    checkShouldShow() {
        // Don't show if already shown in this session
        if (sessionStorage.getItem('onboarding_shown')) {
            return;
        }

        // Show after 15 seconds
        this.timer = setTimeout(() => {
            this.show();
        }, 15000);
    }

    show() {
        if (this.modalShown) return;

        const modal = document.getElementById('onboardingModal');
        const modalContent = document.getElementById('modalContent');

        modal.classList.remove('hidden');
        this.modalShown = true;

        // Animation
        setTimeout(() => {
            modalContent.classList.remove('scale-95');
            modalContent.classList.add('scale-100');
        }, 10);

        // Mark as shown
        sessionStorage.setItem('onboarding_shown', 'true');

        // Analytics event
        this.trackEvent('onboarding_shown');
    }

    close() {
        const modal = document.getElementById('onboardingModal');
        const modalContent = document.getElementById('modalContent');

        modalContent.classList.remove('scale-100');
        modalContent.classList.add('scale-95');

        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }

    skip() {
        this.close();
        this.trackEvent('onboarding_skipped');
        console.log('Onboarding skipped');
    }

    async submit() {
        const form = document.getElementById('onboardingForm');
        const formData = new FormData(form);

        // Validate
        const aiExperience = formData.get('ai_experience');
        const teachingYears = formData.get('teaching_years');

        if (!aiExperience || !teachingYears) {
            alert('Please answer both questions');
            return;
        }

        // Show loading state
        const continueBtn = document.querySelector('.btn-continue');
        const originalText = continueBtn.textContent;
        continueBtn.textContent = 'Saving...';
        continueBtn.disabled = true;

        try {
            const response = await fetch('/onboarding/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    ai_experience: aiExperience,
                    teaching_years: teachingYears,
                    timestamp: new Date().toISOString()
                })
            });

            if (response.ok) {
                sessionStorage.setItem('onboarding_completed', 'true');
                this.trackEvent('onboarding_completed', {
                    ai_experience: aiExperience,
                    teaching_years: teachingYears
                });
                this.close();
                console.log('Onboarding data saved successfully');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

        } catch (error) {
            console.error('Error saving onboarding data:', error);
            this.trackEvent('onboarding_error', { error: error.message });
            
            // Still close modal to not block user
            this.close();
            
            // Optionally show a non-blocking notification
            this.showNotification('Data saved locally. Thank you!', 'success');
        } finally {
            continueBtn.textContent = originalText;
            continueBtn.disabled = false;
        }
    }

    getCSRFToken() {
        const name = "csrftoken";
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(name + '=')) {
                return decodeURIComponent(trimmed.substring(name.length + 1));
            }
        }
        return '';
    }

    trackEvent(eventName, data = {}) {
        // Analytics tracking - can be extended
        console.log(`📊 Onboarding Event: ${eventName}`, data);
        
        // If you have Google Analytics or other tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, {
                event_category: 'onboarding',
                ...data
            });
        }
    }

    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${
            type === 'success' ? 'bg-green-500' : 'bg-blue-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize onboarding
const onboarding = new OnboardingModal();
onboarding.init();