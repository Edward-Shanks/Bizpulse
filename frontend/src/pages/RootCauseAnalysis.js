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
      title: 'Household & Beauty Revenue Decline',
      severity: 'high',
      rootCause:
        'Household & Beauty revenue decreased from about €17.4M in 2023 to €16.2M in 2024, with softness in core grocery customers.',
      impact: '≈€1.2M revenue decline year-on-year (-7%) in Household & Beauty.',
      recommendation: [
        'Re-focus promotions and display investments on the top Household & Beauty SKUs in Grocery ROI.',
        'Bundle Household & Beauty hero SKUs with high-velocity Food lines to lift basket value.',
        'Tighten price ladders vs key competitors where elasticities are highest.',
        'Launch joint business plans with Dunnes and Musgrave to rebuild distribution and share.',
        'Track weekly sell-out dashboards for Household & Beauty to validate recovery actions.'
      ],
      status: 'investigating',
      icon: TrendingDown,
      color: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', icon: '#ef4444' }
    },
    {
      id: 2,
      title: 'Cali Cali Brand Revenue Contraction',
      severity: 'high',
      rootCause:
        'Cali Cali revenue has fallen from roughly €1.04M in 2023 to €0.60M in 2024, indicating range rationalisation and slower rate of sale.',
      impact: '≈€440K revenue loss (-40%+) for Cali Cali between 2023 and 2024.',
      recommendation: [
        'Identify top 10 Cali Cali SKUs by rate of sale and protect distribution and space for these first.',
        'Rationalise long-tail SKUs with low cases and gSales to simplify the range.',
        'Run price and promotion tests with Grocery ROI and Wholesale ROI to re-activate trial.',
        'Use digital and in-store campaigns to reposition Cali Cali around clear shopper occasions.',
        'Set quarterly revenue and distribution targets for Cali Cali and review in brand councils.'
      ],
      status: 'investigating',
      icon: AlertTriangle,
      color: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', icon: '#f59e0b' }
    },
    {
      id: 3,
      title: 'Q3 2025 Sales Slowdown vs H1 2025',
      severity: 'high',
      rootCause:
        'Total revenue in 2025 drops from about €28.5M in Q1 and €28.0M in Q2 to only €7.9M in Q3, driven by fewer orders and listings later in the year.',
      impact: 'Run-rate decline of ~70% vs the average of Q1–Q2 2025, risking full-year targets.',
      recommendation: [
        'Drill into Q3 2025 by business, channel and customer to isolate where cases and gSales fell most.',
        'Align with demand planning to confirm whether the drop is timing-related or a structural slowdown.',
        'Rebuild activation calendars for late Q3 and Q4 with campaigns in Grocery ROI and Online.',
        'Engage key accounts whose Q3 orders have fallen behind 2024 levels to recover volume.',
        'Monitor weekly Q3/Q4 run-rate against 2024 benchmarks to close the gap early.'
      ],
      status: 'investigating',
      icon: TrendingDown,
      color: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', icon: '#ef4444' }
    },
    {
      id: 4,
      title: 'Under-leveraged Online & International Channels',
      severity: 'medium',
      rootCause:
        'In 2025, Online and International channels together generate ~€7M, only about 11% of total revenue, with most sales concentrated in Grocery ROI.',
      impact: 'Missed growth opportunity in higher-margin, scalable channels vs physical retail.',
      recommendation: [
        'Prioritise a focused assortment for Online and International based on high-margin SKUs.',
        'Improve digital content, ratings and reviews for the top 50 SKUs sold online.',
        'Run targeted campaigns in key export and e-commerce markets using performance media.',
        'Align pricing and pack sizes to online shopper missions (bulk, subscription, discovery).',
        'Set channel-specific growth targets and track ROI on digital investments monthly.'
      ],
      status: 'monitoring',
      icon: BarChart3,
      color: { bg: '#dbeafe', border: '#3b82f6', text: '#1d4ed8', icon: '#3b82f6' }
    },
    {
      id: 5,
      title: 'Portfolio Concentration in Food Business',
      severity: 'medium',
      rootCause:
        'In 2025 the Food business delivers ~€44.0M of ~€64.4M total revenue (around two-thirds of the portfolio).',
      impact: 'High dependency on one business line increases risk if Food growth slows or competition intensifies.',
      recommendation: [
        'Define clear growth roles for non-Food businesses such as Household and Kinetica.',
        'Invest in innovation and activation in under-scaled brands to diversify revenue streams.',
        'Create cross-category shopper missions that link Food with Household and Health brands.',
        'Allocate part of trade and media budgets specifically to emerging businesses each year.',
        'Track contribution of each business to total revenue and margin in executive dashboards.'
      ],
      status: 'monitoring',
      icon: Layers,
      color: { bg: '#ecfeff', border: '#06b6d4', text: '#0e7490', icon: '#06b6d4' }
    },
    {
      id: 6,
      title: 'Negative-Margin SKUs and Promotions',
      severity: 'low',
      rootCause:
        'Roughly 2% of rows in yearly_data.csv have negative fGP, often linked to deep discounts or specific customer deals.',
      impact: 'Erosion of overall margin if negative-margin SKUs or deals are not tightly controlled.',
      recommendation: [
        'List all SKUs and customers with consistently negative fGP and review deal structures.',
        'Cap depth and frequency of promotions for SKUs that do not recover margin through uplift.',
        'Introduce guardrails so new trade terms cannot push fGP below agreed thresholds.',
        'Align sales and finance on a common view of margin by SKU, customer and channel.',
        'Track negative-margin share monthly and include it in commercial performance reviews.'
      ],
      status: 'resolved',
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
        <div 
          className="rounded-lg p-4"
          style={{
            background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
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
          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                3
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Critical Issues</p>
              <p className="text-xs text-white opacity-75">Require immediate attention</p>
            </div>
          </div>

          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                5
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Under Investigation</p>
              <p className="text-xs text-white opacity-75">Analysis in progress</p>
            </div>
          </div>

          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                12
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Resolved</p>
              <p className="text-xs text-white opacity-75">Successfully addressed</p>
            </div>
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
                className="rounded-lg p-6"
                style={{
                  background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                  border: '1px solid rgba(0, 0, 0, 0.1)'
                }}
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
                          <p className="text-xs" style={{ color: '#92400e', whiteSpace: 'pre-line' }}>
                            {Array.isArray(issue.recommendation)
                              ? issue.recommendation.join('\n')
                              : issue.recommendation}
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
        <div 
          className="rounded-lg p-5"
          style={{
            background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
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
                      backgroundColor: '#1e293b',
                      borderRadius: 6
                    },
                    {
                      label: 'Profit',
                      data: businessData.map(item => item.Gross_Profit),
                      backgroundColor: '#EDD5B1',
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
