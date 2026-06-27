export interface RuntimeAPIConfig {
  weather_api_key: string;
  weather_developer_host: string;
  map_api_key: string;
  search_api_key: string;
  llm_api_key: string;
  llm_base_url: string;
  llm_model: string;
  llm_temperature: number;
  llm_max_tokens: number;
}

const STORAGE_KEY = 'outdoor-planner-api-config';

export const defaultRuntimeConfig: RuntimeAPIConfig = {
  weather_api_key: '',
  weather_developer_host: 'devapi',
  map_api_key: '',
  search_api_key: '',
  llm_api_key: '',
  llm_base_url: 'https://api.siliconflow.cn/v1',
  llm_model: 'Pro/moonshotai/Kimi-K2.5',
  llm_temperature: 0.3,
  llm_max_tokens: 8192,
};

/** 去除所有字符串字段首尾空白——复制粘贴极易混入不可见空格/换行，
 *  而高德等 API 对 key 前后空白零容忍（直接返回 INVALID_USER_KEY）。 */
function sanitize(config: RuntimeAPIConfig): RuntimeAPIConfig {
  return {
    ...config,
    weather_api_key: config.weather_api_key.trim(),
    weather_developer_host: config.weather_developer_host.trim(),
    map_api_key: config.map_api_key.trim(),
    search_api_key: config.search_api_key.trim(),
    llm_api_key: config.llm_api_key.trim(),
    llm_base_url: config.llm_base_url.trim(),
    llm_model: config.llm_model.trim(),
  };
}

export function loadRuntimeConfig(): RuntimeAPIConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? sanitize({ ...defaultRuntimeConfig, ...JSON.parse(raw) as Partial<RuntimeAPIConfig> }) : defaultRuntimeConfig;
  } catch {
    return defaultRuntimeConfig;
  }
}

export function saveRuntimeConfig(config: RuntimeAPIConfig): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sanitize(config)));
}
