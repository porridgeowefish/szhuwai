import React, { useState } from 'react';
import { Navigation, MapPin, Calendar, Car, Bus } from 'lucide-react';
import { cn } from '../utils/cn';

const TransportPage: React.FC = () => {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [date, setDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [routes, setRoutes] = useState<any>(null);

  const handleQuery = async () => {
    if (!from || !to) return;
    setLoading(true);
    // TODO: 调用交通规划 API
    setTimeout(() => {
      setRoutes({
        driving: {
          distance: '125km',
          duration: '2小时15分',
          tolls: '45元',
        },
        transit: {
          distance: '142km',
          duration: '3小时30分',
          cost: '32元',
        },
      });
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          交通规划
        </h1>
        <p className="text-sm text-zinc-500 mt-1">查询出行路线方案</p>
      </div>

      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">出发地</label>
            <div className="relative">
              <MapPin size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type="text"
                value={from}
                onChange={(e) => setFrom(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                placeholder="如：成都市"
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">目的地</label>
            <div className="relative">
              <MapPin size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type="text"
                value={to}
                onChange={(e) => setTo(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                placeholder="如：峨眉山"
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">出发日期（可选）</label>
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
              disabled={loading || !from || !to}
              className={cn(
                'w-full py-3 rounded-xl text-white font-bold btn-forest',
                (loading || !from || !to) && 'opacity-70 cursor-not-allowed'
              )}
            >
              {loading ? '查询中...' : '查询路线'}
            </button>
          </div>
        </div>
      </div>

      {routes && (
        <div className="space-y-4">
          <div className="bg-white border border-[var(--stone)] rounded-2xl p-6 border-l-4 border-l-amber-500">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Car size={20} className="text-amber-600" />
              </div>
              <h3 className="font-bold text-zinc-900">驾车方案</h3>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-2xl font-bold text-zinc-900">{routes.driving.distance}</div>
                <div className="text-xs text-zinc-500">距离</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-zinc-900">{routes.driving.duration}</div>
                <div className="text-xs text-zinc-500">预计时间</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-zinc-900">{routes.driving.tolls}</div>
                <div className="text-xs text-zinc-500">过路费</div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-[var(--stone)] rounded-2xl p-6 border-l-4 border-l-green-500">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <Bus size={20} className="text-green-600" />
              </div>
              <h3 className="font-bold text-zinc-900">公交方案</h3>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-2xl font-bold text-zinc-900">{routes.transit.distance}</div>
                <div className="text-xs text-zinc-500">距离</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-zinc-900">{routes.transit.duration}</div>
                <div className="text-xs text-zinc-500">预计时间</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-zinc-900">{routes.transit.cost}</div>
                <div className="text-xs text-zinc-500">票价</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransportPage;
