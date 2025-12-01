// Static Sample Data for BeaconIQ Portal Demo
// Use this data for showcasing without database connection

export const staticData = {
  // Filter Options
  filters: {
    years: [2023, 2024, 2025],
    months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    businesses: [
      'Enterprise Solutions',
      'Cloud Services',
      'Consumer Products',
      'Digital Marketing',
      'Professional Services',
      'Technology Hardware',
      'Software Development',
      'Data Analytics'
    ],
    channels: [
      'Direct Sales',
      'E-commerce',
      'Retail Partners',
      'Distributors',
      'Wholesale',
      'Online Marketplace',
      'Enterprise Accounts',
      'Channel Partners'
    ],
    brands: [
      'Premium Suite',
      'Professional Edition',
      'Enterprise Plus',
      'Business Essentials',
      'Starter Pack',
      'Advanced Tools',
      'Cloud Connect',
      'Data Insights Pro',
      'Analytics Dashboard',
      'Workflow Manager'
    ],
    customers: [
      'Enterprise Corp A',
      'Enterprise Corp B',
      'Mid-Market Company 1',
      'Mid-Market Company 2',
      'Tech Startup 1',
      'Retail Chain A',
      'Healthcare Provider 1',
      'Financial Services A',
      'Manufacturing Co 1',
      'Educational Institution A'
    ],
    categories: [
      'Software Licenses',
      'Cloud Infrastructure',
      'Data Analytics',
      'Security Solutions',
      'Productivity Tools',
      'Collaboration Software',
      'Customer Relationship Management',
      'Enterprise Resource Planning',
      'Human Capital Management',
      'Financial Management'
    ]
  },

  // Executive Overview / Business Compass Data
  executiveOverview: {
    total_revenue: 67145834.5,
    total_profit: 35682508.3,
    total_units: 122541250,
    
    yearly_performance: [
      { Year: 2023, Revenue: 21500000, Gross_Profit: 11200000, Units: 40000000 },
      { Year: 2024, Revenue: 24500000, Gross_Profit: 13000000, Units: 45000000 },
      { Year: 2025, Revenue: 21145834.5, Gross_Profit: 11482508.3, Units: 37541250 }
    ],
    
    business_performance: [
      { Business: 'Enterprise Solutions', Revenue: 12500000, Gross_Profit: 6800000, Units: 18000000 },
      { Business: 'Cloud Services', Revenue: 11200000, Gross_Profit: 6200000, Units: 16500000 },
      { Business: 'Consumer Products', Revenue: 9800000, Gross_Profit: 4900000, Units: 22000000 },
      { Business: 'Digital Marketing', Revenue: 8900000, Gross_Profit: 5100000, Units: 15000000 },
      { Business: 'Professional Services', Revenue: 7600000, Gross_Profit: 4200000, Units: 12500000 },
      { Business: 'Technology Hardware', Revenue: 6500000, Gross_Profit: 3100000, Units: 18500000 },
      { Business: 'Software Development', Revenue: 5845834.5, Gross_Profit: 3382508.3, Units: 11041250 },
      { Business: 'Data Analytics', Revenue: 4800000, Gross_Profit: 2000000, Units: 9000000 }
    ],
    
    monthly_trend: [
      { Month_Name: 'January', Revenue: 2100000, Gross_Profit: 1150000, Units: 3800000 },
      { Month_Name: 'February', Revenue: 2250000, Gross_Profit: 1200000, Units: 3950000 },
      { Month_Name: 'March', Revenue: 2600000, Gross_Profit: 1380000, Units: 4500000 },
      { Month_Name: 'April', Revenue: 2400000, Gross_Profit: 1280000, Units: 4200000 },
      { Month_Name: 'May', Revenue: 2550000, Gross_Profit: 1350000, Units: 4350000 },
      { Month_Name: 'June', Revenue: 2700000, Gross_Profit: 1450000, Units: 4600000 },
      { Month_Name: 'July', Revenue: 2500000, Gross_Profit: 1320000, Units: 4300000 },
      { Month_Name: 'August', Revenue: 2350000, Gross_Profit: 1250000, Units: 4100000 },
      { Month_Name: 'September', Revenue: 2695834.5, Gross_Profit: 1102508.3, Units: 5741250 }
    ],
    
    channel_performance: [
      { Channel: 'Direct Sales', Revenue: 15200000, Gross_Profit: 8100000, Units: 28000000 },
      { Channel: 'E-commerce', Revenue: 13800000, Gross_Profit: 7500000, Units: 26500000 },
      { Channel: 'Retail Partners', Revenue: 11500000, Gross_Profit: 6200000, Units: 22000000 },
      { Channel: 'Distributors', Revenue: 9200000, Gross_Profit: 4800000, Units: 17500000 },
      { Channel: 'Wholesale', Revenue: 7600000, Gross_Profit: 3900000, Units: 14000000 },
      { Channel: 'Online Marketplace', Revenue: 5400000, Gross_Profit: 2800000, Units: 8500000 },
      { Channel: 'Enterprise Accounts', Revenue: 3245834.5, Gross_Profit: 1782508.3, Units: 4541250 },
      { Channel: 'Channel Partners', Revenue: 1200000, Gross_Profit: 600000, Units: 1500000 }
    ]
  },

  // Customer Analysis Data
  customerAnalysis: {
    channel_performance: [
      { Channel: 'Direct Sales', Revenue: 15200000, Gross_Profit: 8100000, Units: 28000000 },
      { Channel: 'E-commerce', Revenue: 13800000, Gross_Profit: 7500000, Units: 26500000 },
      { Channel: 'Retail Partners', Revenue: 11500000, Gross_Profit: 6200000, Units: 22000000 },
      { Channel: 'Distributors', Revenue: 9200000, Gross_Profit: 4800000, Units: 17500000 },
      { Channel: 'Wholesale', Revenue: 7600000, Gross_Profit: 3900000, Units: 14000000 },
      { Channel: 'Online Marketplace', Revenue: 5400000, Gross_Profit: 2800000, Units: 8500000 },
      { Channel: 'Enterprise Accounts', Revenue: 3245834.5, Gross_Profit: 1782508.3, Units: 4541250 },
      { Channel: 'Channel Partners', Revenue: 1200000, Gross_Profit: 600000, Units: 1500000 }
    ],
    
    top_customers: [
      { Customer: 'Enterprise Corp A', Revenue: 8500000, Gross_Profit: 4600000, Units: 15000000 },
      { Customer: 'Enterprise Corp B', Revenue: 7200000, Gross_Profit: 3900000, Units: 13000000 },
      { Customer: 'Mid-Market Company 1', Revenue: 6100000, Gross_Profit: 3200000, Units: 11000000 },
      { Customer: 'Retail Chain A', Revenue: 5300000, Gross_Profit: 2800000, Units: 9500000 },
      { Customer: 'Tech Startup 1', Revenue: 4800000, Gross_Profit: 2600000, Units: 8700000 },
      { Customer: 'Healthcare Provider 1', Revenue: 4200000, Gross_Profit: 2200000, Units: 7600000 },
      { Customer: 'Financial Services A', Revenue: 3900000, Gross_Profit: 2000000, Units: 7000000 },
      { Customer: 'Manufacturing Co 1', Revenue: 3500000, Gross_Profit: 1800000, Units: 6300000 },
      { Customer: 'Mid-Market Company 2', Revenue: 3100000, Gross_Profit: 1600000, Units: 5500000 },
      { Customer: 'Educational Institution A', Revenue: 2800000, Gross_Profit: 1400000, Units: 5000000 }
    ]
  },

  // Brand Analysis Data
  brandAnalysis: {
    brand_performance: [
      { Brand: 'Premium Suite', Revenue: 9800000, Gross_Profit: 5400000, Units: 14000000 },
      { Brand: 'Professional Edition', Revenue: 8600000, Gross_Profit: 4700000, Units: 12500000 },
      { Brand: 'Enterprise Plus', Revenue: 7900000, Gross_Profit: 4300000, Units: 11000000 },
      { Brand: 'Business Essentials', Revenue: 6700000, Gross_Profit: 3500000, Units: 10200000 },
      { Brand: 'Cloud Connect', Revenue: 5900000, Gross_Profit: 3200000, Units: 9100000 },
      { Brand: 'Data Insights Pro', Revenue: 5200000, Gross_Profit: 2800000, Units: 8300000 },
      { Brand: 'Analytics Dashboard', Revenue: 4600000, Gross_Profit: 2500000, Units: 7500000 },
      { Brand: 'Workflow Manager', Revenue: 4100000, Gross_Profit: 2200000, Units: 6800000 },
      { Brand: 'Starter Pack', Revenue: 3700000, Gross_Profit: 1900000, Units: 6200000 },
      { Brand: 'Advanced Tools', Revenue: 3300000, Gross_Profit: 1700000, Units: 5500000 },
      { Brand: 'Security Shield', Revenue: 2900000, Gross_Profit: 1500000, Units: 4900000 },
      { Brand: 'Performance Optimizer', Revenue: 2500000, Gross_Profit: 1300000, Units: 4300000 },
      { Brand: 'Integration Hub', Revenue: 2200000, Gross_Profit: 1100000, Units: 3800000 },
      { Brand: 'Mobile Solutions', Revenue: 1900000, Gross_Profit: 1000000, Units: 3300000 },
      { Brand: 'API Gateway', Revenue: 1645834.5, Gross_Profit: 882508.3, Units: 2841250 }
    ]
  },

  // Category Analysis Data
  categoryAnalysis: {
    category_performance: [
      { Category: 'Software Licenses', Revenue: 11200000, Gross_Profit: 6100000, Units: 16500000 },
      { Category: 'Cloud Infrastructure', Revenue: 9800000, Gross_Profit: 5300000, Units: 14200000 },
      { Category: 'Data Analytics', Revenue: 8500000, Gross_Profit: 4600000, Units: 12800000 },
      { Category: 'Security Solutions', Revenue: 7300000, Gross_Profit: 3900000, Units: 11000000 },
      { Category: 'Productivity Tools', Revenue: 6400000, Gross_Profit: 3400000, Units: 9800000 },
      { Category: 'Collaboration Software', Revenue: 5600000, Gross_Profit: 3000000, Units: 8600000 },
      { Category: 'CRM', Revenue: 4900000, Gross_Profit: 2600000, Units: 7500000 },
      { Category: 'ERP', Revenue: 4200000, Gross_Profit: 2200000, Units: 6400000 },
      { Category: 'HCM', Revenue: 3700000, Gross_Profit: 1900000, Units: 5600000 },
      { Category: 'Financial Management', Revenue: 3200000, Gross_Profit: 1700000, Units: 4900000 },
      { Category: 'Supply Chain', Revenue: 2800000, Gross_Profit: 1400000, Units: 4200000 },
      { Category: 'Marketing Automation', Revenue: 2400000, Gross_Profit: 1200000, Units: 3700000 },
      { Category: 'Sales Enablement', Revenue: 2100000, Gross_Profit: 1100000, Units: 3200000 },
      { Category: 'Customer Support', Revenue: 1800000, Gross_Profit: 900000, Units: 2800000 },
      { Category: 'IT Management', Revenue: 1345834.5, Gross_Profit: 682508.3, Units: 2241250 }
    ],
    
    subcategory_performance: [
      { Sub_Category: 'Annual License', Revenue: 4500000, Gross_Profit: 2400000, Units: 6800000 },
      { Sub_Category: 'Monthly Subscription', Revenue: 4200000, Gross_Profit: 2300000, Units: 6300000 },
      { Sub_Category: 'Enterprise Plan', Revenue: 3800000, Gross_Profit: 2000000, Units: 5700000 },
      { Sub_Category: 'Professional Plan', Revenue: 3400000, Gross_Profit: 1800000, Units: 5200000 },
      { Sub_Category: 'Cloud-Hosted', Revenue: 3100000, Gross_Profit: 1600000, Units: 4800000 },
      { Sub_Category: 'SaaS', Revenue: 2800000, Gross_Profit: 1500000, Units: 4300000 },
      { Sub_Category: 'Premium Support', Revenue: 2500000, Gross_Profit: 1300000, Units: 3900000 },
      { Sub_Category: 'Consulting Hours', Revenue: 2200000, Gross_Profit: 1100000, Units: 3500000 },
      { Sub_Category: 'Training Session', Revenue: 1900000, Gross_Profit: 1000000, Units: 3100000 },
      { Sub_Category: 'Basic Plan', Revenue: 1600000, Gross_Profit: 800000, Units: 2700000 }
    ]
  },

  // Projects Data
  projectsData: {
    // Top Projects
    topProjects: [
      {
        id: 1,
        name: 'Q1 2025 Product Launch - Premium Suite',
        category: 'Product Development',
        status: 'on-track',
        priority: 'high',
        progress: 72,
        budget: 850000,
        spent: 612000,
        expectedROI: 3.8,
        actualROI: null,
        startDate: '2024-11-01',
        endDate: '2025-03-31',
        team: 'Product & Marketing Team',
        teamSize: 15,
        milestones: 8,
        completedMilestones: 6,
        keyMetrics: {
          revenue_impact: 3200000,
          market_share_gain: 4.2,
          customer_acquisition: 850
        }
      },
      {
        id: 2,
        name: 'Enterprise Cloud Migration Initiative',
        category: 'Infrastructure',
        status: 'at-risk',
        priority: 'critical',
        progress: 58,
        budget: 1200000,
        spent: 780000,
        expectedROI: 2.4,
        actualROI: null,
        startDate: '2024-09-01',
        endDate: '2025-06-30',
        team: 'Cloud Infrastructure Team',
        teamSize: 22,
        milestones: 12,
        completedMilestones: 6,
        keyMetrics: {
          cost_savings: 450000,
          uptime_improvement: 15,
          migration_complete: 58
        }
      },
      {
        id: 3,
        name: 'Customer Retention Excellence Program',
        category: 'Customer Success',
        status: 'completed',
        priority: 'high',
        progress: 100,
        budget: 350000,
        spent: 335000,
        expectedROI: 5.2,
        actualROI: 6.1,
        startDate: '2024-07-01',
        endDate: '2024-12-31',
        team: 'Customer Success Team',
        teamSize: 12,
        milestones: 6,
        completedMilestones: 6,
        keyMetrics: {
          retention_rate: 94.5,
          churn_reduction: 35,
          upsell_revenue: 2100000
        }
      },
      {
        id: 4,
        name: 'AI-Powered Analytics Platform',
        category: 'Product Innovation',
        status: 'on-track',
        priority: 'high',
        progress: 45,
        budget: 980000,
        spent: 441000,
        expectedROI: 4.5,
        actualROI: null,
        startDate: '2024-12-01',
        endDate: '2025-08-31',
        team: 'Data Science & Engineering',
        teamSize: 18,
        milestones: 10,
        completedMilestones: 4,
        keyMetrics: {
          feature_adoption: 68,
          user_satisfaction: 4.6,
          efficiency_gain: 42
        }
      },
      {
        id: 5,
        name: 'Global Market Expansion - APAC',
        category: 'Business Growth',
        status: 'on-track',
        priority: 'medium',
        progress: 35,
        budget: 1500000,
        spent: 525000,
        expectedROI: 3.2,
        actualROI: null,
        startDate: '2025-01-01',
        endDate: '2025-12-31',
        team: 'International Business Development',
        teamSize: 25,
        milestones: 15,
        completedMilestones: 5,
        keyMetrics: {
          new_markets: 4,
          revenue_projection: 4800000,
          partnerships: 12
        }
      },
      {
        id: 6,
        name: 'Security & Compliance Upgrade',
        category: 'Security',
        status: 'delayed',
        priority: 'critical',
        progress: 62,
        budget: 650000,
        spent: 520000,
        expectedROI: 1.8,
        actualROI: null,
        startDate: '2024-10-01',
        endDate: '2025-04-30',
        team: 'Security & Compliance',
        teamSize: 10,
        milestones: 8,
        completedMilestones: 4,
        keyMetrics: {
          compliance_score: 88,
          vulnerabilities_fixed: 156,
          audit_readiness: 75
        }
      }
    ],

    // Business Planner
    businessPlans: [
      {
        id: 1,
        planName: 'Q4 2025 Strategic Initiatives',
        period: 'Q4 2025',
        totalBudget: 3200000,
        allocatedBudget: 2850000,
        expectedRevenue: 12400000,
        initiatives: [
          { name: 'Product Portfolio Expansion', budget: 850000, revenue: 3800000, priority: 'high', status: 'planning' },
          { name: 'Sales Team Expansion', budget: 550000, revenue: 2900000, priority: 'high', status: 'approved' },
          { name: 'Marketing Campaign - Summer Launch', budget: 620000, revenue: 2500000, priority: 'medium', status: 'planning' },
          { name: 'Customer Experience Redesign', budget: 430000, revenue: 1600000, priority: 'medium', status: 'planning' },
          { name: 'Technology Infrastructure', budget: 400000, revenue: 1600000, priority: 'high', status: 'approved' }
        ],
        milestones: [
          { name: 'Budget Approval', date: '2025-09-15', status: 'completed', progress: 100 },
          { name: 'Resource Allocation', date: '2025-09-30', status: 'in-progress', progress: 75 },
          { name: 'Initiative Kickoff', date: '2025-10-10', status: 'pending', progress: 0 },
          { name: 'Mid-Quarter Review', date: '2025-11-15', status: 'pending', progress: 0 },
          { name: 'Final Review & Optimization', date: '2025-12-25', status: 'pending', progress: 0 }
        ],
        aiInsights: [
          'Marketing Campaign budget should increase by 12% based on Q1 performance and seasonal trends',
          'Technology Infrastructure investment shows highest ROI potential (4.2x) - consider increasing allocation',
          'Customer Experience Redesign shows strong correlation with retention - recommend fast-tracking',
          'Sales expansion timing aligns well with market opportunity window in EMEA region'
        ]
      },
      {
        id: 2,
        planName: 'H2 2025 Growth Strategy',
        period: 'H2 2025',
        totalBudget: 8500000,
        allocatedBudget: 6200000,
        expectedRevenue: 34500000,
        initiatives: [
          { name: 'International Expansion', budget: 1800000, revenue: 9200000, priority: 'critical', status: 'planning' },
          { name: 'AI Product Suite Launch', budget: 1450000, revenue: 11500000, priority: 'critical', status: 'planning' },
          { name: 'Enterprise Partnerships Program', budget: 980000, revenue: 6800000, priority: 'high', status: 'research' },
          { name: 'Brand Transformation', budget: 720000, revenue: 3500000, priority: 'medium', status: 'research' },
          { name: 'Operational Excellence Initiative', budget: 1250000, revenue: 3500000, priority: 'high', status: 'planning' }
        ],
        milestones: [
          { name: 'Strategic Planning Complete', date: '2025-05-01', status: 'in-progress', progress: 60 },
          { name: 'Board Approval', date: '2025-05-30', status: 'pending', progress: 0 },
          { name: 'Q3 Execution Start', date: '2025-07-01', status: 'pending', progress: 0 },
          { name: 'Mid-Period Review', date: '2025-09-15', status: 'pending', progress: 0 },
          { name: 'Year-End Assessment', date: '2025-12-15', status: 'pending', progress: 0 }
        ],
        aiInsights: [
          'International Expansion shows 87% success probability based on market analysis and competitor trends',
          'AI Product Suite has strong pre-launch demand signals - consider accelerating timeline by 3 weeks',
          'Operational Excellence can be partially funded through cost optimization - net investment reduced by 18%',
          'Enterprise Partnerships timing critical - Q3 launch aligns with enterprise budget cycles'
        ]
      }
    ],

    // Campaign Cockpit
    campaigns: [
      {
        id: 1,
        name: 'Spring Product Launch 2025',
        type: 'Product Launch',
        status: 'active',
        startDate: '2025-02-15',
        endDate: '2025-04-30',
        budget: 520000,
        spent: 342000,
        revenue: 2850000,
        leads: 8450,
        conversions: 1240,
        conversionRate: 14.7,
        roi: 4.8,
        channels: ['E-commerce', 'Direct Sales', 'Retail Partners'],
        targetAudience: 'Enterprise',
        reach: 145000,
        engagement: 23400,
        engagementRate: 16.1
      },
      {
        id: 2,
        name: 'Customer Loyalty Campaign Q1',
        type: 'Retention',
        status: 'active',
        startDate: '2025-01-01',
        endDate: '2025-03-31',
        budget: 180000,
        spent: 165000,
        revenue: 890000,
        leads: 3200,
        conversions: 1850,
        conversionRate: 57.8,
        roi: 3.9,
        channels: ['Direct Sales', 'Enterprise Accounts'],
        targetAudience: 'Existing Customers',
        reach: 12500,
        engagement: 8900,
        engagementRate: 71.2
      },
      {
        id: 3,
        name: 'Digital Transformation Webinar Series',
        type: 'Lead Generation',
        status: 'active',
        startDate: '2025-02-01',
        endDate: '2025-05-31',
        budget: 95000,
        spent: 58000,
        revenue: 420000,
        leads: 12800,
        conversions: 890,
        conversionRate: 7.0,
        roi: 3.4,
        channels: ['Online Marketplace', 'E-commerce'],
        targetAudience: 'Mid-Market',
        reach: 58000,
        engagement: 12800,
        engagementRate: 22.1
      },
      {
        id: 4,
        name: 'Year-End Enterprise Sale 2024',
        type: 'Sales Promotion',
        status: 'completed',
        startDate: '2024-11-15',
        endDate: '2024-12-31',
        budget: 420000,
        spent: 415000,
        revenue: 5600000,
        leads: 4200,
        conversions: 2100,
        conversionRate: 50.0,
        roi: 12.5,
        channels: ['Direct Sales', 'Enterprise Accounts', 'Channel Partners'],
        targetAudience: 'Enterprise',
        reach: 28000,
        engagement: 9800,
        engagementRate: 35.0
      },
      {
        id: 5,
        name: 'Brand Awareness - Social Media Blitz',
        type: 'Brand Awareness',
        status: 'active',
        startDate: '2025-03-01',
        endDate: '2025-06-30',
        budget: 280000,
        spent: 112000,
        revenue: 650000,
        leads: 18500,
        conversions: 720,
        conversionRate: 3.9,
        roi: 1.3,
        channels: ['Online Marketplace', 'E-commerce'],
        targetAudience: 'SMB',
        reach: 285000,
        engagement: 42000,
        engagementRate: 14.7
      },
      {
        id: 6,
        name: 'Partner Enablement Program',
        type: 'Channel Marketing',
        status: 'planning',
        startDate: '2025-04-15',
        endDate: '2025-07-31',
        budget: 350000,
        spent: 0,
        revenue: 0,
        leads: 0,
        conversions: 0,
        conversionRate: 0,
        roi: 0,
        channels: ['Channel Partners', 'Distributors'],
        targetAudience: 'Partners',
        reach: 0,
        engagement: 0,
        engagementRate: 0
      }
    ]
  }
};

export default staticData;
