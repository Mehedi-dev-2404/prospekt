import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

const COOKIE_NAME = "prospekt_session";
const SESSION_VALUE = "authenticated";

function verify(value: string | undefined, secret: string): boolean {
  if (!value) return false;
  const [val, sig] = value.split(".");
  if (!val || !sig || val !== SESSION_VALUE) return false;
  const expected = crypto.createHmac("sha256", secret).update(val).digest("hex");
  if (expected.length !== sig.length) return false;
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(sig));
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (
    pathname.startsWith("/login") ||
    pathname.startsWith("/api/login") ||
    pathname.startsWith("/_next") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  const secret = process.env.SESSION_SECRET;
  const cookie = req.cookies.get(COOKIE_NAME)?.value;

  if (!secret || !verify(cookie, secret)) {
    const loginUrl = new URL("/login", req.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image).*)"],
  runtime: "nodejs",
};
