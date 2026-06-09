import React, { useState, useRef, useEffect, useMemo } from 'react';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Bot, X, Send, Sparkles, RotateCcw, ArrowRight, History, CheckSquare, Mic, MicOff, Volume2, VolumeX, Lightbulb, Search, Loader2 } from 'lucide-react';
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
  const [loadingState, setLoadingState] = useState('thinking'); // Progressive loading states
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isContextCleared, setIsContextCleared] = useState(false);
  const [lastPivot, setLastPivot] = useState([]);
  const [pivotKey, setPivotKey] = useState(0);
  const scrollRef = useRef(null);
  const sessionId = useRef(`session-${Date.now()}`);
  const loadingIntervalRef = useRef(null); // Store interval ID in ref for cleanup
  const abortControllerRef = useRef(null); // Store AbortController for cancelling requests
  const streamReaderRef = useRef(null); // Store stream reader for cancelling streaming
  const axiosCancelTokenRef = useRef(null); // Store axios cancel token for cancelling requests
  const streamMessageIntervalRef = useRef(null); // Store streamMessage interval for cleanup
  const isContextClearedRef = useRef(false); // Track if context was cleared to prevent delayed updates
  const [previousQuestions, setPreviousQuestions] = useState([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState(null);
  const [showPreviousQuestions, setShowPreviousQuestions] = useState(false);

  // Voice Q&A: speech-to-text + text-to-speech
  const [isListening, setIsListening] = useState(false);
  const [isSpeakerOn, setIsSpeakerOn] = useState(false);
  const recognitionRef = useRef(null);
  const speechSupportedRef = useRef(false);
  const lastSpokenIndexRef = useRef(-1);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      speechSupportedRef.current = false;
      return;
    }
    speechSupportedRef.current = true;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      if (transcript) setInput(transcript);
    };
    recognition.onerror = (e) => {
      console.warn('SpeechRecognition error:', e?.error || e);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;

    return () => {
      try { recognition.stop(); } catch (e) { /* ignore */ }
    };
  }, []);

  const toggleListening = () => {
    if (!speechSupportedRef.current || !recognitionRef.current) {
      toast.error('Voice input is not supported in this browser. Please use Chrome.');
      return;
    }
    if (isListening) {
      try { recognitionRef.current.stop(); } catch (e) { /* ignore */ }
      setIsListening(false);
      return;
    }
    try {
      setInput('');
      recognitionRef.current.start();
      setIsListening(true);
    } catch (e) {
      console.warn('Could not start recognition:', e);
      setIsListening(false);
    }
  };

  // Strip markdown/symbols so the spoken text sounds natural
  const cleanForSpeech = (text) => {
    if (!text || typeof text !== 'string') return '';
    return text
      .replace(/```[\s\S]*?```/g, ' ')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/[*_#>|]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  };

  const stopSpeaking = () => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;
    try { window.speechSynthesis.cancel(); } catch (e) { /* ignore */ }
  };

  const speak = (text) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;
    const cleaned = cleanForSpeech(text);
    if (!cleaned) return;
    stopSpeaking();
    const utter = new window.SpeechSynthesisUtterance(cleaned);
    utter.lang = 'en-US';
    utter.rate = 1.0;
    utter.pitch = 1.0;
    window.speechSynthesis.speak(utter);
  };

  // Auto-speak newest AI message when speaker is on
  useEffect(() => {
    if (!isSpeakerOn) return;
    if (!messages || messages.length === 0) return;
    const lastIdx = messages.length - 1;
    const last = messages[lastIdx];
    if (last?.role === 'ai' && lastSpokenIndexRef.current !== lastIdx) {
      lastSpokenIndexRef.current = lastIdx;
      speak(last.content);
    }
  }, [messages, isSpeakerOn]);

  // Stop speaking when chat is closed or context is cleared
  useEffect(() => {
    if (!isOpen) stopSpeaking();
  }, [isOpen]);

  const toggleSpeaker = () => {
    setIsSpeakerOn((prev) => {
      const next = !prev;
      if (!next) stopSpeaking();
      return next;
    });
  };
  
  // Progressive loading states dictionary
  const loadingStates = [
    'thinking',
    'analyzing your question',
    'processing data',
    'generating insights',
    'preparing response',
    'finalizing answer'
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Fetch previous questions when component mounts or opens
  useEffect(() => {
    if (isOpen && token) {
      fetchPreviousQuestions();
    }
  }, [isOpen, token]);

  const fetchPreviousQuestions = async () => {
    try {
      const response = await axios.get(`${API}/user-questions`, {
        params: {
          chatbot_type: 'vector_deep_ai',
          limit: 10
        },
        headers: { Authorization: `Bearer ${token}` }
      });
      setPreviousQuestions(response.data.questions || []);
    } catch (error) {
      console.error('Error fetching previous questions:', error);
    }
  };

  const storeQuestion = async (question, response) => {
    try {
      await axios.post(`${API}/user-questions`, {
        question: question,
        chatbot_type: 'vector_deep_ai',
        chart_title: null,
        context: {},
        response: response
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchPreviousQuestions();
    } catch (error) {
      console.error('Error storing question:', error);
    }
  };

  // Simulated streaming function to display text word by word
  const streamMessage = (fullText, onComplete) => {
    // CRITICAL: Clear any existing stream interval first
    if (streamMessageIntervalRef.current) {
      clearInterval(streamMessageIntervalRef.current);
      streamMessageIntervalRef.current = null;
    }
    
    // CRITICAL: Don't start streaming if context was cleared
    if (isContextClearedRef.current) {
      setStreamingMessage('');
      return;
    }
    
    const words = fullText.split(' ');
    let currentText = '';
    let wordIndex = 0;

    const streamInterval = setInterval(() => {
      // CRITICAL: Check if context was cleared during streaming
      if (isContextClearedRef.current) {
        clearInterval(streamInterval);
        streamMessageIntervalRef.current = null;
        setStreamingMessage('');
        return; // Don't call onComplete if context was cleared
      }
      
      if (wordIndex < words.length) {
        currentText += (wordIndex > 0 ? ' ' : '') + words[wordIndex];
        setStreamingMessage(currentText);
        wordIndex++;
      } else {
        clearInterval(streamInterval);
        streamMessageIntervalRef.current = null;
        setStreamingMessage('');
        // CRITICAL: Only call onComplete if context wasn't cleared
        if (!isContextClearedRef.current) {
          onComplete();
        }
      }
    }, 30); // 30ms delay between words for smooth typing effect
    
    streamMessageIntervalRef.current = streamInterval; // Store for cleanup
  };

    const handleSendMessage = async (messageText = null) => {
    // CRITICAL: Reset context cleared flag when starting new message
    // This allows new messages to proceed normally
    if (isContextCleared) {
      isContextClearedRef.current = false;
    }
    
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
    setLoadingState('thinking');
    
    // Start progressive loading states
    let loadingStateIndex = 0;
    const intervalId = setInterval(() => {
      loadingStateIndex = loadingStateIndex + 1;
      // CRITICAL: Stop at the last state - don't loop back to "thinking"
      if (loadingStateIndex >= loadingStates.length) {
        // Reached the last state - stop rotation and clear interval
        clearInterval(intervalId);
        loadingIntervalRef.current = null;
        setLoadingState(loadingStates[loadingStates.length - 1]); // Keep showing last state
        return;
      }
      setLoadingState(loadingStates[loadingStateIndex]);
    }, 11000); // Change state every 11 seconds to allow user to read each state without repetition
    loadingIntervalRef.current = intervalId; // Store in ref for cleanup

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
        conversation_history: conversationHistory,
        selected_previous_question_id: selectedQuestionId || null
      };
      const clickhousePayload = { question: msgToSend };

      // Use ClickHouse AI chatbot endpoint for the main AI Assistant flow.
      // This ensures answers come from Mac Studio ClickHouse, not MongoDB insights endpoint.
      let useStreaming = false; // Streaming path is for /insights/chat/stream; keep disabled for ClickHouse endpoint.
      const endpoint = `${API}/ai/chatbot/chat`;
      
      if (useStreaming) {
        try {
          console.log('🔄 AIAssistant STREAMING: Starting streaming request');
          
          // CRITICAL: Create new AbortController for this request
          abortControllerRef.current = new AbortController();
          const signal = abortControllerRef.current.signal;
          
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
            body: JSON.stringify(payload),
            signal: signal // Add abort signal
          });
          
          if (!response.ok || !response.body) {
            throw new Error(`Streaming failed: ${response.status}`);
          }
          
          const reader = response.body.getReader();
          streamReaderRef.current = reader; // Store reader for cancellation
          const decoder = new TextDecoder();
          let buffer = '';
          let fullResponse = '';
          
          while (true) {
            // CRITICAL: Check if request was aborted
            if (signal.aborted) {
              console.log('🔄 AIAssistant STREAMING: Request aborted, stopping stream');
              try {
                reader.cancel();
              } catch (e) {
                // Reader may already be closed
              }
              streamReaderRef.current = null;
              return; // Exit immediately
            }
            
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
                      const chunkText = data.data || '';
                      fullResponse += chunkText;
                      
                      // CRITICAL: Stop loading states immediately when first content arrives
                      if (loadingIntervalRef.current && fullResponse.length === chunkText.length) {
                        // First chunk received - stop loading states immediately
                        clearInterval(loadingIntervalRef.current);
                        loadingIntervalRef.current = null;
                        setLoading(false);
                        setLoadingState('thinking');
                      }
                      
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
                      if (loadingIntervalRef.current) {
                        clearInterval(loadingIntervalRef.current);
                        loadingIntervalRef.current = null;
                      }
                      setLoading(false);
                      setLoadingState('thinking');
                      return;
                    } else if (data.type === 'done') {
                      setMessages((prev) => 
                        prev.map(msg => 
                          msg.messageId === aiMessageId 
                            ? { ...msg, isStreaming: false }
                            : msg
                        )
                      );
                      if (loadingIntervalRef.current) {
                        clearInterval(loadingIntervalRef.current);
                        loadingIntervalRef.current = null;
                      }
                      setLoading(false);
                      setLoadingState('thinking');
                      return;
                    }
                  } catch (e) {
                    console.error('Error parsing SSE:', e);
                  }
                }
              }
            }
          }
          
          if (loadingIntervalRef.current) {
            clearInterval(loadingIntervalRef.current);
            loadingIntervalRef.current = null;
          }
          setLoading(false);
          setLoadingState('thinking');
          return;
        } catch (error) {
          console.error('🔄 AIAssistant STREAMING: Error, falling back:', error);
          // CRITICAL: Stop loading states immediately on error
          if (loadingIntervalRef.current) {
            clearInterval(loadingIntervalRef.current);
            loadingIntervalRef.current = null;
          }
          setLoading(false);
          setLoadingState('thinking');
          useStreaming = false;
        }
      }
      
      // Non-streaming fallback
      // CRITICAL: Create new AbortController for this request
      abortControllerRef.current = new AbortController();
      const cancelToken = axios.CancelToken.source();
      axiosCancelTokenRef.current = cancelToken; // Store for cancellation
      
      const response = await axios.post(endpoint, clickhousePayload, {
        headers: { Authorization: `Bearer ${token}` },
        cancelToken: cancelToken.token
      });
      
      // CRITICAL: Check if request was aborted after response
      if (abortControllerRef.current?.signal.aborted) {
        return; // Exit immediately, don't process response
      }
      
      // CRITICAL: Stop loading states immediately when response is received
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
      setLoading(false);
      setLoadingState('thinking');

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
      
      let fullResponse = response.data?.response || 'No response';
      // Ensure content is always a string
      if (typeof fullResponse !== 'string') {
        if (fullResponse && typeof fullResponse === 'object') {
          fullResponse = JSON.stringify(fullResponse);
        } else {
          fullResponse = String(fullResponse || 'No response');
        }
      }
      
      // CRITICAL: Sanitize response to remove technical error details
      // Check if response contains technical error information (status codes, service names, URLs, etc.)
      const technicalErrorPatterns = [
        /503.*Ollama/i,
        /Ollama service not available/i,
        /localhost:\d+/i,
        /Error:\s*\d+:/i,
        /HTTP.*error/i,
        /Connection.*refused/i,
        /Service.*unavailable/i,
        /^\d{3}:/, // Status codes like "503:"
        /Ollama|Perplexity|vLLM/i, // LLM provider names
        /http:\/\/localhost/i,
        /http:\/\/\d+\.\d+\.\d+\.\d+/i // IP addresses
      ];
      
      const containsTechnicalError = technicalErrorPatterns.some(pattern => pattern.test(fullResponse));
      if (containsTechnicalError) {
        // Replace technical error with user-friendly message
        console.error('Technical error detected in response, sanitizing:', fullResponse);
        fullResponse = 'I apologize, but I encountered an issue processing your request. Please try rephrasing your question or try again in a moment.';
      }
      
      const safeContent = fullResponse;
      
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

      // Storytelling Mode: deterministic insight bullets from backend
      let narrative = response?.data?.data?.narrative
        ?? response?.data?.narrative
        ?? response?.narrative
        ?? [];
      if (!Array.isArray(narrative)) {
        narrative = [];
      }
      
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
      
      // Store the question and response for future reference
      if (selectedQuestionId) {
        // Increment usage count for selected previous question
        axios.post(`${API}/user-questions/${selectedQuestionId}/use`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(error => console.error('Error incrementing question usage:', error));
        setSelectedQuestionId(null); // Reset selection
      } else {
        // Store new question
        storeQuestion(msgToSend, safeContent);
      }
      
      const aiMessage = { 
        role: 'ai', 
        content: safeContent,
        needs_clarification: needsClarification,
        suggested_questions: suggestedQuestions,
        pivot_table: pivotArray,
        narrative: narrative
      };
      
      console.log('🔍 AIAssistant - Adding message:', aiMessage);
      setMessages((prev) => [...prev, aiMessage]);
      
      // Reset context cleared flag after sending first message after clear
      if (isContextCleared) {
        setIsContextCleared(false);
        isContextClearedRef.current = false; // Reset ref flag too
      }
      
      // CRITICAL: Don't start streaming if context was cleared
      if (!isContextClearedRef.current) {
        // Simulate streaming for better UX
        streamMessage(fullResponse, () => {
          // CRITICAL: Only update if context wasn't cleared
          if (!isContextClearedRef.current) {
            setStreamingMessage('');
          }
        });
      }
    } catch (error) {
      // Log technical error details to console for debugging
      console.error('AIAssistant API Error:', error);
      console.error('Error details:', error.response?.data || error.message);
      console.error('Error status:', error.response?.status);
      
      // Show user-friendly error message (never show technical details)
      toast.error('AI Assistant is temporarily unavailable. Please try again in a moment.');
      
      // CRITICAL: Stop loading states immediately on error
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
      setLoading(false);
      setLoadingState('thinking');
      
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
    // CRITICAL: Set flag immediately to prevent any delayed updates
    isContextClearedRef.current = true;
    
    // CRITICAL: Cancel all ongoing requests immediately
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    // CRITICAL: Cancel axios requests if active
    if (axiosCancelTokenRef.current) {
      try {
        axiosCancelTokenRef.current.cancel('Request cancelled: Context cleared');
      } catch (e) {
        // Cancel token may already be used
      }
      axiosCancelTokenRef.current = null;
    }
    
    // CRITICAL: Cancel streaming reader if active
    if (streamReaderRef.current) {
      try {
        streamReaderRef.current.cancel();
      } catch (e) {
        // Reader may already be closed
      }
      streamReaderRef.current = null;
    }
    
    // CRITICAL: Clear streamMessage interval (typing animation)
    if (streamMessageIntervalRef.current) {
      clearInterval(streamMessageIntervalRef.current);
      streamMessageIntervalRef.current = null;
    }
    
    // CRITICAL: Clear all intervals
    if (loadingIntervalRef.current) {
      clearInterval(loadingIntervalRef.current);
      loadingIntervalRef.current = null;
    }
    
    // CRITICAL: Reset all loading states immediately
    setLoading(false);
    setLoadingState('thinking');
    setStreamingMessage('');

    // Stop any ongoing voice playback / recognition
    stopSpeaking();
    if (isListening && recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) { /* ignore */ }
      setIsListening(false);
    }
    lastSpokenIndexRef.current = -1;

    // CRITICAL: Reset messages to empty array immediately
    setMessages([]);
    
    // Create new session ID
    sessionId.current = `session-${Date.now()}`;
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
                onClick={toggleSpeaker}
                className={`text-white rounded-lg p-2 transition flex items-center gap-2 ${isSpeakerOn ? 'bg-white/30' : 'hover:bg-white/20'}`}
                title={isSpeakerOn ? 'Mute spoken answers' : 'Read answers aloud'}
                data-testid="ai-speaker-toggle"
              >
                {isSpeakerOn ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
                <span className="text-sm hidden sm:inline">{isSpeakerOn ? 'Voice On' : 'Voice Off'}</span>
              </button>
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
                      
                      {/* Storytelling Mode: Key Insights card (deterministic, from data) */}
                      {msg.narrative && Array.isArray(msg.narrative) && msg.narrative.length > 0 && idx === messages.length - 1 && (
                        <div
                          className="mt-4 p-3 rounded-lg border"
                          style={{
                            background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.08) 0%, rgba(249, 115, 22, 0.08) 100%)',
                            borderColor: 'rgba(249, 115, 22, 0.25)'
                          }}
                          data-testid="ai-key-insights"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <Lightbulb className="w-4 h-4 text-amber-600" />
                            <h4 className="text-sm font-semibold text-gray-800">Key Insights</h4>
                          </div>
                          <ul className="space-y-1.5">
                            {msg.narrative.map((bullet, bIdx) => (
                              <li key={bIdx} className="text-sm text-gray-700 flex items-start gap-2">
                                <span className="mt-1 inline-block w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" />
                                <span className="flex-1 break-words">{bullet}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

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
                    <span className="text-sm text-gray-700 font-medium capitalize">
                      {loadingState}...
                    </span>
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
            {/* Previous Questions Section */}
            {previousQuestions.length > 0 && (
              <div className="mb-3">
                <button
                  onClick={() => setShowPreviousQuestions(!showPreviousQuestions)}
                  className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800 mb-2"
                >
                  <History className="w-4 h-4" />
                  <span>Previous Questions ({previousQuestions.length})</span>
                </button>
                {showPreviousQuestions && (
                  <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-lg p-2 bg-gray-50">
                      {previousQuestions.map((q) => (
                        <label
                          key={q.id}
                          className="flex items-start gap-2 p-2 hover:bg-gray-100 rounded cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedQuestionId === q.id}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedQuestionId(q.id);
                                // Append the selected question to existing text
                                const currentText = input.trim();
                                const questionText = q.question.trim();
                                if (currentText) {
                                  // Add space and append if there's existing text
                                  setInput(`${currentText} ${questionText}`);
                                } else {
                                  // Just set the question if input is empty
                                  setInput(questionText);
                                }
                              } else {
                                setSelectedQuestionId(null);
                                // Remove the appended question from input
                                const currentText = input.trim();
                                const questionText = q.question.trim();
                                if (currentText.includes(questionText)) {
                                  // Remove the question text, keeping the original text
                                  const newText = currentText.replace(questionText, '').trim();
                                  setInput(newText);
                                }
                              }
                            }}
                            className="mt-1"
                          />
                          <span className="text-xs text-gray-700 flex-1">{q.question}</span>
                        </label>
                      ))}
                  </div>
                )}
              </div>
            )}
            
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  // Don't clear selection when user types - allow them to edit the appended text
                }}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder={isListening ? 'Listening… speak now' : 'Ask about your business data...'}
                disabled={loading}
                className="flex-1 bg-white border-gray-300"
                data-testid="ai-chat-input"
              />
              <Button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  toggleListening();
                }}
                disabled={loading}
                title={isListening ? 'Stop listening' : 'Speak your question'}
                className={
                  isListening
                    ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
                }
                data-testid="ai-mic-button"
              >
                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </Button>
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
            {selectedQuestionId && (
              <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                <CheckSquare className="w-3 h-3" />
                Asking about a previous question
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
};

// ---------------------------------------------------------------------------
// Drill-down ("Why this number?") helpers
// ---------------------------------------------------------------------------

// Map pivot table column names → backend filter keys
const PIVOT_TO_FILTER_KEY = {
  Brand: 'brand',
  Business: 'business',
  Channel: 'channel',
  Category: 'category',
  Sub_Category: 'sub_category',
  Customer: 'customer',
  Sku: 'sku',
  Year: 'year',
  Month_Name: 'month_name',
  Month: 'month_name',
  Quarter: 'quarter',
};

// All dimensions a user could break down INTO. We filter out ones already
// present in the clicked row at runtime (no point breaking down by Brand
// when the row already pins Brand=Brillo).
const ALL_BREAKDOWN_DIMS = [
  { key: 'customer',     label: 'Customer' },
  { key: 'channel',      label: 'Channel' },
  { key: 'month_name',   label: 'Month' },
  { key: 'sub_category', label: 'Sub-Category' },
  { key: 'category',     label: 'Category' },
  { key: 'business',     label: 'Business' },
  { key: 'brand',        label: 'Brand' },
];

const MEASURE_KEYS = new Set(['Revenue', 'Gross_Profit', 'Cases', 'Units', 'Margin_%']);

// Build a backend filters dict from a clicked pivot row.
const rowToFilters = (row) => {
  const filters = {};
  if (!row) return filters;
  Object.keys(row).forEach((colKey) => {
    const filterKey = PIVOT_TO_FILTER_KEY[colKey];
    if (!filterKey) return;
    const rawValue = row[colKey];
    if (rawValue === null || rawValue === undefined || rawValue === '') return;
    if (filterKey === 'year' || filterKey === 'quarter') {
      const n = Number(rawValue);
      if (!Number.isNaN(n)) filters[filterKey] = [n];
    } else {
      filters[filterKey] = [String(rawValue)];
    }
  });
  return filters;
};

// Format a number as €X.XXM / €XK / €X (matches existing AIDataVisuals look)
const formatCurrencyShort = (value) => {
  const num = Number(value);
  if (Number.isNaN(num)) return '€0';
  if (Math.abs(num) >= 1_000_000) return `€${(num / 1_000_000).toFixed(2)}M`;
  if (Math.abs(num) >= 1_000) return `€${(num / 1_000).toFixed(0)}K`;
  return `€${num.toLocaleString()}`;
};

// Describe the clicked row for the dialog header ("Brand: Brillo · Year: 2024")
const describeClickedRow = (row) => {
  if (!row) return '';
  const parts = [];
  Object.keys(row).forEach((k) => {
    if (MEASURE_KEYS.has(k)) return;
    const v = row[k];
    if (v === null || v === undefined || v === '') return;
    parts.push(`${k.replace(/_/g, ' ')}: ${v}`);
  });
  return parts.join('  ·  ');
};

// Pick the headline value to show in the dialog header
const pickPrimaryMeasure = (row) => {
  if (!row) return null;
  for (const m of ['Revenue', 'Gross_Profit', 'Cases']) {
    if (m in row && row[m] !== null && row[m] !== undefined && row[m] !== '') {
      return { key: m, value: row[m] };
    }
  }
  return null;
};

// Lightweight in-file component to render a table and a simple chart from pivot data
const AIDataVisuals = ({ pivot }) => {
  const { token } = useAuth();
  const [drillRow, setDrillRow] = useState(null);
  const [drillBreakdown, setDrillBreakdown] = useState(null);
  const [drillLoading, setDrillLoading] = useState(false);
  const [drillResult, setDrillResult] = useState(null);
  const [drillError, setDrillError] = useState(null);

  const openDrill = (rawRow) => {
    setDrillRow(rawRow);
    setDrillBreakdown(null);
    setDrillResult(null);
    setDrillError(null);
  };
  const closeDrill = () => {
    setDrillRow(null);
    setDrillBreakdown(null);
    setDrillResult(null);
    setDrillError(null);
    setDrillLoading(false);
  };

  const runDrillDown = async (breakdownKey) => {
    if (!drillRow) return;
    setDrillBreakdown(breakdownKey);
    setDrillLoading(true);
    setDrillError(null);
    setDrillResult(null);
    try {
      const filters = rowToFilters(drillRow);
      const resp = await axios.post(
        `${API}/ai/chatbot/drill-down`,
        {
          breakdown_by: breakdownKey,
          filters,
          measure: 'gsales',
          limit: 10,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setDrillResult(resp.data);
    } catch (err) {
      console.error('Drill-down error:', err);
      setDrillError(
        err.response?.data?.detail
          || 'Could not load the breakdown. Please try again.'
      );
    } finally {
      setDrillLoading(false);
    }
  };

  // Pivot columns already pinned by the clicked row — hide them from the
  // breakdown chooser since breaking down by a fixed value is pointless.
  const drillUsedDims = drillRow
    ? Object.keys(drillRow)
        .map((k) => PIVOT_TO_FILTER_KEY[k])
        .filter(Boolean)
    : [];
  const availableBreakdowns = ALL_BREAKDOWN_DIMS.filter(
    (b) => !drillUsedDims.includes(b.key)
  );

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
                  // CRITICAL: Use K for values < 1M, M for values >= 1M
                  if (Math.abs(value) >= 1_000_000) {
                    return `${label}: €${(value / 1_000_000).toFixed(2)}M`;
                  } else if (Math.abs(value) >= 1_000) {
                    return `${label}: €${(value / 1_000).toFixed(0)}K`;
                  } else {
                    return `${label}: €${value.toLocaleString()}`;
                  }
                } else if (datasetLabel === 'Units' || datasetLabel === 'Cases') {
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
                // CRITICAL: Use K for values < 1M, M for values >= 1M
                if (Math.abs(value) >= 1_000_000) {
                  return `€${(value / 1_000_000).toFixed(2)}M`;
                } else if (Math.abs(value) >= 1_000) {
                  return `€${(value / 1_000).toFixed(0)}K`;
                } else {
                  return `€${value.toLocaleString()}`;
                }
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
                // CRITICAL: Use K for values < 1M, M for values >= 1M
                if (Math.abs(value) >= 1_000_000) {
                  return `€${(value / 1_000_000).toFixed(2)}M`;
                } else if (Math.abs(value) >= 1_000) {
                  return `€${(value / 1_000).toFixed(0)}K`;
                } else {
                  return `€${value.toLocaleString()}`;
                }
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
      // CRITICAL: Use K for values < 1M, M for values >= 1M
      if (rowData.Revenue) {
        const rev = Number(rowData.Revenue);
        rowData.Revenue = Math.abs(rev) >= 1_000_000 
          ? `€${(rev / 1_000_000).toFixed(2)}M` 
          : Math.abs(rev) >= 1_000 
            ? `€${(rev / 1_000).toFixed(0)}K` 
            : `€${rev.toLocaleString()}`;
      }
      if (rowData.Gross_Profit) {
        const profit = Number(rowData.Gross_Profit);
        rowData.Gross_Profit = Math.abs(profit) >= 1_000_000 
          ? `€${(profit / 1_000_000).toFixed(2)}M` 
          : Math.abs(profit) >= 1_000 
            ? `€${(profit / 1_000).toFixed(0)}K` 
            : `€${profit.toLocaleString()}`;
      }
      if (rowData.Units || rowData.Cases) {
        const units = Number(rowData.Units || rowData.Cases);
        rowData.Units = rowData.Units ? units.toLocaleString() : rowData.Units;
        rowData.Cases = rowData.Cases ? units.toLocaleString() : rowData.Cases;
      }
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
          <p className="text-xs text-gray-500 mb-2 italic">
            Click any row to see <span className="font-medium text-amber-700">why this number?</span>
          </p>
          <table className="min-w-full text-xs border-collapse">
            <thead>
              <tr className="bg-gray-100">
                {tableColumns.map((col, idx) => (
                  <th key={idx} className="border border-gray-300 px-3 py-2 text-left font-semibold text-gray-700">
                    {col.replace(/_/g, ' ')}
                  </th>
                ))}
                <th className="border border-gray-300 px-2 py-2 text-center font-semibold text-gray-700 w-8" aria-label="Drill" />
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, rowIdx) => (
                <tr
                  key={rowIdx}
                  className={`${rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} cursor-pointer hover:bg-amber-50 transition`}
                  onClick={() => openDrill(pivot[rowIdx])}
                  title="Click to see breakdown"
                  data-testid="ai-drill-row"
                >
                  {tableColumns.map((col, colIdx) => (
                    <td key={colIdx} className="border border-gray-300 px-3 py-2 text-gray-700">
                      {row[col] !== undefined && row[col] !== null ? String(row[col]) : '-'}
                    </td>
                  ))}
                  <td className="border border-gray-300 px-2 py-2 text-center text-amber-600">
                    <Search className="w-3.5 h-3.5 inline-block" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Drill-down dialog ("Why this number?") */}
      {drillRow && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/40"
          onClick={closeDrill}
          data-testid="ai-drill-overlay"
        >
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
            data-testid="ai-drill-dialog"
          >
            {/* Header */}
            <div
              className="p-4 border-b flex items-start justify-between"
              style={{ background: 'linear-gradient(135deg, #d97706 0%, #f59e0b 100%)' }}
            >
              <div className="text-white">
                <div className="flex items-center gap-2 mb-1">
                  <Search className="w-4 h-4" />
                  <h3 className="text-base font-semibold">Why this number?</h3>
                </div>
                <p className="text-xs text-white/90 leading-snug">{describeClickedRow(drillRow)}</p>
                {(() => {
                  const primary = pickPrimaryMeasure(drillRow);
                  if (!primary) return null;
                  const label = primary.key.replace(/_/g, ' ');
                  const display =
                    primary.key === 'Revenue' || primary.key === 'Gross_Profit'
                      ? formatCurrencyShort(primary.value)
                      : (() => {
                          const numVal = Number(primary.value);
                          return Number.isNaN(numVal) ? String(primary.value) : numVal.toLocaleString();
                        })();
                  return (
                    <p className="text-sm text-white font-semibold mt-1">
                      {label}: {display}
                    </p>
                  );
                })()}
              </div>
              <button
                onClick={closeDrill}
                className="text-white hover:bg-white/20 rounded-lg p-1.5 transition"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="p-4 overflow-y-auto flex-1">
              <p className="text-sm font-medium text-gray-700 mb-2">Break this down by:</p>
              <div className="flex flex-wrap gap-2 mb-4">
                {availableBreakdowns.length === 0 && (
                  <p className="text-sm text-gray-500 italic">
                    No further breakdown available for this row.
                  </p>
                )}
                {availableBreakdowns.map((b) => (
                  <button
                    key={b.key}
                    onClick={() => runDrillDown(b.key)}
                    className={
                      drillBreakdown === b.key
                        ? 'px-3 py-1.5 text-sm rounded-full bg-amber-500 text-white border border-amber-600'
                        : 'px-3 py-1.5 text-sm rounded-full bg-white text-gray-700 border border-gray-300 hover:bg-amber-50 hover:border-amber-400'
                    }
                    disabled={drillLoading}
                  >
                    {b.label}
                  </button>
                ))}
              </div>

              {drillLoading && (
                <div className="flex items-center gap-2 text-sm text-gray-600 py-6 justify-center">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading breakdown…
                </div>
              )}

              {drillError && (
                <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
                  {drillError}
                </div>
              )}

              {drillResult && !drillLoading && (
                <DrillResultView result={drillResult} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Renders the breakdown result returned by /ai/chatbot/drill-down
const DrillResultView = ({ result }) => {
  const rows = Array.isArray(result?.rows) ? result.rows : [];
  if (!rows.length) {
    return (
      <p className="text-sm text-gray-600 italic py-4">
        No breakdown data available for this slice.
      </p>
    );
  }
  // Determine which dimension column is the breakdown key (e.g. Customer)
  const breakdownDim = (result.breakdown_by || '')
    .replace(/_(.)/g, (_, c) => c.toUpperCase())
    .replace(/^(.)/, (c) => c.toUpperCase());
  const dimKey = Object.keys(rows[0]).find(
    (k) => k.toLowerCase() === breakdownDim.toLowerCase()
  ) || Object.keys(rows[0])[0];

  // Pick a measure to show in the bar chart
  const measureKey = ['Revenue', 'Gross_Profit', 'Cases'].find((m) => m in rows[0]) || null;

  const total = Number(result.total) || 0;

  return (
    <div className="space-y-3">
      {measureKey && total > 0 && (
        <p className="text-xs text-gray-600">
          Total {measureKey.replace(/_/g, ' ')}:{' '}
          <span className="font-semibold text-gray-800">
            {measureKey === 'Revenue' || measureKey === 'Gross_Profit'
              ? formatCurrencyShort(total)
              : total.toLocaleString()}
          </span>
        </p>
      )}

      {/* Horizontal bar list */}
      {measureKey && (
        <div className="space-y-1.5">
          {rows.map((r, i) => {
            const share = Number(r.share_pct) || 0;
            const value = Number(r[measureKey]) || 0;
            const display =
              measureKey === 'Revenue' || measureKey === 'Gross_Profit'
                ? formatCurrencyShort(value)
                : value.toLocaleString();
            return (
              <div key={i} className="text-xs">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="font-medium text-gray-800 truncate pr-2" title={String(r[dimKey])}>
                    {String(r[dimKey] ?? '—')}
                  </span>
                  <span className="text-gray-600 whitespace-nowrap">
                    {display} <span className="text-gray-400">({share}%)</span>
                  </span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(100, Math.max(0, share))}%`,
                      background: 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detail table */}
      <div className="overflow-x-auto pt-2 border-t border-gray-100">
        <table className="min-w-full text-xs border-collapse">
          <thead>
            <tr className="bg-gray-50">
              {Object.keys(rows[0]).map((col, idx) => (
                <th
                  key={idx}
                  className="border border-gray-200 px-2 py-1.5 text-left font-semibold text-gray-700"
                >
                  {col.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, ri) => (
              <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                {Object.keys(rows[0]).map((col, ci) => {
                  let cell = r[col];
                  if ((col === 'Revenue' || col === 'Gross_Profit') && cell !== undefined && cell !== null) {
                    cell = formatCurrencyShort(cell);
                  } else if (col === 'Cases' && cell !== undefined && cell !== null) {
                    const n = Number(cell);
                    cell = Number.isNaN(n) ? cell : n.toLocaleString();
                  } else if (col === 'Margin_%' && cell !== undefined && cell !== null) {
                    cell = `${cell}%`;
                  } else if (col === 'share_pct' && cell !== undefined && cell !== null) {
                    cell = `${cell}%`;
                  }
                  return (
                    <td key={ci} className="border border-gray-200 px-2 py-1.5 text-gray-700">
                      {cell !== undefined && cell !== null ? String(cell) : '-'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AIAssistant;