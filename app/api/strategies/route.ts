import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function GET() {
  try {
    const response = await fetch(`${getBackendApiBaseUrl()}/api/strategies`, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    })

    const body = await response.text()

    return new NextResponse(body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error"

    return NextResponse.json(
      {
        detail: "Failed to load strategies from backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
