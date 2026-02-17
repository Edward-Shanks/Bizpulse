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
  Calendar, BarChart3, Activity, Users,
  AlertTriangle, ShoppingBag, DollarSign, Percent, Target
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

const ExecutiveView = () => {
  const { theme } = useTheme();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [activeTab, setActiveTab] = useState('customers');
  
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

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        const params = {};
        
        if (selectedYears.length > 0) params.years = selectedYears.join(',');
        if (selectedMonths.length > 0) params.months = selectedMonths.join(',');
        if (selectedBusinesses.length > 0) params.businesses = selectedBusinesses.join(',');
        if (selectedBrands.length > 0) params.brands = selectedBrands.join(',');
        if (selectedChannels.length > 0) params.channels = selectedChannels.join(',');

        const response = await axios.get(`${API}/analytics/executive-dashboard`, { params });
        setDashboardData(response.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [selectedYears, selectedMonths, selectedBusinesses, selectedBrands, selectedChannels]);

  // Get summary metrics from dashboard data
  const summary = dashboardData?.summary || {
    gross_sales: 0,
    gross_profit: 0,
    transfer_cost: 0,
    margin_pct: 0
  };

  // Prepare chart data
  const prepareChartData = () => {
    if (!dashboardData || !dashboardData.monthly_trend || dashboardData.monthly_trend.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }

    const monthlyData = dashboardData.monthly_trend;
    const labels = monthlyData.map(item => `${item.month} ${item.year}`);
    const revenueData = monthlyData.map(item => item.revenue || 0);
    const profitData = monthlyData.map(item => item.profit || 0);

    return {
      labels,
      datasets: [
        {
          type: 'bar',
          label: 'Gross Sales (€)',
          data: revenueData,
          backgroundColor: theme === 'dark' ? '#60a5fa' : '#1e293b',
          borderRadius: 6,
          order: 2,
        },
        {
          type: 'line',
          label: 'Gross Profit (€)',
          data: profitData,
          borderColor: '#EDD5B1',
          backgroundColor: 'rgba(237, 213, 177, 0.1)',
          borderWidth: 3,
          fill: false,
          tension: 0.4,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: '#EDD5B1',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          order: 1,
        }
      ]
    };
  };

  const chartData = prepareChartData();
  
  // Get top contributors based on active tab
  const getTopContributors = () => {
    if (!dashboardData || !dashboardData.top_contributors) return [];
    return dashboardData.top_contributors[activeTab] || [];
  };

  // Prepare chart data for Top 10 charts (both as bar charts)
  const prepareTop10ChartData = (type) => {
    if (!dashboardData || !dashboardData.top_contributors || !dashboardData.top_contributors[type]) {
      return { labels: [], datasets: [] };
    }

    const data = dashboardData.top_contributors[type];
    const labels = data.map(item => item.name);
    const revenueData = data.map(item => item.revenue || 0);
    const profitData = data.map(item => item.profit || 0);

    return {
      labels,
      datasets: [
        {
          label: 'Revenue',
          data: revenueData,
          backgroundColor: theme === 'dark' ? '#60a5fa' : '#1e293b',
          borderRadius: 6,
        },
        {
          label: 'Profit',
          data: profitData,
          backgroundColor: '#EDD5B1',
          borderRadius: 6,
        },
      ],
    };
  };

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

  // Chart options for Top 10 charts (bar + line combo)
  const top10ChartOptions = {
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
          padding: 15,
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
        intersect: false,
        mode: 'index',
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
          display: false,
        },
        ticks: {
          color: theme === 'dark' ? '#9ca3af' : '#6b7280',
          maxRotation: 45,
          minRotation: 45,
          font: {
            size: 10
          }
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          display: true,
          color: theme === 'dark' ? '#374151' : '#e5e7eb',
        },
        ticks: {
          color: theme === 'dark' ? '#9ca3af' : '#6b7280',
          callback: function(value) {
            return formatNumber(value);
          },
          font: {
            size: 11
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
            <p className="text-gray-600 dark:text-gray-400">Comprehensive business performance metrics and insights</p>
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

        {/* KPI Cards & Exception Highlights - Horizontal Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Side - Summary Cards Container */}
          <div className="lg:col-span-6">
            <div 
              className="rounded-lg p-5 h-full"
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
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Key Metrics</h2>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                {/* Gross Sales */}
                <div 
                  className="rounded-lg p-4 bg-white dark:bg-gray-800/50"
                  style={{
                    border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.08)'
                  }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <DollarSign className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Gross Sales</span>
                  </div>
                  {loading ? (
                    <Skeleton className="h-8 w-32" />
                  ) : (
                    <p className="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                      {formatNumber(summary.gross_sales)}
                    </p>
                  )}
                </div>

                {/* Gross Profit */}
                <div 
                  className="rounded-lg p-4 bg-white dark:bg-gray-800/50"
                  style={{
                    border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.08)'
                  }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-green-600" />
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Gross Profit</span>
                  </div>
                  {loading ? (
                    <Skeleton className="h-8 w-32" />
                  ) : (
                    <p className="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                      {formatNumber(summary.gross_profit)}
                    </p>
                  )}
                </div>

                {/* Transfer Cost */}
                <div 
                  className="rounded-lg p-4 bg-white dark:bg-gray-800/50"
                  style={{
                    border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.08)'
                  }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <ShoppingBag className="w-4 h-4 text-orange-600" />
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Transfer Cost</span>
                  </div>
                  {loading ? (
                    <Skeleton className="h-8 w-32" />
                  ) : (
                    <p className="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                      {formatNumber(summary.transfer_cost)}
                    </p>
                  )}
                </div>

                {/* Margin % */}
                <div 
                  className="rounded-lg p-4 bg-white dark:bg-gray-800/50"
                  style={{
                    border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.08)'
                  }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Percent className="w-4 h-4 text-purple-600" />
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Margin %</span>
                  </div>
                  {loading ? (
                    <Skeleton className="h-8 w-32" />
                  ) : (
                    <p className="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                      {summary.margin_pct.toFixed(2)}%
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right Side - Exception Highlights (Scrollable) */}
          <div className="lg:col-span-6">
            <div 
              className="rounded-lg p-5 h-full"
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
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Exception Highlights</h2>
              </div>
              
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </div>
              ) : dashboardData && dashboardData.exceptions && dashboardData.exceptions.length > 0 ? (
                <div className="space-y-3 overflow-y-auto" style={{ maxHeight: '400px', paddingRight: '8px' }}>
                  {dashboardData.exceptions.map((exception, index) => (
                    <div 
                      key={index}
                      className={`p-3 rounded-lg ${
                        exception.severity === 'high' 
                          ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800' 
                          : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                            {exception.period}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {exception.message}
                          </p>
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded ${
                          exception.severity === 'high'
                            ? 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100'
                        }`}>
                          {exception.severity.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <AlertTriangle className={`w-12 h-12 mx-auto mb-2 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                    <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                      No exceptions to highlight
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Gross Sales & Profit Trend Chart */}
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
              Gross Sales & Profit Trend
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Track gross sales and profit performance over time
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

        {/* Top 10 Charts - Grid Layout (2 per row) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top 10 Customers Chart */}
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
                Top 10 Customers
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Revenue and Profit by customer
              </p>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center" style={{ height: '400px' }}>
                <Skeleton className="w-full h-full" />
              </div>
            ) : prepareTop10ChartData('customers').labels.length === 0 ? (
              <div className="flex items-center justify-center" style={{ height: '400px' }}>
                <div className="text-center">
                  <Users className={`w-12 h-12 mx-auto mb-2 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                  <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                    No customer data available
                  </p>
                </div>
              </div>
            ) : (
              <ChartComponent
                type="bar"
                data={prepareTop10ChartData('customers')}
                options={top10ChartOptions}
                height={400}
              />
            )}
          </div>

          {/* Top 10 Brands Chart */}
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
                Top 10 Brands
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Revenue and Profit by brand
              </p>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center" style={{ height: '400px' }}>
                <Skeleton className="w-full h-full" />
              </div>
            ) : prepareTop10ChartData('brands').labels.length === 0 ? (
              <div className="flex items-center justify-center" style={{ height: '400px' }}>
                <div className="text-center">
                  <Target className={`w-12 h-12 mx-auto mb-2 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                  <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                    No brand data available
                  </p>
                </div>
              </div>
            ) : (
              <ChartComponent
                type="bar"
                data={prepareTop10ChartData('brands')}
                options={top10ChartOptions}
                height={400}
              />
            )}
          </div>

          {/* Top 10 Categories Chart */}
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
                Top 10 Categories
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Revenue and Profit by category
              </p>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center" style={{ height: '400px' }}>
                <Skeleton className="w-full h-full" />
              </div>
            ) : prepareTop10ChartData('categories').labels.length === 0 ? (
              <div className="flex items-center justify-center" style={{ height: '400px' }}>
                <div className="text-center">
                  <BarChart3 className={`w-12 h-12 mx-auto mb-2 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                  <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                    No category data available
                  </p>
                </div>
              </div>
            ) : (
              <ChartComponent
                type="bar"
                data={prepareTop10ChartData('categories')}
                options={top10ChartOptions}
                height={400}
              />
            )}
          </div>

          {/* Top 10 Channels Chart */}
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
                Top 10 Channels
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Revenue and Profit by channel
              </p>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center" style={{ height: '400px' }}>
                <Skeleton className="w-full h-full" />
              </div>
            ) : prepareTop10ChartData('channels').labels.length === 0 ? (
              <div className="flex items-center justify-center" style={{ height: '400px' }}>
                <div className="text-center">
                  <Activity className={`w-12 h-12 mx-auto mb-2 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                  <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                    No channel data available
                  </p>
                </div>
              </div>
            ) : (
              <ChartComponent
                type="bar"
                data={prepareTop10ChartData('channels')}
                options={top10ChartOptions}
                height={400}
              />
            )}
          </div>
        </div>

        {/* Top 10 Contributors */}
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
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Top 10 Contributors</h2>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-4 flex-wrap">
            <button
              onClick={() => setActiveTab('customers')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'customers'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Customers
            </button>
            <button
              onClick={() => setActiveTab('brands')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'brands'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Brands
            </button>
            <button
              onClick={() => setActiveTab('businesses')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'businesses'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Businesses
            </button>
            <button
              onClick={() => setActiveTab('categories')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'categories'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Categories
            </button>
            <button
              onClick={() => setActiveTab('channels')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'channels'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Channels
            </button>
          </div>

          {/* Contributors Table */}
          {loading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-300 dark:border-gray-600">
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-600 dark:text-gray-400">#</th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-600 dark:text-gray-400">Name</th>
                    <th className="text-right py-2 px-3 text-xs font-semibold text-gray-600 dark:text-gray-400">Revenue</th>
                    <th className="text-right py-2 px-3 text-xs font-semibold text-gray-600 dark:text-gray-400">Profit</th>
                    <th className="text-right py-2 px-3 text-xs font-semibold text-gray-600 dark:text-gray-400">Margin %</th>
                    <th className="text-right py-2 px-3 text-xs font-semibold text-gray-600 dark:text-gray-400">Units</th>
                  </tr>
                </thead>
                <tbody>
                  {getTopContributors().map((item, index) => (
                    <tr 
                      key={index}
                      className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                    >
                      <td className="py-2 px-3 text-sm text-gray-600 dark:text-gray-400">{index + 1}</td>
                      <td className="py-2 px-3 text-sm font-medium text-gray-900 dark:text-gray-100">{item.name}</td>
                      <td className="py-2 px-3 text-sm text-right text-gray-900 dark:text-gray-100">{formatNumber(item.revenue)}</td>
                      <td className="py-2 px-3 text-sm text-right text-gray-900 dark:text-gray-100">{formatNumber(item.profit)}</td>
                      <td className="py-2 px-3 text-sm text-right font-medium text-gray-900 dark:text-gray-100">{item.margin_pct}%</td>
                      <td className="py-2 px-3 text-sm text-right text-gray-600 dark:text-gray-400">{formatNumber(item.units)}</td>
                    </tr>
                  ))}
                  {getTopContributors().length === 0 && (
                    <tr>
                      <td colSpan="6" className="py-8 text-center text-gray-500 dark:text-gray-400">
                        No data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default ExecutiveView;
