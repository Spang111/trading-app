import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function GET(request: Request) {
  try {
    const authorization = request.headers.get("authorization")

    const response = await fetch(`${getBackendApiBaseUrl()}/api/strategies/admin/list`, {
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
        detail: "Failed to load admin strategies from backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}

export async function POST(request: Request) {
  try {
    const authorization = request.headers.get("authorization")
    const body = await request.text()
    const contentType = request.headers.get("content-type") ?? "application/json"

    const response = await fetch(`${getBackendApiBaseUrl()}/api/strategies`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": contentType,
        ...(authorization ? { Authorization: authorization } : {}),
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
        detail: "Failed to create strategy against backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
