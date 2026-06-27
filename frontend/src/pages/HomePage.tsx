import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import {
  CalendarDays,
  Car,
  Check,
  CheckCircle2,
  Circle,
  CloudSun,
  BrainCircuit,
  Link2,
  LoaderCircle,
  LocateFixed,
  MapPin,
  Monitor,
  Route,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import {
  planAPI,
  type PlanningRunReport,
  type TrackAnalysis,
  type TwoBuluSessionState,
  type TwoBuluSessionStatus,
  type TwoBuluTrackInfo,
} from '../lib/api/plan';
import { loadRuntimeConfig } from '../lib/runtimeConfig';

const exampleUrl = 'https://www.2bulu.com/track/t-PFdvTj7brIjp%25252FR2KBg5Tzw%25253D%25253D.htm#';
const terminalStates: TwoBuluSessionState[] = ['ready', 'failed'];
const runHistoryKey = 'planning-run-history';

export default function HomePage() {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [tripDate, setTripDate] = useState('');
  const [departurePoint, setDeparturePoint] = useState('');
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [trackInfo, setTrackInfo] = useState<TwoBuluTrackInfo | null>(null);
  const [session, setSession] = useState<TwoBuluSessionStatus | null>(null);
  const [trackAnalysis, setTrackAnalysis] = useState<TrackAnalysis | null>(null);
  const [runReport, setRunReport] = useState<PlanningRunReport | null>(null);
  const [action, setAction] = useState<'idle' | 'starting' | 'generating' | 'locating'>('idle');
  const [error, setError] = useState('');
  const pollSeqRef = useRef(0);

  const config = useMemo(() => loadRuntimeConfig(), []);
  const authorizationReady = session?.state === 'ready';
  const departurePointText = toText(departurePoint);

  useEffect(() => {
    if (!session || terminalStates.includes(session.state)) return;
    const timer = window.setInterval(() => {
      const mySeq = ++pollSeqRef.current;
      void planAPI.getTwoBuluSession(session.session_id)
        .then((next) => {
          // 过时响应直接丢弃，避免慢请求的旧状态覆盖新状态（如已 ready 被回退成 waiting_login）
          if (mySeq !== pollSeqRef.current) return;
          setSession(next);
          if (next.state === 'failed') setError(next.message);
        })
        .catch((caught: unknown) => {
          if (mySeq !== pollSeqRef.current) return;
          setError(readError(caught, '无法读取授权进度'));
        });
    }, 1500);
    return () => window.clearInterval(timer);
  }, [session]);

  const startAuthorization = async () => {
    setAction('starting');
    setError('');
    setSession(null);
    setTrackAnalysis(null);
    setRunReport(null);
    try {
      const normalizedUrl = url.trim();
      const info = await planAPI.inspect(normalizedUrl);
      setTrackInfo(info);
      setSession(await planAPI.createTwoBuluSession(normalizedUrl));
    } catch (caught) {
      setError(readError(caught, '无法打开两步路授权窗口，请确认后端运行在本机桌面环境'));
    } finally {
      setAction('idle');
    }
  };

  const locate = async () => {
    setAction('locating');
    setError('');
    // 浏览器 getCurrentPosition 在桌面/无真实 GPS 环境下走浏览器自带的 IP 库，
    // 常出现跨城误差（如把深圳的出口 IP 定到辽宁）。出发地仅用于驾车/公交路线规划，
    // 城市级精度即可，故直接用后端高德 IP 定位（高德 IP 库对国内出口判断更稳）。
    try {
      const resolved = await planAPI.resolveLocation({ api_config: loadRuntimeConfig() });
      if (resolved.success && resolved.address) {
        setDeparturePoint(resolved.address);
      } else {
        setError(resolved.message || '定位不可用，请手动填写出发地点。');
      }
    } catch (caught) {
      setError(readError(caught, '定位不可用，请手动填写出发地点。'));
    } finally {
      setAction('idle');
    }
  };

  const generate = async () => {
    if (!session || session.state !== 'ready') {
      setError('请先完成两步路授权和轨迹下载');
      return;
    }
    setAction('generating');
    setError('');
    try {
      const result = await planAPI.generate({
        two_bulu_url: url.trim(),
        two_bulu_session_id: session.session_id,
        trip_date: tripDate || null,
        departure_point: departurePointText.trim() || null,
        additional_info: additionalInfo.trim(),
        api_config: loadRuntimeConfig(),
        generation_mode: 'fast',
      });
      setTrackAnalysis(result.track_analysis);
      setRunReport(result.run_report);
      saveRunReport(result.run_report);
      if (result.plan) {
        sessionStorage.setItem('latest-plan', JSON.stringify(result.plan));
        sessionStorage.setItem('latest-run-report', JSON.stringify(result.run_report));
        navigate('/result', { state: { plan: result.plan, runReport: result.run_report } });
      }
    } catch (caught) {
      setError(readError(caught, '轨迹分析失败，请重新授权后再试'));
    } finally {
      setAction('idle');
    }
  };

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-16">
      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start">
        <section>
          <p className="mb-3 text-sm font-semibold text-[var(--primary)]">从线路链接直接开始</p>
          <h1 className="max-w-3xl text-4xl font-bold leading-[1.08] tracking-[-0.04em] sm:text-5xl">
            不用再找轨迹文件。
            <br />
            粘贴两步路 URL 即可。
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--muted)] sm:text-lg">
            系统打开真实两步路页面，在你完成登录与验证后自动下载轨迹，再基于真实数据生成分析和行前策划。
          </p>

          <div className="mt-8 rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-7">
            <label className="grid gap-2 text-sm font-semibold">
              两步路线路 URL
              <div className="relative">
                <Link2 className="pointer-events-none absolute left-3.5 top-3.5 text-[var(--muted)]" size={19} />
                <input
                  className="field pl-11 pr-3"
                  value={url}
                  onChange={(event) => {
                    setUrl(event.target.value);
                    setTrackInfo(null);
                    setSession(null);
                    setTrackAnalysis(null);
                    setRunReport(null);
                    setError('');
                  }}
                  placeholder="https://www.2bulu.com/track/t-....htm"
                  inputMode="url"
                />
              </div>
            </label>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <button type="button" className="text-sm text-[var(--primary)] underline-offset-4 hover:underline" onClick={() => setUrl(exampleUrl)}>
                填入示例 URL
              </button>
              <button type="button" className="primary-button" disabled={!url.trim() || action !== 'idle' || Boolean(session && !terminalStates.includes(session.state))} onClick={() => void startAuthorization()}>
                {action === 'starting' ? <LoaderCircle className="animate-spin" size={18} /> : <Monitor size={18} />}
                {session?.state === 'failed' ? '重新打开授权窗口' : '打开授权窗口'}
              </button>
            </div>

            {trackInfo && session ? <AuthorizationPanel session={session} /> : null}

            <div className="my-6 border-t border-[var(--border)]" />
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="grid gap-2 text-sm font-semibold">
                <span className="flex items-center gap-2"><CalendarDays size={17} /> 出行日期 <em className="font-normal not-italic text-[var(--muted)]">可选</em></span>
                <input className="field" type="date" value={tripDate} onChange={(event) => setTripDate(event.target.value)} />
              </label>
              <label className="grid gap-2 text-sm font-semibold">
                <span className="flex items-center gap-2"><MapPin size={17} /> 出发地点 <em className="font-normal not-italic text-[var(--muted)]">可选</em></span>
                <div className="flex gap-2">
                  <input className="field min-w-0" value={departurePointText} onChange={(event) => setDeparturePoint(event.target.value)} placeholder="手动填写或使用定位" />
                  <button type="button" className="secondary-button shrink-0 px-3" onClick={locate} disabled={action === 'locating'} aria-label="使用当前位置">
                    {action === 'locating' ? <LoaderCircle className="animate-spin" size={18} /> : <LocateFixed size={18} />}
                  </button>
                </div>
              </label>
            </div>
            <label className="mt-4 grid gap-2 text-sm font-semibold">
              补充要求 <span className="font-normal text-[var(--muted)]">可选</span>
              <textarea className="field min-h-24 resize-y" value={additionalInfo} onChange={(event) => setAdditionalInfo(event.target.value)} placeholder="队伍经验、节奏、装备限制等" />
            </label>

            <OptionalCapabilityPanel
              tripDate={tripDate}
              departurePoint={departurePointText}
              weatherReady={Boolean(config.weather_api_key)}
              mapReady={Boolean(config.map_api_key)}
              llmReady={Boolean(config.llm_api_key)}
            />

            {error ? <div role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-[var(--danger)]">{error}</div> : null}

            <button type="button" className="primary-button mt-5 w-full" disabled={!authorizationReady || action !== 'idle'} onClick={() => void generate()}>
              {action === 'generating' ? <LoaderCircle className="animate-spin" size={19} /> : <CheckCircle2 size={19} />}
              {tripDate && departurePointText ? '生成极速策划' : '分析轨迹'}
            </button>
            <p className="mt-3 text-center text-xs leading-5 text-[var(--muted)]">
              日期、出发地、API Key 会启用可选增强；缺失时系统会明确降级，仍先返回轨迹与安全策划。
            </p>
          </div>

          {trackAnalysis ? <TrackSummary track={trackAnalysis} /> : null}
          {runReport ? <RunReportPanel report={runReport} /> : null}
        </section>

        <aside className="rounded-2xl border border-[var(--border)] bg-white p-5 lg:sticky lg:top-8">
          <h2 className="font-semibold">你只需要准备</h2>
          <ol className="mt-4 space-y-4 text-sm text-[var(--muted)]">
            <Step number="1" title="一条两步路 URL" body="系统负责识别线路并找到下载入口。" />
            <Step number="2" title="一次平台授权" body="在独立浏览器窗口扫码登录；如有验证码，由你手动完成。" />
            <Step number="3" title="可选的行程信息" body="日期和出发地用于查询真实天气与交通。" />
          </ol>
          <div className="mt-5 border-t border-[var(--border)] pt-5">
            <Link to="/settings" className="secondary-button w-full">
              <Settings size={17} />
              检查 API 配置
            </Link>
            <p className="mt-3 text-xs leading-5 text-[var(--muted)]">API Key 仅保存在当前浏览器，服务端不持久化。</p>
          </div>
        </aside>
      </div>
    </main>
  );
}

function AuthorizationPanel({ session }: { session: TwoBuluSessionStatus }) {
  const steps: Array<{ state: TwoBuluSessionState; label: string }> = [
    { state: 'waiting_login', label: '扫码登录' },
    { state: 'waiting_captcha', label: '人工验证' },
    { state: 'ready', label: '轨迹就绪' },
  ];
  const currentIndex = session.state === 'starting' ? -1 : steps.findIndex((step) => step.state === session.state);
  const isReady = session.state === 'ready';

  return (
    <div className="mt-5 rounded-xl border border-[var(--border)] bg-[var(--canvas)] p-4">
      <div className="flex items-start gap-3">
        <span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${isReady ? 'bg-green-100 text-[var(--success)]' : 'bg-white text-[var(--primary)]'}`}>
          {isReady ? <ShieldCheck size={20} /> : <LoaderCircle className={session.state === 'failed' ? '' : 'animate-spin'} size={20} />}
        </span>
        <div className="min-w-0">
          <p className="font-semibold">{isReady ? '轨迹已自动下载' : session.state === 'failed' ? '授权未完成' : '请在授权窗口完成操作'}</p>
          <p className="mt-1 text-sm leading-6 text-[var(--muted)]">{session.message}</p>
        </div>
      </div>
      <ol className="mt-4 grid grid-cols-3 gap-2 border-t border-[var(--border)] pt-4">
        {steps.map((step, index) => {
          const complete = isReady || index < currentIndex;
          const active = step.state === session.state || (session.state === 'downloading' && index === 1);
          return (
            <li key={step.state} className={`flex items-center gap-2 text-xs font-semibold ${complete || active ? 'text-[var(--primary)]' : 'text-[var(--muted)]'}`}>
              {complete ? <Check size={15} /> : active ? <LoaderCircle className="animate-spin" size={15} /> : <Circle size={15} />}
              {step.label}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function Step({ number, title, body }: { number: string; title: string; body: string }) {
  return (
    <li className="flex gap-3">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--canvas)] text-xs font-bold text-[var(--primary)]">{number}</span>
      <span><strong className="block font-semibold text-[var(--text)]">{title}</strong>{body}</span>
    </li>
  );
}

function OptionalCapabilityPanel({
  tripDate,
  departurePoint,
  weatherReady,
  mapReady,
  llmReady,
}: {
  tripDate: string;
  departurePoint: string;
  weatherReady: boolean;
  mapReady: boolean;
  llmReady: boolean;
}) {
  const departurePointText = toText(departurePoint);
  const items = [
    {
      icon: <CloudSun size={16} />,
      title: '天气增强',
      enabled: Boolean(tripDate && weatherReady),
      detail: tripDate ? (weatherReady ? '将查询真实天气' : '缺天气 API Key') : '缺出行日期',
    },
    {
      icon: <Car size={16} />,
      title: '交通与救援',
      enabled: Boolean(departurePointText.trim() && mapReady),
      detail: departurePointText.trim() ? (mapReady ? '将查询交通与周边救援点' : '缺高德地图 API Key') : '缺出发地点',
    },
    {
      icon: <BrainCircuit size={16} />,
      title: 'AI 摘要',
      enabled: false,
      detail: llmReady ? '已配置 Key，当前版本后置不阻塞' : '后置增强，当前不阻塞主流程',
    },
  ];

  return (
    <div className="mt-4 rounded-xl border border-[var(--border)] bg-[var(--canvas)] p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold">可选增强能力</h3>
        <span className="text-xs text-[var(--muted)]">缺失会自动降级</span>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        {items.map((item) => (
          <div key={item.title} className="rounded-lg border border-[var(--border)] bg-white px-3 py-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <span className={item.enabled ? 'text-[var(--success)]' : 'text-[var(--muted)]'}>{item.icon}</span>
              {item.title}
            </div>
            <div className="mt-1 flex items-center gap-2 text-xs">
              <span className={`h-2 w-2 rounded-full ${item.enabled ? 'bg-[var(--success)]' : 'bg-amber-500'}`} />
              <span className={item.enabled ? 'text-[var(--success)]' : 'text-[var(--warning)]'}>{item.enabled ? '启用' : '降级'}</span>
              <span className="text-[var(--muted)]">{item.detail}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function toText(value: unknown): string {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (value && typeof value === 'object') {
    const maybeAddress = value as { formatted_address?: unknown; address?: unknown; text?: unknown };
    if (typeof maybeAddress.formatted_address === 'string') return maybeAddress.formatted_address;
    if (typeof maybeAddress.address === 'string') return maybeAddress.address;
    if (typeof maybeAddress.text === 'string') return maybeAddress.text;
  }
  return '';
}

function TrackSummary({ track }: { track: TrackAnalysis }) {
  return (
    <section className="mt-6 rounded-2xl border border-[var(--border)] bg-white p-5">
      <h2 className="font-semibold">{track.trackName || track.track_name || '轨迹分析'}</h2>
      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Metric label="距离" value={`${track.totalDistanceKm.toFixed(1)} km`} />
        <Metric label="累计爬升" value={`${Math.round(track.totalAscentM)} m`} />
        <Metric label="预计时长" value={`${track.estimatedDurationHours.toFixed(1)} h`} />
        <Metric label="难度" value={track.difficultyLevel} />
      </dl>
    </section>
  );
}

function saveRunReport(report: PlanningRunReport) {
  try {
    const raw = localStorage.getItem(runHistoryKey);
    const history = raw ? JSON.parse(raw) as PlanningRunReport[] : [];
    const next = [report, ...history.filter((item) => item.run_id !== report.run_id)].slice(0, 20);
    localStorage.setItem(runHistoryKey, JSON.stringify(next));
  } catch {
    localStorage.setItem(runHistoryKey, JSON.stringify([report]));
  }
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-xs text-[var(--muted)]">{label}</dt><dd className="mt-1 font-semibold">{value}</dd></div>;
}

function RunReportPanel({ report }: { report: PlanningRunReport }) {
  const statusClass: Record<string, string> = {
    success: 'border-green-200 bg-green-50 text-[var(--success)]',
    degraded: 'border-amber-200 bg-amber-50 text-[var(--warning)]',
    skipped: 'border-zinc-200 bg-zinc-50 text-zinc-500',
    failed: 'border-red-200 bg-red-50 text-[var(--danger)]',
  };

  return (
    <section className="mt-6 rounded-2xl border border-[var(--border)] bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">运行回执</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">Run {report.run_id} · {report.total_duration_ms}ms</p>
        </div>
        <span className="rounded-full border border-[var(--border)] px-3 py-1 text-xs font-semibold text-[var(--muted)]">
          {report.strategy === 'fast' ? '极速稳定' : 'AI 增强'}
        </span>
      </div>
      <ol className="mt-4 grid gap-2 sm:grid-cols-2">
        {report.stages.map((stage) => (
          <li key={`${stage.stage}-${stage.title}`} className={`rounded-lg border px-3 py-2 text-xs ${statusClass[stage.status] || statusClass.skipped}`}>
            <div className="flex items-center justify-between gap-2 font-semibold">
              <span>{stage.title}</span>
              <span>{stage.duration_ms}ms</span>
            </div>
            {stage.message ? <p className="mt-1 leading-5 text-zinc-600">{stage.message}</p> : null}
          </li>
        ))}
      </ol>
      {report.warnings.length > 0 ? (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">
          {report.warnings.join('；')}
        </div>
      ) : null}
    </section>
  );
}

function readError(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail.message === 'string') return detail.message;
  }
  return error instanceof Error ? error.message : fallback;
}
