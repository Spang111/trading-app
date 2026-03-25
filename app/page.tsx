"use client"

import Link from "next/link"
import { useState } from "react"

import { Navbar, type ViewKey } from "@/components/navbar"
import { AdminStrategiesView } from "@/components/views/admin-strategies-view"
import { DashboardView } from "@/components/views/dashboard-view"
import { DocsView } from "@/components/views/docs-view"
import { HomeView } from "@/components/views/home-view"
import { MarketplaceView } from "@/components/views/marketplace-view"

export default function Page() {
  const [activeView, setActiveView] = useState<ViewKey>("home")

  return (
    <div className="min-h-screen bg-background">
      <Navbar activeView={activeView} onViewChange={setActiveView} />

      <main className="pt-16">
        <div key={activeView} className="animate-in fade-in duration-300">
          {activeView === "home" && <HomeView onViewChange={setActiveView} />}
          {activeView === "marketplace" && <MarketplaceView />}
          {activeView === "dashboard" && <DashboardView />}
          {activeView === "docs" && <DocsView />}
          {activeView === "admin" && <AdminStrategiesView />}
        </div>
      </main>

      <footer className="border-t border-border/50 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-muted-foreground">(c) 2026 AI Trading. All rights reserved.</p>

            <div className="flex items-center gap-6">
              <button
                onClick={() => setActiveView("docs")}
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                文档
              </button>
              <Link href="/privacy-policy" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                隐私政策
              </Link>
              <Link href="/terms-of-service" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                服务条款
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
