import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 合并类名工具函数
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
