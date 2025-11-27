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
  StopCircle,
  FileText,
  ChevronDown,
  Info
} from 'lucide-react';
import { toast } from 'sonner';

const Cockpit = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('recommended');

  // Key Insights data - 4 cards with gradient backgrounds matching Figma
  const insights = [
    {
      icon: Target,
      title: 'Business AI Score',
      score: '65/100',
      description: 'Overall Business Health and Performance',
      navigateTo: null
    },
    {
      icon: TrendingUp,
      title: 'Revenue Opportunity',
      description: 'Untapped market segments with 20% growth potential',
      navigateTo: '/projects',
      targetTab: 'goals-management'
    },
    {
      icon: Euro,
      title: 'Cost Optimization',
      description: 'Reduce operational expenses by 15% across all departments annually',
      navigateTo: '/projects',
      targetTab: 'goals-management'
    },
    {
      icon: AlertCircle,
      title: 'Customer Retention',
      description: 'Improve customer loyalty by 10% through personalized interactions',
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

  // Action Items - split into Critical and Impact
  const [criticalPriorityFilter, setCriticalPriorityFilter] = useState('all');
  const [impactPriorityFilter, setImpactPriorityFilter] = useState('all');
  
  const actionItems = {
    critical: [
      { id: 1, title: 'Launch QA Campaign', dueDate: '2025-01-15', priority: 'high' },
      { id: 2, title: 'Launch QA Campaign', dueDate: '2025-01-15', priority: 'high' },
      { id: 3, title: 'Launch QA Campaign', dueDate: '2025-01-15', priority: 'high' }
    ],
    impact: [
      { id: 4, title: 'Launch QA Campaign', dueDate: '2025-01-15', priority: 'high' },
      { id: 5, title: 'Launch QA Campaign', dueDate: '2025-01-15', priority: 'medium' },
      { id: 6, title: 'Launch QA Campaign', dueDate: '2025-01-15', priority: 'high' }
    ]
  };
  
  const getFilteredItems = (items, filter) => {
    if (filter === 'all') return items;
    return items.filter(item => item.priority === filter);
  };

  // Campaign data
  const [campaigns, setCampaigns] = useState({
    recommended: [
      {
        id: 1,
        name: 'Summer Sales Boost',
        description: 'Targeted campaign for summer season with focus on outdoor products',
        aiScore: 72,
        budget: '€50K',
        growth: '323%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        aiRecommendation: 'AI recommendation to increase reach by 30% through influencer marketing'
      },
      {
        id: 2,
        name: 'Holiday Campaign 2025',
        description: 'Targeted campaign for holiday season with focus on outdoor products',
        aiScore: 78,
        budget: '€75K',
        growth: '450%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        aiRecommendation: 'AI recommendation to increase reach by 30% through influencer marketing'
      },
      {
        id: 3,
        name: 'New Product Launch',
        description: 'Launch campaign for new premium product line',
        aiScore: 75,
        budget: '€60K',
        growth: '380%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        aiRecommendation: 'AI recommendation to increase reach by 30% through influencer marketing'
      },
      {
        id: 4,
        name: 'Back to School Promo',
        description: 'Targeted campaign for students and parents',
        aiScore: 77,
        budget: '€45K',
        growth: '340%',
        channels: ['Email', 'Display Ads', 'Social Media'],
        aiRecommendation: 'AI recommendation to increase reach by 30% through influencer marketing'
      },
      {
        id: 5,
        name: 'Customer Loyalty Program',
        description: 'Retention campaign for existing high-value customers',
        aiScore: 81,
        budget: '€35K',
        growth: '520%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        aiRecommendation: 'AI recommendation to increase reach by 30% through influencer marketing'
      },
      {
        id: 6,
        name: 'Spring Flash Sale',
        description: 'Limited-time promotional campaign for spring season',
        aiScore: 73,
        budget: '€28K',
        growth: '290%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        aiRecommendation: 'AI recommendation to increase reach by 30% through influencer marketing'
      }
    ],
    active: [
      {
        id: 7,
        name: 'Brand Awareness Drive',
        description: 'Ongoing brand building across multiple touchpoints',
        aiScore: 68,
        budget: '€40K',
        growth: '280%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        startDate: '2025-01-05',
        status: 'running'
      },
      {
        id: 8,
        name: 'Winter Clearance Sale',
        description: 'End of season inventory clearance',
        aiScore: 72,
        budget: '€55K',
        growth: '310%',
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
        growth: '240%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        startDate: '2025-01-08',
        status: 'running'
      },
      {
        id: 10,
        name: 'Partner Co-Marketing',
        description: 'Joint marketing initiative with strategic partners',
        aiScore: 74,
        budget: '€65K',
        growth: '380%',
        channels: ['Email', 'Social Media', 'Display Ads'],
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
        growth: '520%',
        actualGrowth: '548%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        endDate: '2025-11-29'
      },
      {
        id: 12,
        name: 'Cyber Monday Special',
        description: 'Online-focused promotional campaign',
        aiScore: 73,
        budget: '€70K',
        growth: '480%',
        actualGrowth: '495%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        endDate: '2025-12-02'
      },
      {
        id: 13,
        name: 'Q3 Product Showcase',
        description: 'Virtual product demonstration series',
        aiScore: 71,
        budget: '€42K',
        growth: '300%',
        actualGrowth: '315%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        endDate: '2025-09-30'
      },
      {
        id: 14,
        name: 'Summer Festival Sponsorship',
        description: 'Event sponsorship and brand activation',
        aiScore: 69,
        budget: '€50K',
        growth: '270%',
        actualGrowth: '285%',
        channels: ['Email', 'Social Media', 'Display Ads'],
        endDate: '2025-07-15'
      },
      {
        id: 15,
        name: 'Spring Product Launch 2025',
        description: 'Major product line introduction campaign',
        aiScore: 78,
        budget: '€95K',
        growth: '420%',
        actualGrowth: '442%',
        channels: ['Email', 'Social Media', 'Display Ads'],
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
          <p className="text-gray-600">AI-powered Business and Revenue and Campaign Management</p>
        </div>

        {/* Key Insights - 4 cards with gradient backgrounds matching Figma */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Key Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {insights.map((insight, idx) => {
              return (
                <div
                  key={idx}
                  onClick={() => insight.navigateTo && handleInsightClick(insight)}
                  className={`rounded-lg p-5 text-white cursor-pointer hover:shadow-lg transition-shadow ${insight.navigateTo ? 'cursor-pointer' : ''}`}
                  style={{ 
                    background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
                    border: '1px solid rgba(255, 255, 255, 0.1)'
                  }}
                >
                  {insight.score ? (
                    // Business AI Score card
                    <div>
                      <div className="flex items-baseline gap-1 mb-2">
                        <span className="text-5xl font-bold" style={{ color: '#EDD5B1' }}>
                          65
                        </span>
                        <span className="text-2xl font-bold" style={{ color: '#EDD5B1' }}>
                          /100
                        </span>
                      </div>
                      <h3 className="font-semibold mb-1 text-sm text-white opacity-90">
                        {insight.title}
                      </h3>
                      <p className="text-xs text-white opacity-75">
                        {insight.description}
                      </p>
                    </div>
                  ) : (
                    // Other insight cards
                    <div>
                      <h3 className="font-semibold mb-2 text-base" style={{ color: '#EDD5B1' }}>
                        {insight.title}
                      </h3>
                      <p className="text-xs text-white opacity-75">
                        {insight.description}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Action Items - Two Columns */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Top Action Items</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Critical Column */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">Critical</h3>
                <select
                  value={criticalPriorityFilter}
                  onChange={(e) => setCriticalPriorityFilter(e.target.value)}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                >
                  <option value="all">Priority</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                {getFilteredItems(actionItems.critical, criticalPriorityFilter).map((item, idx) => (
                  <div
                    key={item.id}
                    className={`flex items-center justify-between p-4 ${
                      idx !== getFilteredItems(actionItems.critical, criticalPriorityFilter).length - 1 ? 'border-b border-gray-200' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <div>
                        <h4 className="font-medium text-gray-900 text-sm">{item.title}</h4>
                        <p className="text-xs text-gray-500">Due - {new Date(item.dueDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      item.priority === 'high' 
                        ? 'bg-red-100 text-red-700' 
                        : item.priority === 'medium'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Impact Column */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">Impact</h3>
                <select
                  value={impactPriorityFilter}
                  onChange={(e) => setImpactPriorityFilter(e.target.value)}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                >
                  <option value="all">Priority</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                {getFilteredItems(actionItems.impact, impactPriorityFilter).map((item, idx) => (
                  <div
                    key={item.id}
                    className={`flex items-center justify-between p-4 ${
                      idx !== getFilteredItems(actionItems.impact, impactPriorityFilter).length - 1 ? 'border-b border-gray-200' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <div>
                        <h4 className="font-medium text-gray-900 text-sm">{item.title}</h4>
                        <p className="text-xs text-gray-500">Due - {new Date(item.dueDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      item.priority === 'high' 
                        ? 'bg-red-100 text-red-700' 
                        : item.priority === 'medium'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
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
            {campaigns[activeTab].map((campaign) => {
              return (
                <div 
                  key={campaign.id} 
                  className="rounded-[10px] border border-gray-200 p-6"
                  style={{
                    background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                    border: '1px solid rgba(0, 0, 0, 0.1)'
                  }}
                >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{campaign.name}</h3>
                    <p className="text-sm text-gray-600 mb-4">{campaign.description}</p>
                  </div>
                  {/* AI Score on Right Side */}
                  <div className="flex flex-col items-end flex-shrink-0 ml-4">
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">{campaign.aiScore}%</p>
                      <p className="text-xs text-gray-500 mt-1">AI Score</p>
                    </div>
                  </div>
                </div>

                {/* Row 1: Channels and Budget */}
                <div className="flex items-center justify-between gap-4 mb-3">
                  {/* Channels - White Card */}
                  <div className="flex-1 bg-white rounded-lg p-3 border border-gray-200">
                    <p className="text-sm font-medium text-gray-900 mb-2">{campaign.channels.length} Channels</p>
                    <div className="flex items-center gap-3">
                      {campaign.channels.map((channel, idx) => {
                        const channelLogos = {
                          'Email': '/email_logo.svg',
                          'Social Media': '/social_logo.svg',
                          'Video': '/video_logo.svg',
                          'Display Ads': '/display_ads_logo.svg',
                          'Influencer': '/social_logo.svg'
                        };
                        const logoPath = channelLogos[channel] || '/display_ads_logo.svg';
                        return (
                          <div key={idx} className="flex flex-col items-center gap-1.5">
                            <div className="w-6 h-6 flex items-center justify-center">
                              <img src={logoPath} alt={channel} className="w-full h-full object-contain" />
                            </div>
                            <span className="text-xs text-gray-600">{channel}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Budget on Right */}
                  <div className="flex flex-col items-end flex-shrink-0" style={{ minWidth: '100px' }}>
                    <p className="text-lg font-semibold text-gray-900">{campaign.budget}</p>
                    <p className="text-xs text-gray-500 mt-1">Budget</p>
                  </div>
                </div>

                {/* Row 2: AI Recommendation and Expected ROI */}
                {activeTab === 'recommended' && campaign.aiRecommendation && (
                  <div className="flex items-center justify-between gap-4 mb-4">
                    {/* AI Recommendation - Light Beige Background */}
                    <div 
                      className="flex-1 rounded-lg p-3"
                      style={{ background: '#F2E9DB' }}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <h4 className="text-sm font-semibold text-gray-900 mb-1">AI Recommendation</h4>
                          <p className="text-xs text-gray-700 leading-relaxed">
                            {campaign.aiRecommendation}
                          </p>
                        </div>
                        <img src="/ai_logo.svg" alt="AI" className="w-5 h-5 flex-shrink-0" />
                      </div>
                    </div>

                    {/* Expected ROI on Right */}
                    <div className="flex flex-col items-end flex-shrink-0" style={{ minWidth: '100px' }}>
                      <p className="text-lg font-semibold text-gray-900">{activeTab === 'archived' && campaign.actualGrowth ? campaign.actualGrowth : (campaign.growth || campaign.roi)}</p>
                      <p className="text-xs text-gray-500 mt-1">Expected ROI</p>
                    </div>
                  </div>
                )}

                {/* For active and archived tabs, show Expected ROI separately */}
                {(activeTab === 'active' || activeTab === 'archived') && (
                  <div className="flex items-start justify-end gap-4 mb-4">
                    <div className="flex flex-col items-end flex-shrink-0" style={{ minWidth: '100px' }}>
                      <p className="text-lg font-semibold text-gray-900">{activeTab === 'archived' && campaign.actualGrowth ? campaign.actualGrowth : (campaign.growth || campaign.roi)}</p>
                      <p className="text-xs text-gray-500 mt-1">Expected ROI</p>
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


                {activeTab === 'recommended' && (
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleActivate(campaign.id, campaign.name)}
                      className="flex-1 text-white flex items-center justify-center rounded-lg"
                      style={{ background: '#184464' }}
                    >
                      <span className="mr-2">Activate</span>
                      <img src="/arrow_logo.svg" alt="arrow" className="w-4 h-4" />
                    </Button>
                    <Button
                      onClick={() => handleArchive(campaign.id, campaign.name)}
                      className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 border-0 rounded-lg"
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
                      className="flex-1 text-white flex items-center justify-center rounded-lg"
                      style={{ background: '#184464' }}
                    >
                      <span className="mr-2">Activate</span>
                      <img src="/arrow_logo.svg" alt="arrow" className="w-4 h-4" />
                    </Button>
                  </div>
                )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Cockpit;
