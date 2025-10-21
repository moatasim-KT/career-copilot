/**
 * Firebase Configuration for Career Copilot Frontend
 * Handles Firebase initialization and authentication
 */

// Firebase configuration - these values should be set from environment variables
const firebaseConfig = {
    apiKey: window.FIREBASE_API_KEY || "your-api-key-here",
    authDomain: window.FIREBASE_AUTH_DOMAIN || "career-copilot-system.firebaseapp.com",
    projectId: window.FIREBASE_PROJECT_ID || "career-copilot-system",
    storageBucket: window.FIREBASE_STORAGE_BUCKET || "career-copilot-system.appspot.com",
    messagingSenderId: window.FIREBASE_MESSAGING_SENDER_ID || "123456789012",
    appId: window.FIREBASE_APP_ID || "1:123456789012:web:abcdef123456"
};

class FirebaseAuthManager {
    constructor() {
        this.app = null;
        this.auth = null;
        this.currentUser = null;
        this.authStateListeners = [];
        this.initialized = false;
    }

    /**
     * Initialize Firebase
     */
    async initialize() {
        try {
            // Check if Firebase SDK is loaded
            if (typeof firebase === 'undefined') {
                console.error('Firebase SDK not loaded');
                return false;
            }

            // Initialize Firebase app
            this.app = firebase.initializeApp(firebaseConfig);
            this.auth = firebase.auth();

            // Set up auth state listener
            this.auth.onAuthStateChanged((user) => {
                this.currentUser = user;
                this.notifyAuthStateListeners(user);
            });

            this.initialized = true;
            console.log('Firebase initialized successfully');
            return true;

        } catch (error) {
            console.error('Error initializing Firebase:', error);
            return false;
        }
    }

    /**
     * Sign up with email and password
     */
    async signUp(email, password, displayName = null) {
        try {
            if (!this.initialized) {
                throw new Error('Firebase not initialized');
            }

            const userCredential = await this.auth.createUserWithEmailAndPassword(email, password);
            const user = userCredential.user;

            // Update display name if provided
            if (displayName) {
                await user.updateProfile({
                    displayName: displayName
                });
            }

            // Get Firebase ID token
            const idToken = await user.getIdToken();

            // Exchange for JWT access token
            const apiClient = new window.APIClient();
            const tokenResponse = await apiClient.exchangeFirebaseToken(idToken);

            // Set access token in API client
            apiClient.setAuthToken(tokenResponse.access_token);

            console.log('User signed up successfully:', user.uid);
            return {
                success: true,
                user: user,
                accessToken: tokenResponse.access_token,
                message: 'Account created successfully'
            };

        } catch (error) {
            console.error('Sign up error:', error);
            return {
                success: false,
                error: error.code,
                message: this.getErrorMessage(error.code)
            };
        }
    }

    /**
     * Sign in with email and password
     */
    async signIn(email, password) {
        try {
            if (!this.initialized) {
                throw new Error('Firebase not initialized');
            }

            const userCredential = await this.auth.signInWithEmailAndPassword(email, password);
            const user = userCredential.user;

            // Get Firebase ID token
            const idToken = await user.getIdToken();

            // Exchange for JWT access token
            const apiClient = new window.APIClient();
            const tokenResponse = await apiClient.exchangeFirebaseToken(idToken);

            // Set access token in API client
            apiClient.setAuthToken(tokenResponse.access_token);

            console.log('User signed in successfully:', user.uid);
            return {
                success: true,
                user: user,
                accessToken: tokenResponse.access_token,
                message: 'Signed in successfully'
            };

        } catch (error) {
            console.error('Sign in error:', error);
            return {
                success: false,
                error: error.code,
                message: this.getErrorMessage(error.code)
            };
        }
    }

    /**
     * Sign in with Google
     */
    async signInWithGoogle() {
        try {
            if (!this.initialized) {
                throw new Error('Firebase not initialized');
            }

            const provider = new firebase.auth.GoogleAuthProvider();
            provider.addScope('email');
            provider.addScope('profile');

            const result = await this.auth.signInWithPopup(provider);
            const user = result.user;

            // Get Firebase ID token
            const idToken = await user.getIdToken();

            // Exchange for JWT access token
            const apiClient = new window.APIClient();
            const tokenResponse = await apiClient.exchangeFirebaseToken(idToken);

            // Set access token in API client
            apiClient.setAuthToken(tokenResponse.access_token);

            console.log('User signed in with Google:', user.uid);
            return {
                success: true,
                user: user,
                accessToken: tokenResponse.access_token,
                message: 'Signed in with Google successfully'
            };

        } catch (error) {
            console.error('Google sign in error:', error);
            return {
                success: false,
                error: error.code,
                message: this.getErrorMessage(error.code)
            };
        }
    }

    /**
     * Sign out current user
     */
    async signOut() {
        try {
            if (!this.initialized) {
                throw new Error('Firebase not initialized');
            }

            await this.auth.signOut();
            console.log('User signed out successfully');
            return {
                success: true,
                message: 'Signed out successfully'
            };

        } catch (error) {
            console.error('Sign out error:', error);
            return {
                success: false,
                error: error.code,
                message: 'Error signing out'
            };
        }
    }

    /**
     * Get current user's ID token
     */
    async getIdToken(forceRefresh = false) {
        try {
            if (!this.currentUser) {
                return null;
            }

            const idToken = await this.currentUser.getIdToken(forceRefresh);
            return idToken;

        } catch (error) {
            console.error('Error getting ID token:', error);
            return null;
        }
    }

    /**
     * Send password reset email
     */
    async sendPasswordResetEmail(email) {
        try {
            if (!this.initialized) {
                throw new Error('Firebase not initialized');
            }

            await this.auth.sendPasswordResetEmail(email);
            return {
                success: true,
                message: 'Password reset email sent'
            };

        } catch (error) {
            console.error('Password reset error:', error);
            return {
                success: false,
                error: error.code,
                message: this.getErrorMessage(error.code)
            };
        }
    }

    /**
     * Update user profile
     */
    async updateProfile(updates) {
        try {
            if (!this.currentUser) {
                throw new Error('No user signed in');
            }

            await this.currentUser.updateProfile(updates);
            return {
                success: true,
                message: 'Profile updated successfully'
            };

        } catch (error) {
            console.error('Profile update error:', error);
            return {
                success: false,
                error: error.code,
                message: 'Error updating profile'
            };
        }
    }

    /**
     * Add auth state change listener
     */
    onAuthStateChanged(callback) {
        this.authStateListeners.push(callback);
        
        // If already initialized and has current user, call immediately
        if (this.initialized && this.currentUser !== undefined) {
            callback(this.currentUser);
        }
    }

    /**
     * Remove auth state change listener
     */
    removeAuthStateListener(callback) {
        const index = this.authStateListeners.indexOf(callback);
        if (index > -1) {
            this.authStateListeners.splice(index, 1);
        }
    }

    /**
     * Notify all auth state listeners
     */
    notifyAuthStateListeners(user) {
        this.authStateListeners.forEach(callback => {
            try {
                callback(user);
            } catch (error) {
                console.error('Error in auth state listener:', error);
            }
        });
    }

    /**
     * Get user-friendly error message
     */
    getErrorMessage(errorCode) {
        const errorMessages = {
            'auth/user-not-found': 'No account found with this email address.',
            'auth/wrong-password': 'Incorrect password.',
            'auth/email-already-in-use': 'An account with this email already exists.',
            'auth/weak-password': 'Password should be at least 6 characters.',
            'auth/invalid-email': 'Invalid email address.',
            'auth/user-disabled': 'This account has been disabled.',
            'auth/too-many-requests': 'Too many failed attempts. Please try again later.',
            'auth/network-request-failed': 'Network error. Please check your connection.',
            'auth/popup-closed-by-user': 'Sign-in popup was closed.',
            'auth/cancelled-popup-request': 'Sign-in was cancelled.',
            'auth/popup-blocked': 'Sign-in popup was blocked by the browser.'
        };

        return errorMessages[errorCode] || 'An unexpected error occurred. Please try again.';
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.currentUser !== null;
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Wait for auth state to be determined
     */
    async waitForAuthState() {
        return new Promise((resolve) => {
            if (this.currentUser !== null) {
                resolve(this.currentUser);
                return;
            }

            const unsubscribe = this.auth.onAuthStateChanged((user) => {
                unsubscribe();
                resolve(user);
            });
        });
    }
}

// Create global instance
window.firebaseAuthManager = new FirebaseAuthManager();

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    await window.firebaseAuthManager.initialize();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FirebaseAuthManager;
}