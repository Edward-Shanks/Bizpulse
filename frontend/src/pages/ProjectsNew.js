import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import ChartComponent from '@/components/ChartComponent';
import InsightModal from '@/components/InsightModal';
import { formatNumber } from '@/utils/formatters';
import staticData from '@/data/staticData';
import { Button } from '@/components/ui/button';
import { 
  FolderKanban, Plus, CheckCircle2, Clock, AlertCircle, AlertTriangle,
  Sparkles, Calendar, Users, Target, TrendingUp, Euro, Package,
  BarChart3, Lightbulb, Zap, Activity, ArrowUpRight, CheckCircle,
  Flag, Award, Edit, Trash2, ChevronDown, ChevronUp, ChevronLeft,
  MoreVertical
} from 'lucide-react';
import GoalFormModal from '@/components/GoalFormModal';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { toast } from 'sonner';

const ProjectsNew = () => {
  const { token } = useAuth();
  const [activeSection, setActiveSection] = useState('top-projects');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [insightModal, setInsightModal] = useState({ isOpen: false, chartTitle: '' });
  
  // Goals Management state (moved to top to follow Rules of Hooks)
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
        icon: Users,
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
  const [selectedQuarterId, setSelectedQuarterId] = useState(1);
  const [goalModalOpen, setGoalModalOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [goalType, setGoalType] = useState(null);
  const [goalDepartment, setGoalDepartment] = useState(null);

  // Check if we need to navigate to a specific tab (from Cockpit insights)
  React.useEffect(() => {
    const initialTab = sessionStorage.getItem('projectsActiveTab');
    if (initialTab === 'goals-management') {
      setActiveSection('goals-management');
      sessionStorage.removeItem('projectsActiveTab');
    }
  }, []);

  useEffect(() => {
    // Load static data
    try {
      if (staticData && staticData.projectsData) {
        setData(staticData.projectsData);
      } else {
        console.error('Projects data not found in staticData');
        setData({ topProjects: [], businessPlans: [], campaigns: [] });
      }
    } catch (error) {
      console.error('Error loading projects data:', error);
      setData({ topProjects: [], businessPlans: [], campaigns: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeSection === 'goals-management' && token) {
      const loadCorporateGoalsAsync = async () => {
        const departments = ['sales', 'operations', 'finance', 'hr', 'marketing', 'technology'];
        
        try {
          const goalsByDept = {};
          for (const dept of departments) {
            const response = await axios.get(`${API}/goals/by-department/${dept}`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            goalsByDept[dept] = response.data || [];
          }
          
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
      loadCorporateGoalsAsync();
    }
  }, [activeSection, token]);

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
        const iconMap = {
          'sales': TrendingUp,
          'operations': Target,
          'finance': Euro,
          'hr': Users,
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

  useEffect(() => {
    localStorage.setItem('bizpulse_goals', JSON.stringify(goals));
  }, [goals]);

  useEffect(() => {
    const goalsToSave = {
      ...corporateGoals,
      departments: corporateGoals.departments.map(dept => {
        const { icon, ...deptWithoutIcon } = dept;
        return deptWithoutIcon;
      })
    };
    localStorage.setItem('bizpulse_corporate_goals', JSON.stringify(goalsToSave));
  }, [corporateGoals]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading projects...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-600">No data available</p>
        </div>
      </Layout>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return { bg: '#d1fae5', text: '#059669', icon: CheckCircle2 };
      case 'on-track': return { bg: '#dbeafe', text: '#2563eb', icon: Clock };
      case 'at-risk': return { bg: '#fef3c7', text: '#d97706', icon: AlertCircle };
      case 'delayed': return { bg: '#fee2e2', text: '#dc2626', icon: AlertTriangle };
      case 'active': return { bg: '#d1fae5', text: '#059669', icon: Activity };
      case 'planning': return { bg: '#e0e7ff', text: '#4f46e5', icon: Lightbulb };
      default: return { bg: '#f3f4f6', text: '#6b7280', icon: Clock };
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return { bg: '#fee2e2', text: '#dc2626' };
      case 'high': return { bg: '#fed7aa', text: '#ea580c' };
      case 'medium': return { bg: '#fef3c7', text: '#d97706' };
      case 'low': return { bg: '#dbeafe', text: '#2563eb' };
      default: return { bg: '#f3f4f6', text: '#6b7280' };
    }
  };

  // ============ TOP PROJECTS SECTION ============
  const TopProjectsSection = () => {
    const projects = data.topProjects || [];
    
    // Colors with reduced opacity for multi-color graphs
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'];
    const colorsWithOpacity = colors.map(color => {
      const r = parseInt(color.slice(1, 3), 16);
      const g = parseInt(color.slice(3, 5), 16);
      const b = parseInt(color.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, 0.5)`;
    });
    
    // Prepare chart data
    const projectBudgetData = projects.slice(0, 6).map(p => ({
      name: p.name.length > 25 ? p.name.substring(0, 25) + '...' : p.name,
      Budget: p.budget / 1000,
      Spent: p.spent / 1000,
      Remaining: (p.budget - p.spent) / 1000
    }));

    const projectROIData = projects.filter(p => p.expectedROI).slice(0, 6).map(p => ({
      name: p.name.length > 20 ? p.name.substring(0, 20) + '...' : p.name,
      'Expected ROI': p.expectedROI,
      'Actual ROI': p.actualROI || 0
    }));

    const projectProgressData = projects.slice(0, 6).map(p => ({
      name: p.name.length > 25 ? p.name.substring(0, 25) + '...' : p.name,
      Progress: p.progress
    }));

    const statusDistribution = projects.reduce((acc, p) => {
      const status = p.status;
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});

    const statusChartData = Object.keys(statusDistribution).map(status => ({
      status: status.replace('-', ' ').toUpperCase(),
      count: statusDistribution[status]
    }));

    // Summary metrics
    const totalBudget = projects.reduce((sum, p) => sum + p.budget, 0);
    const totalSpent = projects.reduce((sum, p) => sum + p.spent, 0);
    const avgProgress = projects.reduce((sum, p) => sum + p.progress, 0) / projects.length;
    const onTrackProjects = projects.filter(p => p.status === 'on-track' || p.status === 'completed').length;
    const completedProjects = projects.filter(p => p.status === 'completed').length;

    return (
      <div className="space-y-6">
        {/* Summary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {projects.length}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Projects</p>
              <p className="text-xs text-white opacity-75">{completedProjects} completed</p>
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
                {formatNumber(totalBudget / 1000000)}M
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Budget</p>
              <p className="text-xs text-white opacity-75">{formatNumber(totalSpent / 1000000)}M spent</p>
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
                {avgProgress.toFixed(1)}%
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Avg Progress</p>
              <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                <div
                  className="h-1.5 rounded-full"
                  style={{
                    width: `${avgProgress}%`,
                    background: 'linear-gradient(90deg, #d97706 0%, #f59e0b 100%)'
                  }}
                />
              </div>
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
                {onTrackProjects}/{projects.length}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">On Track</p>
              <p className="text-xs text-white opacity-75">{((onTrackProjects / projects.length) * 100).toFixed(1)}% success rate</p>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Budget Overview Chart */}
          <div 
            className="rounded-[10px] p-5"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                Budget Overview (€ k)
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInsightModal({ isOpen: true, chartTitle: 'Budget Overview' })}
                className="text-amber-600 hover:text-amber-700"
              >
                <Lightbulb className="w-4 h-4 mr-1" />
                Insights
              </Button>
            </div>
            <ChartComponent
              type="bar"
              data={{
                labels: projectBudgetData.map(d => d.name),
                datasets: [
                  {
                    label: 'Budget',
                    data: projectBudgetData.map(d => d.Budget),
                    backgroundColor: '#1e293b'
                  },
                  {
                    label: 'Spent',
                    data: projectBudgetData.map(d => d.Spent),
                    backgroundColor: '#EDD5B1'
                  },
                  {
                    label: 'Remaining',
                    data: projectBudgetData.map(d => d.Remaining),
                    backgroundColor: '#1e293b'
                  }
                ]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: true, position: 'bottom' }
                }
              }}
              height={300}
            />
          </div>

          {/* Project Status Distribution */}
          <div 
            className="rounded-[10px] p-5"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                Project Status Distribution
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInsightModal({ isOpen: true, chartTitle: 'Project Status' })}
                className="text-amber-600 hover:text-amber-700"
              >
                <Lightbulb className="w-4 h-4 mr-1" />
                Insights
              </Button>
            </div>
            <ChartComponent
              type="doughnut"
              data={{
                labels: statusChartData.map(d => d.status),
                datasets: [{
                  data: statusChartData.map(d => d.count),
                  backgroundColor: colorsWithOpacity.slice(0, 5)
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: true, position: 'bottom' }
                }
              }}
              height={300}
            />
          </div>

          {/* ROI Comparison */}
          <div 
            className="rounded-[10px] p-5"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                ROI Analysis
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInsightModal({ isOpen: true, chartTitle: 'ROI Analysis' })}
                className="text-amber-600 hover:text-amber-700"
              >
                <Lightbulb className="w-4 h-4 mr-1" />
                Insights
              </Button>
            </div>
            <ChartComponent
              type="bar"
              data={{
                labels: projectROIData.map(d => d.name),
                datasets: [
                  {
                    label: 'Expected ROI',
                    data: projectROIData.map(d => d['Expected ROI']),
                    backgroundColor: '#1e293b'
                  },
                  {
                    label: 'Actual ROI',
                    data: projectROIData.map(d => d['Actual ROI']),
                    backgroundColor: '#EDD5B1'
                  }
                ]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: true, position: 'bottom' }
                },
                scales: {
                  y: { beginAtZero: true }
                }
              }}
              height={300}
            />
          </div>

          {/* Progress Tracker */}
          <div 
            className="rounded-[10px] p-5"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                Project Progress (%)
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInsightModal({ isOpen: true, chartTitle: 'Progress Tracker' })}
                className="text-amber-600 hover:text-amber-700"
              >
                <Lightbulb className="w-4 h-4 mr-1" />
                Insights
              </Button>
            </div>
            <ChartComponent
              type="line"
              data={{
                labels: projectProgressData.map(d => d.name),
                datasets: [{
                  label: 'Progress',
                  data: projectProgressData.map(d => d.Progress),
                  borderColor: '#1e293b',
                  backgroundColor: 'rgba(30, 41, 59, 0.1)',
                  tension: 0.4,
                  fill: true
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false }
                },
                scales: {
                  y: { beginAtZero: true, max: 100 }
                }
              }}
              height={300}
            />
          </div>
        </div>

        {/* Project Cards */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4" style={{ fontFamily: 'Space Grotesk' }}>
            Active Projects
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {projects.map(project => (
              <ProjectCard key={project.id} project={project} getStatusColor={getStatusColor} getPriorityColor={getPriorityColor} />
            ))}
          </div>
        </div>
      </div>
    );
  };

  // ============ BUSINESS PLANNER SECTION ============
  const BusinessPlannerSection = () => {
    const plans = data.businessPlans || [];
    
    if (plans.length === 0) return null;

    return (
      <div className="space-y-6">
        {plans.map(plan => (
          <div 
            key={plan.id} 
            className="rounded-[10px] p-6"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            {/* Plan Header */}
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                  {plan.planName}
                </h3>
                <p className="text-sm text-gray-600">Period: {plan.period}</p>
              </div>
              <div className="px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-600">
                <p className="text-xs text-white font-semibold">Expected Revenue</p>
                <p className="text-lg font-bold text-white">{formatNumber(plan.expectedRevenue / 1000000)}M</p>
              </div>
            </div>

            {/* Budget Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
                <p className="text-xs text-blue-600 font-semibold mb-1">Total Budget</p>
                <p className="text-xl font-bold text-blue-900">{formatNumber(plan.totalBudget / 1000000)}M</p>
              </div>
              <div className="p-4 rounded-lg bg-green-50 border border-green-200">
                <p className="text-xs text-green-600 font-semibold mb-1">Allocated Budget</p>
                <p className="text-xl font-bold text-green-900">{formatNumber(plan.allocatedBudget / 1000000)}M</p>
              </div>
              <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
                <p className="text-xs text-amber-600 font-semibold mb-1">Remaining Budget</p>
                <p className="text-xl font-bold text-amber-900">{formatNumber((plan.totalBudget - plan.allocatedBudget) / 1000000)}M</p>
              </div>
            </div>

            {/* Initiatives */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Strategic Initiatives</h4>
              <div className="space-y-3">
                {plan.initiatives.map((initiative, idx) => {
                  const priorityInfo = getPriorityColor(initiative.priority);
                  const statusInfo = getStatusColor(initiative.status);
                  
                  return (
                    <div key={idx} className="p-4 rounded-lg bg-gray-50 border border-gray-200">
                      <div className="flex items-start justify-between mb-2">
                        <h5 className="text-sm font-semibold text-gray-900">{initiative.name}</h5>
                        <div className="flex gap-2">
                          <span 
                            className="px-2 py-1 rounded-full text-xs font-semibold"
                            style={{ background: priorityInfo.bg, color: priorityInfo.text }}
                          >
                            {initiative.priority}
                          </span>
                          <span 
                            className="px-2 py-1 rounded-full text-xs font-semibold"
                            style={{ background: statusInfo.bg, color: statusInfo.text }}
                          >
                            {initiative.status}
                          </span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div>
                          <span className="text-gray-600">Budget: </span>
                          <span className="font-semibold text-gray-900">{formatNumber(initiative.budget)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Expected Revenue: </span>
                          <span className="font-semibold text-gray-900">{formatNumber(initiative.revenue)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Milestones Timeline */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Key Milestones</h4>
              <div className="space-y-3">
                {plan.milestones.map((milestone, idx) => {
                  const statusInfo = getStatusColor(milestone.status);
                  const StatusIcon = statusInfo.icon;
                  
                  return (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="flex-shrink-0">
                        <div 
                          className="w-10 h-10 rounded-full flex items-center justify-center"
                          style={{ background: statusInfo.bg }}
                        >
                          <StatusIcon className="w-5 h-5" style={{ color: statusInfo.text }} />
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <h5 className="text-sm font-semibold text-gray-900">{milestone.name}</h5>
                          <span className="text-xs text-gray-600">{milestone.date}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="h-2 rounded-full transition-all"
                            style={{
                              width: `${milestone.progress}%`,
                              background: 'linear-gradient(90deg, #d97706 0%, #f59e0b 100%)'
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* AI Insights */}
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 p-4 rounded-lg border border-amber-200">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5 text-amber-600" />
                <h4 className="text-sm font-semibold text-amber-900">AI Strategic Insights</h4>
              </div>
              <ul className="space-y-2">
                {plan.aiInsights.map((insight, idx) => (
                  <li key={idx} className="text-sm text-amber-800 flex items-start gap-2">
                    <Zap className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // ============ CAMPAIGN COCKPIT SECTION ============
  const CampaignCockpitSection = () => {
    const campaigns = data.campaigns || [];
    const activeCampaigns = campaigns.filter(c => c.status === 'active');
    const completedCampaigns = campaigns.filter(c => c.status === 'completed');
    
    // Colors with reduced opacity for multi-color graphs
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'];
    const colorsWithOpacity = colors.map(color => {
      const r = parseInt(color.slice(1, 3), 16);
      const g = parseInt(color.slice(3, 5), 16);
      const b = parseInt(color.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, 0.5)`;
    });
    
    // Summary metrics
    const totalBudget = campaigns.reduce((sum, c) => sum + c.budget, 0);
    const totalSpent = campaigns.reduce((sum, c) => sum + c.spent, 0);
    const totalRevenue = campaigns.reduce((sum, c) => sum + c.revenue, 0);
    const avgROI = campaigns.filter(c => c.roi > 0).reduce((sum, c) => sum + c.roi, 0) / campaigns.filter(c => c.roi > 0).length;
    const totalLeads = campaigns.reduce((sum, c) => sum + c.leads, 0);
    const totalConversions = campaigns.reduce((sum, c) => sum + c.conversions, 0);

    // Chart data
    const campaignPerformanceData = campaigns.slice(0, 6).map(c => ({
      name: c.name.length > 20 ? c.name.substring(0, 20) + '...' : c.name,
      Budget: c.budget / 1000,
      Revenue: c.revenue / 1000,
      ROI: c.roi
    }));

    const campaignROIData = campaigns.filter(c => c.roi > 0).slice(0, 6).map(c => ({
      name: c.name.length > 20 ? c.name.substring(0, 20) + '...' : c.name,
      ROI: c.roi
    }));

    const conversionRateData = campaigns.filter(c => c.conversionRate > 0).slice(0, 6).map(c => ({
      name: c.name.length > 20 ? c.name.substring(0, 20) + '...' : c.name,
      'Conversion Rate': c.conversionRate
    }));

    return (
      <div className="space-y-6">
        {/* Summary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {activeCampaigns.length}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Active Campaigns</p>
              <p className="text-xs text-white opacity-75">{campaigns.length} total campaigns</p>
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
                {formatNumber(totalRevenue / 1000000)}M
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Revenue</p>
              <p className="text-xs text-white opacity-75">{formatNumber(totalSpent)} spent</p>
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
                {avgROI.toFixed(1)}x
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Avg ROI</p>
              <p className="text-xs text-white opacity-75">Return on investment</p>
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
                {formatNumber(totalLeads)}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Leads</p>
              <p className="text-xs text-white opacity-75">{formatNumber(totalConversions)} conversions</p>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Campaign Performance */}
          <div 
            className="rounded-[10px] p-5"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                Campaign Performance (€ k)
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInsightModal({ isOpen: true, chartTitle: 'Campaign Performance' })}
                className="text-amber-600 hover:text-amber-700"
              >
                <Lightbulb className="w-4 h-4 mr-1" />
                Insights
              </Button>
            </div>
            <ChartComponent
              type="bar"
              data={{
                labels: campaignPerformanceData.map(d => d.name),
                datasets: [
                  {
                    label: 'Budget',
                    data: campaignPerformanceData.map(d => d.Budget),
                    backgroundColor: '#1e293b'
                  },
                  {
                    label: 'Revenue',
                    data: campaignPerformanceData.map(d => d.Revenue),
                    backgroundColor: '#EDD5B1'
                  }
                ]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: true, position: 'bottom' }
                }
              }}
              height={300}
            />
          </div>

          {/* ROI by Campaign */}
          <div 
            className="rounded-[10px] p-5"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                ROI by Campaign
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInsightModal({ isOpen: true, chartTitle: 'Campaign ROI' })}
                className="text-amber-600 hover:text-amber-700"
              >
                <Lightbulb className="w-4 h-4 mr-1" />
                Insights
              </Button>
            </div>
            <ChartComponent
              type="bar"
              data={{
                labels: campaignROIData.map(d => d.name),
                datasets: [{
                  label: 'ROI',
                  data: campaignROIData.map(d => d.ROI),
                  backgroundColor: colorsWithOpacity.slice(0, 6)
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false }
                },
                scales: {
                  y: { beginAtZero: true }
                }
              }}
              height={300}
            />
          </div>

          {/* Conversion Rates */}
          <div 
            className="rounded-[10px] p-5 lg:col-span-2"
            style={{
              background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                Conversion Rate Analysis (%)
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInsightModal({ isOpen: true, chartTitle: 'Conversion Rate' })}
                className="text-amber-600 hover:text-amber-700"
              >
                <Lightbulb className="w-4 h-4 mr-1" />
                Insights
              </Button>
            </div>
            <ChartComponent
              type="line"
              data={{
                labels: conversionRateData.map(d => d.name),
                datasets: [{
                  label: 'Conversion Rate (%)',
                  data: conversionRateData.map(d => d['Conversion Rate']),
                  borderColor: '#1e293b',
                  backgroundColor: 'rgba(30, 41, 59, 0.1)',
                  tension: 0.4,
                  fill: true
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false }
                },
                scales: {
                  y: { beginAtZero: true }
                }
              }}
              height={300}
            />
          </div>
        </div>

        {/* Campaign Cards */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4" style={{ fontFamily: 'Space Grotesk' }}>
            Campaign Details
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {campaigns.map(campaign => (
              <CampaignCard key={campaign.id} campaign={campaign} getStatusColor={getStatusColor} />
            ))}
          </div>
        </div>
      </div>
    );
  };

  // ============ GOALS MANAGEMENT SECTION ============
  // Note: Goals Management state is now defined at the top of the component to follow Rules of Hooks
  
  const selectedQuarter = goals?.quarters?.find(q => q.id === selectedQuarterId) || goals?.quarters?.[0] || null;

  const toggleGoalExpansion = (goalId) => {
    setExpandedGoals(prev => ({
      ...prev,
      [goalId]: !prev[goalId]
    }));
  };

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

  const GoalsManagementSection = () => {
    return (
      <div className="space-y-6">
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
          <div 
            className="rounded-lg p-5 text-white"
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <div className="mb-3">
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk', color: '#EDD5B1' }}>
                {selectedQuarter?.objectives?.length || 0}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Total Objectives</p>
              <p className="text-xs text-white opacity-75">{selectedQuarter?.quarter || 'N/A'}</p>
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
                {selectedQuarter?.objectives?.filter(o => o.status === 'on-track').length || 0}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">On Track</p>
              <p className="text-xs text-white opacity-75">Meeting targets</p>
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
                {selectedQuarter?.objectives?.filter(o => o.status === 'at-risk').length || 0}
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">At Risk</p>
              <p className="text-xs text-white opacity-75">Needs attention</p>
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
                {selectedQuarter?.objectives?.length > 0 
                  ? Math.round(selectedQuarter.objectives.reduce((sum, o) => sum + (o.progress || 0), 0) / selectedQuarter.objectives.length)
                  : 0}%
              </h2>
              <p className="text-sm text-white opacity-90 mb-3">Avg Progress</p>
              <p className="text-xs text-white opacity-75">Overall completion</p>
            </div>
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
                    className="rounded-[10px] p-6 cursor-pointer transition-all duration-300 hover:shadow-xl hover:scale-105 border-l-4"
                    style={{ 
                      borderLeftColor: dept.color.border,
                      background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                      border: '1px solid rgba(0, 0, 0, 0.1)',
                      borderLeft: `4px solid ${dept.color.border}`
                    }}
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
              <div 
                className="rounded-[10px] p-6 border-l-4" 
                style={{ 
                  borderLeftColor: selectedDepartment.color.border,
                  background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                  border: '1px solid rgba(0, 0, 0, 0.1)',
                  borderLeft: `4px solid ${selectedDepartment.color.border}`
                }}
              >
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
                  className="rounded-[10px] p-6 border-l-4"
                  style={{ 
                    borderLeftColor: selectedDepartment.color.border,
                    background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                    border: '1px solid rgba(0, 0, 0, 0.1)',
                    borderLeft: `4px solid ${selectedDepartment.color.border}`
                  }}
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
                          <Users className="w-4 h-4" />
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
                className="rounded-[10px] p-6 border-l-4"
                style={{ 
                  borderLeftColor: statusInfo.border,
                  background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                  border: '1px solid rgba(0, 0, 0, 0.1)',
                  borderLeft: `4px solid ${statusInfo.border}`
                }}
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
                        <Users className="w-4 h-4 text-gray-500" />
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
                      <div key={`kr-${objective.id}-${kr.id || krIdx}`} className="bg-gray-50 rounded-lg p-4">
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
      </div>
    );
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
              Projects & Planning
            </h1>
            <p className="text-gray-600 text-sm mt-1">Manage projects, strategic plans, and campaigns</p>
          </div>
          {activeSection === 'goals-management' ? (
            <Button
              className="text-white"
              style={{ background: '#184464' }}
              onClick={() => handleNewGoal('quarterly')}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Goal
            </Button>
          ) : (
            <Button
              className="text-white"
              style={{ background: '#184464' }}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          )}
        </div>

        {/* Section Navigation */}
        <div 
          className="rounded-[10px] p-1"
          style={{
            background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
          <div className="flex gap-1">
            <button
              onClick={() => setActiveSection('top-projects')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeSection === 'top-projects'
                  ? 'text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
              style={activeSection === 'top-projects' ? { background: '#184464' } : {}}
            >
              <FolderKanban className="w-4 h-4" />
              Top Projects
            </button>
            <button
              onClick={() => setActiveSection('business-planner')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeSection === 'business-planner'
                  ? 'text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
              style={activeSection === 'business-planner' ? { background: '#184464' } : {}}
            >
              <Target className="w-4 h-4" />
              Business Planner
            </button>
            <button
              onClick={() => setActiveSection('campaign-cockpit')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeSection === 'campaign-cockpit'
                  ? 'text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
              style={activeSection === 'campaign-cockpit' ? { background: '#184464' } : {}}
            >
              <BarChart3 className="w-4 h-4" />
              Campaign Cockpit
            </button>
            <button
              onClick={() => setActiveSection('goals-management')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeSection === 'goals-management'
                  ? 'text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
              style={activeSection === 'goals-management' ? { background: '#184464' } : {}}
            >
              <Target className="w-4 h-4" />
              Goals Management
            </button>
          </div>
        </div>

        {/* Active Section Content */}
        {activeSection === 'top-projects' && <TopProjectsSection />}
        {activeSection === 'business-planner' && <BusinessPlannerSection />}
        {activeSection === 'campaign-cockpit' && <CampaignCockpitSection />}
        {activeSection === 'goals-management' && <GoalsManagementSection />}

        {/* Insight Modal */}
        {insightModal.isOpen && (
          <InsightModal
            isOpen={insightModal.isOpen}
            onClose={() => setInsightModal({ isOpen: false, chartTitle: '' })}
            chartTitle={insightModal.chartTitle}
          />
        )}

        {/* Goal Form Modal */}
        {activeSection === 'goals-management' && (
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
        )}
      </div>
    </Layout>
  );
};

// ============ PROJECT CARD COMPONENT ============
const ProjectCard = ({ project, getStatusColor, getPriorityColor }) => {
  const statusInfo = getStatusColor(project.status);
  const StatusIcon = statusInfo.icon;
  const priorityInfo = getPriorityColor(project.priority);
  const budgetUtilization = (project.spent / project.budget) * 100;

  return (
    <div 
      className="rounded-[10px] p-5"
      style={{
        background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
        border: '1px solid rgba(0, 0, 0, 0.1)'
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="text-base font-semibold text-gray-900 mb-1" style={{ fontFamily: 'Space Grotesk' }}>
            {project.name}
          </h4>
          <p className="text-xs text-gray-600">{project.category}</p>
        </div>
        <div className="flex gap-2">
          <div 
            className="px-2 py-1 rounded-full text-xs font-semibold flex items-center gap-1"
            style={{ background: statusInfo.bg, color: statusInfo.text }}
          >
            <StatusIcon className="w-3 h-3" />
            {project.status.replace('-', ' ')}
          </div>
          <div 
            className="px-2 py-1 rounded-full text-xs font-semibold"
            style={{ background: priorityInfo.bg, color: priorityInfo.text }}
          >
            {project.priority}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="p-3 rounded-lg bg-gray-50">
          <p className="text-xs text-gray-600 mb-0.5">Budget</p>
          <p className="text-sm font-semibold text-gray-900">{formatNumber(project.budget)}</p>
          <p className="text-xs text-gray-500">{formatNumber(project.spent)} spent</p>
        </div>
        <div className="p-3 rounded-lg bg-gray-50">
          <p className="text-xs text-gray-600 mb-0.5">Expected ROI</p>
          <p className="text-sm font-semibold text-gray-900">{project.expectedROI}x</p>
          {project.actualROI && (
            <p className="text-xs text-green-600">Actual: {project.actualROI}x</p>
          )}
        </div>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-600">Progress</span>
          <span className="text-xs font-semibold text-gray-900">{project.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all"
            style={{
              width: `${project.progress}%`,
              background: project.progress >= 75 ? 'linear-gradient(90deg, #10b981 0%, #059669 100%)' : 
                         project.progress >= 50 ? 'linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)' :
                         'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)'
            }}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs mb-3">
        <div>
          <p className="text-gray-600">Team</p>
          <p className="font-semibold text-gray-900">{project.teamSize}</p>
        </div>
        <div>
          <p className="text-gray-600">Milestones</p>
          <p className="font-semibold text-gray-900">{project.completedMilestones}/{project.milestones}</p>
        </div>
        <div>
          <p className="text-gray-600">End Date</p>
          <p className="font-semibold text-gray-900">{new Date(project.endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</p>
        </div>
      </div>

      {Object.keys(project.keyMetrics).length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-3 rounded-lg border border-blue-200">
          <p className="text-xs font-semibold text-blue-900 mb-2">Key Impact Metrics</p>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {Object.entries(project.keyMetrics).map(([key, value]) => (
              <div key={key}>
                <p className="text-blue-600">{key.replace(/_/g, ' ')}</p>
                <p className="font-semibold text-blue-900">{typeof value === 'number' && value > 1000 ? formatNumber(value) : value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============ CAMPAIGN CARD COMPONENT ============
const CampaignCard = ({ campaign, getStatusColor }) => {
  const statusInfo = getStatusColor(campaign.status);
  const StatusIcon = statusInfo.icon;
  const budgetUtilization = campaign.budget > 0 ? (campaign.spent / campaign.budget) * 100 : 0;

  return (
    <div 
      className="rounded-[10px] p-5"
      style={{
        background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
        border: '1px solid rgba(0, 0, 0, 0.1)'
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="text-base font-semibold text-gray-900 mb-1" style={{ fontFamily: 'Space Grotesk' }}>
            {campaign.name}
          </h4>
          <p className="text-xs text-gray-600">{campaign.type}</p>
        </div>
        <div 
          className="px-2 py-1 rounded-full text-xs font-semibold flex items-center gap-1"
          style={{ background: statusInfo.bg, color: statusInfo.text }}
        >
          <StatusIcon className="w-3 h-3" />
          {campaign.status}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="p-2 rounded-lg bg-blue-50">
          <p className="text-xs text-blue-600 mb-0.5">Budget</p>
          <p className="text-sm font-semibold text-blue-900">{formatNumber(campaign.budget)}</p>
        </div>
        <div className="p-2 rounded-lg bg-green-50">
          <p className="text-xs text-green-600 mb-0.5">Revenue</p>
          <p className="text-sm font-semibold text-green-900">{formatNumber(campaign.revenue)}</p>
        </div>
        <div className="p-2 rounded-lg bg-amber-50">
          <p className="text-xs text-amber-600 mb-0.5">ROI</p>
          <p className="text-sm font-semibold text-amber-900">{campaign.roi}x</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3 text-xs">
        <div>
          <p className="text-gray-600 mb-0.5">Leads</p>
          <p className="font-semibold text-gray-900">{formatNumber(campaign.leads)}</p>
        </div>
        <div>
          <p className="text-gray-600 mb-0.5">Conversions</p>
          <p className="font-semibold text-gray-900">{formatNumber(campaign.conversions)}</p>
        </div>
        <div>
          <p className="text-gray-600 mb-0.5">Conversion Rate</p>
          <p className="font-semibold text-gray-900">{campaign.conversionRate}%</p>
        </div>
        <div>
          <p className="text-gray-600 mb-0.5">Engagement Rate</p>
          <p className="font-semibold text-gray-900">{campaign.engagementRate}%</p>
        </div>
      </div>

      <div className="mb-3">
        <p className="text-xs text-gray-600 mb-1">Budget Utilization: {budgetUtilization.toFixed(1)}%</p>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all"
            style={{
              width: `${Math.min(budgetUtilization, 100)}%`,
              background: budgetUtilization > 90 ? 'linear-gradient(90deg, #ef4444 0%, #dc2626 100%)' :
                         budgetUtilization > 70 ? 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)' :
                         'linear-gradient(90deg, #10b981 0%, #059669 100%)'
            }}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {campaign.channels.slice(0, 3).map((channel, idx) => (
          <span key={idx} className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700">
            {channel}
          </span>
        ))}
        {campaign.channels.length > 3 && (
          <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700">
            +{campaign.channels.length - 3} more
          </span>
        )}
      </div>
    </div>
  );
};

export default ProjectsNew;
