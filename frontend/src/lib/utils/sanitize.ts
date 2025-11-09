/**
 * Input sanitization utilities
 */

export const sanitizeInput = (input: string): string => {
	return input
		.replace(/[<>]/g, '')
		.replace(/javascript:/gi, '')
		.replace(/on\w+=/gi, '')
		.trim();
};

export const sanitizeHTML = (html: string): string => {
	const div = document.createElement('div');
	div.textContent = html;
	return div.innerHTML;
};

export const sanitizeUrl = (url: string): string => {
	try {
		const parsed = new URL(url);
		if (!['http:', 'https:'].includes(parsed.protocol)) {
			return '';
		}
		return url;
	} catch {
		return '';
	}
};
