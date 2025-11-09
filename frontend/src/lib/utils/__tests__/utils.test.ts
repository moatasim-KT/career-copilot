import {
    isValidUrl,
    isValidEmail,
    formatSalaryRange,
    getRelativeTime,
    getInitials,
    generateColor,
    groupBy,
    uniqueBy,
    sleep,
    truncateText,
    capitalizeFirst,
    formatDate,
    formatDateTime,
} from '../utils';

describe('Utils', () => {
    describe('isValidUrl', () => {
        it('should return true for valid URLs', () => {
            expect(isValidUrl('https://example.com')).toBe(true);
            expect(isValidUrl('http://example.com')).toBe(true);
            expect(isValidUrl('https://example.com/path')).toBe(true);
        });

        it('should return false for invalid URLs', () => {
            expect(isValidUrl('not-a-url')).toBe(false);
            expect(isValidUrl('example.com')).toBe(false);
            expect(isValidUrl('')).toBe(false);
        });
    });

    describe('isValidEmail', () => {
        it('should return true for valid emails', () => {
            expect(isValidEmail('test@example.com')).toBe(true);
            expect(isValidEmail('user.name@example.co.uk')).toBe(true);
        });

        it('should return false for invalid emails', () => {
            expect(isValidEmail('not-an-email')).toBe(false);
            expect(isValidEmail('test@')).toBe(false);
            expect(isValidEmail('@example.com')).toBe(false);
            expect(isValidEmail('')).toBe(false);
        });
    });

    describe('formatSalaryRange', () => {
        it('should format both min and max', () => {
            expect(formatSalaryRange(50000, 100000)).toBe('$50,000 - $100,000');
        });

        it('should handle only min value', () => {
            expect(formatSalaryRange(50000, undefined)).toBe('$50,000+');
        });

        it('should handle only max value', () => {
            expect(formatSalaryRange(undefined, 100000)).toBe('Up to $100,000');
        });

        it('should handle no values', () => {
            expect(formatSalaryRange(undefined, undefined)).toBe('Not specified');
        });
    });

    describe('getRelativeTime', () => {
        it('should return "Just now" for very recent dates', () => {
            const now = new Date();
            expect(getRelativeTime(now)).toBe('Just now');
        });

        it('should return minutes ago', () => {
            const date = new Date(Date.now() - 5 * 60 * 1000);
            expect(getRelativeTime(date)).toBe('5 minutes ago');
        });

        it('should return hours ago', () => {
            const date = new Date(Date.now() - 3 * 60 * 60 * 1000);
            expect(getRelativeTime(date)).toBe('3 hours ago');
        });

        it('should return days ago', () => {
            const date = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000);
            expect(getRelativeTime(date)).toBe('2 days ago');
        });
    });

    describe('getInitials', () => {
        it('should return initials for full name', () => {
            expect(getInitials('John Doe')).toBe('JD');
        });

        it('should return single initial for single name', () => {
            expect(getInitials('John')).toBe('J');
        });

        it('should return max 2 characters', () => {
            expect(getInitials('John Paul Doe')).toBe('JP');
        });

        it('should uppercase initials', () => {
            expect(getInitials('john doe')).toBe('JD');
        });
    });

    describe('generateColor', () => {
        it('should generate consistent color for same seed', () => {
            const color1 = generateColor('test');
            const color2 = generateColor('test');
            expect(color1).toBe(color2);
        });

        it('should generate different colors for different seeds', () => {
            const color1 = generateColor('test1');
            const color2 = generateColor('test2');
            expect(color1).not.toBe(color2);
        });

        it('should return hex color', () => {
            const color = generateColor('test');
            expect(color).toMatch(/^#[0-9a-f]{6}$/);
        });
    });

    describe('groupBy', () => {
        it('should group array by key', () => {
            const items = [
                { id: 1, category: 'A' },
                { id: 2, category: 'B' },
                { id: 3, category: 'A' },
            ];

            const grouped = groupBy(items, 'category');

            expect(grouped.A).toHaveLength(2);
            expect(grouped.B).toHaveLength(1);
        });

        it('should handle empty array', () => {
            const grouped = groupBy([], 'category');
            expect(grouped).toEqual({});
        });
    });

    describe('uniqueBy', () => {
        it('should remove duplicates by key', () => {
            const items = [
                { id: 1, name: 'A' },
                { id: 2, name: 'B' },
                { id: 1, name: 'C' },
            ];

            const unique = uniqueBy(items, 'id');

            expect(unique).toHaveLength(2);
            expect(unique[0].id).toBe(1);
            expect(unique[1].id).toBe(2);
        });

        it('should handle empty array', () => {
            const unique = uniqueBy([], 'id');
            expect(unique).toEqual([]);
        });
    });

    describe('sleep', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        it('should resolve after specified time', async () => {
            const promise = sleep(1000);

            jest.advanceTimersByTime(1000);

            await expect(promise).resolves.toBeUndefined();
        });
    });

    describe('truncateText', () => {
        it('should truncate text longer than max length', () => {
            expect(truncateText('Hello World', 5)).toBe('Hello...');
        });

        it('should not truncate text shorter than max length', () => {
            expect(truncateText('Hello', 10)).toBe('Hello');
        });

        it('should handle exact length', () => {
            expect(truncateText('Hello', 5)).toBe('Hello');
        });
    });

    describe('capitalizeFirst', () => {
        it('should capitalize first letter', () => {
            expect(capitalizeFirst('hello')).toBe('Hello');
        });

        it('should not change already capitalized string', () => {
            expect(capitalizeFirst('Hello')).toBe('Hello');
        });

        it('should handle single character', () => {
            expect(capitalizeFirst('h')).toBe('H');
        });
    });

    describe('formatDate', () => {
        it('should format date string', () => {
            const date = '2024-01-15';
            const formatted = formatDate(date);
            expect(formatted).toContain('Jan');
            expect(formatted).toContain('15');
            expect(formatted).toContain('2024');
        });

        it('should format Date object', () => {
            const date = new Date('2024-01-15');
            const formatted = formatDate(date);
            expect(formatted).toContain('Jan');
            expect(formatted).toContain('15');
            expect(formatted).toContain('2024');
        });
    });

    describe('formatDateTime', () => {
        it('should format date and time', () => {
            const date = '2024-01-15T14:30:00';
            const formatted = formatDateTime(date);
            expect(formatted).toContain('Jan');
            expect(formatted).toContain('15');
            expect(formatted).toContain('2024');
        });
    });
});
