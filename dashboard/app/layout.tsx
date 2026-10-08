import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Nav from "@/components/Nav";
import { isAuthenticated } from "@/lib/auth";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Prospekt Dashboard",
  description: "Pipeline operations dashboard for Prospekt",
};

// Every route is gated by a cookie-based session check, so nothing here is
// ever safe to statically prerender.
export const instant = false;

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const authed = await isAuthenticated();

  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-bg text-text">
        {authed && <Nav />}
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
