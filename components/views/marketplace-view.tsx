"use client"

import { useEffect, useState } from "react"
import {
  BarChart3,
  ClipboardCheck,
  QrCode,
  ShieldCheck,
  Target,
  TrendingUp,
  Wallet,
  X,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AUTH_TOKEN_STORAGE_KEY } from "@/lib/auth"

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

type SubscriptionPlan = {
  id: string
  strategy_id: number
  plan_type: "monthly" | "yearly"
  price: string
  duration_days: number
  profit_share_percent: string
  description: string | null
  is_active: boolean
}

type PaymentOrder = {
  id: string
  user_id: number
  subscription_id: string | null
  amount: string
  payment_method: string
  tx_hash: string | null
  status: string
  created_at: string
  pay_address?: string | null
  payment_network?: string | null
  payment_note?: string | null
}

function formatPercent(value: string) {
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)}%` : value
}

function formatMonthlyPrice(value: string) {
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)} USDT / 月` : value
}

function formatPrice(value: string) {
  const amount = Number(value)
  return Number.isFinite(amount) ? `${amount.toFixed(2)} USDT` : value
}

function getTagLabel(strategy: Strategy) {
  if (strategy.tag && strategy.tag.trim()) {
    return strategy.tag.toUpperCase()
  }

  return strategy.status === "active" ? "运行中" : "新策略"
}

function getTagColor(strategy: Strategy) {
  return strategy.status === "active" ? "primary" : "accent"
}

function getPlanTypeLabel(planType: SubscriptionPlan["plan_type"]) {
  return planType === "monthly" ? "月付套餐" : "年付套餐"
}

function getPaymentStatusLabel(status: string) {
  switch (status) {
    case "pending":
      return "待支付 / 待审核"
    case "approved":
      return "已通过"
    case "rejected":
      return "已驳回"
    case "completed":
      return "已完成"
    default:
      return status
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

export function MarketplaceView() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [token, setToken] = useState<string | null>(null)
  const [plans, setPlans] = useState<SubscriptionPlan[]>([])
  const [plansLoading, setPlansLoading] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<string>("")
  const [paymentOrder, setPaymentOrder] = useState<PaymentOrder | null>(null)
  const [txHash, setTxHash] = useState("")
  const [paymentError, setPaymentError] = useState<string | null>(null)
  const [paymentSuccess, setPaymentSuccess] = useState<string | null>(null)
  const [isCreatingOrder, setIsCreatingOrder] = useState(false)
  const [isSubmittingTxHash, setIsSubmittingTxHash] = useState(false)

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
          throw new Error(`请求失败，状态码 ${response.status}`)
        }

        const data = (await response.json()) as Strategy[]
        setStrategies(Array.isArray(data) ? data : [])
      } catch (error) {
        if (controller.signal.aborted) {
          return
        }

        const message = error instanceof Error ? error.message : "暂时无法加载策略数据。"

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

  useEffect(() => {
    if (!modalOpen || !selectedStrategy) {
      return
    }

    let cancelled = false
    const strategyId = selectedStrategy.id
    const storedToken = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
    setToken(storedToken)

    async function loadPlans() {
      try {
        setPlansLoading(true)
        setPaymentError(null)
        setPaymentSuccess(null)
        setPaymentOrder(null)
        setTxHash("")

        const response = await fetch(`/api/strategies/${strategyId}/plans`, {
          cache: "no-store",
        })

        if (!response.ok) {
          throw new Error(await readResponseMessage(response))
        }

        const payload = (await response.json()) as SubscriptionPlan[]
        if (!cancelled) {
          setPlans(payload)
          setSelectedPlanId(payload[0]?.id ?? "")
        }
      } catch (error) {
        if (!cancelled) {
          setPlans([])
          setSelectedPlanId("")
          setPaymentError(error instanceof Error ? error.message : "无法加载套餐信息。")
        }
      } finally {
        if (!cancelled) {
          setPlansLoading(false)
        }
      }
    }

    void loadPlans()

    return () => {
      cancelled = true
    }
  }, [modalOpen, selectedStrategy])

  const openPayment = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setModalOpen(true)
  }

  const closePaymentModal = () => {
    setModalOpen(false)
    setSelectedStrategy(null)
    setPlans([])
    setSelectedPlanId("")
    setPaymentOrder(null)
    setPaymentError(null)
    setPaymentSuccess(null)
    setTxHash("")
  }

  const selectedPlan = plans.find((plan) => plan.id === selectedPlanId) ?? null

  const createPaymentOrder = async () => {
    const strategy = selectedStrategy

    if (!strategy) {
      return
    }

    if (!token) {
      setPaymentError("请先登录账号，再创建订阅订单。")
      return
    }

    if (!selectedPlan) {
      setPaymentError("请先选择一个订阅套餐。")
      return
    }

    setIsCreatingOrder(true)
    setPaymentError(null)
    setPaymentSuccess(null)

    try {
      const response = await fetch("/api/payments/create", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          strategy_id: strategy.id,
          plan_type: selectedPlan.plan_type,
        }),
      })

      if (!response.ok) {
        throw new Error(await readResponseMessage(response))
      }

      const payload = (await response.json()) as PaymentOrder
      setPaymentOrder(payload)
      setPaymentSuccess("订单已创建。完成转账后，请把 TxHash 粘贴到下方提交审核。")
    } catch (error) {
      setPaymentError(error instanceof Error ? error.message : "暂时无法创建支付订单。")
    } finally {
      setIsCreatingOrder(false)
    }
  }

  const submitTxHash = async () => {
    if (!token) {
      setPaymentError("当前登录状态已失效，请重新登录。")
      return
    }

    if (!paymentOrder) {
      setPaymentError("请先创建支付订单。")
      return
    }

    if (!txHash.trim()) {
      setPaymentError("请先填写链上转账的 TxHash。")
      return
    }

    setIsSubmittingTxHash(true)
    setPaymentError(null)
    setPaymentSuccess(null)

    try {
      const response = await fetch(`/api/payments/verify?payment_id=${paymentOrder.id}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tx_hash: txHash.trim(),
        }),
      })

      if (!response.ok) {
        throw new Error(await readResponseMessage(response))
      }

      const payload = (await response.json()) as { message?: string }
      setPaymentSuccess(payload.message || "TxHash 提交成功，正在等待管理员审核。")
    } catch (error) {
      setPaymentError(error instanceof Error ? error.message : "暂时无法提交 TxHash。")
    } finally {
      setIsSubmittingTxHash(false)
    }
  }

  return (
    <div className="flex flex-col">
      <section className="pb-12 pt-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-4 py-1.5 text-sm font-medium text-accent">
              <BarChart3 className="h-3.5 w-3.5" />
              <span>{isLoading ? "正在同步实时策略..." : `当前在线策略 ${strategies.length} 个`}</span>
            </div>

            <h1 className="text-3xl font-bold text-balance text-foreground sm:text-4xl lg:text-5xl">
              策略大厅
            </h1>

            <p className="mt-6 text-sm text-muted-foreground">
              {isLoading
                ? "正在连接后端..."
                : loadError
                  ? `云端同步失败：${loadError}`
                  : "云端同步已开启。"}
            </p>
          </div>
        </div>
      </section>

      <section className="pb-40 md:pb-52">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {loadError && (
            <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">
              <p>从后端加载真实策略失败。</p>
              <button
                onClick={() => setRefreshKey((current) => current + 1)}
                className="mt-3 rounded-lg border border-red-400/30 px-3 py-1.5 text-xs font-medium text-red-50 transition-colors hover:bg-red-500/10"
              >
                重新加载
              </button>
            </div>
          )}

          {!isLoading && !loadError && strategies.length === 0 && (
            <div className="mb-6 rounded-2xl border border-border/50 bg-secondary/20 p-4 text-sm text-muted-foreground">
              后端已成功响应，但当前还没有可展示的策略。
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
                    {strategy.description || "该策略暂未发布详细说明。"}
                  </p>

                  <div className="mb-6 grid grid-cols-3 gap-4">
                    <div className="flex flex-col items-center rounded-xl bg-secondary/30 p-3">
                      <TrendingUp className="mb-1.5 h-4 w-4 text-emerald-400" />
                      <span className="text-xs text-muted-foreground">年化收益</span>
                      <span className="text-sm font-bold text-emerald-400">
                        {formatPercent(strategy.apy)}
                      </span>
                    </div>

                    <div className="flex flex-col items-center rounded-xl bg-secondary/30 p-3">
                      <Target className="mb-1.5 h-4 w-4 text-red-400" />
                      <span className="text-xs text-muted-foreground">最大回撤</span>
                      <span className="text-sm font-bold text-red-400">
                        {formatPercent(strategy.max_drawdown)}
                      </span>
                    </div>

                    <div className="flex flex-col items-center rounded-xl bg-secondary/30 p-3">
                      <BarChart3 className="mb-1.5 h-4 w-4 text-primary" />
                      <span className="text-xs text-muted-foreground">胜率</span>
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
                    onClick={() => openPayment(strategy)}
                    className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-all duration-300 hover:scale-[1.03] hover:shadow-[0_0_20px_rgba(0,229,255,0.3)] active:scale-[0.97]"
                  >
                    <Wallet className="h-4 w-4" />
                    立即订阅
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {modalOpen && selectedStrategy && (
        <div className="fixed inset-0 z-50 overflow-y-auto overscroll-contain">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={closePaymentModal} />

          <div className="relative flex min-h-screen items-center justify-center px-4 py-8 sm:px-6 sm:py-12">
            <div className="relative w-full max-w-lg max-h-[calc(100vh-6rem)] overflow-y-auto overscroll-contain animate-in zoom-in-95 rounded-2xl p-8 duration-200 glass-panel neon-glow-cyan fade-in sm:max-h-[calc(100vh-8rem)]">
            <button
              onClick={closePaymentModal}
              className="absolute right-4 top-4 rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="关闭订阅弹窗"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="text-center">
              <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 neon-glow-cyan">
                <Wallet className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-xl font-bold text-foreground">订阅策略</h3>
              <p className="mt-2 text-sm text-muted-foreground">{selectedStrategy.name}</p>
            </div>

            <div className="mt-6 grid gap-5">
              {!token && (
                <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-100">
                  请先登录账号，再创建订阅订单。
                </div>
              )}

              <div className="grid gap-2">
                <Label>选择套餐</Label>
                <Select
                  value={selectedPlanId}
                  onValueChange={setSelectedPlanId}
                  disabled={plansLoading || plans.length === 0}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={plansLoading ? "正在加载套餐..." : "请选择套餐"} />
                  </SelectTrigger>
                  <SelectContent>
                    {plans.map((plan) => (
                      <SelectItem key={plan.id} value={plan.id}>
                        {getPlanTypeLabel(plan.plan_type)} · {formatPrice(plan.price)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedPlan && (
                  <p className="text-xs leading-6 text-muted-foreground">
                    {selectedPlan.plan_type === "monthly" ? "30 天订阅" : "365 天订阅"}，
                    当前价格 {formatPrice(selectedPlan.price)}，
                    分润比例 {formatPercent(selectedPlan.profit_share_percent)}。
                  </p>
                )}
              </div>

              <Button
                onClick={() => void createPaymentOrder()}
                disabled={!token || !selectedPlan || isCreatingOrder}
              >
                {isCreatingOrder ? "创建订单中..." : "创建支付订单"}
              </Button>

              {paymentOrder && (
                <div className="grid gap-4 rounded-2xl border border-border/50 bg-secondary/20 p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">订单号</p>
                      <p className="text-xs text-muted-foreground">{paymentOrder.id}</p>
                    </div>
                    <Badge className="border-primary/20 bg-primary/10 text-primary">
                      {getPaymentStatusLabel(paymentOrder.status)}
                    </Badge>
                  </div>

                  <div className="grid gap-3 rounded-xl border border-border/40 bg-background/40 p-4">
                    <div className="flex h-32 items-center justify-center rounded-xl border border-border/40 bg-foreground/5">
                      <QrCode className="h-16 w-16 text-muted-foreground/40" />
                    </div>

                    <div className="grid gap-1 text-sm">
                      <p className="text-muted-foreground">付款金额</p>
                      <p className="font-semibold text-foreground">{formatPrice(paymentOrder.amount)}</p>
                    </div>

                    <div className="grid gap-1 text-sm">
                      <p className="text-muted-foreground">付款网络</p>
                      <p className="font-medium text-foreground">
                        {paymentOrder.payment_network || "管理员尚未配置付款网络。"}
                      </p>
                    </div>

                    <div className="grid gap-1 text-sm">
                      <p className="text-muted-foreground">收款地址</p>
                      <p className="break-all font-mono text-foreground">
                        {paymentOrder.pay_address || "管理员尚未配置收款地址，请先到后台补充。"}
                      </p>
                    </div>

                    {paymentOrder.payment_note && (
                      <div className="grid gap-1 text-sm">
                        <p className="text-muted-foreground">付款说明</p>
                        <p className="text-xs leading-6 text-muted-foreground">{paymentOrder.payment_note}</p>
                      </div>
                    )}
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="payment-tx-hash">交易哈希（TxHash）</Label>
                    <Input
                      id="payment-tx-hash"
                      value={txHash}
                      onChange={(event) => setTxHash(event.target.value)}
                      placeholder="转账完成后，把链上 TxHash 粘贴到这里"
                    />
                  </div>

                  <Button
                    variant="outline"
                    onClick={() => void submitTxHash()}
                    disabled={isSubmittingTxHash}
                  >
                    <ClipboardCheck className="h-4 w-4" />
                    {isSubmittingTxHash ? "提交中..." : "提交 TxHash 等待审核"}
                  </Button>
                </div>
              )}

              {paymentError && (
                <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">
                  {paymentError}
                </div>
              )}

              {paymentSuccess && (
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">
                  {paymentSuccess}
                </div>
              )}

              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>订单创建和 TxHash 提交都已接入真实后端，管理员审核通过后订阅才会正式生效。</span>
              </div>
            </div>
          </div>
          </div>
        </div>
      )}
    </div>
  )
}
