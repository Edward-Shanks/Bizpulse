import React, { useState, useEffect, useCallback } from 'react';
import Layout from '@/components/Layout';
import ChartComponent from '@/components/ChartComponent';
import InsightModal from '@/components/InsightModal';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import { formatNumber, formatCurrency, formatUnits } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { toast } from 'sonner';
import { Users, ShoppingCart, TrendingUp, MapPin, Globe, Mail, Euro, Eye, Clock, Package, Calendar, AlertTriangle, MessageSquare, Lightbulb } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

const CustomerInsights = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [insightModal, setInsightModal] = useState({
    isOpen: false,
    chartTitle: '',
    insights: [],
    recommendations: [],
  });

  // Filter states
  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  
  // Chart-level filters (individual filters that override global filters)
  const [chartFilters, setChartFilters] = useState({});
  
  // Chart-specific data (for charts with individual filters)
  const [chartData, setChartData] = useState({});

  // Fetch filters only on initial load - they don't need to update when selections change
  const fetchFilters = useCallback(async () => {
    if (!token) return;
    try {
      // Use customer insights specific filter endpoint that returns only years/months from Shopify data
      const response = await axios.get(`${API}/analytics/customer-insights/filters`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      // Convert years to strings for the filter component
      const filterData = {
        years: (response.data.years || []).map(y => String(y)),
        months: response.data.months || [],
      };
      setFilters(filterData);
      console.log('✅ Customer insights filters loaded:', filterData);
    } catch (error) {
      console.error('Failed to load customer insights filters:', error);
      // Fallback to empty filters if API fails
      setFilters({
        years: [],
        months: [],
      });
    }
  }, [token]);

  // Memoize fetchData to prevent unnecessary re-creations
  const fetchData = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const params = {};
      if (selectedYears.length > 0) {
        params.years = selectedYears.join(',');
      }
      if (selectedMonths.length > 0) {
        params.months = selectedMonths.join(',');
      }
      
      console.log('🔍 Fetching customer insights with params:', params);
      
      const response = await axios.get(`${API}/analytics/customer-insights`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });
      setData(response.data);
      console.log('✅ Customer insights data loaded:', {
        summary: response.data?.summary,
        monthlyTrendLength: response.data?.monthlyTrend?.length,
      });
    } catch (error) {
      console.error('❌ Failed to load customer insights:', error);
      if (error.response) {
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
      }
      toast.error('Failed to load customer insights data');
    } finally {
      setLoading(false);
    }
  }, [token, selectedYears, selectedMonths]);

  // Load filters only once on mount
  useEffect(() => {
    fetchFilters();
  }, [fetchFilters]);

  // Load data when filters or selections change
  useEffect(() => {
    if (!filters) return; // Wait for filters to load first
    fetchData();
  }, [fetchData, filters]);

  // Helper function to merge global and individual filters (individual overrides global)
  const getMergedFilters = (chartName = null) => {
    const globalFilters = {
      years: selectedYears,
      months: selectedMonths,
    };

    // If no chart name, return global filters only
    if (!chartName || !chartFilters[chartName]) {
      return globalFilters;
    }

    // Merge: individual filters override global filters
    const individualFilters = chartFilters[chartName];
    return {
      years: individualFilters.hasOwnProperty('years')
        ? individualFilters.years 
        : globalFilters.years,
      months: individualFilters.hasOwnProperty('months')
        ? individualFilters.months 
        : globalFilters.months,
    };
  };

  // Reset individual chart filters and chart data when global filters change
  useEffect(() => {
    setChartFilters({});
    setChartData({});
  }, [selectedYears, selectedMonths]);

  // Fetch data for a specific chart with merged filters
  const fetchChartData = async (chartName, individualFiltersOverride = null) => {
    try {
      let mergedFilters;
      if (individualFiltersOverride) {
        mergedFilters = {
          years: individualFiltersOverride.hasOwnProperty('years')
            ? individualFiltersOverride.years 
            : selectedYears,
          months: individualFiltersOverride.hasOwnProperty('months')
            ? individualFiltersOverride.months 
            : selectedMonths,
        };
      } else {
        mergedFilters = getMergedFilters(chartName);
      }
      
      const params = {};
      if (mergedFilters.years.length > 0) {
        params.years = mergedFilters.years.join(',');
      }
      if (mergedFilters.months.length > 0) {
        params.months = mergedFilters.months.join(',');
      }
      
      const response = await axios.get(`${API}/analytics/customer-insights`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });
      
      setChartData(prev => ({
        ...prev,
        [chartName]: response.data
      }));
    } catch (error) {
      console.error(`Failed to load data for chart ${chartName}:`, error);
    }
  };

  const handleChartFilterChange = async (chartName, filterType, value) => {
    const filterKeyMap = {
      'year': 'years',
      'years': 'years',
      'month': 'months',
      'months': 'months',
    };

    const mappedKey = filterKeyMap[filterType] || filterType;
    
    let filterValue = [];
    if (value === 'all' || value === null || value === undefined) {
      filterValue = [];
    } else if (Array.isArray(value)) {
      filterValue = value;
    } else {
      filterValue = [value];
    }

    const newIndividualFilters = {
      ...(chartFilters[chartName] || {}),
      [mappedKey]: filterValue
    };
    
    const newFilters = {
      ...chartFilters,
      [chartName]: newIndividualFilters
    };
    
    setChartFilters(newFilters);
    await fetchChartData(chartName, newIndividualFilters);
  };

  // Helper function to get data for a specific chart
  const getChartData = (chartName) => {
    return chartData[chartName] || data;
  };

  // Helper function to derive chart-specific data arrays
  const getChartDataArrays = (chartName) => {
    const chartDataToUse = getChartData(chartName);
    return {
      summary: chartDataToUse?.summary || {},
      newVsReturning: chartDataToUse?.newVsReturning || [],
      channelPerf: chartDataToUse?.channelPerformance || [],
      regionPerf: chartDataToUse?.regionPerformance || [],
      trafficSource: chartDataToUse?.trafficSource || [],
      clv: chartDataToUse?.customerLifetimeValue || [],
      monthlyTrend: chartDataToUse?.monthlyTrend || [],
      subscriptionStatus: chartDataToUse?.subscriptionStatus || [],
      topCustomers: chartDataToUse?.topCustomers || [],
      platformAnalysis: chartDataToUse?.platformAnalysis || [],
      trafficType: chartDataToUse?.trafficType || [],
      hourlyPatterns: chartDataToUse?.hourlyPatterns || [],
      countryDistribution: chartDataToUse?.countryDistribution || [],
      smsSubscription: chartDataToUse?.smsSubscription || [],
      mediumAnalysis: chartDataToUse?.mediumAnalysis || [],
      topProducts: chartDataToUse?.topProducts || [],
      dayOfWeekAnalysis: chartDataToUse?.dayOfWeekAnalysis || [],
      returnTrend: chartDataToUse?.returnTrend || [],
      chartDataToUse,
    };
  };


  const handleViewInsight = (chartTitle, insights, recommendations) => {
    setInsightModal({
      isOpen: true,
      chartTitle,
      insights: insights || [],
      recommendations: recommendations || [],
    });
  };

  const ChartCard = ({ title, children, onViewInsight, icon: Icon, chartId, renderChart }) => {
    const mergedFilters = chartId ? getMergedFilters(chartId) : { years: selectedYears, months: selectedMonths };
    
    // Get chart-specific data arrays if chartId is provided
    const chartDataArrays = chartId ? getChartDataArrays(chartId) : null;
    
    return (
      <div 
        className="rounded-lg shadow-sm p-6"
        style={{
          background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
          border: '1px solid rgba(0, 0, 0, 0.1)'
        }}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {Icon && <Icon className="w-5 h-5 text-indigo-600" />}
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>
          {onViewInsight && (
            <button
              onClick={onViewInsight}
              className="px-4 py-1.5 bg-orange-100 hover:bg-orange-200 text-orange-700 rounded-lg text-sm font-medium transition flex items-center gap-2 whitespace-nowrap"
            >
              <Lightbulb className="w-4 h-4" />
              View Insight
            </button>
          )}
        </div>
        
        {/* Chart Filters - Show merged filter values (individual overrides global) - Only show if chartId is provided */}
        {chartId && (
          <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
            <select
              value={mergedFilters.years.length === 1 ? mergedFilters.years[0] : mergedFilters.years.length > 1 ? 'multiple' : 'all'}
              onChange={async (e) => {
                const value = e.target.value;
                if (value === 'all') {
                  await handleChartFilterChange(chartId, 'years', []);
                } else {
                  await handleChartFilterChange(chartId, 'years', [value]);
                }
              }}
              className="text-sm border border-gray-300 rounded px-3 py-1.5 bg-white flex-shrink-0"
            >
              <option value="all">All Years</option>
              {filters?.years?.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
            
            <select
              value={mergedFilters.months.length === 1 ? mergedFilters.months[0] : mergedFilters.months.length > 1 ? 'multiple' : 'all'}
              onChange={async (e) => {
                const value = e.target.value;
                if (value === 'all') {
                  await handleChartFilterChange(chartId, 'months', []);
                } else {
                  await handleChartFilterChange(chartId, 'months', [value]);
                }
              }}
              className="text-sm border border-gray-300 rounded px-3 py-1.5 bg-white flex-shrink-0"
            >
              <option value="all">All Months</option>
              {filters?.months?.map(month => (
                <option key={month} value={month}>{month}</option>
              ))}
            </select>
          </div>
        )}
        
        {/* Render chart with chart-specific data */}
        {renderChart && chartDataArrays ? renderChart(chartDataArrays) : children}
      </div>
    );
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          {/* Header Skeleton */}
          <div>
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>

          {/* Summary Cards Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <Skeleton className="h-4 w-24 mb-3" />
                    <Skeleton className="h-8 w-32" />
                  </div>
                  <Skeleton className="w-10 h-10 rounded-full" />
                </div>
              </div>
            ))}
          </div>

          {/* Chart Cards Skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Skeleton className="w-5 h-5 rounded" />
                    <Skeleton className="h-6 w-40" />
                  </div>
                  <Skeleton className="h-8 w-32 rounded" />
                </div>
                <Skeleton className="h-64 w-full rounded" />
              </div>
            ))}
          </div>

          {/* Additional Section Skeleton */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <Skeleton className="h-6 w-48 mb-4" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-32 w-full rounded" />
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-red-500">Failed to load data</div>
        </div>
      </Layout>
    );
  }

  const summary = data.summary || {};
  const newVsReturning = data.newVsReturning || [];
  const channelPerf = data.channelPerformance || [];
  const regionPerf = data.regionPerformance || [];
  const trafficSource = data.trafficSource || [];
  const clv = data.customerLifetimeValue || [];
  const monthlyTrend = data.monthlyTrend || [];
  const subscriptionStatus = data.subscriptionStatus || [];
  const topCustomers = data.topCustomers || [];
  const platformAnalysis = data.platformAnalysis || [];
  const trafficType = data.trafficType || [];
  const hourlyPatterns = data.hourlyPatterns || [];
  const countryDistribution = data.countryDistribution || [];
  const smsSubscription = data.smsSubscription || [];
  const mediumAnalysis = data.mediumAnalysis || [];
  const topProducts = data.topProducts || [];
  const dayOfWeekAnalysis = data.dayOfWeekAnalysis || [];
  const returnTrend = data.returnTrend || [];

  // Colors with reduced opacity for multi-color graphs
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'];
  const colorsWithOpacity = colors.map(color => {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.5)`;
  });

  // Chart data configurations
  const newVsReturningChart = {
    labels: newVsReturning.map((item) => item.type || 'Unknown'),
    datasets: [
      {
        label: 'Sales (€)',
        data: newVsReturning.map((item) => item.sales || 0),
        backgroundColor: ['#1e293b', '#EDD5B1'],
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };

  const channelChart = {
    labels: channelPerf.map((item) => item.channel || 'Unknown'),
    datasets: [
      {
        label: 'Sales (€)',
        data: channelPerf.map((item) => item.sales || 0),
        backgroundColor: '#1e293b',
      },
    ],
  };

  const regionChart = {
    labels: regionPerf.map((item) => item.region || 'Unknown'),
    datasets: [
      {
        label: 'Sales (€)',
        data: regionPerf.map((item) => item.sales || 0),
        backgroundColor: '#1e293b',
      },
    ],
  };

  const trafficSourceChart = {
    labels: trafficSource.map((item) => item.source || 'Unknown'),
    datasets: [
      {
        label: 'Sales (€)',
        data: trafficSource.map((item) => item.sales || 0),
        backgroundColor: '#1e293b',
      },
    ],
  };

  const clvChart = {
    labels: clv.map((item) => `${item.order_bucket} orders`),
    datasets: [
      {
        label: 'Avg Sales per Customer (€)',
        data: clv.map((item) => item.avg_sales_per_customer || 0),
        backgroundColor: '#1e293b',
      },
    ],
  };

  const monthlyTrendChart = {
    labels: monthlyTrend.map((item) => item.month_label || item.MonthName || 'Unknown'),
    datasets: [
      {
        type: 'line',
        label: 'Total Sales (€)',
        data: monthlyTrend.map((item) => {
          // Try multiple possible key formats
          const value = item.Total_sales || item['Total_sales'] || item['Total sales'] || item.total_sales || 0;
          return typeof value === 'number' ? value : parseFloat(value) || 0;
        }),
        borderColor: '#745E39',
        backgroundColor: 'rgba(116, 94, 57, 0.1)',
        fill: true,
        tension: 0.4,
        yAxisID: 'y',
      },
      {
        type: 'bar',
        label: 'New Customers',
        data: monthlyTrend.map((item) => {
          // Try multiple possible key formats
          const value = item.Orders_first_time || item['Orders_first_time'] || item['Orders (first-time)'] || item.orders_first_time || 0;
          return typeof value === 'number' ? value : parseFloat(value) || 0;
        }),
        backgroundColor: '#EDD5B1',
        borderRadius: 4,
        yAxisID: 'y1',
      },
      {
        type: 'bar',
        label: 'Returning Customers',
        data: monthlyTrend.map((item) => {
          // Try multiple possible key formats
          const value = item.Orders_returning || item['Orders_returning'] || item['Orders (returning)'] || item.orders_returning || 0;
          return typeof value === 'number' ? value : parseFloat(value) || 0;
        }),
        backgroundColor: '#1e293b',
        borderRadius: 4,
        yAxisID: 'y1',
      },
    ],
  };

  const subscriptionChart = {
    labels: subscriptionStatus.map((item) => item.status || 'Unknown'),
    datasets: [
      {
        label: 'Customers',
        data: subscriptionStatus.map((item) => item.unique_customers || 0),
        backgroundColor: colorsWithOpacity.slice(0, 3),
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };

  const platformChart = {
    labels: platformAnalysis.map((item) => item.platform || 'Unknown'),
    datasets: [
      {
        label: 'Sales (€)',
        data: platformAnalysis.map((item) => item.sales || 0),
        backgroundColor: '#1e293b',
      },
    ],
  };

  const trafficTypeChart = {
    labels: trafficType.map((item) => item.type || 'Unknown'),
    datasets: [
      {
        label: 'Sales (€)',
        data: trafficType.map((item) => item.sales || 0),
        backgroundColor: '#1e293b',
      },
    ],
  };

  // New chart configurations
  const hourlyPatternsChart = {
    labels: hourlyPatterns.length > 0 ? hourlyPatterns.map((item) => `${item.hour}:00`) : ['No Data'],
    datasets: [
      {
        label: 'Sales (€)',
        data: hourlyPatterns.length > 0 ? hourlyPatterns.map((item) => item.sales || 0) : [0],
        borderColor: '#1e293b',
        backgroundColor: 'rgba(30, 41, 59, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Orders',
        data: hourlyPatterns.length > 0 ? hourlyPatterns.map((item) => item.orders || 0) : [0],
        borderColor: '#745E39',
        backgroundColor: 'rgba(116, 94, 57, 0.1)',
        fill: true,
        tension: 0.4,
        yAxisID: 'y1',
      },
    ],
  };

  const countryDistributionChart = {
    labels: countryDistribution.length > 0 ? countryDistribution.map((item) => item.country || 'Unknown') : ['No Data'],
    datasets: [
      {
        label: 'Sales (€)',
        data: countryDistribution.length > 0 ? countryDistribution.map((item) => item.sales || 0) : [0],
        backgroundColor: colorsWithOpacity,
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };

  const smsSubscriptionChart = {
    labels: smsSubscription.length > 0 ? smsSubscription.map((item) => item.status || 'Unknown') : ['No Data'],
    datasets: [
      {
        label: 'Customers',
        data: smsSubscription.length > 0 ? smsSubscription.map((item) => item.unique_customers || 0) : [0],
        backgroundColor: colorsWithOpacity.slice(0, 3),
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };

  // Helper function to build chart data from chart-specific data arrays
  const buildChartData = (chartName, chartDataArrays) => {
    const {
      newVsReturning: chartNewVsReturning,
      channelPerf: chartChannelPerf,
      regionPerf: chartRegionPerf,
      trafficSource: chartTrafficSource,
      clv: chartClv,
      monthlyTrend: chartMonthlyTrend,
      subscriptionStatus: chartSubscriptionStatus,
      platformAnalysis: chartPlatformAnalysis,
      trafficType: chartTrafficType,
      hourlyPatterns: chartHourlyPatterns,
      countryDistribution: chartCountryDistribution,
      smsSubscription: chartSmsSubscription,
      mediumAnalysis: chartMediumAnalysis,
      topProducts: chartTopProducts,
      dayOfWeekAnalysis: chartDayOfWeekAnalysis,
      returnTrend: chartReturnTrend,
    } = chartDataArrays;

    const chartConfigs = {
      newVsReturning: {
        labels: chartNewVsReturning.map((item) => item.type || 'Unknown'),
        datasets: [
          {
            label: 'Sales (€)',
            data: chartNewVsReturning.map((item) => item.sales || 0),
            backgroundColor: ['#1e293b', '#EDD5B1'],
            borderWidth: 2,
            borderColor: '#fff',
          },
        ],
      },
      channel: {
        labels: chartChannelPerf.map((item) => item.channel || 'Unknown'),
        datasets: [
          {
            label: 'Sales (€)',
            data: chartChannelPerf.map((item) => item.sales || 0),
            backgroundColor: '#1e293b',
          },
        ],
      },
      region: {
        labels: chartRegionPerf.map((item) => item.region || 'Unknown'),
        datasets: [
          {
            label: 'Sales (€)',
            data: chartRegionPerf.map((item) => item.sales || 0),
            backgroundColor: '#1e293b',
          },
        ],
      },
      trafficSource: {
        labels: chartTrafficSource.map((item) => item.source || 'Unknown'),
        datasets: [
          {
            label: 'Sales (€)',
            data: chartTrafficSource.map((item) => item.sales || 0),
            backgroundColor: '#1e293b',
          },
        ],
      },
      clv: {
        labels: chartClv.map((item) => `${item.order_bucket} orders`),
        datasets: [
          {
            label: 'Avg Sales per Customer (€)',
            data: chartClv.map((item) => item.avg_sales_per_customer || 0),
            backgroundColor: '#1e293b',
          },
        ],
      },
      monthlyTrend: {
        labels: chartMonthlyTrend.map((item) => item.month_label || item.MonthName || 'Unknown'),
        datasets: [
          {
            type: 'line',
            label: 'Total Sales (€)',
            data: chartMonthlyTrend.map((item) => {
              const value = item.Total_sales || item['Total_sales'] || item['Total sales'] || item.total_sales || 0;
              return typeof value === 'number' ? value : parseFloat(value) || 0;
            }),
            borderColor: '#745E39',
            backgroundColor: 'rgba(116, 94, 57, 0.1)',
            fill: true,
            tension: 0.4,
            yAxisID: 'y',
          },
          {
            type: 'bar',
            label: 'New Customers',
            data: chartMonthlyTrend.map((item) => {
              const value = item.Orders_first_time || item['Orders_first_time'] || item['Orders (first-time)'] || item.orders_first_time || 0;
              return typeof value === 'number' ? value : parseFloat(value) || 0;
            }),
            backgroundColor: '#EDD5B1',
            borderRadius: 4,
            yAxisID: 'y1',
          },
          {
            type: 'bar',
            label: 'Returning Customers',
            data: chartMonthlyTrend.map((item) => {
              const value = item.Orders_returning || item['Orders_returning'] || item['Orders (returning)'] || item.orders_returning || 0;
              return typeof value === 'number' ? value : parseFloat(value) || 0;
            }),
            backgroundColor: '#1e293b',
            borderRadius: 4,
            yAxisID: 'y1',
          },
        ],
      },
      subscription: {
        labels: chartSubscriptionStatus.map((item) => item.status || 'Unknown'),
        datasets: [
          {
            label: 'Customers',
            data: chartSubscriptionStatus.map((item) => item.unique_customers || 0),
            backgroundColor: colorsWithOpacity.slice(0, 3),
            borderWidth: 2,
            borderColor: '#fff',
          },
        ],
      },
      platform: {
        labels: chartPlatformAnalysis.map((item) => item.platform || 'Unknown'),
        datasets: [
          {
            label: 'Sales (€)',
            data: chartPlatformAnalysis.map((item) => item.sales || 0),
            backgroundColor: '#1e293b',
          },
        ],
      },
      trafficType: {
        labels: chartTrafficType.map((item) => item.type || 'Unknown'),
        datasets: [
          {
            label: 'Sales (€)',
            data: chartTrafficType.map((item) => item.sales || 0),
            backgroundColor: '#1e293b',
          },
        ],
      },
      hourlyPatterns: {
        labels: chartHourlyPatterns.length > 0 ? chartHourlyPatterns.map((item) => `${item.hour}:00`) : ['No Data'],
        datasets: [
          {
            label: 'Sales (€)',
            data: chartHourlyPatterns.length > 0 ? chartHourlyPatterns.map((item) => item.sales || 0) : [0],
            borderColor: '#1e293b',
            backgroundColor: 'rgba(30, 41, 59, 0.1)',
            fill: true,
            tension: 0.4,
          },
          {
            label: 'Orders',
            data: chartHourlyPatterns.length > 0 ? chartHourlyPatterns.map((item) => item.orders || 0) : [0],
            borderColor: '#745E39',
            backgroundColor: 'rgba(116, 94, 57, 0.1)',
            fill: true,
            tension: 0.4,
            yAxisID: 'y1',
          },
        ],
      },
      countryDistribution: {
        labels: chartCountryDistribution.length > 0 ? chartCountryDistribution.map((item) => item.country || 'Unknown') : ['No Data'],
        datasets: [
          {
            label: 'Sales (€)',
            data: chartCountryDistribution.length > 0 ? chartCountryDistribution.map((item) => item.sales || 0) : [0],
            backgroundColor: colorsWithOpacity,
            borderWidth: 2,
            borderColor: '#fff',
          },
        ],
      },
      smsSubscription: {
        labels: chartSmsSubscription.length > 0 ? chartSmsSubscription.map((item) => item.status || 'Unknown') : ['No Data'],
        datasets: [
          {
            label: 'Customers',
            data: chartSmsSubscription.length > 0 ? chartSmsSubscription.map((item) => item.unique_customers || 0) : [0],
            backgroundColor: colorsWithOpacity.slice(0, 3),
            borderWidth: 2,
            borderColor: '#fff',
          },
        ],
      },
      mediumAnalysis: {
        labels: chartMediumAnalysis.map((item) => item.medium || 'Unknown'),
        datasets: [
          {
            label: 'Sales (€)',
            data: chartMediumAnalysis.map((item) => item.sales || 0),
            backgroundColor: '#1e293b',
          },
        ],
      },
      topProducts: {
        labels: chartTopProducts.length > 0 ? chartTopProducts.map((item) => item.product_name || `SKU ${item.sku}` || 'Unknown') : ['No Data'],
        datasets: [
          {
            label: 'Sales (€)',
            data: chartTopProducts.length > 0 ? chartTopProducts.map((item) => item.sales || 0) : [0],
            backgroundColor: '#1e293b',
          },
        ],
      },
      dayOfWeek: {
        labels: chartDayOfWeekAnalysis.length > 0 ? chartDayOfWeekAnalysis.map((item) => item.day || item.day_of_week || 'Unknown') : ['No Data'],
        datasets: [
          {
            label: 'Sales (€)',
            data: chartDayOfWeekAnalysis.length > 0 ? chartDayOfWeekAnalysis.map((item) => item.sales || 0) : [0],
            backgroundColor: '#1e293b',
          },
        ],
      },
      returnTrend: {
        labels: chartReturnTrend.length > 0 ? chartReturnTrend.map((item) => item.month_label || item.MonthName || 'Unknown') : ['No Data'],
        datasets: [
          {
            label: 'Return Rate (%)',
            data: chartReturnTrend.length > 0 ? chartReturnTrend.map((item) => {
              const value = item.return_rate || item['return_rate'] || item['Return Rate'] || 0;
              return typeof value === 'number' ? value : parseFloat(value) || 0;
            }) : [0],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            fill: true,
            tension: 0.4,
          },
        ],
      },
    };

    return chartConfigs[chartName] || null;
  };

  const mediumAnalysisChart = {
    labels: mediumAnalysis.length > 0 ? mediumAnalysis.map((item) => item.medium || 'Unknown') : ['No Data'],
    datasets: [
      {
        label: 'Sales (€)',
        data: mediumAnalysis.length > 0 ? mediumAnalysis.map((item) => item.sales || 0) : [0],
        backgroundColor: '#1e293b',
      },
    ],
  };

  const topProductsChart = {
    labels: topProducts.length > 0 ? topProducts.map((item) => `SKU ${item.sku}`) : ['No Data'],
    datasets: [
      {
        label: 'Sales (€)',
        data: topProducts.length > 0 ? topProducts.map((item) => item.sales || 0) : [0],
        backgroundColor: '#1e293b',
      },
    ],
  };

  const dayOfWeekChart = {
    labels: dayOfWeekAnalysis.length > 0 ? dayOfWeekAnalysis.map((item) => item.day || 'Unknown') : ['No Data'],
    datasets: [
      {
        label: 'Sales (€)',
        data: dayOfWeekAnalysis.length > 0 ? dayOfWeekAnalysis.map((item) => item.sales || 0) : [0],
        backgroundColor: '#1e293b',
      },
    ],
  };

  const returnTrendChart = {
    labels: returnTrend.length > 0 ? returnTrend.map((item) => item.month_label || 'Unknown') : ['No Data'],
    datasets: [
      {
        label: 'Return Rate (%)',
        data: returnTrend.length > 0 ? returnTrend.map((item) => item.return_rate || 0) : [0],
        borderColor: '#1e293b',
        backgroundColor: 'rgba(30, 41, 59, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
    },
  };

  const donutChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        top: 10,
        bottom: 20,
        left: 10,
        right: 10,
      },
    },
    plugins: {
      legend: {
        display: true,
        position: 'right',
        labels: {
          boxWidth: 12,
          padding: 10,
          font: { size: 11 },
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
            // Check if the dataset label suggests it's a count (Customers) or currency (Sales)
            const isCurrency = context.dataset.label && (context.dataset.label.includes('Sales') || context.dataset.label.includes('€'));
            const formattedValue = isCurrency ? formatCurrency(value) : formatUnits(value);
            return `${label}: ${formattedValue} (${percentage}%)`;
          },
        },
      },
    },
    cutout: '60%',
  };

  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Sales (€)',
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Number of Orders',
        },
        grid: {
          drawOnChartArea: false,
        },
      },
      x: {
        display: true,
        title: {
          display: true,
          text: 'Month',
        },
      },
    },
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customer Deep Intelligence</h1>
          <p className="text-gray-600 text-sm mt-1">Deep dive into customer behavior and Shopify analytics</p>
        </div>

        {/* Filters */}
        <div 
          className="rounded-lg p-4"
          style={{
            background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <MultiSelectFilter
              label="Year"
              options={filters?.years || []}
              selectedValues={selectedYears}
              onChange={(values) => {
                console.log('📅 Years selected:', values);
                setSelectedYears(values);
              }}
              placeholder="All Years"
            />
            <MultiSelectFilter
              label="Month"
              options={filters?.months || []}
              selectedValues={selectedMonths}
              onChange={(values) => {
                console.log('📅 Months selected:', values);
                setSelectedMonths(values);
              }}
              placeholder="All Months"
            />
          </div>
          {(selectedYears.length > 0 || selectedMonths.length > 0) && (
            <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-800">
              <strong>Active Filters:</strong>{' '}
              {selectedYears.length > 0 && `Years: ${selectedYears.join(', ')}`}
              {selectedYears.length > 0 && selectedMonths.length > 0 && ' | '}
              {selectedMonths.length > 0 && `Months: ${selectedMonths.join(', ')}`}
            </div>
          )}
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div 
            className="rounded-lg shadow-sm p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatUnits(summary.totalCustomers || 0)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Customers</p>
            </div>
          </div>

          <div 
            className="rounded-lg shadow-sm p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatUnits(summary.totalOrders || 0)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Orders</p>
            </div>
          </div>

          <div 
            className="rounded-lg shadow-sm p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatCurrency(summary.totalSales || 0)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Sales</p>
            </div>
          </div>

          <div 
            className="rounded-lg shadow-sm p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatCurrency(summary.avgOrderValue || 0)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Avg Order Value</p>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* New vs Returning Customers */}
          <ChartCard
            title="New vs Returning Customers"
            icon={Users}
            chartId="newVsReturning"
            onViewInsight={() => {
              const chartDataArrays = getChartDataArrays('newVsReturning');
              const chartSummary = chartDataArrays.summary;
              const chartNewVsReturning = chartDataArrays.newVsReturning;
              handleViewInsight(
                'New vs Returning Customers',
                [
                  { type: 'positive', text: `Returning customers generate ${((chartNewVsReturning.find((x) => x.type === 'Returning')?.sales || 0) / (chartSummary.totalSales || 1)) * 100}% of total sales` },
                ],
                ['Focus on retention programs', 'Improve new customer onboarding', 'Create loyalty incentives']
              );
            }}
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('newVsReturning', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="doughnut" data={chartData} options={donutChartOptions} />}
                </div>
              );
            }}
          />

          {/* Sales Channel Performance */}
          <ChartCard
            title="Sales Channel Performance"
            icon={ShoppingCart}
            chartId="channelPerformance"
            onViewInsight={() =>
              handleViewInsight(
                'Sales Channel Performance',
                [{ type: 'positive', text: 'Online Store is the primary sales channel' }],
                ['Optimize online store experience', 'Expand high-performing channels']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('channel', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />

          {/* Geographic Distribution */}
          <ChartCard
            title="Top Regions by Sales"
            icon={MapPin}
            chartId="regionPerformance"
            onViewInsight={() =>
              handleViewInsight(
                'Geographic Distribution',
                [{ type: 'neutral', text: 'Dublin region shows highest sales concentration' }],
                ['Expand marketing in high-performing regions', 'Investigate low-performing areas']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('region', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />

          {/* Traffic Source Analysis */}
          <ChartCard
            title="Traffic Source Analysis"
            icon={Globe}
            chartId="trafficSource"
            onViewInsight={() =>
              handleViewInsight(
                'Traffic Source Analysis',
                [{ type: 'positive', text: 'Google is the primary traffic source' }],
                ['Increase Google Ads budget', 'Optimize SEO strategy', 'Diversify traffic sources']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('trafficSource', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />

          {/* Customer Lifetime Value */}
          <ChartCard
            title="Customer Lifetime Value"
            icon={TrendingUp}
            chartId="customerLifetimeValue"
            onViewInsight={() =>
              handleViewInsight(
                'Customer Lifetime Value',
                [{ type: 'positive', text: 'Customers with 20+ orders have highest average value' }],
                ['Create VIP programs for high-value customers', 'Focus on repeat purchase incentives']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('clv', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />

          {/* Email Subscription Status */}
          <ChartCard
            title="Email Subscription Status"
            icon={Mail}
            chartId="subscriptionStatus"
            onViewInsight={() => {
              const chartDataArrays = getChartDataArrays('subscriptionStatus');
              const chartSummary = chartDataArrays.summary;
              const chartSubscriptionStatus = chartDataArrays.subscriptionStatus;
              handleViewInsight(
                'Email Subscription Status',
                [{ type: 'attention', text: `${((chartSubscriptionStatus.find((x) => x.status === 'SUBSCRIBED')?.unique_customers || 0) / (chartSummary.totalCustomers || 1)) * 100}% of customers are subscribed` }],
                ['Improve email marketing campaigns', 'Re-engage unsubscribed customers']
              );
            }}
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('subscription', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="doughnut" data={chartData} options={donutChartOptions} />}
                </div>
              );
            }}
          />

          {/* Top Products by Sales */}
          <ChartCard
            title="Top 15 Products by Sales"
            icon={Package}
            chartId="topProducts"
            onViewInsight={() =>
              handleViewInsight(
                'Top Products',
                [{ type: 'positive', text: 'Top products driving revenue' }],
                ['Promote best-selling products', 'Analyze product performance']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('topProducts', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />

          {/* Day of Week Analysis */}
          <ChartCard
            title="Day of Week Sales Performance"
            icon={Calendar}
            chartId="dayOfWeekAnalysis"
            onViewInsight={() =>
              handleViewInsight(
                'Day of Week Patterns',
                [{ type: 'neutral', text: 'Weekday vs weekend patterns' }],
                ['Optimize campaigns for best performing days', 'Plan promotions strategically']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('dayOfWeek', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />
        </div>

          {/* Monthly/Daily Trend - Full Width */}
        <ChartCard
          title="Monthly Sales & Customer Trends"
          icon={TrendingUp}
          chartId="monthlyTrend"
          onViewInsight={() => {
            const chartDataArrays = getChartDataArrays('monthlyTrend');
            const chartMonthlyTrend = chartDataArrays.monthlyTrend;
            handleViewInsight(
              chartMonthlyTrend.length <= 31 ? 'Daily Trends' : 'Monthly Trends',
              [{ type: 'positive', text: 'Steady growth in sales and customer acquisition' }],
              ['Maintain current growth trajectory', 'Identify seasonal patterns', 'Monitor daily performance']
            );
          }}
          renderChart={(chartDataArrays) => {
            const chartData = buildChartData('monthlyTrend', chartDataArrays);
            const chartMonthlyTrend = chartDataArrays.monthlyTrend;
            return (
              <div className="h-80">
                {chartData && <ChartComponent type="bar" data={chartData} options={lineChartOptions} />}
              </div>
            );
          }}
        />

        {/* Charts Grid - Continued */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Platform Analysis */}
          <ChartCard
            title="Referring Platform Analysis"
            icon={Globe}
            chartId="platformAnalysis"
            onViewInsight={() =>
              handleViewInsight(
                'Platform Analysis',
                [{ type: 'positive', text: 'Direct traffic shows strong brand recognition' }],
                ['Leverage high-performing platforms', 'Optimize platform-specific campaigns']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('platform', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />

          {/* Traffic Type */}
          <ChartCard
            title="Traffic Type Performance"
            icon={TrendingUp}
            chartId="trafficType"
            onViewInsight={() =>
              handleViewInsight(
                'Traffic Type Performance',
                [{ type: 'neutral', text: 'Mix of paid and organic traffic' }],
                ['Optimize paid campaigns', 'Improve organic reach']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('trafficType', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />

          {/* Hour of Day Shopping Patterns */}
          <ChartCard
            title="Hour of Day Shopping Patterns"
            icon={Clock}
            chartId="hourlyPatterns"
            onViewInsight={() =>
              handleViewInsight(
                'Hourly Shopping Patterns',
                [{ type: 'positive', text: 'Peak shopping hours identified' }],
                ['Optimize marketing campaigns for peak hours', 'Schedule promotions during high-traffic times']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('hourlyPatterns', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="line" data={chartData} options={lineChartOptions} />}
                </div>
              );
            }}
          />

          {/* Country Distribution */}
          <ChartCard
            title="Country Distribution"
            icon={Globe}
            chartId="countryDistribution"
            onViewInsight={() =>
              handleViewInsight(
                'Country Distribution',
                [{ type: 'neutral', text: 'United Kingdom is the primary market' }],
                ['Expand marketing in primary countries', 'Explore opportunities in other regions']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('countryDistribution', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="doughnut" data={chartData} options={donutChartOptions} />}
                </div>
              );
            }}
          />

          {/* SMS Subscription Status */}
          <ChartCard
            title="SMS Subscription Status"
            icon={MessageSquare}
            chartId="smsSubscription"
            onViewInsight={() =>
              handleViewInsight(
                'SMS Subscription',
                [{ type: 'attention', text: 'Low SMS subscription rate' }],
                ['Improve SMS opt-in campaigns', 'Leverage SMS for customer engagement']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('smsSubscription', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="doughnut" data={chartData} options={donutChartOptions} />}
                </div>
              );
            }}
          />

          {/* Referring Medium Analysis */}
          <ChartCard
            title="Referring Medium Analysis"
            icon={Globe}
            chartId="mediumAnalysis"
            onViewInsight={() =>
              handleViewInsight(
                'Medium Analysis',
                [{ type: 'positive', text: 'Search is the primary medium' }],
                ['Optimize SEO strategy', 'Invest in high-performing mediums']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('mediumAnalysis', chartDataArrays);
              return (
                <div className="h-64">
                  {chartData && <ChartComponent type="bar" data={chartData} options={chartOptions} />}
                </div>
              );
            }}
          />
        </div>

        {/* Return Rate Trend - Full Width */}
        {returnTrend.length > 0 && (
          <ChartCard
            title="Return Rate Trend Over Time"
            icon={AlertTriangle}
            chartId="returnTrend"
            onViewInsight={() =>
              handleViewInsight(
                'Return Rate Trend',
                [{ type: 'attention', text: 'Monitor return rates monthly' }],
                ['Identify return patterns', 'Improve product quality', 'Optimize return policies']
              )
            }
            renderChart={(chartDataArrays) => {
              const chartData = buildChartData('returnTrend', chartDataArrays);
              return (
                <div className="h-80">
                  {chartData && <ChartComponent type="line" data={chartData} options={lineChartOptions} />}
                </div>
              );
            }}
          />
        )}

        {/* Top Customers Table */}
        <div 
          className="rounded-lg shadow-sm p-6"
          style={{
            background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 20 Customers by Sales</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Sales</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orders</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Lifetime Orders</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {topCustomers.map((customer, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{customer.name || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{customer.email || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                      {formatCurrency(customer.total_sales || 0)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">{customer.total_orders || 0}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">{customer.lifetime_orders || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <InsightModal
          isOpen={insightModal.isOpen}
          onClose={() => setInsightModal({ ...insightModal, isOpen: false })}
          chartTitle={insightModal.chartTitle}
          insights={insightModal.insights}
          recommendations={insightModal.recommendations}
          apiUrl={API}
        />
      </div>
    </Layout>
  );
};

export default CustomerInsights;

