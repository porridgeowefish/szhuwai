import apiClient from './client';
import type { PlanData } from '../../types';
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
  resolveLocation: async (
    payload: { longitude?: number; latitude?: number; api_config: RuntimeAPIConfig },
  ): Promise<LocationResolveResult> => {
    const response = await apiClient.post<LocationResolveResult>('/location/resolve', payload);
    return response.data;
  },
};
