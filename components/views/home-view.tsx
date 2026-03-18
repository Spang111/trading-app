"use client"

import {
  Shield,
  Clock,
  Zap,
  TrendingUp,
  ArrowRight,
  Bot,
  Lock,
  Twitter,
  Bell,
} from "lucide-react"
import type { ViewKey } from "@/components/navbar"

interface HomeViewProps {
  onViewChange: (view: ViewKey) => void
}

export function HomeView({ onViewChange }: HomeViewProps) {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative min-h-[85vh] flex items-center justify-center overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/5 rounded-full blur-3xl" />
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 rounded-full border border-primary/20 bg-primary/5 text-primary text-sm font-medium">
            <Zap className="h-3.5 w-3.5" />
            <span>全新量化交易引擎已上线</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight text-foreground leading-tight">
            <span className="block">用算法驱动的</span>
            <span className="block mt-2">
              <span className="text-primary neon-text-cyan">自动化</span>
              {" "}加密货币交易
            </span>
          </h1>

          <p className="mt-6 mx-auto max-w-2xl text-lg sm:text-xl text-muted-foreground leading-relaxed">
            {"专业级量化策略，7×24 小时全自动执行。无需盯盘，让算法为您捕捉每一个市场机会。"}
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => onViewChange("marketplace")}
              className="group flex items-center gap-2 px-8 py-3.5 bg-primary text-primary-foreground font-semibold rounded-xl transition-all duration-300 hover:shadow-[0_0_30px_rgba(0,229,255,0.3)] hover:scale-[1.02] active:scale-[0.98]"
            >
              开始使用
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>
            <button
              onClick={() => onViewChange("docs")}
              className="flex items-center gap-2 px-8 py-3.5 border border-border text-foreground font-medium rounded-xl transition-all duration-300 hover:bg-secondary/50 hover:border-primary/30"
            >
              接入文档
            </button>
          </div>

          {/* Stats row */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
            {[
              { value: "$2.4B+", label: "累计交易额" },
              { value: "15,000+", label: "活跃用户" },
              { value: "99.97%", label: "系统在线率" },
              { value: "< 50ms", label: "信号延迟" },
            ].map((stat) => (
              <div key={stat.label} className="flex flex-col items-center">
                <span className="text-2xl sm:text-3xl font-bold text-foreground">{stat.value}</span>
                <span className="mt-1 text-sm text-muted-foreground">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/[0.02] to-transparent" />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
              为什么选择 <span className="text-primary">AI Trading</span>
            </h2>
            <p className="mt-4 text-muted-foreground text-lg max-w-xl mx-auto">
              企业级安全、毫秒级响应、全天候自动执行
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: Shield,
                title: "银行级安全",
                desc: "所有 API 密钥采用 AES-256 加密存储，平台不触碰您的资金。",
                color: "primary" as const,
              },
              {
                icon: Clock,
                title: "7×24 全自动",
                desc: "策略引擎部署在全球边缘节点，永不掉线，永不休眠。",
                color: "primary" as const,
              },
              {
                icon: Bot,
                title: "智能策略引擎",
                desc: "基于机器学习的趋势识别与风控系统，自动优化参数。",
                color: "accent" as const,
              },
              {
                icon: TrendingUp,
                title: "多交易所支持",
                desc: "一键接入 OKX、Binance 等主流交易所，统一管理。",
                color: "primary" as const,
              },
              {
                icon: Zap,
                title: "毫秒级信号",
                desc: "从信号触发到下单执行 < 50ms，抢占市场先机。",
                color: "accent" as const,
              },
              {
                icon: Lock,
                title: "精准风控",
                desc: "内置止盈止损、仓位管理与回撤控制，守护每一笔交易。",
                color: "primary" as const,
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className={`glass-panel rounded-2xl p-6 transition-all duration-300 hover:scale-[1.02] ${
                  feature.color === "primary" ? "hover:neon-glow-cyan" : "hover:neon-glow-purple"
                }`}
              >
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-xl ${
                    feature.color === "primary"
                      ? "bg-primary/10 text-primary"
                      : "bg-accent/10 text-accent"
                  }`}
                >
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">{feature.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Latest Updates / Social Proof Section */}
      <section className="py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
              实时动态
            </h2>
            <p className="mt-4 text-muted-foreground text-lg">
              来自社区与系统的最新消息
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Twitter / Social Proof */}
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-6">
                <Twitter className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold text-foreground">社区动态</h3>
              </div>
              <div className="flex flex-col gap-4">
                {[
                  {
                    user: "@crypto_whale",
                    text: "AI Trading 的 BTC 趋势跟踪策略上个月回报 +18.7%，体验非常丝滑！",
                    time: "2 小时前",
                  },
                  {
                    user: "@defi_hunter",
                    text: "终于找到一个靠谱的量化平台，API 接入只用了 10 分钟。",
                    time: "5 小时前",
                  },
                  {
                    user: "@algo_trader_cn",
                    text: "多空对冲策略在震荡行情中表现惊艳，最大回撤仅 3.2%。",
                    time: "1 天前",
                  },
                ].map((tweet) => (
                  <div
                    key={tweet.user}
                    className="p-4 rounded-xl bg-secondary/30 border border-border/50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-primary">{tweet.user}</span>
                      <span className="text-xs text-muted-foreground">{tweet.time}</span>
                    </div>
                    <p className="text-sm text-foreground/80 leading-relaxed">{tweet.text}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Live Trade Alerts */}
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-6">
                <Bell className="h-5 w-5 text-accent" />
                <h3 className="text-lg font-semibold text-foreground">实时交易信号</h3>
              </div>
              <div className="flex flex-col gap-3">
                {[
                  { action: "BUY", pair: "BTC/USDT", price: "64,280.50", time: "12:03:45", profit: "+2.4%" },
                  { action: "SELL", pair: "ETH/USDT", price: "3,421.80", time: "11:58:12", profit: "+1.8%" },
                  { action: "BUY", pair: "SOL/USDT", price: "142.35", time: "11:45:30", profit: "+5.1%" },
                  { action: "SELL", pair: "BTC/USDT", price: "64,520.00", time: "11:32:08", profit: "+3.2%" },
                  { action: "BUY", pair: "ETH/USDT", price: "3,398.20", time: "11:20:55", profit: "+1.2%" },
                ].map((alert, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3.5 rounded-xl bg-secondary/30 border border-border/50"
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-2 py-0.5 text-xs font-bold rounded ${
                          alert.action === "BUY"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {alert.action}
                      </span>
                      <span className="text-sm font-medium text-foreground">{alert.pair}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground font-mono">${alert.price}</span>
                      <span className="text-xs text-emerald-400 font-medium">{alert.profit}</span>
                      <span className="text-xs text-muted-foreground">{alert.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
