import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { formatNumber } from '@/utils/formatters';
import CreateGoalsModal from '@/components/CreateGoalsModal';
import GoalDetailModal from '@/components/GoalDetailModal';
import axios from 'axios';
import { API, useAuth } from '@/App';
import {
  Plus,
  Calendar,
  Euro,
  TrendingUp,
  Target,
  Sparkles,
  MoreVertical,
  Users as UsersIcon,
  Zap,
  CheckCircle,
  Clock,
  Mail,
  Share2,
  Video,
  Tag as TagIcon,
  Award,
  Flag,
  BarChart3,
  ArrowUpRight,
  Edit,
  Trash2,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  Package,
  Archive,
  AlertCircle,
  Layers,
  Eye,
  RefreshCw,
  MapPin
} from 'lucide-react';
import ChartComponent from '@/components/ChartComponent';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';

const Kanban = () => {
  const { token } = useAuth();
  
  const [activeTab, setActiveTab] = useState('strategic-kanban');
  
  const [initiatives, setInitiatives] = useState({
    recommended: [],
    live: [],
    past: []
  });
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [generatingRecommendations, setGeneratingRecommendations] = useState(false);
  const [activeCampaignTab, setActiveCampaignTab] = useState('live'); // 'live' or 'past'
  const [showReasoning, setShowReasoning] = useState(null);
  const [annualGoal, setAnnualGoal] = useState({
    current: 0,
    target: 100,
    metric: '% Activated Customers',
    progress: 0
  });
  const [expandedCampaigns, setExpandedCampaigns] = useState({});
  const [campaignGoals, setCampaignGoals] = useState({});
  const [createGoalsModalOpen, setCreateGoalsModalOpen] = useState(false);
  const [selectedCampaignForGoals, setSelectedCampaignForGoals] = useState(null);
  const [goalDetailModalOpen, setGoalDetailModalOpen] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState(null);

  // Load recommendations from MongoDB (does not generate new ones)
  useEffect(() => {
    const loadRecommendations = async () => {
      if (!token || activeTab !== 'strategic-kanban') {
        return;
      }

      try {
        setLoadingRecommendations(true);
        const response = await axios.get(`${API}/kanban/recommendations`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data) {
          setInitiatives({
            recommended: response.data.recommended || [],
            live: response.data.live || [],
            past: response.data.past || []
          });
        }
      } catch (error) {
        console.error('Failed to load recommendations:', error);
        toast.error('Failed to load recommendations from database.');
      } finally {
        setLoadingRecommendations(false);
      }
    };

    loadRecommendations();
  }, [token, activeTab]);

  // Load goals for all live campaigns when they're available
  useEffect(() => {
    if (!token || activeTab !== 'strategic-kanban' || !initiatives.live || initiatives.live.length === 0) {
      return;
    }

    const loadAllCampaignGoals = async () => {
      for (const campaign of initiatives.live) {
        if (campaign.id) {
          try {
            const response = await axios.get(`${API}/kanban/campaigns/${campaign.id}/goals`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            setCampaignGoals(prev => ({
              ...prev,
              [campaign.id]: response.data || []
            }));
          } catch (error) {
            console.error(`Failed to load goals for campaign ${campaign.id}:`, error);
            setCampaignGoals(prev => ({
              ...prev,
              [campaign.id]: []
            }));
          }
        }
      }
    };

    loadAllCampaignGoals();
  }, [token, activeTab, initiatives.live]);

  // Load annual goal data
  useEffect(() => {
    const loadAnnualGoal = async () => {
      if (!token || activeTab !== 'strategic-kanban') {
        return;
      }

      try {
        const response = await axios.get(`${API}/kanban/annual-goal`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data) {
          setAnnualGoal({
            current: response.data.current || 0,
            target: response.data.target || 100,
            metric: response.data.metric || '% Activated Customers',
            progress: response.data.progress || 0
          });
        }
      } catch (error) {
        console.error('Failed to load annual goal:', error);
        // Keep default values on error
      }
    };

    loadAnnualGoal();
  }, [token, activeTab]);

  // Load goals for a specific campaign
  const loadCampaignGoals = async (campaignId) => {
    if (!token) return;
    try {
      const response = await axios.get(`${API}/kanban/campaigns/${campaignId}/goals`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCampaignGoals(prev => ({
        ...prev,
        [campaignId]: response.data || []
      }));
    } catch (error) {
      console.error('Failed to load campaign goals:', error);
      setCampaignGoals(prev => ({
        ...prev,
        [campaignId]: []
      }));
    }
  };

  const handleGoalsCreated = () => {
    // Reload goals for the selected campaign
    if (selectedCampaignForGoals) {
      loadCampaignGoals(selectedCampaignForGoals.id);
    }
    // Reload corporate goals to update counts
    loadCorporateGoals();
  };

  // Load corporate goals by department (kept for compatibility with campaign goals)
  const loadCorporateGoals = async () => {
    // No-op: Goals Management moved to Projects page
  };

  // Generate new AI recommendations
  const handleGenerateRecommendations = async () => {
    if (!token) {
      toast.error('Please login to generate recommendations');
      return;
    }

    try {
      setGeneratingRecommendations(true);
      const response = await axios.get(`${API}/analytics/strategic-recommendations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data) {
        setInitiatives({
          recommended: response.data.recommended || [],
          live: response.data.live || initiatives.live,
          past: response.data.past || initiatives.past
        });
        toast.success(`Generated ${response.data.recommended.length} new AI recommendations!`);
      }
    } catch (error) {
      console.error('Failed to generate recommendations:', error);
      toast.error('Failed to generate recommendations. Please try again.');
    } finally {
      setGeneratingRecommendations(false);
    }
  };

  // Accept a campaign (move from recommended to live)
  const handleAccept = async (initiative) => {
    if (!token) {
      toast.error('Please login to accept campaigns');
      return;
    }

    try {
      const response = await axios.post(
        `${API}/kanban/accept`,
        {
          campaignId: initiative.id,
          fromCollection: 'recommended'
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        // Remove from recommended and add to live
        setInitiatives(prev => ({
          ...prev,
          recommended: prev.recommended.filter(rec => rec.id !== initiative.id),
          live: [...prev.live, { ...initiative, status: 'live', acceptedAt: new Date().toISOString() }]
        }));
        toast.success(`Campaign "${initiative.title}" moved to Live!`);
      }
    } catch (error) {
      console.error('Failed to accept campaign:', error);
      toast.error('Failed to accept campaign. Please try again.');
    }
  };

  // Marketing Strategy Data (moved from RootCauseAnalysis.js)
  const [selectedCampaign, setSelectedCampaign] = useState('Overall');
  const marketingStrategyModules = [
    {
      id: 1,
      title: 'Strategic Framework',
      description: 'Define your marketing strategy framework',
      icon: Target,
      status: 'active',
      color: { bg: '#dbeafe', icon: '#2563eb' }
    },
    {
      id: 2,
      title: 'Channel Strategy',
      description: 'Optimize your marketing channel mix',
      icon: Layers,
      status: 'active',
      color: { bg: '#d1fae5', icon: '#059669' }
    },
    {
      id: 3,
      title: 'Budget Allocation',
      description: 'Strategic budget planning and allocation',
      icon: Euro,
      status: 'active',
      color: { bg: '#fef3c7', icon: '#d97706' }
    },
    {
      id: 4,
      title: 'Market Segmentation',
      description: 'Define and refine your target segments',
      icon: UsersIcon,
      status: 'active',
      color: { bg: '#e0e7ff', icon: '#4f46e5' }
    },
    {
      id: 5,
      title: 'Brand Positioning',
      description: 'Develop and maintain brand positioning',
      icon: Award,
      status: 'active',
      color: { bg: '#fce7f3', icon: '#9f1239' }
    },
    {
      id: 6,
      title: 'Competitive Strategy',
      description: 'Strategic response to competitive landscape',
      icon: Zap,
      status: 'active',
      color: { bg: '#fed7aa', icon: '#ea580c' }
    }
  ];

  const aiInsights = [
    {
      id: 1,
      title: 'Signup Drop-off Spike',
      priority: 'critical',
      description: 'AI-generated marketing insight based on campaign performance data',
      details: '42% increase in form abandonment at step 3 detected. Users are leaving at the payment information field, indicating potential security concerns or complex checkout process.',
      color: { bg: '#fee2e2', text: '#991b1b', label: 'Critical' }
    },
    {
      id: 2,
      title: 'Weekend Engagement Window',
      priority: 'medium',
      description: 'AI-generated marketing insight based on campaign performance data',
      details: 'Email engagement increases by 68% on weekends between 10AM-2PM. Consider scheduling high-priority campaigns during this window for maximum impact.',
      color: { bg: '#fef3c7', text: '#92400e', label: 'Medium' }
    },
    {
      id: 3,
      title: 'Mobile Traffic Surge',
      priority: 'high',
      description: 'AI-generated marketing insight based on campaign performance data',
      details: 'Mobile traffic increased 85% but conversion rate is 23% lower than desktop. Mobile UX optimization recommended to capitalize on increased traffic.',
      color: { bg: '#fed7aa', text: '#9a3412', label: 'High' }
    }
  ];

  const roasData = {
    labels: ['Apr 22', 'Apr 25', 'Apr 28', 'May 1', 'May 4', 'May 7', 'May 10', 'May 13', 'May 16', 'May 19', 'May 22', 'May 25', 'May 28', 'Jun 1', 'Jun 4', 'Jun 7', 'Jun 10', 'Jun 13', 'Jun 16', 'Jun 19', 'Jun 22', 'Jun 25', 'Jun 28', 'Jul 1', 'Jul 4', 'Jul 7', 'Jul 10', 'Jul 13'],
    values: [3.2, 4.1, 2.8, 3.5, 4.5, 3.9, 2.9, 4.2, 3.7, 4.8, 3.4, 2.6, 3.8, 4.3, 3.1, 4.6, 3.5, 2.9, 4.1, 3.6, 4.4, 3.2, 3.9, 4.7, 3.3, 4.0, 3.8, 4.2]
  };

  const emailOpenRateData = {
    labels: ['Apr 22', 'Apr 25', 'Apr 28', 'May 1', 'May 4', 'May 7', 'May 10', 'May 13', 'May 16', 'May 19', 'May 22', 'May 25', 'May 28', 'Jun 1', 'Jun 4', 'Jun 7', 'Jun 10', 'Jun 13', 'Jun 16', 'Jun 19', 'Jun 22', 'Jun 25', 'Jun 28', 'Jul 1', 'Jul 4', 'Jul 7', 'Jul 10', 'Jul 13'],
    values: [0.22, 0.21, 0.28, 0.23, 0.22, 0.24, 0.23, 0.22, 0.21, 0.25, 0.23, 0.22, 0.24, 0.23, 0.22, 0.21, 0.24, 0.23, 0.22, 0.23, 0.22, 0.24, 0.23, 0.25, 0.24, 0.23, 0.22, 0.24]
  };

  const clickThroughRateData = {
    labels: ['Apr 22', 'Apr 25', 'Apr 28', 'May 1', 'May 4', 'May 7', 'May 10', 'May 13', 'May 16', 'May 19', 'May 22', 'May 25', 'May 28', 'Jun 1', 'Jun 4', 'Jun 7', 'Jun 10', 'Jun 13', 'Jun 16', 'Jun 19', 'Jun 22', 'Jun 25', 'Jun 28', 'Jul 1', 'Jul 4', 'Jul 7', 'Jul 10', 'Jul 13'],
    values: [0.042, 0.038, 0.051, 0.044, 0.039, 0.048, 0.043, 0.040, 0.037, 0.049, 0.044, 0.038, 0.047, 0.043, 0.039, 0.036, 0.048, 0.044, 0.040, 0.045, 0.041, 0.049, 0.043, 0.050, 0.046, 0.043, 0.039, 0.047]
  };

  const conversionRateData = {
    labels: ['Apr 22', 'Apr 25', 'Apr 28', 'May 1', 'May 4', 'May 7', 'May 10', 'May 13', 'May 16', 'May 19', 'May 22', 'May 25', 'May 28', 'Jun 1', 'Jun 4', 'Jun 7', 'Jun 10', 'Jun 13', 'Jun 16', 'Jun 19', 'Jun 22', 'Jun 25', 'Jun 28', 'Jul 1', 'Jul 4', 'Jul 7', 'Jul 10', 'Jul 13'],
    values: [0.028, 0.025, 0.035, 0.030, 0.026, 0.033, 0.029, 0.027, 0.024, 0.034, 0.030, 0.025, 0.032, 0.029, 0.026, 0.023, 0.033, 0.030, 0.027, 0.031, 0.028, 0.034, 0.029, 0.035, 0.032, 0.029, 0.026, 0.033]
  };

  // Calculate KPIs
  const totalRecommended = initiatives.recommended.length;
  const totalLive = initiatives.live.length;
  const systemRecommended = initiatives.recommended.filter(i => i.type === 'system').length;
  const customRecommended = initiatives.recommended.filter(i => i.type === 'custom').length;
  const systemLive = initiatives.live.filter(i => i.type === 'system').length;
  const customLive = initiatives.live.filter(i => i.type === 'custom').length;
  
  const totalImpact = initiatives.live.reduce((sum, i) => sum + (i.impact?.value || 0), 0);
  const avgUplift = initiatives.live.length > 0 
    ? initiatives.live.reduce((sum, i) => sum + (i.impact?.percentage || 0), 0) / initiatives.live.length 
    : 0;
  
  const goalProgress = annualGoal.target > 0 ? (annualGoal.current / annualGoal.target) * 100 : 0;

  const getCategoryColor = (category) => {
    switch (category) {
      case 'acquisition': return { bg: '#dbeafe', text: '#1e40af', label: 'Acquisition' };
      case 'retention': return { bg: '#d1fae5', text: '#059669', label: 'Retention' };
      case 'engagement': return { bg: '#fef3c7', text: '#d97706', label: 'Engagement' };
      default: return { bg: '#f3f4f6', text: '#6b7280', label: category };
    }
  };

  const getTypeColor = (type) => {
    return type === 'system' 
      ? { bg: '#e0e7ff', text: '#4f46e5', icon: Sparkles }
      : { bg: '#fce7f3', text: '#9f1239', icon: UsersIcon };
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
              Revenue Sentinel
            </h1>
            <p className="text-gray-600 text-sm mt-1">
              Manage strategic initiatives and marketing projects
            </p>
          </div>
          <Button
            className="text-white"
            style={{ background: '#184464' }}
            onClick={handleGenerateRecommendations}
            disabled={generatingRecommendations}
          >
            {generatingRecommendations ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Generating...
              </>
            ) : (
              <>
                <img src="/discover_ai_insights_icon.svg" alt="AI Insights" className="w-4 h-4 mr-2" />
                Discover AI Insights
              </>
            )}
          </Button>
        </div>

        {/* Tab Navigation */}
        <div className="professional-card p-1">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab('strategic-kanban')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeTab === 'strategic-kanban'
                  ? 'text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
              style={activeTab === 'strategic-kanban' ? { background: '#184464' } : {}}
            >
              <Zap className="w-4 h-4" />
              Revenue Sentinel
            </button>
            <button
              onClick={() => setActiveTab('marketing-strategy')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeTab === 'marketing-strategy'
                  ? 'text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
              style={activeTab === 'marketing-strategy' ? { background: '#184464' } : {}}
            >
              <Target className="w-4 h-4" />
              Marketing Strategy
            </button>
          </div>
        </div>

        {/* Revenue Sentinel Content */}
        {activeTab === 'strategic-kanban' && (
          <>
            {loadingRecommendations ? (
              <>
                {/* Header Skeleton */}
                <div className="mb-6">
                  <Skeleton className="h-8 w-64 mb-2" />
                  <Skeleton className="h-4 w-96" />
                </div>

                {/* KPI Banner Skeleton */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="professional-card p-5">
                      <div className="flex items-center gap-2 mb-2">
                        <Skeleton className="w-5 h-5 rounded" />
                        <Skeleton className="h-4 w-32" />
                      </div>
                      <Skeleton className="h-10 w-24 mb-2" />
                      <Skeleton className="h-3 w-full mb-2" />
                      <Skeleton className="h-2 w-full rounded-full" />
                    </div>
                  ))}
                </div>

                {/* Kanban Board Skeleton */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {['Recommended', 'Live'].map((column, colIdx) => (
                    <div key={colIdx} className="space-y-4">
                      <div className="flex items-center gap-2">
                        <Skeleton className="w-3 h-3 rounded-full" />
                        <Skeleton className="h-6 w-32" />
                        <Skeleton className="h-4 w-12" />
                      </div>
                      <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="professional-card p-5">
                            <div className="mb-3">
                              <Skeleton className="h-6 w-3/4 mb-2" />
                              <Skeleton className="h-4 w-full mb-1" />
                              <Skeleton className="h-4 w-5/6" />
                            </div>
                            <div className="flex items-center gap-2 mb-3">
                              <Skeleton className="h-6 w-20 rounded-full" />
                              <Skeleton className="h-6 w-24 rounded-full" />
                              <Skeleton className="h-6 w-24 rounded-full ml-auto" />
                            </div>
                            <div className="grid grid-cols-2 gap-3 mb-3">
                              <Skeleton className="h-4 w-full" />
                              <Skeleton className="h-4 w-full" />
                            </div>
                            <Skeleton className="h-16 w-full rounded-lg mb-3" />
                            <div className="flex gap-2">
                              <Skeleton className="h-9 flex-1 rounded" />
                              <Skeleton className="h-9 flex-1 rounded" />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
            {/* KPI Banner - Dark Background Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Annual Goal */}
          <div 
            className="rounded-lg p-5 text-white relative overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex-1">
                <h2 className="text-3xl font-bold mb-1" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                  {annualGoal.current}/{annualGoal.target}
                </h2>
                <p className="text-sm text-white opacity-90 mb-2">Annual Goal</p>
                <p className="text-xs text-white opacity-75">{annualGoal.metric}</p>
                <p className="text-xs text-white opacity-75">{goalProgress.toFixed(0)}% Complete</p>
              </div>
              <div className="w-2 h-20 rounded-full relative overflow-hidden" style={{ background: 'rgba(237, 213, 177, 0.2)' }}>
                <div
                  className="absolute bottom-0 w-full rounded-full"
                  style={{
                    height: `${goalProgress}%`,
                    background: '#EDD5B1'
                  }}
                />
              </div>
            </div>
          </div>

          {/* Pending Recommendations */}
          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {totalRecommended}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Pending Recommendation</p>
              <div className="flex flex-col gap-1 text-xs text-white opacity-75">
                <span>System: {systemRecommended}</span>
                <span>Custom: {customRecommended}</span>
              </div>
            </div>
          </div>

          {/* Live Campaigns */}
          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {totalLive}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Live Campaigns</p>
              <div className="flex flex-col gap-1 text-xs text-white opacity-75">
                <span>System: {systemLive}</span>
                <span>Custom: {customLive}</span>
              </div>
            </div>
          </div>

          {/* Impact Delivered */}
          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {formatNumber(totalImpact)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Impact Delivered</p>
              <p className="text-xs text-white opacity-75">{avgUplift.toFixed(1)}% Avg Uplift</p>
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recommended Column */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                  Recommended [{totalRecommended}]
                </h3>
              </div>
            </div>

            <div className="space-y-4 max-h-[800px] overflow-y-auto pr-2">
              {initiatives.recommended.length === 0 ? (
                <div className="professional-card p-5">
                  <div className="text-center py-8">
                    <p className="text-gray-600">No recommendations available. Please check your data connection.</p>
                  </div>
                </div>
              ) : (
                initiatives.recommended.map((initiative, idx) => {
                const categoryInfo = getCategoryColor(initiative.category);
                const typeInfo = getTypeColor(initiative.type);
                const TypeIcon = typeInfo.icon;

                return (
                  <div 
                    key={`recommendation-${initiative.id || idx}`} 
                    className="rounded-[10px] border border-gray-200 p-5 hover:shadow-lg transition-shadow"
                    style={{
                      background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                      border: '1px solid rgba(0, 0, 0, 0.1)'
                    }}
                  >
                    {/* Header */}
                    <div className="mb-3">
                      <h4 className="text-base font-semibold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                        {initiative.title}
                      </h4>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {initiative.description}
                      </p>
                    </div>

                    {/* Tags */}
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      <span className="px-2 py-1 rounded text-xs font-semibold bg-blue-100 text-blue-700">
                        System
                      </span>
                      <span className="px-2 py-1 rounded text-xs font-semibold bg-gray-100 text-gray-700">
                        {categoryInfo.label}
                      </span>
                    </div>

                    {/* Date Range */}
                    <div className="mb-3">
                      <p className="text-xs text-gray-500">
                        {new Date(initiative.startDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                        {initiative.endDate && ` - ${new Date(initiative.endDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}`}
                      </p>
                    </div>

                    {/* Expected Impact and AI Score */}
                    <div 
                      className="rounded-lg p-4 mb-3"
                      style={{ background: '#F2E9DB' }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-xs text-gray-500 mb-1">Expected Impact</p>
                          <p className="text-xl font-bold text-gray-900 mb-1" style={{ fontFamily: 'Space Grotesk' }}>
                            {formatNumber(initiative.impact?.value || 0)}
                          </p>
                          <p className="text-xs text-green-600 font-semibold">
                            {initiative.impact?.percentage || 0}% Uplift
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                            {initiative.aiScore}%
                          </p>
                          <p className="text-xs text-gray-500">AI Score</p>
                        </div>
                      </div>
                    </div>

                    {/* Reasoning Section */}
                    {showReasoning === initiative.id && (
                      <div className="bg-blue-50 rounded-lg p-4 mt-3 border border-blue-200">
                        <p className="text-sm font-semibold text-gray-900 mb-2">AI Reasoning</p>
                        <p className="text-sm text-gray-700 leading-relaxed">{initiative.reasoning}</p>
                      </div>
                    )}

                    {/* Channels - Labels */}
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      {initiative.channels.map((channel, idx) => (
                        <span
                          key={`channel-${initiative.id}-${idx}-${channel}`}
                          className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-700"
                        >
                          {channel}
                        </span>
                      ))}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowReasoning(showReasoning === initiative.id ? null : initiative.id)}
                        className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 border-gray-300"
                      >
                        <Sparkles className="w-4 h-4 mr-1" />
                        Reasoning
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleAccept(initiative)}
                        className="flex-1 text-white"
                        style={{ background: '#184464' }}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Accept
                      </Button>
                    </div>
                  </div>
                );
              })
              )}
            </div>
          </div>

          {/* Live/Past Campaigns Column */}
          <div className="space-y-4">
            {/* Tabs for Live/Past */}
            <div className="flex items-center gap-2 mb-4">
              <button
                onClick={() => setActiveCampaignTab('live')}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition ${
                  activeCampaignTab === 'live'
                    ? 'text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                style={activeCampaignTab === 'live' ? { background: '#184464' } : {}}
              >
                Live [{initiatives.live.length}]
              </button>
              <button
                onClick={() => setActiveCampaignTab('past')}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition ${
                  activeCampaignTab === 'past'
                    ? 'text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                style={activeCampaignTab === 'past' ? { background: '#184464' } : {}}
              >
                Past [{initiatives.past.length}]
              </button>
            </div>

            <div className="space-y-4 max-h-[800px] overflow-y-auto pr-2">
              {activeCampaignTab === 'live' ? (
                initiatives.live.length === 0 ? (
                  <div className="professional-card p-5">
                    <div className="text-center py-8">
                      <p className="text-gray-600">No live campaigns. Accept recommendations to add them here.</p>
                    </div>
                  </div>
                ) : (
                  initiatives.live.map((initiative, idx) => {
                const categoryInfo = getCategoryColor(initiative.category);
                const typeInfo = getTypeColor(initiative.type);
                const TypeIcon = typeInfo.icon;

                return (
                  <div 
                    key={`live-${initiative.id || idx}`} 
                    className="rounded-[10px] border border-gray-200 p-5 hover:shadow-lg transition-shadow"
                    style={{
                      background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                      border: '1px solid rgba(0, 0, 0, 0.1)'
                    }}
                  >
                    {/* Header */}
                    <div className="mb-3">
                      <h4 className="text-base font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                        {initiative.title}
                      </h4>
                    </div>

                    {/* Tags - System and Category */}
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      <span className="px-2 py-1 rounded text-xs font-semibold bg-blue-100 text-blue-700">
                        System
                      </span>
                      <span className="px-2 py-1 rounded text-xs font-semibold bg-gray-100 text-gray-700">
                        {categoryInfo.label}
                      </span>
                    </div>

                    {/* Date */}
                    <div className="mb-3">
                      <p className="text-xs text-gray-500">
                        {new Date(initiative.startDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </p>
                    </div>

                    {/* Current Impact */}
                    <div 
                      className="rounded-lg p-4 mb-3"
                      style={{ background: '#F2E9DB' }}
                    >
                      <p className="text-xs text-gray-500 mb-1">Current Impact</p>
                      <div className="flex items-center justify-between">
                        <p className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                          {formatNumber(initiative.impact?.value || 0)}
                        </p>
                        <p className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                          {initiative.impact?.percentage || 0}%
                        </p>
                      </div>
                    </div>


                    {/* Channels - Labels */}
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      {(initiative.channels || []).map((channel, idx) => (
                        <span
                          key={`channel-live-${initiative.id}-${idx}-${channel}`}
                          className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-700"
                        >
                          {channel}
                        </span>
                      ))}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          setSelectedCampaignForGoals(initiative);
                          setCreateGoalsModalOpen(true);
                        }}
                        size="sm"
                        variant="outline"
                        className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 border-gray-300 flex items-center justify-between"
                      >
                        <span>Create Goal</span>
                        <img src="/plus_logo.svg" alt="plus" className="w-4 h-4" />
                      </Button>
                      <Button
                        onClick={() => {
                          const isExpanded = expandedCampaigns[initiative.id];
                          setExpandedCampaigns(prev => ({
                            ...prev,
                            [initiative.id]: !isExpanded
                          }));
                          // Load goals if expanding
                          if (!isExpanded) {
                            loadCampaignGoals(initiative.id);
                          }
                        }}
                        size="sm"
                        className="flex-1 text-white"
                        style={{ background: '#184464' }}
                      >
                        <ChevronDown className="w-4 h-4 mr-2" />
                        View Goal
                      </Button>
                    </div>

                    {/* Expanded Goals Section */}
                    {expandedCampaigns[initiative.id] && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <h5 className="text-sm font-semibold text-gray-900 mb-3">Campaign Goals</h5>
                        {campaignGoals[initiative.id]?.length > 0 ? (
                          <div className="space-y-3">
                            {campaignGoals[initiative.id].slice(-5).map((goal, goalIdx) => (
                              <div
                                key={goal.id || `goal-${initiative.id}-${goalIdx}`}
                                onClick={() => {
                                  setSelectedGoal(goal);
                                  setGoalDetailModalOpen(true);
                                }}
                                className="p-3 bg-gray-50 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-100 hover:border-indigo-300 transition"
                              >
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <h6 className="font-semibold text-gray-900 text-sm">{goal.title}</h6>
                                    <p className="text-xs text-gray-600 mt-1 line-clamp-2">{goal.description}</p>
                                    <div className="flex items-center gap-3 mt-2 flex-wrap">
                                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                                        {goal.department}
                                      </span>
                                      <span className="text-xs text-gray-500">
                                        {goal.status === 'on-track' ? '✓ On Track' : goal.status === 'at-risk' ? '⚠ At Risk' : goal.status === 'completed' ? '✓ Completed' : '○ Not Started'}
                                      </span>
                                      <span className="text-xs text-gray-500">{goal.progress}%</span>
                                      {goal.owners?.length > 0 && (
                                        <span className="text-xs text-gray-500">{goal.owners.length} owner{goal.owners.length !== 1 ? 's' : ''}</span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-4 text-sm text-gray-500">
                            No goals created yet. Click "Create Goals" to get started.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
                  })
                )
              ) : (
                // Past Campaigns
                initiatives.past.length === 0 ? (
                  <div className="professional-card p-5">
                    <div className="text-center py-8">
                      <p className="text-gray-600">No past campaigns yet. Expired live campaigns will appear here.</p>
                    </div>
                  </div>
                ) : (
                  initiatives.past.map((initiative, idx) => {
                    const categoryInfo = getCategoryColor(initiative.category);
                    const typeInfo = getTypeColor(initiative.type);
                    const TypeIcon = typeInfo.icon;

                    return (
                      <div 
                        key={`past-${initiative.id || `past-${initiative.title}-${idx}`}`} 
                        className="rounded-[10px] border border-gray-200 p-5 hover:shadow-lg transition-shadow opacity-75"
                        style={{
                          background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                          border: '1px solid rgba(0, 0, 0, 0.1)'
                        }}
                      >
                        {/* Header */}
                        <div className="flex items-start justify-between mb-3">
                          <h4 className="text-base font-semibold text-gray-900 flex-1" style={{ fontFamily: 'Space Grotesk' }}>
                            {initiative.title}
                          </h4>
                          <div className="px-2 py-1 rounded text-xs bg-gray-200 text-gray-600">
                            Expired
                          </div>
                        </div>

                        {/* Tags */}
                        <div className="flex items-center gap-2 mb-3 flex-wrap">
                          <div
                            className="px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1"
                            style={{ background: typeInfo.bg, color: typeInfo.text }}
                          >
                            <TypeIcon className="w-3 h-3" />
                            {initiative.type}
                          </div>
                          <div
                            className="px-3 py-1 rounded-full text-xs font-semibold"
                            style={{ background: categoryInfo.bg, color: categoryInfo.text }}
                          >
                            {categoryInfo.label}
                          </div>
                        </div>

                        {/* Date */}
                        <div className="flex items-center gap-2 text-xs text-gray-600 mb-3">
                          <Calendar className="w-4 h-4" />
                          <span>
                            {new Date(initiative.startDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                            {initiative.endDate ? ` - ${new Date(initiative.endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}` : ' - None'}
                          </span>
                        </div>

                        {/* Impact */}
                        <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-3 mb-3 border border-gray-200">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-700 font-semibold">Final Impact</span>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-bold text-gray-900">
                                {formatNumber(initiative.impact?.value || 0)}
                              </span>
                              <span className="text-xs text-gray-700">• {initiative.impact?.percentage || 0}%</span>
                            </div>
                          </div>
                        </div>

                        {/* Channels */}
                        <div className="flex items-center gap-2 mb-3 flex-wrap">
                          {(initiative.channels || []).map((channel, idx) => (
                            <span
                              key={`past-channel-${initiative.id}-${idx}`}
                              className="px-2 py-1 rounded-md text-xs bg-gray-100 text-gray-700 flex items-center gap-1"
                            >
                              {channel === 'Email' && <Mail className="w-3 h-3" />}
                              {channel === 'Social Media' && <Share2 className="w-3 h-3" />}
                              {channel === 'Video' && <Video className="w-3 h-3" />}
                              {channel}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  })
                )
              )}
            </div>
          </div>
        </div>
              </>
            )}
          </>
        )}

        {/* Marketing Strategy Content */}
        {activeTab === 'marketing-strategy' && (
          <>
            {/* Strategy Modules Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {marketingStrategyModules.map((module) => {
                const ModuleIcon = module.icon;
                return (
                  <div 
                    key={module.id} 
                    className="professional-card p-6 hover:shadow-lg transition-all cursor-pointer"
                  >
                    <div 
                      className="w-14 h-14 rounded-lg flex items-center justify-center mb-4"
                      style={{ background: module.color.bg }}
                    >
                      <ModuleIcon className="w-7 h-7" style={{ color: module.color.icon }} />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                      {module.title}
                    </h3>
                    <p className="text-sm text-gray-600 mb-4">{module.description}</p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full text-gray-700 border-gray-300"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Configure
                    </Button>
                  </div>
                );
              })}
            </div>

            {/* AI Insights Section */}
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'Space Grotesk' }}>
                Marketing AI Insights & Recommendations
              </h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {aiInsights.map((insight) => (
                  <div key={insight.id} className="professional-card p-5">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-base font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                        {insight.title}
                      </h3>
                      <span 
                        className="px-3 py-1 rounded-full text-xs font-semibold"
                        style={{ background: insight.color.bg, color: insight.color.text }}
                      >
                        {insight.color.label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">{insight.description}</p>
                    <div className="bg-blue-50 rounded-lg p-3 mb-3 border border-blue-200">
                      <p className="text-xs text-blue-800">{insight.details}</p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full text-blue-600 border-blue-300"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Charts */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                  Performance Metrics
                </h2>
                <div className="flex items-center gap-3">
                  <select
                    value={selectedCampaign}
                    onChange={(e) => setSelectedCampaign(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                  >
                    <option value="Overall">Overall</option>
                    <option value="Campaign 1">Campaign 1</option>
                    <option value="Campaign 2">Campaign 2</option>
                    <option value="Campaign 3">Campaign 3</option>
                  </select>
                  <button className="p-2 text-gray-600 hover:text-amber-600 transition">
                    <RefreshCw className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Return on Ad Spend */}
                <div className="professional-card p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                      Return on Ad Spend (ROAS)
                    </h3>
                  </div>
                  <ChartComponent
                    type="line"
                    data={{
                      labels: roasData.labels,
                      datasets: [{
                        label: 'ROAS',
                        data: roasData.values,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          callbacks: {
                            label: (context) => `ROAS: ${context.parsed.y.toFixed(2)}`
                          }
                        }
                      },
                      scales: {
                        x: {
                          title: { display: true, text: 'Date' }
                        },
                        y: {
                          beginAtZero: true,
                          max: 8,
                          title: { display: true, text: 'ROAS' },
                          ticks: {
                            callback: (value) => value.toFixed(1)
                          }
                        }
                      }
                    }}
                    height={300}
                  />
                </div>

                {/* Email Open Rate */}
                <div className="professional-card p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                      Email Open Rate
                    </h3>
                  </div>
                  <ChartComponent
                    type="line"
                    data={{
                      labels: emailOpenRateData.labels,
                      datasets: [{
                        label: 'Open Rate',
                        data: emailOpenRateData.values,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 0.3,
                          ticks: {
                            callback: (value) => (value * 100).toFixed(0) + '%'
                          }
                        }
                      }
                    }}
                    height={300}
                  />
                </div>

                {/* Click-Through Rate */}
                <div className="professional-card p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                      Click-Through Rate (CTR)
                    </h3>
                  </div>
                  <ChartComponent
                    type="bar"
                    data={{
                      labels: clickThroughRateData.labels,
                      datasets: [{
                        label: 'CTR',
                        data: clickThroughRateData.values,
                        backgroundColor: '#f59e0b',
                        borderRadius: 4
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 0.06,
                          ticks: {
                            callback: (value) => (value * 100).toFixed(1) + '%'
                          }
                        }
                      }
                    }}
                    height={300}
                  />
                </div>

                {/* Conversion Rate */}
                <div className="professional-card p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                      Conversion Rate
                    </h3>
                  </div>
                  <ChartComponent
                    type="line"
                    data={{
                      labels: conversionRateData.labels,
                      datasets: [{
                        label: 'Conversion Rate',
                        data: conversionRateData.values,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 0.04,
                          ticks: {
                            callback: (value) => (value * 100).toFixed(1) + '%'
                          }
                        }
                      }
                    }}
                    height={300}
                  />
                </div>
              </div>
            </div>
          </>
        )}
        <CreateGoalsModal
          isOpen={createGoalsModalOpen}
          onClose={() => {
            setCreateGoalsModalOpen(false);
            setSelectedCampaignForGoals(null);
          }}
          campaign={selectedCampaignForGoals}
          onGoalsCreated={handleGoalsCreated}
        />
        <GoalDetailModal
          isOpen={goalDetailModalOpen}
          onClose={() => {
            setGoalDetailModalOpen(false);
            setSelectedGoal(null);
          }}
          goal={selectedGoal}
          onUpdate={() => {
            // Reload goals after update
            if (selectedGoal?.campaignId) {
              loadCampaignGoals(selectedGoal.campaignId);
            }
            loadCorporateGoals();
          }}
        />
      </div>
    </Layout>
  );
};

export default Kanban;
