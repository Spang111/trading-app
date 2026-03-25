"use client"

import { type FormEvent, useEffect, useState } from "react"
import { Edit3, Plus, RefreshCcw, ShieldAlert, ShieldCheck, Wallet } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { AUTH_TOKEN_STORAGE_KEY, type AuthUser } from "@/lib/auth"

type StrategyStatus = "active" | "inactive"
type PaymentStatus = "pending" | "success" | "failed"

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
  status: StrategyStatus
  created_at: string
}

type PendingPayment = {
  id: string
  user_id: number
  subscription_id: string | null
  amount: string
  payment_method: string
  tx_hash: string | null
  status: PaymentStatus
  created_at: string
}

type StrategyFormState = {
  name: string
  description: string
  apy: string
  max_drawdown: string
  win_rate: string
  monthly_price: string
  yearly_price: string
  tag: string
  status: StrategyStatus
}

const INITIAL_FORM_STATE: StrategyFormState = {
  name: "",
  description: "",
  apy: "",
  max_drawdown: "",
  win_rate: "",
  monthly_price: "",
  yearly_price: "",
  tag: "",
  status: "active",
}

function formatPercent(value: string) {
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)}%` : value
}

function formatPrice(value: string) {
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)} USDT` : value
}

function formatDateTime(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
}

function getFormStateFromStrategy(strategy: Strategy): StrategyFormState {
  return {
    name: strategy.name,
    description: strategy.description ?? "",
    apy: strategy.apy,
    max_drawdown: strategy.max_drawdown,
    win_rate: strategy.win_rate,
    monthly_price: strategy.monthly_price,
    yearly_price: strategy.yearly_price,
    tag: strategy.tag ?? "",
    status: strategy.status,
  }
}

async function readResponseMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string; message?: string }
    return payload.detail || payload.message || `请求失败，状态码 ${response.status}`
  } catch {
    return `请求失败，状态码 ${response.status}`
  }
}

export function AdminStrategiesView() {
  const [token, setToken] = useState<string | null>(null)
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [pendingPayments, setPendingPayments] = useState<PendingPayment[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null)
  const [formState, setFormState] = useState<StrategyFormState>(INITIAL_FORM_STATE)
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [approvingPaymentId, setApprovingPaymentId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      const storedToken = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)

      if (!storedToken) {
        if (!cancelled) {
          setCurrentUser(null)
          setToken(null)
          setIsBootstrapping(false)
        }
        return
      }

      try {
        const response = await fetch("/api/auth/me", {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
          cache: "no-store",
        })

        if (!response.ok) {
          throw new Error(await readResponseMessage(response))
        }

        const user = (await response.json()) as AuthUser

        if (!cancelled) {
          setCurrentUser(user)
          setToken(storedToken)
        }
      } catch {
        window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)

        if (!cancelled) {
          setCurrentUser(null)
          setToken(null)
        }
      } finally {
        if (!cancelled) {
          setIsBootstrapping(false)
        }
      }
    }

    void bootstrap()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!token || currentUser?.role !== "admin") {
      return
    }

    void refreshAll(token)
  }, [currentUser?.role, token])

  async function refreshAll(currentToken = token) {
    if (!currentToken) {
      return
    }

    try {
      setIsRefreshing(true)
      setLoadError(null)

      const headers = {
        Authorization: `Bearer ${currentToken}`,
      }

      const [strategiesResponse, pendingPaymentsResponse] = await Promise.all([
        fetch("/api/admin/strategies", { headers, cache: "no-store" }),
        fetch("/api/admin/payments/pending", { headers, cache: "no-store" }),
      ])

      if (!strategiesResponse.ok) {
        throw new Error(await readResponseMessage(strategiesResponse))
      }

      if (!pendingPaymentsResponse.ok) {
        throw new Error(await readResponseMessage(pendingPaymentsResponse))
      }

      const [strategiesPayload, pendingPaymentsPayload] = await Promise.all([
        strategiesResponse.json() as Promise<Strategy[]>,
        pendingPaymentsResponse.json() as Promise<PendingPayment[]>,
      ])

      setStrategies(strategiesPayload)
      setPendingPayments(pendingPaymentsPayload)
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "暂时无法加载管理员数据。")
    } finally {
      setIsRefreshing(false)
    }
  }

  function openCreateDialog() {
    setEditingStrategy(null)
    setFormState(INITIAL_FORM_STATE)
    setFormError(null)
    setDialogOpen(true)
  }

  function openEditDialog(strategy: Strategy) {
    setEditingStrategy(strategy)
    setFormState(getFormStateFromStrategy(strategy))
    setFormError(null)
    setDialogOpen(true)
  }

  function handleDialogOpenChange(open: boolean) {
    setDialogOpen(open)
    if (!open) {
      setEditingStrategy(null)
      setFormState(INITIAL_FORM_STATE)
      setFormError(null)
    }
  }

  function updateField<K extends keyof StrategyFormState>(field: K, value: StrategyFormState[K]) {
    setFormState((current) => ({
      ...current,
      [field]: value,
    }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!token) {
      setFormError("当前登录状态已失效，请重新登录管理员账号。")
      return
    }

    try {
      setIsSubmitting(true)
      setFormError(null)
      setActionMessage(null)

      const payload = {
        name: formState.name.trim(),
        description: formState.description.trim() || null,
        apy: formState.apy.trim(),
        max_drawdown: formState.max_drawdown.trim(),
        win_rate: formState.win_rate.trim(),
        monthly_price: formState.monthly_price.trim(),
        yearly_price: formState.yearly_price.trim(),
        tag: formState.tag.trim() || null,
        ...(editingStrategy ? { status: formState.status } : {}),
      }

      const endpoint = editingStrategy
        ? `/api/admin/strategies/${editingStrategy.id}`
        : "/api/admin/strategies"
      const method = editingStrategy ? "PUT" : "POST"

      const response = await fetch(endpoint, {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(await readResponseMessage(response))
      }

      const savedStrategy = (await response.json()) as Strategy

      setStrategies((current) => {
        if (!editingStrategy) {
          return [savedStrategy, ...current]
        }

        return current.map((item) => (item.id === savedStrategy.id ? savedStrategy : item))
      })

      setActionMessage(editingStrategy ? "策略已更新。" : "策略已创建。")
      handleDialogOpenChange(false)
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "暂时无法保存策略。")
    } finally {
      setIsSubmitting(false)
    }
  }

  async function toggleStrategyStatus(strategy: Strategy) {
    if (!token) {
      setLoadError("当前登录状态已失效，请重新登录管理员账号。")
      return
    }

    const nextStatus: StrategyStatus = strategy.status === "active" ? "inactive" : "active"

    try {
      setActionMessage(null)

      const response = await fetch(`/api/admin/strategies/${strategy.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: nextStatus }),
      })

      if (!response.ok) {
        throw new Error(await readResponseMessage(response))
      }

      const updatedStrategy = (await response.json()) as Strategy

      setStrategies((current) =>
        current.map((item) => (item.id === updatedStrategy.id ? updatedStrategy : item)),
      )
      setActionMessage(updatedStrategy.status === "active" ? "策略已重新上架。" : "策略已下架。")
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "暂时无法切换策略状态。")
    }
  }

  async function approvePayment(paymentId: string) {
    if (!token) {
      setLoadError("当前登录状态已失效，请重新登录管理员账号。")
      return
    }

    try {
      setApprovingPaymentId(paymentId)
      setActionMessage(null)
      setLoadError(null)

      const response = await fetch(`/api/admin/payments/${paymentId}/approve`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error(await readResponseMessage(response))
      }

      setPendingPayments((current) => current.filter((item) => item.id !== paymentId))
      setActionMessage("支付已审核通过，关联订阅已激活。")
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "暂时无法审核该笔支付。")
    } finally {
      setApprovingPaymentId(null)
    }
  }

  if (isBootstrapping) {
    return (
      <section className="pt-8 pb-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="glass-panel rounded-3xl p-8 text-sm text-muted-foreground">
            正在检查管理员登录状态...
          </div>
        </div>
      </section>
    )
  }

  if (!currentUser) {
    return (
      <section className="pt-8 pb-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="glass-panel rounded-3xl border border-amber-500/20 bg-amber-500/5 p-8">
            <div className="flex items-center gap-3 text-amber-200">
              <ShieldAlert className="h-5 w-5" />
              <h1 className="text-xl font-semibold">需要管理员登录</h1>
            </div>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              这个页面只开放给管理员使用。先在右上角登录管理员账号，我们就可以直接在网页里新增策略、
              审核支付、控制策略上下架了。
            </p>
          </div>
        </div>
      </section>
    )
  }

  if (currentUser.role !== "admin") {
    return (
      <section className="pt-8 pb-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="glass-panel rounded-3xl border border-red-500/20 bg-red-500/5 p-8">
            <div className="flex items-center gap-3 text-red-200">
              <ShieldAlert className="h-5 w-5" />
              <h1 className="text-xl font-semibold">当前账号不是管理员</h1>
            </div>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              你当前登录的是普通账号，暂时不能管理策略或审核订单。把这个账号提升成管理员后，
              再回到这里就可以继续。
            </p>
          </div>
        </div>
      </section>
    )
  }

  return (
    <div className="flex flex-col">
      <section className="pt-8 pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
                <ShieldCheck className="h-4 w-4" />
                管理员后台
              </div>
              <h1 className="text-3xl font-bold text-foreground sm:text-4xl">策略与支付审核</h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground sm:text-base">
                这里直接控制策略大厅展示的真实内容，同时处理用户提交的链上支付审核。
                审核通过后，订阅会自动激活。
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={() => void refreshAll()} disabled={isRefreshing}>
                <RefreshCcw className="h-4 w-4" />
                刷新数据
              </Button>
              <Button onClick={openCreateDialog}>
                <Plus className="h-4 w-4" />
                新增策略
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {loadError && (
            <div className="mb-4 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">
              {loadError}
            </div>
          )}

          {actionMessage && (
            <div className="mb-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">
              {actionMessage}
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-3">
            <div className="glass-panel rounded-3xl p-6">
              <p className="text-sm text-muted-foreground">策略总数</p>
              <p className="mt-2 text-3xl font-bold text-foreground">{strategies.length}</p>
              <p className="mt-2 text-xs text-muted-foreground">包含上架和下架中的全部策略。</p>
            </div>
            <div className="glass-panel rounded-3xl p-6">
              <p className="text-sm text-muted-foreground">待审核支付</p>
              <p className="mt-2 text-3xl font-bold text-primary">{pendingPayments.length}</p>
              <p className="mt-2 text-xs text-muted-foreground">用户提交交易哈希后会出现在这里。</p>
            </div>
            <div className="glass-panel rounded-3xl p-6">
              <p className="text-sm text-muted-foreground">当前管理员</p>
              <p className="mt-2 text-2xl font-bold text-foreground">{currentUser.username}</p>
              <p className="mt-2 text-xs text-muted-foreground">{currentUser.email}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="pb-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="glass-panel overflow-hidden rounded-3xl border border-border/50">
            <div className="flex items-center justify-between border-b border-border/50 px-6 py-4">
              <div>
                <h2 className="text-lg font-semibold text-foreground">待审核支付</h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  用户完成链上转账并提交交易哈希后，你可以在这里通过审核。
                </p>
              </div>
              {isRefreshing && <span className="text-xs text-muted-foreground">正在同步后台数据...</span>}
            </div>

            <Table>
              <TableHeader>
                <TableRow className="border-border/50 hover:bg-transparent">
                  <TableHead>支付单号</TableHead>
                  <TableHead>用户 ID</TableHead>
                  <TableHead>金额</TableHead>
                  <TableHead>支付方式</TableHead>
                  <TableHead>交易哈希</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingPayments.length === 0 ? (
                  <TableRow className="border-border/50">
                    <TableCell colSpan={7} className="px-6 py-10 text-center text-sm text-muted-foreground">
                      目前没有待审核支付，新的支付单会自动出现在这里。
                    </TableCell>
                  </TableRow>
                ) : (
                  pendingPayments.map((payment) => (
                    <TableRow key={payment.id} className="border-border/50">
                      <TableCell className="font-mono text-xs text-muted-foreground">{payment.id}</TableCell>
                      <TableCell>{payment.user_id}</TableCell>
                      <TableCell className="font-medium text-foreground">{formatPrice(payment.amount)}</TableCell>
                      <TableCell>{payment.payment_method}</TableCell>
                      <TableCell className="max-w-[16rem] break-all text-xs text-muted-foreground whitespace-normal">
                        {payment.tx_hash || "用户还没有提交交易哈希"}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{formatDateTime(payment.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          onClick={() => void approvePayment(payment.id)}
                          disabled={approvingPaymentId === payment.id}
                        >
                          <Wallet className="h-4 w-4" />
                          {approvingPaymentId === payment.id ? "审核中..." : "通过审核"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </section>

      <section className="pb-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="glass-panel overflow-hidden rounded-3xl border border-border/50">
            <div className="flex items-center justify-between border-b border-border/50 px-6 py-4">
              <div>
                <h2 className="text-lg font-semibold text-foreground">策略列表</h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  策略大厅会直接读取这里维护的真实策略数据。
                </p>
              </div>
            </div>

            <Table>
              <TableHeader>
                <TableRow className="border-border/50 hover:bg-transparent">
                  <TableHead>策略名称</TableHead>
                  <TableHead>标签</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>年化收益</TableHead>
                  <TableHead>月费</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {strategies.length === 0 ? (
                  <TableRow className="border-border/50">
                    <TableCell colSpan={7} className="px-6 py-10 text-center text-sm text-muted-foreground">
                      还没有策略数据。点击右上角“新增策略”就可以开始上传第一条策略。
                    </TableCell>
                  </TableRow>
                ) : (
                  strategies.map((strategy) => (
                    <TableRow key={strategy.id} className="border-border/50">
                      <TableCell className="max-w-[18rem] whitespace-normal">
                        <div className="flex flex-col gap-1">
                          <span className="font-medium text-foreground">{strategy.name}</span>
                          <span className="line-clamp-2 text-xs leading-6 text-muted-foreground">
                            {strategy.description || "暂无描述"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className="border-primary/20 bg-primary/10 text-primary">
                          {(strategy.tag || "none").toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            strategy.status === "active"
                              ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                              : "border-zinc-500/20 bg-zinc-500/10 text-zinc-300"
                          }
                        >
                          {strategy.status === "active" ? "已上架" : "已下架"}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium text-emerald-400">
                        {formatPercent(strategy.apy)}
                      </TableCell>
                      <TableCell>{formatPrice(strategy.monthly_price)}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{formatDateTime(strategy.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" size="sm" onClick={() => openEditDialog(strategy)}>
                            <Edit3 className="h-4 w-4" />
                            编辑
                          </Button>
                          <Button
                            size="sm"
                            variant={strategy.status === "active" ? "outline" : "default"}
                            onClick={() => void toggleStrategyStatus(strategy)}
                          >
                            {strategy.status === "active" ? "下架" : "上架"}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </section>

      <Dialog open={dialogOpen} onOpenChange={handleDialogOpenChange}>
        <DialogContent className="max-w-2xl rounded-3xl border-border/60 bg-background/95">
          <DialogHeader>
            <DialogTitle>{editingStrategy ? "编辑策略" : "新增策略"}</DialogTitle>
            <DialogDescription>
              {editingStrategy
                ? "修改这条策略的展示信息和上下架状态。保存后，前端策略大厅会读取新的真实数据。"
                : "填写后会直接创建一条新策略，并自动生成默认的月付和年付套餐。"}
            </DialogDescription>
          </DialogHeader>

          <form className="grid gap-5" onSubmit={handleSubmit}>
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="strategy-name">策略名称</Label>
                <Input
                  id="strategy-name"
                  value={formState.name}
                  onChange={(event) => updateField("name", event.target.value)}
                  placeholder="例如：BTC AI Trend Strategy"
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="strategy-tag">标签</Label>
                <Input
                  id="strategy-tag"
                  value={formState.tag}
                  onChange={(event) => updateField("tag", event.target.value)}
                  placeholder="例如：btc"
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="strategy-apy">年化收益 (%)</Label>
                <Input
                  id="strategy-apy"
                  type="number"
                  min="0"
                  step="0.01"
                  value={formState.apy}
                  onChange={(event) => updateField("apy", event.target.value)}
                  placeholder="18.50"
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="strategy-drawdown">最大回撤 (%)</Label>
                <Input
                  id="strategy-drawdown"
                  type="number"
                  min="0"
                  step="0.01"
                  value={formState.max_drawdown}
                  onChange={(event) => updateField("max_drawdown", event.target.value)}
                  placeholder="12.00"
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="strategy-win-rate">胜率 (%)</Label>
                <Input
                  id="strategy-win-rate"
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  value={formState.win_rate}
                  onChange={(event) => updateField("win_rate", event.target.value)}
                  placeholder="63.00"
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="strategy-monthly-price">月费 (USDT)</Label>
                <Input
                  id="strategy-monthly-price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={formState.monthly_price}
                  onChange={(event) => updateField("monthly_price", event.target.value)}
                  placeholder="39.99"
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="strategy-yearly-price">年费 (USDT)</Label>
                <Input
                  id="strategy-yearly-price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={formState.yearly_price}
                  onChange={(event) => updateField("yearly_price", event.target.value)}
                  placeholder="399.00"
                  required
                />
              </div>

              {editingStrategy && (
                <div className="grid gap-2">
                  <Label>当前状态</Label>
                  <Select
                    value={formState.status}
                    onValueChange={(value: StrategyStatus) => updateField("status", value)}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="请选择状态" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">已上架</SelectItem>
                      <SelectItem value="inactive">已下架</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="strategy-description">策略描述</Label>
              <Textarea
                id="strategy-description"
                value={formState.description}
                onChange={(event) => updateField("description", event.target.value)}
                placeholder="写一段用户在策略大厅里会看到的策略简介。"
                className="min-h-28"
              />
            </div>

            {formError && <p className="text-sm text-destructive">{formError}</p>}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => handleDialogOpenChange(false)}>
                取消
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "保存中..." : editingStrategy ? "保存修改" : "创建策略"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
