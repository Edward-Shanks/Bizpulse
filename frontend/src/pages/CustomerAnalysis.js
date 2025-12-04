import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import FilterBar from '@/components/FilterBar';
import InsightModal from '@/components/InsightModal';
import AIInsightModal from '@/components/AIInsightModal';
import ChartComponent from '@/components/ChartComponent';
import { formatNumber, formatChartValue, formatCurrency } from '@/utils/formatters';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const CustomerAnalysis = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [selectedFilters, setSelectedFilters] = useState({ year: 'all', month: 'all', business: 'all', channel: 'all', brand: 'all', category: 'all' });
  const [insightModal, setInsightModal] = useState({ isOpen: false, chartTitle: '', insights: [], recommendations: [] });
  const [aiModal, setAiModal] = useState({ isOpen: false, chartTitle: '' });

  useEffect(() => {
    fetchFilters();
    fetchData();
  }, []);

  const fetchFilters = async () => {
    try {
      const response = await axios.get(`${API}/filters/options`, { headers: { Authorization: `Bearer ${token}` } });
      setFilters(response.data);
    } catch (error) {
      console.error('Failed to load filters');
    }
  };

  const fetchData = async () => {
    try {
      const response = await axios.get(`${API}/analytics/customer-analysis`, { headers: { Authorization: `Bearer ${token}` } });
      setData(response.data);
    } catch (error) {
      toast.error('Failed to load customer data');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filterName, value) => {
    setSelectedFilters(prev => ({ ...prev, [filterName]: value }));
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
            <p className="mt-4 text-gray-600">Loading customer analysis...</p>
          </div>
        </div>
      </Layout>
    );
  }

  const channelData = (data?.channel_performance || []).filter(item => item && item.Channel);
  const topCustomers = (data?.top_customers || []).filter(item => item && item.Customer && item.Revenue > 0);

  const channelChartData = {
    labels: channelData.map(item => item.Channel),
    datasets: [
      {
        label: 'Sales',
        data: channelData.map(item => item.Revenue),
        backgroundColor: '#3b82f6',
        borderRadius: 6,
      },
      {
        label: 'Gross_Profit',
        data: channelData.map(item => item.Gross_Profit),
        backgroundColor: '#10b981',
        borderRadius: 6,
      },
    ],
  };

  const customerPieData = {
    labels: topCustomers.map(item => item.Customer),
    datasets: [
      {
        data: topCustomers.map(item => item.Revenue),
        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#db2777'],
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'bottom', labels: { font: { size: 11 }, padding: 10 } },
      tooltip: { 
        backgroundColor: 'rgba(255, 255, 255, 0.95)', 
        titleColor: '#1f2937', 
        bodyColor: '#1f2937', 
        borderColor: '#e5e7eb', 
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) label += ': ';
            label += formatChartValue(context.parsed.y || context.parsed);
            return label;
          }
        }
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { font: { size: 11 } } },
      y: { grid: { color: '#f3f4f6' }, ticks: { font: { size: 11 }, callback: (value) => formatNumber(value) } },
    },
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'right', labels: { font: { size: 11 }, padding: 10 } },
      tooltip: { 
        backgroundColor: 'rgba(255, 255, 255, 0.95)', 
        titleColor: '#1f2937', 
        bodyColor: '#1f2937', 
        borderColor: '#e5e7eb', 
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            let label = context.label || '';
            if (label) label += ': ';
            label += formatChartValue(context.parsed);
            return label;
          }
        }
      },
    },
  };

  return (
    <Layout>
      <div className="space-y-5" data-testid="customer-analysis-page">
        <div>
          <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>Customer Analysis</h1>
          <p className="text-gray-600 text-sm mt-1">Channel-wise and customer drilldowns</p>
        </div>

        <FilterBar filters={filters} selectedFilters={selectedFilters} onFilterChange={handleFilterChange} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <ChartCard title="Channel Performance" onViewInsight={() => handleViewInsight('Channel Performance', [{ type: 'positive', text: 'Grocery channel shows strong performance' }, { type: 'attention', text: 'Convenience channel needs strategic attention' }], ['Optimize channel mix', 'Focus on high-margin channels', 'Expand distribution network'])}>
            <div className="chart-container">
              {channelData.length > 0 && <ChartComponent type="bar" data={channelChartData} options={chartOptions} />}
            </div>
          </ChartCard>

          <ChartCard title="Top 10 Customers" onViewInsight={() => handleViewInsight('Top 10 Customers', [{ type: 'positive', text: 'Strong customer base with loyal repeat buyers' }, { type: 'neutral', text: 'Customer concentration within acceptable range' }], ['Strengthen top customer relationships', 'Develop loyalty programs', 'Expand customer acquisition'])}>
            <div className="chart-container">
              {topCustomers.length > 0 && <ChartComponent type="pie" data={customerPieData} options={pieOptions} />}
            </div>
          </ChartCard>

          <div className="lg:col-span-2">
            <div className="professional-card p-5">
              <h3 className="text-base font-semibold text-gray-900 mb-3" style={{ fontFamily: 'Space Grotesk' }}>Customer Performance Overview</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="text-left py-2 px-3 text-gray-700 font-semibold text-xs">Customer</th>
                      <th className="text-right py-2 px-3 text-gray-700 font-semibold text-xs">Sales</th>
                      <th className="text-right py-2 px-3 text-gray-700 font-semibold text-xs">Gross_Profit</th>
                      <th className="text-right py-2 px-3 text-gray-700 font-semibold text-xs">Cases</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.customer_performance || []).slice(0, 10).map((customer, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50 transition">
                        <td className="py-2 px-3 text-gray-900 font-medium text-sm">{customer.Customer}</td>
                        <td className="text-right py-2 px-3 text-gray-700 text-sm">{formatCurrency(customer.Revenue || 0)}</td>
                        <td className="text-right py-2 px-3 text-gray-700 text-sm">{formatCurrency(customer.Gross_Profit || 0)}</td>
                        <td className="text-right py-2 px-3 text-gray-700 text-sm">{(customer.Units || 0).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <InsightModal isOpen={insightModal.isOpen} onClose={() => setInsightModal({ isOpen: false, chartTitle: '', insights: [], recommendations: [] })} chartTitle={insightModal.chartTitle} insights={insightModal.insights} recommendations={insightModal.recommendations} onExploreDeep={handleExploreDeep} />
      <AIInsightModal isOpen={aiModal.isOpen} onClose={() => setAiModal({ isOpen: false, chartTitle: '' })} chartTitle={aiModal.chartTitle} />
    </Layout>
  );
};

const ChartCard = ({ title, children, onViewInsight }) => (
  <div className="professional-card p-5">
    <div className="flex items-center justify-between mb-3">
      <h3 className="text-base font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>{title}</h3>
      <Button onClick={onViewInsight} size="sm" variant="outline" className="h-8 text-xs border-blue-200 text-blue-600 hover:bg-blue-50">
        <Eye className="w-3 h-3 mr-1.5" />View Insight
      </Button>
    </div>
    {children}
  </div>
);

export default CustomerAnalysis;