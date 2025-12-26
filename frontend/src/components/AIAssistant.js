import React, { useState, useRef, useEffect, useMemo } from 'react';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Bot, X, Send, Sparkles, RotateCcw, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ChartComponent from '@/components/ChartComponent';

const AIAssistant = () => {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isContextCleared, setIsContextCleared] = useState(false);
  const [lastPivot, setLastPivot] = useState([]);
  const [pivotKey, setPivotKey] = useState(0);
  const scrollRef = useRef(null);
  const sessionId = useRef(`session-${Date.now()}`);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

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
    // Ensure messageText is always a string, never an event object
    let msgToSend = null;
    if (messageText !== null && messageText !== undefined) {
      msgToSend = typeof messageText === 'string' ? messageText.trim() : String(messageText || '').trim();
    } else {
      msgToSend = input.trim();
    }
    
    if (!msgToSend) return;

    // Ensure content is always a string
    const safeContent = typeof msgToSend === 'string' ? msgToSend : String(msgToSend || '');
    const userMessage = { role: 'user', content: safeContent };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build conversation history from previous messages
      // If context was cleared, send empty history to ensure backend doesn't use old context
      const conversationHistory = isContextCleared ? [] : messages.map(msg => {
        // Ensure content is always a string
        const safeContent = typeof msg.content === 'string' ? msg.content : String(msg.content || '');
        return {
          role: msg.role === 'user' ? 'user' : 'assistant',
          content: safeContent
        };
      });

      const payload = {
        message: msgToSend,
        chart_title: 'General Business Intelligence Query',
        context: {},
        session_id: sessionId.current,
        conversation_history: conversationHistory
      };

      // CRITICAL: Use non-streaming endpoint when streaming is disabled
      let useStreaming = false; // TEMPORARILY DISABLED - Streaming has extraction issues, using non-streaming for reliable responses
      const endpoint = useStreaming ? `${API}/insights/chat/stream` : `${API}/insights/chat`;
      
      if (useStreaming) {
        try {
          console.log('🔄 AIAssistant STREAMING: Starting streaming request');
          
          // Create AI message placeholder
          const aiMessageId = Date.now();
          const aiMessage = {
            role: 'ai',
            content: '',
            messageId: aiMessageId,
            isStreaming: true
          };
          setMessages((prev) => [...prev, aiMessage]);
          
          const response = await fetch(endpoint + '?think=true', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
              'Accept': 'text/event-stream',
              'Cache-Control': 'no-cache'
            },
            body: JSON.stringify(payload)
          });
          
          if (!response.ok || !response.body) {
            throw new Error(`Streaming failed: ${response.status}`);
          }
          
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          let fullResponse = '';
          
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split('\n\n');
            buffer = events.pop() || '';
            
            for (const event of events) {
              if (!event.trim()) continue;
              
              for (const line of event.split('\n')) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.type === 'content') {
                      fullResponse += data.data || '';
                      setMessages((prev) => 
                        prev.map(msg => 
                          msg.messageId === aiMessageId 
                            ? { ...msg, content: fullResponse, isStreaming: true }
                            : msg
                        )
                      );
                    } else if (data.type === 'metadata') {
                      setMessages((prev) => 
                        prev.map(msg => 
                          msg.messageId === aiMessageId 
                            ? { ...msg, isStreaming: false }
                            : msg
                        )
                      );
                      setLoading(false);
                      return;
                    } else if (data.type === 'done') {
                      setMessages((prev) => 
                        prev.map(msg => 
                          msg.messageId === aiMessageId 
                            ? { ...msg, isStreaming: false }
                            : msg
                        )
                      );
                      setLoading(false);
                      return;
                    }
                  } catch (e) {
                    console.error('Error parsing SSE:', e);
                  }
                }
              }
            }
          }
          
          setLoading(false);
          return;
        } catch (error) {
          console.error('🔄 AIAssistant STREAMING: Error, falling back:', error);
          useStreaming = false;
        }
      }
      
      // Non-streaming fallback
      const response = await axios.post(`${API}/insights/chat`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Check if question needs clarification
      const needsClarification = response.data?.needs_clarification || false;
      let suggestedQuestions = response.data?.suggested_questions || [];
      
      console.log('🔍 AIAssistant - Full API Response:', response.data);
      console.log('🔍 AIAssistant - Clarification check:', { 
        needsClarification, 
        suggestedQuestionsCount: suggestedQuestions?.length || 0, 
        suggestedQuestions,
        suggestedQuestionsType: typeof suggestedQuestions,
        isArray: Array.isArray(suggestedQuestions)
      });
      
      // Ensure suggestedQuestions is always an array
      if (!Array.isArray(suggestedQuestions)) {
        if (suggestedQuestions && typeof suggestedQuestions === 'object') {
          suggestedQuestions = Object.values(suggestedQuestions);
        } else if (typeof suggestedQuestions === 'string') {
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
      
      const fullResponse = response.data?.response || 'No response';
      // Ensure content is always a string
      const safeContent = typeof fullResponse === 'string' ? fullResponse : String(fullResponse || 'No response');
      
      // CRITICAL: Extract pivot table from response
      // Response structure: response.data = InsightsChatResponse { response, data: { pivot_table, ... } }
      let pivot = null;
      if (response?.data?.data?.pivot_table) {
        pivot = response.data.data.pivot_table;
      } else if (response?.data?.pivot_table) {
        pivot = response.data.pivot_table;
      } else if (response?.pivot_table) {
        pivot = response.pivot_table;
      }
      
      const pivotArray = Array.isArray(pivot) ? pivot : [];
      
      // CRITICAL: Log pivot data for debugging
      console.log('🔍 AIAssistant - Pivot table extraction:', {
        responseData: response?.data,
        responseDataData: response?.data?.data,
        pivotTablePath1: response?.data?.data?.pivot_table,
        pivotTablePath2: response?.data?.pivot_table,
        pivotTablePath3: response?.pivot_table,
        extractedPivot: pivot,
        pivotArrayLength: pivotArray.length,
        firstItem: pivotArray[0]
      });
      
      // Update pivot data
      if (pivotArray.length > 0) {
        console.log('✅ AIAssistant - Setting pivot data:', pivotArray.length, 'items');
        setLastPivot(pivotArray);
        setPivotKey(prev => prev + 1);
      } else {
        console.warn('⚠️ AIAssistant - No pivot data received!');
        setLastPivot([]);
      }
      
      const aiMessage = { 
        role: 'ai', 
        content: safeContent,
        needs_clarification: needsClarification,
        suggested_questions: suggestedQuestions,
        pivot_table: pivotArray
      };
      
      console.log('🔍 AIAssistant - Adding message:', aiMessage);
      setMessages((prev) => [...prev, aiMessage]);
      
      // Reset context cleared flag after sending first message after clear
      if (isContextCleared) {
        setIsContextCleared(false);
      }
      
      // Simulate streaming for better UX
      streamMessage(fullResponse, () => setStreamingMessage(''));
    } catch (error) {
      toast.error('AI Assistant is unavailable');
      const errorMessage = {
        role: 'ai',
        content: 'Sorry, I am currently unavailable. Please try again later.'
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const suggestedQuestions = [
    'Show me metrics for business Food, channel Convenience, customer BWG, brand Bensons and category Curry',
    'Compare Q1 gross sales for business Food in 2023 and 2024',
    'Show me top 10 brands by Revenue in 2025',
    'Compare brand Bonne Maman with other brands'
  ];

  const handleClearContext = () => {
    // Reset messages to empty array
    setMessages([]);
    // Create new session ID
    sessionId.current = `session-${Date.now()}`;
    // Clear streaming message
    setStreamingMessage('');
    // Set flag to ensure next message sends empty conversation history
    setIsContextCleared(true);
    // Show confirmation toast
    toast.success('Previous context cleared. Starting fresh conversation.');
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <div className="fixed bottom-8 right-8 z-50 group">
          <button
            onClick={() => setIsOpen(true)}
            className="w-16 h-16 rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-all duration-300"
            style={{
              background: 'linear-gradient(135deg, #d97706 0%, #f59e0b 100%)'
            }}
            data-testid="ai-assistant-button"
            title="Ask VectorDeep AI"
          >
            <Sparkles className="w-8 h-8 text-white" />
          </button>
          {/* Tooltip on hover */}
          <div className="absolute bottom-full right-0 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
            <div className="bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg whitespace-nowrap">
              Ask VectorDeep AI
              <div className="absolute top-full right-6 -mt-1">
                <div className="w-2 h-2 bg-gray-900 transform rotate-45"></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className="fixed bottom-8 right-8 w-[700px] max-w-[90vw] h-[85vh] max-h-[900px] rounded-2xl shadow-2xl flex flex-col z-50 bg-white border border-gray-200"
          data-testid="ai-chat-window"
        >
          {/* Header */}
          <div
            className="p-4 border-b flex items-center justify-between rounded-t-2xl"
            style={{
              background: 'linear-gradient(135deg, #d97706 0%, #f59e0b 100%)'
            }}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                  VectorDeep AI
                </h3>
                <p className="text-xs text-white/80">Business Intelligence Assistant</p>
              </div>
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
                onClick={() => setIsOpen(false)}
                className="text-white hover:bg-white/20 rounded-lg p-2 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-4 bg-gray-50 overflow-y-auto" ref={scrollRef} style={{ maxHeight: 'calc(85vh - 180px)' }}>
            {messages.length === 0 && (
              <div className="text-center py-8">
                <Sparkles className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                <p className="text-gray-700 mb-4">Hi! I'm VectorDeep AI. Ask me anything about your business data.</p>
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const questionText = typeof q === 'string' ? q : String(q || '');
                        if (questionText && questionText.trim()) {
                          handleSendMessage(questionText.trim());
                        }
                      }}
                      className="w-full text-left px-4 py-2 rounded-lg text-sm text-gray-700 bg-white hover:bg-blue-50 transition border border-gray-200 break-words"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-800 border border-gray-200'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <p className="text-sm whitespace-pre-wrap break-words">
                      {typeof msg.content === 'string' ? msg.content : String(msg.content || '')}
                    </p>
                  ) : (
                    <div className="prose prose-sm max-w-none break-words">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {typeof msg.content === 'string' ? msg.content : String(msg.content || '')}
                      </ReactMarkdown>
                      
                      {/* Show pivot table if available for this message - only show for the last message to avoid duplicates */}
                      {msg.pivot_table && Array.isArray(msg.pivot_table) && msg.pivot_table.length > 0 && idx === messages.length - 1 && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <h4 className="text-sm font-semibold mb-3 text-gray-800">Visuals from AI data</h4>
                          <AIDataVisuals pivot={msg.pivot_table} key={`pivot-msg-${idx}-${msg.pivot_table.length}`} />
                        </div>
                      )}
                      
                      {/* Suggested Questions for Clarification */}
                      {msg.needs_clarification && msg.suggested_questions && Array.isArray(msg.suggested_questions) && msg.suggested_questions.length > 0 && (
                        <div className="mt-4 space-y-2 pt-3 border-t border-gray-200">
                          <p className="text-xs font-semibold text-gray-600 mb-2">Did you mean:</p>
                          <div className="grid grid-cols-1 gap-2">
                            {msg.suggested_questions.map((suggestedQ, sqIdx) => (
                              <button
                                key={sqIdx}
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  const questionText = typeof suggestedQ === 'string' ? suggestedQ : String(suggestedQ || '');
                                  if (questionText && questionText.trim()) {
                                    handleSendMessage(questionText.trim());
                                  }
                                }}
                                className="text-left px-4 py-3 rounded-lg text-sm transition-all hover:shadow-md border-2 border-blue-200 hover:border-blue-400 bg-white hover:bg-blue-50 w-full"
                                style={{ color: '#1e40af' }}
                              >
                                <div className="flex items-start gap-2">
                                  <ArrowRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                  <span className="flex-1 break-words">{suggestedQ}</span>
                                </div>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* REMOVED: Duplicate pivot table rendering - now rendered inside the message itself */}

            {loading && (
              <div className="flex justify-start mb-4">
                <div className="bg-white px-4 py-3 rounded-2xl border border-gray-200 flex items-center gap-3">
                  <div className="w-8 h-8 border-4 border-amber-600 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-sm text-gray-700 font-medium">Thinking...</span>
                </div>
              </div>
            )}
            
            {streamingMessage && (
              <div className="flex justify-start mb-4">
                <div className="max-w-[85%] px-4 py-3 rounded-2xl bg-white text-gray-800 border border-gray-200 break-words">
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {typeof streamingMessage === 'string' ? streamingMessage : String(streamingMessage || '')}
                    </ReactMarkdown>
                  </div>
                  <span className="animate-pulse">▊</span>
                </div>
              </div>
            )}
          </ScrollArea>

          {/* Input */}
          <div className="p-4 border-t bg-white rounded-b-2xl">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask about your business data..."
                disabled={loading}
                className="flex-1 bg-white border-gray-300"
                data-testid="ai-chat-input"
              />
              <Button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleSendMessage();
                }}
                disabled={loading || !input.trim()}
                className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700"
                data-testid="ai-send-button"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

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
          enabled: true,
          callbacks: {
            label: (ctx) => {
              // CRITICAL: Validate ctx exists and has required properties
              if (!ctx || ctx.dataset === null || ctx.datasetIndex === undefined) {
                return '';
              }
              
              try {
                const value = ctx.parsed && (ctx.parsed.y !== undefined ? ctx.parsed.y : ctx.parsed) || 0;
                const label = ctx.dataset?.label || datasetLabel || 'Value';
                
                if (datasetLabel === 'Revenue' || datasetLabel === 'Gross_Profit') {
                  return `${label}: €${(value / 1000000).toFixed(2)}M`;
                } else if (datasetLabel === 'Units') {
                  return `${label}: ${value.toLocaleString()}`;
                } else if (datasetLabel === 'Margin_%') {
                  return `${label}: ${value.toFixed(2)}%`;
                }
                return `${label}: ${value}`;
              } catch (error) {
                console.error('Tooltip error:', error);
                return '';
              }
            }
          }
        }
      }
    };
    
    if (chartType === 'line') {
      baseOptions.scales = {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => {
              if (datasetLabel === 'Revenue' || datasetLabel === 'Gross_Profit') {
                return `€${(value / 1000000).toFixed(1)}M`;
              }
              return value.toLocaleString();
            }
          }
        }
      };
    } else if (chartType === 'bar') {
      baseOptions.scales = {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => {
              if (datasetLabel === 'Revenue' || datasetLabel === 'Gross_Profit') {
                return `€${(value / 1000000).toFixed(1)}M`;
              }
              return value.toLocaleString();
            }
          }
        }
      };
    }
    
    return baseOptions;
  }, [chartType, datasetLabel]);

  // Create table data
  const tableData = useMemo(() => {
    if (!pivot || pivot.length === 0) return [];
    return pivot.map((row, idx) => {
      const rowData = { ...row };
      // Format numbers for display
      if (rowData.Revenue) rowData.Revenue = `€${(rowData.Revenue / 1000000).toFixed(2)}M`;
      if (rowData.Gross_Profit) rowData.Gross_Profit = `€${(rowData.Gross_Profit / 1000000).toFixed(2)}M`;
      if (rowData.Units) rowData.Units = rowData.Units.toLocaleString();
      if (rowData['Margin_%']) rowData['Margin_%'] = `${rowData['Margin_%']}%`;
      return rowData;
    });
  }, [pivot]);

  const tableColumns = useMemo(() => {
    if (!pivot || pivot.length === 0) return [];
    return Object.keys(pivot[0] || {});
  }, [pivot]);

  return (
    <div className="space-y-4">
      {/* Chart */}
      {chartData.labels.length > 0 && (
        <div className="w-full" style={{ height: '300px' }}>
          <ChartComponent
            type={chartType}
            data={chartData}
            options={chartOptions}
          />
        </div>
      )}
      
      {/* Table */}
      {tableData.length > 0 && tableColumns.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs border-collapse">
            <thead>
              <tr className="bg-gray-100">
                {tableColumns.map((col, idx) => (
                  <th key={idx} className="border border-gray-300 px-3 py-2 text-left font-semibold text-gray-700">
                    {col.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, rowIdx) => (
                <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  {tableColumns.map((col, colIdx) => (
                    <td key={colIdx} className="border border-gray-300 px-3 py-2 text-gray-700">
                      {row[col] !== undefined && row[col] !== null ? String(row[col]) : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AIAssistant;