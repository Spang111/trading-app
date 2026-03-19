"use client"

import { type FormEvent, useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { type AuthUser } from "@/lib/auth"

type AuthMode = "login" | "register"

type AuthDialogProps = {
  open: boolean
  mode: AuthMode
  onOpenChange: (open: boolean) => void
  onModeChange: (mode: AuthMode) => void
  onAuthSuccess: (payload: { token: string; user: AuthUser }) => void
}

type LoginResponse = {
  access_token: string
  token_type: string
}

type RegistrationResponse = {
  message: string
  email: string
  requires_email_verification: boolean
}

type MessageResponse = {
  message?: string
  detail?: string
}

const INITIAL_REGISTER_FORM = {
  username: "",
  email: "",
  password: "",
  wallet_address: "",
}

const INITIAL_LOGIN_FORM = {
  username: "",
  password: "",
}

const INITIAL_FORGOT_PASSWORD_FORM = {
  email: "",
}

function translateBackendMessage(message: string) {
  const dictionary: Record<string, string> = {
    "Incorrect username/email or password.": "用户名、邮箱或密码错误。",
    "Email address has not been verified.": "邮箱尚未验证，请先前往邮箱完成验证。",
    "Username is already in use.": "这个用户名已经被使用了。",
    "Email is already registered.": "这个邮箱已经注册过了。",
    "Registration successful. Please verify your email before logging in.":
      "注册成功，请先前往邮箱点击验证链接，再回来登录。",
    "Registration successful. You can log in now.": "注册成功，现在可以直接登录。",
    "If that email address exists, a verification message will arrive shortly.":
      "如果该邮箱存在，新的验证邮件很快就会发送过去。",
    "Invalid or expired email verification link.": "验证链接无效或已过期，请重新发送验证邮件。",
    "Your email address has been verified. You can return to the app and log in.":
      "邮箱验证成功，现在可以返回页面登录了。",
    "Your email address has already been verified. You can log in now.":
      "这个邮箱已经验证过了，现在可以直接登录。",
    "Email verification is currently disabled for this environment.":
      "当前环境未开启邮箱验证。",
    "If that email address exists, a password reset link will arrive shortly.":
      "如果该邮箱存在，重置密码邮件很快就会发送过去。",
    "Password reset successful. You can log in now.": "密码重置成功，现在可以直接登录。",
    "Invalid or expired password reset link.": "重置密码链接无效或已过期。",
    "This password reset link has already been used or is no longer valid.":
      "这个重置密码链接已经使用过，或已失效。",
  }

  return dictionary[message] ?? message
}

async function readResponseMessage(response: Response) {
  try {
    const data = (await response.json()) as MessageResponse
    return translateBackendMessage(
      data.detail || data.message || `Request failed with status ${response.status}`,
    )
  } catch {
    return `Request failed with status ${response.status}`
  }
}

export function AuthDialog({
  open,
  mode,
  onOpenChange,
  onModeChange,
  onAuthSuccess,
}: AuthDialogProps) {
  const [loginForm, setLoginForm] = useState(INITIAL_LOGIN_FORM)
  const [registerForm, setRegisterForm] = useState(INITIAL_REGISTER_FORM)
  const [forgotPasswordForm, setForgotPasswordForm] = useState(INITIAL_FORGOT_PASSWORD_FORM)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)
  const [verificationEmail, setVerificationEmail] = useState<string | null>(null)
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false)

  useEffect(() => {
    if (!open) {
      setFormError(null)
      setFormSuccess(null)
      setIsSubmitting(false)
      setVerificationEmail(null)
      setForgotPasswordOpen(false)
      setLoginForm(INITIAL_LOGIN_FORM)
      setRegisterForm(INITIAL_REGISTER_FORM)
      setForgotPasswordForm(INITIAL_FORGOT_PASSWORD_FORM)
    }
  }, [open])

  useEffect(() => {
    if (forgotPasswordOpen) {
      setFormError(null)
      setFormSuccess(null)
    }
  }, [forgotPasswordOpen])

  const title = forgotPasswordOpen
    ? "找回密码"
    : mode === "login"
      ? "登录 AI Trading"
      : "注册 AI Trading 账号"

  const description = forgotPasswordOpen
    ? "输入注册邮箱，我们会把重置密码链接发送到你的邮箱。"
    : mode === "login"
      ? "登录后可以查看订阅、策略和个人控制台。"
      : "注册后请根据系统提示完成账号验证，再开始使用。"

  async function fetchCurrentUser(token: string) {
    const response = await fetch("/api/auth/me", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    })

    if (!response.ok) {
      throw new Error(await readResponseMessage(response))
    }

    return (await response.json()) as AuthUser
  }

  async function handleLoginSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)
    setFormSuccess(null)
    setIsSubmitting(true)

    try {
      const body = new URLSearchParams({
        username: loginForm.username,
        password: loginForm.password,
      })

      const loginResponse = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
      })

      if (!loginResponse.ok) {
        throw new Error(await readResponseMessage(loginResponse))
      }

      const loginPayload = (await loginResponse.json()) as LoginResponse
      const user = await fetchCurrentUser(loginPayload.access_token)

      onAuthSuccess({ token: loginPayload.access_token, user })
      setFormSuccess("登录成功。")
      onOpenChange(false)
    } catch (error) {
      const message = error instanceof Error ? error.message : "暂时无法登录，请稍后再试。"
      setFormError(message)

      if (message.includes("邮箱尚未验证") && loginForm.username.includes("@")) {
        setVerificationEmail(loginForm.username)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleRegisterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)
    setFormSuccess(null)
    setIsSubmitting(true)

    try {
      const registerResponse = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password,
          wallet_address: registerForm.wallet_address || null,
        }),
      })

      if (!registerResponse.ok) {
        throw new Error(await readResponseMessage(registerResponse))
      }

      const registerPayload = (await registerResponse.json()) as RegistrationResponse
      const successMessage = translateBackendMessage(registerPayload.message)

      if (registerPayload.requires_email_verification) {
        setVerificationEmail(registerPayload.email)
        setLoginForm({
          username: registerPayload.email,
          password: "",
        })
        setRegisterForm(INITIAL_REGISTER_FORM)
        setFormSuccess(successMessage)
        onModeChange("login")
        return
      }

      const body = new URLSearchParams({
        username: registerForm.username,
        password: registerForm.password,
      })

      const loginResponse = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
      })

      if (!loginResponse.ok) {
        throw new Error(await readResponseMessage(loginResponse))
      }

      const loginPayload = (await loginResponse.json()) as LoginResponse
      const user = await fetchCurrentUser(loginPayload.access_token)

      onAuthSuccess({ token: loginPayload.access_token, user })
      setFormSuccess("注册成功，已自动登录。")
      onOpenChange(false)
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "暂时无法注册，请稍后再试。")
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleResendVerification() {
    if (!verificationEmail) {
      setFormError("请先输入注册邮箱。")
      return
    }

    setFormError(null)
    setFormSuccess(null)
    setIsSubmitting(true)

    try {
      const response = await fetch("/api/auth/resend-verification", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: verificationEmail }),
      })

      if (!response.ok) {
        throw new Error(await readResponseMessage(response))
      }

      const payload = (await response.json()) as MessageResponse
      setFormSuccess(
        translateBackendMessage(
          payload.message || "如果该邮箱存在，新的验证邮件很快就会发送过去。",
        ),
      )
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "暂时无法发送验证邮件，请稍后再试。",
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleForgotPasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)
    setFormSuccess(null)
    setIsSubmitting(true)

    try {
      const response = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: forgotPasswordForm.email }),
      })

      if (!response.ok) {
        throw new Error(await readResponseMessage(response))
      }

      const payload = (await response.json()) as MessageResponse
      setFormSuccess(
        translateBackendMessage(
          payload.message || "如果该邮箱存在，重置密码邮件很快就会发送过去。",
        ),
      )
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "暂时无法发送重置密码邮件，请稍后再试。",
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  function openForgotPassword() {
    setForgotPasswordOpen(true)
    setFormError(null)
    setFormSuccess(null)
    setForgotPasswordForm({
      email: loginForm.username.includes("@") ? loginForm.username : "",
    })
  }

  function backToLogin() {
    setForgotPasswordOpen(false)
    setFormError(null)
    setFormSuccess(null)
    onModeChange("login")
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[calc(100vw-2rem)] max-w-md rounded-2xl border-border/60 bg-background/95 p-5 shadow-2xl sm:min-h-[33rem]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        {forgotPasswordOpen ? (
          <div className="flex min-h-[25rem] flex-col pt-2">
            <form className="flex flex-1 flex-col gap-4" onSubmit={handleForgotPasswordSubmit}>
              <div className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="forgot-password-email">邮箱</Label>
                  <Input
                    id="forgot-password-email"
                    type="email"
                    placeholder="请输入注册邮箱"
                    value={forgotPasswordForm.email}
                    onChange={(event) =>
                      setForgotPasswordForm({ email: event.target.value })
                    }
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <div className="mt-auto space-y-4">
                {formError && <p className="text-sm text-destructive">{formError}</p>}
                {formSuccess && <p className="text-sm text-emerald-400">{formSuccess}</p>}

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={backToLogin}
                    disabled={isSubmitting}
                  >
                    返回登录
                  </Button>
                  <Button type="submit" className="flex-1" disabled={isSubmitting}>
                    {isSubmitting ? "发送中..." : "发送重置邮件"}
                  </Button>
                </div>
              </div>
            </form>
          </div>
        ) : (
          <Tabs
            value={mode}
            onValueChange={(value) => onModeChange(value as AuthMode)}
            className="flex min-h-[25rem] flex-col"
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">登录</TabsTrigger>
              <TabsTrigger value="register">注册</TabsTrigger>
            </TabsList>

            <TabsContent value="login" className="mt-0 flex flex-1 flex-col pt-4">
              <form className="flex flex-1 flex-col gap-4" onSubmit={handleLoginSubmit}>
                <div className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="login-username">用户名或邮箱</Label>
                    <Input
                      id="login-username"
                      placeholder="请输入用户名或邮箱"
                      value={loginForm.username}
                      onChange={(event) =>
                        setLoginForm((current) => ({ ...current, username: event.target.value }))
                      }
                      autoComplete="username"
                      required
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="login-password">密码</Label>
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="请输入登录密码"
                      value={loginForm.password}
                      onChange={(event) =>
                        setLoginForm((current) => ({ ...current, password: event.target.value }))
                      }
                      autoComplete="current-password"
                      required
                    />
                  </div>

                  <button
                    type="button"
                    className="text-left text-sm text-primary transition-colors hover:text-primary/80"
                    onClick={openForgotPassword}
                  >
                    忘记密码？
                  </button>
                </div>

                <div className="mt-auto space-y-4">
                  {formError && <p className="text-sm text-destructive">{formError}</p>}
                  {formSuccess && <p className="text-sm text-emerald-400">{formSuccess}</p>}

                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "登录中..." : "立即登录"}
                  </Button>
                </div>
              </form>

              {verificationEmail && (
                <div className="mt-4 rounded-xl border border-primary/20 bg-primary/5 p-3">
                  <p className="text-sm text-muted-foreground">
                    没有收到验证邮件？我们可以重新发送到
                    <span className="ml-1 font-medium text-foreground">{verificationEmail}</span>
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    disabled={isSubmitting}
                    onClick={handleResendVerification}
                  >
                    重新发送验证邮件
                  </Button>
                </div>
              )}
            </TabsContent>

            <TabsContent value="register" className="mt-0 flex flex-1 flex-col pt-4">
              <form className="flex flex-1 flex-col gap-4" onSubmit={handleRegisterSubmit}>
                <div className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="register-username">用户名</Label>
                    <Input
                      id="register-username"
                      placeholder="请设置用户名"
                      value={registerForm.username}
                      onChange={(event) =>
                        setRegisterForm((current) => ({ ...current, username: event.target.value }))
                      }
                      autoComplete="username"
                      required
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="register-email">邮箱</Label>
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="请输入常用邮箱"
                      value={registerForm.email}
                      onChange={(event) =>
                        setRegisterForm((current) => ({ ...current, email: event.target.value }))
                      }
                      autoComplete="email"
                      required
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="register-password">密码</Label>
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="至少 6 位密码"
                      value={registerForm.password}
                      onChange={(event) =>
                        setRegisterForm((current) => ({ ...current, password: event.target.value }))
                      }
                      autoComplete="new-password"
                      required
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="register-wallet">钱包地址</Label>
                    <Input
                      id="register-wallet"
                      placeholder="可选，不填也可以"
                      value={registerForm.wallet_address}
                      onChange={(event) =>
                        setRegisterForm((current) => ({
                          ...current,
                          wallet_address: event.target.value,
                        }))
                      }
                    />
                  </div>
                </div>

                <div className="mt-auto space-y-4">
                  {formError && <p className="text-sm text-destructive">{formError}</p>}
                  {formSuccess && <p className="text-sm text-emerald-400">{formSuccess}</p>}

                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "注册中..." : "创建账号"}
                  </Button>
                </div>
              </form>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  )
}
