import {
    validateField,
    validateForm,
    required,
    minLength,
    maxLength,
    email,
    url,
    pattern,
    min,
    max,
    oneOf,
} from '../validation';

describe('Validation', () => {
    describe('validateField', () => {
        it('should return null for valid field', () => {
            const rules = [required()];
            expect(validateField('test', rules)).toBeNull();
        });

        it('should return error message for invalid field', () => {
            const rules = [required()];
            expect(validateField('', rules)).toBe('This field is required');
        });

        it('should return null when no rules provided', () => {
            expect(validateField('test', undefined)).toBeNull();
        });

        it('should return first error when multiple rules fail', () => {
            const rules = [required(), minLength(5)];
            expect(validateField('', rules)).toBe('This field is required');
        });
    });

    describe('validateForm', () => {
        it('should validate all fields', () => {
            const values = {
                email: '',
                password: 'abc',
            };

            const rules = {
                email: [required(), email()],
                password: [required(), minLength(8)],
            };

            const errors = validateForm(values, rules);

            expect(errors.email).toBe('This field is required');
            expect(errors.password).toBe('Must be at least 8 characters');
        });

        it('should return empty object for valid form', () => {
            const values = {
                email: 'test@example.com',
                password: 'password123',
            };

            const rules = {
                email: [required(), email()],
                password: [required(), minLength(8)],
            };

            const errors = validateForm(values, rules);

            expect(errors).toEqual({});
        });
    });

    describe('required', () => {
        it('should validate non-empty string', () => {
            const rule = required();
            expect(rule.validate('test')).toBe(true);
        });

        it('should fail for empty string', () => {
            const rule = required();
            expect(rule.validate('')).toBe(false);
        });

        it('should fail for whitespace-only string', () => {
            const rule = required();
            expect(rule.validate('   ')).toBe(false);
        });

        it('should validate non-empty array', () => {
            const rule = required<string[]>();
            expect(rule.validate(['item'])).toBe(true);
        });

        it('should fail for empty array', () => {
            const rule = required<string[]>();
            expect(rule.validate([])).toBe(false);
        });

        it('should fail for null or undefined', () => {
            const rule = required<string | null | undefined>();
            expect(rule.validate(null)).toBe(false);
            expect(rule.validate(undefined)).toBe(false);
        });

        it('should use custom message', () => {
            const rule = required('Custom message');
            expect(rule.message).toBe('Custom message');
        });
    });

    describe('minLength', () => {
        it('should validate string meeting minimum length', () => {
            const rule = minLength(5);
            expect(rule.validate('hello')).toBe(true);
            expect(rule.validate('hello world')).toBe(true);
        });

        it('should fail for string below minimum length', () => {
            const rule = minLength(5);
            expect(rule.validate('hi')).toBe(false);
        });

        it('should use custom message', () => {
            const rule = minLength(5, 'Too short');
            expect(rule.message).toBe('Too short');
        });
    });

    describe('maxLength', () => {
        it('should validate string within maximum length', () => {
            const rule = maxLength(10);
            expect(rule.validate('hello')).toBe(true);
        });

        it('should fail for string exceeding maximum length', () => {
            const rule = maxLength(5);
            expect(rule.validate('hello world')).toBe(false);
        });

        it('should use custom message', () => {
            const rule = maxLength(5, 'Too long');
            expect(rule.message).toBe('Too long');
        });
    });

    describe('email', () => {
        it('should validate correct email format', () => {
            const rule = email();
            expect(rule.validate('test@example.com')).toBe(true);
            expect(rule.validate('user.name@example.co.uk')).toBe(true);
        });

        it('should fail for incorrect email format', () => {
            const rule = email();
            expect(rule.validate('not-an-email')).toBe(false);
            expect(rule.validate('test@')).toBe(false);
            expect(rule.validate('@example.com')).toBe(false);
        });

        it('should use custom message', () => {
            const rule = email('Custom email error');
            expect(rule.message).toBe('Custom email error');
        });
    });

    describe('url', () => {
        it('should validate correct URL format', () => {
            const rule = url();
            expect(rule.validate('https://example.com')).toBe(true);
            expect(rule.validate('http://example.com')).toBe(true);
        });

        it('should fail for incorrect URL format', () => {
            const rule = url();
            expect(rule.validate('not-a-url')).toBe(false);
            expect(rule.validate('example.com')).toBe(false);
        });

        it('should use custom message', () => {
            const rule = url('Custom URL error');
            expect(rule.message).toBe('Custom URL error');
        });
    });

    describe('pattern', () => {
        it('should validate matching pattern', () => {
            const rule = pattern(/^\d{3}-\d{3}-\d{4}$/, 'Invalid phone');
            expect(rule.validate('123-456-7890')).toBe(true);
        });

        it('should fail for non-matching pattern', () => {
            const rule = pattern(/^\d{3}-\d{3}-\d{4}$/, 'Invalid phone');
            expect(rule.validate('1234567890')).toBe(false);
        });
    });

    describe('min', () => {
        it('should validate number meeting minimum', () => {
            const rule = min(5);
            expect(rule.validate(5)).toBe(true);
            expect(rule.validate(10)).toBe(true);
        });

        it('should fail for number below minimum', () => {
            const rule = min(5);
            expect(rule.validate(3)).toBe(false);
        });

        it('should use custom message', () => {
            const rule = min(5, 'Too small');
            expect(rule.message).toBe('Too small');
        });
    });

    describe('max', () => {
        it('should validate number within maximum', () => {
            const rule = max(10);
            expect(rule.validate(5)).toBe(true);
            expect(rule.validate(10)).toBe(true);
        });

        it('should fail for number exceeding maximum', () => {
            const rule = max(10);
            expect(rule.validate(15)).toBe(false);
        });

        it('should use custom message', () => {
            const rule = max(10, 'Too large');
            expect(rule.message).toBe('Too large');
        });
    });

    describe('oneOf', () => {
        it('should validate value in list', () => {
            const rule = oneOf(['A', 'B', 'C']);
            expect(rule.validate('A')).toBe(true);
            expect(rule.validate('B')).toBe(true);
        });

        it('should fail for value not in list', () => {
            const rule = oneOf(['A', 'B', 'C']);
            expect(rule.validate('D')).toBe(false);
        });

        it('should use custom message', () => {
            const rule = oneOf(['A', 'B'], 'Must be A or B');
            expect(rule.message).toBe('Must be A or B');
        });
    });
});
