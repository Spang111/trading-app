"use client"

import {
  KeyRound,
  Link2,
  Webhook,
  PlayCircle,
  ShieldCheck,
  BookOpen,
} from "lucide-react"
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion"

const steps = [
  {
    step: 1,
    icon: KeyRound,
    title: "获取交易所 API 密钥",
    desc: "登录 OKX 或 Binance，在「API 管理」中创建新的 API Key。务必开启「交易权限」并设置 IP 白名单。",
    details: [
      "进入交易所账户设置 > API 管理",
      "点击「创建 API」，设置备注名称",
      "权限勾选：交易（必选）、读取（必选）",
      "绑定 IP 白名单：填入 AI Trading 服务器 IP",
      "保存 API Key、Secret Key 和 Passphrase",
    ],
  },
  {
    step: 2,
    icon: Link2,
    title: "在 AI Trading 绑定 API",
    desc: "进入控制台，选择对应交易所，粘贴 API Key、Secret 和 Passphrase 完成绑定。",
    details: [
      "进入「我的控制台」> 交易所管理",
      "选择交易所：OKX / Binance",
      "粘贴 API Key 和 Secret Key",
      "如为 OKX，还需填写 Passphrase",
      "点击「验证连接」确认绑定成功",
    ],
  },
  {
    step: 3,
    icon: Webhook,
    title: "配置 TradingView Webhook",
    desc: "在 TradingView 警报中添加 Webhook URL，并将 JSON Payload 粘贴到消息体中。",
    details: [
      "在 TradingView 创建新的警报（Alert）",
      "在「通知」选项卡中勾选 Webhook URL",
      "粘贴 AI Trading 提供的 Webhook 地址",
      "在「消息」栏粘贴 JSON Payload 模板",
      "设置触发条件并保存警报",
    ],
  },
  {
    step: 4,
    icon: PlayCircle,
    title: "发送测试信号",
    desc: "回到 AI Trading 控制台，点击「发送测试信号」按钮，验证整个链路是否正常工作。",
    details: [
      "进入「我的控制台」",
      "点击「发送测试信号」",
      "检查信号日志中是否出现测试记录",
      "在交易所确认是否产生测试订单（小额）",
      "如一切正常，即可启用正式策略",
    ],
  },
]

const faqs = [
  {
    q: "支持哪些交易所？",
    a: "目前支持 OKX 和 Binance 两大主流交易所，后续将陆续接入 Bybit、Bitget 等平台。所有交易所均通过官方 API 接入，确保安全可靠。",
  },
  {
    q: "API 密钥安全吗？",
    a: "所有 API 密钥均采用 AES-256 加密存储，传输过程使用 TLS 1.3 加密。平台不具备提币权限，您的资金始终在交易所账户中，完全由您掌控。",
  },
  {
    q: "订阅后多久可以开始交易？",
    a: "完成 API 绑定和 Webhook 配置后，策略即刻生效。通常整个过程仅需 10-15 分钟。首次使用建议先发送测试信号确认链路正常。",
  },
  {
    q: "如何取消订阅？",
    a: "您可以在控制台的「订阅管理」中随时取消订阅。取消后策略将在当前周期结束后停止运行，已支付的费用不予退还。",
  },
  {
    q: "策略的历史回测数据可信吗？",
    a: "所有策略回测均基于真实历史 K 线数据，包含手续费和滑点计算。同时我们提供实盘运行数据作为参考，回测与实盘数据均公开透明。",
  },
  {
    q: "支持自定义策略参数吗？",
    a: "专业版及以上套餐支持自定义策略参数，包括仓位大小、杠杆倍数、止盈止损比例等。您也可以通过 Webhook 自行传入自定义参数。",
  },
]

export function DocsView() {
  return (
    <div className="flex flex-col">
      {/* Header */}
      <section className="pt-8 pb-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 rounded-full border border-primary/20 bg-primary/5 text-primary text-sm font-medium">
            <BookOpen className="h-3.5 w-3.5" />
            <span>快速上手指南</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground text-balance">
            接入指南
          </h1>
          <p className="mt-4 max-w-xl mx-auto text-muted-foreground text-lg leading-relaxed">
            只需四步，即可将 AI Trading 与您的交易所账户连接并开始自动交易。
          </p>
        </div>
      </section>

      {/* Steps */}
      <section className="pb-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-6 top-6 bottom-6 w-px bg-gradient-to-b from-primary/40 via-accent/40 to-transparent hidden sm:block" />

            <div className="flex flex-col gap-8">
              {steps.map((s, i) => (
                <div key={s.step} className="relative flex gap-5 sm:gap-6">
                  {/* Step number circle */}
                  <div
                    className={`relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${
                      i % 2 === 0
                        ? "bg-primary/10 text-primary neon-glow-cyan"
                        : "bg-accent/10 text-accent neon-glow-purple"
                    }`}
                  >
                    <s.icon className="h-5 w-5" />
                  </div>

                  {/* Content */}
                  <div className="glass-panel rounded-2xl p-6 flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                        {"第 " + s.step + " 步"}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-foreground">{s.title}</h3>
                    <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{s.desc}</p>
                    <ul className="mt-4 flex flex-col gap-2">
                      {s.details.map((d, j) => (
                        <li key={j} className="flex items-start gap-2.5 text-sm text-foreground/70">
                          <ShieldCheck className="h-4 w-4 shrink-0 text-primary/60 mt-0.5" />
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="pb-24">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl sm:text-3xl font-bold text-foreground text-center mb-10">
            常见问题
          </h2>
          <div className="glass-panel rounded-2xl p-6">
            <Accordion type="single" collapsible className="w-full">
              {faqs.map((faq, i) => (
                <AccordionItem key={i} value={`faq-${i}`} className="border-border/50">
                  <AccordionTrigger className="text-foreground hover:no-underline text-left text-base">
                    {faq.q}
                  </AccordionTrigger>
                  <AccordionContent className="text-muted-foreground leading-relaxed">
                    {faq.a}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </div>
      </section>
    </div>
  )
}
