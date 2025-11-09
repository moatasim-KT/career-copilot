/**
 * Get badge color classes based on job source
 * @param source - Job source string
 * @returns Tailwind CSS classes for badge styling
 */
export function getSourceBadgeColor(source: string): string {
    switch (source.toLowerCase()) {
        case 'manual':
            return 'bg-gray-100 text-gray-800';
        case 'scraped':
            return 'bg-blue-100 text-blue-800';
        case 'linkedin':
            return 'bg-blue-100 text-blue-800';
        case 'indeed':
            return 'bg-green-100 text-green-800';
        case 'glassdoor':
            return 'bg-purple-100 text-purple-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

/**
 * Get color classes based on match score
 * @param score - Match score percentage
 * @returns Tailwind CSS text color class
 */
export function getMatchScoreColor(score?: number): string {
    if (!score) return '';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
}

/**
 * Get application status badge color
 * @param status - Application status
 * @returns Tailwind CSS classes for badge styling
 */
export function getApplicationStatusColor(status: string): string {
    switch (status.toLowerCase()) {
        case 'applied':
            return 'bg-blue-100 text-blue-800';
        case 'interviewing':
            return 'bg-yellow-100 text-yellow-800';
        case 'offer':
            return 'bg-green-100 text-green-800';
        case 'rejected':
            return 'bg-red-100 text-red-800';
        case 'accepted':
            return 'bg-green-100 text-green-800';
        case 'withdrawn':
            return 'bg-gray-100 text-gray-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

/**
 * Get priority level color
 * @param priority - Priority level
 * @returns Tailwind CSS classes for badge styling
 */
export function getPriorityColor(priority: string): string {
    switch (priority.toLowerCase()) {
        case 'high':
            return 'bg-red-100 text-red-800';
        case 'medium':
            return 'bg-yellow-100 text-yellow-800';
        case 'low':
            return 'bg-green-100 text-green-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

/**
 * Get remote work badge color
 * @param isRemote - Whether job is remote
 * @returns Tailwind CSS classes for badge styling
 */
export function getRemoteBadgeColor(isRemote: boolean): string {
    return isRemote ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
}
