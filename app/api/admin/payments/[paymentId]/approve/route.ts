import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function POST(
  request: Request,
  { params }: { params: Promise<{ paymentId: string }> },
) {
  try {
    const { paymentId } = await params
    const authorization = request.headers.get("authorization")

    const response = await fetch(
      `${getBackendApiBaseUrl()}/api/payments/admin/${paymentId}/approve`,
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          ...(authorization ? { Authorization: authorization } : {}),
        },
        cache: "no-store",
      },
    )

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
        detail: "Failed to approve payment against backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
