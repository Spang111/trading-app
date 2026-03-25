"use client"

import { useEffect, useState } from "react"
import { Activity, LogOut, Menu, UserRound, X } from "lucide-react"

import { AuthDialog } from "@/components/auth-dialog"
import { Button } from "@/components/ui/button"
import { AUTH_TOKEN_STORAGE_KEY, type AuthUser } from "@/lib/auth"

const baseNavItems = [
  { key: "home", label: "首页" },
  { key: "marketplace", label: "策略大厅" },
  { key: "dashboard", label: "我的控制台" },
  { key: "docs", label: "接入指南" },
] as const

export type ViewKey = (typeof baseNavItems)[number]["key"] | "admin"

interface NavbarProps {
  activeView: ViewKey
  onViewChange: (view: ViewKey) => void
}

export function Navbar({ activeView, onViewChange }: NavbarProps) {
  const [authDialogOpen, setAuthDialogOpen] = useState(false)
  const [authMode, setAuthMode] = useState<"login" | "register">("login")
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [isSessionLoading, setIsSessionLoading] = useState(true)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      const token = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)

      if (!token) {
        if (!cancelled) {
          setCurrentUser(null)
          setIsSessionLoading(false)
        }
        return
      }

      try {
        const response = await fetch("/api/auth/me", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          cache: "no-store",
        })

        if (!response.ok) {
          throw new Error("Session expired")
        }

        const user = (await response.json()) as AuthUser

        if (!cancelled) {
          setCurrentUser(user)
        }
      } catch {
        window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)

        if (!cancelled) {
          setCurrentUser(null)
        }
      } finally {
        if (!cancelled) {
          setIsSessionLoading(false)
        }
      }
    }

    void restoreSession()

    return () => {
      cancelled = true
    }
  }, [])

  const visibleNavItems =
    currentUser?.role === "admin"
      ? [...baseNavItems, { key: "admin" as const, label: "策略管理" }]
      : baseNavItems

  function openAuthDialog(mode: "login" | "register") {
    setAuthMode(mode)
    setAuthDialogOpen(true)
    setMobileMenuOpen(false)
  }

  function handleAuthSuccess({ token, user }: { token: string; user: AuthUser }) {
    window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token)
    setCurrentUser(user)
    setIsSessionLoading(false)
  }

  function handleLogout() {
    window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
    setCurrentUser(null)
    setMobileMenuOpen(false)

    if (activeView === "admin") {
      onViewChange("home")
    }
  }

  return (
    <>
      <nav className="fixed left-0 right-0 top-0 z-50 border-b border-border/50 glass-panel">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <button
              onClick={() => onViewChange("home")}
              className="group flex items-center gap-2"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 neon-glow-cyan">
                <Activity className="h-5 w-5 text-primary" />
              </div>
              <span className="text-lg font-bold tracking-tight text-foreground">
                AITra<span className="text-primary neon-text-cyan">ding</span>
              </span>
            </button>

            <div className="hidden items-center gap-4 md:flex">
              <div className="flex items-center gap-1">
                {visibleNavItems.map((item) => (
                  <button
                    key={item.key}
                    onClick={() => onViewChange(item.key)}
                    className={`relative rounded-lg px-4 py-2 text-sm font-medium transition-all duration-300 ${
                      activeView === item.key
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
                    }`}
                  >
                    {item.label}
                    {activeView === item.key && (
                      <span className="absolute bottom-0 left-1/2 h-0.5 w-6 -translate-x-1/2 rounded-full bg-primary" />
                    )}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-2 border-l border-border/50 pl-4">
                {isSessionLoading ? (
                  <span className="text-xs text-muted-foreground">正在检查登录状态...</span>
                ) : currentUser ? (
                  <>
                    <div className="flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-sm text-foreground">
                      <UserRound className="h-4 w-4 text-primary" />
                      <span>{currentUser.username}</span>
                    </div>
                    <Button variant="ghost" size="sm" onClick={handleLogout}>
                      <LogOut className="h-4 w-4" />
                      退出登录
                    </Button>
                  </>
                ) : (
                  <>
                    <Button variant="ghost" size="sm" onClick={() => openAuthDialog("login")}>
                      登录
                    </Button>
                    <Button size="sm" onClick={() => openAuthDialog("register")}>
                      注册
                    </Button>
                  </>
                )}
              </div>
            </div>

            <button
              className="rounded-lg p-2 text-muted-foreground hover:text-foreground md:hidden"
              onClick={() => setMobileMenuOpen((current) => !current)}
              aria-label={mobileMenuOpen ? "关闭菜单" : "打开菜单"}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="animate-in slide-in-from-top-2 fade-in border-t border-border/50 glass-panel duration-200 md:hidden">
            <div className="flex flex-col gap-1 px-4 py-3">
              {visibleNavItems.map((item) => (
                <button
                  key={item.key}
                  onClick={() => {
                    onViewChange(item.key)
                    setMobileMenuOpen(false)
                  }}
                  className={`rounded-lg px-4 py-2.5 text-left text-sm font-medium transition-all duration-200 ${
                    activeView === item.key
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
                  }`}
                >
                  {item.label}
                </button>
              ))}

              <div className="mt-3 border-t border-border/50 pt-3">
                {isSessionLoading ? (
                  <p className="px-4 py-2 text-xs text-muted-foreground">正在检查登录状态...</p>
                ) : currentUser ? (
                  <div className="flex flex-col gap-2 px-4">
                    <div className="flex items-center gap-2 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm text-foreground">
                      <UserRound className="h-4 w-4 text-primary" />
                      <span>{currentUser.username}</span>
                    </div>
                    <Button variant="ghost" onClick={handleLogout}>
                      <LogOut className="h-4 w-4" />
                      退出登录
                    </Button>
                  </div>
                ) : (
                  <div className="grid gap-2 px-4">
                    <Button variant="ghost" onClick={() => openAuthDialog("login")}>
                      登录
                    </Button>
                    <Button onClick={() => openAuthDialog("register")}>注册</Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </nav>

      <AuthDialog
        open={authDialogOpen}
        mode={authMode}
        onOpenChange={setAuthDialogOpen}
        onModeChange={setAuthMode}
        onAuthSuccess={handleAuthSuccess}
      />
    </>
  )
}
