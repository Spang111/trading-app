import Link from "next/link"

const sections = [
  {
    title: "我们收集的信息",
    content:
      "当你注册、登录、订阅策略、绑定交易所 API 或联系客服时，我们可能会收集你的用户名、邮箱地址、钱包地址、支付记录、订阅信息以及你主动填写的交易所连接信息。",
  },
  {
    title: "信息的使用方式",
    content:
      "这些信息主要用于提供账号登录、邮箱验证、找回密码、策略订阅、支付核验、交易所连接配置以及安全审计等服务。我们也会将必要的系统日志用于故障排查和风控分析。",
  },
  {
    title: "交易所 API 与敏感信息",
    content:
      "你提交的交易所 API 信息仅用于完成你授权的策略执行与连接验证。我们会尽量采取加密和最小权限原则存储此类信息，但仍建议你只开启必要权限，并定期轮换密钥。",
  },
  {
    title: "信息共享与披露",
    content:
      "除法律法规要求、保护平台与用户安全，或完成支付、邮件发送、基础云服务等必要处理外，我们不会将你的个人信息出售给第三方。",
  },
  {
    title: "数据保存与安全",
    content:
      "我们会在业务所需期限内保存必要数据，并采用合理的技术与管理措施保护你的账户和数据安全。但任何互联网传输都无法保证绝对安全，请你妥善保管密码、邮箱和 API 密钥。",
  },
  {
    title: "你的权利",
    content:
      "你可以申请更新账户资料、删除不再使用的交易所连接信息，或停止继续使用本服务。若涉及法律、审计或安全要求，部分数据可能需要在规定期限内保留。",
  },
  {
    title: "政策更新",
    content:
      "我们可能会根据业务变化、产品迭代或法律要求更新本隐私政策。若有重大变化，我们会通过站内公告、邮件或其他合理方式提示你。",
  },
]

export default function PrivacyPolicyPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-10 flex flex-col gap-4 border-b border-border/50 pb-8 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.28em] text-primary/80">Privacy Policy</p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight">隐私政策</h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">
              本页面说明 AI Trading 在提供账户、订阅、支付、策略服务及交易所连接时，如何收集、使用与保护你的信息。
            </p>
          </div>

          <Link
            href="/"
            className="inline-flex w-fit items-center rounded-full border border-border/60 px-4 py-2 text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
          >
            返回首页
          </Link>
        </div>

        <div className="space-y-6">
          {sections.map((section) => (
            <section key={section.title} className="rounded-3xl border border-border/50 bg-secondary/10 p-6 sm:p-8">
              <h2 className="text-xl font-semibold">{section.title}</h2>
              <p className="mt-3 text-sm leading-7 text-muted-foreground sm:text-base">{section.content}</p>
            </section>
          ))}
        </div>

        <p className="mt-8 text-xs leading-6 text-muted-foreground">
          提示：当前内容为网站上线可用的基础版政策文本。若你准备正式对外运营，建议结合所在地区法规、支付方式和业务模式做进一步法律审阅。
        </p>
      </div>
    </main>
  )
}
