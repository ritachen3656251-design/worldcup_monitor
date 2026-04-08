import React from 'react';
import { SourceContent } from '../types';

interface RawListProps {
  items: SourceContent[];
}

const RawList: React.FC<RawListProps> = ({ items }) => {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
  };

  const getPlatformBadgeColor = (platform: string) => {
    switch (platform) {
      case 'hupu':
        return 'bg-orange-500';
      case 'dongqiudi':
        return 'bg-green-500';
      case 'bilibili':
        return 'bg-pink-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getPlatformName = (platform: string) => {
    switch (platform) {
      case 'hupu':
        return '虎扑';
      case 'dongqiudi':
        return '懂球帝';
      case 'bilibili':
        return 'B站';
      default:
        return platform;
    }
  };

  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        暂无内容，等待抓取...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div
          key={item.id}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-lg font-semibold text-gray-900 flex-1">
              {item.title}
            </h3>
            <span
              className={`${getPlatformBadgeColor(item.platform)} text-white text-xs px-2 py-1 rounded ml-2`}
            >
              {getPlatformName(item.platform)}
            </span>
          </div>

          <p className="text-gray-600 text-sm mb-3 line-clamp-3">
            {item.cleaned_text}
          </p>

          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-4">
              {item.author && (
                <span>作者: {item.author}</span>
              )}
              <span>互动: {item.interaction_count}</span>
            </div>
            <div className="flex items-center space-x-4">
              <span>发布: {formatDate(item.published_at)}</span>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700"
              >
                查看原文 →
              </a>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RawList;
