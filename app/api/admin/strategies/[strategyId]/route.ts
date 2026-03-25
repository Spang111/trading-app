import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ strategyId: string }> },
) {
  try {
    const { strategyId } = await params
    const authorization = request.headers.get("authorization")
    const body = await request.text()
    const contentType = request.headers.get("content-type") ?? "application/json"

    const response = await fetch(
      `${getBackendApiBaseUrl()}/api/strategies/${strategyId}`,
      {
        method: "PUT",
        headers: {
          Accept: "application/json",
          "Content-Type": contentType,
          ...(authorization ? { Authorization: authorization } : {}),
        },
        body,
        cache: "no-store",
      },
    )

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
        detail: "Failed to update strategy against backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
