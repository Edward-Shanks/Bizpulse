import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import FilterBar from '@/components/FilterBar';
import InsightModal from '@/components/InsightModal';
import AIInsightModal from '@/components/AIInsightModal';
import axios from 'axios';
import { API, useAuth } from '@/App';
import ChartComponent from '@/components/ChartComponent';
import { formatNumber, formatChartValue, formatCurrency } from '@/utils/formatters';
import { Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const CategoryAnalysis = () => {
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
      const response = await axios.get(`${API}/analytics/category-analysis`, { headers: { Authorization: `Bearer ${token}` } });
      setData(response.data);
    } catch (error) {
      toast.error('Failed to load category data');
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
            <p className="mt-4 text-gray-600">Loading category analysis...</p>
          </div>
        </div>
      </Layout>
    );
  }

  const categoryData = (data?.category_performance || []).filter(item => item && item.Category);
  const boardCategoryData = (data?.board_category_performance || []).filter(item => item && item.Board_Category && item.Revenue > 0);

  const categoryChartData = {
    labels: categoryData.map(item => item.Category),
    datasets: [
      { label: 'Sales', data: categoryData.map(item => item.Revenue), backgroundColor: '#3b82f6', borderRadius: 6 },
      { label: 'Gross_Profit', data: categoryData.map(item => item.Gross_Profit), backgroundColor: '#10b981', borderRadius: 6 },
    ],
  };

  const boardCategoryPieData = {
    labels: boardCategoryData.map(item => item.Board_Category),
    datasets: [
      {
        data: boardCategoryData.map(item => item.Revenue),
        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'],
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
      <div className="space-y-5" data-testid="category-analysis-page">
        <div>
          <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>Category Analysis</h1>
          <p className="text-gray-600 text-sm mt-1">Category and sub-category deep dives</p>
        </div>

        <FilterBar filters={filters} selectedFilters={selectedFilters} onFilterChange={handleFilterChange} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <ChartCard title="Category Performance" onViewInsight={() => handleViewInsight('Category Performance', [{ type: 'positive', text: 'Beauty category leads with 45% market share' }, { type: 'neutral', text: 'Category mix diversified across segments' }], ['Focus on high-margin categories', 'Expand product range in top categories', 'Optimize category portfolio'])}>
            <div className="chart-container">
              {categoryData.length > 0 && <ChartComponent type="bar" data={categoryChartData} options={chartOptions} />}
            </div>
          </ChartCard>

          <ChartCard title="Board Category Distribution" onViewInsight={() => handleViewInsight('Board Category Distribution', [{ type: 'positive', text: 'Balanced portfolio across board categories' }, { type: 'attention', text: 'Opportunity to expand in emerging categories' }], ['Review category strategy', 'Invest in growth categories', 'Optimize underperforming segments'])}>
            <div className="chart-container">
              {boardCategoryData.length > 0 && <ChartComponent type="pie" data={boardCategoryPieData} options={pieOptions} />}
            </div>
          </ChartCard>

          <div className="lg:col-span-2">
            <div className="professional-card p-5">
              <h3 className="text-base font-semibold text-gray-900 mb-3" style={{ fontFamily: 'Space Grotesk' }}>Sub-Category Performance</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="text-left py-2 px-3 text-gray-700 font-semibold text-xs">Sub-Category</th>
                      <th className="text-right py-2 px-3 text-gray-700 font-semibold text-xs">Sales</th>
                      <th className="text-right py-2 px-3 text-gray-700 font-semibold text-xs">Gross_Profit</th>
                      <th className="text-right py-2 px-3 text-gray-700 font-semibold text-xs">Cases</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.subcategory_performance || []).slice(0, 15).map((item, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50 transition">
                        <td className="py-2 px-3 text-gray-900 font-medium text-sm">{item.Sub_Cat}</td>
                        <td className="text-right py-2 px-3 text-gray-700 text-sm">{formatCurrency(item.Revenue || 0)}</td>
                        <td className="text-right py-2 px-3 text-gray-700 text-sm">{formatCurrency(item.Gross_Profit || 0)}</td>
                        <td className="text-right py-2 px-3 text-gray-700 text-sm">{(item.Units || 0).toLocaleString()}</td>
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

export default CategoryAnalysis;