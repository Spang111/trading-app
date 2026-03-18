"use client"

import { useState } from "react"
import { TrendingUp, BarChart3, Target, Wallet, QrCode, X, Zap, ShieldCheck } from "lucide-react"
import { Badge } from "@/components/ui/badge"

const strategies = [
  {
    name: "BTC 趋势跟踪",
    desc: "基于多时间框架趋势识别，自动捕捉 BTC 中长期行情。",
    apy: "127.4%",
    drawdown: "8.2%",
    winRate: "68.5%",
    price: "299 USDT/月",
    tag: "热门",
    tagColor: "primary",
  },
  {
    name: "ETH 网格交易",
    desc: "在震荡区间内自动高抛低吸，稳定收益来源。",
    apy: "85.6%",
    drawdown: "4.1%",
    winRate: "82.3%",
    price: "199 USDT/月",
    tag: "稳健",
    tagColor: "accent",
  },
  {
    name: "多空对冲 Alpha",
    desc: "同时做多强势币、做空弱势币，获取市场中性收益。",
    apy: "64.2%",
    drawdown: "3.2%",
    winRate: "71.8%",
    price: "399 USDT/月",
    tag: "专业",
    tagColor: "accent",
  },
  {
    name: "SOL 动量突破",
    desc: "捕捉 SOL 短期动量突破信号，快进快出。",
    apy: "156.8%",
    drawdown: "12.5%",
    winRate: "62.1%",
    price: "249 USDT/月",
    tag: "高收益",
    tagColor: "primary",
  },
  {
    name: "BTC/ETH 套利",
    desc: "跨交易所价差套利，低风险稳定盈利。",
    apy: "42.3%",
    drawdown: "1.8%",
    winRate: "91.2%",
    price: "349 USDT/月",
    tag: "低风险",
    tagColor: "primary",
  },
  {
    name: "AI 智能混合",
    desc: "基于深度学习模型，动态调整多策略权重组合。",
    apy: "198.5%",
    drawdown: "15.3%",
    winRate: "65.7%",
    price: "599 USDT/月",
    tag: "AI",
    tagColor: "accent",
  },
]

export function MarketplaceView() {
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null)

  const openPayment = (name: string) => {
    setSelectedStrategy(name)
    setModalOpen(true)
  }

  return (
    <div className="flex flex-col">
      {/* Header */}
      <section className="pt-8 pb-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 rounded-full border border-accent/20 bg-accent/5 text-accent text-sm font-medium">
              <BarChart3 className="h-3.5 w-3.5" />
              <span>{"已上线 " + strategies.length + " 款策略"}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground text-balance">
              策略大厅
            </h1>
            <p className="mt-4 max-w-xl text-muted-foreground text-lg leading-relaxed">
              精选量化策略，经过严格回测与实盘验证，一键订阅即可启用。
            </p>
          </div>
        </div>
      </section>

      {/* Strategy Grid */}
      <section className="pb-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {strategies.map((s) => (
              <div
                key={s.name}
                className="glass-panel rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 hover:scale-[1.02] hover:neon-glow-cyan group"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-foreground">{s.name}</h3>
                    <Badge
                      className={
                        s.tagColor === "primary"
                          ? "bg-primary/10 text-primary border-primary/20"
                          : "bg-accent/10 text-accent border-accent/20"
                      }
                    >
                      {s.tag}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed mb-6">{s.desc}</p>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="flex flex-col items-center p-3 rounded-xl bg-secondary/30">
                      <TrendingUp className="h-4 w-4 text-emerald-400 mb-1.5" />
                      <span className="text-xs text-muted-foreground">年化收益</span>
                      <span className="text-sm font-bold text-emerald-400">{s.apy}</span>
                    </div>
                    <div className="flex flex-col items-center p-3 rounded-xl bg-secondary/30">
                      <Target className="h-4 w-4 text-red-400 mb-1.5" />
                      <span className="text-xs text-muted-foreground">最大回撤</span>
                      <span className="text-sm font-bold text-red-400">{s.drawdown}</span>
                    </div>
                    <div className="flex flex-col items-center p-3 rounded-xl bg-secondary/30">
                      <BarChart3 className="h-4 w-4 text-primary mb-1.5" />
                      <span className="text-xs text-muted-foreground">胜率</span>
                      <span className="text-sm font-bold text-primary">{s.winRate}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">{s.price}</span>
                  <button
                    onClick={() => openPayment(s.name)}
                    className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground text-sm font-semibold rounded-xl transition-all duration-300 hover:shadow-[0_0_20px_rgba(0,229,255,0.3)] hover:scale-[1.03] active:scale-[0.97]"
                  >
                    <Wallet className="h-4 w-4" />
                    使用 USDT 订阅
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Payment Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setModalOpen(false)}
          />
          <div className="relative glass-panel rounded-2xl p-8 max-w-md w-full neon-glow-cyan animate-in fade-in zoom-in-95 duration-200">
            <button
              onClick={() => setModalOpen(false)}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
              aria-label="关闭"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="text-center">
              <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/10 neon-glow-cyan mb-4">
                <Wallet className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-xl font-bold text-foreground">订阅策略</h3>
              <p className="mt-2 text-sm text-muted-foreground">{selectedStrategy}</p>
            </div>

            <div className="mt-6 flex flex-col gap-4">
              {/* QR Code area */}
              <div className="flex flex-col items-center gap-3 p-6 rounded-xl bg-secondary/30 border border-border/50">
                <div className="h-40 w-40 rounded-xl bg-foreground/5 border border-border/50 flex items-center justify-center">
                  <QrCode className="h-20 w-20 text-muted-foreground/40" />
                </div>
                <p className="text-xs text-muted-foreground">扫描二维码发送 USDT (TRC-20)</p>
              </div>

              <div className="relative flex items-center">
                <div className="flex-1 border-t border-border/50" />
                <span className="px-4 text-xs text-muted-foreground">或</span>
                <div className="flex-1 border-t border-border/50" />
              </div>

              {/* Connect Wallet */}
              <button className="flex items-center justify-center gap-2 w-full px-5 py-3 rounded-xl border border-accent/30 bg-accent/5 text-accent font-medium text-sm transition-all duration-300 hover:bg-accent/10 hover:shadow-[0_0_20px_rgba(168,85,247,0.2)]">
                <Zap className="h-4 w-4" />
                连接钱包支付
              </button>

              <div className="flex items-center justify-center gap-2 mt-2">
                <ShieldCheck className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">安全加密交易，资金即时到账</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
