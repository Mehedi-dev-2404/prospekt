import { NextRequest, NextResponse } from "next/server";
import { setPageApproval } from "@/lib/data";

export async function POST(req: NextRequest) {
  const { business_id, approved } = await req.json();

  if (typeof business_id !== "string" || typeof approved !== "boolean") {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }

  await setPageApproval(business_id, approved);
  return NextResponse.json({ ok: true });
}
