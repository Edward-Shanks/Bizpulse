import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Bot, X, Send, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const AIAssistant = () => {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
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
    const msgToSend = messageText || input.trim();
    if (!msgToSend) return;

    const userMessage = { role: 'user', content: msgToSend };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build conversation history from previous messages
      const conversationHistory = messages.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      const payload = {
        message: msgToSend,
        chart_title: 'General Business Intelligence Query',
        context: {},
        session_id: sessionId.current,
        conversation_history: conversationHistory
      };

      const response = await axios.post(`${API}/insights/chat`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const fullResponse = response.data?.response || 'No response';
      const aiMessage = { role: 'ai', content: fullResponse };
      setMessages((prev) => [...prev, aiMessage]);
      
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
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white/20 rounded-lg p-2 transition"
            >
              <X className="w-5 h-5" />
            </button>
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
                      onClick={() => handleSendMessage(q)}
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
                    <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                  ) : (
                    <div className="prose prose-sm max-w-none break-words">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}

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
                      {streamingMessage}
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
                onClick={handleSendMessage}
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

export default AIAssistant;