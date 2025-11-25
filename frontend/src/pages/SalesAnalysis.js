import React, { useState, useEffect } from 'react';
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

  // Multi-select filter states
  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);

  const [insightModal, setInsightModal] = useState({
    isOpen: false,
    chartTitle: '',
    insights: [],
    recommendations: [],
    context: {},
  });

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
        setFilters(res.data);
      } catch (error) {
        console.error('Failed to load filters', error);
        if (error.response?.status === 401) {
          toast.error('Session expired. Please login again.');
          // Optionally redirect to login
          // window.location.href = '/login';
        } else {
          toast.error('Unable to load filter options');
        }
        setFilters({
          years: [],
          months: [],
          businesses: [],
          channels: [],
          brands: [],
          categories: [],
        });
      }
    };

    loadFilters();
  }, [token]);

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
    data?.total_units ?? yearlyData.reduce((sum, item) => sum + (item.Units || 0), 0);
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

  const ChartCard = ({ title, chartId, children }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
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

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top' },
      tooltip: {
        callbacks: {
          label: (context) => `${context.dataset.label}: ${formatNumber(context.parsed.y)}`,
        },
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Sales Analysis</h1>
          <p className="text-gray-600">Comprehensive sales performance metrics and trends</p>
        </div>

        {/* Multi-Select Filters */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
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
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Sales</h3>
              <Euro className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{formatNumber(totalRevenue)}</p>
            <p className="text-sm text-green-600 mt-1">
              <TrendingUp className="w-4 h-4 inline mr-1" />
              Last period comparison coming soon
            </p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Units</h3>
              <Package className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{formatUnits(totalUnits)}</p>
            <p className="text-sm text-blue-600 mt-1">
              <TrendingUp className="w-4 h-4 inline mr-1" />
              Track unit growth with filters
            </p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Avg Price/Case</h3>
              <Target className="w-5 h-5 text-amber-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{formatNumber(avgPrice)}</p>
            <p className="text-sm text-amber-600 mt-1">
              <TrendingUp className="w-4 h-4 inline mr-1" />
              Combine filters to refine insights
            </p>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard title="Sales by Year" chartId="salesByYear">
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
                        backgroundColor: '#f59e0b',
                        borderRadius: 6,
                      },
                      {
                        label: 'Gross Profit',
                        data: yearlyData.map(item => item.Gross_Profit),
                        backgroundColor: '#34d399',
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
          </ChartCard>

          <ChartCard title="Sales by Business" chartId="salesByBusiness">
            <div className="h-80">
              {businessData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: businessData.map(item => item.Business),
                    datasets: [
                      {
                        label: 'Revenue',
                        data: businessData.map(item => item.Revenue),
                        backgroundColor: '#3b82f6',
                        borderRadius: 6,
                      },
                      {
                        label: 'Gross Profit',
                        data: businessData.map(item => item.Gross_Profit),
                        backgroundColor: '#60a5fa',
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

export default SalesAnalysis;
