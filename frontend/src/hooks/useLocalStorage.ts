import { useState, useEffect } from 'react';

import { logger } from '@/lib/logger';


/**
 * Local storage hook with JSON serialization
 * @param key - Storage key
 * @param initialValue - Initial value if key doesn't exist
 * @returns [storedValue, setValue] tuple
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((val: T) => T)) => void] {
    // Get initial value from localStorage or use initialValue
    const [storedValue, setStoredValue] = useState<T>(() => {
        if (typeof window === 'undefined') {
            return initialValue;
        }

        try {
            const item = window.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            logger.error(`Error reading localStorage key "${key}":`, error);
            return initialValue;
        }
    });

    // Update localStorage when value changes
    useEffect(() => {
        if (typeof window === 'undefined') {
            return;
        }

        try {
            window.localStorage.setItem(key, JSON.stringify(storedValue));
        } catch (error) {
            logger.error(`Error setting localStorage key "${key}":`, error);
        }
    }, [key, storedValue]);

    // Wrapper to handle both direct values and updater functions
    const setValue = (value: T | ((val: T) => T)) => {
        try {
            const valueToStore = value instanceof Function ? value(storedValue) : value;
            setStoredValue(valueToStore);
        } catch (error) {
            logger.error(`Error updating state for key "${key}":`, error);
        }
    };

    return [storedValue, setValue];
}
