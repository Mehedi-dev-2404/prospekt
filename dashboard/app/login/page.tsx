"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });

    if (res.ok) {
      router.push(params.get("next") || "/jobs");
      router.refresh();
    } else {
      setError("Incorrect password");
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-surface rounded-2xl p-6 shadow-xl border border-border"
    >
      <label className="block text-sm font-semibold text-text mb-2">
        Password
      </label>
      <input
        autoFocus
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="w-full rounded-lg border border-border px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-bright"
        placeholder="••••••••"
      />
      {error && <p className="text-danger text-sm mt-2">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="mt-4 w-full bg-teal-bright hover:bg-teal text-white font-semibold text-sm rounded-lg py-2.5 transition-colors disabled:opacity-60"
      >
        {loading ? "Checking…" : "Sign in"}
      </button>
    </form>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-navy px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <span className="text-2xl font-extrabold text-white tracking-tight">
            Prosp<span className="text-teal-bright">ekt</span>
          </span>
          <p className="text-white/50 text-sm mt-1">Pipeline Dashboard</p>
        </div>
        <Suspense fallback={null}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
