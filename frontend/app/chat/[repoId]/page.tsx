"use client";

import { useState, useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import api from "@/lib/api";
import ScoreCard from "@/components/ScoreCard";
import SecurityPanel from "@/components/SecurityPanel";
import MermaidViewer from "@/components/MermaidViewer";

interface Source {
  filepath: string;
  start_line: number;
  end_line: number;
  score: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export default function ChatPage() {
  const params = useParams();
  const repoId = params.repoId as string;
  
  // Tab control
  const [activeTab, setActiveTab] = useState<"chat" | "security" | "architecture">("chat");

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scan State
  const [scanLoading, setScanLoading] = useState(false);
  const [scanResults, setScanResults] = useState<any>(null);
  const [scanError, setScanError] = useState<string | null>(null);

  // Architecture State
  const [archLoading, setArchLoading] = useState(false);
  const [archResults, setArchResults] = useState<any>(null);
  const [archError, setArchError] = useState<string | null>(null);

  useEffect(() => {
    if (activeTab === "chat") {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, activeTab]);

  useEffect(() => {
    if (activeTab === "architecture" && !archResults && !archLoading) {
      fetchArchitecture();
    }
  }, [activeTab]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const { data } = await api.post(`/api/v1/chat/${repoId}`, { question, history });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: Could not get response." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const runScan = async () => {
    setScanLoading(true);
    setScanError(null);
    try {
      const { data } = await api.get(`/api/v1/repos/${repoId}/scan`);
      setScanResults(data);
    } catch (err: any) {
      setScanError(err.response?.data?.detail || "Failed to scan repository.");
    } finally {
      setScanLoading(false);
    }
  };

  const fetchArchitecture = async () => {
    setArchLoading(true);
    setArchError(null);
    try {
      const { data } = await api.get(`/api/v1/repos/${repoId}/architecture`);
      setArchResults(data);
    } catch (err: any) {
      setArchError(err.response?.data?.detail || "Failed to generate architecture.");
    } finally {
      setArchLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950">
      {/* Top Header */}
      <div className="border-b border-zinc-800 px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-lg font-semibold text-white">Repository Workbench</h1>
          <p className="text-sm text-zinc-500">Analyze code and scan security metrics</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-zinc-850 bg-zinc-950 px-6">
        <button
          onClick={() => setActiveTab("chat")}
          className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors focus:outline-none cursor-pointer ${
            activeTab === "chat"
              ? "border-purple-500 text-white"
              : "border-transparent text-zinc-500 hover:text-zinc-300"
          }`}
        >
          Chat Assistant
        </button>
        <button
          onClick={() => setActiveTab("security")}
          className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors focus:outline-none cursor-pointer ${
            activeTab === "security"
              ? "border-purple-500 text-white"
              : "border-transparent text-zinc-500 hover:text-zinc-300"
          }`}
        >
          Security & Quality Scanner
        </button>
        <button
          onClick={() => setActiveTab("architecture")}
          className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors focus:outline-none cursor-pointer ${
            activeTab === "architecture"
              ? "border-purple-500 text-white"
              : "border-transparent text-zinc-500 hover:text-zinc-300"
          }`}
        >
          Architecture & README
        </button>
      </div>

      {/* Tab Contents */}
      <div className="flex-1 overflow-y-auto min-h-0 bg-zinc-950/30">
        {activeTab === "chat" ? (
          /* Chat Section */
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
              {messages.length === 0 && (
                <div className="text-center text-zinc-500 mt-20">
                  <p className="text-lg mb-2">Ask anything about this codebase</p>
                  <div className="flex flex-col gap-2 items-center">
                    {[
                      "How does authentication work?",
                      "What is the folder structure?",
                      "Explain the database models",
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => setInput(q)}
                        className="text-sm text-purple-400 hover:text-purple-300 border border-purple-400/20 rounded-lg px-4 py-2 transition-colors cursor-pointer"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-3xl ${
                      msg.role === "user" ? "bg-purple-600 text-white" : "bg-zinc-900 text-zinc-100"
                    } rounded-xl px-4 py-3`}
                  >
                    <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                      {msg.content}
                    </pre>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-zinc-700">
                        <p className="text-xs text-zinc-400 mb-2">Sources:</p>
                        <div className="flex flex-wrap gap-2">
                          {msg.sources.map((s, j) => (
                            <span
                              key={j}
                              className="text-xs bg-zinc-800 text-teal-400 px-2 py-1 rounded font-mono"
                            >
                              {s.filepath}:{s.start_line}-{s.end_line}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-zinc-900 rounded-xl px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></span>
                      <span
                        className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                        style={{ animationDelay: "150ms" }}
                      ></span>
                      <span
                        className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                        style={{ animationDelay: "300ms" }}
                      ></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
            {/* Input Form */}
            <div className="border-t border-zinc-800 px-4 py-4 bg-zinc-950">
              <div className="flex gap-3 max-w-4xl mx-auto">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Ask about the codebase..."
                  className="flex-1 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-purple-500 text-sm"
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors text-sm cursor-pointer"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        ) : activeTab === "security" ? (
          /* Security Scanner Section */
          <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
            {scanLoading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-4">
                <div className="relative w-16 h-16">
                  <span className="absolute inset-0 border-4 border-purple-500/20 rounded-full"></span>
                  <span className="absolute inset-0 border-4 border-t-purple-500 rounded-full animate-spin"></span>
                </div>
                <p className="text-zinc-300 font-medium text-sm animate-pulse">
                  Running Security Scans & Smell Detectors...
                </p>
                <p className="text-zinc-500 text-xs">
                  Analyzing dependencies, scanning for secrets, and computing quality metrics
                </p>
              </div>
            ) : scanError ? (
              <div className="p-6 bg-rose-500/10 border border-rose-500/20 rounded-xl space-y-4 text-center max-w-md mx-auto">
                <p className="text-rose-400 text-sm font-medium">{scanError}</p>
                <button
                  onClick={runScan}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-medium text-sm rounded-lg transition-colors cursor-pointer"
                >
                  Try Again
                </button>
              </div>
            ) : scanResults ? (
              <div className="space-y-8 animate-fadeIn">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">Repository Health Report</h2>
                    <p className="text-zinc-400 text-sm">Review identified security issues and quality smell list</p>
                  </div>
                  <button
                    onClick={runScan}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium text-sm rounded-lg transition-colors shadow-lg shadow-purple-500/10 cursor-pointer"
                  >
                    Re-run Audit
                  </button>
                </div>

                {/* Score Summary Gauges */}
                <ScoreCard scores={scanResults.scores} />

                {/* Issues Table/Cards */}
                <div className="space-y-4">
                  <h3 className="text-base font-bold text-white">Identified Vulnerabilities & Code Smells</h3>
                  <SecurityPanel issues={scanResults.issues} />
                </div>
              </div>
            ) : (
              /* Initial State (Scan not triggered yet) */
              <div className="flex flex-col items-center justify-center py-20 max-w-md mx-auto text-center space-y-6">
                <div className="p-4 bg-purple-600/10 border border-purple-500/20 rounded-full text-purple-400">
                  <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Start Repository Audit</h3>
                  <p className="text-zinc-400 text-sm mt-2 leading-relaxed">
                    Trigger a security and quality inspection to trace hardcoded secrets, dangerous function calls, excessive function complexity, and code duplication.
                  </p>
                </div>
                <button
                  onClick={runScan}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors shadow-lg shadow-purple-500/15 cursor-pointer"
                >
                  Scan Codebase
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Architecture Section */
          <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
            {archLoading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-4">
                <div className="relative w-16 h-16">
                  <span className="absolute inset-0 border-4 border-purple-500/20 rounded-full"></span>
                  <span className="absolute inset-0 border-4 border-t-purple-500 rounded-full animate-spin"></span>
                </div>
                <p className="text-zinc-300 font-medium text-sm animate-pulse">
                  Analyzing repository structure & generating architecture map...
                </p>
                <p className="text-zinc-500 text-xs">
                  Generating flowchart layers and structuring readme content
                </p>
              </div>
            ) : archError ? (
              <div className="p-6 bg-rose-500/10 border border-rose-500/20 rounded-xl space-y-4 text-center max-w-md mx-auto">
                <p className="text-rose-400 text-sm font-medium">{archError}</p>
                <button
                  onClick={fetchArchitecture}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-medium text-sm rounded-lg transition-colors cursor-pointer"
                >
                  Try Again
                </button>
              </div>
            ) : archResults ? (
              <div className="space-y-8 animate-fadeIn">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">System Architecture Map</h2>
                    <p className="text-zinc-400 text-sm">Visual flowchart of codebase layers and dependencies</p>
                  </div>
                  <button
                    onClick={fetchArchitecture}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium text-sm rounded-lg transition-colors shadow-lg shadow-purple-500/10 cursor-pointer"
                  >
                    Re-generate Map
                  </button>
                </div>

                {/* Render Mermaid flowcharts */}
                <MermaidViewer chart={archResults.mermaid_diagram} />

                {/* Render markdown readme contents */}
                <div className="space-y-4 border-t border-zinc-800 pt-8">
                  <div>
                    <h2 className="text-xl font-bold text-white">Auto-Generated README.md</h2>
                    <p className="text-zinc-400 text-sm">Overview, Core Features, and Setup guide</p>
                  </div>

                  <div className="p-6 bg-zinc-900/40 border border-zinc-800 rounded-xl max-h-[600px] overflow-y-auto leading-relaxed text-zinc-300 shadow-inner">
                    <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans">{archResults.readme_content}</pre>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}