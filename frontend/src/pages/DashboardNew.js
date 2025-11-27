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
  
  // Chart-level filters
  const [chartFilters, setChartFilters] = useState({});
  
  // Insight modal
  const [insightModal, setInsightModal] = useState({ isOpen: false, chartTitle: '' });
  const [dataSource, setDataSource] = useState(null);
  const [syncing, setSyncing] = useState(false);

  const { token } = useAuth();
  
  // Check if running in development mode
  const isDevelopment = process.env.NODE_ENV === 'development';

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
        if (isDevelopment) console.log('Making API call to load filters...');
        const res = await axios.get(`${API}/filters/options`, {
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
        setFilters(res.data);
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
  }, [token, isDevelopment]);

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
        const url = `${API}/analytics/executive-overview${params.toString() ? `?${params.toString()}` : ''}`;
        if (isDevelopment) {
          console.log('Loading data with URL:', url);
          console.log('Filter values:', { selectedYears, selectedMonths, selectedBusinesses, selectedChannels });
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
  }, [token, selectedYears, selectedMonths, selectedBusinesses, selectedChannels]);

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
    const newFilters = {
      ...chartFilters,
      [chartName]: {
        ...(chartFilters[chartName] || {}),
        [filterType]: value
      }
    };
    setChartFilters(newFilters);

    // Link Sales Trend chart filters to global API filters so the chart becomes dynamic
    if (chartName === 'salesTrend') {
      if (filterType === 'year') {
        if (value === 'all') setSelectedYears([]);
        else setSelectedYears([Number(value)]);
      }
      if (filterType === 'month') {
        if (value === 'all') setSelectedMonths([]);
        else setSelectedMonths([value]);
      }
      if (filterType === 'business') {
        if (value === 'all') setSelectedBusinesses([]);
        else setSelectedBusinesses([value]);
      }
    }
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

  const yearlyData = (data?.yearly_performance || []).filter(item => item && item.Year);
  const businessData = (data?.business_performance || []).filter(item => item && item.Business && item.Revenue > 0);
  // Normalize monthly trend from backend (supports both 'Month_Name' and 'Month Name') and sort by month order
  const monthOrder = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const monthlyData = (data?.monthly_trend || [])
    .map(item => ({
      Month_Name: item?.Month_Name ?? item?.['Month Name'],
      Revenue: item?.Revenue ?? 0,
      Gross_Profit: item?.Gross_Profit ?? 0,
      Units: item?.Units ?? 0,
    }))
    .filter(item => !!item.Month_Name)
    .sort((a,b) => monthOrder.indexOf(a.Month_Name) - monthOrder.indexOf(b.Month_Name));

  // Debug: log monthly trend mapping (dev only)
  if (data && isDevelopment) {
    console.log('[Sales Trend] monthly_trend raw:', data?.monthly_trend);
    console.log('[Sales Trend] normalized monthlyData:', monthlyData);
  }
  const channelData = (data?.channel_performance || []).filter(item => item && item.Channel);

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

  const ChartCard = ({ title, chartName, children, context }) => {
    const currentFilters = chartFilters[chartName] || {};
    
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
        
        {/* Chart Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
          <select
            value={currentFilters.year || 'all'}
            onChange={(e) => handleChartFilterChange(chartName, 'year', e.target.value)}
            className="text-sm border border-gray-300 rounded px-3 py-1.5 bg-white flex-shrink-0"
          >
            <option value="all">All Years</option>
            {filters?.years?.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          
          <select
            value={currentFilters.month || 'all'}
            onChange={(e) => handleChartFilterChange(chartName, 'month', e.target.value)}
            className="text-sm border border-gray-300 rounded px-3 py-1.5 bg-white flex-shrink-0"
          >
            <option value="all">All Months</option>
            {filters?.months?.map(month => (
              <option key={month} value={month}>{month}</option>
            ))}
          </select>
          
          <select
            value={currentFilters.business || 'all'}
            onChange={(e) => handleChartFilterChange(chartName, 'business', e.target.value)}
            className="text-sm border border-gray-300 rounded px-3 py-1.5 bg-white flex-shrink-0"
          >
            <option value="all">All Businesses</option>
            {filters?.businesses?.map(business => (
              <option key={business} value={business}>{business}</option>
            ))}
          </select>
        </div>
        
        {children}
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
          {(selectedYears.length > 0 || selectedMonths.length > 0 || selectedBusinesses.length > 0 || selectedChannels.length > 0) && (
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
          <ChartCard title="Sales Trend (YTD)" chartName="salesTrend" context={{ monthlyData, selectedYears, selectedMonths, selectedBusinesses }}>
            <div className="h-80">
              {monthlyData.length > 0 ? (
                <ChartComponent
                  type="line"
                  data={{
                    labels: monthlyData.map(item => item.Month_Name),
                    datasets: [{
                      label: 'Revenue',
                      data: monthlyData.map(item => item.Revenue),
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
          </ChartCard>

          {/* Revenue vs Expenses */}
          <ChartCard title="Revenue vs Expenses" chartName="revenueExpenses">
            <div className="h-80">
              {yearlyData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: yearlyData.map(item => item.Year),
                    datasets: [
                      {
                        label: 'Revenue',
                        data: yearlyData.map(item => item.Revenue),
                        backgroundColor: '#1e293b',
                        borderRadius: 8
                      },
                      {
                        label: 'Expenses',
                        data: yearlyData.map(item => item.Revenue - item.Gross_Profit),
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
          </ChartCard>

          {/* Business vs Cases */}
          <ChartCard title="Business vs Cases" chartName="businessCases">
            <div className="h-80">
              {businessData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: businessData.map(item => item.Business),
                    datasets: [{
                      label: 'Units',
                      data: businessData.map(item => item.Units),
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
                          label: (context) => `${formatUnits(context.parsed.y)} units`
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
          </ChartCard>

          {/* Business vs Sales */}
          <ChartCard title="Business vs Sales" chartName="businessSales">
            <div className="h-80">
              {businessData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: businessData.map(item => item.Business),
                    datasets: [{
                      label: 'Revenue',
                      data: businessData.map(item => item.Revenue),
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
          </ChartCard>

          {/* Business vs Gross Profit */}
          <ChartCard title="Business vs Gross Profit" chartName="businessProfit">
            <div className="h-80">
              {businessData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: businessData.map(item => item.Business),
                    datasets: [{
                      label: 'Profit',
                      data: businessData.map(item => item.Gross_Profit),
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
          </ChartCard>

          {/* Channel Distribution */}
          <ChartCard title="Channel Distribution" chartName="channelDist">
            <div className="h-80">
              {channelData.length > 0 ? (
                <ChartComponent
                  type="doughnut"
                  data={{
                    labels: channelData.map(item => item.Channel),
                    datasets: [{
                      data: channelData.map(item => item.Revenue),
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
          </ChartCard>

          {/* Business Performance */}
          <ChartCard title="Business Performance" chartName="businessPerf">
            <div className="h-80">
              {businessData.length > 0 ? (
                <ChartComponent
                  type="pie"
                  data={{
                    labels: businessData.map(item => item.Business),
                    datasets: [{
                      data: businessData.map(item => item.Revenue),
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
          </ChartCard>

          {/* Top Performers */}
          <ChartCard title="Top Performers" chartName="topPerformers">
            <div className="h-80">
              {businessData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: businessData.slice(0, 5).map(item => item.Business),
                    datasets: [
                      {
                        label: 'Revenue',
                        data: businessData.slice(0, 5).map(item => item.Revenue),
                        backgroundColor: '#1e293b',
                        borderRadius: 6
                      },
                      {
                        label: 'Profit',
                        data: businessData.slice(0, 5).map(item => item.Gross_Profit),
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
          </ChartCard>
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
