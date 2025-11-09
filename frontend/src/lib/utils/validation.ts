/**
 * Form validation utilities
 */

export type ValidationRule<T> = {
    validate: (value: T) => boolean;
    message: string;
};

export type ValidationRules<T> = {
    [K in keyof T]?: ValidationRule<T[K]>[];
};

/**
 * Validate a single field against rules
 * @param value - Value to validate
 * @param rules - Array of validation rules
 * @returns Error message or null if valid
 */
export function validateField<T>(value: T, rules?: ValidationRule<T>[]): string | null {
    if (!rules) return null;

    for (const rule of rules) {
        if (!rule.validate(value)) {
            return rule.message;
        }
    }

    return null;
}

/**
 * Validate all fields in a form
 * @param values - Form values
 * @param rules - Validation rules for each field
 * @returns Object with errors for each field
 */
export function validateForm<T extends Record<string, unknown>>(
    values: T,
    rules: ValidationRules<T>,
): Partial<Record<keyof T, string>> {
    const errors: Partial<Record<keyof T, string>> = {};

    for (const key in rules) {
        const fieldRules = rules[key];
        const error = validateField(values[key], fieldRules);
        if (error) {
            errors[key] = error;
        }
    }

    return errors;
}

// Common validation rules
export const required = <T>(message = 'This field is required'): ValidationRule<T> => ({
    validate: (value) => {
        if (typeof value === 'string') return value.trim().length > 0;
        if (Array.isArray(value)) return value.length > 0;
        return value !== null && value !== undefined;
    },
    message,
});

export const minLength = (min: number, message?: string): ValidationRule<string> => ({
    validate: (value) => value.length >= min,
    message: message || `Must be at least ${min} characters`,
});

export const maxLength = (max: number, message?: string): ValidationRule<string> => ({
    validate: (value) => value.length <= max,
    message: message || `Must be at most ${max} characters`,
});

export const email = (message = 'Invalid email address'): ValidationRule<string> => ({
    validate: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
    message,
});

export const url = (message = 'Invalid URL'): ValidationRule<string> => ({
    validate: (value) => {
        try {
            new URL(value);
            return true;
        } catch {
            return false;
        }
    },
    message,
});

export const pattern = (regex: RegExp, message: string): ValidationRule<string> => ({
    validate: (value) => regex.test(value),
    message,
});

export const min = (minValue: number, message?: string): ValidationRule<number> => ({
    validate: (value) => value >= minValue,
    message: message || `Must be at least ${minValue}`,
});

export const max = (maxValue: number, message?: string): ValidationRule<number> => ({
    validate: (value) => value <= maxValue,
    message: message || `Must be at most ${maxValue}`,
});

export const oneOf = <T>(values: T[], message?: string): ValidationRule<T> => ({
    validate: (value) => values.includes(value),
    message: message || `Must be one of: ${values.join(', ')}`,
});
