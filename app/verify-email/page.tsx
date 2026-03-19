"use client"

import { CheckCircle2, Loader2, MailWarning, RefreshCcw } from "lucide-react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"

type VerifyState = "loading" | "success" | "error"

type VerifyResponse = {
  message?: string
  detail?: string
}

function translateMessage(message: string) {
  const dictionary: Record<string, string> = {
    "Your email address has been verified. You can return to the app and log in.":
      "邮箱验证成功，现在可以返回首页登录了。",
    "Your email address has already been verified. You can log in now.":
      "这个邮箱已经验证过了，现在可以直接登录。",
    "Invalid or expired email verification link.": "验证链接无效或已过期，请重新发送验证邮件。",
    "This email verification link is no longer valid.": "这个验证链接已经失效，请重新发送验证邮件。",
  }

  return dictionary[message] ?? message
}

export default function VerifyEmailPage() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")
  const [state, setState] = useState<VerifyState>("loading")
  const [message, setMessage] = useState("正在验证邮箱，请稍候...")

  useEffect(() => {
    if (!token) {
      setState("error")
      setMessage("没有找到验证参数，请确认你打开的是完整的验证链接。")
      return
    }

    let cancelled = false

    async function verifyEmail() {
      try {
        const response = await fetch("/api/auth/verify-email", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token }),
        })

        const payload = (await response.json()) as VerifyResponse
        const nextMessage = translateMessage(
          payload.message || payload.detail || "邮箱验证完成。",
        )

        if (cancelled) {
          return
        }

        if (!response.ok) {
          setState("error")
          setMessage(nextMessage)
          return
        }

        setState("success")
        setMessage(nextMessage)
      } catch {
        if (!cancelled) {
          setState("error")
          setMessage("暂时无法连接验证服务，请稍后重试。")
        }
      }
    }

    void verifyEmail()

    return () => {
      cancelled = true
    }
  }, [token])

  const icon =
    state === "loading" ? (
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    ) : state === "success" ? (
      <CheckCircle2 className="h-8 w-8 text-emerald-400" />
    ) : (
      <MailWarning className="h-8 w-8 text-destructive" />
    )

  const title =
    state === "loading"
      ? "正在验证邮箱"
      : state === "success"
        ? "邮箱验证成功"
        : "邮箱验证失败"

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-16">
      <section className="w-full max-w-lg rounded-3xl border border-border/60 bg-card/90 p-8 text-center shadow-2xl">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          {icon}
        </div>
        <h1 className="text-3xl font-semibold text-foreground">{title}</h1>
        <p className="mt-4 text-sm leading-7 text-muted-foreground">{message}</p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Button asChild>
            <Link href="/">返回首页</Link>
          </Button>
          {state === "error" && (
            <Button variant="outline" onClick={() => window.location.reload()}>
              <RefreshCcw className="mr-2 h-4 w-4" />
              重新尝试
            </Button>
          )}
        </div>
      </section>
    </main>
  )
}
