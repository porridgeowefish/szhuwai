import { useMemo, useState, type ReactNode } from 'react';
import {
  AlertTriangle,
  BrainCircuit,
  Check,
  CloudSun,
  ExternalLink,
  HelpCircle,
  KeyRound,
  MapPin,
  RotateCcw,
  Search,
  ShieldCheck,
} from 'lucide-react';
import {
  defaultRuntimeConfig,
  loadRuntimeConfig,
  saveRuntimeConfig,
  type RuntimeAPIConfig,
} from '../lib/runtimeConfig';

export default function AISettingsPage() {
  const [config, setConfig] = useState<RuntimeAPIConfig>(() => loadRuntimeConfig());
  const [saved, setSaved] = useState(false);

  const readyCount = useMemo(
    () => [
      config.map_api_key,
      config.weather_api_key,
      config.search_api_key,
      config.llm_api_key,
    ].filter(Boolean).length,
    [config],
  );

  const update = <K extends keyof RuntimeAPIConfig>(key: K, value: RuntimeAPIConfig[K]) => {
    setSaved(false);
    setConfig((current) => ({ ...current, [key]: value }));
  };

  const handleSave = () => {
    saveRuntimeConfig(config);
    setSaved(true);
  };

  const handleReset = () => {
    setConfig(defaultRuntimeConfig);
    saveRuntimeConfig(defaultRuntimeConfig);
    setSaved(true);
  };

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
        <div>
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-[var(--primary)]">
            <KeyRound size={17} />
            API 配置与答疑
          </div>
          <h1 className="max-w-2xl text-3xl font-bold tracking-[-0.03em] sm:text-4xl">把增强能力配清楚，失败时也知道为什么</h1>
          <p className="mt-4 max-w-3xl leading-7 text-[var(--muted)]">
            Key 只保存在当前浏览器 localStorage。生成策划时会随请求发送给本项目后端代理调用，后端不会写入文件或数据库。
            没配置的能力会明确降级，主流程仍会先返回轨迹分析和安全策划。
          </p>
        </div>

        <aside className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold">增强能力</div>
              <div className="mt-1 text-xs text-[var(--muted)]">已配置 {readyCount}/4 项</div>
            </div>
            <span className="rounded-full bg-[var(--canvas)] px-3 py-1 text-xs font-bold text-[var(--primary)]">
              本机浏览器
            </span>
          </div>
          <div className="mt-4 space-y-2">
            <StatusLine label="高德地图" ready={Boolean(config.map_api_key)} />
            <StatusLine label="和风天气" ready={Boolean(config.weather_api_key)} />
            <StatusLine label="网络搜索" ready={Boolean(config.search_api_key)} />
            <StatusLine label="AI 摘要" ready={Boolean(config.llm_api_key)} />
          </div>
        </aside>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
        <div className="space-y-5 rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-7">
          <ConfigSection
            icon={<MapPin size={18} />}
            title="地图与位置"
            status={config.map_api_key ? '已启用' : '未配置会跳过交通、救援点、地址反查'}
            description="用于浏览器定位后的地址反查、出发地解析、驾车/公交方案、周边救援点和景观线索。"
            links={[{ label: '高德开发控制台', href: 'https://console.amap.com/dev/index' }]}
          >
            <Field label="高德地图 Web 服务 Key" type="password" value={config.map_api_key} onChange={(value) => update('map_api_key', value)} />
          </ConfigSection>

          <ConfigSection
            icon={<CloudSun size={18} />}
            title="天气"
            status={config.weather_api_key ? '已启用' : '未配置会跳过真实天气'}
            description="用于出行日天气、风力、降水、体感、风寒和关键海拔点估算。"
            links={[{ label: '和风天气控制台', href: 'https://console.qweather.com/setting?lang=zh' }]}
          >
            <Field label="和风天气 API Key" type="password" value={config.weather_api_key} onChange={(value) => update('weather_api_key', value)} />
            <Field label="和风天气 Host" value={config.weather_developer_host} onChange={(value) => update('weather_developer_host', value)} />
          </ConfigSection>

          <ConfigSection
            icon={<Search size={18} />}
            title="网络搜索"
            status={config.search_api_key ? '已启用' : '未配置会跳过网络洞察'}
            description="用于搜索百度、抖音、B 站、小红书等平台线索，并交给 AI 汇总成可读攻略。"
            links={[{ label: 'Tavily', href: 'https://www.tavily.com/' }]}
          >
            <Field label="Tavily API Key" type="password" value={config.search_api_key} onChange={(value) => update('search_api_key', value)} />
          </ConfigSection>

          <ConfigSection
            icon={<BrainCircuit size={18} />}
            title="AI 摘要"
            status={config.llm_api_key ? '已启用' : '未配置时只展示结构化结果'}
            description="用于网络搜索结果、沿途风光、电话信息和攻略文本的提炼。"
            links={[
              { label: 'DeepSeek', href: 'https://www.deepseek.com/' },
              { label: 'SiliconFlow 模型', href: 'https://cloud.siliconflow.cn/me/models' },
              { label: 'OhMyGPT APIs', href: 'https://www.ohmygpt.com/apis' },
            ]}
          >
            <Field label="API Key" type="password" value={config.llm_api_key} onChange={(value) => update('llm_api_key', value)} />
            <Field label="Base URL" value={config.llm_base_url} onChange={(value) => update('llm_base_url', value)} />
            <Field label="模型名称" value={config.llm_model} onChange={(value) => update('llm_model', value)} />
          </ConfigSection>

          <div className="flex flex-col gap-3 border-t border-[var(--border)] pt-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2 text-sm text-[var(--muted)]">
              <ShieldCheck size={17} className="text-[var(--success)]" />
              保存前会自动去除首尾空格和换行
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={handleReset} className="secondary-button">
                <RotateCcw size={17} />
                恢复默认
              </button>
              <button type="button" onClick={handleSave} className="primary-button">
                {saved ? <Check size={17} /> : null}
                {saved ? '已保存到本浏览器' : '保存配置'}
              </button>
            </div>
          </div>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-24">
          <GuideCard
            icon={<HelpCircle size={18} />}
            title="定位为什么会失败？"
            items={[
              '浏览器定位只在 HTTPS 或 localhost 环境可用。',
              '拒绝定位权限后，需要在浏览器地址栏权限里重新允许。',
              '没有高德 Key 时，系统只能填入经纬度，不能自动反查地址。',
              '高德 Key 要选择 Web 服务类型，复制后不要带空格或换行。',
            ]}
          />
          <GuideCard
            icon={<AlertTriangle size={18} />}
            title="生成结果降级怎么看？"
            items={[
              '缺天气 Key：不展示真实天气，只保留轨迹和安全基础判断。',
              '缺高德 Key：不展示交通、救援点和景观线索。',
              '缺搜索或 AI Key：不编造攻略，只展示已有结构化内容。',
              '每次生成后的运行回执会标出成功、跳过或失败的模块。',
            ]}
          />
          <GuideCard
            icon={<KeyRound size={18} />}
            title="推荐最小配置"
            items={[
              '只验收轨迹：无需任何 Key。',
              '验收交通和定位：至少配置高德地图 Web 服务 Key。',
              '验收天气：配置和风天气 Key，Host 保持 devapi 即可。',
              '验收攻略摘要：配置 Tavily Key 和大模型 Key。',
            ]}
          />
        </aside>
      </section>
    </main>
  );
}

function StatusLine({ label, ready }: { label: string; ready: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--canvas)] px-3 py-2 text-sm">
      <span>{label}</span>
      <span className={ready ? 'font-semibold text-[var(--success)]' : 'font-semibold text-[var(--warning)]'}>
        {ready ? '已配置' : '会降级'}
      </span>
    </div>
  );
}

function ConfigSection({
  icon,
  title,
  status,
  description,
  children,
  links = [],
}: {
  icon: ReactNode;
  title: string;
  status: string;
  description: string;
  children: ReactNode;
  links?: Array<{ label: string; href: string }>;
}) {
  return (
    <section className="border-b border-[var(--border)] pb-5 last:border-0">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[var(--primary)]">{icon}</span>
            <h2 className="font-semibold">{title}</h2>
          </div>
          <p className="mt-1 text-sm leading-6 text-[var(--muted)]">{description}</p>
          <p className="mt-1 text-xs font-semibold text-[var(--warning)]">{status}</p>
        </div>
        {links.length > 0 ? (
          <div className="flex shrink-0 flex-wrap gap-2">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                target="_blank"
                rel="noreferrer"
                className="inline-flex min-h-8 items-center gap-1 rounded-lg border border-[var(--border)] px-2.5 text-xs font-semibold text-[var(--primary)] hover:bg-[var(--canvas)]"
              >
                {link.label}
                <ExternalLink size={13} />
              </a>
            ))}
          </div>
        ) : null}
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">{children}</div>
    </section>
  );
}

function GuideCard({ icon, title, items }: { icon: ReactNode; title: string; items: string[] }) {
  return (
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5">
      <div className="flex items-center gap-2 font-semibold">
        <span className="text-[var(--primary)]">{icon}</span>
        {title}
      </div>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-[var(--muted)]">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--primary)]" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="grid gap-2 text-sm font-semibold">
      {label}
      <input className="field font-normal" type={type} value={value} onChange={(event) => onChange(event.target.value)} autoComplete="off" />
    </label>
  );
}
