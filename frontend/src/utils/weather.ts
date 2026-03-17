/**
 * 天气计算工具函数
 * 用于前端纯计算任务，无需后端处理
 */

/**
 * 计算风寒指数 (Wind Chill Index)
 * 使用加拿大环境部风寒公式
 *
 * @param tempC - 温度 (摄氏度)
 * @param windSpeedKmh - 风速 (公里/小时)
 * @returns 风寒温度 (摄氏度)，如果输入无效返回 null
 */
export function calculateWindChill(tempC: number, windSpeedKmh: number): number | null {
  // 风寒指数仅在温度 <= 10°C 且风速 >= 4.8 km/h 时有效
  if (tempC > 10 || windSpeedKmh < 4.8) {
    return null;
  }

  // 风寒公式: WCI = 13.12 + 0.6215*T - 11.37*V^0.16 + 0.3965*T*V^0.16
  const windChill =
    13.12 +
    0.6215 * tempC -
    11.37 * Math.pow(windSpeedKmh, 0.16) +
    0.3965 * tempC * Math.pow(windSpeedKmh, 0.16);

  return Math.round(windChill * 10) / 10;
}

/**
 * 计算体感温度 (综合风寒和湿度)
 * 简化版：优先返回风寒指数，否则返回实际温度
 *
 * @param tempC - 温度 (摄氏度)
 * @param windSpeedKmh - 风速 (公里/小时)
 * @param humidityPercent - 相对湿度 (百分比)
 * @returns 体感温度
 */
export function calculateFeelsLike(
  tempC: number,
  windSpeedKmh: number,
  humidityPercent: number
): number {
  // 优先使用风寒指数
  const windChill = calculateWindChill(tempC, windSpeedKmh);
  if (windChill !== null) {
    return windChill;
  }

  // 高温高湿情况：计算湿热指数 (Heat Index)
  if (tempC >= 27 && humidityPercent >= 40) {
    // 简化的湿热指数公式
    const heatIndex =
      -8.78469475556 +
      1.61139411 * tempC +
      2.33854883889 * humidityPercent -
      0.14611605 * tempC * humidityPercent -
      0.012308094 * tempC * tempC -
      0.0164248277778 * humidityPercent * humidityPercent +
      0.002211732 * tempC * tempC * humidityPercent +
      0.00072546 * tempC * humidityPercent * humidityPercent -
      0.000003582 * tempC * tempC * humidityPercent * humidityPercent;
    return Math.round(heatIndex * 10) / 10;
  }

  return tempC;
}

/**
 * 根据风力等级估算风速范围
 * 使用蒲福风级标准
 *
 * @param windScale - 风力等级 (0-12)
 * @returns 风速范围 { min, max } (km/h)
 */
export function windScaleToSpeed(windScale: number | string): { min: number; max: number; avg: number } {
  const scale = typeof windScale === 'string' ? parseInt(windScale, 10) : windScale;

  // 蒲福风级风速对照表 (km/h)
  const windSpeedMap: Record<number, { min: number; max: number }> = {
    0: { min: 0, max: 1 },
    1: { min: 1, max: 5 },
    2: { min: 6, max: 11 },
    3: { min: 12, max: 19 },
    4: { min: 20, max: 28 },
    5: { min: 29, max: 38 },
    6: { min: 39, max: 49 },
    7: { min: 50, max: 61 },
    8: { min: 62, max: 74 },
    9: { min: 75, max: 88 },
    10: { min: 89, max: 102 },
    11: { min: 103, max: 117 },
    12: { min: 118, max: 150 }
  };

  const range = windSpeedMap[scale] || { min: 0, max: 0 };
  return {
    min: range.min,
    max: range.max,
    avg: Math.round((range.min + range.max) / 2)
  };
}

/**
 * 获取风寒风险等级描述
 *
 * @param windChill - 风寒温度 (摄氏度)
 * @returns 风险等级和描述
 */
export function getWindChillRisk(windChill: number): { level: string; color: string; description: string } {
  if (windChill >= 0) {
    return { level: '低', color: 'text-green-600', description: '舒适' };
  } else if (windChill >= -10) {
    return { level: '中', color: 'text-yellow-600', description: '略冷，注意保暖' };
  } else if (windChill >= -20) {
    return { level: '高', color: 'text-orange-600', description: '寒冷，需穿厚外套' };
  } else if (windChill >= -30) {
    return { level: '很高', color: 'text-red-600', description: '极寒，暴露皮肤可能冻伤' };
  } else {
    return { level: '极高', color: 'text-purple-600', description: '危险，避免户外活动' };
  }
}

/**
 * 计算海拔修正后的温度
 * 气温递减率约为 6.5°C / 1000m
 *
 * @param baseTemp - 基准温度 (摄氏度)
 * @param baseElevation - 基准海拔 (米)
 * @param targetElevation - 目标海拔 (米)
 * @returns 修正后的温度
 */
export function adjustTempForElevation(
  baseTemp: number,
  baseElevation: number,
  targetElevation: number
): number {
  const lapseRate = 6.5; // °C per 1000m
  const elevationDiff = (targetElevation - baseElevation) / 1000;
  return Math.round((baseTemp - lapseRate * elevationDiff) * 10) / 10;
}

/**
 * 格式化温度显示
 * @param temp - 温度
 * @param showSign - 是否显示正负号
 * @returns 格式化后的温度字符串
 */
export function formatTemperature(temp: number | null | undefined, showSign: boolean = false): string {
  if (temp === null || temp === undefined) return '--';
  if (showSign && temp > 0) {
    return `+${temp}°C`;
  }
  return `${temp}°C`;
}

/**
 * 计算海拔可视化颜色
 * 绿色(低海拔) -> 黄色 -> 红色(高海拔)
 * @param elevation - 海拔 (米)
 * @param minElevation - 最小海拔 (米)
 * @param maxElevation - 最大海拔 (米)
 * @returns 颜色字符串
 */
export function getElevationColor(elevation: number, minElevation: number, maxElevation: number): string {
  if (maxElevation <= minElevation) {
    return 'rgb(34, 197, 94)'; // 默认绿色
  }

  const ratio = (elevation - minElevation) / (maxElevation - minElevation);

  // 绿色 -> 黄色 -> 红色 渐变
  let r: number, g: number, b: number;

  if (ratio < 0.5) {
    // 绿色到黄色
    const t = ratio * 2;
    r = Math.round(34 + (234 - 34) * t);
    g = Math.round(197 + (179 - 197) * t);
    b = Math.round(94 + (8 - 94) * t);
  } else {
    // 黄色到红色
    const t = (ratio - 0.5) * 2;
    r = Math.round(234 + (239 - 234) * t);
    g = Math.round(179 + (68 - 179) * t);
    b = Math.round(8 + (68 - 8) * t);
  }

  return `rgb(${r}, ${g}, ${b})`;
}
