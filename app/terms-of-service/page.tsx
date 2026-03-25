import Link from "next/link"

const sections = [
  {
    title: "服务说明",
    content:
      "AI Trading 提供策略展示、订阅、支付核验、交易所连接配置、交易信号展示及相关辅助功能。平台展示的信息仅供你根据自身情况判断是否使用。",
  },
  {
    title: "账户与使用资格",
    content:
      "你需要使用真实、有效且可访问的邮箱注册账户，并妥善保管登录密码、邮箱及相关验证信息。你对自己账户下发生的操作承担责任。",
  },
  {
    title: "风险提示",
    content:
      "数字资产交易具有高波动、高风险特征，任何历史收益、回测数据、胜率或年化指标都不构成未来收益承诺。你应独立承担使用策略、连接交易所或执行交易所带来的风险。",
  },
  {
    title: "支付与订阅",
    content:
      "用户创建订单并完成支付后，订阅是否生效以平台核验结果为准。若你提交了无效支付信息、错误链路或与订单不匹配的交易哈希，平台有权拒绝该笔订阅申请。",
  },
  {
    title: "禁止行为",
    content:
      "你不得利用本服务从事违法违规活动，不得恶意攻击、绕过鉴权、批量爬取平台数据、伪造支付凭证、盗用他人账户或滥用交易所接口权限。",
  },
  {
    title: "服务可用性",
    content:
      "我们会尽力保持服务稳定，但不保证服务持续不中断，也不保证第三方依赖（如邮件服务、云服务、交易所 API）始终可用。系统维护、网络波动或第三方异常都可能影响服务体验。",
  },
  {
    title: "责任限制",
    content:
      "在法律允许范围内，平台对因市场波动、第三方服务异常、用户配置错误、账户信息泄露、交易所限制或不可抗力导致的损失，不承担超出已收取服务费用范围之外的责任。",
  },
  {
    title: "条款更新",
    content:
      "我们可能根据产品迭代、合规要求或业务变化更新本服务条款。更新后的条款公布后继续使用本服务，视为你已阅读并接受最新版本。",
  },
]

export default function TermsOfServicePage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-10 flex flex-col gap-4 border-b border-border/50 pb-8 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.28em] text-primary/80">Terms of Service</p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight">服务条款</h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">
              本页面说明你在使用 AI Trading 的账户、策略、支付、订阅及相关功能时，需要共同遵守的基础规则与风险边界。
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
          提示：当前内容为网站上线可用的基础版条款文本。若你准备正式商业化运营，建议结合支付、会员、风险披露和所在地区合规要求进一步完善。
        </p>
      </div>
    </main>
  )
}
