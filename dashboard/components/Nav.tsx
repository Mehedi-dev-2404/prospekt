"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const links = [
  { href: "/jobs", label: "Jobs" },
  { href: "/businesses", label: "Campaign Tracker" },
  { href: "/run", label: "New Run" },
];

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    await fetch("/api/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <nav className="bg-navy border-b border-black/10 sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/jobs" className="font-extrabold text-white text-lg tracking-tight">
            Prosp<span className="text-teal-bright">ekt</span>
          </Link>
          <div className="flex items-center gap-1">
            {links.map((l) => {
              const active = pathname?.startsWith(l.href);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`text-sm font-medium px-3 py-1.5 rounded-md transition-colors ${
                    active
                      ? "bg-white/10 text-white"
                      : "text-white/60 hover:text-white hover:bg-white/5"
                  }`}
                >
                  {l.label}
                </Link>
              );
            })}
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-white/50 hover:text-white font-medium"
        >
          Sign out
        </button>
      </div>
    </nav>
  );
}
