import React, { useEffect, useRef } from 'react';
import { Chart as ChartJS } from 'chart.js/auto';

const ChartComponent = ({ type, data, options, height = 280 }) => {
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    // For scatter charts, we don't need labels - only datasets
    // For other chart types, we need both labels and datasets
    const hasValidData = data && data.datasets && Array.isArray(data.datasets) && data.datasets.length > 0 && (
      type === 'scatter' || 
      (data.labels && Array.isArray(data.labels))
    );
    
    if (chartRef.current && hasValidData) {
      // Destroy previous chart instance
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }

      // Create new chart
      const ctx = chartRef.current.getContext('2d');
      chartInstanceRef.current = new ChartJS(ctx, {
        type: type,
        data: data,
        options: {
          ...options,
          responsive: options?.responsive !== undefined ? options.responsive : true,
          maintainAspectRatio: options?.maintainAspectRatio !== undefined ? options.maintainAspectRatio : false
        },
      });
    }
    

    // Cleanup on unmount
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [type, data, options]);

  return (
    <div style={{ position: 'relative', height: `${height}px`, width: '100%' }}>
      <canvas ref={chartRef} />
    </div>
  );
};

export default ChartComponent;
