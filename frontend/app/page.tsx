import Link from "next/link";

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4 text-center">
      <div className="max-w-2xl">
        <div className="inline-block px-3 py-1 mb-6 text-xs font-medium text-purple-400 border border-purple-400/30 rounded-full bg-purple-400/10">
          AI-Powered Code Intelligence
        </div>
        <h1 className="text-5xl font-bold tracking-tight text-white mb-6 leading-tight">
          Understand Any Codebase{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-teal-400">
            with AI
          </span>
        </h1>
        <p className="text-lg text-zinc-400 mb-10 leading-relaxed">
          Analyze, review, and chat with any GitHub repository.
          Get security scores, architecture diagrams, and AI-powered insights instantly.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
          >
            Analyze a Repository
          </Link>
        </div>
      </div>
    </main>
  );
}
