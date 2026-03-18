"use client"

import { useState } from "react"
import { Navbar, type ViewKey } from "@/components/navbar"
import { HomeView } from "@/components/views/home-view"
import { MarketplaceView } from "@/components/views/marketplace-view"
import { DashboardView } from "@/components/views/dashboard-view"
import { DocsView } from "@/components/views/docs-view"

export default function Page() {
  const [activeView, setActiveView] = useState<ViewKey>("home")

  return (
    <div className="min-h-screen bg-background">
      <Navbar activeView={activeView} onViewChange={setActiveView} />
      <main className="pt-16">
        <div
          key={activeView}
          className="animate-in fade-in duration-300"
        >
          {activeView === "home" && <HomeView onViewChange={setActiveView} />}
          {activeView === "marketplace" && <MarketplaceView />}
          {activeView === "dashboard" && <DashboardView />}
          {activeView === "docs" && <DocsView />}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-muted-foreground">
              {"© 2026 AI Trading. All rights reserved."}
            </p>
            <div className="flex items-center gap-6">
              <button
                onClick={() => setActiveView("docs")}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                文档
              </button>
              <span className="text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                隐私政策
              </span>
              <span className="text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                服务条款
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
