import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function GET(request: Request) {
  try {
    const authorization = request.headers.get("authorization")
    const url = new URL(request.url)
    const query = url.searchParams.toString()
    const backendUrl = `${getBackendApiBaseUrl()}/api/signals${query ? `?${query}` : ""}`

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(authorization ? { Authorization: authorization } : {}),
      },
      cache: "no-store",
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
        detail: "Failed to load signal logs from backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
