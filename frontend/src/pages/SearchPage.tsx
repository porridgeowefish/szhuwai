import React, { useState } from 'react';
import { Search, MapPin, Trees, Landmark, Phone } from 'lucide-react';
import { cn } from '../utils/cn';

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<'scenic' | 'guide' | 'rescue'>('scenic');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const handleSearch = async () => {
    if (!query) return;
    setLoading(true);
    // TODO: 调用搜索 API
    setTimeout(() => {
      setResults([
        {
          id: 1,
          title: '峨眉山金顶',
          type: 'scenic',
          description: '峨眉山最高峰，海拔3079米，是观赏日出、云海、佛光的绝佳位置。',
        },
        {
          id: 2,
          title: '万年寺',
          type: 'scenic',
          description: '峨眉山著名古刹，建于明代，是全国重点文物保护单位。',
        },
      ]);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          搜索
        </h1>
        <p className="text-sm text-zinc-500 mt-1">搜索景点、攻略、救援信息</p>
      </div>

      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <div className="flex gap-4 mb-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
              placeholder="搜索景点、攻略、救援..."
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading || !query}
            className={cn(
              'px-8 py-3 rounded-xl text-white font-bold btn-forest',
              (loading || !query) && 'opacity-70 cursor-not-allowed'
            )}
          >
            搜索
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setCategory('scenic')}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              category === 'scenic'
                ? 'bg-[var(--forest)] text-white'
                : 'bg-[var(--sand)] text-zinc-600 hover:bg-zinc-200'
            )}
          >
            景点
          </button>
          <button
            onClick={() => setCategory('guide')}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              category === 'guide'
                ? 'bg-[var(--forest)] text-white'
                : 'bg-[var(--sand)] text-zinc-600 hover:bg-zinc-200'
            )}
          >
            攻略
          </button>
          <button
            onClick={() => setCategory('rescue')}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              category === 'rescue'
                ? 'bg-[var(--forest)] text-white'
                : 'bg-[var(--sand)] text-zinc-600 hover:bg-zinc-200'
            )}
          >
            救援
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-[var(--stone)] border-t-[var(--forest)] rounded-full animate-spin" />
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-4">
          {results.map((result) => (
            <div
              key={result.id}
              className="bg-white border border-[var(--stone)] rounded-2xl p-6 card-hover"
            >
              <div className="flex items-start gap-4">
                <div className={cn(
                  'w-12 h-12 rounded-xl flex items-center justify-center shrink-0',
                  result.type === 'scenic'
                    ? 'bg-[var(--forest)]/10 text-[var(--forest)]'
                    : result.type === 'guide'
                    ? 'bg-blue-50 text-blue-600'
                    : 'bg-red-50 text-red-600'
                )}>
                  {result.type === 'scenic' && <Trees size={24} />}
                  {result.type === 'guide' && <MapPin size={24} />}
                  {result.type === 'rescue' && <Phone size={24} />}
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-lg text-zinc-900 mb-2">{result.title}</h3>
                  <p className="text-sm text-zinc-600 leading-relaxed">{result.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && query && results.length === 0 && (
        <div className="text-center py-16 border-2 border-dashed border-[var(--stone)] rounded-2xl">
          <Search size={48} className="mx-auto text-zinc-300 mb-4" />
          <p className="text-zinc-500 font-medium">未找到相关结果</p>
          <p className="text-sm text-zinc-400 mt-1">试试其他关键词</p>
        </div>
      )}
    </div>
  );
};

export default SearchPage;
