import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import ChartComponent from '@/components/ChartComponent';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import InsightModal from '@/components/InsightModal';
import { formatNumber } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { Tag, TrendingUp, Euro, Lightbulb } from 'lucide-react';

const BrandAnalysis = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);

  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedBrands, setSelectedBrands] = useState([]);
  
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
        if (selectedBrands.length) params.set('brands', selectedBrands.join(','));

        const url = `${API}/filters/options${params.toString() ? `?${params.toString()}` : ''}`;
        const res = await axios.get(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        
        const newFilters = res.data;
        setFilters(newFilters);
        
        // Remove invalid selections (selections that no longer exist in the filtered options)
        // This happens when filters change and some options are no longer available
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
        if (selectedBrands.length > 0) {
          const validBrands = selectedBrands.filter(b => newFilters.brands.includes(b));
          if (validBrands.length !== selectedBrands.length) {
            setSelectedBrands(validBrands);
          }
        }
      } catch (error) {
        console.error('Failed to load filters', error);
        toast.error('Unable to load filter options');
        setFilters({ years: [], months: [], businesses: [], channels: [], categories: [], brands: [] });
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
    selectedBrands,
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
        if (selectedBrands.length) params.set('brands', selectedBrands.join(','));

        const url = `${API}/analytics/brand-analysis${params.toString() ? `?${params.toString()}` : ''}`;
        const res = await axios.get(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
      } catch (error) {
        console.error('Failed to load brand analysis', error);
        toast.error('Failed to load brand analysis data');
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
    selectedBrands,
  ]);

  // Helper function to merge global and individual filters (individual overrides global)
  const getMergedFilters = (chartName = null) => {
    const globalFilters = {
      years: selectedYears,
      months: selectedMonths,
      businesses: selectedBusinesses,
      channels: selectedChannels,
      categories: selectedCategories,
      brands: selectedBrands,
    };

    // If no chart name, return global filters only
    if (!chartName || !chartFilters[chartName]) {
      return globalFilters;
    }

    // Merge: individual filters override global filters
    // If individual filter key exists (even if empty array), it overrides global
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
      brands: individualFilters.hasOwnProperty('brands')
        ? individualFilters.brands 
        : globalFilters.brands,
    };
  };

  // Reset individual chart filters and chart data when global filters change
  useEffect(() => {
    // Reset all individual chart filters when global filters change
    setChartFilters({});
    setChartData({});
  }, [selectedYears, selectedMonths, selectedBusinesses, selectedChannels, selectedCategories, selectedBrands]);

  // Fetch data for a specific chart with merged filters
  const fetchChartData = async (chartName, individualFiltersOverride = null) => {
    try {
      // If individualFiltersOverride is provided, use it directly; otherwise read from state
      let mergedFilters;
      if (individualFiltersOverride) {
        // Manually merge with global filters
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
          brands: individualFiltersOverride.hasOwnProperty('brands')
            ? individualFiltersOverride.brands 
            : selectedBrands,
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
      if (mergedFilters.brands.length) params.set('brands', mergedFilters.brands.join(','));

      const url = `${API}/analytics/brand-analysis${params.toString() ? `?${params.toString()}` : ''}`;
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
    // Convert filterType to match our filter structure
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
      'brand': 'brands',
      'brands': 'brands',
    };

    const mappedKey = filterKeyMap[filterType] || filterType;
    
    // Convert value to array format
    let filterValue = [];
    if (value === 'all' || value === null || value === undefined) {
      filterValue = [];
    } else if (Array.isArray(value)) {
      filterValue = value;
    } else {
      filterValue = [value];
    }

    // Update individual chart filters
    const newIndividualFilters = {
      ...(chartFilters[chartName] || {}),
      [mappedKey]: filterValue
    };
    
    const newFilters = {
      ...chartFilters,
      [chartName]: newIndividualFilters
    };
    
    // Update state
    setChartFilters(newFilters);
    
    // Fetch data for this chart with merged filters
    await fetchChartData(chartName, newIndividualFilters);
  };

  // Helper function to get data for a specific chart
  const getChartData = (chartName) => {
    return chartData[chartName] || data;
  };

  // Helper function to derive chart-specific data arrays
  const getChartDataArrays = (chartName) => {
    const chartDataToUse = getChartData(chartName);
    const brandData = (chartDataToUse?.brand_performance || []).filter(item => item && item.Brand);
    
    return { brandData, chartDataToUse };
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
  const brandData = (data?.brand_performance || []).slice(0, 15);
  const brandByBusiness = data?.brand_by_business || [];
  const totalRevenue = data?.total_revenue ?? brandData.reduce((sum, item) => sum + (item.Revenue || 0), 0);
  const totalProfit = data?.total_profit ?? brandData.reduce((sum, item) => sum + (item.Gross_Profit || 0), 0);
  const activeBrands =
    data?.active_brands ?? brandData.filter(item => item && item.Brand && item.Revenue > 0).length;
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;

  const colors = [
    '#3b82f6',
    '#10b981',
    '#f59e0b',
    '#ef4444',
    '#8b5cf6',
    '#ec4899',
    '#14b8a6',
    '#f97316',
    '#06b6d4',
    '#84cc16',
    '#6366f1',
    '#f43f5e',
    '#0ea5e9',
    '#d946ef',
    '#facc15',
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
    selectedBrands,
    brandData,
    brandByBusiness,
    totalRevenue,
    totalProfit,
    activeBrands,
  };

  const getInsightPayload = (chartId) => {
    const defaultInsights = [
      { type: 'info', text: 'Use the filters to focus on specific brands, categories, or channels.' },
    ];
    const defaultRecommendations = [
      'Ask the AI assistant to compare performance across filters.',
      'Drill into categories or channels that show unexpected trends.',
    ];
    const safeContext = { ...baseInsightContext, chartId };

    if (!brandData.length) {
      return {
        insights: defaultInsights,
        recommendations: defaultRecommendations,
        context: safeContext,
      };
    }

    switch (chartId) {
      case 'revenueTop': {
        const topBrand = brandData[0] || {};
        const top5Revenue = brandData.slice(0, 5).reduce((sum, item) => sum + (item?.Revenue || 0), 0);
        const shareTop = totalRevenue > 0 ? ((topBrand?.Revenue || 0) / totalRevenue) * 100 : 0;
        const shareTop5 = totalRevenue > 0 ? (top5Revenue / totalRevenue) * 100 : 0;
        return {
          insights: [
            {
              type: 'positive',
              text: `${topBrand?.Brand || 'Top brand'} leads revenue at ${formatNumber(topBrand?.Revenue || 0)} (${shareTop.toFixed(1)}% share).`,
            },
            {
              type: 'neutral',
              text: `Top 5 brands contribute ${shareTop5.toFixed(1)}% of total revenue.`,
            },
          ],
          recommendations: [
            'Review the campaigns that are driving the leading brands.',
            'Investigate tail brands to uncover growth opportunities.',
          ],
          context: { ...safeContext, metric: 'revenue' },
        };
      }
      case 'revenueDistribution': {
        const topBrand = brandData[0] || {};
        const top3Revenue = brandData.slice(0, 3).reduce((sum, item) => sum + (item?.Revenue || 0), 0);
        const shareTop3 = totalRevenue > 0 ? (top3Revenue / totalRevenue) * 100 : 0;
        return {
          insights: [
            {
              type: 'positive',
              text: `${topBrand?.Brand || 'Leading brand'} dominates the revenue mix at ${formatNumber(topBrand?.Revenue || 0)}.`,
            },
            {
              type: 'attention',
              text: `Top 3 brands capture ${shareTop3.toFixed(1)}% of portfolio revenue.`,
            },
          ],
          recommendations: [
            'Balance investments between core brands and emerging challengers.',
            'Apply channel filters to validate distribution mix by market.',
          ],
          context: { ...safeContext, metric: 'distribution' },
        };
      }
      case 'profitTop': {
        const profitSorted = [...brandData].sort(
          (a, b) => (b?.Gross_Profit || 0) - (a?.Gross_Profit || 0)
        );
        const topProfitBrand = profitSorted[0] || {};
        const topProfit = topProfitBrand?.Gross_Profit || 0;
        const marginTop = topProfitBrand?.Revenue
          ? (topProfit / topProfitBrand.Revenue) * 100
          : 0;
        return {
          insights: [
            {
              type: 'positive',
              text: `${topProfitBrand?.Brand || 'Top brand'} delivers the highest profit at ${formatNumber(topProfit)}.`,
            },
            {
              type: 'neutral',
              text: `Margin for this brand is ${marginTop.toFixed(1)}%, vs portfolio average ${avgMargin.toFixed(1)}%.`,
            },
          ],
          recommendations: [
            'Replicate pricing and trade levers from high-margin brands.',
            'Monitor cost structure for brands below the average margin.',
          ],
          context: { ...safeContext, metric: 'profit' },
        };
      }
      case 'revenueVsProfit': {
        const topBrand = brandData[0] || {};
        const revenue = topBrand?.Revenue || 0;
        const profit = topBrand?.Gross_Profit || 0;
        const gap = revenue - profit;
        return {
          insights: [
            {
              type: 'positive',
              text: `${topBrand?.Brand || 'Top brand'} generates ${formatNumber(revenue)} revenue with ${formatNumber(profit)} profit.`,
            },
            {
              type: 'attention',
              text: `Revenue-to-profit gap is ${formatNumber(gap)}; review cost drivers for optimization.`,
            },
          ],
          recommendations: [
            'Analyse discounting and trade spend for brands with large gaps.',
            'Use the AI assistant to benchmark profit conversion across segments.',
          ],
          context: { ...safeContext, metric: 'revenue_vs_profit' },
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
    const { brandData: chartBrandData } = getChartDataArrays(chartId);
    
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
        <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
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
            className="text-sm border border-gray-300 rounded px-3 py-1.5 bg-white flex-shrink-0"
          >
            <option value="all">All Businesses</option>
            {filters?.businesses?.map(business => (
              <option key={business} value={business}>{business}</option>
            ))}
          </select>
        </div>
        
        {/* Render chart with chart-specific data */}
        {renderChart ? renderChart({ brandData: chartBrandData }) : children}
      </div>
    );
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Brand Analysis</h1>
          <p className="text-gray-600">Brand performance metrics and insights</p>
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
              label="Brand"
              options={filters?.brands || []}
              selectedValues={selectedBrands}
              onChange={setSelectedBrands}
              placeholder="All Brands"
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
              <p className="text-xs text-white opacity-75">Across {activeBrands} active brands</p>
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
                {activeBrands}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Active Brands</p>
              <p className="text-xs text-white opacity-75">In portfolio</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard 
            title="Top 15 Brands by Revenue" 
            chartId="revenueTop"
            renderChart={({ brandData: chartBrandData }) => {
              // Sort by Revenue descending (largest first), then take top 15
              const topBrands = [...chartBrandData].sort((a, b) => (b.Revenue || 0) - (a.Revenue || 0)).slice(0, 15);
              const brandLabels = topBrands.map(item => item.Brand || 'Unknown');
              const brandRevenues = topBrands.map(item => item.Revenue || 0);
              
              return (
                <div className="h-96">
                  {topBrands.length > 0 ? (
                    <ChartComponent
                      type="bar"
                      data={{
                        labels: brandLabels,
                        datasets: [
                          {
                            label: 'Revenue',
                            data: brandRevenues,
                            backgroundColor: colorsWithOpacity,
                            borderRadius: 6,
                          },
                        ],
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
                                  
                                  // Fallback: Get from stored brandLabels array
                                  if (dataIndex !== undefined && dataIndex >= 0 && brandLabels && brandLabels[dataIndex]) {
                                    return String(brandLabels[dataIndex]);
                                  }
                                  
                                  // Last fallback: Try item properties
                                  return String(item.label || item.yLabel || 'Unknown');
                                }
                                return 'Unknown';
                              },
                              label: (context) => {
                                // For horizontal bars, value is on x-axis
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
                          },
                        },
                        scales: {
                          x: {
                            beginAtZero: true,
                            ticks: { callback: value => formatNumber(value) },
                            grid: { color: '#f3f4f6' },
                          },
                          y: { grid: { display: false } },
                        },
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
            title="Brand Revenue Distribution" 
            chartId="revenueDistribution"
            renderChart={({ brandData: chartBrandData }) => {
              // Sort by Revenue descending (largest first), then take top 10
              const topBrands = [...chartBrandData].sort((a, b) => (b.Revenue || 0) - (a.Revenue || 0)).slice(0, 10);
              return (
                <div className="h-96">
                  {topBrands.length > 0 ? (
                    <ChartComponent
                      type="pie"
                      data={{
                        labels: topBrands.map(item => item.Brand || 'Unknown'),
                        datasets: [
                          {
                            data: topBrands.map(item => item.Revenue || 0),
                            backgroundColor: colorsWithOpacity,
                            borderWidth: 2,
                            borderColor: '#fff',
                          },
                        ],
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'right',
                            labels: { boxWidth: 12, padding: 8, font: { size: 10 } },
                          },
                          tooltip: {
                            enabled: true,
                            displayColors: true,
                            callbacks: {
                              label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0) || 1;
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                                // Always show value, even if very small
                                return `${label}: ${formatNumber(value)} (${percentage}%)`;
                              },
                              afterLabel: (context) => {
                                const value = context.parsed || 0;
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
            title="Top 10 Brands by Profit" 
            chartId="profitTop"
            renderChart={({ brandData: chartBrandData }) => {
              // Sort by Gross_Profit descending (largest first), then take top 10
              const topBrands = [...chartBrandData].sort((a, b) => (b.Gross_Profit || 0) - (a.Gross_Profit || 0)).slice(0, 10);
              return (
                <div className="h-80">
                  {topBrands.length > 0 ? (
                    <ChartComponent
                      type="bar"
                      data={{
                        labels: topBrands.map(item => item.Brand || 'Unknown'),
                        datasets: [
                          {
                            label: 'Profit',
                            data: topBrands.map(item => item.Gross_Profit || 0),
                            backgroundColor: '#1e293b',
                            borderRadius: 8,
                          },
                        ],
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
                                // Show the brand name from the label
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
                          },
                        },
                        scales: {
                          y: {
                            beginAtZero: true,
                            ticks: { callback: value => formatNumber(value) },
                            grid: { color: '#f3f4f6' },
                          },
                          x: {
                            grid: { display: false },
                            ticks: { maxRotation: 45, minRotation: 45 },
                          },
                        },
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
            title="Revenue vs Profit (Top 10)" 
            chartId="revenueVsProfit"
            renderChart={({ brandData: chartBrandData }) => {
              // Sort by Revenue descending (largest first), then take top 10
              const topBrands = [...chartBrandData].sort((a, b) => (b.Revenue || 0) - (a.Revenue || 0)).slice(0, 10);
              return (
                <div className="h-80">
                  {topBrands.length > 0 ? (
                    <ChartComponent
                      type="bar"
                      data={{
                        labels: topBrands.map(item => item.Brand || 'Unknown'),
                        datasets: [
                          {
                            label: 'Revenue',
                            data: topBrands.map(item => item.Revenue || 0),
                            backgroundColor: '#1e293b',
                            borderRadius: 6,
                          },
                          {
                            label: 'Profit',
                            data: topBrands.map(item => item.Gross_Profit || 0),
                            backgroundColor: '#EDD5B1',
                            borderRadius: 6,
                          },
                        ],
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { position: 'top' },
                          tooltip: {
                            enabled: true,
                            displayColors: true,
                            callbacks: {
                              title: (context) => {
                                // Show the brand name from the label
                                const label = context[0]?.label || '';
                                return label || 'Unknown';
                              },
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
                            ticks: { callback: value => formatNumber(value) },
                            grid: { color: '#f3f4f6' },
                          },
                          x: {
                            grid: { display: false },
                            ticks: { maxRotation: 45, minRotation: 45 },
                          },
                        },
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

        <div 
          className="rounded-lg p-6"
          style={{
            background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Brand Performance by Business</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-2 px-3 text-gray-700 font-semibold text-xs">Brand</th>
                  <th className="text-left py-2 px-3 text-gray-700 font-semibold text-xs">Business</th>
                  <th className="text-right py-2 px-3 text-gray-700 font-semibold text-xs">Revenue</th>
                  <th className="text-right py-2 px-3 text-gray-700 font-semibold text-xs">Gross Profit</th>
                </tr>
              </thead>
              <tbody>
                {brandByBusiness.slice(0, 25).map((item, idx) => (
                  <tr key={`${item.Brand}-${item.Business}-${idx}`} className="border-b border-gray-100 hover:bg-gray-50 transition">
                    <td className="py-2 px-3 text-gray-900 font-medium text-sm">{item.Brand || 'Unknown'}</td>
                    <td className="py-2 px-3 text-gray-700 text-sm">{item.Business || 'Unknown'}</td>
                    <td className="text-right py-2 px-3 text-gray-700 text-sm">{formatNumber(item.Revenue || 0)}</td>
                    <td className="text-right py-2 px-3 text-gray-700 text-sm">{formatNumber(item.Gross_Profit || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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

export default BrandAnalysis;
