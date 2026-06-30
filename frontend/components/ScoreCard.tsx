"use client";

import React from "react";

interface Scores {
  security_score: number;
  quality_score: number;
  maintainability_score: number;
  overall_score: number;
}

interface ScoreCardProps {
  scores: Scores;
}

export default function ScoreCard({ scores }: ScoreCardProps) {
  const getScoreColorClass = (score: number) => {
    if (score >= 80) return "text-emerald-400 border-emerald-500/20 bg-emerald-500/5";
    if (score >= 50) return "text-amber-400 border-amber-500/20 bg-amber-500/5";
    return "text-rose-400 border-rose-500/20 bg-rose-500/5";
  };

  const getScoreColorRaw = (score: number) => {
    if (score >= 80) return "rgb(16, 185, 129)"; // emerald-500
    if (score >= 50) return "rgb(245, 158, 11)"; // amber-500
    return "rgb(244, 63, 94)"; // rose-500
  };

  const { overall_score, security_score, quality_score, maintainability_score } = scores;

  // Circle properties for overall progress
  const radius = 50;
  const strokeWidth = 8;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (overall_score / 100) * circumference;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 p-6 bg-zinc-900/60 border border-zinc-800 rounded-2xl backdrop-blur-md shadow-2xl">
      {/* Overall Score Circle */}
      <div className="flex flex-col items-center justify-center p-6 border border-zinc-800 bg-zinc-950/40 rounded-xl">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4">
          Overall Rating
        </span>
        <div className="relative flex items-center justify-center w-32 h-32">
          <svg className="w-full h-full transform -rotate-90">
            {/* Background track circle */}
            <circle
              className="text-zinc-800"
              strokeWidth={strokeWidth}
              stroke="currentColor"
              fill="transparent"
              r={normalizedRadius}
              cx={radius + strokeWidth}
              cy={radius + strokeWidth}
            />
            {/* Foreground progress circle */}
            <circle
              strokeWidth={strokeWidth}
              strokeDasharray={circumference + " " + circumference}
              style={{ strokeDashoffset, stroke: getScoreColorRaw(overall_score), transition: "stroke-dashoffset 0.8s ease" }}
              strokeLinecap="round"
              fill="transparent"
              r={normalizedRadius}
              cx={radius + strokeWidth}
              cy={radius + strokeWidth}
            />
          </svg>
          <div className="absolute text-3xl font-extrabold text-white tracking-tight">
            {overall_score}%
          </div>
        </div>
      </div>

      {/* Security Score Card */}
      <div className={`flex flex-col justify-between p-6 border rounded-xl transition-all hover:scale-[1.02] ${getScoreColorClass(security_score)}`}>
        <div>
          <h3 className="text-zinc-400 font-medium text-sm mb-1">Security Score</h3>
          <p className="text-xs text-zinc-500 mb-4">Vulnerability & rules status</p>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-black text-white">{security_score}</span>
          <span className="text-sm text-zinc-400">/100</span>
        </div>
      </div>

      {/* Code Quality Score Card */}
      <div className={`flex flex-col justify-between p-6 border rounded-xl transition-all hover:scale-[1.02] ${getScoreColorClass(quality_score)}`}>
        <div>
          <h3 className="text-zinc-400 font-medium text-sm mb-1">Code Quality</h3>
          <p className="text-xs text-zinc-500 mb-4">Duplicate code & patterns</p>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-black text-white">{quality_score}</span>
          <span className="text-sm text-zinc-400">/100</span>
        </div>
      </div>

      {/* Maintainability Score Card */}
      <div className={`flex flex-col justify-between p-6 border rounded-xl transition-all hover:scale-[1.02] ${getScoreColorClass(maintainability_score)}`}>
        <div>
          <h3 className="text-zinc-400 font-medium text-sm mb-1">Maintainability</h3>
          <p className="text-xs text-zinc-500 mb-4">Complexity & function length</p>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-black text-white">{maintainability_score}</span>
          <span className="text-sm text-zinc-400">/100</span>
        </div>
      </div>
    </div>
  );
}
