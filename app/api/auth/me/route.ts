import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function GET(request: Request) {
  try {
    const authorization = request.headers.get("authorization")

    const response = await fetch(`${getBackendApiBaseUrl()}/api/auth/me`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(authorization ? { Authorization: authorization } : {}),
      },
      cache: "no-store",
    })

    const responseBody = await response.text()

    return new NextResponse(responseBody, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error"

    return NextResponse.json(
      {
        detail: "Failed to fetch current user from backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
