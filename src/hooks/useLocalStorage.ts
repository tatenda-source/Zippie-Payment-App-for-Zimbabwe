/**
 * Custom hook for localStorage with type safety and error handling
 */

import { useState, useEffect, useCallback } from 'react';
import { logger } from '../utils/logger';

/**
 * Hook for syncing state with localStorage
 * @param key - localStorage key
 * @param initialValue - Initial value if key doesn't exist
 * @returns [value, setValue, removeValue]
 */
export function useLocalStorage<T>(
    key: string,
    initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
    // Get from localStorage or use initial value
    const [storedValue, setStoredValue] = useState<T>(() => {
        try {
            const item = window.localStorage.getItem(key);
            return item ? (JSON.parse(item) as T) : initialValue;
        } catch (error) {
            logger.error(`Error reading localStorage key "${key}":`, error);
            return initialValue;
        }
    });

    // Update localStorage when state changes
    const setValue = useCallback(
        (value: T | ((prev: T) => T)) => {
            try {
                // Allow value to be a function so we have same API as useState
                const valueToStore = value instanceof Function ? value(storedValue) : value;

                setStoredValue(valueToStore);
                window.localStorage.setItem(key, JSON.stringify(valueToStore));
            } catch (error) {
                logger.error(`Error setting localStorage key "${key}":`, error);
            }
        },
        [key, storedValue]
    );

    // Remove from localStorage
    const removeValue = useCallback(() => {
        try {
            window.localStorage.removeItem(key);
            setStoredValue(initialValue);
        } catch (error) {
            logger.error(`Error removing localStorage key "${key}":`, error);
        }
    }, [key, initialValue]);

    // Listen for changes from other tabs/windows
    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === key && e.newValue !== null) {
                try {
                    setStoredValue(JSON.parse(e.newValue) as T);
                } catch (error) {
                    logger.error(`Error parsing storage event for key "${key}":`, error);
                }
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, [key]);

    return [storedValue, setValue, removeValue];
}
