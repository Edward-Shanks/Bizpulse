import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import ChartComponent from '@/components/ChartComponent';
import { formatNumber } from '@/utils/formatters';
import staticData from '@/data/staticData';
import { Button } from '@/components/ui/button';
import { 
  AlertCircle, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  Sparkles,
  Target,
  BarChart3,
  Euro,
  Users,
  TrendingUp,
  Mail,
  MousePointer,
  RefreshCw,
  Eye,
  Layers,
  Award
} from 'lucide-react';

const RootCauseAnalysis = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  
  // Multi-select filter states
  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);

  useEffect(() => {
    // Load static data
    setFilters(staticData.filters);
    setData(staticData.executiveOverview);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading root cause analysis...</p>
          </div>
        </div>
      </Layout>
    );
  }

  const businessData = (data?.business_performance || []).filter(item => item && item.Business && item.Revenue > 0);

  // Root Cause Analysis Issues
  const issues = [
    {
      id: 1,
      title: 'Sales Decline in Q4',
      severity: 'high',
      rootCause: 'Increased competition from new market entrants',
      impact: '€250K revenue loss',
      recommendation: 'Launch competitive pricing strategy and enhanced marketing',
      status: 'investigating',
      icon: TrendingDown,
      color: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', icon: '#ef4444' }
    },
    {
      id: 2,
      title: 'Customer Churn Rate Increase',
      severity: 'medium',
      rootCause: 'Service delivery delays due to supply chain issues',
      impact: '15% increase in churn',
      recommendation: 'Optimize logistics and implement customer retention program',
      status: 'resolved',
      icon: AlertTriangle,
      color: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', icon: '#f59e0b' }
    },
    {
      id: 3,
      title: 'Inventory Turnover Slowdown',
      severity: 'low',
      rootCause: 'Overstocking of seasonal products',
      impact: '€120K in tied capital',
      recommendation: 'Implement dynamic inventory management system',
      status: 'monitoring',
      icon: CheckCircle,
      color: { bg: '#d1fae5', border: '#10b981', text: '#065f46', icon: '#10b981' }
    }
  ];


  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Root Cause Analysis
          </h1>
          <p className="text-gray-600">
            Identify and resolve business performance issues
          </p>
        </div>

        {/* Root Cause Analysis Content */}
        {(
          <>
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

        {/* Issues Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Critical Issues</h3>
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">3</p>
            <p className="text-sm text-red-600 mt-1">Require immediate attention</p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Under Investigation</h3>
              <AlertTriangle className="w-5 h-5 text-amber-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">5</p>
            <p className="text-sm text-amber-600 mt-1">Analysis in progress</p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Resolved</h3>
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">12</p>
            <p className="text-sm text-green-600 mt-1">Successfully addressed</p>
          </div>
        </div>

        {/* Issues List */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-gray-900">Identified Issues</h2>
          
          {issues.map((issue) => {
            const Icon = issue.icon;
            return (
              <div
                key={issue.id}
                className="bg-white rounded-lg border p-6"
                style={{ borderColor: issue.color.border }}
              >
                <div className="flex items-start gap-4">
                  <div className="mt-1">
                    <Icon className="w-6 h-6" style={{ color: issue.color.icon }} />
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">{issue.title}</h3>
                        <span className={`text-xs font-semibold px-2 py-1 rounded ${
                          issue.severity === 'high' ? 'bg-red-100 text-red-700' :
                          issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                          {issue.severity.toUpperCase()} PRIORITY
                        </span>
                      </div>
                      <span className={`text-xs font-medium px-3 py-1 rounded-full ${
                        issue.status === 'investigating' ? 'bg-blue-100 text-blue-700' :
                        issue.status === 'resolved' ? 'bg-green-100 text-green-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {issue.status.charAt(0).toUpperCase() + issue.status.slice(1)}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Root Cause</p>
                        <p className="text-sm text-gray-900">{issue.rootCause}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Impact</p>
                        <p className="text-sm font-semibold text-gray-900">{issue.impact}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Status</p>
                        <p className="text-sm text-gray-900 capitalize">{issue.status}</p>
                      </div>
                    </div>

                    <div 
                      className="rounded-lg p-3"
                      style={{ background: '#fef3c7' }}
                    >
                      <div className="flex items-start gap-2">
                        <Sparkles className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#f59e0b' }} />
                        <div>
                          <p className="text-xs font-semibold mb-1" style={{ color: '#92400e' }}>
                            AI Recommendation:
                          </p>
                          <p className="text-xs" style={{ color: '#92400e' }}>
                            {issue.recommendation}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Performance Analysis Chart */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Business Performance by Segment</h3>
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
                      borderRadius: 6
                    },
                    {
                      label: 'Profit',
                      data: businessData.map(item => item.Gross_Profit),
                      backgroundColor: '#10b981',
                      borderRadius: 6
                    }
                  ]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: true, position: 'top' } },
                  scales: {
                    y: {
                      beginAtZero: true,
                      ticks: { callback: (value) => formatNumber(value) }
                    }
                  }
                }}
              />
            ) : (
              <p className="text-center text-gray-500 py-8">No data available</p>
            )}
          </div>
        </div>
          </>
        )}
      </div>
    </Layout>
  );
};

export default RootCauseAnalysis;
