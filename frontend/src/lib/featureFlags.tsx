/**
 * Feature Flags System
 * 
 * Enterprise-grade feature flags with remote configuration,
 * user targeting, A/B testing, and gradual rollouts.
 * 
 * @module lib/featureFlags
 */

'use client';

import { useState, useEffect, createContext, useContext, useCallback } from 'react';

export interface FeatureFlag {
    name: string;
    enabled: boolean;
    description?: string;
    rolloutPercentage?: number;
    targetUsers?: string[];
    targetGroups?: string[];
    expiresAt?: Date;
}

export interface FeatureFlagsConfig {
    flags: Record<string, FeatureFlag>;
    defaultValue: boolean;
}

interface FeatureFlagsContextValue {
    isEnabled: (flagName: string) => boolean;
    setFlag: (flagName: string, enabled: boolean) => void;
    getFlag: (flagName: string) => FeatureFlag | undefined;
    getAllFlags: () => Record<string, FeatureFlag>;
    refreshFlags: () => Promise<void>;
}

const FeatureFlagsContext = createContext<FeatureFlagsContextValue | undefined>(undefined);

/**
 * Default feature flags configuration
 */
const DEFAULT_FLAGS: Record<string, FeatureFlag> = {
    'workflow-automation': {
        name: 'workflow-automation',
        enabled: true,
        description: 'Enable workflow automation features',
    },
    'bulk-operations': {
        name: 'bulk-operations',
        enabled: true,
        description: 'Enable bulk operations',
    },
    'advanced-search': {
        name: 'advanced-search',
        enabled: true,
        description: 'Enable advanced search with fuzzy matching',
    },
    'ai-recommendations': {
        name: 'ai-recommendations',
        enabled: false,
        description: 'Enable AI-powered job recommendations',
        rolloutPercentage: 20,
    },
    'dark-mode': {
        name: 'dark-mode',
        enabled: false,
        description: 'Enable dark mode',
        rolloutPercentage: 50,
    },
    'analytics-dashboard': {
        name: 'analytics-dashboard',
        enabled: false,
        description: 'Enable analytics dashboard',
    },
    'social-features': {
        name: 'social-features',
        enabled: false,
        description: 'Enable social sharing features',
    },
    'performance-monitoring': {
        name: 'performance-monitoring',
        enabled: true,
        description: 'Enable performance monitoring',
    },
    'offline-mode': {
        name: 'offline-mode',
        enabled: true,
        description: 'Enable PWA offline mode',
    },
    'beta-features': {
        name: 'beta-features',
        enabled: false,
        description: 'Enable beta features',
        rolloutPercentage: 10,
    },
};

/**
 * Feature Flags Provider
 * 
 * @example
 * ```tsx
 * <FeatureFlagsProvider apiEndpoint="/api/feature-flags">
 *   <App />
 * </FeatureFlagsProvider>
 * ```
 */
export function FeatureFlagsProvider({
    children,
    apiEndpoint,
    defaultFlags = DEFAULT_FLAGS,
}: {
    children: React.ReactNode;
    apiEndpoint?: string;
    defaultFlags?: Record<string, FeatureFlag>;
}) {
    const [flags, setFlags] = useState<Record<string, FeatureFlag>>(defaultFlags);
    const [userId, setUserId] = useState<string | null>(null);

    /**
     * Check if user is in rollout percentage
     */
    const isInRollout = useCallback((flag: FeatureFlag): boolean => {
        if (!flag.rolloutPercentage || !userId) return true;

        // Simple hash-based rollout
        const hash = userId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        const bucket = hash % 100;
        return bucket < flag.rolloutPercentage;
    }, [userId]);

    /**
     * Check if flag is enabled for current user
     */
    const isEnabled = useCallback((flagName: string): boolean => {
        const flag = flags[flagName];

        if (!flag) {
            console.warn(`Feature flag "${flagName}" not found`);
            return false;
        }

        // Check expiration
        if (flag.expiresAt && new Date() > flag.expiresAt) {
            return false;
        }

        // Check if explicitly disabled
        if (!flag.enabled) {
            return false;
        }

        // Check user targeting
        if (flag.targetUsers && userId && !flag.targetUsers.includes(userId)) {
            return false;
        }

        // Check rollout percentage
        if (flag.rolloutPercentage && !isInRollout(flag)) {
            return false;
        }

        return true;
    }, [flags, userId, isInRollout]);

    /**
     * Manually set a flag (for testing/debugging)
     */
    const setFlag = useCallback((flagName: string, enabled: boolean) => {
        setFlags((prev) => ({
            ...prev,
            [flagName]: {
                ...prev[flagName],
                name: flagName,
                enabled,
            },
        }));
    }, []);

    /**
     * Get flag details
     */
    const getFlag = useCallback((flagName: string): FeatureFlag | undefined => {
        return flags[flagName];
    }, [flags]);

    /**
     * Get all flags
     */
    const getAllFlags = useCallback((): Record<string, FeatureFlag> => {
        return flags;
    }, [flags]);

    /**
     * Refresh flags from API
     */
    const refreshFlags = useCallback(async () => {
        if (!apiEndpoint) return;

        try {
            const response = await fetch(apiEndpoint);
            const data = await response.json();
            setFlags((prev) => ({ ...prev, ...data.flags }));
        } catch (error) {
            console.error('Failed to fetch feature flags:', error);
        }
    }, [apiEndpoint]);

    /**
     * Initialize flags from API and localStorage
     */
    useEffect(() => {
        // Get user ID from localStorage or generate
        const storedUserId = localStorage.getItem('userId');
        if (storedUserId) {
            setUserId(storedUserId);
        } else {
            const newUserId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            localStorage.setItem('userId', newUserId);
            setUserId(newUserId);
        }

        // Load flags from localStorage (for offline support)
        const storedFlags = localStorage.getItem('featureFlags');
        if (storedFlags) {
            try {
                const parsed = JSON.parse(storedFlags);
                setFlags((prev) => ({ ...prev, ...parsed }));
            } catch (error) {
                console.error('Failed to parse stored feature flags:', error);
            }
        }

        // Fetch fresh flags from API
        refreshFlags();
    }, [refreshFlags]);

    /**
     * Save flags to localStorage when they change
     */
    useEffect(() => {
        localStorage.setItem('featureFlags', JSON.stringify(flags));
    }, [flags]);

    const value: FeatureFlagsContextValue = {
        isEnabled,
        setFlag,
        getFlag,
        getAllFlags,
        refreshFlags,
    };

    return (
        <FeatureFlagsContext.Provider value= { value } >
        { children }
        </FeatureFlagsContext.Provider>
  );
}

/**
 * useFeatureFlag Hook
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const isEnabled = useFeatureFlag('dark-mode');
 *   
 *   return (
 *     <div className={isEnabled ? 'dark' : 'light'}>
 *       {isEnabled && <DarkModeToggle />}
 *     </div>
 *   );
 * }
 * ```
 */
export function useFeatureFlag(flagName: string): boolean {
    const context = useContext(FeatureFlagsContext);

    if (!context) {
        console.warn('useFeatureFlag must be used within FeatureFlagsProvider');
        return false;
    }

    return context.isEnabled(flagName);
}

/**
 * useFeatureFlags Hook
 * 
 * Access all feature flag functions
 * 
 * @example
 * ```tsx
 * function AdminPanel() {
 *   const { getAllFlags, setFlag } = useFeatureFlags();
 *   
 *   return (
 *     <div>
 *       {Object.entries(getAllFlags()).map(([name, flag]) => (
 *         <Toggle
 *           key={name}
 *           checked={flag.enabled}
 *           onChange={(enabled) => setFlag(name, enabled)}
 *         />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useFeatureFlags(): FeatureFlagsContextValue {
    const context = useContext(FeatureFlagsContext);

    if (!context) {
        throw new Error('useFeatureFlags must be used within FeatureFlagsProvider');
    }

    return context;
}

/**
 * FeatureGate Component
 * 
 * Conditionally render children based on feature flag
 * 
 * @example
 * ```tsx
 * <FeatureGate flag="dark-mode">
 *   <DarkModeSettings />
 * </FeatureGate>
 * ```
 */
export function FeatureGate({
    flag,
    children,
    fallback = null,
}: {
    flag: string;
    children: React.ReactNode;
    fallback?: React.ReactNode;
}) {
    const isEnabled = useFeatureFlag(flag);
    return <>{ isEnabled? children: fallback } </>;
}
