"use client";

import React, { useState } from "react";

interface Issue {
  tool: string;
  category: string;
  severity: "high" | "medium" | "low" | "warning" | "info";
  message: string;
  filepath: string;
  line: number;
  test_id: string;
  code?: string;
  explanation?: string;
  duplicate_file?: string;
  duplicate_start?: number;
  duplicate_end?: number;
}

interface SecurityPanelProps {
  issues: Issue[];
}

export default function SecurityPanel({ issues }: SecurityPanelProps) {
  const [search, setSearch] = useState("");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "medium":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "low":
      case "warning":
        return "bg-yellow-500/10 text-yellow-300 border-yellow-500/20";
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700";
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case "security":
        return "bg-purple-500/10 text-purple-400 border-purple-500/20";
      case "quality":
        return "bg-teal-500/10 text-teal-400 border-teal-500/20";
      case "maintainability":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700";
    }
  };

  // Filtering logic
  const filteredIssues = issues.filter((issue) => {
    const matchesSearch =
      issue.filepath.toLowerCase().includes(search.toLowerCase()) ||
      issue.message.toLowerCase().includes(search.toLowerCase());

    const matchesSeverity =
      filterSeverity === "all" ||
      issue.severity.toLowerCase() === filterSeverity.toLowerCase() ||
      (filterSeverity === "low" && issue.severity.toLowerCase() === "warning");

    const matchesCategory =
      filterCategory === "all" ||
      issue.category.toLowerCase() === filterCategory.toLowerCase();

    return matchesSearch && matchesSeverity && matchesCategory;
  });

  const toggleExpand = (index: number) => {
    if (expandedIndex === index) {
      setExpandedIndex(null);
    } else {
      setExpandedIndex(index);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-4 p-4 bg-zinc-900 border border-zinc-800 rounded-xl">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by filename or keyword..."
          className="flex-1 px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-zinc-100 placeholder:text-zinc-500 text-sm focus:outline-none focus:border-purple-500"
        />

        <div className="flex flex-wrap gap-3">
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-zinc-300 text-sm focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Severities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low / Warning</option>
          </select>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-zinc-300 text-sm focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Categories</option>
            <option value="security">Security</option>
            <option value="quality">Quality</option>
            <option value="maintainability">Maintainability</option>
          </select>
        </div>
      </div>

      {/* Issues Count */}
      <div className="text-sm text-zinc-400">
        Showing <span className="font-semibold text-zinc-200">{filteredIssues.length}</span> of{" "}
        <span className="font-semibold text-zinc-200">{issues.length}</span> issues
      </div>

      {/* Issues List */}
      {filteredIssues.length === 0 ? (
        <div className="text-center py-12 bg-zinc-900/20 border border-zinc-800 rounded-xl text-zinc-500 text-sm">
          No matching issues found. Codebase is clean in this section!
        </div>
      ) : (
        <div className="space-y-4">
          {filteredIssues.map((issue, index) => {
            const isExpanded = expandedIndex === index;
            return (
              <div
                key={index}
                className={`border rounded-xl transition-colors overflow-hidden ${
                  isExpanded ? "border-purple-500 bg-zinc-900" : "border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900 hover:border-zinc-700"
                }`}
              >
                {/* Header Section (Clickable) */}
                <div
                  onClick={() => toggleExpand(index)}
                  className="flex flex-col md:flex-row md:items-center justify-between p-5 gap-4 cursor-pointer select-none"
                >
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap gap-2 items-center">
                      <span
                        className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 border rounded-full ${getSeverityColor(
                          issue.severity
                        )}`}
                      >
                        {issue.severity}
                      </span>
                      <span
                        className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 border rounded-full ${getCategoryColor(
                          issue.category
                        )}`}
                      >
                        {issue.category}
                      </span>
                      <span className="text-xs text-zinc-500 font-mono bg-zinc-950 px-2 py-0.5 rounded border border-zinc-850">
                        {issue.tool}
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-white leading-snug">{issue.message}</h4>
                    <p className="text-xs text-zinc-400 font-mono">
                      {issue.filepath}:{issue.line}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-purple-400 font-medium">
                      {isExpanded ? "Collapse" : "Explain & View Code"}
                    </span>
                    <svg
                      className={`w-4 h-4 text-zinc-500 transform transition-transform ${isExpanded ? "rotate-180" : ""}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {/* Expanded Details Section */}
                {isExpanded && (
                  <div className="p-5 border-t border-zinc-800 bg-zinc-950/60 space-y-6">
                    {/* Code Snippet */}
                    {issue.code && (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">
                          Affected Code Snippet
                        </span>
                        <div className="overflow-x-auto p-4 bg-zinc-950 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-300 leading-relaxed max-h-60">
                          <pre className="whitespace-pre-wrap">{issue.code}</pre>
                        </div>
                      </div>
                    )}

                    {/* LLM Explanation */}
                    {issue.explanation && (
                      <div className="space-y-2 p-5 bg-purple-950/20 border border-purple-500/20 rounded-lg">
                        <div className="flex items-center gap-2 mb-2 text-purple-400">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                            />
                          </svg>
                          <span className="text-xs font-bold uppercase tracking-wider">
                            AI Explanation & Remediation
                          </span>
                        </div>
                        <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">
                          {issue.explanation}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
