// Format number to thousands with 'k' suffix
export const formatNumber = (value) => {
  if (!value && value !== 0) return '€0';
  
  const num = parseFloat(value);
  
  if (num >= 1000000) {
    return `€${(num / 1000000).toFixed(1)}M`;
  } else if (num >= 1000) {
    return `€${(num / 1000).toFixed(1)}k`;
  }
  return `€${num.toFixed(0)}`;
};

// Format cases (previously called units) without currency symbol
export const formatUnits = (value) => {
  if (!value && value !== 0) return '0';
  
  const num = parseFloat(value);
  
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}k`;
  }
  return num.toFixed(0);
};

// Format number with thousand separators
export const formatCurrency = (value) => {
  if (!value && value !== 0) return '€0';
  return `€${parseFloat(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
};

// For chart tooltips
export const formatChartValue = (value) => {
  if (!value && value !== 0) return '€0';
  
  const num = parseFloat(value);
  
  if (num >= 1000000) {
    return `€${(num / 1000000).toFixed(2)}M`;
  } else if (num >= 1000) {
    return `€${(num / 1000).toFixed(1)}k`;
  }
  return `€${num.toFixed(0)}`;
};
