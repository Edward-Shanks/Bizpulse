import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  Euro, 
  AlertCircle,
  Mail,
  Share2,
  Video,
  Users as UsersIcon,
  Play,
  Sparkles,
  Calendar,
  Target,
  Archive,
  StopCircle
} from 'lucide-react';
import { toast } from 'sonner';

const Cockpit = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('recommended');

  // Key Insights data
  const insights = [
    {
      icon: TrendingUp,
      title: 'Revenue Opportunity',
      description: 'Untapped market segment with 25% growth potential',
      color: { bg: '#d1fae5', text: '#065f46', icon: '#10b981' },
      navigateTo: '/projects',
      targetTab: 'goals-management'
    },
    {
      icon: Euro,
      title: 'Cost Optimization',
      description: 'Operational efficiency improvements can save €150K annually',
      color: { bg: '#dbeafe', text: '#1e3a8a', icon: '#3b82f6' },
      navigateTo: '/projects',
      targetTab: 'goals-management'
    },
    {
      icon: AlertCircle,
      title: 'Customer Retention',
      description: 'Churn rate increased by 3% - immediate action needed',
      color: { bg: '#fef3c7', text: '#92400e', icon: '#f59e0b' },
      navigateTo: '/projects',
      targetTab: 'goals-management'
    }
  ];

  // Handle insight card click - navigate to Projects Goals Management
  const handleInsightClick = (insight) => {
    if (insight.navigateTo) {
      // Store the target tab in sessionStorage so Projects page can read it
      if (insight.targetTab) {
        sessionStorage.setItem('projectsActiveTab', insight.targetTab);
      }
      navigate(insight.navigateTo);
      toast.success(`Navigating to Goals Management...`);
    }
  };

  // Action Items
  const actionItems = [
    { id: 1, title: 'Launch Q4 Campaign', dueDate: '2025-01-15', priority: 'high' },
    { id: 2, title: 'Review Pricing Strategy', dueDate: '2025-01-20', priority: 'medium' },
    { id: 3, title: 'Analyze Competitor Activity', dueDate: '2025-01-10', priority: 'high' },
    { id: 4, title: 'Optimize Supply Chain', dueDate: '2025-01-25', priority: 'medium' }
  ];

  // Campaign data
  const [campaigns, setCampaigns] = useState({
    recommended: [
      {
        id: 1,
        name: 'Summer Sales Boost',
        description: 'Targeted campaign for summer season with focus on outdoor products',
        aiScore: 72,
        budget: '€50K',
        roi: '320%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        aiRecommendation: 'High potential for Q3 revenue growth. Recommended to activate immediately.'
      },
      {
        id: 2,
        name: 'Holiday Campaign 2025',
        description: 'Comprehensive holiday season marketing initiative',
        aiScore: 78,
        budget: '€175K',
        roi: '450%',
        channels: ['Email', 'Social Media', 'Video', 'Influencer'],
        aiRecommendation: 'Optimal timing for holiday shopping season. Expected 45% increase in conversions.'
      },
      {
        id: 3,
        name: 'New Product Launch',
        description: 'Launch campaign for new premium product line',
        aiScore: 75,
        budget: '€60K',
        roi: '380%',
        channels: ['Social Media', 'Video', 'Influencer'],
        aiRecommendation: 'Prioritize Japan and Singapore markets first. Engage local consulting partners.'
      },
      {
        id: 4,
        name: 'Back to School Promo',
        description: 'Targeted campaign for students and parents',
        aiScore: 77,
        budget: '€45K',
        roi: '340%',
        channels: ['Email', 'Display Ads', 'Social Media'],
        aiRecommendation: 'Strong seasonal opportunity. Recommend early August activation for maximum impact.'
      },
      {
        id: 5,
        name: 'Customer Loyalty Program',
        description: 'Retention campaign for existing high-value customers',
        aiScore: 81,
        budget: '€35K',
        roi: '520%',
        channels: ['Email', 'Video'],
        aiRecommendation: 'Top 10 customers account for 62% revenue. Focus on personalized offers.'
      },
      {
        id: 6,
        name: 'Spring Flash Sale',
        description: 'Limited-time promotional campaign for spring season',
        aiScore: 73,
        budget: '€28K',
        roi: '290%',
        channels: ['Social Media', 'Display Ads', 'Email'],
        aiRecommendation: 'Budget-efficient option with solid ROI. Perfect for quick wins.'
      }
    ],
    active: [
      {
        id: 7,
        name: 'Brand Awareness Drive',
        description: 'Ongoing brand building across multiple touchpoints',
        aiScore: 68,
        budget: '€40K',
        roi: '280%',
        channels: ['Social Media', 'Display Ads'],
        startDate: '2025-01-05',
        status: 'running'
      },
      {
        id: 8,
        name: 'Winter Clearance Sale',
        description: 'End of season inventory clearance',
        aiScore: 72,
        budget: '€55K',
        roi: '310%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        startDate: '2025-01-10',
        status: 'running'
      },
      {
        id: 9,
        name: 'Digital Transformation Series',
        description: 'Webinar series for lead generation',
        aiScore: 66,
        budget: '€30K',
        roi: '240%',
        channels: ['Video', 'Email', 'Social Media'],
        startDate: '2025-01-08',
        status: 'running'
      },
      {
        id: 10,
        name: 'Partner Co-Marketing',
        description: 'Joint marketing initiative with strategic partners',
        aiScore: 74,
        budget: '€65K',
        roi: '380%',
        channels: ['Email', 'Video', 'Display Ads'],
        startDate: '2025-01-12',
        status: 'running'
      }
    ],
    archived: [
      {
        id: 11,
        name: 'Black Friday 2025',
        description: 'Successful Black Friday promotional campaign',
        aiScore: 75,
        budget: '€85K',
        roi: '520%',
        actualROI: '548%',
        channels: ['Email', 'Social Media', 'Video', 'Display Ads'],
        endDate: '2025-11-29'
      },
      {
        id: 12,
        name: 'Cyber Monday Special',
        description: 'Online-focused promotional campaign',
        aiScore: 73,
        budget: '€70K',
        roi: '480%',
        actualROI: '495%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        endDate: '2025-12-02'
      },
      {
        id: 13,
        name: 'Q3 Product Showcase',
        description: 'Virtual product demonstration series',
        aiScore: 71,
        budget: '€42K',
        roi: '300%',
        actualROI: '315%',
        channels: ['Video', 'Email', 'Social Media'],
        endDate: '2025-09-30'
      },
      {
        id: 14,
        name: 'Summer Festival Sponsorship',
        description: 'Event sponsorship and brand activation',
        aiScore: 69,
        budget: '€50K',
        roi: '270%',
        actualROI: '285%',
        channels: ['Social Media', 'Display Ads'],
        endDate: '2025-07-15'
      },
      {
        id: 15,
        name: 'Spring Product Launch 2025',
        description: 'Major product line introduction campaign',
        aiScore: 78,
        budget: '€95K',
        roi: '420%',
        actualROI: '442%',
        channels: ['Email', 'Social Media', 'Video', 'Influencer'],
        endDate: '2025-05-31'
      }
    ]
  });

  const handleActivate = (campaignId, campaignName, fromTab = 'recommended') => {
    // Move campaign from recommended or archived to active
    const campaign = fromTab === 'archived' 
      ? campaigns.archived.find(c => c.id === campaignId)
      : campaigns.recommended.find(c => c.id === campaignId);
      
    if (campaign) {
      setCampaigns(prev => ({
        ...prev,
        [fromTab]: prev[fromTab].filter(c => c.id !== campaignId),
        active: [...prev.active, { ...campaign, startDate: new Date().toISOString().split('T')[0], status: 'running' }]
      }));
      toast.success(`Campaign "${campaignName}" activated successfully!`);
    }
  };

  const handleDeactivate = (campaignId, campaignName) => {
    // Move campaign from active to archived
    const campaign = campaigns.active.find(c => c.id === campaignId);
    if (campaign) {
      setCampaigns(prev => ({
        ...prev,
        active: prev.active.filter(c => c.id !== campaignId),
        archived: [...prev.archived, { ...campaign, endDate: new Date().toISOString().split('T')[0], actualROI: campaign.roi }]
      }));
      toast.success(`Campaign "${campaignName}" deactivated and archived successfully!`);
    }
  };

  const handleArchive = (campaignId, campaignName, fromTab = 'recommended') => {
    // Move campaign from recommended or active to archived
    const campaign = fromTab === 'active'
      ? campaigns.active.find(c => c.id === campaignId)
      : campaigns.recommended.find(c => c.id === campaignId);
      
    if (campaign) {
      setCampaigns(prev => ({
        ...prev,
        [fromTab]: prev[fromTab].filter(c => c.id !== campaignId),
        archived: [...prev.archived, { ...campaign, endDate: new Date().toISOString().split('T')[0] }]
      }));
      toast.success(`Campaign "${campaignName}" archived successfully!`);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Business Cockpit</h1>
          <p className="text-gray-600">AI-powered business intelligence and campaign management</p>
        </div>

        {/* Business AI Score Banner */}
        <div 
          className="rounded-xl p-6 border"
          style={{ background: '#fef3c7', borderColor: '#f59e0b' }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Business AI Score</h2>
              <p className="text-sm text-gray-700">Overall business health and performance indicator</p>
            </div>
            <div className="text-5xl font-bold" style={{ color: '#d97706' }}>
              65<span className="text-2xl text-gray-600">/100</span>
            </div>
          </div>
        </div>

        {/* Key Insights */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Key Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {insights.map((insight, idx) => {
              const Icon = insight.icon;
              return (
                <div
                  key={idx}
                  onClick={() => handleInsightClick(insight)}
                  className="rounded-lg p-5 border cursor-pointer hover:shadow-md transition-shadow"
                  style={{ 
                    background: insight.color.bg, 
                    borderColor: insight.color.bg
                  }}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      <Icon className="w-5 h-5" style={{ color: insight.color.icon }} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1" style={{ color: insight.color.text }}>
                        {insight.title}
                      </h3>
                      <p className="text-sm" style={{ color: insight.color.text, opacity: 0.8 }}>
                        {insight.description}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Action Items */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Top Action Items</h2>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {actionItems.map((item, idx) => (
              <div
                key={item.id}
                className={`flex items-center justify-between p-4 ${
                  idx !== actionItems.length - 1 ? 'border-b border-gray-200' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    item.priority === 'high' ? 'bg-red-500' : 'bg-yellow-500'
                  }`}></div>
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <div>
                    <h4 className="font-medium text-gray-900">{item.title}</h4>
                    <p className="text-sm text-gray-500">Due: {item.dueDate}</p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  item.priority === 'high' 
                    ? 'bg-red-100 text-red-700' 
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {item.priority}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Campaign Tabs */}
        <div>
          <div className="flex gap-2 mb-4">
            {[
              { key: 'recommended', label: 'Recommended', count: campaigns.recommended.length },
              { key: 'active', label: 'Active', count: campaigns.active.length },
              { key: 'archived', label: 'Archived', count: campaigns.archived.length }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  activeTab === tab.key
                    ? 'bg-amber-100 text-amber-900'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>

          {/* Campaign Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {campaigns[activeTab].map((campaign) => (
              <div key={campaign.id} className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{campaign.name}</h3>
                    <p className="text-sm text-gray-600 mb-3">{campaign.description}</p>
                  </div>
                  <div className="flex flex-col items-end">
                    <div className="flex items-baseline gap-1 mb-1">
                      <span className="text-2xl font-bold" style={{ color: '#f59e0b' }}>
                        {campaign.aiScore}%
                      </span>
                      <span className="text-xs text-gray-500">AI Score</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Budget</p>
                    <p className="font-semibold text-gray-900">{campaign.budget}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">{activeTab === 'archived' && campaign.actualROI ? 'Actual ROI' : 'Expected ROI'}</p>
                    <p className="font-semibold text-gray-900">{activeTab === 'archived' && campaign.actualROI ? campaign.actualROI : campaign.roi}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Channels</p>
                    <p className="font-semibold text-gray-900">{campaign.channels.length}</p>
                  </div>
                </div>

                {activeTab === 'recommended' && campaign.aiRecommendation && (
                  <div 
                    className="rounded-lg p-3 mb-4"
                    style={{ background: '#dbeafe' }}
                  >
                    <div className="flex items-start gap-2">
                      <Sparkles className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#1e40af' }} />
                      <div>
                        <p className="text-xs font-semibold mb-1" style={{ color: '#1e3a8a' }}>
                          AI Recommendation:
                        </p>
                        <p className="text-xs" style={{ color: '#1e3a8a' }}>
                          {campaign.aiRecommendation}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'active' && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-1">Start Date</p>
                    <p className="text-sm font-medium text-gray-900">{campaign.startDate}</p>
                  </div>
                )}

                {activeTab === 'archived' && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-1">End Date</p>
                    <p className="text-sm font-medium text-gray-900">{campaign.endDate}</p>
                  </div>
                )}

                <div className="flex items-center gap-2 mb-4 flex-wrap">
                  {campaign.channels.map((channel, idx) => {
                    const channelIcons = {
                      'Email': Mail,
                      'Social Media': Share2,
                      'Video': Video,
                      'Display Ads': Target,
                      'Influencer': UsersIcon,
                      'PR': Sparkles
                    };
                    const ChannelIcon = channelIcons[channel] || Target;
                    return (
                      <div
                        key={idx}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-full"
                      >
                        <ChannelIcon className="w-3.5 h-3.5 text-gray-600" />
                        <span className="text-xs font-medium text-gray-700">{channel}</span>
                      </div>
                    );
                  })}
                </div>

                {activeTab === 'recommended' && (
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleActivate(campaign.id, campaign.name)}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Activate
                    </Button>
                    <Button
                      onClick={() => handleArchive(campaign.id, campaign.name)}
                      className="flex-1 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300"
                      variant="outline"
                    >
                      <Archive className="w-4 h-4 mr-2" />
                      Archive
                    </Button>
                  </div>
                )}

                {activeTab === 'active' && (
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleDeactivate(campaign.id, campaign.name)}
                      className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                    >
                      <StopCircle className="w-4 h-4 mr-2" />
                      Deactivate
                    </Button>
                    <Button
                      onClick={() => handleArchive(campaign.id, campaign.name, 'active')}
                      className="flex-1 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300"
                      variant="outline"
                    >
                      <Archive className="w-4 h-4 mr-2" />
                      Archive
                    </Button>
                  </div>
                )}

                {activeTab === 'archived' && (
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleActivate(campaign.id, campaign.name, 'archived')}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Activate
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Cockpit;
