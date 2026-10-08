import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { location, category } = await req.json();

  if (typeof location !== "string" || !location.trim()) {
    return NextResponse.json({ error: "Location is required" }, { status: 400 });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return NextResponse.json({ error: "BACKEND_URL is not configured" }, { status: 500 });
  }

  try {
    const res = await fetch(`${backendUrl}/pipeline/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location, category: category || undefined }),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json({ error: data.detail ?? "Backend rejected the request" }, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json({ error: "Could not reach the Prospekt backend" }, { status: 502 });
  }
}
