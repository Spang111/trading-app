"use client"

import { Activity, Menu, X } from "lucide-react"
import { useState } from "react"

const navItems = [
  { key: "home", label: "首页" },
  { key: "marketplace", label: "策略大厅" },
  { key: "dashboard", label: "我的控制台" },
  { key: "docs", label: "接入指南" },
] as const

export type ViewKey = (typeof navItems)[number]["key"]

interface NavbarProps {
  activeView: ViewKey
  onViewChange: (view: ViewKey) => void
}

export function Navbar({ activeView, onViewChange }: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-panel border-b border-border/50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <button
            onClick={() => onViewChange("home")}
            className="flex items-center gap-2 group"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 neon-glow-cyan">
              <Activity className="h-5 w-5 text-primary" />
            </div>
            <span className="text-lg font-bold text-foreground tracking-tight">
              AITra<span className="text-primary neon-text-cyan">ding</span>
            </span>
          </button>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.key}
                onClick={() => onViewChange(item.key)}
                className={`relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 ${
                  activeView === item.key
                    ? "text-primary bg-primary/10"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                }`}
              >
                {item.label}
                {activeView === item.key && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 w-6 bg-primary rounded-full" />
                )}
              </button>
            ))}
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 text-muted-foreground hover:text-foreground rounded-lg"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? "关闭菜单" : "打开菜单"}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-panel border-t border-border/50 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="px-4 py-3 flex flex-col gap-1">
            {navItems.map((item) => (
              <button
                key={item.key}
                onClick={() => {
                  onViewChange(item.key)
                  setMobileMenuOpen(false)
                }}
                className={`px-4 py-2.5 text-sm font-medium rounded-lg text-left transition-all duration-200 ${
                  activeView === item.key
                    ? "text-primary bg-primary/10"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </nav>
  )
}
