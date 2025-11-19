import {
    getSourceBadgeColor,
    getMatchScoreColor,
    getApplicationStatusColor,
    getPriorityColor,
    getRemoteBadgeColor,
} from '../badges';

describe('Badge Utils', () => {
    describe('getSourceBadgeColor', () => {
        it('should return gray for manual', () => {
            expect(getSourceBadgeColor('manual')).toBe('bg-gray-100 text-gray-800');
        });

        it('should return blue for scraped', () => {
            expect(getSourceBadgeColor('scraped')).toBe('bg-blue-100 text-blue-800');
        });

        it('should return blue for linkedin', () => {
            expect(getSourceBadgeColor('linkedin')).toBe('bg-blue-100 text-blue-800');
        });

        it('should return green for indeed', () => {
            expect(getSourceBadgeColor('indeed')).toBe('bg-green-100 text-green-800');
        });

        it('should return purple for glassdoor', () => {
            expect(getSourceBadgeColor('glassdoor')).toBe('bg-purple-100 text-purple-800');
        });

        it('should return gray for unknown source', () => {
            expect(getSourceBadgeColor('unknown')).toBe('bg-gray-100 text-gray-800');
        });

        it('should be case insensitive', () => {
            expect(getSourceBadgeColor('MANUAL')).toBe('bg-gray-100 text-gray-800');
            expect(getSourceBadgeColor('LinkedIn')).toBe('bg-blue-100 text-blue-800');
        });
    });

    describe('getMatchScoreColor', () => {
        it('should return green for high scores', () => {
            expect(getMatchScoreColor(80)).toBe('text-green-600');
            expect(getMatchScoreColor(90)).toBe('text-green-600');
            expect(getMatchScoreColor(100)).toBe('text-green-600');
        });

        it('should return yellow for medium scores', () => {
            expect(getMatchScoreColor(60)).toBe('text-yellow-600');
            expect(getMatchScoreColor(70)).toBe('text-yellow-600');
            expect(getMatchScoreColor(79)).toBe('text-yellow-600');
        });

        it('should return red for low scores', () => {
            expect(getMatchScoreColor(0)).toBe('');
            expect(getMatchScoreColor(30)).toBe('text-red-600');
            expect(getMatchScoreColor(59)).toBe('text-red-600');
        });

        it('should return empty string for undefined', () => {
            expect(getMatchScoreColor(undefined)).toBe('');
        });
    });

    describe('getApplicationStatusColor', () => {
        it('should return blue for applied', () => {
            expect(getApplicationStatusColor('applied')).toBe('bg-blue-100 text-blue-800');
        });

        it('should return yellow for interviewing', () => {
            expect(getApplicationStatusColor('interviewing')).toBe('bg-yellow-100 text-yellow-800');
        });

        it('should return green for offer', () => {
            expect(getApplicationStatusColor('offer')).toBe('bg-green-100 text-green-800');
        });

        it('should return red for rejected', () => {
            expect(getApplicationStatusColor('rejected')).toBe('bg-red-100 text-red-800');
        });

        it('should return green for accepted', () => {
            expect(getApplicationStatusColor('accepted')).toBe('bg-green-100 text-green-800');
        });

        it('should return gray for withdrawn', () => {
            expect(getApplicationStatusColor('withdrawn')).toBe('bg-gray-100 text-gray-800');
        });

        it('should return gray for unknown status', () => {
            expect(getApplicationStatusColor('unknown')).toBe('bg-gray-100 text-gray-800');
        });

        it('should be case insensitive', () => {
            expect(getApplicationStatusColor('APPLIED')).toBe('bg-blue-100 text-blue-800');
            expect(getApplicationStatusColor('Interviewing')).toBe('bg-yellow-100 text-yellow-800');
        });
    });

    describe('getPriorityColor', () => {
        it('should return red for high priority', () => {
            expect(getPriorityColor('high')).toBe('bg-red-100 text-red-800');
        });

        it('should return yellow for medium priority', () => {
            expect(getPriorityColor('medium')).toBe('bg-yellow-100 text-yellow-800');
        });

        it('should return green for low priority', () => {
            expect(getPriorityColor('low')).toBe('bg-green-100 text-green-800');
        });

        it('should return gray for unknown priority', () => {
            expect(getPriorityColor('unknown')).toBe('bg-gray-100 text-gray-800');
        });

        it('should be case insensitive', () => {
            expect(getPriorityColor('HIGH')).toBe('bg-red-100 text-red-800');
            expect(getPriorityColor('Medium')).toBe('bg-yellow-100 text-yellow-800');
        });
    });

    describe('getRemoteBadgeColor', () => {
        it('should return green for remote', () => {
            expect(getRemoteBadgeColor(true)).toBe('bg-green-100 text-green-800');
        });

        it('should return gray for not remote', () => {
            expect(getRemoteBadgeColor(false)).toBe('bg-gray-100 text-gray-800');
        });
    });
});
