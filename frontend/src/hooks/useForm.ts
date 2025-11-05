import { useState, useCallback } from 'react';

/**
 * Form state management hook with validation support
 * @template T - The type of the form data
 * @param initialValues - Initial form values
 * @returns Form state and handlers
 */
export function useForm<T extends Record<string, unknown>>(initialValues: T) {
    const [values, setValues] = useState<T>(initialValues);
    const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
    const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});

    /**
     * Handle input change
     */
    const handleChange = useCallback((name: keyof T, value: unknown) => {
        setValues((prev) => ({ ...prev, [name]: value }));
    }, []);

    /**
     * Handle input blur
     */
    const handleBlur = useCallback((name: keyof T) => {
        setTouched((prev) => ({ ...prev, [name]: true }));
    }, []);

    /**
     * Set a specific error
     */
    const setError = useCallback((name: keyof T, error: string) => {
        setErrors((prev) => ({ ...prev, [name]: error }));
    }, []);

    /**
     * Clear a specific error
     */
    const clearError = useCallback((name: keyof T) => {
        setErrors((prev) => {
            const newErrors = { ...prev };
            delete newErrors[name];
            return newErrors;
        });
    }, []);

    /**
     * Reset form to initial values
     */
    const reset = useCallback(() => {
        setValues(initialValues);
        setErrors({});
        setTouched({});
    }, [initialValues]);

    /**
     * Set all errors at once
     */
    const setAllErrors = useCallback((newErrors: Partial<Record<keyof T, string>>) => {
        setErrors(newErrors);
    }, []);

    return {
        values,
        errors,
        touched,
        handleChange,
        handleBlur,
        setError,
        clearError,
        setAllErrors,
        reset,
        setValues,
    };
}
