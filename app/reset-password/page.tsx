"use client"

import { Suspense, useState, type FormEvent } from "react"

import { CheckCircle2, Loader2, MailWarning, RefreshCcw } from "lucide-react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

type SubmitState = "idle" | "submitting" | "success" | "error"

type MessageResponse = {
  message?: string
  detail?: string
}

function translateMessage(message: string) {
  const dictionary: Record<string, string> = {
    "Password reset successful. You can log in now.": "密码重置成功，现在可以直接登录了。",
    "Invalid or expired password reset link.": "重置密码链接无效或已过期。",
    "This password reset link has already been used or is no longer valid.":
      "这个重置密码链接已经使用过，或已失效。",
  }

  return dictionary[message] ?? message
}

function ResetPasswordContent() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [state, setState] = useState<SubmitState>("idle")
  const [message, setMessage] = useState("请输入你的新密码。")

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!token) {
      setState("error")
      setMessage("没有找到重置密码参数，请确认你打开的是完整的邮件链接。")
      return
    }

    if (password !== confirmPassword) {
      setState("error")
      setMessage("两次输入的密码不一致，请重新确认。")
      return
    }

    setState("submitting")
    setMessage("正在保存新密码，请稍候...")

    try {
      const response = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token,
          new_password: password,
        }),
      })

      const payload = (await response.json()) as MessageResponse
      const nextMessage = translateMessage(
        payload.message || payload.detail || "密码重置完成。",
      )

      if (!response.ok) {
        setState("error")
        setMessage(nextMessage)
        return
      }

      setState("success")
      setMessage(nextMessage)
    } catch {
      setState("error")
      setMessage("暂时无法连接重置密码服务，请稍后再试。")
    }
  }

  const icon =
    state === "submitting" ? (
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    ) : state === "success" ? (
      <CheckCircle2 className="h-8 w-8 text-emerald-400" />
    ) : (
      <MailWarning className="h-8 w-8 text-primary" />
    )

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-16">
      <section className="w-full max-w-lg rounded-3xl border border-border/60 bg-card/90 p-8 shadow-2xl">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          {icon}
        </div>
        <h1 className="text-center text-3xl font-semibold text-foreground">重置密码</h1>
        <p className="mt-4 text-center text-sm leading-7 text-muted-foreground">{message}</p>

        {state !== "success" && (
          <form className="mt-8 grid gap-4" onSubmit={handleSubmit}>
            <div className="grid gap-2">
              <Label htmlFor="new-password">新密码</Label>
              <Input
                id="new-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="至少 6 位密码"
                minLength={6}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="confirm-password">确认新密码</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="再次输入新密码"
                minLength={6}
                required
              />
            </div>

            <Button type="submit" disabled={state === "submitting"}>
              {state === "submitting" ? "提交中..." : "保存新密码"}
            </Button>
          </form>
        )}

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Button asChild variant={state === "success" ? "default" : "outline"}>
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

function ResetPasswordFallback() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-16">
      <section className="w-full max-w-lg rounded-3xl border border-border/60 bg-card/90 p-8 text-center shadow-2xl">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
        <h1 className="text-3xl font-semibold text-foreground">正在加载重置页面</h1>
        <p className="mt-4 text-sm leading-7 text-muted-foreground">请稍候...</p>
      </section>
    </main>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<ResetPasswordFallback />}>
      <ResetPasswordContent />
    </Suspense>
  )
}
