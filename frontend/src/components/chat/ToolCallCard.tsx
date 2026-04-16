import React from 'react';
import { Wrench, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ToolCallCardProps {
  tool: string;
  status: 'running' | 'completed' | 'error';
  output?: string;
}

const ToolCallCard: React.FC<ToolCallCardProps> = ({ tool, status, output }) => {
  const getToolDisplayName = (toolName: string): string => {
    const toolMap: Record<string, string> = {
      track_analyze: '轨迹分析',
      weather_query: '天气查询',
      transport_query: '交通查询',
      search_query: '信息搜索',
      report_generate: '报告生成',
    };
    return toolMap[toolName] || toolName;
  };

  return (
    <div className="bg-[var(--sand)] rounded-xl p-3 mb-3 animate-fade-in-up">
      <div className="flex items-center gap-2 mb-2">
        <Wrench size={16} className="text-[var(--earth)]" />
        <span className="text-sm font-medium text-zinc-700">
          {getToolDisplayName(tool)}
        </span>
        <div className="flex-shrink-0 ml-auto">
          {status === 'running' && (
            <Loader2 size={16} className="text-[var(--forest)] animate-spin" />
          )}
          {status === 'completed' && (
            <CheckCircle2 size={16} className="text-green-600" />
          )}
          {status === 'error' && (
            <XCircle size={16} className="text-red-600" />
          )}
        </div>
      </div>

      {status === 'running' && (
        <p className="text-xs text-zinc-500">正在执行...</p>
      )}

      {status === 'completed' && output && (
        <div className="mt-2 p-2 bg-white rounded-lg border border-[var(--stone)]">
          <p className="text-xs text-zinc-600 whitespace-pre-wrap break-words">
            {output}
          </p>
        </div>
      )}

      {status === 'error' && output && (
        <div className="mt-2 p-2 bg-red-50 rounded-lg border border-red-200">
          <p className="text-xs text-red-600 whitespace-pre-wrap break-words">
            {output}
          </p>
        </div>
      )}
    </div>
  );
};

export default ToolCallCard;
