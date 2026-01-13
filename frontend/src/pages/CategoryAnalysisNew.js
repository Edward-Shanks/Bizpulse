import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import ChartComponent from '@/components/ChartComponent';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import InsightModal from '@/components/InsightModal';
import { formatNumber } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { useTheme } from '@/contexts/ThemeContext';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { Layers, TrendingUp, Euro, Lightbulb } from 'lucide-react';

const CategoryAnalysis = () => {
  const { token } = useAuth();
  const { theme } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);

  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedSubCategories, setSelectedSubCategories] = useState([]);
  
  // Chart-level filters (individual filters that override global filters)
  const [chartFilters, setChartFilters] = useState({});
  
  // Chart-specific data (for charts with individual filters)
  const [chartData, setChartData] = useState({});

  const [insightModal, setInsightModal] = useState({
    isOpen: false,
    chartTitle: '',
    insights: [],
    recommendations: [],
    context: {},
  });

  useEffect(() => {
    if (!token) return;

    const loadFilters = async () => {
      try {
        // Build query params with current filter selections for dynamic filtering
        const params = new URLSearchParams();
        if (selectedYears.length) params.set('years', selectedYears.join(','));
        if (selectedMonths.length) params.set('months', selectedMonths.join(','));
        if (selectedBusinesses.length) params.set('businesses', selectedBusinesses.join(','));
        if (selectedChannels.length) params.set('channels', selectedChannels.join(','));
        if (selectedCategories.length) params.set('categories', selectedCategories.join(','));

        const url = `${API}/filters/options${params.toString() ? `?${params.toString()}` : ''}`;
        const res = await axios.get(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        
        const newFilters = res.data;
        setFilters(newFilters);
        
        // Remove invalid selections
        if (selectedYears.length > 0) {
          const validYears = selectedYears.filter(y => newFilters.years.includes(y));
          if (validYears.length !== selectedYears.length) {
            setSelectedYears(validYears);
          }
        }
        if (selectedMonths.length > 0) {
          const validMonths = selectedMonths.filter(m => newFilters.months.includes(m));
          if (validMonths.length !== selectedMonths.length) {
            setSelectedMonths(validMonths);
          }
        }
        if (selectedBusinesses.length > 0) {
          const validBusinesses = selectedBusinesses.filter(b => newFilters.businesses.includes(b));
          if (validBusinesses.length !== selectedBusinesses.length) {
            setSelectedBusinesses(validBusinesses);
          }
        }
        if (selectedChannels.length > 0) {
          const validChannels = selectedChannels.filter(c => newFilters.channels.includes(c));
          if (validChannels.length !== selectedChannels.length) {
            setSelectedChannels(validChannels);
          }
        }
        if (selectedCategories.length > 0) {
          const validCategories = selectedCategories.filter(c => newFilters.categories.includes(c));
          if (validCategories.length !== selectedCategories.length) {
            setSelectedCategories(validCategories);
          }
        }
        if (selectedSubCategories.length > 0) {
          const validSubCategories = selectedSubCategories.filter(s => newFilters.sub_categories.includes(s));
          if (validSubCategories.length !== selectedSubCategories.length) {
            setSelectedSubCategories(validSubCategories);
          }
        }
      } catch (error) {
        console.error('Failed to load filters', error);
        toast.error('Unable to load filter options');
        setFilters({
          years: [],
          months: [],
          businesses: [],
          channels: [],
          categories: [],
          sub_categories: [],
        });
      }
    };

    loadFilters();
  }, [
    token,
    selectedYears,
    selectedMonths,
    selectedBusinesses,
    selectedChannels,
    selectedCategories,
    selectedSubCategories,
  ]);

  useEffect(() => {
    if (!token) return;

    const loadData = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        if (selectedYears.length) params.set('years', selectedYears.join(','));
        if (selectedMonths.length) params.set('months', selectedMonths.join(','));
        if (selectedBusinesses.length) params.set('businesses', selectedBusinesses.join(','));
        if (selectedChannels.length) params.set('channels', selectedChannels.join(','));
        if (selectedCategories.length) params.set('categories', selectedCategories.join(','));
        if (selectedSubCategories.length) params.set('sub_categories', selectedSubCategories.join(','));

        const url = `${API}/analytics/category-analysis${params.toString() ? `?${params.toString()}` : ''}`;
        const res = await axios.get(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
      } catch (error) {
        console.error('Failed to load category analysis', error);
        toast.error('Failed to load category analysis data');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [
    token,
    selectedYears,
    selectedMonths,
    selectedBusinesses,
    selectedChannels,
    selectedCategories,
    selectedSubCategories,
  ]);

  // Helper function to merge global and individual filters (individual overrides global)
  const getMergedFilters = (chartName = null) => {
    const globalFilters = {
      years: selectedYears,
      months: selectedMonths,
      businesses: selectedBusinesses,
      channels: selectedChannels,
      categories: selectedCategories,
      sub_categories: selectedSubCategories,
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
      categories: individualFilters.hasOwnProperty('categories')
        ? individualFilters.categories 
        : globalFilters.categories,
      sub_categories: individualFilters.hasOwnProperty('sub_categories')
        ? individualFilters.sub_categories 
        : globalFilters.sub_categories,
    };
  };

  // Reset individual chart filters and chart data when global filters change
  useEffect(() => {
    setChartFilters({});
    setChartData({});
  }, [selectedYears, selectedMonths, selectedBusinesses, selectedChannels, selectedCategories, selectedSubCategories]);

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
          categories: individualFiltersOverride.hasOwnProperty('categories')
            ? individualFiltersOverride.categories 
            : selectedCategories,
          sub_categories: individualFiltersOverride.hasOwnProperty('sub_categories')
            ? individualFiltersOverride.sub_categories 
            : selectedSubCategories,
        };
      } else {
        mergedFilters = getMergedFilters(chartName);
      }
      
      const params = new URLSearchParams();
      if (mergedFilters.years.length) params.set('years', mergedFilters.years.join(','));
      if (mergedFilters.months.length) params.set('months', mergedFilters.months.join(','));
      if (mergedFilters.businesses.length) params.set('businesses', mergedFilters.businesses.join(','));
      if (mergedFilters.channels.length) params.set('channels', mergedFilters.channels.join(','));
      if (mergedFilters.categories.length) params.set('categories', mergedFilters.categories.join(','));
      if (mergedFilters.sub_categories.length) params.set('sub_categories', mergedFilters.sub_categories.join(','));

      const url = `${API}/analytics/category-analysis${params.toString() ? `?${params.toString()}` : ''}`;
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
      'category': 'categories',
      'categories': 'categories',
      'sub_category': 'sub_categories',
      'sub_categories': 'sub_categories',
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
    const categoryData = (chartDataToUse?.category_performance || []).slice(0, 15);
    const subCategoryData = (chartDataToUse?.subcategory_performance || []).slice(0, 20);
    
    return { categoryData, subCategoryData, chartDataToUse };
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
              <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5">
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
          <p className="text-gray-600 dark:text-gray-400">No data available</p>
        </div>
      </Layout>
    );
  }

  // Global data arrays (for cards and charts without individual filters)
  const categoryData = (data?.category_performance || []).slice(0, 15);
  const subcategoryData = (data?.subcategory_performance || []).slice(0, 20);
  const totalRevenue = data?.total_revenue ?? categoryData.reduce((sum, item) => sum + (item.Revenue || 0), 0);
  const totalProfit = data?.total_profit ?? categoryData.reduce((sum, item) => sum + (item.Gross_Profit || 0), 0);
  const activeCategories = data?.active_categories ?? categoryData.filter(item => item && item.Category && item.Revenue > 0).length;
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;

  const colors = [
    '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#10b981',
    '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1',
    '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
  ];

  // Colors with reduced opacity for multi-color graphs
  const colorsWithOpacity = colors.map(color => {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.5)`;
  });

  const baseInsightContext = {
    selectedYears,
    selectedMonths,
    selectedBusinesses,
    selectedChannels,
    selectedCategories,
    selectedSubCategories,
    categoryData,
    subcategoryData,
    totalRevenue,
    totalProfit,
    activeCategories,
  };

  const getInsightPayload = (chartId) => {
    const defaultInsights = [
      { type: 'info', text: 'Use the filters to focus on specific categories, channels, or sub-categories.' },
    ];
    const defaultRecommendations = [
      'Ask the AI assistant to compare category performance across filters.',
      'Drill into sub-categories to uncover hidden growth opportunities.',
    ];
    const safeContext = { ...baseInsightContext, chartId };

    if (!categoryData.length) {
      return {
        insights: defaultInsights,
        recommendations: defaultRecommendations,
        context: safeContext,
      };
    }

    switch (chartId) {
      case 'categoryRevenue': {
        const topCategory = categoryData[0] || {};
        const top5Revenue = categoryData.slice(0, 5).reduce((sum, item) => sum + (item?.Revenue || 0), 0);
        const shareTop = totalRevenue > 0 ? ((topCategory?.Revenue || 0) / totalRevenue) * 100 : 0;
        const shareTop5 = totalRevenue > 0 ? (top5Revenue / totalRevenue) * 100 : 0;
        return {
          insights: [
            {
              type: 'positive',
              text: `${topCategory?.Category || 'Top category'} leads revenue at ${formatNumber(topCategory?.Revenue || 0)} (${shareTop.toFixed(1)}% share).`,
            },
            {
              type: 'neutral',
              text: `Top 5 categories account for ${shareTop5.toFixed(1)}% of overall revenue.`,
            },
          ],
          recommendations: [
            'Validate marketing investments behind leading categories.',
            'Explore tail categories for margin-friendly growth.',
          ],
          context: { ...safeContext, metric: 'category_revenue' },
        };
      }
      case 'categoryDistribution': {
        const topCategory = categoryData[0] || {};
        return {
          insights: [
            {
              type: 'positive',
              text: `${topCategory?.Category || 'Leading category'} dominates mix with ${formatNumber(topCategory?.Revenue || 0)} in revenue.`,
            },
            {
              type: 'attention',
              text: 'Distribution curve highlights concentration risk—consider diversification strategies.',
            },
          ],
          recommendations: [
            'Review channel performance for top categories to ensure coverage.',
            'Evaluate pricing and promotions for long-tail categories.',
          ],
          context: { ...safeContext, metric: 'distribution' },
        };
      }
      case 'categoryProfit': {
        const profitSorted = [...categoryData].sort(
          (a, b) => (b?.Gross_Profit || 0) - (a?.Gross_Profit || 0)
        );
        const topProfitCategory = profitSorted[0] || {};
        const marginTop = topProfitCategory?.Revenue
          ? ((topProfitCategory?.Gross_Profit || 0) / topProfitCategory.Revenue) * 100
          : 0;
        return {
          insights: [
            {
              type: 'positive',
              text: `${topProfitCategory?.Category || 'Top category'} delivers ${formatNumber(topProfitCategory?.Gross_Profit || 0)} profit.`,
            },
            {
              type: 'neutral',
              text: `Margin sits at ${marginTop.toFixed(1)}% vs portfolio average ${avgMargin.toFixed(1)}%.`,
            },
          ],
          recommendations: [
            'Replicate pricing and mix strategies from high-margin categories.',
            'Use AI to benchmark profit conversion across businesses or channels.',
          ],
          context: { ...safeContext, metric: 'category_profit' },
        };
      }
      case 'subcategoryRevenue': {
        const topSubCategory = subcategoryData[0] || {};
        return {
          insights: [
            {
              type: 'positive',
              text: `${topSubCategory?.Sub_Category || 'Top sub-category'} is the strongest sub-category with ${formatNumber(topSubCategory?.Revenue || 0)} revenue.`,
            },
            {
              type: 'attention',
              text: `Review the parent category (${topSubCategory?.Category || 'N/A'}) for additional growth levers.`,
            },
          ],
          recommendations: [
            'Deep dive into sub-category drivers (price, promo, channel mix).',
            'Explore adjacent sub-categories for cross-sell opportunities.',
          ],
          context: { ...safeContext, metric: 'subcategory_revenue' },
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
    const mergedFilters = getMergedFilters(chartId);
    
    // Get chart-specific data arrays
    const { categoryData: chartCategoryData, subCategoryData: chartSubCategoryData } = getChartDataArrays(chartId);
    
    return (
      <div 
        className="rounded-lg p-6"
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
        
        {/* Chart Filters - Show merged filter values (individual overrides global) */}
        <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <select
            value={mergedFilters.years.length === 1 ? mergedFilters.years[0] : mergedFilters.years.length > 1 ? 'multiple' : 'all'}
            onChange={async (e) => {
              const value = e.target.value;
              if (value === 'all') {
                await handleChartFilterChange(chartId, 'years', []);
              } else {
                await handleChartFilterChange(chartId, 'years', [Number(value)]);
              }
            }}
            className="text-sm border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 flex-shrink-0"
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
            className="text-sm border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 flex-shrink-0"
          >
            <option value="all">All Months</option>
            {filters?.months?.map(month => (
              <option key={month} value={month}>{month}</option>
            ))}
          </select>
          
          <select
            value={mergedFilters.businesses.length === 1 ? mergedFilters.businesses[0] : mergedFilters.businesses.length > 1 ? 'multiple' : 'all'}
            onChange={async (e) => {
              const value = e.target.value;
              if (value === 'all') {
                await handleChartFilterChange(chartId, 'businesses', []);
              } else {
                await handleChartFilterChange(chartId, 'businesses', [value]);
              }
            }}
            className="text-sm border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 flex-shrink-0"
          >
            <option value="all">All Businesses</option>
            {filters?.businesses?.map(business => (
              <option key={business} value={business}>{business}</option>
            ))}
          </select>
        </div>
        
        {/* Render chart with chart-specific data */}
        {renderChart ? renderChart({ categoryData: chartCategoryData, subCategoryData: chartSubCategoryData }) : children}
      </div>
    );
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Category Analysis</h1>
          <p className="text-gray-600 dark:text-gray-400">Product category and sub-category performance</p>
        </div>

        <div 
          className="rounded-lg p-5"
          style={{
            background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
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
            <MultiSelectFilter
              label="Category"
              options={filters?.categories || []}
              selectedValues={selectedCategories}
              onChange={setSelectedCategories}
              placeholder="All Categories"
            />
            <MultiSelectFilter
              label="Sub-Category"
              options={filters?.sub_categories || []}
              selectedValues={selectedSubCategories}
              onChange={setSelectedSubCategories}
              placeholder="All Sub-Categories"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            className="rounded-lg p-6 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatNumber(totalRevenue)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Revenue</p>
              <p className="text-xs text-white opacity-75">Across categories</p>
            </div>
          </div>

          <div 
            className="rounded-lg p-6 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatNumber(totalProfit)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Profit</p>
              <p className="text-xs text-white opacity-75">{avgMargin.toFixed(1)}% margin</p>
            </div>
          </div>

          <div 
            className="rounded-lg p-6 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {activeCategories}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Categories</p>
              <p className="text-xs text-white opacity-75">Active categories</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard 
            title="Revenue by Category" 
            chartId="categoryRevenue"
            renderChart={({ categoryData: chartCategoryData }) => {
              // Sort by Revenue descending (largest first)
              const sortedCategoryData = [...chartCategoryData].sort((a, b) => (b.Revenue || 0) - (a.Revenue || 0));
              const categoryLabels = sortedCategoryData.map(item => item.Category || 'Unknown');
              return (
              <div className="h-96">
                {sortedCategoryData.length > 0 ? (
                  <ChartComponent
                    type="bar"
                    data={{
                      labels: categoryLabels,
                      datasets: [{
                        label: 'Revenue',
                        data: sortedCategoryData.map(item => item.Revenue || 0),
                        backgroundColor: colorsWithOpacity,
                        borderRadius: 6
                      }]
                    }}
                    options={{
                      indexAxis: 'y',
                      responsive: true,
                      maintainAspectRatio: false,
                      interaction: {
                        intersect: false,
                        mode: 'nearest',
                      },
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          enabled: true,
                          displayColors: true,
                          intersect: false,
                          mode: 'nearest',
                          filter: null, // Don't filter tooltip items
                          callbacks: {
                            title: (tooltipItems) => {
                              // For horizontal bar charts, get label using dataIndex
                              if (tooltipItems && tooltipItems.length > 0) {
                                const item = tooltipItems[0];
                                const dataIndex = item.dataIndex;
                                
                                // Primary method: Get from chart's data labels (most reliable)
                                if (item.chart && item.chart.data && item.chart.data.labels) {
                                  const chartLabel = item.chart.data.labels[dataIndex];
                                  if (chartLabel) {
                                    return String(chartLabel);
                                  }
                                }
                                
                                // Fallback: Get from stored categoryLabels array
                                if (dataIndex !== undefined && dataIndex >= 0 && categoryLabels && categoryLabels[dataIndex]) {
                                  return String(categoryLabels[dataIndex]);
                                }
                                
                                // Last fallback: Try item properties
                                return String(item.label || item.yLabel || 'Unknown');
                              }
                              return 'Unknown';
                            },
                            label: (context) => {
                              const value = context.parsed.x || 0;
                              // Always show value, even if very small
                              return `Revenue: ${formatNumber(value)}`;
                            },
                            afterLabel: (context) => {
                              const value = context.parsed.x || 0;
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
                        }
                      },
                      scales: {
                        x: {
                          beginAtZero: true,
                          ticks: { callback: (value) => formatNumber(value) },
                          grid: { color: '#f3f4f6' }
                        },
                        y: { grid: { display: false } }
                      }
                    }}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data available</p>
                )}
              </div>
              );
            }}
          />

          <ChartCard 
            title="Category Distribution" 
            chartId="categoryDistribution"
            renderChart={({ categoryData: chartCategoryData }) => {
              // Sort by Revenue descending (largest first), then take top 10
              const topCategories = [...chartCategoryData].sort((a, b) => (b.Revenue || 0) - (a.Revenue || 0)).slice(0, 10);
              return (
                <div className="h-96">
                  {topCategories.length > 0 ? (
                    <ChartComponent
                      type="doughnut"
                      data={{
                        labels: topCategories.map(item => item.Category || 'Unknown'),
                        datasets: [{
                          data: topCategories.map(item => item.Revenue || 0),
                          backgroundColor: colorsWithOpacity,
                          borderWidth: 2,
                          borderColor: '#fff'
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { 
                            position: 'right',
                            labels: { boxWidth: 12, padding: 8, font: { size: 10 } }
                          },
                          tooltip: {
                            callbacks: {
                              label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ${formatNumber(value)}`;
                              }
                            }
                          }
                        }
                      }}
                    />
                  ) : (
                    <p className="text-center text-gray-500 py-8">No data available</p>
                  )}
                </div>
              );
            }}
          />

          <ChartCard 
            title="Profit by Category (Top 10)" 
            chartId="categoryProfit"
            renderChart={({ categoryData: chartCategoryData }) => {
              // Sort by Gross_Profit descending (largest first), then take top 10
              const topCategories = [...chartCategoryData].sort((a, b) => (b.Gross_Profit || 0) - (a.Gross_Profit || 0)).slice(0, 10);
              return (
                <div className="h-80">
                  {topCategories.length > 0 ? (
                    <ChartComponent
                      type="bar"
                      data={{
                        labels: topCategories.map(item => item.Category || 'Unknown'),
                        datasets: [{
                          label: 'Profit',
                          data: topCategories.map(item => item.Gross_Profit || 0),
                          backgroundColor: '#1e293b',
                          borderRadius: 8
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false },
                        tooltip: {
                          enabled: true,
                          displayColors: true,
                          callbacks: {
                            title: (context) => {
                              // Show the category name from the label
                              const label = context[0]?.label || '';
                              return label || 'Unknown';
                            },
                            label: (context) => {
                              const value = context.parsed.y || 0;
                              // Always show value, even if very small
                              return `Profit: ${formatNumber(value)}`;
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
                        }
                        },
                        scales: {
                          y: {
                            beginAtZero: true,
                            ticks: { callback: (value) => formatNumber(value) },
                            grid: { color: '#f3f4f6' }
                          },
                          x: { 
                            grid: { display: false },
                            ticks: { maxRotation: 45, minRotation: 45 }
                          }
                        }
                      }}
                    />
                  ) : (
                    <p className="text-center text-gray-500 py-8">No data available</p>
                  )}
                </div>
              );
            }}
          />

          <ChartCard 
            title="Top Sub-Categories by Revenue" 
            chartId="subcategoryRevenue"
            renderChart={({ subCategoryData: chartSubCategoryData }) => {
              // Sort by Revenue descending (largest first), then take top 10
              const topSubCategories = [...chartSubCategoryData].sort((a, b) => (b.Revenue || 0) - (a.Revenue || 0)).slice(0, 10);
              return (
                <div className="h-80">
                  {topSubCategories.length > 0 ? (
                    <ChartComponent
                      type="bar"
                      data={{
                        labels: topSubCategories.map(item => item.Sub_Category || 'Unknown'),
                        datasets: [{
                          label: 'Revenue',
                          data: topSubCategories.map(item => item.Revenue || 0),
                          backgroundColor: '#1e293b',
                          borderRadius: 8
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false },
                          tooltip: {
                            enabled: true,
                            displayColors: true,
                            callbacks: {
                              title: (context) => {
                                // Show the sub-category name from the label
                                const label = context[0]?.label || '';
                                return label || 'Unknown';
                              },
                              label: (context) => {
                                const value = context.parsed.y || 0;
                                // Always show value, even if very small
                                return `Revenue: ${formatNumber(value)}`;
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
                          }
                        },
                        scales: {
                          y: {
                            beginAtZero: true,
                            ticks: { callback: (value) => formatNumber(value) },
                            grid: { color: '#f3f4f6' }
                          },
                          x: { 
                            grid: { display: false },
                            ticks: { maxRotation: 45, minRotation: 45 }
                          }
                        }
                      }}
                    />
                  ) : (
                    <p className="text-center text-gray-500 py-8">No data available</p>
                  )}
                </div>
              );
            }}
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

export default CategoryAnalysis;
