"use client"

import { type FormEvent, useEffect, useState } from "react"
import { Check, Copy, CreditCard, KeyRound, RefreshCcw, Save, ShieldAlert, Trash2 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { AUTH_TOKEN_STORAGE_KEY, type AuthUser } from "@/lib/auth"
import { getBackendApiBaseUrl } from "@/lib/backend-api"

type UserStats = { active_subscriptions: number; monthly_profit: string; today_signals: number; running_hours: number }
type Strategy = { id: number; name: string }
type Subscription = { id: string; strategy_id: number; end_date: string; status: string; profit_share_percent: string }
type Payment = { id: string; amount: string; status: string; tx_hash: string | null; created_at: string }
type Signal = { id: string; action: "buy" | "sell"; ticker: string; price: string | null; received_at: string; status: string }
type ExchangeApi = { id: string; exchange: "okx" | "binance"; api_key: string; is_active: boolean; last_verified_at: string | null }
type ProfileForm = { username: string; wallet_address: string }
type ExchangeForm = { exchange: "okx" | "binance"; api_key: string; api_secret: string; passphrase: string }

const EMPTY_STATS: UserStats = { active_subscriptions: 0, monthly_profit: "0", today_signals: 0, running_hours: 0 }
const EMPTY_PROFILE: ProfileForm = { username: "", wallet_address: "" }
const EMPTY_EXCHANGE: ExchangeForm = { exchange: "okx", api_key: "", api_secret: "", passphrase: "" }

function fmtDate(value: string | null) {
  if (!value) return "-"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN")
}

function fmtPrice(value: string | null) {
  if (!value) return "-"
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)} USDT` : value
}

function fmtPercent(value: string) {
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)}%` : value
}

async function readResponseMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string; message?: string }
    return payload.detail || payload.message || `请求失败，状态码 ${response.status}`
  } catch {
    return `请求失败，状态码 ${response.status}`
  }
}

export function DashboardView() {
  const [token, setToken] = useState<string | null>(null)
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [booting, setBooting] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [stats, setStats] = useState<UserStats>(EMPTY_STATS)
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [signals, setSignals] = useState<Signal[]>([])
  const [exchanges, setExchanges] = useState<ExchangeApi[]>([])
  const [profileForm, setProfileForm] = useState<ProfileForm>(EMPTY_PROFILE)
  const [exchangeForm, setExchangeForm] = useState<ExchangeForm>(EMPTY_EXCHANGE)
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingExchange, setSavingExchange] = useState(false)
  const [verifyingExchangeId, setVerifyingExchangeId] = useState<string | null>(null)
  const [deletingExchangeId, setDeletingExchangeId] = useState<string | null>(null)
  const [copiedWebhookUrl, setCopiedWebhookUrl] = useState(false)
  const [copiedWebhookPayload, setCopiedWebhookPayload] = useState(false)

  const strategyNameById = Object.fromEntries(strategies.map((item) => [item.id, item.name]))
  const webhookUrl = `${getBackendApiBaseUrl()}/api/webhook/receive`
  const webhookPayload = JSON.stringify(
    {
      strategy_id: subscriptions[0]?.strategy_id ?? "YOUR_STRATEGY_ID",
      action: "buy",
      ticker: "BTCUSDT",
      order_type: "market",
      quantity: "0.01",
      price: "{{close}}",
      timestamp: "{{timenow}}",
      passphrase: "你的TradingView口令",
      exchange: exchangeForm.exchange,
      leverage: 3,
    },
    null,
    2,
  )

  async function refreshDashboard(currentToken = token) {
    if (!currentToken) return
    try {
      setLoading(true)
      setError(null)
      const headers = { Authorization: `Bearer ${currentToken}` }
      const [profileRes, statsRes, subscriptionsRes, paymentsRes, signalsRes, exchangesRes, strategiesRes] = await Promise.all([
        fetch("/api/users/profile", { headers, cache: "no-store" }),
        fetch("/api/stats/user", { headers, cache: "no-store" }),
        fetch("/api/subscriptions", { headers, cache: "no-store" }),
        fetch("/api/payments/history", { headers, cache: "no-store" }),
        fetch("/api/signals?limit=10", { headers, cache: "no-store" }),
        fetch("/api/exchanges/apis", { headers, cache: "no-store" }),
        fetch("/api/strategies", { cache: "no-store" }),
      ])
      if (!profileRes.ok) throw new Error(await readResponseMessage(profileRes))
      if (!statsRes.ok) throw new Error(await readResponseMessage(statsRes))
      if (!subscriptionsRes.ok) throw new Error(await readResponseMessage(subscriptionsRes))
      if (!paymentsRes.ok) throw new Error(await readResponseMessage(paymentsRes))
      if (!signalsRes.ok) throw new Error(await readResponseMessage(signalsRes))
      if (!exchangesRes.ok) throw new Error(await readResponseMessage(exchangesRes))
      if (!strategiesRes.ok) throw new Error(await readResponseMessage(strategiesRes))

      const [profile, statsPayload, subscriptionsPayload, paymentsPayload, signalsPayload, exchangesPayload, strategiesPayload] = await Promise.all([
        profileRes.json() as Promise<AuthUser>,
        statsRes.json() as Promise<UserStats>,
        subscriptionsRes.json() as Promise<Subscription[]>,
        paymentsRes.json() as Promise<Payment[]>,
        signalsRes.json() as Promise<Signal[]>,
        exchangesRes.json() as Promise<ExchangeApi[]>,
        strategiesRes.json() as Promise<Strategy[]>,
      ])

      setCurrentUser(profile)
      setProfileForm({ username: profile.username, wallet_address: profile.wallet_address ?? "" })
      setStats(statsPayload)
      setSubscriptions(subscriptionsPayload)
      setPayments(paymentsPayload)
      setSignals(signalsPayload)
      setExchanges(exchangesPayload)
      setStrategies(strategiesPayload)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "暂时无法加载控制台数据。")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    async function bootstrap() {
      const storedToken = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
      if (!storedToken) {
        if (!cancelled) setBooting(false)
        return
      }
      try {
        const response = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${storedToken}` },
          cache: "no-store",
        })
        if (!response.ok) throw new Error(await readResponseMessage(response))
        const user = (await response.json()) as AuthUser
        if (!cancelled) {
          setToken(storedToken)
          setCurrentUser(user)
          setProfileForm({ username: user.username, wallet_address: user.wallet_address ?? "" })
          await refreshDashboard(storedToken)
        }
      } catch {
        window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
        if (!cancelled) {
          setToken(null)
          setCurrentUser(null)
        }
      } finally {
        if (!cancelled) setBooting(false)
      }
    }
    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [])

  async function copyText(value: string, kind: "url" | "payload") {
    await navigator.clipboard.writeText(value)
    if (kind === "url") {
      setCopiedWebhookUrl(true)
      window.setTimeout(() => setCopiedWebhookUrl(false), 2000)
      return
    }
    setCopiedWebhookPayload(true)
    window.setTimeout(() => setCopiedWebhookPayload(false), 2000)
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    try {
      setSavingProfile(true)
      setError(null)
      setMessage(null)
      const response = await fetch("/api/users/profile", {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ username: profileForm.username.trim(), wallet_address: profileForm.wallet_address.trim() || null }),
      })
      if (!response.ok) throw new Error(await readResponseMessage(response))
      const updated = (await response.json()) as AuthUser
      setCurrentUser(updated)
      setProfileForm({ username: updated.username, wallet_address: updated.wallet_address ?? "" })
      setMessage("账户资料已更新。")
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "暂时无法更新账户资料。")
    } finally {
      setSavingProfile(false)
    }
  }

  async function createExchangeApi(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    try {
      setSavingExchange(true)
      setError(null)
      setMessage(null)
      const response = await fetch("/api/exchanges/apis", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          exchange: exchangeForm.exchange,
          api_key: exchangeForm.api_key.trim(),
          api_secret: exchangeForm.api_secret.trim(),
          passphrase: exchangeForm.exchange === "okx" ? exchangeForm.passphrase.trim() || null : null,
        }),
      })
      if (!response.ok) throw new Error(await readResponseMessage(response))
      setExchangeForm(EMPTY_EXCHANGE)
      setMessage("交易所 API 已保存。")
      await refreshDashboard()
    } catch (exchangeError) {
      setError(exchangeError instanceof Error ? exchangeError.message : "暂时无法保存交易所 API。")
    } finally {
      setSavingExchange(false)
    }
  }

  async function verifyExchangeApi(apiId: string) {
    if (!token) return
    try {
      setVerifyingExchangeId(apiId)
      setError(null)
      setMessage(null)
      const response = await fetch(`/api/exchanges/apis/${apiId}/verify`, { method: "POST", headers: { Authorization: `Bearer ${token}` } })
      if (!response.ok) throw new Error(await readResponseMessage(response))
      const payload = (await response.json()) as { message?: string }
      setMessage(payload.message || "交易所连接验证成功。")
      await refreshDashboard()
    } catch (verifyError) {
      setError(verifyError instanceof Error ? verifyError.message : "暂时无法验证交易所连接。")
    } finally {
      setVerifyingExchangeId(null)
    }
  }

  async function deleteExchangeApi(apiId: string) {
    if (!token) return
    try {
      setDeletingExchangeId(apiId)
      setError(null)
      setMessage(null)
      const response = await fetch(`/api/exchanges/apis/${apiId}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } })
      if (!response.ok) throw new Error(await readResponseMessage(response))
      setMessage("交易所 API 已删除。")
      await refreshDashboard()
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "暂时无法删除交易所 API。")
    } finally {
      setDeletingExchangeId(null)
    }
  }

  if (booting) {
    return <section className="pt-8 pb-24"><div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8"><div className="glass-panel rounded-3xl p-8 text-sm text-muted-foreground">正在检查登录状态...</div></div></section>
  }

  if (!currentUser) {
    return <section className="pt-8 pb-24"><div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8"><div className="glass-panel rounded-3xl border border-amber-500/20 bg-amber-500/5 p-8"><div className="flex items-center gap-3 text-amber-200"><ShieldAlert className="h-5 w-5" /><h1 className="text-xl font-semibold">需要先登录</h1></div><p className="mt-3 text-sm leading-7 text-muted-foreground">登录后，这里会展示你的真实订阅、支付记录、交易信号、交易所 API 和 Webhook 配置信息。</p></div></div></section>
  }

  return (
    <div className="flex flex-col">
      <section className="pt-8 pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground sm:text-4xl">我的控制台</h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground sm:text-base">这里已经切到真实后端数据：订阅、支付、信号、交易所 API 和 Webhook 信息都会从云端读取。</p>
            </div>
            <Button variant="outline" onClick={() => void refreshDashboard()} disabled={loading}><RefreshCcw className="h-4 w-4" />刷新控制台</Button>
          </div>
        </div>
      </section>

      <section className="pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {error && <div className="mb-4 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>}
          {message && <div className="mb-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">{message}</div>}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {[{ label: "活跃订阅", value: String(stats.active_subscriptions), hint: "已审核并生效" }, { label: "本月收益", value: fmtPrice(stats.monthly_profit), hint: "来自统计接口" }, { label: "今日信号", value: String(stats.today_signals), hint: "来自信号日志" }, { label: "运行时长", value: `${stats.running_hours}h`, hint: "按订阅数据估算" }].map((item) => <div key={item.label} className="glass-panel rounded-2xl p-5"><p className="text-sm text-muted-foreground">{item.label}</p><p className="mt-2 text-xl font-bold text-foreground">{item.value}</p><p className="mt-4 text-xs text-muted-foreground">{item.hint}</p></div>)}
          </div>
        </div>
      </section>

      <section className="pb-8">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 sm:px-6 lg:grid-cols-[1.2fr_0.8fr] lg:px-8">
          <div className="glass-panel rounded-3xl p-6">
            <h2 className="text-xl font-semibold text-foreground">账户资料</h2>
            <p className="mt-1 text-sm text-muted-foreground">用户名和钱包地址可以在这里维护。邮箱保持只读，避免影响当前验证状态。</p>
            <form className="mt-5 grid gap-5" onSubmit={saveProfile}>
              <div className="grid gap-2"><Label htmlFor="profile-username">用户名</Label><Input id="profile-username" value={profileForm.username} onChange={(event) => setProfileForm((current) => ({ ...current, username: event.target.value }))} required /></div>
              <div className="grid gap-2"><Label htmlFor="profile-email">邮箱</Label><Input id="profile-email" value={currentUser.email} disabled /></div>
              <div className="grid gap-2"><Label htmlFor="profile-wallet">钱包地址</Label><Input id="profile-wallet" value={profileForm.wallet_address} onChange={(event) => setProfileForm((current) => ({ ...current, wallet_address: event.target.value }))} placeholder="可选，不填也可以" /></div>
              <div className="flex flex-wrap items-center gap-3"><Button type="submit" disabled={savingProfile}><Save className="h-4 w-4" />{savingProfile ? "保存中..." : "保存资料"}</Button><Badge className={currentUser.email_verified ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" : "border-amber-500/20 bg-amber-500/10 text-amber-300"}>{currentUser.email_verified ? "邮箱已验证" : "邮箱待验证"}</Badge></div>
            </form>
          </div>

          <div className="glass-panel rounded-3xl p-6">
            <h2 className="text-xl font-semibold text-foreground">活跃订阅</h2>
            <p className="mt-1 text-sm text-muted-foreground">这里会显示你已经生效的策略订阅和待审核订单。</p>
            <div className="mt-5 grid gap-4">
              {subscriptions.length === 0 ? <div className="rounded-2xl border border-border/50 bg-secondary/20 p-4 text-sm text-muted-foreground">你还没有任何订阅。去策略大厅下单后，这里会自动显示真实状态。</div> : subscriptions.map((subscription) => <div key={subscription.id} className="rounded-2xl border border-border/50 bg-secondary/20 p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-medium text-foreground">{strategyNameById[subscription.strategy_id] ?? `策略 #${subscription.strategy_id}`}</p><p className="mt-1 text-xs text-muted-foreground">到期时间：{fmtDate(subscription.end_date)}</p><p className="mt-1 text-xs text-muted-foreground">分润比例：{fmtPercent(subscription.profit_share_percent)}</p></div><Badge className={subscription.status === "active" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" : subscription.status === "pending" ? "border-amber-500/20 bg-amber-500/10 text-amber-300" : subscription.status === "expired" ? "border-zinc-500/20 bg-zinc-500/10 text-zinc-300" : "border-red-500/20 bg-red-500/10 text-red-300"}>{subscription.status === "active" ? "运行中" : subscription.status === "pending" ? "待审核" : subscription.status === "expired" ? "已到期" : "已取消"}</Badge></div></div>)}
            </div>
          </div>
        </div>
      </section>

      <section className="pb-8">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
          <div className="glass-panel rounded-3xl p-6">
            <h2 className="text-xl font-semibold text-foreground">交易所 API 绑定</h2>
            <p className="mt-1 text-sm text-muted-foreground">当前支持 OKX 和 Binance，可以直接绑定、验证和删除。</p>
            <form className="mt-5 grid gap-5" onSubmit={createExchangeApi}>
              <div className="grid gap-2"><Label>交易所</Label><Select value={exchangeForm.exchange} onValueChange={(value: "okx" | "binance") => setExchangeForm((current) => ({ ...current, exchange: value }))}><SelectTrigger className="w-full"><SelectValue placeholder="请选择交易所" /></SelectTrigger><SelectContent><SelectItem value="okx">OKX</SelectItem><SelectItem value="binance">Binance</SelectItem></SelectContent></Select></div>
              <div className="grid gap-2"><Label htmlFor="exchange-api-key">接口密钥（API Key）</Label><Input id="exchange-api-key" value={exchangeForm.api_key} onChange={(event) => setExchangeForm((current) => ({ ...current, api_key: event.target.value }))} required /></div>
              <div className="grid gap-2"><Label htmlFor="exchange-api-secret">接口私钥（API Secret）</Label><Input id="exchange-api-secret" type="password" value={exchangeForm.api_secret} onChange={(event) => setExchangeForm((current) => ({ ...current, api_secret: event.target.value }))} required /></div>
              {exchangeForm.exchange === "okx" && <div className="grid gap-2"><Label htmlFor="exchange-passphrase">接口口令（Passphrase）</Label><Input id="exchange-passphrase" type="password" value={exchangeForm.passphrase} onChange={(event) => setExchangeForm((current) => ({ ...current, passphrase: event.target.value }))} /></div>}
              <Button type="submit" disabled={savingExchange}><KeyRound className="h-4 w-4" />{savingExchange ? "保存中..." : "绑定交易所 API"}</Button>
            </form>
            <div className="mt-6 grid gap-4">
              {exchanges.length === 0 ? <div className="rounded-2xl border border-border/50 bg-secondary/20 p-4 text-sm text-muted-foreground">你还没有绑定任何交易所 API。</div> : exchanges.map((exchangeApi) => <div key={exchangeApi.id} className="rounded-2xl border border-border/50 bg-secondary/20 p-4"><div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"><div><div className="flex items-center gap-3"><p className="font-medium text-foreground">{exchangeApi.exchange.toUpperCase()}</p><Badge className="border-primary/20 bg-primary/10 text-primary">{exchangeApi.api_key}</Badge><Badge className={exchangeApi.is_active ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" : "border-zinc-500/20 bg-zinc-500/10 text-zinc-300"}>{exchangeApi.is_active ? "已启用" : "未启用"}</Badge></div><p className="mt-2 text-xs text-muted-foreground">最后验证时间：{fmtDate(exchangeApi.last_verified_at)}</p></div><div className="flex flex-wrap gap-2"><Button variant="outline" size="sm" onClick={() => void verifyExchangeApi(exchangeApi.id)} disabled={verifyingExchangeId === exchangeApi.id}>{verifyingExchangeId === exchangeApi.id ? "验证中..." : "验证连接"}</Button><Button variant="outline" size="sm" onClick={() => void deleteExchangeApi(exchangeApi.id)} disabled={deletingExchangeId === exchangeApi.id}><Trash2 className="h-4 w-4" />{deletingExchangeId === exchangeApi.id ? "删除中..." : "删除"}</Button></div></div></div>)}
            </div>
          </div>

          <div className="glass-panel rounded-3xl p-6">
            <h2 className="text-xl font-semibold text-foreground">TradingView Webhook 配置</h2>
            <p className="mt-1 text-sm text-muted-foreground">这里提供可直接复制的地址和消息模板，口令字段需要替换成你在 Cloud Run 中配置的值。</p>
            <div className="mt-5 grid gap-5">
              <div className="grid gap-2"><Label htmlFor="webhook-url">Webhook 地址</Label><div className="flex gap-2"><Input id="webhook-url" value={webhookUrl} readOnly /><Button type="button" variant="outline" onClick={() => void copyText(webhookUrl, "url")}>{copiedWebhookUrl ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}</Button></div></div>
              <div className="rounded-2xl border border-border/50 bg-secondary/20 p-4"><div className="mb-3 flex items-center justify-between gap-3"><span className="text-sm font-medium text-foreground">消息模板（JSON）</span><Button type="button" variant="outline" size="sm" onClick={() => void copyText(webhookPayload, "payload")}>{copiedWebhookPayload ? "已复制" : "复制"}</Button></div><pre className="overflow-x-auto text-xs leading-6 text-muted-foreground"><code>{webhookPayload}</code></pre></div>
            </div>
          </div>
        </div>
      </section>

      <section className="pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="glass-panel rounded-3xl p-6">
            <div className="mb-5 flex items-center justify-between gap-3"><div><h2 className="text-xl font-semibold text-foreground">支付记录</h2><p className="mt-1 text-sm text-muted-foreground">下单、提交交易哈希、审核状态都会显示在这里。</p></div><CreditCard className="h-5 w-5 text-primary" /></div>
            <Table><TableHeader><TableRow className="border-border/50 hover:bg-transparent"><TableHead>订单号</TableHead><TableHead>金额</TableHead><TableHead>状态</TableHead><TableHead>交易哈希</TableHead><TableHead>创建时间</TableHead></TableRow></TableHeader><TableBody>{payments.length === 0 ? <TableRow className="border-border/50"><TableCell colSpan={5} className="px-6 py-10 text-center text-sm text-muted-foreground">你还没有支付记录。去策略大厅创建订单后，这里会自动显示真实数据。</TableCell></TableRow> : payments.map((payment) => <TableRow key={payment.id} className="border-border/50"><TableCell className="font-mono text-xs text-muted-foreground">{payment.id}</TableCell><TableCell>{fmtPrice(payment.amount)}</TableCell><TableCell><Badge className={payment.status === "success" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" : payment.status === "pending" ? "border-amber-500/20 bg-amber-500/10 text-amber-300" : "border-red-500/20 bg-red-500/10 text-red-300"}>{payment.status === "success" ? "已完成" : payment.status === "pending" ? "待审核" : "失败"}</Badge></TableCell><TableCell className="max-w-[16rem] break-all whitespace-normal text-xs text-muted-foreground">{payment.tx_hash || "未提交"}</TableCell><TableCell className="text-xs text-muted-foreground">{fmtDate(payment.created_at)}</TableCell></TableRow>)}</TableBody></Table>
          </div>
        </div>
      </section>

      <section className="pb-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="glass-panel rounded-3xl p-6">
            <div className="mb-5 flex items-center justify-between gap-3"><div><h2 className="text-xl font-semibold text-foreground">最近信号</h2><p className="mt-1 text-sm text-muted-foreground">这里读取的是你真实可见的信号日志。</p></div><Button variant="outline" size="sm" onClick={() => void refreshDashboard()} disabled={loading}><RefreshCcw className="h-4 w-4" />刷新</Button></div>
            <Table><TableHeader><TableRow className="border-border/50 hover:bg-transparent"><TableHead>时间</TableHead><TableHead>方向</TableHead><TableHead>交易对</TableHead><TableHead>状态</TableHead><TableHead>价格</TableHead></TableRow></TableHeader><TableBody>{signals.length === 0 ? <TableRow className="border-border/50"><TableCell colSpan={5} className="px-6 py-10 text-center text-sm text-muted-foreground">当前还没有信号日志。等策略接到真实信号后，这里会开始累计记录。</TableCell></TableRow> : signals.map((signal) => <TableRow key={signal.id} className="border-border/50"><TableCell className="text-xs text-muted-foreground">{fmtDate(signal.received_at)}</TableCell><TableCell><Badge className={signal.action === "buy" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" : "border-red-500/20 bg-red-500/10 text-red-300"}>{signal.action.toUpperCase()}</Badge></TableCell><TableCell className="font-medium text-foreground">{signal.ticker}</TableCell><TableCell><Badge className={signal.status === "completed" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" : signal.status === "pending" ? "border-amber-500/20 bg-amber-500/10 text-amber-300" : signal.status === "processing" ? "border-primary/20 bg-primary/10 text-primary" : "border-red-500/20 bg-red-500/10 text-red-300"}>{signal.status === "completed" ? "已完成" : signal.status === "pending" ? "待处理" : signal.status === "processing" ? "处理中" : "失败"}</Badge></TableCell><TableCell className="text-sm text-muted-foreground">{signal.price ? fmtPrice(signal.price) : "市价"}</TableCell></TableRow>)}</TableBody></Table>
          </div>
        </div>
      </section>
    </div>
  )
}
