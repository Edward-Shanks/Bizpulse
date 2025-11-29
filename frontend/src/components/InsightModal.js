import React, { useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { X, Send, Sparkles, TrendingUp, AlertCircle, Lightbulb, ArrowRight, CheckCircle, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import ChartComponent from '@/components/ChartComponent';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const InsightModal = ({ isOpen, onClose, chartTitle, insights, recommendations, onExploreDeep, context, apiUrl }) => {
  const { token } = useAuth();
  const INSIGHTS_API = apiUrl || process.env.REACT_APP_INSIGHTS_URL || 'http://localhost:8005';
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      content: `I'm analyzing ${chartTitle}. What would you like to know about this data?`
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastPivot, setLastPivot] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [dynamicRecommendations, setDynamicRecommendations] = useState([]);
  const [dynamicFollowUps, setDynamicFollowUps] = useState([]);
  const sessionId = `insight-${Date.now()}`;

  if (!isOpen) return null;

  // AI-generated recommendations based on chart type
  const defaultRecommendations = [
    {
      type: 'positive',
      icon: CheckCircle,
      title: 'Strong Sales Growth',
      description: 'Sales have increased by 25% over the last quarter, showing positive momentum.',
      action: 'Continue current strategy',
      color: { bg: '#d1fae5', border: '#10b981', text: '#065f46', icon: '#10b981' }
    },
    {
      type: 'warning',
      icon: AlertTriangle,
      title: 'Profit Margin Declining',
      description: 'While sales are up, profit margins have decreased by 8%, indicating rising costs.',
      action: 'Review operational expenses',
      color: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', icon: '#f59e0b' }
    },
    {
      type: 'urgent',
      icon: AlertCircle,
      title: 'Immediate Action Required',
      description: 'Customer acquisition cost has spiked 40% this month. Immediate review needed.',
      action: 'Schedule urgent review',
      color: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', icon: '#ef4444' }
    }
  ];

  // Use dynamic recommendations from API if available, otherwise use props or defaults
  const recommendationsToUse = dynamicRecommendations.length > 0 
    ? dynamicRecommendations 
    : (recommendations && recommendations.length > 0 ? recommendations : []);
  
  // Convert string recommendations to proper format if needed
  const aiRecommendations = recommendationsToUse.length > 0
    ? recommendationsToUse.map((rec, index) => {
        if (typeof rec === 'string') {
          // Convert string to recommendation object
          const colors = [
            { bg: '#d1fae5', border: '#10b981', text: '#065f46', icon: '#10b981' },
            { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', icon: '#f59e0b' },
            { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af', icon: '#3b82f6' },
            { bg: '#e0e7ff', border: '#6366f1', text: '#312e81', icon: '#6366f1' },
            { bg: '#fce7f3', border: '#ec4899', text: '#831843', icon: '#ec4899' }
          ];
          return {
            type: 'info',
            icon: Lightbulb,
            title: `Recommendation ${index + 1}`,
            description: rec,
            action: 'Review',
            color: colors[index % colors.length]
          };
        }
        // If it's already an object, ensure it has color property
        return {
          ...rec,
          color: rec.color || { bg: '#d1fae5', border: '#10b981', text: '#065f46', icon: '#10b981' }
        };
      })
    : defaultRecommendations;

  // Suggested prompts based on chart context
  const suggestedPrompts = [
    'Show trends',
    'Identify issues',
    'Recommendations',
    'Forecast'
  ];

  // Use dynamic follow-ups from API if available, otherwise use defaults
  const followUpPrompts = dynamicFollowUps.length > 0 
    ? dynamicFollowUps 
    : [
        'Show sales overview',
        'Analyze profitability',
        'Customer insights',
        'Channel performance'
      ];

  // Simulated streaming function to display text word by word
  const streamMessage = (fullText, onComplete) => {
    const words = fullText.split(' ');
    let currentText = '';
    let wordIndex = 0;

    const streamInterval = setInterval(() => {
      if (wordIndex < words.length) {
        currentText += (wordIndex > 0 ? ' ' : '') + words[wordIndex];
        setStreamingMessage(currentText);
        wordIndex++;
      } else {
        clearInterval(streamInterval);
        setStreamingMessage('');
        onComplete();
      }
    }, 30); // 30ms delay between words for smooth typing effect
  };

  const handleSendMessage = async (messageText = null) => {
    const msgToSend = messageText || input.trim();
    if (!msgToSend) return;

    const userMessage = { role: 'user', content: msgToSend };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build conversation history from previous messages
      const conversationHistory = messages.slice(1).map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      const payload = {
        message: msgToSend,
        chart_title: chartTitle,
        context: {
          monthlyData: context?.monthlyData || [],
          selectedYears: context?.selectedYears || [],
          selectedMonths: context?.selectedMonths || [],
          selectedBusinesses: context?.selectedBusinesses || []
        },
        session_id: sessionId,
        conversation_history: conversationHistory
      };

      // Determine the correct endpoint based on API URL
      // If apiUrl is provided (from Customer Deep Intelligence), use the backend API
      // Note: apiUrl already includes /api prefix (e.g., http://localhost:8000/api)
      // Otherwise, use the external insights API
      let endpoint;
      if (apiUrl) {
        // apiUrl is like "http://localhost:8000/api", so we append the path
        // Use view-insights/chat endpoint for Customer Deep Intelligence view insights modal
        endpoint = `${apiUrl}/analytics/customer-insights/view-insights/chat`;
      } else {
        endpoint = `${INSIGHTS_API}/insights/chat`;
      }
      
      console.log('InsightModal - Making API call to:', endpoint);
      console.log('InsightModal - Payload:', payload);
      console.log('InsightModal - API URL:', INSIGHTS_API);
      console.log('InsightModal - apiUrl prop:', apiUrl);
      
      const response = await axios.post(endpoint, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const fullResponse = response.data?.response || 'No response';
      const pivot = response?.data?.data?.pivot_table || [];
      setLastPivot(Array.isArray(pivot) ? pivot : []);
      
      // Extract dynamic recommendations and follow-up questions from API response
      const apiRecommendations = response?.data?.data?.recommendations || [];
      const apiFollowUps = response?.data?.data?.follow_up_questions || [];
      
      // Update dynamic recommendations and follow-ups
      if (apiRecommendations.length > 0) {
        setDynamicRecommendations(apiRecommendations);
      }
      if (apiFollowUps.length > 0) {
        setDynamicFollowUps(apiFollowUps);
      }
      
      // Start streaming the message word by word
      setLoading(false);
      streamMessage(fullResponse, () => {
        // When streaming completes, add the full message to chat
        const aiMessage = { role: 'ai', content: fullResponse };
        setMessages((prev) => [...prev, aiMessage]);
      });
    } catch (error) {
      console.error('InsightModal API Error:', error);
      console.error('Error details:', error.response?.data || error.message);
      toast.error('AI Assistant is unavailable');
      setLoading(false);
      const errorMessage = {
        role: 'ai',
        content: error.response?.data?.detail || error.message || 'Sorry, I am currently unavailable. Please try again later.'
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handlePromptClick = (prompt) => {
    handleSendMessage(prompt);
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4" 
      style={{ background: 'rgba(0, 0, 0, 0.5)' }} 
      onClick={onClose}
    >
      <div
        className="w-full max-w-6xl bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
        data-testid="insight-modal"
      >
        {/* Header */}
        <div
          className="p-5 border-b flex items-center justify-between rounded-t-2xl"
          style={{ background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)' }}
        >
          <div>
            <h3 className="text-white font-bold text-xl" style={{ fontFamily: 'Space Grotesk' }}>
              {chartTitle} - Insights & Analysis
            </h3>
            <p className="text-sm text-blue-100">AI-powered recommendations and chat analysis</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white/20 rounded-lg p-2 transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Two Column Layout */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Column - Recommendations */}
          <div className="w-2/5 border-r bg-gray-50 flex flex-col">
            <div className="p-5">
              <h3 className="text-lg font-bold text-gray-900 mb-1" style={{ fontFamily: 'Space Grotesk' }}>
                Recommendations
              </h3>
            </div>

            <ScrollArea className="flex-1 px-5 pb-5">
              <div className="space-y-4">
                {aiRecommendations.map((rec, idx) => {
                  const Icon = rec.icon;
                  return (
                    <div
                      key={idx}
                      className="rounded-lg p-4 border-l-4"
                      style={{
                        background: rec.color.bg,
                        borderColor: rec.color.border
                      }}
                    >
                      <div className="flex items-start gap-3">
                        <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: rec.color.icon }} />
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm mb-1" style={{ color: rec.color.text }}>
                            {rec.title}
                          </h4>
                          <p className="text-xs mb-3" style={{ color: rec.color.text, opacity: 0.8 }}>
                            {rec.description}
                          </p>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs h-8 border"
                            style={{ 
                              borderColor: rec.color.border,
                              color: rec.color.text
                            }}
                            onClick={() => handleSendMessage(rec.action)}
                          >
                            {rec.action}
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          </div>

          {/* Right Column - Chat Analysis */}
          <div className="flex-1 flex flex-col bg-white">
            <div className="p-5">
              <h3 className="text-lg font-bold text-gray-900 mb-1" style={{ fontFamily: 'Space Grotesk' }}>
                Chat Analysis
              </h3>
            </div>

            {/* Chat Messages */}
            <ScrollArea className="flex-1 px-5">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`mb-4 ${msg.role === 'user' ? 'flex justify-end' : ''}`}
                >
                  {msg.role === 'ai' && (
                    <div className="bg-gray-100 rounded-lg p-4 border border-gray-200">
                      <div className="text-sm text-gray-800 mb-3 prose prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                      
                      {/* Suggested Prompts */}
                      {idx === 0 && (
                        <div className="grid grid-cols-1 gap-2">
                          {suggestedPrompts.map((prompt, pidx) => (
                            <button
                              key={pidx}
                              onClick={() => handlePromptClick(prompt)}
                              className="text-left px-3 py-2 rounded text-sm transition hover:bg-amber-100"
                              style={{ background: '#fef3c7', color: '#92400e' }}
                            >
                              {prompt}
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {/* Follow-up prompts after first response */}
                      {idx > 1 && idx === messages.length - 1 && msg.role === 'ai' && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-xs text-gray-600 mb-2">
                            I can help you analyze your business data. Try asking about sales trends, profit margins, customer performance, or brand analysis. What would you like to know?
                          </p>
                          <div className="grid grid-cols-2 gap-2">
                            {followUpPrompts.map((prompt, pidx) => (
                              <button
                                key={pidx}
                                onClick={() => handlePromptClick(prompt)}
                                className="text-left px-3 py-2 rounded text-xs transition hover:bg-amber-100"
                                style={{ background: '#fef3c7', color: '#92400e' }}
                              >
                                {prompt}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {msg.role === 'user' && (
                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg px-4 py-3 max-w-[80%]">
                      <p className="text-sm">{msg.content}</p>
                    </div>
                  )}
                </div>
              ))}

              {/* Visualization from AI data */}
              {lastPivot && lastPivot.length > 0 && (
                <div className="mb-6">
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <h4 className="text-sm font-semibold mb-3 text-gray-800">Visuals from AI data</h4>
                    <AIDataVisuals pivot={lastPivot} />
                  </div>
                </div>
              )}

              {loading && (
                <div className="mb-4">
                  <div className="bg-gradient-to-r from-amber-50 to-orange-50 px-6 py-4 rounded-lg border border-amber-200 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-amber-600 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-amber-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-amber-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                      <span className="text-amber-700 font-medium text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Streaming message */}
              {streamingMessage && (
                <div className="mb-4">
                  <div className="bg-gray-100 rounded-lg p-4 border border-gray-200">
                    <div className="text-sm text-gray-800 prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {streamingMessage}
                      </ReactMarkdown>
                      <span className="inline-block w-2 h-4 bg-blue-600 ml-1 animate-pulse" />
                    </div>
                  </div>
                </div>
              )}
            </ScrollArea>

            {/* Chat Input */}
            <div className="p-5 border-t bg-white">
              <div className="flex gap-3">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !loading && handleSendMessage()}
                  placeholder="Ask about this chart..."
                  disabled={loading}
                  className="flex-1"
                  data-testid="insight-chat-input"
                />
                <Button
                  onClick={() => handleSendMessage()}
                  disabled={loading || !input.trim()}
                  className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white"
                  data-testid="insight-send-button"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InsightModal;

// Lightweight in-file component to render a table and a simple chart from pivot data
const AIDataVisuals = ({ pivot }) => {
  const { labels, datasetLabel, datasetValues } = useMemo(() => {
    if (!pivot || pivot.length === 0) return { labels: [], datasetLabel: '', datasetValues: [] };
    const sample = pivot[0];
    const labelCandidates = ['Year', 'Month Name', 'Business', 'Brand', 'Category', 'Customer', 'Channel'];
    const valueCandidates = ['gSales', 'fGP', 'Cases'];
    
    // Find all available label candidates
    const availableLabels = labelCandidates.filter((k) => Object.prototype.hasOwnProperty.call(sample, k));
    
    // If multiple category columns exist (e.g., Business + Channel), combine them
    let labels;
    if (availableLabels.length > 1 && !availableLabels.includes('Year') && !availableLabels.includes('Month Name')) {
      // Combine category columns to create unique labels (e.g., "Business Channel" or "Brand Category")
      labels = pivot.map((r) => {
        const combined = availableLabels.slice(0, 2).map(k => String(r[k])).join(' ');
        return combined;
      });
    } else {
      // Use first available label or fallback to first key
      const labelKey = labelCandidates.find((k) => Object.prototype.hasOwnProperty.call(sample, k)) || Object.keys(sample)[0];
      labels = pivot.map((r) => String(r[labelKey]));
    }
    
    const valueKey = valueCandidates.find((k) => Object.prototype.hasOwnProperty.call(sample, k)) || Object.keys(sample).find(k => typeof sample[k] === 'number');
    const datasetValues = pivot.map((r) => Number(r[valueKey] || 0));
    return { labels, datasetLabel: valueKey || 'Value', datasetValues };
  }, [pivot]);

  const chartData = useMemo(() => ({
    labels,
    datasets: [
      {
        label: datasetLabel,
        data: datasetValues,
        backgroundColor: 'rgba(59, 130, 246, 0.3)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1.5,
      },
    ],
  }), [labels, datasetLabel, datasetValues]);

  const chartOptions = useMemo(() => ({
    responsive: true,
    plugins: {
      legend: { display: true },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const v = ctx.parsed.y;
            if (Math.abs(v) >= 1_000_000) return `€${(v/1_000_000).toFixed(1)}M`;
            if (Math.abs(v) >= 1_000) return `€${(v/1_000).toFixed(1)}k`;
            return `€${v.toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      y: {
        ticks: {
          callback: (v) => {
            if (Math.abs(v) >= 1_000_000) return `€${(v/1_000_000).toFixed(1)}M`;
            if (Math.abs(v) >= 1_000) return `€${(v/1_000).toFixed(1)}k`;
            return `€${v}`;
          },
        },
      },
    },
  }), []);

  return (
    <div className="space-y-4">
      <div className="overflow-auto border rounded">
        <table className="min-w-full text-xs">
          <thead className="bg-gray-50 text-gray-700">
            <tr>
              {Object.keys(pivot[0]).slice(0, 6).map((k) => (
                <th key={k} className="px-3 py-2 text-left font-medium">{k}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pivot.slice(0, 10).map((row, idx) => (
              <tr key={idx} className={idx % 2 ? 'bg-white' : 'bg-gray-50'}>
                {Object.keys(pivot[0]).slice(0, 6).map((k) => (
                  <td key={k} className="px-3 py-2 whitespace-nowrap text-gray-800">
                    {typeof row[k] === 'number'
                      ? Number(row[k]).toLocaleString('en-US')
                      : String(row[k])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {labels.length > 0 && datasetValues.length > 0 && (
        <ChartComponent type="bar" data={chartData} options={chartOptions} />
      )}
    </div>
  );
};