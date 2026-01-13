/**
 * Utility functions for theme-aware styling
 */

/**
 * Returns theme-aware background color classes
 */
export const bgTheme = (light = 'bg-white', dark = 'bg-gray-800') => {
  return `${light} dark:${dark}`;
};

/**
 * Returns theme-aware text color classes
 */
export const textTheme = (light = 'text-gray-900', dark = 'text-gray-100') => {
  return `${light} dark:${dark}`;
};

/**
 * Returns theme-aware border color classes
 */
export const borderTheme = (light = 'border-gray-200', dark = 'border-gray-700') => {
  return `${light} dark:${dark}`;
};

/**
 * Returns theme-aware card styling classes
 */
export const cardTheme = () => {
  return 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100';
};

