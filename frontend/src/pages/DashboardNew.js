import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import ChartComponent from '@/components/ChartComponent';
import InsightModal from '@/components/InsightModal';
import { formatNumber, formatUnits } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { 
  TrendingUp, TrendingDown, Euro, Package, 
  Users, Target, Activity, Lightbulb 
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  
  // Page-level multi-select filters
  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedBrands, setSelectedBrands] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  
  // Chart-level filters (individual filters that override global filters)
  const [chartFilters, setChartFilters] = useState({});
  
  // Chart-specific data (for charts with individual filters)
  const [chartData, setChartData] = useState({});
  
  // Insight modal
  const [insightModal, setInsightModal] = useState({ isOpen: false, chartTitle: '' });
  const [dataSource, setDataSource] = useState(null);
  const [syncing, setSyncing] = useState(false);

  const { token } = useAuth();
  
  // Check if running in development mode
  const isDevelopment = process.env.NODE_ENV === 'development';

  // Helper function to merge global and individual filters (individual overrides global)
  const getMergedFilters = (chartName = null) => {
    const globalFilters = {
      years: selectedYears,
      months: selectedMonths,
      businesses: selectedBusinesses,
      channels: selectedChannels,
      brands: selectedBrands,
    };

    // If no chart name, return global filters only
    if (!chartName || !chartFilters[chartName]) {
      return globalFilters;
    }

    // Merge: individual filters override global filters
    // If individual filter key exists (even if empty array), it overrides global
    // Empty array means "all" (no filter), which should override global filter
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
  }, [selectedYears, selectedMonths, selectedBusinesses, selectedChannels, selectedBrands]);

  // Fetch data for a specific chart with merged filters
  const fetchChartData = async (chartName, individualFiltersOverride = null) => {
    try {
      // If individualFiltersOverride is provided, use it directly; otherwise read from state
      let mergedFilters;
      if (individualFiltersOverride) {
        // Manually merge with global filters
        // If individual filter key exists (even if empty array), it overrides global
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
      if (mergedFilters.brands.length) params.set('brands', mergedFilters.brands.join(','));

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

  useEffect(() => {
    const loadFilters = async () => {
      if (isDevelopment) {
        console.log('=== FILTER LOADING DEBUG ===');
        console.log('Token available:', !!token);
        console.log('Token value:', token ? token.substring(0, 20) + '...' : 'null');
        console.log('API URL:', `${API}/filters/options`);
      }
      
      if (!token) {
        if (isDevelopment) console.log('No token available, skipping filter load');
        return;
      }
      try {
        // Build query params with current filter selections for dynamic filtering
        const params = new URLSearchParams();
        if (selectedYears.length) params.set('years', selectedYears.join(','));
        if (selectedMonths.length) params.set('months', selectedMonths.join(','));
        if (selectedBusinesses.length) params.set('businesses', selectedBusinesses.join(','));
        if (selectedChannels.length) params.set('channels', selectedChannels.join(','));
        if (selectedBrands.length) params.set('brands', selectedBrands.join(','));

        const url = `${API}/filters/options${params.toString() ? `?${params.toString()}` : ''}`;
        if (isDevelopment) console.log('Making API call to load filters with URL:', url);
        const res = await axios.get(url, {
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
        });
        if (isDevelopment) {
          console.log('✅ Filters loaded successfully:', res.data);
          console.log('✅ Brands count:', res.data.brands?.length || 0);
          console.log('✅ Sample brands:', res.data.brands?.slice(0, 10) || []);
          console.log('✅ All brands:', res.data.brands || []);
        }
        
        const newFilters = res.data;
        setFilters(newFilters);
        
        // Remove invalid selections (selections that no longer exist in the filtered options)
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
        if (selectedBrands.length > 0) {
          const validBrands = selectedBrands.filter(b => newFilters.brands.includes(b));
          if (validBrands.length !== selectedBrands.length) {
            setSelectedBrands(validBrands);
          }
        }
      } catch (e) {
        console.error('❌ Failed to load filters:', e.response?.data || e.message);
        if (isDevelopment) {
          console.error('❌ Error status:', e.response?.status);
          console.error('❌ Error headers:', e.response?.headers);
          console.error('❌ Full error:', e);
        }
        // fallback to empty filters
        setFilters({ years: [], months: [], businesses: [], channels: [], brands: [], categories: [] });
      }
    };
    loadFilters();
  }, [token, isDevelopment, selectedYears, selectedMonths, selectedBusinesses, selectedChannels, selectedBrands]);

  useEffect(() => {
    const loadDataSource = async () => {
      try {
        const res = await axios.get(`${API}/data/source`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setDataSource(res.data);
      } catch (e) {
        setDataSource({ source: 'unknown', message: 'Unable to determine data source' });
      }
    };
    loadDataSource();
  }, [token]);

  useEffect(() => {
    const loadData = async () => {
      if (!token) {
        console.log('No token available, skipping data load');
        return;
      }
      try {
        setLoading(true);
        const params = new URLSearchParams();
        if (selectedYears.length) params.set('years', selectedYears.join(','));
        if (selectedMonths.length) params.set('months', selectedMonths.join(','));
        if (selectedBusinesses.length) params.set('businesses', selectedBusinesses.join(','));
        if (selectedChannels.length) params.set('channels', selectedChannels.join(','));
        if (selectedBrands.length) params.set('brands', selectedBrands.join(','));
        const url = `${API}/analytics/executive-overview${params.toString() ? `?${params.toString()}` : ''}`;
        if (isDevelopment) {
          console.log('Loading data with URL:', url);
          console.log('Filter values:', { selectedYears, selectedMonths, selectedBusinesses, selectedChannels, selectedBrands });
        }
        const res = await axios.get(url, {
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
        });
        if (isDevelopment) console.log('Data loaded successfully:', res.data);
        setData(res.data);
      } catch (e) {
        console.error('Failed to load data:', e.response?.data || e.message);
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [token, selectedYears, selectedMonths, selectedBusinesses, selectedChannels, selectedBrands]);

  const handleSyncData = async () => {
    try {
      setSyncing(true);
      const res = await axios.get(`${API}/data/sync`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      // Reload data source info
      const sourceRes = await axios.get(`${API}/data/source`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDataSource(sourceRes.data);
      // Reload data
      const params = new URLSearchParams();
      if (selectedYears.length) params.set('years', selectedYears.join(','));
      if (selectedMonths.length) params.set('months', selectedMonths.join(','));
      if (selectedBusinesses.length) params.set('businesses', selectedBusinesses.join(','));
      if (selectedChannels.length) params.set('channels', selectedChannels.join(','));
      if (selectedBrands.length) params.set('brands', selectedBrands.join(','));
      const url = `${API}/analytics/executive-overview${params.toString() ? `?${params.toString()}` : ''}`;
      const dataRes = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(dataRes.data);
    } catch (e) {
      console.error('Sync failed:', e);
    } finally {
      setSyncing(false);
    }
  };

  const handleChartFilterChange = async (chartName, filterType, value) => {
    // Convert filterType to match our filter structure (years, months, businesses, etc.)
    const filterKeyMap = {
      'year': 'years',
      'years': 'years',
      'month': 'months',
      'months': 'months',
      'business': 'businesses',
      'businesses': 'businesses',
      'channel': 'channels',
      'channels': 'channels',
      'brand': 'brands',
      'brands': 'brands',
    };

    const mappedKey = filterKeyMap[filterType] || filterType;
    
    // Convert value to array format (handle both single values and arrays)
    let filterValue = [];
    if (value === 'all' || value === null || value === undefined) {
      filterValue = [];
    } else if (Array.isArray(value)) {
      filterValue = value;
    } else {
      filterValue = [value];
    }

    // Update individual chart filters (these override global filters)
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
    
    // Fetch data for this chart with merged filters (individual overrides global)
    // Pass the new individual filters directly to avoid state timing issues
    await fetchChartData(chartName, newIndividualFilters);
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          {/* Header Skeleton */}
          <div className="flex justify-between items-start">
            <div>
              <Skeleton className="h-9 w-64 mb-2" />
              <Skeleton className="h-5 w-96" />
            </div>
          </div>

          {/* KPI Cards Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg border border-gray-200 p-5">
                <Skeleton className="h-4 w-24 mb-3" />
                <Skeleton className="h-10 w-32 mb-2" />
                <Skeleton className="h-3 w-full" />
              </div>
            ))}
          </div>

          {/* Charts Grid Skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg border border-gray-200 p-5">
                <div className="flex items-center justify-between mb-4">
                  <Skeleton className="h-6 w-40" />
                  <Skeleton className="h-8 w-32 rounded" />
                </div>
                <div className="flex flex-wrap gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
                  <Skeleton className="h-9 w-24 rounded" />
                  <Skeleton className="h-9 w-24 rounded" />
                  <Skeleton className="h-9 w-24 rounded" />
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

  // Helper function to get data for a specific chart (uses chart-specific data if available, otherwise global data)
  const getChartData = (chartName) => {
    return chartData[chartName] || data;
  };

  // Helper function to derive chart-specific data arrays
  const getChartDataArrays = (chartName) => {
    const chartDataToUse = getChartData(chartName);
    const monthOrder = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    
    const yearlyData = (chartDataToUse?.yearly_performance || []).filter(item => item && item.Year);
    const businessData = (chartDataToUse?.business_performance || []).filter(item => item && item.Business && item.Revenue > 0);
    const monthlyData = (chartDataToUse?.monthly_trend || [])
      .map(item => ({
        Month_Name: item?.Month_Name ?? item?.['Month Name'],
        Revenue: item?.Revenue ?? 0,
        Gross_Profit: item?.Gross_Profit ?? 0,
        Units: item?.Units ?? 0,
      }))
      .filter(item => !!item.Month_Name)
      .sort((a,b) => monthOrder.indexOf(a.Month_Name) - monthOrder.indexOf(b.Month_Name));
    const channelData = (chartDataToUse?.channel_performance || []).filter(item => item && item.Channel);
    
    return { yearlyData, businessData, monthlyData, channelData, chartDataToUse };
  };

  // Global data arrays (for cards and charts without individual filters)
  const { yearlyData, businessData, monthlyData, channelData } = getChartDataArrays(null);

  // Calculate metrics
  const totalRevenue = data?.total_revenue || 0;
  const totalProfit = data?.total_profit || 0;
  const totalUnits = data?.total_units || 0;
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
  
  // Mock growth percentages (in real app, calculate from historical data)
  const revenueGrowth = 8.2;
  const profitGrowth = 5.1;
  const unitsGrowth = -2.3;
  const yoyGrowth = 15.2;
  const customerAcquisition = 245;
  const marketShare = 28.5;
  const operationalEfficiency = 92;

  const colors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
  ];
  
  // Colors with reduced opacity for Business vs Cases graph
  const colorsWithOpacity = colors.map(color => {
    // Convert hex to rgba with 0.5 opacity
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.5)`;
  });

  const ChartCard = ({ title, chartName, children, context, renderChart }) => {
    const mergedFilters = getMergedFilters(chartName);
    
    // Get chart-specific data arrays
    const { yearlyData: chartYearlyData, businessData: chartBusinessData, monthlyData: chartMonthlyData, channelData: chartChannelData } = getChartDataArrays(chartName);
    
    return (
      <div 
        className="rounded-lg p-5"
        style={{
          background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
          border: '1px solid rgba(0, 0, 0, 0.1)'
        }}
      >
        {/* Title and View Insight Button */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          <button
            onClick={() => setInsightModal({ isOpen: true, chartTitle: title, context })}
            className="px-4 py-1.5 bg-orange-100 hover:bg-orange-200 text-orange-700 rounded-lg text-sm font-medium transition flex items-center gap-2 whitespace-nowrap"
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
                // Set individual filter to empty array to override global (show all years)
                await handleChartFilterChange(chartName, 'years', []);
              } else {
                // Set individual filter to specific year
                await handleChartFilterChange(chartName, 'years', [Number(value)]);
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
                // Set individual filter to empty array to override global (show all months)
                await handleChartFilterChange(chartName, 'months', []);
              } else {
                // Set individual filter to specific month
                await handleChartFilterChange(chartName, 'months', [value]);
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
                // Set individual filter to empty array to override global (show all businesses)
                await handleChartFilterChange(chartName, 'businesses', []);
              } else {
                // Set individual filter to specific business
                await handleChartFilterChange(chartName, 'businesses', [value]);
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
        {renderChart ? renderChart({ 
          yearlyData: chartYearlyData, 
          businessData: chartBusinessData, 
          monthlyData: chartMonthlyData, 
          channelData: chartChannelData 
        }) : children}
      </div>
    );
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Business Compass</h1>
            <p className="text-gray-600">Comprehensive business analytics and performance metrics</p>
          </div>
          
          {/* Data Source Indicator - Only in development */}
          {isDevelopment && (
            <div className="flex items-center gap-3">
              {/* Auth Status */}
              <div className={`px-3 py-1.5 rounded-full text-sm font-medium ${
                token ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {token ? '🔐 Authenticated' : '❌ Not Authenticated'}
              </div>
              
              {dataSource && (
                <div className={`px-3 py-1.5 rounded-full text-sm font-medium ${
                  dataSource.source === 'azure' 
                    ? 'bg-green-100 text-green-800' 
                    : dataSource.source === 'dummy'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {dataSource.source === 'azure' ? '📊 Azure Data' : 
                   dataSource.source === 'dummy' ? '🧪 Dummy Data' : 
                   '❓ Unknown Source'}
                  <span className="ml-2 text-xs">({dataSource.records_count} records)</span>
                </div>
              )}
              
              <button
                onClick={handleSyncData}
                disabled={syncing}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  syncing 
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {syncing ? 'Syncing...' : '🔄 Sync from Azure'}
              </button>
            </div>
          )}
        </div>

        {/* Overall Page Filters */}
        <div 
        className="rounded-lg p-5"
        style={{
          background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
          border: '1px solid rgba(0, 0, 0, 0.1)'
        }}
      >
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-semibold text-gray-700">Global Filters</h3>
            {isDevelopment && (
              <div className="text-xs text-gray-500">
                {filters ? (
                  <div>
                    <div>Loaded: {Object.keys(filters).length} filter types</div>
                    <div>Brands: {filters.brands?.length || 0} items</div>
                    {filters.brands?.length > 0 && (
                      <div className="text-green-600">✅ Real Azure Data</div>
                    )}
                  </div>
                ) : (
                  'Loading filters...'
                )}
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
              label="Brand"
              options={filters?.brands || []}
              selectedValues={selectedBrands}
              onChange={setSelectedBrands}
              placeholder="All Brands"
            />
            <MultiSelectFilter
              label="Channel"
              options={filters?.channels || []}
              selectedValues={selectedChannels}
              onChange={setSelectedChannels}
              placeholder="All Channels"
            />
          </div>
          
          {/* Debug: Show current filter selections */}
          {(selectedYears.length > 0 || selectedMonths.length > 0 || selectedBusinesses.length > 0 || selectedChannels.length > 0 || selectedBrands.length > 0) && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 mb-2">Active Filters:</h4>
              <div className="flex flex-wrap gap-2 text-xs">
                {selectedYears.length > 0 && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    Years: {selectedYears.join(', ')}
                  </span>
                )}
                {selectedMonths.length > 0 && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    Months: {selectedMonths.join(', ')}
                  </span>
                )}
                {selectedBusinesses.length > 0 && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    Businesses: {selectedBusinesses.join(', ')}
                  </span>
                )}
                {selectedChannels.length > 0 && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    Channels: {selectedChannels.join(', ')}
                  </span>
                )}
                {selectedBrands.length > 0 && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    Brands: {selectedBrands.join(', ')}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          <div 
            className="rounded-lg p-4"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Euro className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-gray-600">Total Sales</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{formatNumber(totalRevenue)}</p>
            <p className={`text-xs flex items-center gap-1 ${revenueGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {revenueGrowth >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {Math.abs(revenueGrowth)}%
            </p>
          </div>

          <div 
            className="rounded-lg p-4"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-xs text-gray-600">Gross Profit</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{formatNumber(totalProfit)}</p>
            <p className={`text-xs flex items-center gap-1 ${profitGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {profitGrowth >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {Math.abs(profitGrowth)}%
            </p>
          </div>

          <div 
            className="rounded-lg p-4"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Package className="w-4 h-4 text-purple-600" />
              <span className="text-xs text-gray-600">Cases Sold</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{formatUnits(totalUnits)}</p>
            <p className={`text-xs flex items-center gap-1 ${unitsGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {unitsGrowth >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {Math.abs(unitsGrowth)}%
            </p>
          </div>

          <div 
            className="rounded-lg p-4"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-orange-600" />
              <span className="text-xs text-gray-600">Avg. Margin</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{avgMargin.toFixed(1)}%</p>
            <p className="text-xs text-gray-500">Current</p>
          </div>

          <div 
            className="rounded-lg p-4"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-gray-600">YoY Growth</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{yoyGrowth}%</p>
            <p className="text-xs text-green-600 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              Strong
            </p>
          </div>

          <div 
            className="rounded-lg p-4"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-green-600" />
              <span className="text-xs text-gray-600">New Customers</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{customerAcquisition}</p>
            <p className="text-xs text-green-600 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              8.5%
            </p>
          </div>

          <div 
            className="rounded-lg p-4"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-indigo-600" />
              <span className="text-xs text-gray-600">Market Share</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{marketShare}%</p>
            <p className="text-xs text-green-600 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              3.2%
            </p>
          </div>

          <div 
            className="rounded-lg p-4"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <span className="text-xs text-gray-600">Efficiency</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{operationalEfficiency}%</p>
            <p className="text-xs text-green-600 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              3.0%
            </p>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sales Trend YTD */}
          <ChartCard 
            title="Sales Trend (YTD)" 
            chartName="salesTrend" 
            context={{ monthlyData, selectedYears, selectedMonths, selectedBusinesses }}
            renderChart={({ monthlyData: chartMonthlyData }) => {
              const monthOrder = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
              const sortedMonthlyData = [...chartMonthlyData].sort((a,b) => 
                monthOrder.indexOf(a.Month_Name) - monthOrder.indexOf(b.Month_Name)
              );
              return (
                <div className="h-80">
                  {sortedMonthlyData.length > 0 ? (
                    <ChartComponent
                      type="line"
                      data={{
                        labels: sortedMonthlyData.map(item => item.Month_Name),
                        datasets: [{
                          label: 'Revenue',
                          data: sortedMonthlyData.map(item => item.Revenue),
                      borderColor: '#1e293b',
                      backgroundColor: 'rgba(30, 41, 59, 0.1)',
                      tension: 0.4,
                      fill: true,
                      borderWidth: 3
                    }]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label: (context) => `${formatNumber(context.parsed.y)}`
                        }
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: { callback: (value) => formatNumber(value) }
                      }
                    }
                  }}
                />
                  ) : (
                    <p className="text-center text-gray-500 py-8">No data</p>
                  )}
                </div>
              );
            }}
          />

          {/* Revenue vs Expenses */}
          <ChartCard 
            title="Revenue vs Expenses" 
            chartName="revenueExpenses"
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
                          borderRadius: 8
                        },
                        {
                          label: 'Expenses',
                          data: chartYearlyData.map(item => item.Revenue - item.Gross_Profit),
                          backgroundColor: '#EDD5B1',
                          borderRadius: 8
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                          callbacks: {
                            label: (context) => `${context.dataset.label}: ${formatNumber(context.parsed.y)}`
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          ticks: { callback: (value) => formatNumber(value) }
                        }
                      }
                    }}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data</p>
                )}
              </div>
            )}
          />

          {/* Business vs Cases */}
          <ChartCard 
            title="Business vs Cases" 
            chartName="businessCases"
            renderChart={({ businessData: chartBusinessData }) => (
              <div className="h-80">
                {chartBusinessData.length > 0 ? (
                  <ChartComponent
                    type="bar"
                    data={{
                      labels: chartBusinessData.map(item => item.Business),
                      datasets: [{
                        label: 'Cases',
                        data: chartBusinessData.map(item => item.Units),
                        backgroundColor: colorsWithOpacity,
                        borderRadius: 8
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          callbacks: {
                            label: (context) => `${formatUnits(context.parsed.y)} cases`
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          ticks: { callback: (value) => formatNumber(value) }
                        },
                        x: { ticks: { maxRotation: 45, minRotation: 45 } }
                      }
                    }}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data</p>
                )}
              </div>
            )}
          />

          {/* Business vs Sales */}
          <ChartCard 
            title="Business vs Sales" 
            chartName="businessSales"
            renderChart={({ businessData: chartBusinessData }) => (
              <div className="h-80">
                {chartBusinessData.length > 0 ? (
                  <ChartComponent
                    type="bar"
                    data={{
                      labels: chartBusinessData.map(item => item.Business),
                      datasets: [{
                        label: 'Revenue',
                        data: chartBusinessData.map(item => item.Revenue),
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
                          callbacks: {
                            label: (context) => `${formatNumber(context.parsed.y)}`
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          ticks: { callback: (value) => formatNumber(value) }
                        },
                        x: { ticks: { maxRotation: 45, minRotation: 45 } }
                      }
                    }}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data</p>
                )}
              </div>
            )}
          />

          {/* Business vs Gross Profit */}
          <ChartCard 
            title="Business vs Gross Profit" 
            chartName="businessProfit"
            renderChart={({ businessData: chartBusinessData }) => (
              <div className="h-80">
                {chartBusinessData.length > 0 ? (
                  <ChartComponent
                    type="bar"
                    data={{
                      labels: chartBusinessData.map(item => item.Business),
                      datasets: [{
                        label: 'Profit',
                        data: chartBusinessData.map(item => item.Gross_Profit),
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
                          callbacks: {
                            label: (context) => `${formatNumber(context.parsed.y)}`
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          ticks: { callback: (value) => formatNumber(value) }
                        },
                        x: { ticks: { maxRotation: 45, minRotation: 45 } }
                      }
                    }}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data</p>
                )}
              </div>
            )}
          />

          {/* Channel Distribution */}
          <ChartCard 
            title="Channel Distribution" 
            chartName="channelDist"
            renderChart={({ channelData: chartChannelData }) => (
              <div className="h-80">
                {chartChannelData.length > 0 ? (
                  <ChartComponent
                    type="doughnut"
                    data={{
                      labels: chartChannelData.map(item => item.Channel),
                      datasets: [{
                        data: chartChannelData.map(item => item.Revenue),
                        backgroundColor: colorsWithOpacity,
                        borderWidth: 2,
                        borderColor: '#fff'
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { position: 'right', labels: { boxWidth: 12, font: { size: 10 } } },
                        tooltip: {
                          callbacks: {
                            label: (context) => `${context.label}: ${formatNumber(context.parsed)}`
                          }
                        }
                      }
                    }}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data</p>
                )}
              </div>
            )}
          />

          {/* Business Performance */}
          <ChartCard 
            title="Business Performance" 
            chartName="businessPerf"
            renderChart={({ businessData: chartBusinessData }) => (
              <div className="h-80">
                {chartBusinessData.length > 0 ? (
                  <ChartComponent
                    type="pie"
                    data={{
                      labels: chartBusinessData.map(item => item.Business),
                      datasets: [{
                        data: chartBusinessData.map(item => item.Revenue),
                        backgroundColor: colorsWithOpacity,
                        borderWidth: 2,
                        borderColor: '#fff'
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { position: 'right', labels: { boxWidth: 12, font: { size: 10 } } },
                        tooltip: {
                          callbacks: {
                            label: (context) => `${context.label}: ${formatNumber(context.parsed)}`
                          }
                        }
                      }
                    }}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data</p>
                )}
              </div>
            )}
          />

          {/* Top Performers */}
          <ChartCard 
            title="Top Performers" 
            chartName="topPerformers"
            renderChart={({ businessData: chartBusinessData }) => (
              <div className="h-80">
                {chartBusinessData.length > 0 ? (
                  <ChartComponent
                    type="bar"
                    data={{
                      labels: chartBusinessData.slice(0, 5).map(item => item.Business),
                      datasets: [
                        {
                          label: 'Revenue',
                          data: chartBusinessData.slice(0, 5).map(item => item.Revenue),
                          backgroundColor: '#1e293b',
                          borderRadius: 6
                        },
                        {
                          label: 'Profit',
                          data: chartBusinessData.slice(0, 5).map(item => item.Gross_Profit),
                          backgroundColor: '#EDD5B1',
                          borderRadius: 6
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                          callbacks: {
                            label: (context) => `${context.dataset.label}: ${formatNumber(context.parsed.y)}`
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          ticks: { callback: (value) => formatNumber(value) }
                        }
                      }
                    }}
                  />
                ) : (
                  <p className="text-center text-gray-500 py-8">No data</p>
                )}
              </div>
            )}
          />
        </div>
      </div>

      {/* Insight Modal */}
      <InsightModal
        isOpen={insightModal.isOpen}
        onClose={() => setInsightModal({ isOpen: false, chartTitle: '' })}
        chartTitle={insightModal.chartTitle}
        insights={[]}
        recommendations={[]}
        onExploreDeep={() => {}}
      />
    </Layout>
  );
};

export default Dashboard;
