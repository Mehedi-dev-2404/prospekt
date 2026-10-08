"use client";

import { useState } from "react";
import Link from "next/link";

export default function RunPage() {
  const [location, setLocation] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ job_id: string } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    const res = await fetch("/api/trigger-run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location, category }),
    });
    const data = await res.json();

    if (!res.ok) {
      setError(data.error ?? "Something went wrong");
    } else {
      setResult(data);
    }
    setLoading(false);
  }

  return (
    <div className="max-w-lg mx-auto px-4 sm:px-6 py-10">
      <h1 className="text-2xl font-extrabold text-navy tracking-tight mb-1">Start a New Run</h1>
      <p className="text-text-secondary text-sm mb-6">
        Discover local businesses, score their websites, and queue them for approval.
      </p>

      <form onSubmit={handleSubmit} className="bg-surface border border-border rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-semibold text-text mb-1.5">Location</label>
          <input
            required
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Brixton, London"
            className="w-full rounded-lg border border-border px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-bright"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-text mb-1.5">Category (optional)</label>
          <input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="barbershops"
            className="w-full rounded-lg border border-border px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-bright"
          />
        </div>
        {error && <p className="text-danger text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-teal-bright hover:bg-teal text-white font-semibold text-sm rounded-lg py-2.5 transition-colors disabled:opacity-60"
        >
          {loading ? "Starting…" : "Start Pipeline Run"}
        </button>
      </form>

      {result && (
        <div className="mt-5 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-sm">
          <p className="font-semibold text-emerald-800">Pipeline started.</p>
          <Link href={`/jobs/${result.job_id}`} className="text-teal font-medium hover:underline">
            View run →
          </Link>
        </div>
      )}
    </div>
  );
}
