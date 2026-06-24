"use client";

import { useState } from "react";
import { useRepos, useCreateRepo } from "@/lib/hooks/useRepos";

const statusColors = {
  pending: "text-yellow-400",
  processing: "text-blue-400",
  ready: "text-green-400",
  failed: "text-red-400",
};

export default function Dashboard() {
  const [url, setUrl] = useState("");
  const { data: repos, isLoading } = useRepos();
  const createRepo = useCreateRepo();

  const handleAnalyze = async () => {
    if (!url.trim()) return;
    await createRepo.mutateAsync(url.trim());
    setUrl("");
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
      <p className="text-zinc-400 mb-10">Analyze any public GitHub repository</p>
      <div className="flex gap-3 mb-12">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
          placeholder="https://github.com/user/repo"
          className="flex-1 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-purple-500"
        />
        <button
          onClick={handleAnalyze}
          disabled={createRepo.isPending || !url.trim()}
          className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
        >
          {createRepo.isPending ? "Adding..." : "Analyze"}
        </button>
      </div>
      <div>
        <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-4">
          Repositories
        </h2>
        {isLoading && <p className="text-zinc-500">Loading...</p>}
        {repos?.length === 0 && (
          <p className="text-zinc-500">No repositories yet. Add one above.</p>
        )}
        <div className="space-y-3">
          {repos?.map((repo) => (
            <div
              key={repo.id}
              className="flex items-center justify-between p-4 bg-zinc-900 border border-zinc-800 rounded-lg"
            >
              <div>
                <p className="font-medium text-white">{repo.name}</p>
                <p className="text-sm text-zinc-500">{repo.github_url}</p>
              </div>
              <span className={"text-sm font-medium " + statusColors[repo.status]}>
                {repo.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
