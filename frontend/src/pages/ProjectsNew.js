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
import { useTheme } from '@/contexts/ThemeContext';

const ProjectsNew = () => {
  const { token } = useAuth();
  const { theme } = useTheme();
  const [activeSection, setActiveSection] = useState('top-projects');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [insightModal, setInsightModal] = useState({ isOpen: false, chartTitle: '' });


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



  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading projects...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">No data available</p>
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

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100" style={{ fontFamily: 'Space Grotesk' }}>
              Projects & Planning
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">Manage projects, strategic plans, and campaigns</p>
          </div>
          <Button
            className="text-white"
            style={{ background: '#184464' }}
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Section Navigation */}
        <div 
          className="rounded-[10px] p-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
          style={theme === 'dark' 
            ? {
                background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }
            : {
                background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                border: '1px solid rgba(0, 0, 0, 0.1)'
              }
          }
        >
          <div className="flex gap-1">
            <button
              onClick={() => setActiveSection('top-projects')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                activeSection === 'top-projects'
                  ? 'text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
              style={activeSection === 'top-projects' ? { background: '#184464' } : {}}
            >
              <FolderKanban className="w-4 h-4" />
              Top Projects
            </button>
          </div>
        </div>

        {/* Active Section Content */}
        {activeSection === 'top-projects' && <TopProjectsSection />}

        {/* Insight Modal */}
        {insightModal.isOpen && (
          <InsightModal
            isOpen={insightModal.isOpen}
            onClose={() => setInsightModal({ isOpen: false, chartTitle: '' })}
            chartTitle={insightModal.chartTitle}
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
