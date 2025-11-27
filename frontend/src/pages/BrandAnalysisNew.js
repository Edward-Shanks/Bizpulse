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
        setFilters({ years: [], months: [], businesses: [], channels: [], categories: [], brands: [] });
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
          <ChartCard title="Top 15 Brands by Revenue" chartId="revenueTop">
            <div className="h-96">
              {brandData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: brandData.map(item => item.Brand || 'Unknown'),
                    datasets: [
                      {
                        label: 'Revenue',
                        data: brandData.map(item => item.Revenue || 0),
                        backgroundColor: colorsWithOpacity,
                        borderRadius: 6,
                      },
                    ],
                  }}
                  options={{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label: context => `${formatNumber(context.parsed.x)}`,
                        },
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
          </ChartCard>

          <ChartCard title="Brand Revenue Distribution" chartId="revenueDistribution">
            <div className="h-96">
              {brandData.length > 0 ? (
                <ChartComponent
                  type="pie"
                  data={{
                    labels: brandData.slice(0, 10).map(item => item.Brand || 'Unknown'),
                    datasets: [
                      {
                        data: brandData.slice(0, 10).map(item => item.Revenue || 0),
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
                        callbacks: {
                          label: context => {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0) || 1;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${formatNumber(value)} (${percentage}%)`;
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

          <ChartCard title="Top 10 Brands by Profit" chartId="profitTop">
            <div className="h-80">
              {brandData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: brandData.slice(0, 10).map(item => item.Brand || 'Unknown'),
                    datasets: [
                      {
                        label: 'Profit',
                        data: brandData.slice(0, 10).map(item => item.Gross_Profit || 0),
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
                        callbacks: {
                          label: context => `Profit: ${formatNumber(context.parsed.y)}`,
                        },
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
          </ChartCard>

          <ChartCard title="Revenue vs Profit (Top 10)" chartId="revenueVsProfit">
            <div className="h-80">
              {brandData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: brandData.slice(0, 10).map(item => item.Brand || 'Unknown'),
                    datasets: [
                      {
                        label: 'Revenue',
                        data: brandData.slice(0, 10).map(item => item.Revenue || 0),
                        backgroundColor: '#1e293b',
                        borderRadius: 6,
                      },
                      {
                        label: 'Profit',
                        data: brandData.slice(0, 10).map(item => item.Gross_Profit || 0),
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
                        callbacks: {
                          label: context => `${context.dataset.label}: ${formatNumber(context.parsed.y)}`,
                        },
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
          </ChartCard>
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
