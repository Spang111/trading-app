import { NextResponse } from "next/server"

import { getBackendApiBaseUrl } from "@/lib/backend-api"

export const dynamic = "force-dynamic"

export async function POST(request: Request) {
  try {
    const authorization = request.headers.get("authorization")
    const body = await request.text()
    const contentType = request.headers.get("content-type") ?? "application/json"
    const { searchParams } = new URL(request.url)
    const paymentId = searchParams.get("payment_id")

    if (!paymentId) {
      return NextResponse.json(
        { detail: "payment_id is required." },
        { status: 400 },
      )
    }

    const response = await fetch(
      `${getBackendApiBaseUrl()}/api/payments/verify?payment_id=${encodeURIComponent(paymentId)}`,
      {
        method: "POST",
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
        detail: "Failed to submit payment verification against backend.",
        error: message,
      },
      { status: 502 },
    )
  }
}
