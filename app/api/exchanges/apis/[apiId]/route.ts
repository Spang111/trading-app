import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ apiId: string }> },
) {
  try {
    const { apiId } = await params
    const authorization = request.headers.get("authorization")

    const response = await fetch(`${getBackendApiBaseUrl()}/api/exchanges/apis/${apiId}`, {
      method: "DELETE",
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
        detail: "Failed to delete exchange API against backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
