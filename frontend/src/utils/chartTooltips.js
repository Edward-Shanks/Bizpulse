/**
 * Chart tooltip utilities
 * Ensures tooltips always show values, even when very small
 */
import { formatNumber, formatUnits } from './formatters';

/**
 * Get enhanced tooltip configuration for Chart.js
 * Always shows values, even when very small
 */
export const getEnhancedTooltipConfig = (options = {}) => {
  const {
    labelPrefix = '',
    showExactValue = true,
    formatValue = formatNumber,
    showPercentage = false,
    unit = '',
  } = options;

  return {
    enabled: true,
    displayColors: true,
    intersect: false,
    mode: 'index',
    callbacks: {
      title: (context) => {
        return context[0]?.label || '';
      },
      label: (context) => {
        const value = context.parsed.y !== undefined ? context.parsed.y : 
                     context.parsed.x !== undefined ? context.parsed.x : 
                     context.parsed || 0;
        
        let label = labelPrefix || context.dataset?.label || '';
        if (label && !label.endsWith(':')) label += ':';
        
        const formattedValue = formatValue(value);
        let result = label ? `${label} ${formattedValue}` : formattedValue;
        
        if (unit) {
          result += ` ${unit}`;
        }
        
        // Add percentage for pie charts
        if (showPercentage && context.dataset?.data) {
          const total = context.dataset.data.reduce((a, b) => a + (b || 0), 0);
          if (total > 0) {
            const percentage = ((value / total) * 100).toFixed(1);
            result += ` (${percentage}%)`;
          }
        }
        
        return result;
      },
      afterLabel: (context) => {
        if (!showExactValue) return '';
        
        const value = context.parsed.y !== undefined ? context.parsed.y : 
                     context.parsed.x !== undefined ? context.parsed.x : 
                     context.parsed || 0;
        
        // Show exact value for very small numbers (less than 1)
        if (value > 0 && value < 1) {
          return `Exact: €${value.toFixed(4)}`;
        }
        
        // Show exact value if formatted value shows 0 but actual value is > 0
        const formatted = formatValue(value);
        if (formatted === '€0' || formatted === '€0k' || formatted === '€0M') {
          if (value > 0) {
            return `Exact: €${value.toFixed(4)}`;
          }
        }
        
        return '';
      },
    },
    padding: 8,
    titleFont: { size: 12, weight: 'bold' },
    bodyFont: { size: 11 },
    footerFont: { size: 10 },
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    titleColor: '#fff',
    bodyColor: '#fff',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
  };
};

/**
 * Get tooltip config for revenue charts
 */
export const getRevenueTooltipConfig = () => {
  return getEnhancedTooltipConfig({
    labelPrefix: 'Revenue',
    formatValue: formatNumber,
  });
};

/**
 * Get tooltip config for profit charts
 */
export const getProfitTooltipConfig = () => {
  return getEnhancedTooltipConfig({
    labelPrefix: 'Profit',
    formatValue: formatNumber,
  });
};

/**
 * Get tooltip config for units/cases charts
 */
export const getUnitsTooltipConfig = () => {
  return getEnhancedTooltipConfig({
    labelPrefix: 'Cases',
    formatValue: formatUnits,
    unit: 'cases',
  });
};

/**
 * Get tooltip config for pie charts (with percentage)
 */
export const getPieTooltipConfig = () => {
  return getEnhancedTooltipConfig({
    showPercentage: true,
    formatValue: formatNumber,
  });
};

