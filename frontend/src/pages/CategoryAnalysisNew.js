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
import { Layers, TrendingUp, Euro, Lightbulb } from 'lucide-react';

const CategoryAnalysis = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);

  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedSubCategories, setSelectedSubCategories] = useState([]);

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
          categories: [],
          sub_categories: [],
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Category Analysis</h1>
          <p className="text-gray-600">Product category and sub-category performance</p>
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
          <ChartCard title="Revenue by Category" chartId="categoryRevenue">
            <div className="h-96">
              {categoryData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: categoryData.map(item => item.Category || 'Unknown'),
                    datasets: [{
                      label: 'Revenue',
                      data: categoryData.map(item => item.Revenue || 0),
                      backgroundColor: colorsWithOpacity,
                      borderRadius: 6
                    }]
                  }}
                  options={{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label: (context) => `${formatNumber(context.parsed.x)}`
                        }
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
          </ChartCard>

          <ChartCard title="Category Distribution" chartId="categoryDistribution">
            <div className="h-96">
              {categoryData.length > 0 ? (
                <ChartComponent
                  type="doughnut"
                  data={{
                    labels: categoryData.slice(0, 10).map(item => item.Category || 'Unknown'),
                    datasets: [{
                      data: categoryData.slice(0, 10).map(item => item.Revenue || 0),
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
          </ChartCard>

          <ChartCard title="Profit by Category (Top 10)" chartId="categoryProfit">
            <div className="h-80">
              {categoryData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: categoryData.slice(0, 10).map(item => item.Category || 'Unknown'),
                    datasets: [{
                      label: 'Profit',
                      data: categoryData.slice(0, 10).map(item => item.Gross_Profit || 0),
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
                          label: (context) => `Profit: ${formatNumber(context.parsed.y)}`
                        }
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
          </ChartCard>

          <ChartCard title="Top Sub-Categories by Revenue" chartId="subcategoryRevenue">
            <div className="h-80">
              {subcategoryData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: subcategoryData.slice(0, 10).map(item => item.Sub_Category || 'Unknown'),
                    datasets: [{
                      label: 'Revenue',
                      data: subcategoryData.slice(0, 10).map(item => item.Revenue || 0),
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
                          label: (context) => `Revenue: ${formatNumber(context.parsed.y)}`
                        }
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

export default CategoryAnalysis;
