"use client"

import { ArrowRight, Bot, Clock, Lock, Shield, TrendingUp, Zap } from "lucide-react"

import type { ViewKey } from "@/components/navbar"

interface HomeViewProps {
  onViewChange: (view: ViewKey) => void
}

const features = [
  {
    icon: Shield,
    title: "银行级安全",
    desc: "所有 API 密钥采用 AES-256 加密存储，平台不接触您的资金。",
    color: "primary" as const,
  },
  {
    icon: Clock,
    title: "7x24 全自动",
    desc: "策略引擎部署在全球边缘节点，持续运行，不错过市场机会。",
    color: "primary" as const,
  },
  {
    icon: Bot,
    title: "智能策略引擎",
    desc: "基于趋势识别与风控系统自动优化参数，减少人为情绪干扰。",
    color: "accent" as const,
  },
  {
    icon: TrendingUp,
    title: "多交易所支持",
    desc: "一键接入 OKX、Binance 等主流交易所，统一管理策略执行。",
    color: "primary" as const,
  },
  {
    icon: Zap,
    title: "毫秒级信号",
    desc: "从信号触发到下单执行保持低延迟，帮助你更快响应行情。",
    color: "accent" as const,
  },
  {
    icon: Lock,
    title: "精细风控",
    desc: "内置止盈止损、仓位管理与回撤控制，保护每一笔交易。",
    color: "primary" as const,
  },
]

export function HomeView({ onViewChange }: HomeViewProps) {
  return (
    <div className="flex flex-col">
      <section className="relative flex min-h-[58vh] items-center justify-center overflow-hidden pb-10 pt-16 sm:min-h-[62vh] lg:min-h-[66vh] lg:pt-20">
        <div className="absolute inset-0">
          <div className="absolute left-[-6%] top-[18%] h-[28rem] w-[40rem] rounded-full bg-[radial-gradient(circle_at_center,rgba(0,229,255,0.16),rgba(0,229,255,0.08)_38%,rgba(0,229,255,0)_72%)] blur-3xl" />
          <div className="absolute right-[-10%] top-[10%] h-[24rem] w-[34rem] rounded-full bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.12),rgba(139,92,246,0.06)_34%,rgba(139,92,246,0)_70%)] blur-3xl" />
          <div className="absolute inset-x-[18%] top-[32%] h-40 bg-[radial-gradient(circle_at_center,rgba(0,229,255,0.06),rgba(0,229,255,0)_72%)] blur-2xl" />
          <div className="absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
        </div>

        <div className="relative mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
            <Zap className="h-3.5 w-3.5" />
            <span>全新量化交易引擎已上线</span>
          </div>

          <h1 className="text-4xl font-bold leading-tight tracking-tight text-foreground sm:text-5xl lg:text-7xl">
            <span className="block">用算法驱动的</span>
            <span className="mt-2 block">
              <span className="text-primary neon-text-cyan">自动化</span> 加密货币交易
            </span>
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
            专业级量化策略，7x24 小时全自动执行。无需盯盘，让算法为您捕捉每一个市场机会。
          </p>

          <div className="mt-10 flex translate-y-6 flex-col items-center justify-center gap-4 sm:mt-12 sm:translate-y-7 sm:flex-row">
            <button
              onClick={() => onViewChange("marketplace")}
              className="group flex items-center gap-2 rounded-xl bg-primary px-8 py-3.5 font-semibold text-primary-foreground transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(0,229,255,0.3)] active:scale-[0.98]"
            >
              开始使用
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>
            <button
              onClick={() => onViewChange("docs")}
              className="flex items-center gap-2 rounded-xl border border-border px-8 py-3.5 font-medium text-foreground transition-all duration-300 hover:border-primary/30 hover:bg-secondary/50"
            >
              接入文档
            </button>
          </div>
        </div>
      </section>

      <section className="relative pb-24 pt-16">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/[0.02] to-transparent" />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-foreground sm:text-4xl">
              为什么选择 <span className="text-primary">AI Trading</span>
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-lg text-muted-foreground">
              企业级安全、低延迟执行、全天候自动运行。
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
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
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
