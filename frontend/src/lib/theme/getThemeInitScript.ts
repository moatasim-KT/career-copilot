import { DARK_CLASS, THEME_STORAGE_KEY } from '@/lib/theme/constants';

/**
 * Returns an inline script that synchronizes the initial theme
 * before the React tree hydrates. Safe to call during SSR.
 */
export function getThemeInitScript(): string {
  return `
    (function() {
      try {
        var theme = localStorage.getItem('${THEME_STORAGE_KEY}') || 'system';
        var resolvedTheme = theme;

        if (theme === 'system') {
          resolvedTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }

        if (resolvedTheme === 'dark') {
          document.documentElement.classList.add('${DARK_CLASS}');
        }

        document.documentElement.style.colorScheme = resolvedTheme;
      } catch (e) {
        logger.error('Failed to initialize theme:', e);
      }
    })();
  `;
}
