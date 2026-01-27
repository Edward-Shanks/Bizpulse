import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import ChartComponent from '@/components/ChartComponent';
import { formatNumber } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { useTheme } from '@/contexts/ThemeContext';
import { 
  TrendingUp, TrendingDown, Euro,
  Calendar, BarChart3, Activity
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

const ExecutiveView = () => {
  const { theme } = useTheme();
  const [salesData, setSalesData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  
  // Page-level multi-select filters
  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedBrands, setSelectedBrands] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);

  const { token } = useAuth();

  // Fetch filter options
  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const response = await axios.get(`${API}/filters/options`);
        setFilters(response.data);
      } catch (error) {
        console.error('Error fetching filters:', error);
      }
    };
    fetchFilters();
  }, []);

  // Fetch sales data
  useEffect(() => {
    const fetchSalesData = async () => {
      setLoading(true);
      try {
        const params = {};
        
        if (selectedYears.length > 0) params.years = selectedYears.join(',');
        if (selectedMonths.length > 0) params.months = selectedMonths.join(',');
        if (selectedBusinesses.length > 0) params.businesses = selectedBusinesses.join(',');
        if (selectedBrands.length > 0) params.brands = selectedBrands.join(',');
        if (selectedChannels.length > 0) params.channels = selectedChannels.join(',');

        const response = await axios.get(`${API}/analytics/sales-by-month`, { params });
        setSalesData(response.data);
      } catch (error) {
        console.error('Error fetching sales data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSalesData();
  }, [selectedYears, selectedMonths, selectedBusinesses, selectedBrands, selectedChannels]);

  // Calculate summary metrics
  const calculateMetrics = () => {
    if (!salesData || !salesData.data || salesData.data.length === 0) {
      return {
        totalSales: 0,
        avgMonthlySales: 0,
        highestMonth: 'N/A',
        highestSales: 0,
        growth: 0
      };
    }

    const data = salesData.data;
    const totalSales = data.reduce((sum, item) => sum + (item.revenue || 0), 0);
    const avgMonthlySales = totalSales / data.length;
    
    const highestEntry = data.reduce((max, item) => 
      (item.revenue || 0) > (max.revenue || 0) ? item : max
    , data[0]);
    
    // Calculate growth (compare first and last data points)
    const firstValue = data[0]?.revenue || 0;
    const lastValue = data[data.length - 1]?.revenue || 0;
    const growth = firstValue > 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;

    return {
      totalSales,
      avgMonthlySales,
      highestMonth: `${highestEntry.month_name || ''} ${highestEntry.year || ''}`,
      highestSales: highestEntry.revenue || 0,
      growth
    };
  };

  const metrics = calculateMetrics();

  // Prepare chart data
  const prepareChartData = () => {
    if (!salesData || !salesData.data || salesData.data.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }

    // Sort data by year and month
    const sortedData = [...salesData.data].sort((a, b) => {
      if (a.year !== b.year) return a.year - b.year;
      const monthOrder = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return monthOrder.indexOf(a.month_name) - monthOrder.indexOf(b.month_name);
    });

    const labels = sortedData.map(item => `${item.month_name} ${item.year}`);
    const revenueData = sortedData.map(item => item.revenue || 0);

    return {
      labels,
      datasets: [
        {
          label: 'Gross Sales (€)',
          data: revenueData,
          borderColor: '#ef4444', // Red color similar to screenshot
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#ef4444',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        }
      ]
    };
  };

  const chartData = prepareChartData();

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: theme === 'dark' ? '#e5e7eb' : '#1f2937',
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            weight: 'bold'
          }
        }
      },
      tooltip: {
        enabled: true,
        backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
        titleColor: theme === 'dark' ? '#fff' : '#1f2937',
        bodyColor: theme === 'dark' ? '#e5e7eb' : '#4b5563',
        borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${formatNumber(context.parsed.y)}`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: true,
          color: theme === 'dark' ? '#374151' : '#e5e7eb',
          drawBorder: false,
        },
        ticks: {
          color: theme === 'dark' ? '#9ca3af' : '#6b7280',
          maxRotation: 45,
          minRotation: 45,
          font: {
            size: 10
          }
        },
        title: {
          display: true,
          text: 'Month Year',
          color: theme === 'dark' ? '#e5e7eb' : '#1f2937',
          font: {
            size: 12,
            weight: 'bold'
          }
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          display: true,
          color: theme === 'dark' ? '#374151' : '#e5e7eb',
          drawBorder: false,
        },
        ticks: {
          color: theme === 'dark' ? '#9ca3af' : '#6b7280',
          callback: function(value) {
            return '€' + (value >= 1000000 ? (value / 1000000).toFixed(1) + 'M' : 
                          value >= 1000 ? (value / 1000).toFixed(0) + 'K' : 
                          value.toFixed(0));
          },
          font: {
            size: 11
          }
        },
        title: {
          display: true,
          text: 'Gross Sales (€)',
          color: theme === 'dark' ? '#e5e7eb' : '#1f2937',
          font: {
            size: 12,
            weight: 'bold'
          }
        }
      }
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Executive</h1>
            <p className="text-gray-600 dark:text-gray-400">High-level overview of gross sales performance over time</p>
          </div>
        </div>

        {/* Filters */}
        <div 
          className="rounded-lg p-5"
          style={theme === 'dark' 
            ? {
                background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }
            : {
                background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                border: '1px solid rgba(0, 0, 0, 0.1)'
              }
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {filters && (
              <>
                <MultiSelectFilter
                  label="Year"
                  options={filters.years || []}
                  selectedValues={selectedYears}
                  onChange={setSelectedYears}
                  placeholder="All Years"
                />
                <MultiSelectFilter
                  label="Month"
                  options={filters.months || []}
                  selectedValues={selectedMonths}
                  onChange={setSelectedMonths}
                  placeholder="All Months"
                />
                <MultiSelectFilter
                  label="Business"
                  options={filters.businesses || []}
                  selectedValues={selectedBusinesses}
                  onChange={setSelectedBusinesses}
                  placeholder="All Businesses"
                />
                <MultiSelectFilter
                  label="Brand"
                  options={filters.brands || []}
                  selectedValues={selectedBrands}
                  onChange={setSelectedBrands}
                  placeholder="All Brands"
                />
                <MultiSelectFilter
                  label="Channel"
                  options={filters.channels || []}
                  selectedValues={selectedChannels}
                  onChange={setSelectedChannels}
                  placeholder="All Channels"
                />
              </>
            )}
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-3">
          {/* Total Sales */}
          <div 
            className="rounded-lg p-4"
            style={theme === 'dark' 
              ? {
                  background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }
              : {
                  background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                  border: '1px solid rgba(0, 0, 0, 0.1)'
                }
            }
          >
            <div className="flex items-center gap-2 mb-2">
              <Euro className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Total Sales</span>
            </div>
            {loading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                {formatNumber(metrics.totalSales)}
              </p>
            )}
          </div>

          {/* Average Monthly Sales */}
          <div 
            className="rounded-lg p-4"
            style={theme === 'dark' 
              ? {
                  background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }
              : {
                  background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                  border: '1px solid rgba(0, 0, 0, 0.1)'
                }
            }
          >
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-green-600" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Avg Monthly Sales</span>
            </div>
            {loading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                {formatNumber(metrics.avgMonthlySales)}
              </p>
            )}
          </div>

          {/* Highest Month */}
          <div 
            className="rounded-lg p-4"
            style={theme === 'dark' 
              ? {
                  background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }
              : {
                  background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                  border: '1px solid rgba(0, 0, 0, 0.1)'
                }
            }
          >
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-4 h-4 text-purple-600" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Highest Month</span>
            </div>
            {loading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <>
                <p className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
                  {metrics.highestMonth}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {formatNumber(metrics.highestSales)}
                </p>
              </>
            )}
          </div>

          {/* Growth Rate */}
          <div 
            className="rounded-lg p-4"
            style={theme === 'dark' 
              ? {
                  background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }
              : {
                  background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                  border: '1px solid rgba(0, 0, 0, 0.1)'
                }
            }
          >
            <div className="flex items-center gap-2 mb-2">
              {metrics.growth >= 0 ? (
                <TrendingUp className="w-4 h-4 text-green-600" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-600" />
              )}
              <span className="text-xs text-gray-600 dark:text-gray-400">Growth Rate</span>
            </div>
            {loading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                  {metrics.growth >= 0 ? '+' : ''}{metrics.growth.toFixed(2)}%
                </p>
                <p className={`text-xs flex items-center gap-1 ${metrics.growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {metrics.growth >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  Period Trend
                </p>
              </>
            )}
          </div>
        </div>

        {/* Gross Sales Chart */}
        <div 
          className="rounded-lg p-6"
          style={theme === 'dark' 
            ? {
                background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }
            : {
                background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                border: '1px solid rgba(0, 0, 0, 0.1)'
              }
          }
        >
          <div className="mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Gross Sales by Month Year
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Track gross sales performance over time
            </p>
          </div>
          
          {loading ? (
            <div className="flex items-center justify-center" style={{ height: '400px' }}>
              <Skeleton className="w-full h-full" />
            </div>
          ) : chartData.labels.length === 0 ? (
            <div className="flex items-center justify-center" style={{ height: '400px' }}>
              <div className="text-center">
                <Activity className={`w-12 h-12 mx-auto mb-2 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                  No data available for the selected filters
                </p>
              </div>
            </div>
          ) : (
            <ChartComponent
              type="line"
              data={chartData}
              options={chartOptions}
              height={400}
            />
          )}
        </div>
      </div>
    </Layout>
  );
};

export default ExecutiveView;
