import React, { useState } from 'react';
import { CloudSun, Search, MapPin, Calendar, Wind, Droplets, Thermometer } from 'lucide-react';
import { cn } from '../utils/cn';

const WeatherQueryPage: React.FC = () => {
  const [location, setLocation] = useState('');
  const [date, setDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [weather, setWeather] = useState<any>(null);

  const handleQuery = async () => {
    if (!location) return;
    setLoading(true);
    // TODO: 调用天气查询 API
    setTimeout(() => {
      setWeather({
        location: location,
        date: date || new Date().toISOString().split('T')[0],
        temp_max: 25,
        temp_min: 15,
        text_day: '多云',
        wind_scale_day: '3级',
        precip: '0',
        humidity: 65,
      });
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          天气查询
        </h1>
        <p className="text-sm text-zinc-500 mt-1">查询指定地点的天气预报</p>
      </div>

      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">地点</label>
            <div className="relative">
              <MapPin size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                placeholder="如：峨眉山"
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">日期（可选）</label>
            <div className="relative">
              <Calendar size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
              />
            </div>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleQuery}
              disabled={loading || !location}
              className={cn(
                'w-full py-3 rounded-xl text-white font-bold btn-forest',
                (loading || !location) && 'opacity-70 cursor-not-allowed'
              )}
            >
              {loading ? '查询中...' : '查询天气'}
            </button>
          </div>
        </div>
      </div>

      {weather && (
        <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
          <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
            <CloudSun size={20} className="text-blue-500" />
            {weather.location} 天气预报
          </h2>
          <div className="flex items-center gap-6 mb-6">
            <div className="text-5xl font-black tracking-tighter">
              {weather.temp_max}°<span className="text-zinc-300">/</span>{weather.temp_min}°
            </div>
            <div>
              <div className="text-sm font-bold">{weather.text_day}</div>
              <div className="text-xs text-zinc-500">{weather.date}</div>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2 text-zinc-600">
              <Wind size={18} className="text-zinc-400" />
              <span className="text-sm">风力: {weather.wind_scale_day}</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-600">
              <Droplets size={18} className="text-zinc-400" />
              <span className="text-sm">降水: {weather.precip}mm</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-600">
              <Thermometer size={18} className="text-zinc-400" />
              <span className="text-sm">湿度: {weather.humidity}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WeatherQueryPage;
