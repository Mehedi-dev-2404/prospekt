import "server-only";
import crypto from "crypto";
import { cookies } from "next/headers";

const COOKIE_NAME = "prospekt_session";
const SESSION_VALUE = "authenticated";

function secret(): string {
  const s = process.env.SESSION_SECRET;
  if (!s) throw new Error("SESSION_SECRET must be set");
  return s;
}

function sign(value: string): string {
  return crypto.createHmac("sha256", secret()).update(value).digest("hex");
}

export function createSessionCookieValue(): string {
  return `${SESSION_VALUE}.${sign(SESSION_VALUE)}`;
}

export function verifySessionCookieValue(value: string | undefined): boolean {
  if (!value) return false;
  const [val, sig] = value.split(".");
  if (!val || !sig) return false;
  const expected = sign(val);
  if (expected.length !== sig.length) return false;
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(sig)) && val === SESSION_VALUE;
}

export async function isAuthenticated(): Promise<boolean> {
  const store = await cookies();
  return verifySessionCookieValue(store.get(COOKIE_NAME)?.value);
}

export function checkPassword(password: string): boolean {
  const expected = process.env.DASHBOARD_PASSWORD;
  if (!expected) throw new Error("DASHBOARD_PASSWORD must be set");
  if (password.length !== expected.length) return false;
  return crypto.timingSafeEqual(Buffer.from(password), Buffer.from(expected));
}

export const SESSION_COOKIE_NAME = COOKIE_NAME;
