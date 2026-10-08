import { NextRequest, NextResponse } from "next/server";
import { checkPassword, createSessionCookieValue, SESSION_COOKIE_NAME } from "@/lib/auth";

export async function POST(req: NextRequest) {
  const { password } = await req.json();

  if (typeof password !== "string" || !checkPassword(password)) {
    return NextResponse.json({ error: "Incorrect password" }, { status: 401 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE_NAME, createSessionCookieValue(), {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
  return res;
}
