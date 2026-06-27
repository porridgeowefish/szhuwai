import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Clock3, Gauge, RotateCcw, Trash2 } from 'lucide-react';
import type { PlanningRunReport, PlanningStageLog } from '../lib/api/plan';

const runHistoryKey = 'planning-run-history';

export default function MonitorPage() {
  const [runs, setRuns] = useState<PlanningRunReport[]>(() => loadRuns());
  const [selectedRunId, setSelectedRunId] = useState(runs[0]?.run_id || '');
  const selectedRun = runs.find((run) => run.run_id === selectedRunId) || runs[0] || null;

  const summary = useMemo(() => {
    const total = runs.length;
    const degraded = runs.filter((run) => run.warnings.length > 0 || run.stages.some((stage) => stage.status !== 'success')).length;
    const avgMs = total > 0 ? Math.round(runs.reduce((sum, run) => sum + run.total_duration_ms, 0) / total) : 0;
    return { total, degraded, avgMs };
  }, [runs]);

  const refresh = () => {
    const next = loadRuns();
    setRuns(next);
    setSelectedRunId(next[0]?.run_id || '');
  };

  const clear = () => {
    localStorage.removeItem(runHistoryKey);
    setRuns([]);
    setSelectedRunId('');
  };

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-[var(--primary)]">Planning Run Monitor</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">运行监控</h1>
        </div>
        <div className="flex gap-2">
          <button type="button" className="secondary-button" onClick={refresh}>
            <RotateCcw size={16} />
            刷新
          </button>
          <button type="button" className="secondary-button" onClick={clear} disabled={runs.length === 0}>
            <Trash2 size={16} />
            清空
          </button>
        </div>
      </div>

      <section className="mt-6 grid gap-3 sm:grid-cols-3">
        <MetricCard icon={<Activity size={18} />} label="运行次数" value={String(summary.total)} />
        <MetricCard icon={<AlertTriangle size={18} />} label="降级次数" value={String(summary.degraded)} tone="warning" />
        <MetricCard icon={<Clock3 size={18} />} label="平均耗时" value={`${summary.avgMs}ms`} />
      </section>

      {runs.length === 0 ? (
        <section className="mt-6 rounded-2xl border border-dashed border-[var(--border)] bg-white p-8 text-center">
          <Gauge className="mx-auto text-[var(--muted)]" size={32} />
          <h2 className="mt-3 font-semibold">暂无运行记录</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">生成一次轨迹分析或策划后，这里会显示阶段耗时和降级原因。</p>
        </section>
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
          <section className="rounded-2xl border border-[var(--border)] bg-white p-3">
            <div className="px-2 pb-2 text-xs font-semibold text-[var(--muted)]">最近运行</div>
            <div className="space-y-2">
              {runs.map((run) => (
                <button
                  key={run.run_id}
                  type="button"
                  onClick={() => setSelectedRunId(run.run_id)}
                  className={`w-full rounded-xl border px-3 py-3 text-left transition-colors ${
                    selectedRun?.run_id === run.run_id
                      ? 'border-[var(--primary)] bg-[var(--canvas)]'
                      : 'border-[var(--border)] bg-white hover:bg-[var(--canvas)]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-xs font-semibold">{run.run_id}</span>
                    <RunStatus run={run} />
                  </div>
                  <div className="mt-2 flex items-center gap-3 text-xs text-[var(--muted)]">
                    <span>{run.total_duration_ms}ms</span>
                    <span>{run.stages.length} 阶段</span>
                    <span>{run.strategy === 'fast' ? '极速稳定' : 'AI 增强'}</span>
                  </div>
                </button>
              ))}
            </div>
          </section>

          {selectedRun ? <RunDetail run={selectedRun} /> : null}
        </div>
      )}
    </main>
  );
}

function RunDetail({ run }: { run: PlanningRunReport }) {
  const maxDuration = Math.max(...run.stages.map((stage) => stage.duration_ms), 1);

  return (
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">运行详情</h2>
          <p className="mt-1 font-mono text-xs text-[var(--muted)]">{run.run_id}</p>
        </div>
        <RunStatus run={run} />
      </div>

      <div className="mt-5 space-y-3">
        {run.stages.map((stage) => (
          <div key={`${stage.stage}-${stage.title}`}>
            <StageRow stage={stage} maxDuration={maxDuration} />
          </div>
        ))}
      </div>

      {run.warnings.length > 0 ? (
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-amber-800">
            <AlertTriangle size={16} />
            降级原因
          </div>
          <ul className="mt-2 space-y-1 text-sm leading-6 text-amber-800">
            {run.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function StageRow({ stage, maxDuration }: { stage: PlanningStageLog; maxDuration: number }) {
  const colors: Record<PlanningStageLog['status'], string> = {
    success: 'accent-green-700',
    degraded: 'accent-amber-500',
    skipped: 'accent-zinc-300',
    failed: 'accent-red-700',
  };

  return (
    <div className="rounded-xl border border-[var(--border)] p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{stage.title}</div>
          <div className="mt-1 text-xs text-[var(--muted)]">{stage.message || stage.stage}</div>
        </div>
        <span className="font-mono text-xs text-[var(--muted)]">{stage.duration_ms}ms</span>
      </div>
      <progress className={`mt-3 h-2 w-full overflow-hidden rounded-full ${colors[stage.status]}`} max={maxDuration} value={Math.max(stage.duration_ms, 1)} />
    </div>
  );
}

function RunStatus({ run }: { run: PlanningRunReport }) {
  const failed = run.stages.some((stage) => stage.status === 'failed');
  const degraded = run.warnings.length > 0 || run.stages.some((stage) => stage.status === 'degraded' || stage.status === 'skipped');

  if (failed) {
    return <span className="rounded-full bg-red-50 px-2 py-1 text-xs font-semibold text-[var(--danger)]">失败</span>;
  }
  if (degraded) {
    return <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-semibold text-[var(--warning)]">降级</span>;
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-1 text-xs font-semibold text-[var(--success)]">
      <CheckCircle2 size={12} />
      正常
    </span>
  );
}

function MetricCard({
  icon,
  label,
  value,
  tone = 'default',
}: {
  icon: ReactNode;
  label: string;
  value: string;
  tone?: 'default' | 'warning';
}) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-white p-4">
      <div className={`flex items-center gap-2 text-sm font-semibold ${tone === 'warning' ? 'text-[var(--warning)]' : 'text-[var(--primary)]'}`}>
        {icon}
        {label}
      </div>
      <div className="mt-3 text-2xl font-bold">{value}</div>
    </div>
  );
}

function loadRuns(): PlanningRunReport[] {
  try {
    const raw = localStorage.getItem(runHistoryKey);
    const history = raw ? JSON.parse(raw) as PlanningRunReport[] : [];
    const latestRaw = sessionStorage.getItem('latest-run-report');
    const latest = latestRaw ? JSON.parse(latestRaw) as PlanningRunReport : null;
    if (!latest) return history;
    return [latest, ...history.filter((run) => run.run_id !== latest.run_id)].slice(0, 20);
  } catch {
    return [];
  }
}
