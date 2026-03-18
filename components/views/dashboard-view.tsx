"use client"

import { useState } from "react"
import {
  Copy,
  Check,
  Send,
  Activity,
  TrendingUp,
  Clock,
  Zap,
  CircleDot,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table"

const webhookPayload = `{
  "action": "buy",
  "ticker": "BTCUSDT",
  "order_type": "market",
  "quantity": "0.05",
  "price": "{{close}}",
  "timestamp": "{{timenow}}",
  "passphrase": "your_secret_key",
  "exchange": "okx",
  "leverage": "3"
}`

const signalLogs = [
  {
    id: 1,
    time: "2026-02-26 12:03:45",
    action: "BUY",
    pair: "BTC/USDT",
    price: "64,280.50",
    status: "已执行",
  },
  {
    id: 2,
    time: "2026-02-26 11:58:12",
    action: "SELL",
    pair: "ETH/USDT",
    price: "3,421.80",
    status: "已执行",
  },
  {
    id: 3,
    time: "2026-02-26 11:45:30",
    action: "BUY",
    pair: "SOL/USDT",
    price: "142.35",
    status: "已执行",
  },
  {
    id: 4,
    time: "2026-02-26 11:32:08",
    action: "SELL",
    pair: "BTC/USDT",
    price: "64,520.00",
    status: "已执行",
  },
  {
    id: 5,
    time: "2026-02-26 11:20:55",
    action: "BUY",
    pair: "ETH/USDT",
    price: "3,398.20",
    status: "待处理",
  },
]

const subscriptions = [
  { name: "BTC 趋势跟踪", status: "运行中", daysLeft: 24 },
  { name: "ETH 网格交易", status: "运行中", daysLeft: 18 },
]

export function DashboardView() {
  const [copied, setCopied] = useState(false)
  const [testSent, setTestSent] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(webhookPayload)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleTestSignal = () => {
    setTestSent(true)
    setTimeout(() => setTestSent(false), 3000)
  }

  return (
    <div className="flex flex-col">
      {/* Header */}
      <section className="pt-8 pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-foreground">我的控制台</h1>
          <p className="mt-2 text-muted-foreground text-lg">管理订阅、查看信号日志、配置 Webhook。</p>
        </div>
      </section>

      {/* Stats Row */}
      <section className="pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: Activity, label: "活跃订阅", value: "2", color: "text-primary" },
              { icon: TrendingUp, label: "本月收益", value: "+12.8%", color: "text-emerald-400" },
              { icon: Zap, label: "今日信号", value: "47", color: "text-accent" },
              { icon: Clock, label: "运行时长", value: "724h", color: "text-primary" },
            ].map((stat) => (
              <div key={stat.label} className="glass-panel rounded-2xl p-5 flex items-center gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-secondary/50">
                  <stat.icon className={`h-5 w-5 ${stat.color}`} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Active Subscriptions */}
      <section className="pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-semibold text-foreground mb-4">活跃订阅</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {subscriptions.map((sub) => (
              <div key={sub.name} className="glass-panel rounded-2xl p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                    <CircleDot className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">{sub.name}</p>
                    <p className="text-xs text-muted-foreground">{"剩余 " + sub.daysLeft + " 天"}</p>
                  </div>
                </div>
                <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                  {sub.status}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Webhook Payload */}
      <section className="pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground">TradingView Webhook</h2>
            <button
              onClick={handleTestSignal}
              disabled={testSent}
              className="flex items-center gap-2 px-4 py-2 bg-accent/10 text-accent text-sm font-medium rounded-xl border border-accent/20 transition-all duration-300 hover:bg-accent/20 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              {testSent ? "信号已发送" : "发送测试信号"}
            </button>
          </div>
          <div className="glass-panel rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border/50">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-red-500/60" />
                <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
                <div className="h-3 w-3 rounded-full bg-emerald-500/60" />
                <span className="ml-2 text-xs text-muted-foreground font-mono">webhook-payload.json</span>
              </div>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-emerald-400">已复制</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    复制
                  </>
                )}
              </button>
            </div>
            <pre className="p-5 text-sm font-mono text-foreground/80 leading-relaxed overflow-x-auto">
              <code>{webhookPayload}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* Recent Signals Table */}
      <section className="pb-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-semibold text-foreground mb-4">近期信号</h2>
          <div className="glass-panel rounded-2xl overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-border/50 hover:bg-transparent">
                  <TableHead className="text-muted-foreground">时间</TableHead>
                  <TableHead className="text-muted-foreground">方向</TableHead>
                  <TableHead className="text-muted-foreground">交易对</TableHead>
                  <TableHead className="text-muted-foreground">价格</TableHead>
                  <TableHead className="text-muted-foreground text-right">状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {signalLogs.map((log) => (
                  <TableRow key={log.id} className="border-border/50">
                    <TableCell className="text-sm text-muted-foreground font-mono">{log.time}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex px-2.5 py-0.5 text-xs font-bold rounded-md ${
                          log.action === "BUY"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {log.action}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm font-medium text-foreground">{log.pair}</TableCell>
                    <TableCell className="text-sm text-foreground font-mono">${log.price}</TableCell>
                    <TableCell className="text-right">
                      <Badge
                        className={
                          log.status === "已执行"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                        }
                      >
                        {log.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </section>
    </div>
  )
}
