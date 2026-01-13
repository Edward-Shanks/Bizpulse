import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import Layout from '@/components/Layout';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import ChartComponent from '@/components/ChartComponent';
import InsightModal from '@/components/InsightModal';
import { formatNumber, formatUnits } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { toast } from 'sonner';
import { TrendingUp, Euro, Package, Target, Lightbulb } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

const SalesAnalysis = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const filtersRef = useRef(null);

  // Multi-select filter states
  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  
  // Chart-level filters (individual filters that override global filters)
  const [chartFilters, setChartFilters] = useState({});
  
  // Chart-specific data (for charts with individual filters)
  const [chartData, setChartData] = useState({});
  
  // Chart-specific dynamic filter options (for cascading filters)
  const [chartFilterOptions, setChartFilterOptions] = useState({});
  // Track last fetched filterKey per chart to prevent duplicate fetches
  const lastFetchedFilterKeyRef = useRef({});

  const [insightModal, setInsightModal] = useState({
    isOpen: false,
    chartTitle: '',
    insights: [],
    recommendations: [],
    context: {},
  });

  // Load filters only once on mount or when token changes
  useEffect(() => {
    if (!token) {
      console.warn('No token available, skipping filter load');
      return;
    }

    const loadFilters = async () => {
      try {
        const res = await axios.get(`${API}/filters/options`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        
        const newFilters = res.data;
        setFilters(newFilters);
        filtersRef.current = newFilters;
      } catch (error) {
        console.error('Failed to load filters', error);
        if (error.response?.status === 401) {
          toast.error('Session expired. Please login again.');
        } else {
          toast.error('Unable to load filter options');
        }
        const emptyFilters = {
          years: [],
          months: [],
          businesses: [],
          channels: [],
        };
        setFilters(emptyFilters);
        filtersRef.current = emptyFilters;
      }
    };

    loadFilters();
  }, [token]);

  // Validate and clean up filter selections when filters change
  useEffect(() => {
    if (!filters) return;
    
    // Remove invalid selections (selections that no longer exist in the filtered options)
    // Use functional updates to avoid dependency on selected values
    setSelectedYears(prev => {
      if (prev.length === 0) return prev;
      const validYears = prev.filter(y => filters.years?.includes(y));
      return validYears.length !== prev.length ? validYears : prev;
    });
    
    setSelectedMonths(prev => {
      if (prev.length === 0) return prev;
      const validMonths = prev.filter(m => filters.months?.includes(m));
      return validMonths.length !== prev.length ? validMonths : prev;
    });
    
    setSelectedBusinesses(prev => {
      if (prev.length === 0) return prev;
      const validBusinesses = prev.filter(b => filters.businesses?.includes(b));
      return validBusinesses.length !== prev.length ? validBusinesses : prev;
    });
    
    setSelectedChannels(prev => {
      if (prev.length === 0) return prev;
      const validChannels = prev.filter(c => filters.channels?.includes(c));
      return validChannels.length !== prev.length ? validChannels : prev;
    });
  }, [filters]); // Only depend on filters, using functional updates to avoid dependency on selected values

  // Keep ref in sync with filters
  useEffect(() => {
    filtersRef.current = filters;
  }, [filters]);

  useEffect(() => {
    if (!token) {
      console.warn('No token available, skipping data load');
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        if (selectedYears.length) params.set('years', selectedYears.join(','));
        if (selectedMonths.length) params.set('months', selectedMonths.join(','));
        if (selectedBusinesses.length) params.set('businesses', selectedBusinesses.join(','));
        if (selectedChannels.length) params.set('channels', selectedChannels.join(','));

        const url = `${API}/analytics/executive-overview${params.toString() ? `?${params.toString()}` : ''}`;
        const res = await axios.get(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
      } catch (error) {
        console.error('Failed to load sales analysis', error);
        if (error.response?.status === 401) {
          toast.error('Session expired. Please login again.');
          // Optionally redirect to login
          // window.location.href = '/login';
        } else {
          toast.error('Failed to load sales analysis data');
        }
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [token, selectedYears, selectedMonths, selectedBusinesses, selectedChannels]);

  // Fetch dynamic filter options for a specific chart based on merged filters
  const fetchChartFilterOptions = useCallback(async (chartId, mergedFilters) => {
    if (!token) return;
    
    try {
      const params = new URLSearchParams();
      if (mergedFilters.years.length) params.set('years', mergedFilters.years.join(','));
      if (mergedFilters.months.length) params.set('months', mergedFilters.months.join(','));
      if (mergedFilters.businesses.length) params.set('businesses', mergedFilters.businesses.join(','));
      
      const url = `${API}/filters/options${params.toString() ? `?${params.toString()}` : ''}`;
      const res = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      setChartFilterOptions(prev => ({
        ...prev,
        [chartId]: res.data
      }));
    } catch (error) {
      console.error(`Failed to load filter options for chart ${chartId}:`, error);
      // Use current filters from ref instead of closure
      setChartFilterOptions(prev => {
        const currentFilters = filtersRef.current || { years: [], months: [], businesses: [], channels: [] };
        return {
          ...prev,
          [chartId]: currentFilters
        };
      });
    }
  }, [token]); // Remove filters from dependencies to prevent recreation

  // Helper function to merge global and individual filters (individual overrides global)
  const getMergedFilters = (chartName = null) => {
    const globalFilters = {
      years: selectedYears,
      months: selectedMonths,
      businesses: selectedBusinesses,
      channels: selectedChannels,
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
      businesses: individualFilters.hasOwnProperty('businesses')
        ? individualFilters.businesses 
        : globalFilters.businesses,
      channels: individualFilters.hasOwnProperty('channels')
        ? individualFilters.channels 
        : globalFilters.channels,
    };
  };

  // Reset individual chart filters and chart data when global filters change
  useEffect(() => {
    setChartFilters({});
    setChartData({});
    // Clear the fetched filter keys when global filters change
    lastFetchedFilterKeyRef.current = {};
  }, [selectedYears, selectedMonths, selectedBusinesses, selectedChannels]);

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
          businesses: individualFiltersOverride.hasOwnProperty('businesses')
            ? individualFiltersOverride.businesses 
            : selectedBusinesses,
          channels: individualFiltersOverride.hasOwnProperty('channels')
            ? individualFiltersOverride.channels 
            : selectedChannels,
        };
      } else {
        mergedFilters = getMergedFilters(chartName);
      }
      
      const params = new URLSearchParams();
      if (mergedFilters.years.length) params.set('years', mergedFilters.years.join(','));
      if (mergedFilters.months.length) params.set('months', mergedFilters.months.join(','));
      if (mergedFilters.businesses.length) params.set('businesses', mergedFilters.businesses.join(','));
      if (mergedFilters.channels.length) params.set('channels', mergedFilters.channels.join(','));

      const url = `${API}/analytics/executive-overview${params.toString() ? `?${params.toString()}` : ''}`;
      const res = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      setChartData(prev => ({
        ...prev,
        [chartName]: res.data
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
      'business': 'businesses',
      'businesses': 'businesses',
      'channel': 'channels',
      'channels': 'channels',
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
    const yearlyData = (chartDataToUse?.yearly_performance || []).filter(item => item && item.Year);
    const businessData = (chartDataToUse?.business_performance || []).filter(item => item && item.Business && item.Revenue > 0);
    
    return { yearlyData, businessData, chartDataToUse };
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

          {/* KPI Cards Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <Skeleton className="h-4 w-24 mb-3" />
                    <Skeleton className="h-10 w-32 mb-2" />
                    <Skeleton className="h-3 w-full" />
                  </div>
                  <Skeleton className="w-10 h-10 rounded-full" />
                </div>
              </div>
            ))}
          </div>

          {/* Charts Grid Skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <Skeleton className="h-6 w-40" />
                  <Skeleton className="h-8 w-28 rounded" />
                </div>
                <Skeleton className="h-64 w-full rounded" />
              </div>
            ))}
          </div>
        </div>
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-600">No data available</p>
        </div>
      </Layout>
    );
  }

  // Global data arrays (for cards and charts without individual filters)
  const yearlyData = (data?.yearly_performance || []).filter(item => item && item.Year);
  const businessData = (data?.business_performance || []).filter(
    item => item && item.Business && item.Revenue > 0
  );
  const channelData = (data?.channel_performance || []).filter(
    item => item && item.Channel && item.Revenue > 0
  );
  const monthlyTrend = data?.monthly_trend || [];

  // KPIs
  const totalRevenue =
    data?.total_revenue ?? yearlyData.reduce((sum, item) => sum + (item.Revenue || 0), 0);
  const totalUnits =
    data?.total_units ?? yearlyData.reduce((sum, item) => sum + (item.Cases || 0), 0);
  const totalProfit =
    data?.total_profit ?? yearlyData.reduce((sum, item) => sum + (item.Gross_Profit || 0), 0);
  const avgPrice = totalUnits > 0 ? totalRevenue / totalUnits : 0;

  const baseInsightContext = {
    selectedYears,
    selectedMonths,
    selectedBusinesses,
    selectedChannels,
    yearlyData,
    businessData,
    channelData,
    monthlyTrend,
    totalRevenue,
    totalUnits,
    totalProfit,
    avgPrice,
  };

  const getInsightPayload = (chartId) => {
    const defaultInsights = [
      {
        type: 'info',
        text: 'Use the filters to explore trends by year, business, or channel.',
      },
    ];
    const defaultRecommendations = [
      'Ask the AI assistant to surface growth drivers for the selected filters.',
      'Compare channel performance to confirm alignment with strategic goals.',
    ];
    const safeContext = { ...baseInsightContext, chartId };

    if (!yearlyData.length) {
      return {
        insights: defaultInsights,
        recommendations: defaultRecommendations,
        context: safeContext,
      };
    }

    switch (chartId) {
      case 'salesByYear': {
        const sortedYears = [...yearlyData].sort((a, b) => (b?.Revenue || 0) - (a?.Revenue || 0));
        const bestYear = sortedYears[0] || {};
        const worstYear = sortedYears[sortedYears.length - 1] || {};
        const delta =
          bestYear?.Revenue && worstYear?.Revenue
            ? ((bestYear.Revenue - worstYear.Revenue) / Math.max(worstYear.Revenue, 1)) * 100
            : 0;

        return {
          insights: [
            {
              type: 'positive',
              text: `${bestYear?.Year || 'Top Year'} delivered ${formatNumber(
                bestYear?.Revenue || 0
              )} revenue.`,
            },
            {
              type: 'attention',
              text: `Revenue variance between best and lowest year is ${delta.toFixed(1)}%.`,
            },
          ],
          recommendations: [
            'Review campaigns that contributed to the best performing year.',
            'Use AI insights to identify risks in years showing slower growth.',
          ],
          context: { ...safeContext, metric: 'yearly_revenue' },
        };
      }
      case 'salesByBusiness': {
        const sortedBusiness = [...businessData].sort(
          (a, b) => (b?.Revenue || 0) - (a?.Revenue || 0)
        );
        const topBusiness = sortedBusiness[0] || {};
        const totalBusinessRevenue = businessData.reduce(
          (sum, item) => sum + (item?.Revenue || 0),
          0
        );
        const share =
          totalBusinessRevenue > 0
            ? ((topBusiness?.Revenue || 0) / totalBusinessRevenue) * 100
            : 0;

        return {
          insights: [
            {
              type: 'positive',
              text: `${topBusiness?.Business || 'Leading business'} leads revenue with ${formatNumber(
                topBusiness?.Revenue || 0
              )}.`,
            },
            {
              type: 'neutral',
              text: `Top business accounts for ${share.toFixed(1)}% of total revenue.`,
            },
          ],
          recommendations: [
            'Replicate successful go-to-market motions from the leading business.',
            'Assess underperforming businesses for margin or cost issues.',
          ],
          context: { ...safeContext, metric: 'business_revenue' },
        };
      }
      default:
        return {
          insights: defaultInsights,
          recommendations: defaultRecommendations,
          context: safeContext,
        };
    }
  };

  const handleViewInsight = (chartTitle, chartId) => {
    const payload = getInsightPayload(chartId);
    setInsightModal({
      isOpen: true,
      chartTitle,
      insights: payload.insights,
      recommendations: payload.recommendations,
      context: payload.context,
    });
  };

  const closeInsightModal = () => {
    setInsightModal((prev) => ({ ...prev, isOpen: false }));
  };

  const ChartCard = ({ title, chartId, children, renderChart }) => {
    // Create stable keys for memoization
    const yearsKey = selectedYears.join(',');
    const monthsKey = selectedMonths.join(',');
    const businessesKey = selectedBusinesses.join(',');
    const channelsKey = selectedChannels.join(',');
    const chartFilterKey = chartId ? [
      chartFilters[chartId]?.years?.join(',') || '',
      chartFilters[chartId]?.months?.join(',') || '',
      chartFilters[chartId]?.businesses?.join(',') || '',
      chartFilters[chartId]?.channels?.join(',') || ''
    ].join('|') : '';
    
    // Memoize merged filters to prevent new object on every render
    const mergedFilters = useMemo(() => getMergedFilters(chartId), [
      chartId,
      yearsKey,
      monthsKey,
      businessesKey,
      channelsKey,
      chartFilterKey
    ]);
    
    // Memoize filter values as strings for stable comparison
    const yearsStr = mergedFilters.years.join(',');
    const monthsStr = mergedFilters.months.join(',');
    const businessesStr = mergedFilters.businesses.join(',');
    const filterKey = useMemo(() => {
      return `${chartId}-${yearsStr}-${monthsStr}-${businessesStr}`;
    }, [chartId, yearsStr, monthsStr, businessesStr]);
    
    // Get chart-specific filter options (dynamic/cascading)
    const chartOptions = chartFilterOptions[chartId] || filters;
    
    // Fetch dynamic filter options when merged filters change (using stable key)
    useEffect(() => {
      // Only fetch if filterKey has changed for this chart
      if (lastFetchedFilterKeyRef.current[chartId] !== filterKey) {
        lastFetchedFilterKeyRef.current[chartId] = filterKey;
        fetchChartFilterOptions(chartId, mergedFilters);
      }
    }, [filterKey, chartId, fetchChartFilterOptions, mergedFilters]); // fetchChartFilterOptions is stable (only depends on token)
    
    // Get chart-specific data arrays
    const { yearlyData: chartYearlyData, businessData: chartBusinessData } = getChartDataArrays(chartId);
    
    return (
      <div 
        className="rounded-lg p-5 relative"
        style={{
          background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
          border: '1px solid rgba(0, 0, 0, 0.1)'
        }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <button
            onClick={() => handleViewInsight(title, chartId)}
            className="px-4 py-1.5 bg-orange-100 hover:bg-orange-200 text-orange-700 rounded-lg text-sm font-medium transition flex items-center gap-2"
          >
            <Lightbulb className="w-4 h-4" />
            View Insight
          </button>
        </div>
        
        {/* Chart Filters - Show merged filter values (individual overrides global) with search functionality - Only Years, Months, Businesses */}
        <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="relative" style={{ zIndex: 1000 }}>
            <MultiSelectFilter
              options={chartOptions?.years || []}
              selectedValues={mergedFilters.years.map(y => String(y))}
              onChange={async (selected) => {
                const yearNumbers = selected.map(y => Number(y));
                await handleChartFilterChange(chartId, 'years', yearNumbers);
              }}
              placeholder="All Years"
            />
          </div>
          
          <div className="relative" style={{ zIndex: 999 }}>
            <MultiSelectFilter
              options={chartOptions?.months || []}
              selectedValues={mergedFilters.months}
              onChange={async (selected) => {
                await handleChartFilterChange(chartId, 'months', selected);
              }}
              placeholder="All Months"
            />
          </div>
          
          <div className="relative" style={{ zIndex: 998 }}>
            <MultiSelectFilter
              options={chartOptions?.businesses || []}
              selectedValues={mergedFilters.businesses}
              onChange={async (selected) => {
                await handleChartFilterChange(chartId, 'businesses', selected);
              }}
              placeholder="All Businesses"
            />
          </div>
        </div>
        
        {/* Render chart with chart-specific data */}
        {renderChart ? renderChart({ yearlyData: chartYearlyData, businessData: chartBusinessData }) : children}
      </div>
    );
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top' },
      tooltip: {
        enabled: true,
        displayColors: true,
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y || 0;
            // Always show value, even if very small
            return `${label}: ${formatNumber(value)}`;
          },
          afterLabel: (context) => {
            const value = context.parsed.y || 0;
            // Show exact value for very small numbers
            if (value > 0 && value < 1) {
              return `Exact: €${value.toFixed(4)}`;
            }
            return '';
          },
        },
        padding: 8,
        titleFont: { size: 12, weight: 'bold' },
        bodyFont: { size: 11 },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => formatNumber(value),
        },
        grid: { color: '#f3f4f6' },
      },
      x: {
        grid: { display: false },
      },
    },
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Sales Analysis</h1>
          <p className="text-gray-600 dark:text-gray-400">Comprehensive sales performance metrics and trends</p>
        </div>

        {/* Multi-Select Filters */}
        <div 
          className="rounded-lg p-4"
          style={{
            background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MultiSelectFilter
              label="Year"
              options={filters?.years || []}
              selectedValues={selectedYears}
              onChange={setSelectedYears}
              placeholder="All Years"
            />
            <MultiSelectFilter
              label="Month"
              options={filters?.months || []}
              selectedValues={selectedMonths}
              onChange={setSelectedMonths}
              placeholder="All Months"
            />
            <MultiSelectFilter
              label="Business"
              options={filters?.businesses || []}
              selectedValues={selectedBusinesses}
              onChange={setSelectedBusinesses}
              placeholder="All Businesses"
            />
            <MultiSelectFilter
              label="Channel"
              options={filters?.channels || []}
              selectedValues={selectedChannels}
              onChange={setSelectedChannels}
              placeholder="All Channels"
            />
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatNumber(totalRevenue)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Sales</p>
              <p className="text-xs text-white opacity-75">Last period comparison coming soon</p>
            </div>
          </div>

          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatUnits(totalUnits)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Cases</p>
              <p className="text-xs text-white opacity-75">Track unit growth with filters</p>
            </div>
          </div>

          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatNumber(avgPrice)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Avg Price/Case</p>
              <p className="text-xs text-white opacity-75">Combine filters to refine insights</p>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard 
            title="Sales by Year" 
            chartId="salesByYear"
            renderChart={({ yearlyData: chartYearlyData }) => (
              <div className="h-80">
                {chartYearlyData.length > 0 ? (
                  <ChartComponent
                    type="bar"
                    data={{
                      labels: chartYearlyData.map(item => item.Year),
                      datasets: [
                        {
                          label: 'Revenue',
                          data: chartYearlyData.map(item => item.Revenue),
                          backgroundColor: '#1e293b',
                          borderRadius: 6,
                        },
                        {
                          label: 'Gross Profit',
                          data: chartYearlyData.map(item => item.Gross_Profit),
                          backgroundColor: '#EDD5B1',
                          borderRadius: 6,
                        },
                      ],
                    }}
                    options={chartOptions}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data available</p>
                )}
              </div>
            )}
          />

          <ChartCard 
            title="Sales by Business" 
            chartId="salesByBusiness"
            renderChart={({ businessData: chartBusinessData }) => (
              <div className="h-80">
                {chartBusinessData.length > 0 ? (
                  <ChartComponent
                    type="bar"
                    data={{
                      labels: chartBusinessData.map(item => item.Business),
                      datasets: [
                        {
                          label: 'Revenue',
                          data: chartBusinessData.map(item => item.Revenue),
                          backgroundColor: '#1e293b',
                          borderRadius: 6,
                        },
                        {
                          label: 'Gross Profit',
                          data: chartBusinessData.map(item => item.Gross_Profit),
                          backgroundColor: '#EDD5B1',
                          borderRadius: 6,
                        },
                      ],
                    }}
                    options={chartOptions}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data available</p>
                )}
              </div>
            )}
          />
        </div>
      </div>

      <InsightModal
        isOpen={insightModal.isOpen}
        onClose={closeInsightModal}
        chartTitle={insightModal.chartTitle}
        insights={insightModal.insights}
        recommendations={insightModal.recommendations}
        onExploreDeep={() => {}}
        context={insightModal.context}
      />
    </Layout>
  );
};

export default SalesAnalysis;
