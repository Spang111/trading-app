import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function POST(request: Request) {
  try {
    const body = await request.text()
    const contentType =
      request.headers.get("content-type") ?? "application/x-www-form-urlencoded"

    const response = await fetch(`${getBackendApiBaseUrl()}/api/auth/login`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": contentType,
      },
      body,
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
        detail: "Failed to log in against backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
