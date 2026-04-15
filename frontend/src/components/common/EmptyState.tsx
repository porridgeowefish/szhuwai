import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../../utils/cn';

interface EmptyStateAction {
  label: string;
  onClick?: () => void;
  to?: string;
}

interface EmptyStateProps {
  icon: React.ElementType;
  title: string;
  description?: string;
  action?: EmptyStateAction;
  className?: string;
}

/**
 * 统一的空状态组件
 * - 一致的图标大小 (48px)、颜色 (text-zinc-300)、文案风格
 * - 统一的 CTA 按钮样式 (Link 或 button)
 * - 圆角 rounded-2xl，虚线边框
 */
const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'text-center py-16 border-2 border-dashed border-[var(--stone)] rounded-2xl',
        className
      )}
    >
      <Icon size={48} className="mx-auto text-zinc-300 mb-4" />
      <p className="text-zinc-500 font-medium">{title}</p>
      {description && (
        <p className="text-sm text-zinc-400 mt-1">{description}</p>
      )}
      {action && (
        action.to ? (
          <Link
            to={action.to}
            className="inline-block mt-4 px-6 py-2 btn-forest rounded-xl text-white font-bold text-sm"
          >
            {action.label}
          </Link>
        ) : (
          <button
            onClick={action.onClick}
            className="mt-4 px-6 py-2 btn-forest rounded-xl text-white font-bold text-sm"
          >
            {action.label}
          </button>
        )
      )}
    </div>
  );
};

export default EmptyState;
