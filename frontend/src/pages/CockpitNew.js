import React, { useState, useEffect, useMemo } from 'react';
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
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Skeleton } from '@/components/ui/skeleton';

const Cockpit = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('recommended');
  const [loadingActionItems, setLoadingActionItems] = useState(true);

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
  const [actionItems, setActionItems] = useState({
    critical: [],
    impact: []
  });
  
  // Fetch action items from API
  useEffect(() => {
    let isMounted = true;
    const fetchActionItems = async () => {
      if (!token) return;
      
      try {
        setLoadingActionItems(true);
        const response = await axios.get(`${API}/cockpit/action-items`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (isMounted && response.data) {
          setActionItems({
            critical: response.data.critical || [],
            impact: response.data.impact || []
          });
        }
      } catch (error) {
        if (!isMounted) return;
        
        // Only log 404 errors, don't show toast for missing data
        if (error.response?.status === 404) {
          console.log('No action items found in database. Using empty state.');
          setActionItems({
            critical: [],
            impact: []
          });
        } else {
          console.error('Failed to fetch action items:', error);
          // Only show toast for non-404 errors
          toast.error('Failed to load action items.');
          setActionItems({
            critical: [],
            impact: []
          });
        }
      } finally {
        if (isMounted) {
          setLoadingActionItems(false);
        }
      }
    };
    
    fetchActionItems();
    
    return () => {
      isMounted = false;
    };
  }, [token]);
  
  const getFilteredItems = (items, priorityFilter) => {
    if (priorityFilter === 'all') return items;
    return items.filter(item => item.priority === priorityFilter);
  };

  // Skeleton loader component for action items
  const ActionItemSkeleton = () => (
    <div className="flex items-center justify-between p-4 border-b border-gray-200">
      <div className="flex items-center gap-3 flex-1">
        <Skeleton className="w-4 h-4" />
        <div className="flex-1">
          <Skeleton className="h-4 w-3/4 mb-2" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <Skeleton className="h-6 w-16 rounded" />
    </div>
  );

  // Campaign data - fetch from API
  const [campaigns, setCampaigns] = useState({
    recommended: [],
    active: [],
    archived: []
  });
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);

  // Fetch campaigns from API
  useEffect(() => {
    let isMounted = true;
    const fetchCampaigns = async () => {
      if (!token) return;
      
      try {
        setLoadingCampaigns(true);
        const response = await axios.get(`${API}/kanban/recommendations`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (isMounted && response.data) {
          // Map API response to frontend format
          const mapCampaign = (campaign, index) => {
            // Calculate ROI from impact data
            let roiPercentage = '0%';
            if (campaign.impact) {
              if (typeof campaign.impact.percentage === 'number' && campaign.impact.percentage > 0) {
                roiPercentage = `${Math.round(campaign.impact.percentage)}%`;
              } else if (campaign.impact.value && campaign.budget && campaign.budget > 0) {
                // Calculate ROI from value and budget: (value / budget) * 100
                const calculatedROI = (campaign.impact.value / campaign.budget) * 100;
                if (calculatedROI > 0) {
                  roiPercentage = `${Math.round(calculatedROI)}%`;
                }
              } else if (campaign.impact.expectedROI) {
                roiPercentage = `${Math.round(campaign.impact.expectedROI * 100)}%`;
              }
            }
            
            return {
              id: campaign.id || index,
              name: campaign.title || 'Untitled Campaign',
              description: campaign.description || '',
              aiScore: campaign.aiScore || 0,
              budget: campaign.budget ? `€${(campaign.budget / 1000).toFixed(0)}K` : '€0K',
              growth: roiPercentage,
              channels: campaign.channels || [],
              aiRecommendation: campaign.reasoning || campaign.impact?.recommendation || 'No recommendation available',
              startDate: campaign.startDate,
              endDate: campaign.endDate,
              status: campaign.status || 'recommended'
            };
          };
          
          setCampaigns({
            recommended: (response.data.recommended || []).map(mapCampaign),
            active: (response.data.live || []).map(mapCampaign),
            archived: (response.data.past || []).map(mapCampaign)
          });
        }
      } catch (error) {
        if (!isMounted) return;
        console.error('Failed to fetch campaigns:', error);
        // Keep empty arrays on error
        setCampaigns({
          recommended: [],
          active: [],
          archived: []
        });
      } finally {
        if (isMounted) {
          setLoadingCampaigns(false);
        }
      }
    };
    
    fetchCampaigns();
    
    return () => {
      isMounted = false;
    };
  }, [token]);

  // Memoize current campaigns based on activeTab to ensure proper filtering
  const currentCampaigns = useMemo(() => {
    if (activeTab === 'recommended') {
      return campaigns.recommended || [];
    } else if (activeTab === 'active') {
      return campaigns.active || [];
    } else if (activeTab === 'archived') {
      return campaigns.archived || [];
    }
    return [];
  }, [activeTab, campaigns.recommended, campaigns.active, campaigns.archived]);

  // Refetch campaigns after any change
  const refetchCampaigns = async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${API}/kanban/recommendations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data) {
        const mapCampaign = (campaign, index) => {
          // Calculate ROI from impact data
          let roiPercentage = '0%';
          if (campaign.impact) {
            if (typeof campaign.impact.percentage === 'number' && campaign.impact.percentage > 0) {
              roiPercentage = `${Math.round(campaign.impact.percentage)}%`;
            } else if (campaign.impact.value && campaign.budget && campaign.budget > 0) {
              const calculatedROI = (campaign.impact.value / campaign.budget) * 100;
              if (calculatedROI > 0) {
                roiPercentage = `${Math.round(calculatedROI)}%`;
              }
            } else if (campaign.impact.expectedROI) {
              roiPercentage = `${Math.round(campaign.impact.expectedROI * 100)}%`;
            }
          }
          
          return {
            id: campaign.id || index,
            name: campaign.title || 'Untitled Campaign',
            description: campaign.description || '',
            aiScore: campaign.aiScore || 0,
            budget: campaign.budget ? `€${(campaign.budget / 1000).toFixed(0)}K` : '€0K',
            growth: roiPercentage,
            channels: campaign.channels || [],
            aiRecommendation: campaign.reasoning || campaign.impact?.recommendation || 'No recommendation available',
            startDate: campaign.startDate,
            endDate: campaign.endDate,
            status: campaign.status || 'recommended'
          };
        };
        
        setCampaigns({
          recommended: (response.data.recommended || []).map(mapCampaign),
          active: (response.data.live || []).map(mapCampaign),
          archived: (response.data.past || []).map(mapCampaign)
        });
      }
    } catch (error) {
      console.error('Failed to refetch campaigns:', error);
      toast.error('Failed to refresh campaigns');
    }
  };

  const handleActivate = async (campaignId, campaignName, fromTab = 'recommended') => {
    try {
      // If from archived, use move-to-live endpoint
      if (fromTab === 'archived') {
        await axios.post(`${API}/kanban/move-to-live`, 
          { campaignId: campaignId, fromCollection: 'past' },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } else {
        // Call backend API to move campaign from recommended to live
        await axios.post(`${API}/kanban/accept`, 
          { campaignId: campaignId, fromCollection: 'recommended' },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      
      toast.success(`Campaign "${campaignName}" activated successfully!`);
      // Refetch campaigns to get updated state
      await refetchCampaigns();
    } catch (error) {
      console.error('Failed to activate campaign:', error);
      toast.error(`Failed to activate campaign: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeactivate = async (campaignId, campaignName) => {
    try {
      // Move campaign from live to past (archive)
      await axios.post(`${API}/kanban/archive`, 
        { campaignId: campaignId, fromCollection: 'live' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Campaign "${campaignName}" deactivated and archived successfully!`);
      // Refetch campaigns to get updated state
      await refetchCampaigns();
    } catch (error) {
      console.error('Failed to deactivate campaign:', error);
      toast.error(`Failed to deactivate campaign: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleArchive = async (campaignId, campaignName, fromTab = 'recommended') => {
    try {
      // Move campaign to archived (past)
      const fromCollection = fromTab === 'active' ? 'live' : 'recommended';
      await axios.post(`${API}/kanban/archive`, 
        { campaignId: campaignId, fromCollection: fromCollection },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Campaign "${campaignName}" archived successfully!`);
      // Refetch campaigns to get updated state
      await refetchCampaigns();
    } catch (error) {
      console.error('Failed to archive campaign:', error);
      toast.error(`Failed to archive campaign: ${error.response?.data?.detail || error.message}`);
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
                {loadingActionItems ? (
                  <>
                    <ActionItemSkeleton />
                    <ActionItemSkeleton />
                    <ActionItemSkeleton />
                    <ActionItemSkeleton />
                    <ActionItemSkeleton />
                  </>
                ) : getFilteredItems(actionItems.critical, criticalPriorityFilter).length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <p className="text-sm">No critical action items found</p>
                  </div>
                ) : (
                  getFilteredItems(actionItems.critical, criticalPriorityFilter).map((item, idx, arr) => (
                  <div
                    key={`critical-${item.id}-${idx}`}
                    className={`flex items-center justify-between p-4 ${
                      idx !== arr.length - 1 ? 'border-b border-gray-200' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <div>
                        <h4 className="font-medium text-gray-900 text-sm">{item.title}</h4>
                        <p className="text-xs text-gray-500">Due: {new Date(item.dueDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
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
                  ))
                )}
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
                {loadingActionItems ? (
                  <>
                    <ActionItemSkeleton />
                    <ActionItemSkeleton />
                    <ActionItemSkeleton />
                    <ActionItemSkeleton />
                    <ActionItemSkeleton />
                  </>
                ) : getFilteredItems(actionItems.impact, impactPriorityFilter).length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <p className="text-sm">No impact action items found</p>
                  </div>
                ) : (
                  getFilteredItems(actionItems.impact, impactPriorityFilter).map((item, idx, arr) => (
                  <div
                    key={`impact-${item.id}-${idx}`}
                    className={`flex items-center justify-between p-4 ${
                      idx !== arr.length - 1 ? 'border-b border-gray-200' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <div>
                        <h4 className="font-medium text-gray-900 text-sm">{item.title}</h4>
                        <p className="text-xs text-gray-500">Due: {new Date(item.dueDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
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
                  ))
                )}
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
          <div key={activeTab} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {loadingCampaigns ? (
              // Skeleton loaders for campaigns
              Array.from({ length: 6 }).map((_, idx) => (
                <div key={idx} className="rounded-[10px] border border-gray-200 p-6 bg-gray-50">
                  <Skeleton className="h-6 w-3/4 mb-2" />
                  <Skeleton className="h-4 w-full mb-4" />
                  <Skeleton className="h-8 w-16 mb-4" />
                  <Skeleton className="h-20 w-full mb-4" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ))
            ) : currentCampaigns.length === 0 ? (
              <div className="col-span-2 p-8 text-center text-gray-500">
                <p className="text-sm">No {activeTab} campaigns found</p>
              </div>
            ) : (
              currentCampaigns.map((campaign) => (
                <div 
                  key={`${activeTab}-${campaign.id}`} 
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
                    <div className="flex flex-wrap items-center gap-2">
                      {campaign.channels.map((channel, idx) => (
                        <span 
                          key={idx} 
                          className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded"
                        >
                          {channel}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Budget on Right */}
                  <div className="flex flex-col items-end flex-shrink-0" style={{ minWidth: '100px' }}>
                    <p className="text-lg font-semibold text-gray-900">{campaign.budget}</p>
                    <p className="text-xs text-gray-500 mt-1">Budget</p>
                  </div>
                </div>

                {/* Row 2: AI Recommendation and Expected ROI - Show for all tabs */}
                {campaign.aiRecommendation && (
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
                      <p className="text-lg font-semibold text-gray-900">
                        {campaign.growth && campaign.growth !== '0%' ? campaign.growth : 'N/A'}
                      </p>
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
              ))
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Cockpit;
