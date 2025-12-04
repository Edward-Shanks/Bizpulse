import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import FilterBar from '@/components/FilterBar';
import InsightModal from '@/components/InsightModal';
import AIInsightModal from '@/components/AIInsightModal';
import ChartComponent from '@/components/ChartComponent';
import { formatNumber, formatChartValue } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { TrendingUp, DollarSign, Package, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const Dashboard = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [selectedFilters, setSelectedFilters] = useState({
    year: 'all',
    month: 'all',
    business: 'all',
    channel: 'all',
    brand: 'all',
    category: 'all'
  });
  
  // Individual chart filters
  const [chartFilters, setChartFilters] = useState({
    yearlyPerformance: { year: 'all', month: 'all', business: 'all', channel: 'all' },
    businessPerformance: { year: 'all', month: 'all', business: 'all', channel: 'all' },
    monthlyTrend: { year: 'all', month: 'all', business: 'all', channel: 'all' },
    businessUnits: { year: 'all', month: 'all', business: 'all', channel: 'all' },
    businessSales: { year: 'all', month: 'all', business: 'all', channel: 'all' },
    businessProfit: { year: 'all', month: 'all', business: 'all', channel: 'all' },
  });
  
  const [insightModal, setInsightModal] = useState({ isOpen: false, chartTitle: '', insights: [], recommendations: [] });
  const [aiModal, setAiModal] = useState({ isOpen: false, chartTitle: '' });

  useEffect(() => {
    fetchFilters();
  }, []);
  
  useEffect(() => {
    fetchData();
  }, [selectedFilters]);

  const fetchFilters = async () => {
    try {
      const response = await axios.get(`${API}/filters/options`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFilters(response.data);
    } catch (error) {
      console.error('Failed to load filters', error);
      toast.error('Failed to load filters');
    }
  };

  const fetchData = async (customFilters = null) => {
    try {
      setLoading(true);
      const filterParams = customFilters || selectedFilters;
      const queryParams = new URLSearchParams();
      if (filterParams.year !== 'all') queryParams.append('year', filterParams.year);
      if (filterParams.month !== 'all') queryParams.append('month', filterParams.month);
      if (filterParams.business !== 'all') queryParams.append('business', filterParams.business);
      if (filterParams.channel !== 'all') queryParams.append('channel', filterParams.channel);
      
      const response = await axios.get(`${API}/analytics/executive-overview?${queryParams.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
    } catch (error) {
      console.error('Failed to load dashboard data', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filterName, value) => {
    setSelectedFilters(prev => ({ ...prev, [filterName]: value }));
  };
  
  const handleChartFilterChange = async (chartName, filterName, value) => {
    const updatedFilters = {
      ...chartFilters[chartName],
      [filterName]: value
    };
    
    setChartFilters(prev => ({
      ...prev,
      [chartName]: updatedFilters
    }));
    
    // Fetch data with the chart-specific filters
    await fetchData(updatedFilters);
  };

  const handleViewInsight = (chartTitle, insights, recommendations) => {
    setInsightModal({ isOpen: true, chartTitle, insights, recommendations });
  };

  const handleExploreDeep = () => {
    setInsightModal({ isOpen: false, chartTitle: '', insights: [], recommendations: [] });
    setAiModal({ isOpen: true, chartTitle: insightModal.chartTitle });
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading dashboard...</p>
          </div>
        </div>
      </Layout>
    );
  }
  
  if (!data) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <p className="text-gray-600">No data available</p>
          </div>
        </div>
      </Layout>
    );
  }

  const yearlyData = (data?.yearly_performance || []).filter(item => item && item.Year);
  const businessData = (data?.business_performance || []).filter(item => item && item.Business && item.Revenue > 0);
  const monthlyData = (data?.monthly_trend || []).filter(item => item && item.Month_Name);

  // Yearly Performance Chart Data
  const yearlyChartData = {
    labels: yearlyData.map(item => item.Year),
    datasets: [
      {
        label: 'Revenue',
        data: yearlyData.map(item => item.Revenue),
        backgroundColor: '#3b82f6',
        borderColor: '#3b82f6',
        borderWidth: 1,
        borderRadius: 6,
      },
      {
        label: 'Profit',
        data: yearlyData.map(item => item.Gross_Profit),
        backgroundColor: '#10b981',
        borderColor: '#10b981',
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };

  // Business Performance Pie Chart Data
  const businessChartData = {
    labels: businessData.map(item => item.Business),
    datasets: [
      {
        data: businessData.map(item => item.Revenue),
        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'],
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };
  
  // NEW: Business vs Units Bar Chart
  const businessUnitsChartData = {
    labels: businessData.map(item => item.Business),
    datasets: [
      {
        label: 'Units',
        data: businessData.map(item => item.Units),
        backgroundColor: '#f59e0b',
        borderColor: '#f59e0b',
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };
  
  // NEW: Business vs Sales Bar Chart
  const businessSalesChartData = {
    labels: businessData.map(item => item.Business),
    datasets: [
      {
        label: 'Revenue',
        data: businessData.map(item => item.Revenue),
        backgroundColor: '#3b82f6',
        borderColor: '#3b82f6',
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };
  
  // NEW: Business vs Gross_Profit Bar Chart
  const businessProfitChartData = {
    labels: businessData.map(item => item.Business),
    datasets: [
      {
        label: 'Profit',
        data: businessData.map(item => item.Gross_Profit),
        backgroundColor: '#10b981',
        borderColor: '#10b981',
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };

  // Monthly Trend Line Chart Data
  const monthlyChartData = {
    labels: monthlyData.map(item => item.Month_Name),
    datasets: [
      {
        label: 'Revenue',
        data: monthlyData.map(item => item.Revenue),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#3b82f6',
      },
      {
        label: 'Profit',
        data: monthlyData.map(item => item.Gross_Profit),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#10b981',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          font: { size: 11 },
          padding: 10,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#1f2937',
        bodyColor: '#1f2937',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: 10,
        displayColors: true,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            label += formatChartValue(context.parsed.y || context.parsed);
            return label;
          }
        }
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { font: { size: 11 } },
      },
      y: {
        grid: { color: '#f3f4f6' },
        ticks: { 
          font: { size: 11 },
          callback: function(value) {
            return formatNumber(value);
          }
        },
      },
    },
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right',
        labels: {
          font: { size: 11 },
          padding: 10,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#1f2937',
        bodyColor: '#1f2937',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            let label = context.label || '';
            if (label) {
              label += ': ';
            }
            label += formatChartValue(context.parsed);
            return label;
          }
        }
      },
    },
  };

  return (
    <Layout>
      <div className="space-y-5" data-testid="dashboard-page">
        <div>
          <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
            Executive Overview
          </h1>
          <p className="text-gray-600 text-sm mt-1">Year-over-year performance and key metrics</p>
        </div>

        <FilterBar
          filters={filters}
          selectedFilters={selectedFilters}
          onFilterChange={handleFilterChange}
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <KPICard
            title="Total Profit"
            value={formatNumber(data?.total_profit || 0)}
            icon={<DollarSign className="w-5 h-5" />}
            color="#10b981"
            bgColor="#d1fae5"
          />
          <KPICard
            title="Total Revenue"
            value={formatNumber(data?.total_revenue || 0)}
            icon={<TrendingUp className="w-5 h-5" />}
            color="#3b82f6"
            bgColor="#dbeafe"
          />
          <KPICard
            title="Total Cases"
            value={(data?.total_units || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            icon={<Package className="w-5 h-5" />}
            color="#f59e0b"
            bgColor="#fef3c7"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <ChartCard
            title="Yearly Performance"
            filters={filters}
            chartName="yearlyPerformance"
            chartFilters={chartFilters.yearlyPerformance}
            onChartFilterChange={handleChartFilterChange}
            onViewInsight={() =>
              handleViewInsight(
                'Yearly Performance',
                [
                  { type: 'positive', text: `Total revenue of ${formatNumber(data?.total_revenue || 0)} across ${yearlyData.length} years` },
                  { type: 'neutral', text: 'Profit margins remain stable' }
                ],
                [
                  'Monitor year-over-year growth trends',
                  'Focus on maintaining consistent profit margins',
                  'Explore opportunities in high-growth years'
                ]
              )
            }
          >
            <div className="chart-container">
              {yearlyData.length > 0 ? (
                <ChartComponent type="bar" data={yearlyChartData} options={chartOptions} />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available for selected filters</p>
              )}
            </div>
          </ChartCard>

          <ChartCard
            title="Business Performance"
            filters={filters}
            chartName="businessPerformance"
            chartFilters={chartFilters.businessPerformance}
            onChartFilterChange={handleChartFilterChange}
            onViewInsight={() =>
              handleViewInsight(
                'Business Performance',
                [
                  { type: 'positive', text: `${businessData.length} active business units contributing to revenue` },
                  { type: 'attention', text: 'Consider portfolio diversification for risk mitigation' }
                ],
                [
                  'Analyze top-performing business units',
                  'Invest in emerging business opportunities',
                  'Balance portfolio across business segments'
                ]
              )
            }
          >
            <div className="chart-container">
              {businessData.length > 0 ? (
                <ChartComponent type="pie" data={businessChartData} options={pieOptions} />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available for selected filters</p>
              )}
            </div>
          </ChartCard>

          <ChartCard
            title="Business vs Units"
            filters={filters}
            chartName="businessUnits"
            chartFilters={chartFilters.businessUnits}
            onChartFilterChange={handleChartFilterChange}
            onViewInsight={() =>
              handleViewInsight(
                'Business vs Units',
                [
                  { type: 'positive', text: `Total ${formatNumber(data?.total_units || 0)} units across all businesses` },
                  { type: 'neutral', text: 'Unit volume shows business distribution patterns' }
                ],
                [
                  'Optimize inventory based on unit volume',
                  'Focus on high-volume business segments',
                  'Balance distribution efficiency'
                ]
              )
            }
          >
            <div className="chart-container">
              {businessData.length > 0 ? (
                <ChartComponent type="bar" data={businessUnitsChartData} options={chartOptions} />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available for selected filters</p>
              )}
            </div>
          </ChartCard>

          <ChartCard
            title="Business vs Revenue"
            filters={filters}
            chartName="businessSales"
            chartFilters={chartFilters.businessSales}
            onChartFilterChange={handleChartFilterChange}
            onViewInsight={() =>
              handleViewInsight(
                'Business vs Revenue',
                [
                  { type: 'positive', text: `Total revenue of ${formatNumber(data?.total_revenue || 0)} across businesses` },
                  { type: 'neutral', text: 'Revenue distribution indicates market strength' }
                ],
                [
                  'Invest in top-performing business units',
                  'Develop strategies for underperforming segments',
                  'Leverage successful business models'
                ]
              )
            }
          >
            <div className="chart-container">
              {businessData.length > 0 ? (
                <ChartComponent type="bar" data={businessSalesChartData} options={chartOptions} />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available for selected filters</p>
              )}
            </div>
          </ChartCard>

          <ChartCard
            title="Business vs Profit"
            filters={filters}
            chartName="businessProfit"
            chartFilters={chartFilters.businessProfit}
            onChartFilterChange={handleChartFilterChange}
            onViewInsight={() =>
              handleViewInsight(
                'Business vs Profit',
                [
                  { type: 'positive', text: `Total profit of ${formatNumber(data?.total_profit || 0)} generated` },
                  { type: 'attention', text: 'Profit margin variations need analysis' }
                ],
                [
                  'Focus on high-margin business units',
                  'Review cost structures in lower-margin segments',
                  'Optimize pricing strategies'
                ]
              )
            }
          >
            <div className="chart-container">
              {businessData.length > 0 ? (
                <ChartComponent type="bar" data={businessProfitChartData} options={chartOptions} />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available for selected filters</p>
              )}
            </div>
          </ChartCard>

          <ChartCard
            title="Monthly Trend (Current Year)"
            className="lg:col-span-2"
            filters={filters}
            chartName="monthlyTrend"
            chartFilters={chartFilters.monthlyTrend}
            onChartFilterChange={handleChartFilterChange}
            onViewInsight={() =>
              handleViewInsight(
                'Monthly Trend',
                [
                  { type: 'positive', text: `${monthlyData.length} months of data showing seasonal patterns` },
                  { type: 'neutral', text: 'Performance aligns with industry benchmarks' }
                ],
                [
                  'Optimize inventory for peak months',
                  'Plan marketing campaigns around high-performing periods',
                  'Address underperforming months with targeted strategies'
                ]
              )
            }
          >
            <div className="chart-container">
              {monthlyData.length > 0 ? (
                <ChartComponent type="line" data={monthlyChartData} options={chartOptions} />
              ) : (
                <p className="text-center text-gray-500 py-8">No data available for selected filters</p>
              )}
            </div>
          </ChartCard>
        </div>
      </div>

      <InsightModal
        isOpen={insightModal.isOpen}
        onClose={() => setInsightModal({ isOpen: false, chartTitle: '', insights: [], recommendations: [] })}
        chartTitle={insightModal.chartTitle}
        insights={insightModal.insights}
        recommendations={insightModal.recommendations}
        onExploreDeep={handleExploreDeep}
      />

      <AIInsightModal
        isOpen={aiModal.isOpen}
        onClose={() => setAiModal({ isOpen: false, chartTitle: '' })}
        chartTitle={aiModal.chartTitle}
      />
    </Layout>
  );
};

const KPICard = ({ title, value, icon, color, bgColor }) => (
  <div className="professional-card p-5" data-testid={`kpi-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-600 text-xs mb-1">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
      <div className="p-2.5 rounded-xl" style={{ backgroundColor: bgColor, color }}>
        {icon}
      </div>
    </div>
  </div>
);

const ChartCard = ({ title, children, onViewInsight, className = '', filters, chartName, onChartFilterChange, chartFilters }) => (
  <div className={`professional-card p-5 ${className}`}>
    <div className="flex items-center justify-between mb-3">
      <h3 className="text-base font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
        {title}
      </h3>
      <Button
        onClick={onViewInsight}
        size="sm"
        variant="outline"
        className="h-8 text-xs border-blue-200 text-blue-600 hover:bg-blue-50"
        data-testid={`view-insight-${title.toLowerCase().replace(/\s+/g, '-')}`}
      >
        <Eye className="w-3 h-3 mr-1.5" />
        View Insight
      </Button>
    </div>
    
    {/* Chart Filters */}
    {filters && chartFilters && (
      <div className="grid grid-cols-4 gap-2 mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div>
          <label className="text-xs text-gray-600 mb-1 block">Year</label>
          <select
            value={chartFilters.year}
            onChange={(e) => onChartFilterChange(chartName, 'year', e.target.value)}
            className="w-full text-xs border border-gray-300 rounded px-2 py-1.5"
          >
            <option value="all">All Years</option>
            {filters?.years?.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-600 mb-1 block">Month</label>
          <select
            value={chartFilters.month}
            onChange={(e) => onChartFilterChange(chartName, 'month', e.target.value)}
            className="w-full text-xs border border-gray-300 rounded px-2 py-1.5"
          >
            <option value="all">All Months</option>
            {filters?.months?.map(month => (
              <option key={month} value={month}>{month}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-600 mb-1 block">Business</label>
          <select
            value={chartFilters.business}
            onChange={(e) => onChartFilterChange(chartName, 'business', e.target.value)}
            className="w-full text-xs border border-gray-300 rounded px-2 py-1.5"
          >
            <option value="all">All Businesses</option>
            {filters?.businesses?.map(business => (
              <option key={business} value={business}>{business}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-600 mb-1 block">Channel</label>
          <select
            value={chartFilters.channel}
            onChange={(e) => onChartFilterChange(chartName, 'channel', e.target.value)}
            className="w-full text-xs border border-gray-300 rounded px-2 py-1.5"
          >
            <option value="all">All Channels</option>
            {filters?.channels?.map(channel => (
              <option key={channel} value={channel}>{channel}</option>
            ))}
          </select>
        </div>
      </div>
    )}
    
    {children}
  </div>
);

export default Dashboard;