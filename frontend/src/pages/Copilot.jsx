import React, { useState, useRef, useEffect } from 'react';
import { 
  Bot, 
  Send, 
  User, 
  Sparkles, 
  ShieldCheck, 
  FileText, 
  Layers, 
  AlertTriangle, 
  CheckCircle2, 
  HelpCircle,
  CornerDownRight
} from 'lucide-react';
import { runAgentQuery } from '../api/copilot';
import AdvisoryNotice from '../components/common/AdvisoryNotice';
import RiskBadge from '../components/common/RiskBadge';

const STARTER_QUESTIONS = [
  "Which products are at risk of stockout?",
  "Why is SKU-102 at high risk?",
  "Which suppliers have the most delays?",
  "What does Supplier ABC's contract say about late delivery?",
  "What happens if Supplier SUP-001 is delayed by 7 days?",
  "What happens if SKU-102 demand increases by 20%?",
];

export default function Copilot() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Hello! I am your **SupplyChain AI Copilot**, powered by LangGraph, pgvector RAG, XGBoost forecasting, and a deterministic inventory risk engine. How can I assist your supply chain decisions today?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendQuestion = async (queryText) => {
    const q = queryText || inputQuestion;
    if (!q.trim() || loading) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuestion('');
    setLoading(true);

    try {
      const response = await runAgentQuery({ question: q });
      
      const botMsg = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: response.answer || response.summary || "Completed query analysis.",
        summary: response.summary,
        intent: response.intent,
        riskLevel: response.risk_level,
        affectedProducts: response.affected_products || [],
        recommendedActions: response.recommended_actions || [],
        sources: response.sources || [],
        dataUsed: response.data_used || [],
        warnings: response.warnings || [],
        toolTrace: response.tool_trace || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errorMsg = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        isError: true,
        text: err?.message || "Your request could not be processed safely by security guardrails.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 flex flex-col h-[calc(100vh-6.5rem)]">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            AI Supply Chain Copilot
            <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-mono font-normal">
              LangGraph Multi-Tool
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Conversational decision support combining SQL, pgvector RAG, XGBoost ML, and deterministic risk rules.
          </p>
        </div>
      </div>

      <AdvisoryNotice compact />

      {/* Main Chat Interface */}
      <div className="flex-1 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl">
        {/* Messages Scroll Container */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-1 shadow-md shadow-indigo-500/20">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`space-y-3 max-w-3xl ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                {/* Message Content Bubble */}
                <div
                  className={`rounded-2xl p-5 text-sm leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-none'
                      : msg.isError
                      ? 'bg-rose-950/80 border border-rose-500/40 text-rose-200 rounded-tl-none'
                      : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none space-y-4'
                  }`}
                >
                  <div className="flex items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
                    <span className="font-mono text-[10px] text-slate-400 font-semibold uppercase">
                      {msg.sender === 'user' ? 'User Question' : msg.isError ? 'Security Guardrail Alert' : 'Copilot Analytical Answer'}
                    </span>
                    <span className="font-mono text-[10px] text-slate-500">{msg.timestamp}</span>
                  </div>

                  <p className="whitespace-pre-wrap font-sans text-xs sm:text-sm">{msg.text}</p>

                  {/* Structured Assistant Sections */}
                  {msg.sender === 'assistant' && !msg.isError && (
                    <>
                      {/* Risk Level Badge */}
                      {msg.riskLevel && (
                        <div className="flex items-center gap-2 pt-1 font-mono text-xs">
                          <span className="text-slate-400">Identified Risk Level:</span>
                          <RiskBadge level={msg.riskLevel} />
                        </div>
                      )}

                      {/* Affected Products Grid */}
                      {msg.affectedProducts && msg.affectedProducts.length > 0 && (
                        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
                          <p className="text-xs font-mono font-semibold text-indigo-300 uppercase">Impacted SKUs / Products</p>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {msg.affectedProducts.map((p, idx) => (
                              <div key={idx} className="p-2 rounded bg-slate-950 border border-slate-800/80 text-xs">
                                <span className="font-mono font-bold text-slate-200">{p.sku}</span>{' '}
                                <span className="text-slate-400">— {p.product_name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Advisory Recommendations */}
                      {msg.recommendedActions && msg.recommendedActions.length > 0 && (
                        <div className="p-3.5 rounded-lg bg-amber-950/40 border border-amber-500/30 space-y-2">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-semibold text-amber-300 uppercase flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                              Advisory Recommendation
                            </span>
                            <span className="text-[10px] text-amber-400/80 font-normal">Advisory Only — No Action Executed</span>
                          </div>
                          {msg.recommendedActions.map((rec, idx) => (
                            <div key={idx} className="space-y-1">
                              <p className="text-xs font-mono font-bold text-slate-100">
                                {rec.action} ({rec.recommended_order_quantity || 0} units)
                              </p>
                              {rec.reason && <p className="text-xs text-slate-300 leading-snug">{rec.reason}</p>}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Data Provenance & Cited Sources */}
                      {((msg.sources && msg.sources.length > 0) || (msg.dataUsed && msg.dataUsed.length > 0)) && (
                        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs font-mono">
                          <div className="flex items-center space-x-2 text-slate-400">
                            <FileText className="w-3.5 h-3.5 text-indigo-400" />
                            <span className="font-semibold text-slate-300">Trusted Sources & Engine Evidence:</span>
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.dataUsed?.map((dataSrc, idx) => (
                              <span key={`d-${idx}`} className="px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 text-[10px]">
                                {dataSrc}
                              </span>
                            ))}
                            {msg.sources?.map((src, idx) => (
                              <span key={`s-${idx}`} className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 text-[10px]">
                                {src.document_name || src.source || 'RAG Document Chunk'}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Safe High-Level Agent Execution Trace Timeline */}
                      {msg.toolTrace && msg.toolTrace.length > 0 && (
                        <details className="group pt-1">
                          <summary className="text-[11px] font-mono text-slate-400 hover:text-slate-200 cursor-pointer flex items-center gap-1.5">
                            <Layers className="w-3.5 h-3.5 text-indigo-400" />
                            <span>View Execution Audit Trace ({msg.toolTrace.length} Steps)</span>
                          </summary>
                          <div className="mt-2 p-3 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[11px] space-y-1.5">
                            {msg.toolTrace.map((trace, idx) => (
                              <div key={idx} className="flex items-center gap-2 text-slate-400">
                                <CornerDownRight className="w-3 h-3 text-slate-600 shrink-0" />
                                <span className="font-bold text-slate-200">{trace.step}</span>
                                <span className="text-emerald-400">• {trace.status}</span>
                                {trace.detail && <span className="text-slate-500">({trace.detail})</span>}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </>
                  )}
                </div>
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-1">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {/* Loading Thinking Indicator */}
          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md shadow-indigo-500/20 animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-950 border border-slate-800 rounded-2xl rounded-tl-none p-4 text-xs font-mono text-slate-400 flex items-center space-x-3">
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                <span>LangGraph Multi-Tool Agent reasoning and validating...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Clickable Starter Questions Chips */}
        <div className="p-3 bg-slate-950 border-t border-slate-800/80 overflow-x-auto flex items-center gap-2 shrink-0">
          <span className="text-[10px] font-mono text-slate-500 uppercase shrink-0 flex items-center gap-1">
            <HelpCircle className="w-3 h-3" /> Starter Prompts:
          </span>
          {STARTER_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              disabled={loading}
              onClick={() => handleSendQuestion(q)}
              className="text-xs bg-slate-900 hover:bg-indigo-600/20 text-slate-300 hover:text-indigo-300 border border-slate-800 hover:border-indigo-500/40 px-3 py-1 rounded-full whitespace-nowrap transition-all font-mono shrink-0 disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuestion();
          }}
          className="p-4 bg-slate-950 border-t border-slate-800 flex items-center gap-3 shrink-0"
        >
          <input
            type="text"
            placeholder="Ask a supply-chain question (e.g. Which products are at stockout risk?)..."
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            disabled={loading}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !inputQuestion.trim()}
            className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all shadow-lg shadow-indigo-600/30 flex items-center gap-2 disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
}
