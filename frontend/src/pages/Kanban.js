import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { formatNumber } from '@/utils/formatters';
import GoalFormModal from '@/components/GoalFormModal';
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
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';

const Kanban = () => {
  const { token } = useAuth();
  
  // Check if we need to navigate to a specific tab (from Cockpit insights)
  const initialTab = sessionStorage.getItem('kanbanActiveTab') || 'strategic-kanban';
  const [activeTab, setActiveTab] = useState(initialTab);
  
  // Clear the session storage after reading
  React.useEffect(() => {
    sessionStorage.removeItem('kanbanActiveTab');
  }, []);
  
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

  // Load corporate goals by department
  const loadCorporateGoals = async () => {
    if (!token || activeTab !== 'goals-management') return;
    
    const departments = ['sales', 'operations', 'finance', 'hr', 'marketing', 'technology'];
    
    try {
      const goalsByDept = {};
      for (const dept of departments) {
        const response = await axios.get(`${API}/goals/by-department/${dept}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        goalsByDept[dept] = response.data || [];
      }
      
      // Update corporate goals state with real data
      setCorporateGoals(prev => ({
        ...prev,
        departments: prev.departments.map(dept => ({
          ...dept,
          activeGoals: goalsByDept[dept.id]?.length || 0,
          goals: goalsByDept[dept.id] || []
        }))
      }));
    } catch (error) {
      console.error('Failed to load corporate goals:', error);
    }
  };

  // Load corporate goals when goals management tab is active
  useEffect(() => {
    if (activeTab === 'goals-management' && token) {
      loadCorporateGoals();
    }
  }, [activeTab, token]);

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

  // Goals Management Data
  const [goals, setGoals] = useState({
    quarters: [
      {
        id: 1,
        quarter: 'Q1 2026',
        period: 'Jan - Mar 2026',
        status: 'active',
        objectives: [
          {
            id: 1,
            title: 'Increase Customer Acquisition',
            description: 'Drive 30% growth in new customer acquisition through digital channels',
            owner: 'Marketing Team',
            progress: 72,
            status: 'on-track',
            targetValue: 5000,
            currentValue: 3600,
            metric: 'customers',
            keyResults: [
              { id: 1, description: 'Launch 3 new acquisition campaigns', progress: 100, target: 3, current: 3 },
              { id: 2, description: 'Achieve 15% conversion rate on landing pages', progress: 80, target: 15, current: 12 },
              { id: 3, description: 'Reduce CAC by 20%', progress: 45, target: 20, current: 9 }
            ]
          },
          {
            id: 2,
            title: 'Improve Customer Retention',
            description: 'Increase retention rate from 85% to 92% through engagement programs',
            owner: 'Customer Success',
            progress: 58,
            status: 'at-risk',
            targetValue: 92,
            currentValue: 88,
            metric: '% retention',
            keyResults: [
              { id: 1, description: 'Implement loyalty program with 50% enrollment', progress: 65, target: 50, current: 32.5 },
              { id: 2, description: 'Reduce churn rate to 8%', progress: 50, target: 8, current: 12 },
              { id: 3, description: 'Achieve NPS score of 70+', progress: 60, target: 70, current: 62 }
            ]
          },
          {
            id: 3,
            title: 'Expand Product Revenue',
            description: 'Grow product revenue by 40% through upselling and cross-selling',
            owner: 'Sales Team',
            progress: 85,
            status: 'on-track',
            targetValue: 8500000,
            currentValue: 7225000,
            metric: '$ revenue',
            keyResults: [
              { id: 1, description: 'Increase average order value by 25%', progress: 90, target: 25, current: 22.5 },
              { id: 2, description: 'Cross-sell to 40% of existing customers', progress: 82, target: 40, current: 33 },
              { id: 3, description: 'Launch 2 premium product tiers', progress: 100, target: 2, current: 2 }
            ]
          }
        ]
      },
      {
        id: 2,
        quarter: 'Q2 2026',
        period: 'Apr - Jun 2026',
        status: 'upcoming',
        objectives: [
          {
            id: 4,
            title: 'Launch International Expansion',
            description: 'Enter 3 new international markets with localized offerings',
            owner: 'Business Development',
            progress: 15,
            status: 'planning',
            targetValue: 3,
            currentValue: 0,
            metric: 'markets',
            keyResults: [
              { id: 1, description: 'Complete market research for 5 countries', progress: 60, target: 5, current: 3 },
              { id: 2, description: 'Establish partnerships in 3 markets', progress: 0, target: 3, current: 0 },
              { id: 3, description: 'Localize platform for 3 languages', progress: 0, target: 3, current: 0 }
            ]
          },
          {
            id: 5,
            title: 'Optimize Operational Efficiency',
            description: 'Reduce operational costs by 15% through automation',
            owner: 'Operations Team',
            progress: 8,
            status: 'planning',
            targetValue: 15,
            currentValue: 0,
            metric: '% reduction',
            keyResults: [
              { id: 1, description: 'Automate 50% of manual processes', progress: 10, target: 50, current: 5 },
              { id: 2, description: 'Reduce support ticket resolution time by 30%', progress: 5, target: 30, current: 1.5 },
              { id: 3, description: 'Implement AI-powered analytics', progress: 0, target: 1, current: 0 }
            ]
          }
        ]
      },
      {
        id: 3,
        quarter: 'Q3 2026',
        period: 'Jul - Sep 2026',
        status: 'upcoming',
        objectives: []
      },
      {
        id: 4,
        quarter: 'Q4 2026',
        period: 'Oct - Dec 2026',
        status: 'upcoming',
        objectives: []
      }
    ]
  });

  // Corporate Strategy Goals by Department
  const [corporateGoals, setCorporateGoals] = useState({
    departments: [
      {
        id: 'sales',
        name: 'Sales',
        icon: TrendingUp,
        color: { bg: '#d1fae5', text: '#065f46', icon: '#10b981', border: '#10b981' },
        activeGoals: 3,
        owner: 'Sarah Johnson',
        goals: [
          {
            id: 1,
            title: 'Increase Q1 2026 Revenue by 25%',
            description: 'Drive growth through new markets and product expansion. Focus on enterprise segment and strategic partnerships.',
            owner: 'Sarah Johnson',
            dependencies: ['Marketing Campaign Launch', 'Product Team Readiness', 'Sales Training Complete'],
            metrics: ['Monthly Recurring Revenue (MRR)', 'Customer Acquisition Cost (CAC)', 'Sales Cycle Length'],
            status: 'on-track',
            progress: 65,
            aiRecommendations: {
              owners: ['Sarah Johnson (VP Sales)', 'Mike Chen (Sales Director)'],
              dependencies: ['Q1 Marketing Campaign must complete by Jan 31', 'Sales training should be finished before Feb 1', 'New CRM integration required'],
              metrics: ['Track MRR growth rate weekly - target 8% month-over-month', 'Keep CAC under $150 per customer', 'Reduce sales cycle to 45 days or less', 'Monitor pipeline velocity and conversion rates']
            }
          }
        ]
      },
      {
        id: 'operations',
        name: 'Operations',
        icon: Target,
        color: { bg: '#dbeafe', text: '#1e3a8a', icon: '#3b82f6', border: '#3b82f6' },
        activeGoals: 2,
        owner: 'David Martinez',
        goals: [
          {
            id: 2,
            title: 'Reduce Operational Costs by 15%',
            description: 'Optimize processes, automate workflows, and eliminate inefficiencies across all operations.',
            owner: 'David Martinez',
            dependencies: ['Automation Tool Implementation', 'Process Documentation Complete'],
            metrics: ['Cost per Transaction', 'Process Efficiency Rate', 'Automation Coverage %'],
            status: 'on-track',
            progress: 48,
            aiRecommendations: {
              owners: ['David Martinez (COO)', 'Lisa Wang (Operations Manager)'],
              dependencies: ['Automation tools must be deployed by mid-Q1', 'All processes need documentation by Jan 15'],
              metrics: ['Reduce cost per transaction by 12%', 'Achieve 75% process efficiency', 'Automate 40% of manual tasks', 'Track monthly operational savings']
            }
          }
        ]
      },
      {
        id: 'finance',
        name: 'Finance',
        icon: Euro,
        color: { bg: '#fef3c7', text: '#92400e', icon: '#f59e0b', border: '#f59e0b' },
        activeGoals: 2,
        owner: 'Jennifer Lee',
        goals: [
          {
            id: 3,
            title: 'Improve Profitability Margin to 35%',
            description: 'Increase gross margin through pricing optimization and cost management strategies.',
            owner: 'Jennifer Lee',
            dependencies: ['Pricing Strategy Review', 'Cost Analysis Complete'],
            metrics: ['Gross Profit Margin', 'Operating Cash Flow', 'EBITDA'],
            status: 'at-risk',
            progress: 32,
            aiRecommendations: {
              owners: ['Jennifer Lee (CFO)', 'Robert Kim (Finance Director)'],
              dependencies: ['Pricing review must finish by Feb 1', 'Need cost reduction proposals from all departments'],
              metrics: ['Target 35% gross margin by Q1 end', 'Maintain positive cash flow monthly', 'Improve EBITDA by 20%', 'Reduce variable costs by 10%']
            }
          }
        ]
      },
      {
        id: 'hr',
        name: 'Human Resources',
        icon: UsersIcon,
        color: { bg: '#e0e7ff', text: '#3730a3', icon: '#6366f1', border: '#6366f1' },
        activeGoals: 3,
        owner: 'Patricia Rodriguez',
        goals: [
          {
            id: 4,
            title: 'Achieve 90% Employee Retention Rate',
            description: 'Enhance employee satisfaction, career development opportunities, and workplace culture.',
            owner: 'Patricia Rodriguez',
            dependencies: ['Employee Engagement Survey', 'Career Development Program Launch'],
            metrics: ['Employee Retention Rate', 'Employee Satisfaction Score', 'Time to Hire'],
            status: 'on-track',
            progress: 78,
            aiRecommendations: {
              owners: ['Patricia Rodriguez (CHRO)', 'Amanda Foster (HR Manager)'],
              dependencies: ['Complete engagement survey by Jan 20', 'Launch career program before Feb 1'],
              metrics: ['Maintain 90%+ retention rate', 'Achieve 4.5/5 satisfaction score', 'Reduce time-to-hire to 30 days', 'Complete 100% performance reviews on time']
            }
          }
        ]
      },
      {
        id: 'marketing',
        name: 'Marketing',
        icon: Sparkles,
        color: { bg: '#fce7f3', text: '#831843', icon: '#ec4899', border: '#ec4899' },
        activeGoals: 4,
        owner: 'Michael Chen',
        goals: [
          {
            id: 5,
            title: 'Generate 5000 Qualified Leads in Q1',
            description: 'Execute multi-channel marketing campaigns to drive lead generation and brand awareness.',
            owner: 'Michael Chen',
            dependencies: ['Content Calendar Approval', 'Ad Budget Allocation', 'Marketing Automation Setup'],
            metrics: ['Marketing Qualified Leads (MQL)', 'Cost Per Lead', 'Lead-to-Customer Conversion Rate'],
            status: 'on-track',
            progress: 55,
            aiRecommendations: {
              owners: ['Michael Chen (CMO)', 'Emily Davis (Marketing Director)'],
              dependencies: ['Finalize content calendar by Jan 10', 'Allocate Q1 ad budget ($250K)', 'Complete marketing automation setup'],
              metrics: ['Generate 5000 MQLs by March 31', 'Keep cost per lead under $50', 'Achieve 15% lead-to-customer conversion', 'Increase website traffic by 40%']
            }
          }
        ]
      },
      {
        id: 'technology',
        name: 'Technology',
        icon: Zap,
        color: { bg: '#fed7aa', text: '#7c2d12', icon: '#ea580c', border: '#ea580c' },
        activeGoals: 2,
        owner: 'Alex Thompson',
        goals: [
          {
            id: 6,
            title: 'Achieve 99.9% System Uptime',
            description: 'Ensure infrastructure reliability, implement redundancy, and optimize system performance.',
            owner: 'Alex Thompson',
            dependencies: ['Cloud Migration Complete', 'Monitoring System Upgrade'],
            metrics: ['System Uptime %', 'Mean Time to Recovery (MTTR)', 'Infrastructure Cost'],
            status: 'on-track',
            progress: 82,
            aiRecommendations: {
              owners: ['Alex Thompson (CTO)', 'Rachel Green (Engineering Manager)'],
              dependencies: ['Complete cloud migration by Jan 25', 'Upgrade monitoring by Feb 1'],
              metrics: ['Maintain 99.9% uptime continuously', 'Keep MTTR under 15 minutes', 'Reduce infrastructure costs by 10%', 'Zero critical security incidents']
            }
          }
        ]
      }
    ]
  });

  const [selectedDepartment, setSelectedDepartment] = useState(null);
  const [expandedGoals, setExpandedGoals] = useState({});

  const toggleGoalExpansion = (goalId) => {
    setExpandedGoals(prev => ({
      ...prev,
      [goalId]: !prev[goalId]
    }));
  };

  const [selectedQuarterId, setSelectedQuarterId] = useState(1);
  
  // Get the selected quarter from goals state
  const selectedQuarter = goals.quarters.find(q => q.id === selectedQuarterId) || goals.quarters[0];

  // Goal Modal State
  const [goalModalOpen, setGoalModalOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [goalType, setGoalType] = useState(null); // 'quarterly' or 'corporate'
  const [goalDepartment, setGoalDepartment] = useState(null); // For corporate goals

  // Load goals from localStorage on mount
  useEffect(() => {
    const savedGoals = localStorage.getItem('bizpulse_goals');
    const savedCorporateGoals = localStorage.getItem('bizpulse_corporate_goals');
    
    if (savedGoals) {
      try {
        const parsed = JSON.parse(savedGoals);
        setGoals(prev => ({ ...prev, quarters: parsed.quarters || prev.quarters }));
      } catch (e) {
        console.error('Failed to load saved goals:', e);
      }
    }
    
    if (savedCorporateGoals) {
      try {
        const parsed = JSON.parse(savedCorporateGoals);
        // Restore icon components after parsing from localStorage
        const iconMap = {
          'sales': TrendingUp,
          'operations': Target,
          'finance': Euro,
          'hr': UsersIcon,
          'marketing': Sparkles,
          'technology': Zap
        };
        
        const restoredDepartments = (parsed.departments || []).map(dept => ({
          ...dept,
          icon: iconMap[dept.id] || null
        }));
        
        setCorporateGoals(prev => ({ 
          ...prev, 
          departments: restoredDepartments.length > 0 ? restoredDepartments : prev.departments 
        }));
      } catch (e) {
        console.error('Failed to load saved corporate goals:', e);
      }
    }
  }, []);

  // Save goals to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('bizpulse_goals', JSON.stringify(goals));
  }, [goals]);

  useEffect(() => {
    // Save corporate goals but exclude icon functions (they can't be serialized)
    const goalsToSave = {
      ...corporateGoals,
      departments: corporateGoals.departments.map(dept => {
        const { icon, ...deptWithoutIcon } = dept;
        return deptWithoutIcon;
      })
    };
    localStorage.setItem('bizpulse_corporate_goals', JSON.stringify(goalsToSave));
  }, [corporateGoals]);

  const handleNewGoal = (type = 'quarterly', department = null) => {
    setGoalType(type);
    setGoalDepartment(department);
    setEditingGoal(null);
    setGoalModalOpen(true);
  };

  const handleEditGoal = (goal, type = 'quarterly', department = null) => {
    setGoalType(type);
    setGoalDepartment(department);
    setEditingGoal(goal);
    setGoalModalOpen(true);
  };

  const handleSaveGoal = (goalData, action) => {
    if (goalType === 'quarterly') {
      // Handle quarterly objectives
      if (action === 'create') {
        setGoals(prev => ({
          ...prev,
          quarters: prev.quarters.map(quarter => 
            quarter.id === selectedQuarterId
              ? { 
                  ...quarter, 
                  objectives: [...(quarter.objectives || []), goalData] 
                }
              : quarter
          )
        }));
        toast.success('Goal created successfully!');
      } else if (action === 'update') {
        setGoals(prev => ({
          ...prev,
          quarters: prev.quarters.map(quarter => 
            quarter.id === selectedQuarterId
              ? {
                  ...quarter,
                  objectives: (quarter.objectives || []).map(obj => 
                    obj.id === goalData.id ? goalData : obj
                  )
                }
              : quarter
          )
        }));
        toast.success('Goal updated successfully!');
      }
    } else if (goalType === 'corporate') {
      // Handle corporate goals
      const deptId = goalDepartment?.id || selectedDepartment?.id;
      if (!deptId) {
        toast.error('Department not found');
        return;
      }
      
      if (action === 'create') {
        setCorporateGoals(prev => ({
          ...prev,
          departments: prev.departments.map(dept => 
            dept.id === deptId
              ? { 
                  ...dept, 
                  goals: [...(dept.goals || []), goalData],
                  activeGoals: (dept.activeGoals || 0) + 1
                }
              : dept
          )
        }));
        toast.success('Corporate goal created successfully!');
      } else if (action === 'update') {
        setCorporateGoals(prev => ({
          ...prev,
          departments: prev.departments.map(dept => 
            dept.id === deptId
              ? {
                  ...dept,
                  goals: (dept.goals || []).map(g => g.id === goalData.id ? goalData : g)
                }
              : dept
          )
        }));
        toast.success('Corporate goal updated successfully!');
      }
    }
  };

  const handleDeleteGoal = (goalId, type = 'quarterly') => {
    if (window.confirm('Are you sure you want to delete this goal?')) {
      if (type === 'quarterly') {
        setGoals(prev => ({
          ...prev,
          quarters: prev.quarters.map(quarter => 
            quarter.id === selectedQuarterId
              ? {
                  ...quarter,
                  objectives: (quarter.objectives || []).filter(obj => obj.id !== goalId)
                }
              : quarter
          )
        }));
        toast.success('Goal deleted successfully!');
      } else if (type === 'corporate') {
        const deptId = goalDepartment?.id || selectedDepartment?.id;
        if (deptId) {
          setCorporateGoals(prev => ({
            ...prev,
            departments: prev.departments.map(dept => 
              dept.id === deptId
                ? {
                    ...dept,
                    goals: dept.goals.filter(g => g.id !== goalId),
                    activeGoals: Math.max(0, dept.activeGoals - 1)
                  }
                : dept
            )
          }));
          toast.success('Corporate goal deleted successfully!');
        }
      }
    }
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
              {activeTab === 'strategic-kanban' ? 'Strategic Kanban' : 'Goals Management'}
            </h1>
            <p className="text-gray-600 text-sm mt-1">
              {activeTab === 'strategic-kanban' 
                ? 'Manage strategic initiatives and marketing projects'
                : 'Track and manage organizational goals and OKRs'}
            </p>
          </div>
          {activeTab === 'strategic-kanban' ? (
            <Button
              className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white"
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
                  <Sparkles className="w-4 h-4 mr-2" />
                  Discover AI Insights
                </>
              )}
            </Button>
          ) : (
            <Button
              className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white"
              onClick={() => handleNewGoal('quarterly')}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Goal
            </Button>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="professional-card p-1">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab('strategic-kanban')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeTab === 'strategic-kanban'
                  ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Zap className="w-4 h-4" />
              Strategic Kanban
            </button>
            <button
              onClick={() => setActiveTab('goals-management')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeTab === 'goals-management'
                  ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Target className="w-4 h-4" />
              Goals Management
            </button>
          </div>
        </div>

        {/* Strategic Kanban Content */}
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
            {/* KPI Banner */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Annual Goal */}
          <div className="professional-card p-5 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-amber-600" />
              <p className="text-sm font-semibold text-gray-700">Annual Goal</p>
            </div>
            <div className="mb-2">
              <h2 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                {annualGoal.current}/{annualGoal.target}
              </h2>
              <p className="text-xs text-gray-600 mt-1">{annualGoal.metric} • {goalProgress.toFixed(0)}% complete</p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="h-2 rounded-full"
                style={{
                  width: `${goalProgress}%`,
                  background: 'linear-gradient(90deg, #d97706 0%, #f59e0b 100%)'
                }}
              />
            </div>
          </div>

          {/* Pending Recommendations */}
          <div className="professional-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              <p className="text-sm font-semibold text-gray-700">Pending Recommendations</p>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              {totalRecommended}
            </h2>
            <div className="flex gap-3 text-xs text-gray-600">
              <span>System: {systemRecommended}</span>
              <span>Custom: {customRecommended}</span>
            </div>
          </div>

          {/* Live Campaigns */}
          <div className="professional-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5 text-green-600" />
              <p className="text-sm font-semibold text-gray-700">Live Campaigns</p>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              {totalLive}
            </h2>
            <div className="flex gap-3 text-xs text-gray-600">
              <span>System: {systemLive}</span>
              <span>Custom: {customLive}</span>
            </div>
          </div>

          {/* Impact Delivered */}
          <div className="professional-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-purple-600" />
              <p className="text-sm font-semibold text-gray-700">Impact Delivered</p>
            </div>
            <h2 className="text-3xl font-bold text-green-600 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              {formatNumber(totalImpact)}
            </h2>
            <div className="flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 text-green-600" />
              <span className="text-green-600 font-semibold">{avgUplift.toFixed(1)}% avg uplift</span>
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recommended Column */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                  RECOMMENDED
                </h3>
                <span className="text-sm text-gray-500">({totalRecommended})</span>
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
                initiatives.recommended.map((initiative) => {
                const categoryInfo = getCategoryColor(initiative.category);
                const typeInfo = getTypeColor(initiative.type);
                const TypeIcon = typeInfo.icon;

                return (
                  <div key={initiative.id} className="professional-card p-5 hover:shadow-lg transition-shadow">
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
                      <div className="flex items-center gap-1 text-xs text-gray-500 ml-auto">
                        <Sparkles className="w-3 h-3 text-amber-600" />
                        <span className="font-semibold text-amber-600">{initiative.aiScore}% AI Score</span>
                      </div>
                    </div>

                    {/* Date & Budget */}
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div className="flex items-center gap-2 text-xs text-gray-600">
                        <Calendar className="w-4 h-4" />
                        <span>
                          {new Date(initiative.startDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          {initiative.endDate && ` - ${new Date(initiative.endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-600">
                        <Euro className="w-4 h-4" />
                        <span className="font-semibold text-gray-900">{formatNumber(initiative.budget)}</span>
                      </div>
                    </div>

                    {/* Expected Impact */}
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-3 mb-3 border border-green-200">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-green-700 font-semibold">Expected Impact</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-green-900">
                            {formatNumber(initiative.impact.value)}
                          </span>
                          <span className="text-xs text-green-700">• {initiative.impact.percentage}% uplift</span>
                        </div>
                      </div>
                    </div>

                    {/* Reasoning Section */}
                    {showReasoning === initiative.id && (
                      <div className="bg-blue-50 rounded-lg p-3 mb-3 border border-blue-200">
                        <div className="flex items-start gap-2">
                          <Zap className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="text-xs font-semibold text-blue-900 mb-1">AI Reasoning:</p>
                            <p className="text-xs text-blue-800 leading-relaxed">{initiative.reasoning}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Channels */}
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      {initiative.channels.map((channel, idx) => (
                        <span
                          key={`channel-${initiative.id}-${idx}-${channel}`}
                          className="px-2 py-1 rounded-md text-xs bg-gray-100 text-gray-700 flex items-center gap-1"
                        >
                          {channel === 'Email' && <Mail className="w-3 h-3" />}
                          {channel === 'Social Media' && <Share2 className="w-3 h-3" />}
                          {channel === 'Video' && <Video className="w-3 h-3" />}
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
                        className="flex-1 text-gray-700 border-gray-300"
                      >
                        <Zap className="w-4 h-4 mr-1" />
                        Reasoning
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleAccept(initiative)}
                        className="flex-1 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white"
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
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Live ({initiatives.live.length})
              </button>
              <button
                onClick={() => setActiveCampaignTab('past')}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition ${
                  activeCampaignTab === 'past'
                    ? 'bg-gradient-to-r from-gray-500 to-gray-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Past ({initiatives.past.length})
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
                  initiatives.live.map((initiative) => {
                const categoryInfo = getCategoryColor(initiative.category);
                const typeInfo = getTypeColor(initiative.type);
                const TypeIcon = typeInfo.icon;

                return (
                  <div key={initiative.id} className="professional-card p-5 hover:shadow-lg transition-shadow">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="text-base font-semibold text-gray-900 flex-1" style={{ fontFamily: 'Space Grotesk' }}>
                        {initiative.title}
                      </h4>
                      <button className="text-gray-400 hover:text-gray-600">
                        <MoreVertical className="w-5 h-5" />
                      </button>
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
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-3 mb-3 border border-green-200">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-green-700 font-semibold">Current Impact</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-green-900">
                            {formatNumber(initiative.impact?.value || 0)}
                          </span>
                          <span className="text-xs text-green-700">• {initiative.impact?.percentage || 0}%</span>
                        </div>
                      </div>
                    </div>

                    {/* Progress */}
                    {initiative.progress !== undefined && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs text-gray-600">Progress</span>
                          <span className="text-xs font-semibold text-gray-900">{initiative.progress || 0}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="h-2 rounded-full"
                            style={{
                              width: `${initiative.progress || 0}%`,
                              background: (initiative.progress || 0) >= 75 
                                ? 'linear-gradient(90deg, #10b981 0%, #059669 100%)'
                                : (initiative.progress || 0) >= 50
                                ? 'linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)'
                                : 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)'
                            }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Channels */}
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      {(initiative.channels || []).map((channel, idx) => (
                        <span
                          key={`channel-past-${initiative.id}-${idx}-${channel}`}
                          className="px-2 py-1 rounded-md text-xs bg-gray-100 text-gray-700 flex items-center gap-1"
                        >
                          {channel === 'Email' && <Mail className="w-3 h-3" />}
                          {channel === 'Push Notification' && <Zap className="w-3 h-3" />}
                          {channel === 'In-App' && <TagIcon className="w-3 h-3" />}
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
                        className="flex-1 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Create Goals
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
                        variant="outline"
                        size="sm"
                        className="flex-1 text-gray-700 border-gray-300"
                      >
                        {expandedCampaigns[initiative.id] ? (
                          <>
                            <ChevronUp className="w-4 h-4 mr-2" />
                            Hide Goals
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-4 h-4 mr-2" />
                            View Goals ({campaignGoals[initiative.id]?.length || 0})
                          </>
                        )}
                      </Button>
                    </div>

                    {/* Expanded Goals Section */}
                    {expandedCampaigns[initiative.id] && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <h5 className="text-sm font-semibold text-gray-900 mb-3">Campaign Goals</h5>
                        {campaignGoals[initiative.id]?.length > 0 ? (
                          <div className="space-y-3">
                            {campaignGoals[initiative.id].map((goal, goalIdx) => (
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
                  initiatives.past.map((initiative) => {
                    const categoryInfo = getCategoryColor(initiative.category);
                    const typeInfo = getTypeColor(initiative.type);
                    const TypeIcon = typeInfo.icon;

                    return (
                      <div key={`past-${initiative.id || initiative.title}`} className="professional-card p-5 hover:shadow-lg transition-shadow opacity-75">
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

        {/* Goals Management Content */}
        {activeTab === 'goals-management' && (
          <>
            {/* Quarter Selector */}
            <div className="flex gap-3 overflow-x-auto pb-2">
              {goals.quarters.map((quarter) => (
                <button
                  key={quarter.id}
                  onClick={() => setSelectedQuarterId(quarter.id)}
                  className={`px-6 py-3 rounded-lg font-semibold text-sm transition-all whitespace-nowrap ${
                    selectedQuarterId === quarter.id
                      ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md'
                      : 'bg-white text-gray-700 border border-gray-200 hover:border-amber-300'
                  }`}
                >
                  {quarter.quarter}
                  <span className="block text-xs mt-0.5 opacity-90">{quarter.period}</span>
                </button>
              ))}
            </div>

            {/* Goals Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="professional-card p-5">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  <p className="text-sm font-semibold text-gray-700">Total Objectives</p>
                </div>
                <h2 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                  {selectedQuarter.objectives.length}
                </h2>
                <p className="text-xs text-gray-600 mt-1">{selectedQuarter.quarter}</p>
              </div>

              <div className="professional-card p-5">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <p className="text-sm font-semibold text-gray-700">On Track</p>
                </div>
                <h2 className="text-3xl font-bold text-green-600" style={{ fontFamily: 'Space Grotesk' }}>
                  {selectedQuarter?.objectives?.filter(o => o.status === 'on-track').length || 0}
                </h2>
                <p className="text-xs text-gray-600 mt-1">Meeting targets</p>
              </div>

              <div className="professional-card p-5">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-5 h-5 text-amber-600" />
                  <p className="text-sm font-semibold text-gray-700">At Risk</p>
                </div>
                <h2 className="text-3xl font-bold text-amber-600" style={{ fontFamily: 'Space Grotesk' }}>
                  {selectedQuarter?.objectives?.filter(o => o.status === 'at-risk').length || 0}
                </h2>
                <p className="text-xs text-gray-600 mt-1">Needs attention</p>
              </div>

              <div className="professional-card p-5">
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                  <p className="text-sm font-semibold text-gray-700">Avg Progress</p>
                </div>
                <h2 className="text-3xl font-bold text-purple-600" style={{ fontFamily: 'Space Grotesk' }}>
                  {selectedQuarter?.objectives?.length > 0 
                    ? Math.round(selectedQuarter.objectives.reduce((sum, o) => sum + o.progress, 0) / selectedQuarter.objectives.length)
                    : 0}%
                </h2>
                <p className="text-xs text-gray-600 mt-1">Overall completion</p>
              </div>
            </div>

            {/* Corporate Strategy Goals Section */}
            <div className="mt-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                Corporate Strategy Goals
              </h2>
              <p className="text-gray-600 mb-6">Manage department-level strategic goals and track progress</p>
              
              {/* Department Cards Grid */}
              {!selectedDepartment && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {corporateGoals.departments.map((dept) => {
                    const DeptIcon = dept.icon;
                    return (
                      <div
                        key={dept.id}
                        onClick={() => setSelectedDepartment(dept)}
                        className="professional-card p-6 cursor-pointer transition-all duration-300 hover:shadow-xl hover:scale-105 border-l-4"
                        style={{ borderLeftColor: dept.color.border }}
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div
                            className="w-14 h-14 rounded-lg flex items-center justify-center"
                            style={{ background: dept.color.bg }}
                          >
                            <DeptIcon className="w-7 h-7" style={{ color: dept.color.icon }} />
                          </div>
                          <ArrowUpRight className="w-5 h-5 text-gray-400 group-hover:text-amber-600" />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                          {dept.name}
                        </h3>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Active Goals</span>
                            <span className="font-semibold text-gray-900">{dept.activeGoals}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Owner</span>
                            <span className="font-semibold text-gray-900">{dept.owner}</span>
                          </div>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <span className="text-xs text-gray-500">Click to view goals →</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Department Goals View */}
              {selectedDepartment && (
                <div className="space-y-4">
                  {/* Back Button and New Goal */}
                  <div className="flex items-center justify-between mb-4">
                    <button
                      onClick={() => setSelectedDepartment(null)}
                      className="flex items-center gap-2 text-gray-600 hover:text-amber-600 transition-colors"
                    >
                      <ChevronLeft className="w-5 h-5" />
                      Back to Departments
                    </button>
                    <Button
                      size="sm"
                      className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white"
                      onClick={() => handleNewGoal('corporate', selectedDepartment)}
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      New Goal
                    </Button>
                  </div>

                  {/* Department Header */}
                  <div className="professional-card p-6 border-l-4" style={{ borderLeftColor: selectedDepartment.color.border }}>
                    <div className="flex items-center gap-4">
                      <div
                        className="w-16 h-16 rounded-lg flex items-center justify-center"
                        style={{ background: selectedDepartment.color.bg }}
                      >
                        {(() => {
                          const IconComponent = selectedDepartment.icon;
                          if (!IconComponent || typeof IconComponent !== 'function') return null;
                          return <IconComponent className="w-8 h-8" style={{ color: selectedDepartment.color.icon }} />;
                        })()}
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                          {selectedDepartment.name} Goals
                        </h2>
                        <p className="text-sm text-gray-600">Owner: {selectedDepartment.owner}</p>
                      </div>
                    </div>
                  </div>

                  {/* Goals List */}
                  {selectedDepartment.goals.map((goal, goalIdx) => (
                    <div
                      key={goal.id || `dept-goal-${selectedDepartment.id}-${goalIdx}`}
                      className="professional-card p-6 border-l-4"
                      style={{ borderLeftColor: selectedDepartment.color.border }}
                    >
                      {/* Goal Header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                              {goal.title}
                            </h3>
                            <span
                              className="px-3 py-1 rounded-full text-xs font-semibold"
                              style={{
                                background: goal.status === 'on-track' ? '#d1fae5' : '#fef3c7',
                                color: goal.status === 'on-track' ? '#065f46' : '#92400e'
                              }}
                            >
                              {goal.status.replace('-', ' ')}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{goal.description}</p>
                        </div>
                        <button
                          onClick={() => toggleGoalExpansion(goal.id)}
                          className="ml-4 text-gray-400 hover:text-amber-600 transition-colors"
                        >
                          {expandedGoals[goal.id] ? <ChevronUp className="w-6 h-6" /> : <ChevronDown className="w-6 h-6" />}
                        </button>
                      </div>

                      {/* Progress Bar */}
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-semibold text-gray-700">Overall Progress</span>
                          <span className="text-sm font-bold text-gray-900">{goal.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className="h-3 rounded-full transition-all"
                            style={{
                              width: `${goal.progress}%`,
                              background: goal.progress >= 75
                                ? 'linear-gradient(90deg, #10b981 0%, #059669 100%)'
                                : goal.progress >= 50
                                ? 'linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)'
                                : 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)'
                            }}
                          />
                        </div>
                      </div>

                      {/* Expandable Details */}
                      {expandedGoals[goal.id] && (
                        <div className="space-y-6 mt-6 pt-6 border-t border-gray-200">
                          {/* Assigned Owner */}
                          <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                              <UsersIcon className="w-4 h-4" />
                              Assigned Owner
                            </label>
                            <div className="flex items-center gap-2">
                              <input
                                type="text"
                                value={goal.owner}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                                readOnly
                              />
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-gray-700 border-gray-300"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>

                          {/* Dependencies */}
                          <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                              <Package className="w-4 h-4" />
                              Dependencies
                            </label>
                            <div className="space-y-2">
                              {goal.dependencies.map((dep, idx) => (
                                <div key={`dep-${goal.id}-${idx}`} className="flex items-center gap-2 bg-gray-50 rounded-lg p-3">
                                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                                  <span className="text-sm text-gray-900 flex-1">{dep}</span>
                                  <button className="text-red-500 hover:text-red-700">
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </div>
                              ))}
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full text-gray-700 border-gray-300 border-dashed"
                              >
                                <Plus className="w-4 h-4 mr-2" />
                                Add Dependency
                              </Button>
                            </div>
                          </div>

                          {/* Metrics to Achieve */}
                          <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                              <BarChart3 className="w-4 h-4" />
                              Metrics to Achieve
                            </label>
                            <div className="space-y-2">
                              {goal.metrics.map((metric, idx) => (
                                <div key={`member-${goal.id}-${idx}`} className="flex items-center gap-2 bg-blue-50 rounded-lg p-3">
                                  <Target className="w-4 h-4 text-blue-600 flex-shrink-0" />
                                  <span className="text-sm text-gray-900 flex-1">{metric}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* AI Recommendations */}
                          <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg p-5 border-2 border-amber-200">
                            <div className="flex items-center gap-2 mb-4">
                              <Sparkles className="w-5 h-5 text-amber-600" />
                              <h4 className="text-base font-semibold text-amber-900">AI Recommendations</h4>
                            </div>

                            {/* Recommended Owners */}
                            <div className="mb-4">
                              <h5 className="text-sm font-semibold text-amber-800 mb-2">Recommended Owners</h5>
                              <div className="space-y-1">
                                {goal.aiRecommendations?.owners?.map((owner, idx) => (
                                  <div key={`owner-rec-${goal.id}-${idx}`} className="flex items-center gap-2 text-sm text-amber-900">
                                    <Zap className="w-3 h-3 text-amber-600" />
                                    <span>{owner}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Suggested Dependencies */}
                            <div className="mb-4">
                              <h5 className="text-sm font-semibold text-amber-800 mb-2">Suggested Dependencies</h5>
                              <div className="space-y-1">
                                {goal.aiRecommendations?.dependencies?.map((dep, idx) => (
                                  <div key={`dep-rec-${goal.id}-${idx}`} className="flex items-center gap-2 text-sm text-amber-900">
                                    <Zap className="w-3 h-3 text-amber-600" />
                                    <span>{dep}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Recommended Metrics */}
                            <div>
                              <h5 className="text-sm font-semibold text-amber-800 mb-2">How to Achieve This Goal</h5>
                              <div className="space-y-1">
                                {goal.aiRecommendations?.metrics?.map((metric, idx) => (
                                  <div key={`metric-rec-${goal.id}-${idx}`} className="flex items-start gap-2 text-sm text-amber-900">
                                    <Zap className="w-3 h-3 text-amber-600 flex-shrink-0 mt-0.5" />
                                    <span>{metric}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="flex gap-3">
                            <Button
                              className="flex-1 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white"
                              onClick={() => handleEditGoal(goal, 'corporate', selectedDepartment)}
                            >
                              <Edit className="w-4 h-4 mr-2" />
                              Edit Goal
                            </Button>
                            <Button
                              variant="outline"
                              className="text-gray-700 border-gray-300"
                              onClick={() => handleDeleteGoal(goal.id, 'corporate')}
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quarterly Objectives Section */}
            <div className="mt-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                Quarterly Objectives & Key Results
              </h2>
              <p className="text-gray-600 mb-6">Track progress on strategic objectives and their key results for {selectedQuarter?.quarter || 'Selected Quarter'}</p>
              
              {/* Objectives List */}
              <div className="space-y-6">
              {(selectedQuarter?.objectives || []).map((objective) => {
                const statusColors = {
                  'on-track': { bg: '#d1fae5', text: '#059669', border: '#10b981' },
                  'at-risk': { bg: '#fef3c7', text: '#d97706', border: '#f59e0b' },
                  'delayed': { bg: '#fee2e2', text: '#dc2626', border: '#ef4444' },
                  'planning': { bg: '#e0e7ff', text: '#4f46e5', border: '#6366f1' }
                };
                const statusInfo = statusColors[objective.status];

                return (
                  <div 
                    key={objective.id} 
                    className="professional-card p-6 border-l-4"
                    style={{ borderLeftColor: statusInfo.border }}
                  >
                    {/* Objective Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                            {objective.title}
                          </h3>
                          <span 
                            className="px-3 py-1 rounded-full text-xs font-semibold"
                            style={{ background: statusInfo.bg, color: statusInfo.text }}
                          >
                            {objective.status.replace('-', ' ')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{objective.description}</p>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-1">
                            <UsersIcon className="w-4 h-4 text-gray-500" />
                            <span className="text-gray-700">{objective.owner}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Flag className="w-4 h-4 text-gray-500" />
                            <span className="font-semibold text-gray-900">
                              {objective.currentValue} / {objective.targetValue} {objective.metric}
                            </span>
                          </div>
                        </div>
                      </div>
                      <button className="text-gray-400 hover:text-gray-600">
                        <MoreVertical className="w-5 h-5" />
                      </button>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-gray-700">Overall Progress</span>
                        <span className="text-sm font-bold text-gray-900">{objective.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className="h-3 rounded-full transition-all"
                          style={{
                            width: `${objective.progress}%`,
                            background: objective.progress >= 75 
                              ? 'linear-gradient(90deg, #10b981 0%, #059669 100%)'
                              : objective.progress >= 50
                              ? 'linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)'
                              : 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)'
                          }}
                        />
                      </div>
                    </div>

                    {/* Key Results */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                        <Award className="w-4 h-4" />
                        Key Results ({objective.keyResults.length})
                      </h4>
                      <div className="space-y-3">
                        {objective.keyResults.map((kr, krIdx) => (
                          <div key={kr.id || `kr-${objective.id}-${krIdx}`} className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-start justify-between mb-2">
                              <p className="text-sm text-gray-900 flex-1">{kr.description}</p>
                              <span className="text-sm font-semibold text-gray-900 ml-4">{kr.progress}%</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="flex-1">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className="h-2 rounded-full"
                                    style={{
                                      width: `${kr.progress}%`,
                                      background: kr.progress >= 75 
                                        ? 'linear-gradient(90deg, #10b981 0%, #059669 100%)'
                                        : kr.progress >= 50
                                        ? 'linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)'
                                        : 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)'
                                    }}
                                  />
                                </div>
                              </div>
                              <span className="text-xs text-gray-600 whitespace-nowrap">
                                {kr.current} / {kr.target}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2 mt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-gray-700 border-gray-300"
                        onClick={() => handleEditGoal(objective, 'quarterly')}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 border-red-300"
                        onClick={() => handleDeleteGoal(objective.id, 'quarterly')}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          </>
        )}

        {/* Goal Form Modal */}
        <GoalFormModal
          isOpen={goalModalOpen}
          onClose={() => {
            setGoalModalOpen(false);
            setEditingGoal(null);
            setGoalType(null);
            setGoalDepartment(null);
          }}
          goal={editingGoal}
          quarter={selectedQuarter}
          onSave={handleSaveGoal}
        />
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
