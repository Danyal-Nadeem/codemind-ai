"use client";

import { useState, useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import api from "@/lib/api";

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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const { data } = await api.post(`/api/v1/chat/${repoId}`, { question, history });
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer, sources: data.sources }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Error: Could not get response." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950">
      <div className="border-b border-zinc-800 px-6 py-4">
        <h1 className="text-lg font-semibold text-white">Chat with Repository</h1>
        <p className="text-sm text-zinc-500">Ask anything about this codebase</p>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-zinc-500 mt-20">
            <p className="text-lg mb-2">Ask anything about this codebase</p>
            <div className="flex flex-col gap-2 items-center">
              {["How does authentication work?", "What is the folder structure?", "Explain the database models"].map((q) => (
                <button key={q} onClick={() => setInput(q)} className="text-sm text-purple-400 hover:text-purple-300 border border-purple-400/20 rounded-lg px-4 py-2 transition-colors">{q}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-3xl ${msg.role === "user" ? "bg-purple-600 text-white" : "bg-zinc-900 text-zinc-100"} rounded-xl px-4 py-3`}>
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{msg.content}</pre>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-zinc-700">
                  <p className="text-xs text-zinc-400 mb-2">Sources:</p>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((s, j) => (
                      <span key={j} className="text-xs bg-zinc-800 text-teal-400 px-2 py-1 rounded font-mono">{s.filepath}:{s.start_line}-{s.end_line}</span>
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
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: "150ms"}}></span>
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: "300ms"}}></span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-zinc-800 px-4 py-4">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendMessage()} placeholder="Ask about the codebase..." className="flex-1 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-purple-500" />
          <button onClick={sendMessage} disabled={loading || !input.trim()} className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors">Send</button>
        </div>
      </div>
    </div>
  );
}