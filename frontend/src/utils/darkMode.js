/**
 * Utility function to add dark mode classes to common text/background patterns
 * This helps maintain consistency across all pages
 */

export const addDarkModeClasses = (className) => {
  if (!className) return '';
  
  // Common patterns and their dark mode equivalents
  const patterns = {
    'text-gray-900': 'text-gray-900 dark:text-gray-100',
    'text-gray-800': 'text-gray-800 dark:text-gray-200',
    'text-gray-700': 'text-gray-700 dark:text-gray-300',
    'text-gray-600': 'text-gray-600 dark:text-gray-400',
    'text-gray-500': 'text-gray-500 dark:text-gray-400',
    'text-gray-400': 'text-gray-400 dark:text-gray-500',
    'bg-white': 'bg-white dark:bg-gray-800',
    'bg-gray-50': 'bg-gray-50 dark:bg-gray-900',
    'bg-gray-100': 'bg-gray-100 dark:bg-gray-700',
    'border-gray-200': 'border-gray-200 dark:border-gray-700',
    'border-gray-300': 'border-gray-300 dark:border-gray-600',
  };
  
  let result = className;
  Object.keys(patterns).forEach(pattern => {
    // Only replace if pattern exists as a whole word (not part of another class)
    const regex = new RegExp(`\\b${pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g');
    if (result.includes(pattern)) {
      // Check if dark mode version already exists
      if (!result.includes(`dark:${pattern.split('-')[1]}`)) {
        result = result.replace(regex, patterns[pattern]);
      }
    }
  });
  
  return result;
};

/**
 * Helper function to apply dark mode to common component patterns
 */
export const darkModeText = {
  primary: 'text-gray-900 dark:text-gray-100',
  secondary: 'text-gray-600 dark:text-gray-400',
  muted: 'text-gray-500 dark:text-gray-400',
  heading: 'text-gray-900 dark:text-gray-100',
  body: 'text-gray-700 dark:text-gray-300',
};

export const darkModeBg = {
  card: 'bg-white dark:bg-gray-800',
  page: 'bg-gray-50 dark:bg-gray-900',
  hover: 'hover:bg-gray-50 dark:hover:bg-gray-700',
  border: 'border-gray-200 dark:border-gray-700',
};

