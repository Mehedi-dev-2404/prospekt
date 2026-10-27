import { NextRequest, NextResponse } from "next/server";
import { getDemoHtml } from "@/lib/data";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ businessId: string }> }
) {
  const { businessId } = await params;
  const html = await getDemoHtml(businessId);

  if (!html) {
    return new NextResponse("No page has been built for this business yet.", { status: 404 });
  }

  // The page is generated from scraped content, so never let it run scripts
  // on the dashboard origin.
  return new NextResponse(html, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": "sandbox; default-src 'none'; img-src * data:; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com",
      "X-Content-Type-Options": "nosniff",
      "Cache-Control": "private, no-store",
    },
  });
}
