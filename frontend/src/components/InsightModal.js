import React, { useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth, API } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { X, Send, Sparkles, TrendingUp, AlertCircle, Lightbulb, ArrowRight, CheckCircle, AlertTriangle, RotateCcw } from 'lucide-react';
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
      content: `I'm analyzing ${chartTitle}. What would you like to know about this data?`,
      pivot_table: [] // Store pivot data with each message
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastPivot, setLastPivot] = useState([]);
  const [pivotKey, setPivotKey] = useState(0); // Key to force re-render when pivot data changes
  const [streamingMessage, setStreamingMessage] = useState('');
  const [dynamicRecommendations, setDynamicRecommendations] = useState([]);
  const [dynamicFollowUps, setDynamicFollowUps] = useState([]);
  const [sessionId, setSessionId] = useState(`insight-${Date.now()}`);
  const [isContextCleared, setIsContextCleared] = useState(false);

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
    // Ensure messageText is a string, not an event object
    let msgToSend;
    if (messageText && typeof messageText === 'string') {
      msgToSend = messageText;
    } else {
      msgToSend = input.trim();
    }
    if (!msgToSend || typeof msgToSend !== 'string') return;

    // CRITICAL: Clear lastPivot when sending a new message to avoid stale data
    setLastPivot([]);
    setPivotKey(prev => prev + 1); // Increment key to force re-render
    
    // Ensure user message content is always a string
    const safeUserContent = typeof msgToSend === 'string' ? msgToSend : String(msgToSend || '');
    const userMessage = { role: 'user', content: safeUserContent, pivot_table: [] };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build conversation history from previous messages
      // If context was cleared, send empty history to ensure backend doesn't use old context
      const conversationHistory = isContextCleared ? [] : messages.slice(1).map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      const payload = {
        message: msgToSend,
        chart_title: chartTitle,
        context: {
          monthlyData: context?.monthlyData || context?.monthlyTrend || [],
          selectedYears: context?.selectedYears || [],
          selectedMonths: context?.selectedMonths || [],
          selectedBusinesses: context?.selectedBusinesses || [],
          selectedChannels: context?.selectedChannels || [],
          yearlyData: context?.yearlyData || [],
          businessData: context?.businessData || [],
          channelData: context?.channelData || [],
          monthlyTrend: context?.monthlyTrend || [],
          totalRevenue: context?.totalRevenue,
          totalUnits: context?.totalUnits,
          totalProfit: context?.totalProfit,
          avgPrice: context?.avgPrice
        },
        session_id: sessionId,
        conversation_history: conversationHistory
      };

      // Determine the correct endpoint based on API URL
      // Priority: 1) apiUrl prop (Customer Deep Intelligence), 2) Backend API (MongoDB-based), 3) External insights API
      let endpoint;
      if (apiUrl) {
        // apiUrl is like "http://localhost:8000/api", so we append the path
        // Use view-insights/chat endpoint for Customer Deep Intelligence view insights modal
        endpoint = `${apiUrl}/analytics/customer-insights/view-insights/chat`;
      } else if (API) {
        // Use backend MongoDB-based insights API for all screens (Business Compass, Brands, Customers, Categories, Sales Analysis)
        endpoint = `${API}/insights/chat`;
      } else {
        // Fallback to external insights API
        endpoint = `${INSIGHTS_API}/insights/chat`;
      }
      
      console.log('InsightModal - Making API call to:', endpoint);
      console.log('InsightModal - Payload:', payload);
      console.log('InsightModal - API URL:', INSIGHTS_API);
      console.log('InsightModal - apiUrl prop:', apiUrl);
      
      const response = await axios.post(endpoint, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Check if question needs clarification
      const needsClarification = response.data?.needs_clarification || false;
      let suggestedQuestions = response.data?.suggested_questions || [];
      
      console.log('🔍 Full API Response:', response.data);
      console.log('🔍 Clarification check:', { 
        needsClarification, 
        suggestedQuestionsCount: suggestedQuestions?.length || 0, 
        suggestedQuestions,
        suggestedQuestionsType: typeof suggestedQuestions,
        isArray: Array.isArray(suggestedQuestions)
      });
      
      // Ensure suggestedQuestions is always an array
      if (!Array.isArray(suggestedQuestions)) {
        if (suggestedQuestions && typeof suggestedQuestions === 'object') {
          // If it's an object, try to convert to array
          suggestedQuestions = Object.values(suggestedQuestions);
        } else if (typeof suggestedQuestions === 'string') {
          // If it's a string, try to parse it
          try {
            const parsed = JSON.parse(suggestedQuestions);
            suggestedQuestions = Array.isArray(parsed) ? parsed : [];
          } catch {
            suggestedQuestions = [suggestedQuestions];
          }
        } else {
          suggestedQuestions = [];
        }
      }
      
      if (needsClarification) {
        // Question needs clarification - show suggested questions
        setLoading(false);
        const clarificationResponse = response.data?.response || 'I want to make sure I understand your question correctly. Could you please select one of these clarified versions, or rewrite your question?';
        const clarificationMessage = {
          role: 'ai',
          content: clarificationResponse,
          needs_clarification: true,
          suggested_questions: suggestedQuestions, // Now guaranteed to be an array
          messageId: Date.now()
        };
        console.log('🔍 Adding clarification message:', clarificationMessage);
        console.log('🔍 Suggested questions array:', suggestedQuestions);
        setMessages((prev) => {
          const newMessages = [...prev, clarificationMessage];
          console.log('🔍 Updated messages array length:', newMessages.length);
          console.log('🔍 Last message:', newMessages[newMessages.length - 1]);
          return newMessages;
        });
        return; // Don't process further, just show suggestions
      }
      
      // Ensure response is always a string
      let fullResponse = response.data?.response || 'No response';
      if (typeof fullResponse !== 'string') {
        // If response is not a string, try to convert it
        if (fullResponse && typeof fullResponse === 'object') {
          fullResponse = JSON.stringify(fullResponse);
        } else {
          fullResponse = String(fullResponse || 'No response');
        }
      }
      const pivot = response?.data?.data?.pivot_table || [];
      const pivotArray = Array.isArray(pivot) ? pivot : [];
      
      // CRITICAL: Log pivot data for debugging
      console.log('🔍 InsightModal - Received pivot data:', {
        length: pivotArray.length,
        firstItem: pivotArray[0],
        question: msgToSend
      });
      
      // CRITICAL: Update lastPivot with fresh data for this response
      // Increment pivotKey FIRST to force component unmount, then update pivot data
      setPivotKey(prev => {
        const newKey = prev + 1;
        console.log('🔄 InsightModal - Incrementing pivotKey to:', newKey);
        // Update pivot data after key change
        setTimeout(() => {
          setLastPivot(pivotArray);
          console.log('✅ InsightModal - Updated lastPivot with', pivotArray.length, 'items for question:', msgToSend);
        }, 10);
        return newKey;
      });
      
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
      // Reset context cleared flag after sending first message after clear
      if (isContextCleared) {
        setIsContextCleared(false);
      }
      streamMessage(fullResponse, () => {
        // When streaming completes, add the full message to chat with pivot data
        // Ensure content is always a string
        const safeContent = typeof fullResponse === 'string' ? fullResponse : String(fullResponse || 'No response');
        const aiMessage = { 
          role: 'ai', 
          content: safeContent,
          pivot_table: pivotArray, // Store pivot data with this message
          messageId: Date.now() // Unique ID for this message to force re-render
        };
        setMessages((prev) => [...prev, aiMessage]);
        // CRITICAL: Update lastPivot AFTER message is added to ensure visualization updates
        setLastPivot(pivotArray);
        setPivotKey(prev => prev + 1);
      });
    } catch (error) {
      console.error('InsightModal API Error:', error);
      console.error('Error details:', error.response?.data || error.message);
      toast.error('AI Assistant is unavailable');
      setLoading(false);
      // Ensure error message content is always a string
      let errorContent = error.response?.data?.detail || error.message || 'Sorry, I am currently unavailable. Please try again later.';
      if (typeof errorContent !== 'string') {
        errorContent = String(errorContent || 'Sorry, I am currently unavailable. Please try again later.');
      }
      const errorMessage = {
        role: 'ai',
        content: errorContent
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handlePromptClick = (prompt) => {
    if (typeof prompt === 'string') {
      handleSendMessage(prompt);
    }
  };

  const handleClearContext = () => {
    // Reset messages to initial state
    setMessages([
      {
        role: 'ai',
        content: `I'm analyzing ${chartTitle}. What would you like to know about this data?`,
        pivot_table: []
      }
    ]);
    // Clear pivot data
    setLastPivot([]);
    setPivotKey(0);
    // Clear dynamic recommendations and follow-ups
    setDynamicRecommendations([]);
    setDynamicFollowUps([]);
    // Generate new session ID to ensure fresh conversation
    setSessionId(`insight-${Date.now()}`);
    // Set flag to ensure next message sends empty conversation history
    setIsContextCleared(true);
    // Show confirmation toast
    toast.success('Previous context cleared. Starting fresh conversation.');
  };

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center p-4" 
      style={{ background: 'rgba(0, 0, 0, 0.5)', zIndex: 9999 }} 
      onClick={onClose}
    >
      <div
        className="w-full max-w-6xl bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
        data-testid="insight-modal"
        style={{ zIndex: 10000 }}
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
          <div className="flex items-center gap-2">
            <button
              onClick={handleClearContext}
              className="text-white hover:bg-white/20 rounded-lg p-2 transition flex items-center gap-2"
              title="Clear Previous Context"
            >
              <RotateCcw className="w-5 h-5" />
              <span className="text-sm hidden sm:inline">Clear Context</span>
            </button>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-lg p-2 transition"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
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
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              if (rec.action && typeof rec.action === 'string') {
                                handleSendMessage(rec.action);
                              }
                            }}
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
            <div className="p-5 border-b">
              <h3 className="text-lg font-bold text-gray-900 mb-1" style={{ fontFamily: 'Space Grotesk' }}>
                VectorDeep AI - Business Intelligence Assistant
              </h3>
              <p className="text-xs text-gray-600">Ask questions about your data</p>
            </div>

            {/* Chat Messages */}
            <ScrollArea className="flex-1 px-5">
              {messages.map((msg, idx) => {
                // Ensure content is a string, not an event object or any other type
                let content = '';
                try {
                  if (typeof msg.content === 'string') {
                    content = msg.content;
                  } else if (msg.content && typeof msg.content === 'object') {
                    // If it's an object (like an event), don't render it
                    console.error('Invalid content type in message:', typeof msg.content, msg.content);
                    content = '[Invalid message content - please refresh the page]';
                  } else {
                    content = String(msg.content || '');
                  }
                } catch (e) {
                  console.error('Error processing message content:', e);
                  content = '[Error processing message]';
                }
                
                // Debug: Log message object for clarification messages
                if (msg.needs_clarification) {
                  console.log('🔍 Rendering clarification message:', {
                    idx,
                    needs_clarification: msg.needs_clarification,
                    suggested_questions: msg.suggested_questions,
                    suggested_questions_type: typeof msg.suggested_questions,
                    is_array: Array.isArray(msg.suggested_questions),
                    length: msg.suggested_questions?.length,
                    full_message: msg
                  });
                }
                
                return (
                  <div
                    key={idx}
                    className={`mb-4 ${msg.role === 'user' ? 'flex justify-end' : ''}`}
                  >
                    {msg.role === 'ai' && (
                      <div className="bg-gray-100 rounded-lg p-4 border border-gray-200">
                        <div className="text-sm text-gray-800 mb-3 prose prose-sm max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                          </ReactMarkdown>
                        </div>
                      
                      {/* Suggested Questions for Clarification */}
                      {(() => {
                        const hasClarification = msg.needs_clarification === true;
                        const hasSuggestions = msg.suggested_questions && Array.isArray(msg.suggested_questions) && msg.suggested_questions.length > 0;
                        console.log(`🔍 Message ${idx} clarification check:`, {
                          hasClarification,
                          hasSuggestions,
                          needs_clarification: msg.needs_clarification,
                          suggested_questions: msg.suggested_questions,
                          suggested_questions_length: msg.suggested_questions?.length
                        });
                        return hasClarification && hasSuggestions;
                      })() && (
                        <div className="mt-4 space-y-2">
                          <p className="text-xs font-semibold text-gray-600 mb-2">Did you mean:</p>
                          <div className="grid grid-cols-1 gap-2">
                            {msg.suggested_questions.map((suggestedQ, sqIdx) => {
                              console.log('🔍 Rendering suggestion:', suggestedQ);
                              return (
                                <button
                                  key={sqIdx}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    if (suggestedQ && typeof suggestedQ === 'string') {
                                      handleSendMessage(suggestedQ);
                                    }
                                  }}
                                  className="text-left px-4 py-3 rounded-lg text-sm transition-all hover:shadow-md border-2 border-blue-200 hover:border-blue-400 bg-white hover:bg-blue-50"
                                  style={{ color: '#1e40af' }}
                                >
                                  <div className="flex items-start gap-2">
                                    <ArrowRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                    <span className="flex-1">{suggestedQ}</span>
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      
                      {/* Suggested Prompts */}
                      {idx === 0 && !msg.needs_clarification && (
                        <div className="grid grid-cols-1 gap-2">
                          {suggestedPrompts.map((prompt, pidx) => (
                            <button
                              key={pidx}
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                if (prompt && typeof prompt === 'string') {
                                  handlePromptClick(prompt);
                                }
                              }}
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
                            I can help you analyze your business data. What would you like to know?
                          </p>
                          <div className="grid grid-cols-2 gap-2">
                            {followUpPrompts.map((prompt, pidx) => (
                              <button
                                key={pidx}
                                onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                if (prompt && typeof prompt === 'string') {
                                  handlePromptClick(prompt);
                                }
                              }}
                                className="text-left px-3 py-2 rounded text-xs transition hover:bg-amber-200 hover:shadow-sm cursor-pointer"
                                style={{ background: '#fef3c7', color: '#92400e', border: '1px solid #fbbf24' }}
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
                        <p className="text-sm">{typeof content === 'string' ? content : String(content || '')}</p>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Visualization from AI data - Show only for the most recent AI message */}
              {/* CRITICAL: Use pivotKey AND pivot data hash to force re-render */}
              {lastPivot && lastPivot.length > 0 && messages.length > 0 && (
                <div className="mb-6" key={`pivot-container-${pivotKey}-${lastPivot.length}`}>
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <h4 className="text-sm font-semibold mb-3 text-gray-800">Visuals from AI data</h4>
                    {/* CRITICAL: Create unique key from pivotKey + first item's brand/revenue to force re-render */}
                    {lastPivot[0] && (
                      <AIDataVisuals 
                        pivot={lastPivot} 
                        key={`pivot-${pivotKey}-${lastPivot.length}-${lastPivot[0].Brand || lastPivot[0].Category || lastPivot[0].Customer || 'default'}-${lastPivot[0].Revenue || 0}`} 
                      />
                    )}
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
              {streamingMessage && typeof streamingMessage === 'string' && (
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
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !loading) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Ask about this chart..."
                  disabled={loading}
                  className="flex-1"
                  data-testid="insight-chat-input"
                />
                <Button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleSendMessage();
                  }}
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
  const { labels, datasetLabel, datasetValues, chartType, secondaryDataset } = useMemo(() => {
    if (!pivot || pivot.length === 0) return { labels: [], datasetLabel: '', datasetValues: [], chartType: 'bar', secondaryDataset: null };
    const sample = pivot[0];
    
    // Updated label candidates to match backend data
    const labelCandidates = ['Year', 'Month_Name', 'Month Name', 'Business', 'Brand', 'Category', 'Customer', 'Channel'];
    // Updated value candidates to match backend data
    const valueCandidates = ['Revenue', 'Gross_Profit', 'Units', 'Margin_%', 'gSales', 'fGP', 'Cases'];
    
    // Find all available label candidates
    const availableLabels = labelCandidates.filter((k) => Object.prototype.hasOwnProperty.call(sample, k));
    
    // Determine labels based on data structure
    let labels;
    let chartType = 'bar'; // Default chart type
    
    // If we have time-based data (Year or Month), use line chart
    if (availableLabels.includes('Year') || availableLabels.includes('Month_Name') || availableLabels.includes('Month Name')) {
      chartType = 'line';
      const timeKey = availableLabels.find(k => ['Year', 'Month_Name', 'Month Name'].includes(k));
      labels = pivot.map((r) => String(r[timeKey] || ''));
    } else if (availableLabels.length > 1) {
      // Combine category columns for unique labels
      labels = pivot.map((r) => {
        const combined = availableLabels.slice(0, 2).map(k => String(r[k] || '')).join(' - ');
        return combined;
      });
    } else {
      // Use first available label
      const labelKey = availableLabels[0] || Object.keys(sample).find(k => typeof sample[k] !== 'number');
      labels = pivot.map((r) => String(r[labelKey] || ''));
    }
    
    // Determine value column - prioritize Revenue, then Gross_Profit, then Units
    const valueKey = valueCandidates.find((k) => Object.prototype.hasOwnProperty.call(sample, k)) 
      || Object.keys(sample).find(k => typeof sample[k] === 'number' && !k.includes('%'));
    const datasetValues = pivot.map((r) => Number(r[valueKey] || 0));
    
    // If we have both Revenue and Gross_Profit, create a comparison chart
    let secondaryDataset = null;
    if (sample.hasOwnProperty('Revenue') && sample.hasOwnProperty('Gross_Profit')) {
      chartType = 'bar'; // Use grouped bar for comparison
      secondaryDataset = {
        label: 'Gross Profit',
        data: pivot.map((r) => Number(r['Gross_Profit'] || 0)),
        backgroundColor: 'rgba(16, 185, 129, 0.3)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 1.5,
      };
    } else if (availableLabels.length === 1 && pivot.length <= 10 && valueKey === 'Revenue') {
      // If we have few items and revenue data, use pie chart for distribution
      chartType = 'pie';
    }
    
    return { 
      labels, 
      datasetLabel: valueKey || 'Value', 
      datasetValues,
      chartType,
      secondaryDataset
    };
  }, [pivot]);

  const chartData = useMemo(() => {
    const baseDataset = {
      label: datasetLabel,
      data: datasetValues,
      backgroundColor: chartType === 'pie' 
        ? ['rgba(59, 130, 246, 0.6)', 'rgba(16, 185, 129, 0.6)', 'rgba(245, 158, 11, 0.6)', 'rgba(239, 68, 68, 0.6)', 'rgba(139, 92, 246, 0.6)', 'rgba(236, 72, 153, 0.6)', 'rgba(20, 184, 166, 0.6)', 'rgba(249, 115, 22, 0.6)', 'rgba(6, 182, 212, 0.6)', 'rgba(132, 204, 22, 0.6)']
        : 'rgba(59, 130, 246, 0.3)',
      borderColor: chartType === 'pie'
        ? ['rgba(59, 130, 246, 1)', 'rgba(16, 185, 129, 1)', 'rgba(245, 158, 11, 1)', 'rgba(239, 68, 68, 1)', 'rgba(139, 92, 246, 1)', 'rgba(236, 72, 153, 1)', 'rgba(20, 184, 166, 1)', 'rgba(249, 115, 22, 1)', 'rgba(6, 182, 212, 1)', 'rgba(132, 204, 22, 1)']
        : 'rgba(59, 130, 246, 1)',
      borderWidth: chartType === 'pie' ? 2 : 1.5,
    };
    
    return {
      labels,
      datasets: secondaryDataset ? [baseDataset, secondaryDataset] : [baseDataset],
    };
  }, [labels, datasetLabel, datasetValues, chartType, secondaryDataset]);

  const chartOptions = useMemo(() => {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { 
          display: true,
          position: chartType === 'pie' ? 'right' : 'top'
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              if (chartType === 'pie') {
                const v = ctx.parsed;
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((v / total) * 100).toFixed(1);
                if (Math.abs(v) >= 1_000_000) return `${ctx.label}: €${(v/1_000_000).toFixed(1)}M (${percentage}%)`;
                if (Math.abs(v) >= 1_000) return `${ctx.label}: €${(v/1_000).toFixed(1)}k (${percentage}%)`;
                return `${ctx.label}: €${v.toLocaleString()} (${percentage}%)`;
              } else {
                const v = ctx.parsed.y;
                if (Math.abs(v) >= 1_000_000) return `${ctx.dataset.label}: €${(v/1_000_000).toFixed(1)}M`;
                if (Math.abs(v) >= 1_000) return `${ctx.dataset.label}: €${(v/1_000).toFixed(1)}k`;
                return `${ctx.dataset.label}: €${v.toLocaleString()}`;
              }
            },
          },
        },
      },
    };
    
    // Add scales only for bar and line charts (not pie)
    if (chartType !== 'pie') {
      baseOptions.scales = {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (v) => {
              if (Math.abs(v) >= 1_000_000) return `€${(v/1_000_000).toFixed(1)}M`;
              if (Math.abs(v) >= 1_000) return `€${(v/1_000).toFixed(1)}k`;
              return `€${v}`;
            },
          },
        },
        x: chartType === 'line' ? {
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        } : {}
      };
    }
    
    return baseOptions;
  }, [chartType]);

  return (
    <div className="space-y-4">
      <div className="overflow-auto border rounded">
        <table className="min-w-full text-xs">
          <thead className="bg-gray-50 text-gray-700">
            <tr>
              {Object.keys(pivot[0]).map((k) => (
                <th key={k} className="px-3 py-2 text-left font-medium">{k}</th>
              ))}
            </tr>
          </thead>
          <tbody>
              {pivot.map((row, idx) => (
                <tr key={idx} className={idx % 2 ? 'bg-white' : 'bg-gray-50'}>
                  {Object.keys(pivot[0]).map((k) => (
                    <td key={k} className="px-3 py-2 whitespace-nowrap text-gray-800">
                      {typeof row[k] === 'number'
                        ? (() => {
                            const num = Number(row[k]);
                            // Format based on column type
                            if (k === 'Year' || k === 'year') {
                              // Year column - show as integer, no formatting
                              return num.toString();
                            } else if (k.includes('Revenue') || k.includes('Profit') || k.includes('Gross')) {
                              // Currency columns
                              if (Math.abs(num) >= 1_000_000) {
                                return `€${(num/1_000_000).toFixed(1)}M`;
                              } else if (Math.abs(num) >= 1_000) {
                                return `€${(num/1_000).toFixed(1)}k`;
                              } else {
                                return `€${num.toLocaleString('en-US')}`;
                              }
                            } else if (k.includes('Units')) {
                              // Units column - no currency symbol
                              if (Math.abs(num) >= 1_000_000) {
                                return `${(num/1_000_000).toFixed(1)}M`;
                              } else if (Math.abs(num) >= 1_000) {
                                return `${(num/1_000).toFixed(1)}k`;
                              } else {
                                return num.toLocaleString('en-US');
                              }
                            } else if (k.includes('%') || k.includes('Margin')) {
                              // Percentage columns
                              return `${num.toFixed(1)}%`;
                            } else {
                              // Other numeric columns
                              if (Math.abs(num) >= 1_000_000) {
                                return `${(num/1_000_000).toFixed(1)}M`;
                              } else if (Math.abs(num) >= 1_000) {
                                return `${(num/1_000).toFixed(1)}k`;
                              } else {
                                return num.toLocaleString('en-US');
                              }
                            }
                          })()
                        : String(row[k] || '')}
                    </td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {labels.length > 0 && datasetValues.length > 0 && (
        <div className="h-80 w-full">
          <ChartComponent type={chartType} data={chartData} options={chartOptions} />
        </div>
      )}
    </div>
  );
};