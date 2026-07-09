import apiClient from './client';
import type { PlanData, WebReference } from '../../types';
import type { RuntimeAPIConfig } from '../runtimeConfig';

export interface TwoBuluTrackInfo {
  source_url: string;
  track_id: string;
  authorization_required: boolean;
  message: string;
}

export interface TrackAnalysis {
  track_name?: string;
  trackName?: string;
  totalDistanceKm: number;
  totalAscentM: number;
  totalDescentM: number;
  maxElevationM: number;
  difficultyLevel: string;
  estimatedDurationHours: number;
}

export type TwoBuluSessionState =
  | 'starting'
  | 'waiting_login'
  | 'waiting_captcha'
  | 'downloading'
  | 'ready'
  | 'failed';

export interface TwoBuluSessionStatus {
  session_id: string;
  track_id: string;
  state: TwoBuluSessionState;
  message: string;
  file_name: string | null;
}

export interface PlanGeneratePayload {
  two_bulu_url: string;
  two_bulu_session_id: string;
  trip_date: string | null;
  departure_point: string | null;
  additional_info: string;
  api_config: RuntimeAPIConfig;
  generation_mode?: 'fast' | 'ai';
}

export interface PlanningStageLog {
  stage: string;
  title: string;
  status: 'success' | 'degraded' | 'failed' | 'skipped';
  duration_ms: number;
  message: string;
}

export interface PlanningRunReport {
  run_id: string;
  strategy: 'fast' | 'ai';
  total_duration_ms: number;
  stages: PlanningStageLog[];
  warnings: string[];
}

export interface PlanGenerateResult {
  mode: 'track_only' | 'quick_plan' | 'full_plan';
  track_analysis: TrackAnalysis;
  plan: PlanData | null;
  message: string;
  run_report: PlanningRunReport;
}

export interface LocationResolveResult {
  success: boolean;
  source: 'reverse_geocode' | 'ip' | 'none';
  address: string | null;
  coordinate_text: string | null;
  province: string | null;
  city: string | null;
  district: string | null;
  message: string;
}

export interface WebInsightResult {
  success: boolean;
  summary: string;
  message: string;
}

export type ApiService = 'map' | 'weather' | 'search' | 'llm';

export interface ApiConnectionTestResult {
  service: ApiService;
  label: string;
  status: 'success' | 'failed' | 'skipped';
  message: string;
  duration_ms: number;
}

export interface ApiConnectionTestResponse {
  results: ApiConnectionTestResult[];
}

function parseSSE(raw: string): { event: string; data: unknown } | null {
  let event = 'message';
  const dataLines: string[] = [];
  for (const line of raw.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim();
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return null;
  try {
    return { event, data: JSON.parse(dataLines.join('\n')) };
  } catch {
    return null;
  }
}

export const planAPI = {
  inspect: async (url: string): Promise<TwoBuluTrackInfo> => {
    const response = await apiClient.post<TwoBuluTrackInfo>('/two-bulu/inspect', { url });
    return response.data;
  },
  createTwoBuluSession: async (url: string): Promise<TwoBuluSessionStatus> => {
    const response = await apiClient.post<TwoBuluSessionStatus>('/two-bulu/sessions', { url });
    return response.data;
  },
  getTwoBuluSession: async (sessionId: string): Promise<TwoBuluSessionStatus> => {
    const response = await apiClient.get<TwoBuluSessionStatus>(`/two-bulu/sessions/${sessionId}`);
    return response.data;
  },
  generate: async (payload: PlanGeneratePayload): Promise<PlanGenerateResult> => {
    const response = await apiClient.post<PlanGenerateResult>('/plan/generate', payload);
    return response.data;
  },
  streamGenerate: async (
    payload: PlanGeneratePayload,
    onStage: (stage: PlanningStageLog) => void,
  ): Promise<PlanGenerateResult> => {
    const resp = await fetch('/api/v1/plan/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!resp.ok || !resp.body) throw new Error(`生成请求失败（${resp.status}）`);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let result: PlanGenerateResult | null = null;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let sep = buffer.indexOf('\n\n');
      while (sep >= 0) {
        const evt = parseSSE(buffer.slice(0, sep));
        buffer = buffer.slice(sep + 2);
        if (evt) {
          if (evt.event === 'stage') onStage(evt.data as PlanningStageLog);
          else if (evt.event === 'result') result = evt.data as PlanGenerateResult;
          else if (evt.event === 'error') throw new Error((evt.data as { detail?: string }).detail || '生成失败');
        }
        sep = buffer.indexOf('\n\n');
      }
    }
    if (!result) throw new Error('未收到生成结果');
    return result;
  },
  resolveLocation: async (
    payload: { longitude?: number; latitude?: number; api_config: RuntimeAPIConfig },
  ): Promise<LocationResolveResult> => {
    const response = await apiClient.post<LocationResolveResult>('/location/resolve', payload);
    return response.data;
  },
  synthesizeInsight: async (
    payload: { keywords: string; references: WebReference[]; api_config: RuntimeAPIConfig },
  ): Promise<WebInsightResult> => {
    const response = await apiClient.post<WebInsightResult>('/plan/insight', payload);
    return response.data;
  },
  testApiConnection: async (
    payload: { service: ApiService | 'all'; api_config: RuntimeAPIConfig },
  ): Promise<ApiConnectionTestResponse> => {
    const response = await apiClient.post<ApiConnectionTestResponse>('/runtime/test', payload);
    return response.data;
  },
};
