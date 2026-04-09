import React from 'react';
import type { HotCard as HotCardType } from '../types';

interface HotCardProps {
  card: HotCardType;
  onClick?: (card: HotCardType) => void;
  size?: 'large' | 'small';
}

const credibilityColors: Record<string, string> = {
  '可信': 'bg-green-100 text-green-800',
  '待确认': 'bg-yellow-100 text-yellow-800',
  '传闻': 'bg-red-100 text-red-800',
};

const categoryColors: Record<string, string> = {
  '转会传闻': 'bg-purple-100 text-purple-700',
  '球队动态': 'bg-blue-100 text-blue-700',
  '赛程赛制': 'bg-teal-100 text-teal-700',
  '球迷讨论': 'bg-orange-100 text-orange-700',
};

const platformColors: Record<string, string> = {
  '虎扑': 'bg-orange-500',
  '懂球帝': 'bg-green-500',
  'B站': 'bg-pink-500',
  '搜索引擎聚合': 'bg-gray-500',
};

export const HotCard: React.FC<HotCardProps> = ({ card, onClick, size = 'small' }) => {
  const isLarge = size === 'large';

  const handleClick = () => {
    if (onClick) onClick(card);
  };

  const formatTime = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffHour = Math.floor(diffMs / 3600000);

    if (diffMin < 60) return `${diffMin}分钟前`;
    if (diffHour < 24) return `${diffHour}小时前`;
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  return (
    <div
      onClick={handleClick}
      className={`
        bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200
        cursor-pointer border border-gray-100 overflow-hidden
        ${isLarge ? 'col-span-2 row-span-2' : ''}
      `}
    >
      <div className={`p-4 ${isLarge ? 'p-6' : 'p-4'}`}>
        {/* Category & Credibility badges */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              categoryColors[card.category] || 'bg-gray-100 text-gray-700'
            }`}
          >
            {card.category}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              credibilityColors[card.credibility] || 'bg-gray-100 text-gray-600'
            }`}
          >
            {card.credibility}
          </span>
        </div>

        {/* Title */}
        <h3
          className={`font-bold text-gray-900 leading-tight mb-2 ${
            isLarge ? 'text-xl' : 'text-base'
          } line-clamp-2`}
        >
          {card.title}
        </h3>

        {/* Summary */}
        <p
          className={`text-gray-600 leading-relaxed mb-3 ${
            isLarge ? 'text-base line-clamp-3' : 'text-sm line-clamp-2'
          }`}
        >
          {card.summary}
        </p>

        {/* Footer: Sources + Time */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            {card.sources.map((source, idx) => (
              <span
                key={idx}
                className="flex items-center gap-1 text-xs text-gray-500"
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    platformColors[source] || 'bg-gray-400'
                  }`}
                />
                {source}
              </span>
            ))}
            {card.sources.length > 1 && (
              <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-full font-medium ml-1">
                {card.sources.length}源
              </span>
            )}
          </div>
          <span className="text-xs text-gray-400">
            {formatTime(card.generated_at)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default HotCard;
