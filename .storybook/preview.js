import '../frontend/src/app/globals.css';
import { themes } from '@storybook/theming';

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: { expanded: true },
  darkMode: {
    dark: { ...themes.dark, appBg: '#0f172a' },
    light: { ...themes.normal, appBg: '#fff' },
    current: 'light',
  },
  backgrounds: {
    default: 'light',
    values: [
      { name: 'light', value: '#fff' },
      { name: 'dark', value: '#0f172a' },
    ],
  },
};
