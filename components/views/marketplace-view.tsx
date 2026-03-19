"use client"

import { useEffect, useState } from "react"
import { BarChart3, QrCode, ShieldCheck, Target, TrendingUp, Wallet, X, Zap } from "lucide-react"

import { Badge } from "@/components/ui/badge"

type Strategy = {
  id: number
  name: string
  description: string | null
  apy: string
  max_drawdown: string
  win_rate: string
  monthly_price: string
  yearly_price: string
  tag: string | null
  status: string
  created_at: string
}

function formatPercent(value: string) {
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)}%` : value
}

function formatMonthlyPrice(value: string) {
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)} USDT / month` : value
}

function getTagLabel(strategy: Strategy) {
  if (strategy.tag && strategy.tag.trim()) {
    return strategy.tag.toUpperCase()
  }

  return strategy.status === "active" ? "LIVE" : "NEW"
}

function getTagColor(strategy: Strategy) {
  return strategy.status === "active" ? "primary" : "accent"
}

export function MarketplaceView() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function loadStrategies() {
      try {
        setIsLoading(true)
        setLoadError(null)

        const response = await fetch("/api/strategies", {
          cache: "no-store",
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`)
        }

        const data = (await response.json()) as Strategy[]
        setStrategies(Array.isArray(data) ? data : [])
      } catch (error) {
        if (controller.signal.aborted) {
          return
        }

        const message =
          error instanceof Error ? error.message : "Unable to load strategy data right now."

        setLoadError(message)
        setStrategies([])
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void loadStrategies()

    return () => controller.abort()
  }, [refreshKey])

  const openPayment = (name: string) => {
    setSelectedStrategy(name)
    setModalOpen(true)
  }

  return (
    <div className="flex flex-col">
      <section className="pt-8 pb-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-4 py-1.5 text-sm font-medium text-accent">
              <BarChart3 className="h-3.5 w-3.5" />
              <span>{isLoading ? "Syncing live strategies..." : `${strategies.length} live strategies`}</span>
            </div>

            <h1 className="text-3xl font-bold text-foreground text-balance sm:text-4xl lg:text-5xl">
              Strategy Marketplace
            </h1>

            <p className="mt-4 max-w-xl text-lg leading-relaxed text-muted-foreground">
              The cards below are now fetched from your Cloud Run backend instead of local mock data.
            </p>

            <p className="mt-3 text-sm text-muted-foreground">
              {isLoading
                ? "Connecting to backend..."
                : loadError
                  ? `Cloud sync failed: ${loadError}`
                  : "Cloud sync is active."}
            </p>
          </div>
        </div>
      </section>

      <section className="pb-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {loadError && (
            <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">
              <p>Failed to load real strategies from the backend.</p>
              <button
                onClick={() => setRefreshKey((current) => current + 1)}
                className="mt-3 rounded-lg border border-red-400/30 px-3 py-1.5 text-xs font-medium text-red-50 transition-colors hover:bg-red-500/10"
              >
                Retry
              </button>
            </div>
          )}

          {!isLoading && !loadError && strategies.length === 0 && (
            <div className="mb-6 rounded-2xl border border-border/50 bg-secondary/20 p-4 text-sm text-muted-foreground">
              The backend responded successfully, but there are no strategies to display yet.
            </div>
          )}

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {strategies.map((strategy) => (
              <div
                key={strategy.id}
                className="group flex flex-col justify-between rounded-2xl p-6 glass-panel transition-all duration-300 hover:scale-[1.02] hover:neon-glow-cyan"
              >
                <div>
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <h3 className="text-lg font-semibold text-foreground">{strategy.name}</h3>
                    <Badge
                      className={
                        getTagColor(strategy) === "primary"
                          ? "border-primary/20 bg-primary/10 text-primary"
                          : "border-accent/20 bg-accent/10 text-accent"
                      }
                    >
                      {getTagLabel(strategy)}
                    </Badge>
                  </div>

                  <p className="mb-6 text-sm leading-relaxed text-muted-foreground">
                    {strategy.description || "No description has been published for this strategy yet."}
                  </p>

                  <div className="mb-6 grid grid-cols-3 gap-4">
                    <div className="flex flex-col items-center rounded-xl bg-secondary/30 p-3">
                      <TrendingUp className="mb-1.5 h-4 w-4 text-emerald-400" />
                      <span className="text-xs text-muted-foreground">APY</span>
                      <span className="text-sm font-bold text-emerald-400">
                        {formatPercent(strategy.apy)}
                      </span>
                    </div>

                    <div className="flex flex-col items-center rounded-xl bg-secondary/30 p-3">
                      <Target className="mb-1.5 h-4 w-4 text-red-400" />
                      <span className="text-xs text-muted-foreground">Drawdown</span>
                      <span className="text-sm font-bold text-red-400">
                        {formatPercent(strategy.max_drawdown)}
                      </span>
                    </div>

                    <div className="flex flex-col items-center rounded-xl bg-secondary/30 p-3">
                      <BarChart3 className="mb-1.5 h-4 w-4 text-primary" />
                      <span className="text-xs text-muted-foreground">Win Rate</span>
                      <span className="text-sm font-bold text-primary">
                        {formatPercent(strategy.win_rate)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <span className="text-sm font-medium text-muted-foreground">
                    {formatMonthlyPrice(strategy.monthly_price)}
                  </span>

                  <button
                    onClick={() => openPayment(strategy.name)}
                    className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-all duration-300 hover:scale-[1.03] hover:shadow-[0_0_20px_rgba(0,229,255,0.3)] active:scale-[0.97]"
                  >
                    <Wallet className="h-4 w-4" />
                    Subscribe
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setModalOpen(false)}
          />

          <div className="relative w-full max-w-md rounded-2xl p-8 glass-panel neon-glow-cyan animate-in fade-in zoom-in-95 duration-200">
            <button
              onClick={() => setModalOpen(false)}
              className="absolute right-4 top-4 rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="Close payment dialog"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="text-center">
              <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 neon-glow-cyan">
                <Wallet className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-xl font-bold text-foreground">Subscribe Strategy</h3>
              <p className="mt-2 text-sm text-muted-foreground">{selectedStrategy}</p>
            </div>

            <div className="mt-6 flex flex-col gap-4">
              <div className="flex flex-col items-center gap-3 rounded-xl border border-border/50 bg-secondary/30 p-6">
                <div className="flex h-40 w-40 items-center justify-center rounded-xl border border-border/50 bg-foreground/5">
                  <QrCode className="h-20 w-20 text-muted-foreground/40" />
                </div>
                <p className="text-xs text-muted-foreground">Scan to pay USDT (TRC20)</p>
              </div>

              <div className="relative flex items-center">
                <div className="flex-1 border-t border-border/50" />
                <span className="px-4 text-xs text-muted-foreground">OR</span>
                <div className="flex-1 border-t border-border/50" />
              </div>

              <button className="flex w-full items-center justify-center gap-2 rounded-xl border border-accent/30 bg-accent/5 px-5 py-3 text-sm font-medium text-accent transition-all duration-300 hover:bg-accent/10 hover:shadow-[0_0_20px_rgba(168,85,247,0.2)]">
                <Zap className="h-4 w-4" />
                Connect Wallet
              </button>

              <div className="mt-2 flex items-center justify-center gap-2">
                <ShieldCheck className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  Payment UI is still demo-only. The list itself is now live.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
