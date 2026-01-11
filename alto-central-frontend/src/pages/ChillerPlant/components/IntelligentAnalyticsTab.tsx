import React, { useState, useEffect, useCallback, useRef } from 'react';
import Plot from 'react-plotly.js';
import { Data, Layout } from 'plotly.js';
import { FiSend, FiCpu, FiUser, FiZap, FiTrendingUp, FiBarChart2, FiThermometer } from 'react-icons/fi';
import { API_ENDPOINTS } from '@/config/api';

// Types based on backend API spec
interface PlotlySpec {
  data: Data[];
  layout: Partial<Layout>;
}

interface ChartGenerationResponse {
  chart_id: string | null;
  plotly_spec: PlotlySpec | null;
  template_used: string | null;
  template_match_confidence: number | null;
  data_sources: string[];
  query_summary: string;
  message: string;
  suggestions: string[];
  error?: string;
}

interface TemplateListItem {
  template_id: string;
  title: string;
  description: string;
  category: 'performance' | 'energy' | 'equipment' | 'comparison' | 'forecast' | 'custom';
  created_by: 'system' | 'ai' | 'user';
  usage_count: number;
  tags: string[];
}

interface TemplateListResponse {
  templates: TemplateListItem[];
  total_count: number;
  builtin_count: number;
  custom_count: number;
}

// Chat message types
interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  chartData?: ChartGenerationResponse;
  isLoading?: boolean;
  isError?: boolean;
}

interface IntelligentAnalyticsTabProps {
  siteId: string;
}

const EXAMPLE_PROMPTS = [
  { icon: <FiTrendingUp className="w-3.5 h-3.5" />, text: 'Plant efficiency vs cooling load' },
  { icon: <FiBarChart2 className="w-3.5 h-3.5" />, text: 'Daily energy for last week' },
  { icon: <FiThermometer className="w-3.5 h-3.5" />, text: 'Temperature trends 24h' },
  { icon: <FiZap className="w-3.5 h-3.5" />, text: 'Compare chiller 1 and 2' },
];

const IntelligentAnalyticsTab: React.FC<IntelligentAnalyticsTabProps> = ({ siteId }) => {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentChart, setCurrentChart] = useState<ChartGenerationResponse | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [templates, setTemplates] = useState<TemplateListItem[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);

  // Auto-scroll to bottom when new messages added
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Fetch templates on mount
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const url = API_ENDPOINTS.aiAnalyticsTemplates(siteId);
        const response = await fetch(url);
        if (response.ok) {
          const data: TemplateListResponse = await response.json();
          setTemplates(data.templates);
        }
      } catch (err) {
        console.error('Failed to fetch templates:', err);
      } finally {
        setTemplatesLoading(false);
      }
    };
    fetchTemplates();
  }, [siteId]);

  // Generate chart from prompt with streaming
  const handleGenerate = useCallback(async (customPrompt?: string) => {
    const messageText = customPrompt || prompt;
    if (!messageText.trim()) return;

    const userMessageId = Date.now().toString();
    const assistantMessageId = (Date.now() + 1).toString();

    // Add user message
    const userMessage: ChatMessage = {
      id: userMessageId,
      type: 'user',
      content: messageText,
      timestamp: new Date(),
    };

    // Add loading assistant message
    const loadingMessage: ChatMessage = {
      id: assistantMessageId,
      type: 'assistant',
      content: 'Starting...',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setPrompt('');
    setLoading(true);

    try {
      const response = await fetch(API_ENDPOINTS.aiAnalyticsChartStream(siteId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: messageText }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      // Buffer for handling chunks that split across reads
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Append new data to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete lines (SSE events end with \n\n or \n)
        const lines = buffer.split('\n');
        // Keep the last potentially incomplete line in buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith('data: ')) {
            try {
              const jsonStr = trimmedLine.slice(6);
              const data = JSON.parse(jsonStr);

              if (data.event === 'progress') {
                // Update message with progress
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: data.message || 'Processing...' }
                    : msg
                ));
              } else if (data.event === 'complete') {
                // Final result
                const result: ChartGenerationResponse = data.result;
                console.log('SSE complete - plotly_spec:', result.plotly_spec);
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        content: result.message || 'Here is your chart.',
                        chartData: result,
                        isLoading: false,
                        isError: false,
                      }
                    : msg
                ));
                if (result.plotly_spec) {
                  setCurrentChart(result);
                }
              } else if (data.event === 'error') {
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        content: data.message || 'An error occurred.',
                        isLoading: false,
                        isError: true,
                      }
                    : msg
                ));
              }
            } catch (e) {
              console.warn('SSE JSON parse error:', e, 'Line:', trimmedLine.slice(0, 100));
            }
          }
        }
      }

      // Process any remaining data in buffer
      if (buffer.trim().startsWith('data: ')) {
        try {
          const data = JSON.parse(buffer.trim().slice(6));
          if (data.event === 'complete' && data.result?.plotly_spec) {
            console.log('SSE buffer complete - plotly_spec:', data.result.plotly_spec);
            setCurrentChart(data.result);
          }
        } catch (e) {
          console.warn('SSE buffer parse error:', e);
        }
      }
    } catch (err) {
      // Fallback to non-streaming API
      try {
        const response = await fetch(API_ENDPOINTS.aiAnalyticsChart(siteId), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: messageText }),
        });

        const data: ChartGenerationResponse = await response.json();

        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: data.error || data.message || 'Here is your chart.',
                chartData: data.error ? undefined : data,
                isLoading: false,
                isError: !!data.error,
              }
            : msg
        ));

        if (!data.error && data.plotly_spec) {
          setCurrentChart(data);
        }
      } catch (fallbackErr) {
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: 'Sorry, I encountered an error. Please try again.',
                isLoading: false,
                isError: true,
              }
            : msg
        ));
      }
    } finally {
      setLoading(false);
    }
  }, [siteId, prompt]);

  // Generate chart from template
  const handleTemplateSelect = async (template: TemplateListItem) => {
    const userMessageId = Date.now().toString();
    const assistantMessageId = (Date.now() + 1).toString();

    const userMessage: ChatMessage = {
      id: userMessageId,
      type: 'user',
      content: template.title,
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessage = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setLoading(true);

    try {
      const response = await fetch(API_ENDPOINTS.aiAnalyticsTemplateChart(siteId, template.template_id), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parameters: {} }),
      });

      const data: ChartGenerationResponse = await response.json();

      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? {
              ...msg,
              content: data.error || data.message || 'Here is your chart.',
              chartData: data.error ? undefined : data,
              isLoading: false,
              isError: !!data.error,
            }
          : msg
      ));

      if (!data.error && data.plotly_spec) {
        setCurrentChart(data);
      }
    } catch (err) {
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? {
              ...msg,
              content: 'Sorry, I encountered an error. Please try again.',
              isLoading: false,
              isError: true,
            }
          : msg
      ));
    } finally {
      setLoading(false);
    }
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Left Panel - Chat */}
      <div className="w-96 border-r flex flex-col overflow-hidden bg-white">
        {/* Header */}
        <div className="p-3 border-b bg-gray-50">
          <div className="flex items-center gap-2">
            <FiCpu className="w-5 h-5 text-[#0E7EE4]" />
            <span className="font-medium text-[#272E3B]">AI Analytics Chat</span>
          </div>
        </div>

        {/* Chat Messages */}
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-3 space-y-3">
          {messages.length === 0 ? (
            // Welcome + Quick prompts
            <div className="space-y-3">
              <div className="text-center py-4">
                <FiCpu className="w-10 h-10 text-[#0E7EE4] mx-auto mb-2" />
                <p className="text-sm text-gray-500">Ask me anything about your chiller plant data</p>
              </div>

              {/* Example prompts */}
              <div className="space-y-1.5">
                <div className="text-xs text-gray-400 px-1">Try these:</div>
                {EXAMPLE_PROMPTS.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleGenerate(example.text)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-left bg-gray-50 border border-gray-200 rounded-lg hover:border-[#0E7EE4] hover:bg-blue-50/30 transition-colors"
                  >
                    <span className="text-[#0E7EE4]">{example.icon}</span>
                    <span className="text-gray-700">{example.text}</span>
                  </button>
                ))}
              </div>

              {/* Templates */}
              {!templatesLoading && templates.length > 0 && (
                <div className="space-y-1.5 pt-2">
                  <div className="text-xs text-gray-400 px-1">Templates:</div>
                  {templates.slice(0, 5).map((template) => (
                    <button
                      key={template.template_id}
                      onClick={() => handleTemplateSelect(template)}
                      className="w-full px-3 py-2 text-xs text-left bg-gray-50 border border-gray-200 rounded-lg hover:border-[#0E7EE4] hover:bg-blue-50/30 transition-colors"
                    >
                      <div className="font-medium text-gray-700">{template.title}</div>
                      <div className="text-gray-500 truncate">{template.description}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            // Chat messages
            messages.map((msg) => (
              <div key={msg.id} className={`flex gap-2 ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.type === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-[#0E7EE4] flex items-center justify-center flex-shrink-0">
                    <FiCpu className="w-3.5 h-3.5 text-white" />
                  </div>
                )}

                <div className={`max-w-[85%] ${msg.type === 'user' ? 'order-first' : ''}`}>
                  <div className={`rounded-2xl px-3 py-2 text-sm ${
                    msg.type === 'user'
                      ? 'bg-[#0E7EE4] text-white rounded-br-sm'
                      : msg.isError
                        ? 'bg-red-50 text-red-700 border border-red-200 rounded-bl-sm'
                        : 'bg-gray-100 text-[#272E3B] rounded-bl-sm'
                  }`}>
                    {msg.isLoading ? (
                      <div className="flex items-center gap-1.5 py-1">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>

                  {/* Suggestions */}
                  {msg.chartData?.suggestions && msg.chartData.suggestions.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {msg.chartData.suggestions.slice(0, 3).map((suggestion, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleGenerate(suggestion)}
                          disabled={loading}
                          className="px-2 py-1 text-[10px] bg-white border border-gray-200 text-gray-600 rounded-full hover:border-[#0E7EE4] hover:text-[#0E7EE4] transition-colors disabled:opacity-50"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {msg.type === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
                    <FiUser className="w-3.5 h-3.5 text-gray-600" />
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Input Area */}
        <div className="border-t p-3 bg-white">
          <div className="flex items-end gap-2">
            <textarea
              ref={(el) => {
                if (el) {
                  el.style.height = 'auto';
                  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
                }
              }}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your data..."
              rows={1}
              className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:border-[#0E7EE4] focus:ring-1 focus:ring-[#0E7EE4] resize-none overflow-y-auto"
              style={{ minHeight: '38px', maxHeight: '120px' }}
            />
            <button
              onClick={() => handleGenerate()}
              disabled={loading || !prompt.trim()}
              className="p-2 bg-[#0E7EE4] text-white rounded-lg hover:bg-[#0a6bc4] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            >
              <FiSend className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel - Big Chart Display */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gray-50 p-4">
        {!currentChart ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <FiBarChart2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-400">Your chart will appear here</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col bg-white rounded-lg border border-gray-200 overflow-hidden">
            {/* Chart */}
            <div className="flex-1 min-h-0 p-2">
              <Plot
                data={currentChart.plotly_spec!.data as Data[]}
                layout={(() => {
                  const backendLayout = currentChart.plotly_spec!.layout as Record<string, any>;
                  const traces = currentChart.plotly_spec!.data as Record<string, any>[];

                  // Check if any trace uses secondary y-axis
                  const hasYaxis2 = traces.some(trace => trace.yaxis === 'y2');

                  // Build layout with proper yaxis2 support
                  const layout: Record<string, any> = {
                    ...backendLayout,
                    autosize: true,
                    margin: {
                      l: backendLayout?.margin?.l || 60,
                      r: hasYaxis2 ? Math.max(backendLayout?.margin?.r || 80, 100) : (backendLayout?.margin?.r || 60),
                      t: Math.max(backendLayout?.margin?.t || 60, 70), // Extra top margin for modebar
                      b: backendLayout?.margin?.b || 60,
                    },
                    // Position legend below the modebar
                    legend: {
                      ...backendLayout?.legend,
                      y: backendLayout?.legend?.y ?? 0.95,
                    },
                  };

                  // Always create yaxis2 when traces reference it
                  if (hasYaxis2) {
                    // Find the trace that uses y2 for its name (for axis title)
                    const y2Trace = traces.find(trace => trace.yaxis === 'y2');
                    layout.yaxis2 = {
                      title: backendLayout?.yaxis2?.title || y2Trace?.name || 'Secondary Axis',
                      side: 'right',
                      overlaying: 'y',
                      showgrid: false,
                      ...backendLayout?.yaxis2,
                      // Force these properties to ensure axis shows
                      anchor: 'x',
                    };
                  }

                  // Debug: log layout to console
                  console.log('Plotly layout:', layout);

                  return layout as Partial<Layout>;
                })()}
                config={{
                  responsive: true,
                  displayModeBar: 'hover',
                  displaylogo: false,
                  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                }}
                useResizeHandler
                style={{ width: '100%', height: '100%' }}
              />
            </div>

            {/* Chart Info Footer */}
            <div className="px-4 py-3 border-t bg-gray-50 flex items-center gap-3 flex-wrap">
              {currentChart.template_used && (
                <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                  Template: {currentChart.template_used}
                </span>
              )}
              {currentChart.data_sources.length > 0 && (
                <span className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded">
                  Sources: {currentChart.data_sources.join(', ')}
                </span>
              )}
              {currentChart.query_summary && (
                <span className="text-xs text-gray-500">{currentChart.query_summary}</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligentAnalyticsTab;
