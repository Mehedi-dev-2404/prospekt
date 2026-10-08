import { NextRequest, NextResponse } from "next/server";
import { setApprovalStatus } from "@/lib/data";

export async function POST(req: NextRequest) {
  const { business_id, status } = await req.json();

  if (typeof business_id !== "string" || !["approved", "rejected", null].includes(status)) {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }

  await setApprovalStatus(business_id, status);
  return NextResponse.json({ ok: true });
}
