import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import ChartComponent from '@/components/ChartComponent';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import InsightModal from '@/components/InsightModal';
import { formatNumber, formatUnits } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { TrendingUp, Euro, ShoppingCart, Lightbulb } from 'lucide-react';

const CustomerAnalysis = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);

  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [selectedCustomers, setSelectedCustomers] = useState([]);
  const [selectedBrands, setSelectedBrands] = useState([]);

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
        const res = await axios.get(`${API}/filters/options`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setFilters(res.data);
      } catch (error) {
        console.error('Failed to load filters', error);
        toast.error('Unable to load filter options');
        setFilters({
          years: [],
          months: [],
          businesses: [],
          channels: [],
          customers: [],
          brands: [],
        });
      }
    };

    loadFilters();
  }, [token]);

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
        if (selectedCustomers.length) params.set('customers', selectedCustomers.join(','));
        if (selectedBrands.length) params.set('brands', selectedBrands.join(','));

        const url = `${API}/analytics/customer-analysis${params.toString() ? `?${params.toString()}` : ''}`;
        const res = await axios.get(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
      } catch (error) {
        console.error('Failed to load customer analysis', error);
        toast.error('Failed to load customer analysis data');
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
    selectedCustomers,
    selectedBrands,
  ]);

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

  const channelData = (data?.channel_performance || []).filter(item => item && item.Channel);
  const customerData = (data?.customer_performance || []).filter(item => item && item.Customer);
  const topCustomers = (data?.top_customers || []).slice(0, 10);

  const totalRevenue = data?.total_revenue ?? channelData.reduce((sum, item) => sum + (item.Revenue || 0), 0);
  const totalProfit = data?.total_profit ?? channelData.reduce((sum, item) => sum + (item.Gross_Profit || 0), 0);
  const totalUnits = data?.total_units ?? channelData.reduce((sum, item) => sum + (item.Units || 0), 0);
  const activeChannels = data?.active_channels ?? channelData.filter(item => item && item.Channel && item.Revenue > 0).length;
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;

  const colors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16',
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
    selectedCustomers,
    selectedBrands,
    channelData,
    customerData,
    topCustomers,
    totalRevenue,
    totalProfit,
    totalUnits,
    activeChannels,
  };

  const getInsightPayload = (chartId) => {
    const defaultInsights = [
      { type: 'info', text: 'Use the filters to compare performance across channels or customer groups.' },
    ];
    const defaultRecommendations = [
      'Ask the AI assistant to surface growth opportunities in a specific channel.',
      'Drill into customer cohorts to identify retention or upsell plays.',
    ];
    const safeContext = { ...baseInsightContext, chartId };

    if (!channelData.length) {
      return {
        insights: defaultInsights,
        recommendations: defaultRecommendations,
        context: safeContext,
      };
    }

    switch (chartId) {
      case 'revenueByChannel': {
        const topChannel = channelData[0] || {};
        const topShare = totalRevenue > 0 ? ((topChannel?.Revenue || 0) / totalRevenue) * 100 : 0;
        return {
          insights: [
            {
              type: 'positive',
              text: `${topChannel?.Channel || 'Top channel'} leads revenue with ${formatNumber(topChannel?.Revenue || 0)} (${topShare.toFixed(1)}% share).`,
            },
            {
              type: 'neutral',
              text: `Average margin across channels is ${avgMargin.toFixed(1)}%.`,
            },
          ],
          recommendations: [
            'Review allocation of marketing spend across high-growth channels.',
            'Investigate the lowest contributing channels for efficiency gains.',
          ],
          context: { ...safeContext, metric: 'channel_revenue' },
        };
      }
      case 'topCustomers': {
        const topCustomer = topCustomers[0] || {};
        return {
          insights: [
            {
              type: 'positive',
              text: `${topCustomer?.Customer || 'Key customer'} is the top revenue contributor at ${formatNumber(topCustomer?.Revenue || 0)}.`,
            },
            {
              type: 'attention',
              text: 'Customer concentration is high—consider diversification strategies.',
            },
          ],
          recommendations: [
            'Use AI to profile similar customers for targeted acquisition campaigns.',
            'Check contract terms or service levels for top accounts.',
          ],
          context: { ...safeContext, metric: 'customer_mix' },
        };
      }
      case 'profitByChannel': {
        const profitSorted = [...channelData].sort((a, b) => (b?.Gross_Profit || 0) - (a?.Gross_Profit || 0));
        const topProfitChannel = profitSorted[0] || {};
        const margin = topProfitChannel?.Revenue ? ((topProfitChannel?.Gross_Profit || 0) / topProfitChannel.Revenue) * 100 : 0;
        return {
          insights: [
            {
              type: 'positive',
              text: `${topProfitChannel?.Channel || 'Top channel'} delivers ${formatNumber(topProfitChannel?.Gross_Profit || 0)} profit.`,
            },
            {
              type: 'neutral',
              text: `Margin for this channel is ${margin.toFixed(1)}%, compared to the portfolio average of ${avgMargin.toFixed(1)}%.`,
            },
          ],
          recommendations: [
            'Replicate successful price and promo mixes from high-margin channels.',
            'Ask AI to break down cost drivers in lower performing channels.',
          ],
          context: { ...safeContext, metric: 'channel_profit' },
        };
      }
      case 'unitsByChannel': {
        const unitsSorted = [...channelData].sort((a, b) => (b?.Units || 0) - (a?.Units || 0));
        const topUnitsChannel = unitsSorted[0] || {};
        return {
          insights: [
            {
              type: 'positive',
              text: `${topUnitsChannel?.Channel || 'Leading channel'} leads volume with ${formatUnits(topUnitsChannel?.Units || 0)} units.`,
            },
            {
              type: 'attention',
              text: 'Compare high-volume channels with profit data to ensure healthy conversion.',
            },
          ],
          recommendations: [
            'Use AI to identify cross-sell opportunities in high-volume channels.',
            'Align inventory planning with channel-specific demand trends.',
          ],
          context: { ...safeContext, metric: 'channel_units' },
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

  const closeInsightModal = () => setInsightModal(prev => ({ ...prev, isOpen: false }));

  const ChartCard = ({ title, chartId, children }) => (
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
      {children}
    </div>
  );

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Customer Analysis</h1>
          <p className="text-gray-600">Channel performance and customer insights</p>
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
              label="Customer"
              options={filters?.customers || []}
              selectedValues={selectedCustomers}
              onChange={setSelectedCustomers}
              placeholder="All Customers"
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
              <p className="text-xs text-white opacity-75">Across {activeChannels} active channels</p>
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
                {formatUnits(totalUnits)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Units</p>
              <p className="text-xs text-white opacity-75">Units sold</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard title="Revenue by Channel" chartId="revenueByChannel">
            <div className="h-80">
              {channelData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: channelData.map(item => item.Channel || 'Unknown'),
                    datasets: [{
                      label: 'Revenue',
                      data: channelData.map(item => item.Revenue || 0),
                      backgroundColor: colorsWithOpacity,
                      borderRadius: 8,
                      borderWidth: 0,
                    }],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label: (context) => `Revenue: ${formatNumber(context.parsed.y)}`,
                        },
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: { callback: (value) => formatNumber(value) },
                        grid: { color: '#f3f4f6' },
                      },
                      x: { grid: { display: false } },
                    },
                  }}
                />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available</p>
              )}
            </div>
          </ChartCard>

          <ChartCard title="Top 10 Customers" chartId="topCustomers">
            <div className="h-80">
              {topCustomers.length > 0 ? (
                <ChartComponent
                  type="pie"
                  data={{
                    labels: topCustomers.map(item => item.Customer || 'Unknown'),
                    datasets: [{
                      data: topCustomers.map(item => item.Revenue || 0),
                      backgroundColor: colorsWithOpacity,
                      borderWidth: 2,
                      borderColor: '#fff',
                    }],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'right',
                        labels: { boxWidth: 12, padding: 10, font: { size: 11 } },
                      },
                      tooltip: {
                        callbacks: {
                          label: (context) => {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return `${label}: ${formatNumber(value)}`;
                          },
                        },
                      },
                    },
                  }}
                />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available</p>
              )}
            </div>
          </ChartCard>

          <ChartCard title="Profit by Channel" chartId="profitByChannel">
            <div className="h-80">
              {channelData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: channelData.map(item => item.Channel || 'Unknown'),
                    datasets: [{
                      label: 'Profit',
                      data: channelData.map(item => item.Gross_Profit || 0),
                      backgroundColor: '#1e293b',
                      borderRadius: 8,
                    }],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label: (context) => `Profit: ${formatNumber(context.parsed.y)}`,
                        },
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: { callback: (value) => formatNumber(value) },
                        grid: { color: '#f3f4f6' },
                      },
                      x: { grid: { display: false } },
                    },
                  }}
                />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available</p>
              )}
            </div>
          </ChartCard>

          <ChartCard title="Units by Channel" chartId="unitsByChannel">
            <div className="h-80">
              {channelData.length > 0 ? (
                <ChartComponent
                  type="doughnut"
                  data={{
                    labels: channelData.map(item => item.Channel || 'Unknown'),
                    datasets: [{
                      data: channelData.map(item => item.Units || 0),
                      backgroundColor: colorsWithOpacity,
                      borderWidth: 2,
                      borderColor: '#fff',
                    }],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'right',
                        labels: { boxWidth: 12, padding: 10, font: { size: 11 } },
                      },
                      tooltip: {
                        callbacks: {
                          label: (context) => {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return `${label}: ${formatUnits(value)} units`;
                          },
                        },
                      },
                    },
                  }}
                />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available</p>
              )}
            </div>
          </ChartCard>
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

export default CustomerAnalysis;