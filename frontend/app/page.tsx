"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";

interface ChatSource {
  document_title: string;
  score?: number;
}

interface Message {
  id: string;
  role: "customer" | "assistant";
  content: string;
  sources?: ChatSource[];
  leadCaptured?: boolean;
  timestamp: string;
}

interface BusinessInfo {
  id: string;
  name: string;
  description: string;
  address: string;
  phone: string;
  email: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SUGGESTED_QUESTIONS = [
  "What services do you provide?",
  "How much does teeth cleaning cost?",
  "I want to book teeth whitening. My name is Ali and my email is ali@example.com.",
  "What are your opening hours?",
  "Where are you located?",
  "Do you perform brain surgery?",
];

export default function ChatPage() {
  const [business, setBusiness] = useState<BusinessInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-msg",
      role: "assistant",
      content:
        "Welcome to Apex Dental Studio! I am your AI assistant, grounded in our clinic's official services, pricing, hours, and policies. How can I assist you today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Load demo business metadata
  useEffect(() => {
    async function loadBusiness() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/business/demo`);
        if (res.ok) {
          const data = await res.json();
          setBusiness(data);
        }
      } catch (err) {
        console.warn("Could not fetch demo business metadata, falling back to default.", err);
      }
    }
    loadBusiness();
  }, []);

  const handleSendMessage = async (userPrompt?: string) => {
    const textToSend = (userPrompt || inputValue).trim();
    if (!textToSend || isLoading) return;

    setApiError(null);
    const newCustomerMsg: Message = {
      id: "msg-" + Date.now(),
      role: "customer",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, newCustomerMsg]);
    if (!userPrompt) setInputValue("");
    setIsLoading(true);

    try {
      const payload: { message: string; business_id?: string } = {
        message: textToSend,
      };
      if (business?.id) {
        payload.business_id = business.id;
      }

      const res = await fetch(`${API_BASE}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        const errMsg = errorData?.detail || `API responded with status ${res.status}`;
        throw new Error(errMsg);
      }

      const data = await res.json();
      const assistantMsg: Message = {
        id: "msg-" + Date.now() + "-ai",
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        leadCaptured: data.lead?.created === true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to connect to AI chat service";
      setApiError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 antialiased">
      {/* Top Navbar */}
      <header className="flex-none border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-4 sm:px-8 py-3.5 z-20">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-sky-500/20">
              AD
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-semibold text-base sm:text-lg text-white tracking-tight leading-tight">
                  {business?.name || "Apex Dental Studio"}
                </h1>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  RAG Grounded
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {business?.address || "124 Pine Street, Suite 300, Seattle, WA"} • {business?.phone || "(555) 019-2831"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <Link
              href="/dashboard"
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors shadow-sm shadow-indigo-600/25 flex items-center gap-1.5"
            >
              <span>Owner Dashboard</span>
              <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Chat Layout */}
      <main className="flex-1 flex flex-col max-w-4xl w-full mx-auto p-4 sm:p-6 overflow-hidden">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1 sm:pr-2 scrollbar-thin scrollbar-thumb-slate-800">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === "customer" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 shadow-sm text-sm leading-relaxed ${
                  msg.role === "customer"
                    ? "bg-indigo-600 text-white rounded-br-xs"
                    : "bg-slate-900 border border-slate-800/90 text-slate-200 rounded-bl-xs"
                }`}
              >
                {/* Role header for assistant */}
                {msg.role === "assistant" && (
                  <div className="flex items-center gap-1.5 mb-1.5 text-xs text-sky-400 font-medium">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.523a9.014 9.014 0 01-5.46 0L5 14.5"
                      />
                    </svg>
                    <span>Apex Dental Assistant</span>
                  </div>
                )}

                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Grounding Sources Badge */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80">
                    <div className="text-[11px] font-medium text-slate-400 mb-1.5 flex items-center gap-1">
                      <svg className="w-3 h-3 text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Grounded Sources ({msg.sources.length})
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.sources.map((s, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800/90 text-slate-300 border border-slate-700/60"
                        >
                          <span>{s.document_title}</span>
                          {s.score !== undefined && (
                            <span className="text-emerald-400/90">
                              ({(s.score * 100).toFixed(0)}%)
                            </span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Subtle Customer-facing Lead Captured Confirmation (No internal score exposed) */}
                {msg.leadCaptured && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center gap-2 text-xs text-emerald-400 font-medium bg-emerald-950/20 px-3 py-2 rounded-lg border border-emerald-800/30">
                    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>Thanks! We&apos;ve captured your request and will follow up with you.</span>
                  </div>
                )}
              </div>

              {/* Timestamp */}
              <span className="text-[11px] text-slate-500 mt-1 px-1">{msg.timestamp}</span>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex flex-col items-start">
              <div className="max-w-[75%] rounded-2xl rounded-bl-xs p-4 bg-slate-900 border border-slate-800/90 shadow-sm text-slate-400 text-sm flex items-center gap-3">
                <div className="flex space-x-1.5">
                  <div className="w-2 h-2 bg-sky-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" />
                </div>
                <span className="text-xs text-slate-400">Retrieving business knowledge & generating answer...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* API Error Notification */}
        {apiError && (
          <div className="my-2 p-3 rounded-xl bg-red-950/60 border border-red-800/80 text-red-200 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{apiError}</span>
            </div>
            <button
              onClick={() => setApiError(null)}
              className="text-red-400 hover:text-red-200 text-xs underline font-medium ml-3 cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Suggested Question Chips */}
        <div className="pt-3 pb-2 flex items-center gap-2 overflow-x-auto no-scrollbar">
          <span className="text-[11px] font-medium text-slate-500 flex-shrink-0">Try Demo:</span>
          {SUGGESTED_QUESTIONS.map((question, i) => (
            <button
              key={i}
              type="button"
              disabled={isLoading}
              onClick={() => handleSendMessage(question)}
              className="flex-shrink-0 text-xs px-3 py-1 rounded-full bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-colors cursor-pointer disabled:opacity-50"
            >
              {question}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="pt-2">
          <div className="relative flex items-center">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about dental services, booking, pricing, or hours..."
              disabled={isLoading}
              className="w-full pl-4 pr-24 py-3.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder:text-slate-500 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            />
            <button
              type="button"
              onClick={() => handleSendMessage()}
              disabled={isLoading || !inputValue.trim()}
              className="absolute right-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 cursor-pointer shadow-sm shadow-indigo-600/30"
            >
              <span>Send</span>
              <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </div>
          <p className="text-[11px] text-center text-slate-500 mt-2">
            Apex Dental Studio AI uses grounded RAG semantic retrieval over official clinic documents.
          </p>
        </div>
      </main>
    </div>
  );
}
