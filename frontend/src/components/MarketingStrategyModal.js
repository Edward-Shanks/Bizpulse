import React, { useState, useEffect } from 'react';
import { X, Save, Download, FileText, MessageSquare, Clock, User, CheckCircle, AlertCircle, Sparkles, Check, Plus, Trash2, ChevronLeft, Edit, Target } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea.jsx';
import { Checkbox } from '@/components/ui/checkbox';
import ChartComponent from '@/components/ChartComponent';
import MultiSelect from '@/components/ui/multi-select';
import { cn } from '@/lib/utils';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { toast } from 'sonner';

const MarketingStrategyModal = ({ isOpen, onClose, moduleId, moduleTitle }) => {
  const { token } = useAuth();
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'config'
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [activeSection, setActiveSection] = useState('A');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStrategies, setLoadingStrategies] = useState(false);
  const [formData, setFormData] = useState({});
  const [strategyName, setStrategyName] = useState('');
  const [aiInsights, setAiInsights] = useState('');
  const [generatingAI, setGeneratingAI] = useState(false);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [showAIInsights, setShowAIInsights] = useState(true);

  // Load strategies list on mount
  useEffect(() => {
    if (isOpen && moduleId) {
      loadStrategies();
      loadComments();
    }
  }, [isOpen, moduleId]);

  // Reset view mode when modal opens
  useEffect(() => {
    if (isOpen) {
      setViewMode('list');
      setSelectedStrategy(null);
      setFormData({});
      setStrategyName('');
      setAiInsights('');
    }
  }, [isOpen]);

  const loadStrategies = async () => {
    try {
      setLoadingStrategies(true);
      const response = await axios.get(`${API}/marketing-strategy/${moduleId}/list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStrategies(response.data.strategies || []);
    } catch (error) {
      console.error('Error loading strategies:', error);
      setStrategies([]);
    } finally {
      setLoadingStrategies(false);
    }
  };

  const loadStrategy = async (strategyId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/marketing-strategy/${moduleId}/${strategyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data) {
        setFormData(response.data.config || getDefaultFormData());
        setStrategyName(response.data.strategy_name || '');
        setAiInsights(response.data.ai_insights || '');
        setSelectedStrategy(response.data);
      }
    } catch (error) {
      console.error('Error loading strategy:', error);
      toast.error('Failed to load strategy');
    } finally {
      setLoading(false);
    }
  };

  // const loadVersions = async () => {
  //   try {
  //     const response = await axios.get(`${API}/marketing-strategy/${moduleId}/versions`, {
  //       headers: { Authorization: `Bearer ${token}` }
  //     });
  //     setVersions(response.data.versions || []);
  //   } catch (error) {
  //     console.error('Error loading versions:', error);
  //   }
  // };

  const loadComments = async () => {
    try {
      const response = await axios.get(`${API}/marketing-strategy/${moduleId}/comments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setComments(response.data.comments || []);
    } catch (error) {
      console.error('Error loading comments:', error);
    }
  };

  const getDefaultFormData = () => {
    const defaults = {
      strategicFramework: {
        businessObjectives: {
          primaryGoal: '',
          revenueTarget: '',
          growthTarget: '',
          timeHorizon: 'Quarter'
        },
        strategicFocus: {
          marketFocus: [],
          geography: [],
          productFocus: []
        },
        valueProposition: {
          coreMessage: '',
          differentiators: [],
          pricingStrategy: ''
        },
        kpis: {
          northStarMetric: '',
          supportingKPIs: []
        }
      },
      channelStrategy: {
        channels: [],
        channelRoles: {},
        benchmarks: {},
        visualization: {}
      },
      budgetAllocation: {
        totalBudget: '',
        timePeriod: '',
        currency: 'EUR',
        allocations: {},
        scenarios: {}
      },
      marketSegmentation: {
        segmentationType: [],
        segments: [],
        customerTraits: {},
        priorities: {}
      },
      brandPositioning: {
        brandIdentity: {
          personality: [],
          tone: ''
        },
        positioningStatement: {
          targetCustomer: '',
          marketCategory: '',
          brandPromise: '',
          reasonToBelieve: ''
        },
        messagingFramework: {
          coreMessage: '',
          supportingMessages: [],
          dos: [],
          donts: []
        },
        competitivePerception: {}
      },
      competitiveStrategy: {
        competitors: [],
        competitiveMoves: {},
        responseStrategies: {},
        swot: {}
      }
    };
    return defaults;
  };

  const handleCreateNew = () => {
    setViewMode('config');
    setSelectedStrategy(null);
    setFormData(getDefaultFormData());
    setStrategyName('');
    setAiInsights('');
    setActiveSection('A');
  };

  const handleEditStrategy = (strategy) => {
    setSelectedStrategy(strategy);
    setViewMode('config');
    loadStrategy(strategy.id);
  };

  const handleDeleteStrategy = async (strategyId) => {
    if (!window.confirm('Are you sure you want to delete this strategy? This action cannot be undone.')) {
      return;
    }

    try {
      await axios.delete(
        `${API}/marketing-strategy/${moduleId}/${strategyId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Strategy deleted successfully');
      await loadStrategies();
    } catch (error) {
      console.error('Error deleting strategy:', error);
      toast.error('Failed to delete strategy');
    }
  };

  const handleGenerateAI = async () => {
    try {
      setGeneratingAI(true);
      const response = await axios.post(
        `${API}/marketing-strategy/${moduleId}/generate-ai-insights`,
        {
          config: formData,
          module_id: moduleId,
          module_title: moduleTitle
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAiInsights(response.data.ai_insights || '');
      toast.success('AI insights generated successfully');
    } catch (error) {
      console.error('Error generating AI insights:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate AI insights');
    } finally {
      setGeneratingAI(false);
    }
  };

  const handleSave = async () => {
    if (!strategyName.trim()) {
      toast.error('Please enter a strategy name');
      return;
    }

    try {
      setSaving(true);
      const payload = {
        strategy_name: strategyName,
        config: formData,
        ai_insights: aiInsights
      };

      if (selectedStrategy?.id) {
        // Update existing strategy
        await axios.put(
          `${API}/marketing-strategy/${moduleId}/${selectedStrategy.id}`,
          payload,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success('Strategy updated successfully');
      } else {
        // Create new strategy
        await axios.post(
          `${API}/marketing-strategy/${moduleId}`,
          payload,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success('Strategy saved successfully');
      }

      // Return to list view
      setViewMode('list');
      setSelectedStrategy(null);
      await loadStrategies();
    } catch (error) {
      console.error('Error saving strategy:', error);
      toast.error('Failed to save strategy');
    } finally {
      setSaving(false);
    }
  };

  const handleBackToList = () => {
    setViewMode('list');
    setSelectedStrategy(null);
    setFormData({});
    setStrategyName('');
    setAiInsights('');
  };

  // const handleExport = async (format) => {
  //   try {
  //     const response = await axios.get(`${API}/marketing-strategy/${moduleId}/export?format=${format}`, {
  //       headers: { Authorization: `Bearer ${token}` },
  //       responseType: 'blob'
  //     });
  //     const url = window.URL.createObjectURL(new Blob([response.data]));
  //     const link = document.createElement('a');
  //     link.href = url;
  //     link.setAttribute('download', `${moduleTitle}_${new Date().toISOString()}.${format}`);
  //     document.body.appendChild(link);
  //     link.click();
  //     link.remove();
  //     toast.success(`Exported as ${format.toUpperCase()}`);
  //   } catch (error) {
  //     console.error('Error exporting:', error);
  //     toast.error('Failed to export');
  //   }
  // };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    try {
      await axios.post(
        `${API}/marketing-strategy/${moduleId}/comments`,
        { text: newComment },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setNewComment('');
      await loadComments();
      toast.success('Comment added');
    } catch (error) {
      console.error('Error adding comment:', error);
      toast.error('Failed to add comment');
    }
  };

  if (!isOpen) return null;

  const sections = getSectionsForModule(moduleId);

  // List View
  if (viewMode === 'list') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{moduleTitle}</h2>
              <p className="text-sm text-gray-500">Manage your strategies</p>
            </div>
            <div className="flex items-center gap-2">
              <Button onClick={handleCreateNew} size="sm" className="bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Create New Strategy
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>

          {/* Strategies List */}
          <div className="flex-1 overflow-y-auto p-6">
            {loadingStrategies ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : strategies.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Target className="w-16 h-16 text-gray-300 mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">No strategies yet</h3>
                <p className="text-gray-500 mb-6">Create your first strategy to get started</p>
                <Button onClick={handleCreateNew} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Create New Strategy
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {strategies.map((strategy) => (
                  <div
                    key={strategy.id}
                    className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer bg-white"
                    onClick={() => handleEditStrategy(strategy)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-gray-900 text-lg">{strategy.strategy_name}</h3>
                      {strategy.has_ai_insights && (
                        <Sparkles className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mb-3">
                      Created: {new Date(strategy.created_at).toLocaleDateString()}
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditStrategy(strategy);
                        }}
                        className="flex-1"
                      >
                        <Edit className="w-3 h-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteStrategy(strategy.id);
                        }}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Configuration View
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={handleBackToList}>
              <ChevronLeft className="w-4 h-4 mr-2" />
              Back to List
            </Button>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{moduleTitle}</h2>
              <p className="text-sm text-gray-500">
                {selectedStrategy ? 'Edit Strategy' : 'Create New Strategy'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleSave} disabled={saving} size="sm">
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save'}
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Navigation */}
          <div className="w-64 border-r bg-gray-50 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Sections</h3>
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg mb-1 transition ${
                    activeSection === section.id
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {section.label}
                </button>
              ))}
            </div>

            {/* AI Insights Summary Panel */}
            {aiInsights && showAIInsights && (
              <div className="p-4 border-t">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-700">AI Insights</h3>
                  <button onClick={() => setShowAIInsights(false)}>
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
                <div className="p-2 bg-blue-50 rounded text-xs text-blue-800 line-clamp-3">
                  <Sparkles className="w-3 h-3 inline mr-1" />
                  {aiInsights.substring(0, 150)}...
                </div>
              </div>
            )}

            {/* Version History - Commented out */}
            {/* <div className="p-4 border-t">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Versions</h3>
              <select
                value={selectedVersion || ''}
                onChange={(e) => setSelectedVersion(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              >
                <option value="">Current Version</option>
                {versions.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name} - {new Date(v.createdAt).toLocaleDateString()}
                  </option>
                ))}
              </select>
            </div> */}
          </div>

          {/* Main Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Strategy Name Input */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <Label className="text-sm font-semibold text-gray-700 mb-2">Strategy Name</Label>
                  <Input
                    value={strategyName}
                    onChange={(e) => setStrategyName(e.target.value)}
                    placeholder="Enter strategy name (e.g., Q1 2025 Strategy, Product Launch Strategy)"
                    className="bg-white"
                  />
                </div>

                {/* Configuration Sections */}
                <div>
                  {renderSectionContent(moduleId, activeSection, formData, setFormData, aiInsights, generatingAI, handleGenerateAI, moduleTitle)}
                </div>
              </div>
            )}
          </div>

          {/* Right Sidebar - Comments & Notes */}
          <div className="w-80 border-l bg-gray-50 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Comments & Notes</h3>
              <div className="mb-4">
                <Textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a comment..."
                  className="mb-2"
                  rows={3}
                />
                <Button onClick={handleAddComment} size="sm" className="w-full">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Add Comment
                </Button>
              </div>
              <div className="space-y-3">
                {comments.map((comment) => (
                  <div key={comment.id} className="p-3 bg-white rounded-lg border">
                    <div className="flex items-center gap-2 mb-1">
                      <User className="w-4 h-4 text-gray-400" />
                      <span className="text-xs font-medium text-gray-700">{comment.author}</span>
                      <span className="text-xs text-gray-400">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {new Date(comment.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{comment.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to get sections for each module
const getSectionsForModule = (moduleId) => {
  const sectionMap = {
    1: [ // Strategic Framework
      { id: 'A', label: 'A. Business Objectives' },
      { id: 'B', label: 'B. Strategic Focus' },
      { id: 'C', label: 'C. Value Proposition' },
      { id: 'D', label: 'D. KPIs & Success Metrics' }
    ],
    2: [ // Channel Strategy
      { id: 'A', label: 'A. Channel Selection' },
      { id: 'B', label: 'B. Channel Role Definition' },
      { id: 'C', label: 'C. Performance Benchmarks' },
      { id: 'D', label: 'D. Channel Mix Visualization' }
    ],
    3: [ // Budget Allocation
      { id: 'A', label: 'A. Budget Inputs' },
      { id: 'B', label: 'B. Allocation Logic' },
      { id: 'C', label: 'C. ROI Forecast' },
      { id: 'D', label: 'D. Scenario Planning' }
    ],
    4: [ // Market Segmentation
      { id: 'A', label: 'A. Segmentation Type' },
      { id: 'B', label: 'B. Segment Definition' },
      { id: 'C', label: 'C. Customer Traits' },
      { id: 'D', label: 'D. Segment Priority' }
    ],
    5: [ // Brand Positioning
      { id: 'A', label: 'A. Brand Identity' },
      { id: 'B', label: 'B. Positioning Statement' },
      { id: 'C', label: 'C. Messaging Framework' },
      { id: 'D', label: 'D. Competitive Perception' }
    ],
    6: [ // Competitive Strategy
      { id: 'A', label: 'A. Competitor Mapping' },
      { id: 'B', label: 'B. Competitive Moves' },
      { id: 'C', label: 'C. Response Strategy' },
      { id: 'D', label: 'D. SWOT Comparison' }
    ]
  };
  return sectionMap[moduleId] || [];
};

// Render section content based on module and section
// Helper function to render AI Insights section
const renderAISection = (aiInsights, generatingAI, handleGenerateAI) => {
  return (
    <div className="mt-8 pt-6 border-t border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            AI Strategic Insights
          </h4>
          <p className="text-sm text-gray-500 mt-1">Generate AI-powered insights based on your complete configuration</p>
        </div>
        <Button
          onClick={handleGenerateAI}
          disabled={generatingAI}
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white shadow-lg"
        >
          {generatingAI ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Generate Insights
            </>
          )}
        </Button>
      </div>
      
      {aiInsights && (
        <div className="mt-4 p-6 bg-gradient-to-br from-blue-50 via-purple-50 to-indigo-50 border-2 border-blue-200 rounded-xl shadow-sm">
          <div className="prose prose-sm max-w-none">
            <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
              {aiInsights.split('\n').map((line, idx) => {
                // Format headings
                if (line.match(/^#{1,3}\s/)) {
                  const level = line.match(/^#+/)[0].length;
                  const text = line.replace(/^#+\s/, '');
                  return (
                    <div
                      key={idx}
                      className={`font-bold text-gray-900 mb-2 mt-4 ${
                        level === 1 ? 'text-xl' : level === 2 ? 'text-lg' : 'text-base'
                      }`}
                    >
                      {text}
                    </div>
                  );
                }
                // Format numbered/bullet lists
                if (line.match(/^[\d•\-\*]\s/)) {
                  return (
                    <div key={idx} className="ml-4 mb-1 text-gray-700">
                      {line}
                    </div>
                  );
                }
                // Format bold text
                if (line.match(/\*\*.*\*\*/)) {
                  const parts = line.split(/(\*\*.*?\*\*)/);
                  return (
                    <div key={idx} className="mb-2 text-gray-700">
                      {parts.map((part, pIdx) =>
                        part.match(/\*\*(.*?)\*\*/) ? (
                          <strong key={pIdx} className="font-semibold text-gray-900">
                            {part.replace(/\*\*/g, '')}
                          </strong>
                        ) : (
                          part
                        )
                      )}
                    </div>
                  );
                }
                // Regular paragraph
                if (line.trim()) {
                  return (
                    <p key={idx} className="mb-3 text-gray-700">
                    {line}
                  </p>
                  );
                }
                return <br key={idx} />;
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const renderSectionContent = (moduleId, sectionId, formData, setFormData, aiInsights = '', generatingAI = false, handleGenerateAI = null, moduleTitle = '') => {
  const updateFormData = (path, value) => {
    setFormData(prev => {
      const keys = path.split('.');
      const newData = { ...prev };
      let current = newData;
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {};
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      return newData;
    });
  };

  switch (moduleId) {
    case 1: // Strategic Framework
      return renderStrategicFramework(sectionId, formData, updateFormData, aiInsights, generatingAI, handleGenerateAI, moduleTitle);
    case 2: // Channel Strategy
      return renderChannelStrategy(sectionId, formData, updateFormData, aiInsights, generatingAI, handleGenerateAI, moduleTitle);
    case 3: // Budget Allocation
      return renderBudgetAllocation(sectionId, formData, updateFormData, aiInsights, generatingAI, handleGenerateAI, moduleTitle);
    case 4: // Market Segmentation
      return renderMarketSegmentation(sectionId, formData, updateFormData, aiInsights, generatingAI, handleGenerateAI, moduleTitle);
    case 5: // Brand Positioning
      return renderBrandPositioning(sectionId, formData, updateFormData, aiInsights, generatingAI, handleGenerateAI, moduleTitle);
    case 6: // Competitive Strategy
      return renderCompetitiveStrategy(sectionId, formData, updateFormData, aiInsights, generatingAI, handleGenerateAI, moduleTitle);
    default:
      return <div>Unknown module</div>;
  }
};

// Strategic Framework Sections
const renderStrategicFramework = (sectionId, formData, updateFormData, aiInsights = '', generatingAI = false, handleGenerateAI = null, moduleTitle = '') => {
  const data = formData.strategicFramework || {};
  
  switch (sectionId) {
    case 'A': // Business Objectives
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Business Objectives</h3>
          <div className="space-y-4">
            <div>
              <Label>Primary Goal</Label>
              <select
                value={data.businessObjectives?.primaryGoal || ''}
                onChange={(e) => updateFormData('strategicFramework.businessObjectives.primaryGoal', e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-lg"
              >
                <option value="">Select Primary Goal</option>
                <option value="Revenue Growth">Revenue Growth</option>
                <option value="Market Expansion">Market Expansion</option>
                <option value="Profitability">Profitability</option>
                <option value="Brand Awareness">Brand Awareness</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Revenue Target</Label>
                <Input
                  type="number"
                  value={data.businessObjectives?.revenueTarget || ''}
                  onChange={(e) => updateFormData('strategicFramework.businessObjectives.revenueTarget', e.target.value)}
                  placeholder="Enter revenue target"
                  className="mt-1"
                />
              </div>
              <div>
                <Label>Growth % Target</Label>
                <Input
                  type="number"
                  value={data.businessObjectives?.growthTarget || ''}
                  onChange={(e) => updateFormData('strategicFramework.businessObjectives.growthTarget', e.target.value)}
                  placeholder="Enter growth %"
                  className="mt-1"
                />
              </div>
            </div>
            <div>
              <Label>Time Horizon</Label>
              <select
                value={data.businessObjectives?.timeHorizon || 'Quarter'}
                onChange={(e) => updateFormData('strategicFramework.businessObjectives.timeHorizon', e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-lg"
              >
                <option value="Quarter">Quarter</option>
                <option value="Half-Year">Half-Year</option>
                <option value="Annual">Annual</option>
              </select>
            </div>
          </div>
        </div>
      );
    
    case 'B': // Strategic Focus
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Strategic Focus</h3>
          <div className="space-y-4">
            <div>
              <Label>Market Focus</Label>
              <div className="mt-3 space-y-3">
                {['New Customers', 'Retention', 'Upsell / Cross-sell'].map((option) => {
                  const isChecked = (data.strategicFocus?.marketFocus || []).includes(option);
                  return (
                    <label 
                      key={option} 
                      className={cn(
                        "flex items-center gap-3 px-4 py-3 rounded-lg border-2 cursor-pointer transition-all",
                        "hover:bg-gray-50 hover:border-gray-300",
                        isChecked 
                          ? "bg-blue-50 border-blue-300 shadow-sm" 
                          : "bg-white border-gray-200"
                      )}
                    >
                      <Checkbox
                        checked={isChecked}
                        onCheckedChange={(checked) => {
                          const current = data.strategicFocus?.marketFocus || [];
                          const updated = checked
                            ? [...current, option]
                            : current.filter(item => item !== option);
                          updateFormData('strategicFramework.strategicFocus.marketFocus', updated);
                        }}
                      />
                      <span className={cn(
                        "text-sm font-medium flex-1",
                        isChecked ? "text-blue-900" : "text-gray-700"
                      )}>
                        {option}
                      </span>
                      {isChecked && (
                        <Check className="w-4 h-4 text-blue-600" />
                      )}
                    </label>
                  );
                })}
              </div>
            </div>
            <div>
              <Label>Geography (Multi-select)</Label>
              <MultiSelect
                options={[
                  { value: 'North America', label: 'North America' },
                  { value: 'Europe', label: 'Europe' },
                  { value: 'Asia Pacific', label: 'Asia Pacific' },
                  { value: 'Latin America', label: 'Latin America' },
                  { value: 'Middle East & Africa', label: 'Middle East & Africa' }
                ]}
                value={data.strategicFocus?.geography || []}
                onChange={(selected) => updateFormData('strategicFramework.strategicFocus.geography', selected)}
                placeholder="Select regions..."
                className="mt-1"
              />
            </div>
            <div>
              <Label>Product / Category Focus (Multi-select)</Label>
              <MultiSelect
                options={[
                  { value: 'Category A', label: 'Category A' },
                  { value: 'Category B', label: 'Category B' },
                  { value: 'Category C', label: 'Category C' },
                  { value: 'SKU 1', label: 'SKU 1' },
                  { value: 'SKU 2', label: 'SKU 2' }
                ]}
                value={data.strategicFocus?.productFocus || []}
                onChange={(selected) => updateFormData('strategicFramework.strategicFocus.productFocus', selected)}
                placeholder="Select products/categories..."
                className="mt-1"
              />
            </div>
          </div>
        </div>
      );
    
    case 'C': // Value Proposition
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Value Proposition</h3>
          <div className="space-y-4">
            <div>
              <Label>Core Value Message</Label>
              <Textarea
                value={data.valueProposition?.coreMessage || ''}
                onChange={(e) => updateFormData('strategicFramework.valueProposition.coreMessage', e.target.value)}
                placeholder="Enter your core value message"
                rows={4}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Key Differentiators</Label>
              <div className="mt-2 space-y-2">
                {(data.valueProposition?.differentiators || []).map((diff, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <Input
                      value={diff}
                      onChange={(e) => {
                        const updated = [...(data.valueProposition?.differentiators || [])];
                        updated[idx] = e.target.value;
                        updateFormData('strategicFramework.valueProposition.differentiators', updated);
                      }}
                      placeholder="Enter differentiator"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const updated = (data.valueProposition?.differentiators || []).filter((_, i) => i !== idx);
                        updateFormData('strategicFramework.valueProposition.differentiators', updated);
                      }}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const updated = [...(data.valueProposition?.differentiators || []), ''];
                    updateFormData('strategicFramework.valueProposition.differentiators', updated);
                  }}
                >
                  + Add Differentiator
                </Button>
              </div>
            </div>
            <div>
              <Label>Pricing Strategy</Label>
              <select
                value={data.valueProposition?.pricingStrategy || ''}
                onChange={(e) => updateFormData('strategicFramework.valueProposition.pricingStrategy', e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-lg"
              >
                <option value="">Select Pricing Strategy</option>
                <option value="Premium">Premium</option>
                <option value="Competitive">Competitive</option>
                <option value="Penetration">Penetration</option>
              </select>
            </div>
          </div>
        </div>
      );
    
    case 'D': // KPIs & Success Metrics
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">KPIs & Success Metrics</h3>
          <div className="space-y-4">
            <div>
              <Label>North Star Metric</Label>
              <select
                value={data.kpis?.northStarMetric || ''}
                onChange={(e) => updateFormData('strategicFramework.kpis.northStarMetric', e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-lg"
              >
                <option value="">Select North Star Metric</option>
                <option value="Revenue">Revenue</option>
                <option value="Customer Acquisition">Customer Acquisition</option>
                <option value="Customer Retention">Customer Retention</option>
                <option value="Market Share">Market Share</option>
              </select>
            </div>
            <div>
              <Label>Supporting KPIs (Multi-select)</Label>
              <MultiSelect
                options={[
                  { value: 'CAC', label: 'CAC' },
                  { value: 'LTV', label: 'LTV' },
                  { value: 'Conversion Rate', label: 'Conversion Rate' },
                  { value: 'Revenue per User', label: 'Revenue per User' }
                ]}
                value={data.kpis?.supportingKPIs || []}
                onChange={(selected) => updateFormData('strategicFramework.kpis.supportingKPIs', selected)}
                placeholder="Select supporting KPIs..."
                className="mt-1"
              />
            </div>
          </div>

          {renderAISection(aiInsights, generatingAI, handleGenerateAI)}
        </div>
      );
    
    default:
      return null;
  }
};

// Channel Strategy Sections
const renderChannelStrategy = (sectionId, formData, updateFormData, aiInsights = '', generatingAI = false, handleGenerateAI = null, moduleTitle = '') => {
  const data = formData.channelStrategy || {};
  const channels = ['Paid Search', 'Marketplaces', 'Social Ads', 'Email', 'Influencers', 'Offline'];
  
  switch (sectionId) {
    case 'A': // Channel Selection
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Channel Selection</h3>
          <div className="space-y-4">
            <div>
              <Label>Channels (Multi-select)</Label>
              <MultiSelect
                options={channels.map(ch => ({ value: ch, label: ch }))}
                value={data.channels || []}
                onChange={(selected) => updateFormData('channelStrategy.channels', selected)}
                placeholder="Select channels..."
                className="mt-1"
              />
            </div>
            <div>
              <Label>Channel Owner (User mapping)</Label>
              <div className="mt-2 space-y-2">
                {(data.channels || []).map((channel) => (
                  <div key={channel} className="flex items-center gap-2">
                    <span className="w-32 text-sm text-gray-700">{channel}:</span>
                    <Input
                      value={data.channelOwners?.[channel] || ''}
                      onChange={(e) => {
                        const owners = { ...(data.channelOwners || {}), [channel]: e.target.value };
                        updateFormData('channelStrategy.channelOwners', owners);
                      }}
                      placeholder="Enter owner email"
                      className="flex-1"
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    
    case 'B': // Channel Role Definition
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Channel Role Definition</h3>
          <div className="space-y-6">
            {(data.channels || []).map((channel) => (
              <div key={channel} className="border rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-4">{channel}</h4>
                <div className="space-y-4">
                  <div>
                    <Label>Objective</Label>
                    <select
                      value={data.channelRoles?.[channel]?.objective || ''}
                      onChange={(e) => {
                        const roles = { ...(data.channelRoles || {}), [channel]: { ...(data.channelRoles?.[channel] || {}), objective: e.target.value } };
                        updateFormData('channelStrategy.channelRoles', roles);
                      }}
                      className="w-full mt-1 px-3 py-2 border rounded-lg"
                    >
                      <option value="">Select Objective</option>
                      <option value="Acquisition">Acquisition</option>
                      <option value="Retention">Retention</option>
                      <option value="Branding">Branding</option>
                    </select>
                  </div>
                  <div>
                    <Label>Funnel Stage</Label>
                    <select
                      value={data.channelRoles?.[channel]?.funnelStage || ''}
                      onChange={(e) => {
                        const roles = { ...(data.channelRoles || {}), [channel]: { ...(data.channelRoles?.[channel] || {}), funnelStage: e.target.value } };
                        updateFormData('channelStrategy.channelRoles', roles);
                      }}
                      className="w-full mt-1 px-3 py-2 border rounded-lg"
                    >
                      <option value="">Select Funnel Stage</option>
                      <option value="Awareness">Awareness</option>
                      <option value="Consideration">Consideration</option>
                      <option value="Conversion">Conversion</option>
                    </select>
                  </div>
                  <div>
                    <Label>Priority Level</Label>
                    <select
                      value={data.channelRoles?.[channel]?.priority || ''}
                      onChange={(e) => {
                        const roles = { ...(data.channelRoles || {}), [channel]: { ...(data.channelRoles?.[channel] || {}), priority: e.target.value } };
                        updateFormData('channelStrategy.channelRoles', roles);
                      }}
                      className="w-full mt-1 px-3 py-2 border rounded-lg"
                    >
                      <option value="">Select Priority</option>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    
    case 'C': // Performance Benchmarks
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Performance Benchmarks</h3>
          <div className="space-y-4">
            {(data.channels || []).map((channel) => (
              <div key={channel} className="border rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-4">{channel}</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Expected CAC</Label>
                    <Input
                      type="number"
                      value={data.benchmarks?.[channel]?.cac || ''}
                      onChange={(e) => {
                        const benchmarks = { ...(data.benchmarks || {}), [channel]: { ...(data.benchmarks?.[channel] || {}), cac: e.target.value } };
                        updateFormData('channelStrategy.benchmarks', benchmarks);
                      }}
                      placeholder="CAC"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Expected ROAS</Label>
                    <Input
                      type="number"
                      value={data.benchmarks?.[channel]?.roas || ''}
                      onChange={(e) => {
                        const benchmarks = { ...(data.benchmarks || {}), [channel]: { ...(data.benchmarks?.[channel] || {}), roas: e.target.value } };
                        updateFormData('channelStrategy.benchmarks', benchmarks);
                      }}
                      placeholder="ROAS"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Expected Conversion %</Label>
                    <Input
                      type="number"
                      value={data.benchmarks?.[channel]?.conversion || ''}
                      onChange={(e) => {
                        const benchmarks = { ...(data.benchmarks || {}), [channel]: { ...(data.benchmarks?.[channel] || {}), conversion: e.target.value } };
                        updateFormData('channelStrategy.benchmarks', benchmarks);
                      }}
                      placeholder="Conversion %"
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    
    case 'D': // Channel Mix Visualization
      const channelData = (data.channels || []).map(ch => ({
        label: ch,
        value: data.benchmarks?.[ch]?.roas || 0
      }));
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Channel Mix Visualization</h3>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-4">Revenue Contribution %</h4>
              {channelData.length > 0 ? (
                <ChartComponent
                  type="pie"
                  data={{
                    labels: channelData.map(d => d.label),
                    datasets: [{
                      data: channelData.map(d => d.value || 1),
                      backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
                    }]
                  }}
                  height={300}
                />
              ) : (
                <div className="text-center py-12 text-gray-500">Select channels to see visualization</div>
              )}
            </div>
            <div>
              <h4 className="font-semibold mb-4">Channel Performance</h4>
              {channelData.length > 0 ? (
                <ChartComponent
                  type="bar"
                  data={{
                    labels: channelData.map(d => d.label),
                    datasets: [{
                      label: 'ROAS',
                      data: channelData.map(d => d.value || 0),
                      backgroundColor: '#3b82f6'
                    }]
                  }}
                  height={300}
                />
              ) : (
                <div className="text-center py-12 text-gray-500">Select channels to see visualization</div>
              )}
            </div>
          </div>
          {renderAISection(aiInsights, generatingAI, handleGenerateAI)}
        </div>
      );
    
    default:
      return null;
  }
};

// Budget Allocation Sections
const renderBudgetAllocation = (sectionId, formData, updateFormData, aiInsights = '', generatingAI = false, handleGenerateAI = null, moduleTitle = '') => {
  const data = formData.budgetAllocation || {};
  
  switch (sectionId) {
    case 'A': // Budget Inputs
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Budget Inputs</h3>
          <div className="space-y-4">
            <div>
              <Label>Total Marketing Budget</Label>
              <Input
                type="number"
                value={data.totalBudget || ''}
                onChange={(e) => updateFormData('budgetAllocation.totalBudget', e.target.value)}
                placeholder="Enter total budget"
                className="mt-1"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Time Period</Label>
                <select
                  value={data.timePeriod || ''}
                  onChange={(e) => updateFormData('budgetAllocation.timePeriod', e.target.value)}
                  className="w-full mt-1 px-3 py-2 border rounded-lg"
                >
                  <option value="">Select Period</option>
                  <option value="Quarter">Quarter</option>
                  <option value="Half-Year">Half-Year</option>
                  <option value="Annual">Annual</option>
                </select>
              </div>
              <div>
                <Label>Currency</Label>
                <select
                  value={data.currency || 'EUR'}
                  onChange={(e) => updateFormData('budgetAllocation.currency', e.target.value)}
                  className="w-full mt-1 px-3 py-2 border rounded-lg"
                >
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      );
    
    case 'B': // Allocation Logic
      const channels = formData.channelStrategy?.channels || [];
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Allocation Logic</h3>
          <div className="space-y-4">
            {channels.map((channel) => (
              <div key={channel} className="border rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-4">{channel}</h4>
                <div className="space-y-4">
                  <div>
                    <Label>Budget Assigned</Label>
                    <Input
                      type="number"
                      value={data.allocations?.[channel]?.budget || ''}
                      onChange={(e) => {
                        const allocations = { ...(data.allocations || {}), [channel]: { ...(data.allocations?.[channel] || {}), budget: e.target.value } };
                        updateFormData('budgetAllocation.allocations', allocations);
                      }}
                      placeholder="Enter budget"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Allocation Type</Label>
                    <select
                      value={data.allocations?.[channel]?.type || ''}
                      onChange={(e) => {
                        const allocations = { ...(data.allocations || {}), [channel]: { ...(data.allocations?.[channel] || {}), type: e.target.value } };
                        updateFormData('budgetAllocation.allocations', allocations);
                      }}
                      className="w-full mt-1 px-3 py-2 border rounded-lg"
                    >
                      <option value="">Select Type</option>
                      <option value="Fixed">Fixed</option>
                      <option value="Performance-based">Performance-based</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Min Cap %</Label>
                      <Input
                        type="number"
                        value={data.allocations?.[channel]?.minCap || ''}
                        onChange={(e) => {
                          const allocations = { ...(data.allocations || {}), [channel]: { ...(data.allocations?.[channel] || {}), minCap: e.target.value } };
                          updateFormData('budgetAllocation.allocations', allocations);
                        }}
                        placeholder="Min %"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label>Max Cap %</Label>
                      <Input
                        type="number"
                        value={data.allocations?.[channel]?.maxCap || ''}
                        onChange={(e) => {
                          const allocations = { ...(data.allocations || {}), [channel]: { ...(data.allocations?.[channel] || {}), maxCap: e.target.value } };
                          updateFormData('budgetAllocation.allocations', allocations);
                        }}
                        placeholder="Max %"
                        className="mt-1"
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    
    case 'C': // ROI Forecast
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">ROI Forecast</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Expected Revenue</Label>
                <Input
                  type="number"
                  value={data.roiForecast?.expectedRevenue || ''}
                  onChange={(e) => {
                    const forecast = { ...(data.roiForecast || {}), expectedRevenue: e.target.value };
                    updateFormData('budgetAllocation.roiForecast', forecast);
                  }}
                  placeholder="Expected Revenue"
                  className="mt-1"
                />
              </div>
              <div>
                <Label>Expected ROAS</Label>
                <Input
                  type="number"
                  value={data.roiForecast?.expectedROAS || ''}
                  onChange={(e) => {
                    const forecast = { ...(data.roiForecast || {}), expectedROAS: e.target.value };
                    updateFormData('budgetAllocation.roiForecast', forecast);
                  }}
                  placeholder="Expected ROAS"
                  className="mt-1"
                />
              </div>
              <div>
                <Label>Break-even Point</Label>
                <Input
                  type="number"
                  value={data.roiForecast?.breakEven || ''}
                  onChange={(e) => {
                    const forecast = { ...(data.roiForecast || {}), breakEven: e.target.value };
                    updateFormData('budgetAllocation.roiForecast', forecast);
                  }}
                  placeholder="Break-even Point"
                  className="mt-1"
                />
              </div>
            </div>
            {data.roiForecast?.expectedRevenue && data.totalBudget && (
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-800">
                  ROI: {((parseFloat(data.roiForecast.expectedRevenue) / parseFloat(data.totalBudget)) * 100).toFixed(2)}%
                </p>
              </div>
            )}
          </div>
        </div>
      );
    
    case 'D': // Scenario Planning
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Scenario Planning</h3>
          <div className="space-y-4">
            <div>
              <Label>Select Scenario</Label>
              <select
                value={data.selectedScenario || 'base'}
                onChange={(e) => updateFormData('budgetAllocation.selectedScenario', e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-lg"
              >
                <option value="conservative">Conservative</option>
                <option value="base">Base</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
            <div>
              <Label>Budget Shift Simulator</Label>
              <input
                type="range"
                min="-50"
                max="50"
                value={data.budgetShift || 0}
                onChange={(e) => updateFormData('budgetAllocation.budgetShift', e.target.value)}
                className="w-full mt-2"
              />
              <div className="flex justify-between text-sm text-gray-600 mt-1">
                <span>-50%</span>
                <span className="font-semibold">{data.budgetShift || 0}%</span>
                <span>+50%</span>
              </div>
            </div>
            {data.budgetShift && data.totalBudget && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  Adjusted Budget: {parseFloat(data.totalBudget) * (1 + parseFloat(data.budgetShift || 0) / 100)}
                </p>
              </div>
            )}
          </div>
          {renderAISection(aiInsights, generatingAI, handleGenerateAI)}
        </div>
      );
    
    default:
      return null;
  }
};

// Market Segmentation Sections
const renderMarketSegmentation = (sectionId, formData, updateFormData, aiInsights = '', generatingAI = false, handleGenerateAI = null, moduleTitle = '') => {
  const data = formData.marketSegmentation || {};
  
  switch (sectionId) {
    case 'A': // Segmentation Type
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Segmentation Type</h3>
          <div className="space-y-2">
            {['Demographic', 'Geographic', 'Behavioral', 'Firmographic (B2B)'].map((type) => (
              <label key={type} className="flex items-center">
                <input
                  type="checkbox"
                  checked={(data.segmentationType || []).includes(type)}
                  onChange={(e) => {
                    const current = data.segmentationType || [];
                    const updated = e.target.checked
                      ? [...current, type]
                      : current.filter(item => item !== type);
                    updateFormData('marketSegmentation.segmentationType', updated);
                  }}
                  className="mr-2"
                />
                {type}
              </label>
            ))}
          </div>
        </div>
      );
    
    case 'B': // Segment Definition
      const segments = data.segments || [];
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Segment Definition</h3>
          <div className="space-y-4">
            {segments.map((segment, idx) => (
              <div key={idx} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900">Segment {idx + 1}</h4>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      const updated = segments.filter((_, i) => i !== idx);
                      updateFormData('marketSegmentation.segments', updated);
                    }}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Segment Name</Label>
                    <Input
                      value={segment.name || ''}
                      onChange={(e) => {
                        const updated = [...segments];
                        updated[idx] = { ...updated[idx], name: e.target.value };
                        updateFormData('marketSegmentation.segments', updated);
                      }}
                      placeholder="Segment name"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Size</Label>
                    <Input
                      type="number"
                      value={segment.size || ''}
                      onChange={(e) => {
                        const updated = [...segments];
                        updated[idx] = { ...updated[idx], size: e.target.value };
                        updateFormData('marketSegmentation.segments', updated);
                      }}
                      placeholder="Size"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Revenue Contribution %</Label>
                    <Input
                      type="number"
                      value={segment.revenueContribution || ''}
                      onChange={(e) => {
                        const updated = [...segments];
                        updated[idx] = { ...updated[idx], revenueContribution: e.target.value };
                        updateFormData('marketSegmentation.segments', updated);
                      }}
                      placeholder="Revenue %"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Growth Rate</Label>
                    <Input
                      type="number"
                      value={segment.growthRate || ''}
                      onChange={(e) => {
                        const updated = [...segments];
                        updated[idx] = { ...updated[idx], growthRate: e.target.value };
                        updateFormData('marketSegmentation.segments', updated);
                      }}
                      placeholder="Growth %"
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>
            ))}
            <Button
              variant="outline"
              onClick={() => {
                const updated = [...segments, { name: '', size: '', revenueContribution: '', growthRate: '' }];
                updateFormData('marketSegmentation.segments', updated);
              }}
            >
              + Add Segment
            </Button>
          </div>
        </div>
      );
    
    case 'C': // Customer Traits
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Customer Traits</h3>
          <div className="space-y-4">
            {(data.segments || []).map((segment, idx) => (
              <div key={idx} className="border rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-4">{segment.name || `Segment ${idx + 1}`}</h4>
                <div className="space-y-4">
                  <div>
                    <Label>Pain Points (Multi-text)</Label>
                    <Textarea
                      value={data.customerTraits?.[idx]?.painPoints || ''}
                      onChange={(e) => {
                        const traits = { ...(data.customerTraits || {}), [idx]: { ...(data.customerTraits?.[idx] || {}), painPoints: e.target.value } };
                        updateFormData('marketSegmentation.customerTraits', traits);
                      }}
                      placeholder="Enter pain points"
                      rows={3}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Buying Triggers</Label>
                    <Textarea
                      value={data.customerTraits?.[idx]?.buyingTriggers || ''}
                      onChange={(e) => {
                        const traits = { ...(data.customerTraits || {}), [idx]: { ...(data.customerTraits?.[idx] || {}), buyingTriggers: e.target.value } };
                        updateFormData('marketSegmentation.customerTraits', traits);
                      }}
                      placeholder="Enter buying triggers"
                      rows={2}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Price Sensitivity</Label>
                    <select
                      value={data.customerTraits?.[idx]?.priceSensitivity || ''}
                      onChange={(e) => {
                        const traits = { ...(data.customerTraits || {}), [idx]: { ...(data.customerTraits?.[idx] || {}), priceSensitivity: e.target.value } };
                        updateFormData('marketSegmentation.customerTraits', traits);
                      }}
                      className="w-full mt-1 px-3 py-2 border rounded-lg"
                    >
                      <option value="">Select Sensitivity</option>
                      <option value="Low">Low</option>
                      <option value="Medium">Medium</option>
                      <option value="High">High</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    
    case 'D': // Segment Priority
      const segmentList = data.segments || [];
      const segmentData = segmentList.map((seg, idx) => {
        const strategicImportance = parseFloat(data.priorities?.[idx]?.strategicImportance) || 0;
        const profitabilityIndex = parseFloat(data.priorities?.[idx]?.profitabilityIndex) || 0;
        return {
          name: seg.name || `Segment ${idx + 1}`,
          strategicImportance: strategicImportance,
          profitabilityIndex: profitabilityIndex
        };
      }).filter(seg => seg.strategicImportance > 0 || seg.profitabilityIndex > 0);
      
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Segment Priority</h3>
          <p className="text-sm text-gray-500">Set priority scores for each segment to visualize strategic focus</p>
          
          {segmentList.length === 0 ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <p className="text-gray-500 mb-4">No segments defined yet. Please add segments in Section B (Segment Definition) first.</p>
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {segmentList.map((segment, idx) => (
                  <div key={idx} className="border rounded-lg p-4 bg-gray-50">
                    <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      <span className="w-8 h-8 rounded-full bg-green-100 text-green-700 flex items-center justify-center text-sm font-bold">
                        {idx + 1}
                      </span>
                      {segment.name || `Segment ${idx + 1}`}
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Strategic Importance (Score 1-5)</Label>
                        <Input
                          type="number"
                          min="1"
                          max="5"
                          step="0.5"
                          value={data.priorities?.[idx]?.strategicImportance || ''}
                          onChange={(e) => {
                            const priorities = { ...(data.priorities || {}), [idx]: { ...(data.priorities?.[idx] || {}), strategicImportance: e.target.value } };
                            updateFormData('marketSegmentation.priorities', priorities);
                          }}
                          placeholder="1-5"
                          className="mt-1"
                        />
                        <p className="text-xs text-gray-500 mt-1">Rate how strategically important this segment is</p>
                      </div>
                      <div>
                        <Label>Profitability Index</Label>
                        <Input
                          type="number"
                          min="0"
                          max="10"
                          step="0.5"
                          value={data.priorities?.[idx]?.profitabilityIndex || ''}
                          onChange={(e) => {
                            const priorities = { ...(data.priorities || {}), [idx]: { ...(data.priorities?.[idx] || {}), profitabilityIndex: e.target.value } };
                            updateFormData('marketSegmentation.priorities', priorities);
                          }}
                          placeholder="0-10"
                          className="mt-1"
                        />
                        <p className="text-xs text-gray-500 mt-1">Rate the profitability potential (0-10 scale)</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6">
                <h4 className="font-semibold mb-4">Segment Heatmap</h4>
                {segmentData.length > 0 ? (
                  <div className="border rounded-lg p-4 bg-white">
                    <p className="text-sm text-gray-600 mb-4">
                      Visual representation of segment priorities. X-axis: Strategic Importance (1-5), Y-axis: Profitability Index (0-10)
                    </p>
                    <ChartComponent
                      type="scatter"
                      height={400}
                      data={{
                        datasets: segmentData.map((seg, idx) => ({
                          label: seg.name,
                          data: [{ 
                            x: Number(seg.strategicImportance), 
                            y: Number(seg.profitabilityIndex) 
                          }],
                          backgroundColor: `hsl(${idx * 60}, 70%, 50%)`,
                          borderColor: `hsl(${idx * 60}, 70%, 40%)`,
                          borderWidth: 2,
                          pointRadius: 10,
                          pointHoverRadius: 12
                        }))
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          x: {
                            type: 'linear',
                            position: 'bottom',
                            title: {
                              display: true,
                              text: 'Strategic Importance (1-5)'
                            },
                            min: 0,
                            max: 5,
                            ticks: {
                              stepSize: 1
                            }
                          },
                          y: {
                            type: 'linear',
                            title: {
                              display: true,
                              text: 'Profitability Index (0-10)'
                            },
                            min: 0,
                            max: 10,
                            ticks: {
                              stepSize: 1
                            }
                          }
                        },
                        plugins: {
                          legend: {
                            display: true,
                            position: 'right'
                          },
                          tooltip: {
                            callbacks: {
                              label: function(context) {
                                const point = context.raw;
                                return `${context.dataset.label}: Importance ${point.x}, Profitability ${point.y}`;
                              }
                            }
                          }
                        }
                      }}
                    />
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-gray-50">
                    <p className="text-gray-500">
                      Enter Strategic Importance and Profitability Index scores above to see the heatmap visualization.
                    </p>
                  </div>
                )}
              </div>
            </>
          )}
          {renderAISection(aiInsights, generatingAI, handleGenerateAI)}
        </div>
      );
    
    default:
      return null;
  }
};

// Brand Positioning Sections
const renderBrandPositioning = (sectionId, formData, updateFormData, aiInsights = '', generatingAI = false, handleGenerateAI = null, moduleTitle = '') => {
  const data = formData.brandPositioning || {};
  
  switch (sectionId) {
    case 'A': // Brand Identity
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Brand Identity</h3>
          <div className="space-y-4">
            <div>
              <Label>Brand Personality (Checkbox)</Label>
              <div className="mt-2 space-y-2">
                {['Premium', 'Innovative', 'Value-driven'].map((personality) => (
                  <label key={personality} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={(data.brandIdentity?.personality || []).includes(personality)}
                      onChange={(e) => {
                        const current = data.brandIdentity?.personality || [];
                        const updated = e.target.checked
                          ? [...current, personality]
                          : current.filter(item => item !== personality);
                        updateFormData('brandPositioning.brandIdentity.personality', updated);
                      }}
                      className="mr-2"
                    />
                    {personality}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <Label>Brand Tone</Label>
              <select
                value={data.brandIdentity?.tone || ''}
                onChange={(e) => updateFormData('brandPositioning.brandIdentity.tone', e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-lg"
              >
                <option value="">Select Tone</option>
                <option value="Formal">Formal</option>
                <option value="Friendly">Friendly</option>
                <option value="Bold">Bold</option>
              </select>
            </div>
          </div>
        </div>
      );
    
    case 'B': // Positioning Statement
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Positioning Statement</h3>
          <div className="space-y-4">
            <div>
              <Label>Target Customer</Label>
              <Textarea
                value={data.positioningStatement?.targetCustomer || ''}
                onChange={(e) => {
                  const statement = { ...(data.positioningStatement || {}), targetCustomer: e.target.value };
                  updateFormData('brandPositioning.positioningStatement', statement);
                }}
                placeholder="Describe target customer"
                rows={3}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Market Category</Label>
              <Input
                value={data.positioningStatement?.marketCategory || ''}
                onChange={(e) => {
                  const statement = { ...(data.positioningStatement || {}), marketCategory: e.target.value };
                  updateFormData('brandPositioning.positioningStatement', statement);
                }}
                placeholder="Enter market category"
                className="mt-1"
              />
            </div>
            <div>
              <Label>Brand Promise</Label>
              <Textarea
                value={data.positioningStatement?.brandPromise || ''}
                onChange={(e) => {
                  const statement = { ...(data.positioningStatement || {}), brandPromise: e.target.value };
                  updateFormData('brandPositioning.positioningStatement', statement);
                }}
                placeholder="Enter brand promise"
                rows={3}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Reason to Believe</Label>
              <Textarea
                value={data.positioningStatement?.reasonToBelieve || ''}
                onChange={(e) => {
                  const statement = { ...(data.positioningStatement || {}), reasonToBelieve: e.target.value };
                  updateFormData('brandPositioning.positioningStatement', statement);
                }}
                placeholder="Enter reason to believe"
                rows={3}
                className="mt-1"
              />
            </div>
          </div>
        </div>
      );
    
    case 'C': // Messaging Framework
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Messaging Framework</h3>
          <div className="space-y-4">
            <div>
              <Label>Core Message</Label>
              <Textarea
                value={data.messagingFramework?.coreMessage || ''}
                onChange={(e) => {
                  const framework = { ...(data.messagingFramework || {}), coreMessage: e.target.value };
                  updateFormData('brandPositioning.messagingFramework', framework);
                }}
                placeholder="Enter core message"
                rows={4}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Supporting Messages</Label>
              <div className="mt-2 space-y-2">
                {(data.messagingFramework?.supportingMessages || []).map((msg, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <Input
                      value={msg}
                      onChange={(e) => {
                        const updated = [...(data.messagingFramework?.supportingMessages || [])];
                        updated[idx] = e.target.value;
                        const framework = { ...(data.messagingFramework || {}), supportingMessages: updated };
                        updateFormData('brandPositioning.messagingFramework', framework);
                      }}
                      placeholder="Supporting message"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const updated = (data.messagingFramework?.supportingMessages || []).filter((_, i) => i !== idx);
                        const framework = { ...(data.messagingFramework || {}), supportingMessages: updated };
                        updateFormData('brandPositioning.messagingFramework', framework);
                      }}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const updated = [...(data.messagingFramework?.supportingMessages || []), ''];
                    const framework = { ...(data.messagingFramework || {}), supportingMessages: updated };
                    updateFormData('brandPositioning.messagingFramework', framework);
                  }}
                >
                  + Add Supporting Message
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Do's</Label>
                <div className="mt-2 space-y-2">
                  {(data.messagingFramework?.dos || []).map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Input
                        value={item}
                        onChange={(e) => {
                          const updated = [...(data.messagingFramework?.dos || [])];
                          updated[idx] = e.target.value;
                          const framework = { ...(data.messagingFramework || {}), dos: updated };
                          updateFormData('brandPositioning.messagingFramework', framework);
                        }}
                        placeholder="Do"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const updated = (data.messagingFramework?.dos || []).filter((_, i) => i !== idx);
                          const framework = { ...(data.messagingFramework || {}), dos: updated };
                          updateFormData('brandPositioning.messagingFramework', framework);
                        }}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const updated = [...(data.messagingFramework?.dos || []), ''];
                      const framework = { ...(data.messagingFramework || {}), dos: updated };
                      updateFormData('brandPositioning.messagingFramework', framework);
                    }}
                  >
                    + Add Do
                  </Button>
                </div>
              </div>
              <div>
                <Label>Don'ts</Label>
                <div className="mt-2 space-y-2">
                  {(data.messagingFramework?.donts || []).map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Input
                        value={item}
                        onChange={(e) => {
                          const updated = [...(data.messagingFramework?.donts || [])];
                          updated[idx] = e.target.value;
                          const framework = { ...(data.messagingFramework || {}), donts: updated };
                          updateFormData('brandPositioning.messagingFramework', framework);
                        }}
                        placeholder="Don't"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const updated = (data.messagingFramework?.donts || []).filter((_, i) => i !== idx);
                          const framework = { ...(data.messagingFramework || {}), donts: updated };
                          updateFormData('brandPositioning.messagingFramework', framework);
                        }}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const updated = [...(data.messagingFramework?.donts || []), ''];
                      const framework = { ...(data.messagingFramework || {}), donts: updated };
                      updateFormData('brandPositioning.messagingFramework', framework);
                    }}
                  >
                    + Add Don't
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    
    case 'D': // Competitive Perception
      const competitors = data.competitivePerception?.competitors || [];
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Competitive Perception</h3>
          <div className="space-y-4">
            <div>
              <Label>Competitors</Label>
              <div className="mt-2 space-y-2">
                {competitors.map((comp, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <Input
                      value={comp}
                      onChange={(e) => {
                        const updated = [...competitors];
                        updated[idx] = e.target.value;
                        const perception = { ...(data.competitivePerception || {}), competitors: updated };
                        updateFormData('brandPositioning.competitivePerception', perception);
                      }}
                      placeholder="Competitor name"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const updated = competitors.filter((_, i) => i !== idx);
                        const perception = { ...(data.competitivePerception || {}), competitors: updated };
                        updateFormData('brandPositioning.competitivePerception', perception);
                      }}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const updated = [...competitors, ''];
                    const perception = { ...(data.competitivePerception || {}), competitors: updated };
                    updateFormData('brandPositioning.competitivePerception', perception);
                  }}
                >
                  + Add Competitor
                </Button>
              </div>
            </div>
            {competitors.length > 0 && (
              <div>
                <h4 className="font-semibold mb-4">Brand vs Competitors (Radar Chart)</h4>
                <ChartComponent
                  type="radar"
                  data={{
                    labels: ['Price', 'Quality', 'Innovation', 'Service', 'Brand'],
                    datasets: [
                      {
                        label: 'Our Brand',
                        data: [4, 5, 4, 5, 4],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.2)'
                      },
                      ...competitors.map((comp, idx) => ({
                        label: comp || `Competitor ${idx + 1}`,
                        data: [3, 4, 3, 4, 3],
                        borderColor: `hsl(${idx * 60}, 70%, 50%)`,
                        backgroundColor: `hsla(${idx * 60}, 70%, 50%, 0.2)`
                      }))
                    ]
                  }}
                  height={400}
                />
              </div>
            )}
          </div>
          {renderAISection(aiInsights, generatingAI, handleGenerateAI)}
        </div>
      );
    
    default:
      return null;
  }
};

// Competitive Strategy Sections
const renderCompetitiveStrategy = (sectionId, formData, updateFormData, aiInsights = '', generatingAI = false, handleGenerateAI = null, moduleTitle = '') => {
  const data = formData.competitiveStrategy || {};
  const competitors = data.competitors || [];
  
  switch (sectionId) {
    case 'A': // Competitor Mapping
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Competitor Mapping</h3>
          <div className="space-y-4">
            {competitors.map((comp, idx) => (
              <div key={idx} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900">{comp.name || `Competitor ${idx + 1}`}</h4>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      const updated = competitors.filter((_, i) => i !== idx);
                      updateFormData('competitiveStrategy.competitors', updated);
                    }}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Competitor Name</Label>
                    <Input
                      value={comp.name || ''}
                      onChange={(e) => {
                        const updated = [...competitors];
                        updated[idx] = { ...updated[idx], name: e.target.value };
                        updateFormData('competitiveStrategy.competitors', updated);
                      }}
                      placeholder="Competitor name"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Market Share</Label>
                    <Input
                      type="number"
                      value={comp.marketShare || ''}
                      onChange={(e) => {
                        const updated = [...competitors];
                        updated[idx] = { ...updated[idx], marketShare: e.target.value };
                        updateFormData('competitiveStrategy.competitors', updated);
                      }}
                      placeholder="Market share %"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Price Positioning</Label>
                    <select
                      value={comp.pricePositioning || ''}
                      onChange={(e) => {
                        const updated = [...competitors];
                        updated[idx] = { ...updated[idx], pricePositioning: e.target.value };
                        updateFormData('competitiveStrategy.competitors', updated);
                      }}
                      className="w-full mt-1 px-3 py-2 border rounded-lg"
                    >
                      <option value="">Select Positioning</option>
                      <option value="Premium">Premium</option>
                      <option value="Mid-range">Mid-range</option>
                      <option value="Budget">Budget</option>
                    </select>
                  </div>
                  <div>
                    <Label>Channel Presence</Label>
                    <Input
                      value={comp.channelPresence || ''}
                      onChange={(e) => {
                        const updated = [...competitors];
                        updated[idx] = { ...updated[idx], channelPresence: e.target.value };
                        updateFormData('competitiveStrategy.competitors', updated);
                      }}
                      placeholder="Channels"
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>
            ))}
            <Button
              variant="outline"
              onClick={() => {
                const updated = [...competitors, { name: '', marketShare: '', pricePositioning: '', channelPresence: '' }];
                updateFormData('competitiveStrategy.competitors', updated);
              }}
            >
              + Add Competitor
            </Button>
          </div>
        </div>
      );
    
    case 'B': // Competitive Moves
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Competitive Moves</h3>
          <p className="text-sm text-gray-500">Track competitive moves for each competitor identified in Competitor Mapping</p>
          
          {competitors.length === 0 ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <p className="text-gray-500 mb-4">No competitors added yet. Please add competitors in Section A (Competitor Mapping) first.</p>
              <Button
                variant="outline"
                onClick={() => {
                  const updated = [...competitors, { name: '', marketShare: '', pricePositioning: '', channelPresence: '' }];
                  updateFormData('competitiveStrategy.competitors', updated);
                }}
              >
                + Add Competitor in Section A
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {competitors.map((comp, idx) => (
                <div key={idx} className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold">
                      {idx + 1}
                    </span>
                    {comp.name || `Competitor ${idx + 1}`}
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    {['Price Cuts', 'New Launches', 'Promotions', 'Expansion'].map((move) => {
                      const isChecked = data.competitiveMoves?.[idx]?.[move] || false;
                      return (
                        <label
                          key={move}
                          className={cn(
                            "flex items-center gap-3 px-4 py-3 rounded-lg border-2 cursor-pointer transition-all",
                            "hover:bg-white hover:border-gray-300",
                            isChecked
                              ? "bg-blue-50 border-blue-300 shadow-sm"
                              : "bg-white border-gray-200"
                          )}
                        >
                          <Checkbox
                            checked={isChecked}
                            onCheckedChange={(checked) => {
                              const moves = { ...(data.competitiveMoves || {}), [idx]: { ...(data.competitiveMoves?.[idx] || {}), [move]: checked } };
                              updateFormData('competitiveStrategy.competitiveMoves', moves);
                            }}
                          />
                          <span className={cn(
                            "text-sm font-medium flex-1",
                            isChecked ? "text-blue-900" : "text-gray-700"
                          )}>
                            {move}
                          </span>
                          {isChecked && (
                            <Check className="w-4 h-4 text-blue-600" />
                          )}
                        </label>
                      );
                    })}
                  </div>
                  <div className="mt-4">
                    <Label>Additional Notes</Label>
                    <Textarea
                      value={data.competitiveMoves?.[idx]?.notes || ''}
                      onChange={(e) => {
                        const moves = { ...(data.competitiveMoves || {}), [idx]: { ...(data.competitiveMoves?.[idx] || {}), notes: e.target.value } };
                        updateFormData('competitiveStrategy.competitiveMoves', moves);
                      }}
                      placeholder="Add notes about this competitor's moves..."
                      rows={2}
                      className="mt-1"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    
    case 'C': // Response Strategy
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">Response Strategy</h3>
          <p className="text-sm text-gray-500">Define how to respond to each competitor's moves</p>
          
          {competitors.length === 0 ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <p className="text-gray-500 mb-4">No competitors added yet. Please add competitors in Section A (Competitor Mapping) first.</p>
              <Button
                variant="outline"
                onClick={() => {
                  const updated = [...competitors, { name: '', marketShare: '', pricePositioning: '', channelPresence: '' }];
                  updateFormData('competitiveStrategy.competitors', updated);
                }}
              >
                + Add Competitor in Section A
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {competitors.map((comp, idx) => (
                <div key={idx} className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-sm font-bold">
                      {idx + 1}
                    </span>
                    {comp.name || `Competitor ${idx + 1}`}
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Strategy Type</Label>
                      <select
                        value={data.responseStrategies?.[idx]?.strategyType || ''}
                        onChange={(e) => {
                          const strategies = { ...(data.responseStrategies || {}), [idx]: { ...(data.responseStrategies?.[idx] || {}), strategyType: e.target.value } };
                          updateFormData('competitiveStrategy.responseStrategies', strategies);
                        }}
                        className="w-full mt-1 px-3 py-2 border rounded-lg bg-white"
                      >
                        <option value="">Select Strategy</option>
                        <option value="Defensive">Defensive - Protect market position</option>
                        <option value="Offensive">Offensive - Aggressively compete</option>
                        <option value="Neutral">Neutral - Monitor and adapt</option>
                      </select>
                    </div>
                    <div>
                      <Label>Risk Level</Label>
                      <select
                        value={data.responseStrategies?.[idx]?.riskLevel || ''}
                        onChange={(e) => {
                          const strategies = { ...(data.responseStrategies || {}), [idx]: { ...(data.responseStrategies?.[idx] || {}), riskLevel: e.target.value } };
                          updateFormData('competitiveStrategy.responseStrategies', strategies);
                        }}
                        className="w-full mt-1 px-3 py-2 border rounded-lg bg-white"
                      >
                        <option value="">Select Risk Level</option>
                        <option value="Low">Low Risk</option>
                        <option value="Medium">Medium Risk</option>
                        <option value="High">High Risk</option>
                      </select>
                    </div>
                  </div>
                  <div className="mt-4">
                    <Label>Counter-actions</Label>
                    <Textarea
                      value={data.responseStrategies?.[idx]?.counterActions || ''}
                      onChange={(e) => {
                        const strategies = { ...(data.responseStrategies || {}), [idx]: { ...(data.responseStrategies?.[idx] || {}), counterActions: e.target.value } };
                        updateFormData('competitiveStrategy.responseStrategies', strategies);
                      }}
                      placeholder="Describe specific counter-actions to take (e.g., price matching, product differentiation, marketing campaigns)..."
                      rows={4}
                      className="mt-1"
                    />
                  </div>
                  <div className="mt-4">
                    <Label>Timeline</Label>
                    <Input
                      value={data.responseStrategies?.[idx]?.timeline || ''}
                      onChange={(e) => {
                        const strategies = { ...(data.responseStrategies || {}), [idx]: { ...(data.responseStrategies?.[idx] || {}), timeline: e.target.value } };
                        updateFormData('competitiveStrategy.responseStrategies', strategies);
                      }}
                      placeholder="e.g., Immediate, Q1 2025, 3 months"
                      className="mt-1"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    
    case 'D': // SWOT Comparison
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">SWOT Comparison</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Strengths</Label>
              <Textarea
                value={data.swot?.strengths || ''}
                onChange={(e) => {
                  const swot = { ...(data.swot || {}), strengths: e.target.value };
                  updateFormData('competitiveStrategy.swot', swot);
                }}
                placeholder="Enter strengths"
                rows={4}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Weaknesses</Label>
              <Textarea
                value={data.swot?.weaknesses || ''}
                onChange={(e) => {
                  const swot = { ...(data.swot || {}), weaknesses: e.target.value };
                  updateFormData('competitiveStrategy.swot', swot);
                }}
                placeholder="Enter weaknesses"
                rows={4}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Opportunities</Label>
              <Textarea
                value={data.swot?.opportunities || ''}
                onChange={(e) => {
                  const swot = { ...(data.swot || {}), opportunities: e.target.value };
                  updateFormData('competitiveStrategy.swot', swot);
                }}
                placeholder="Enter opportunities"
                rows={4}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Threats</Label>
              <Textarea
                value={data.swot?.threats || ''}
                onChange={(e) => {
                  const swot = { ...(data.swot || {}), threats: e.target.value };
                  updateFormData('competitiveStrategy.swot', swot);
                }}
                placeholder="Enter threats"
                rows={4}
                className="mt-1"
              />
            </div>
          </div>
          {renderAISection(aiInsights, generatingAI, handleGenerateAI)}
        </div>
      );
    
    default:
      return null;
  }
};

export default MarketingStrategyModal;

