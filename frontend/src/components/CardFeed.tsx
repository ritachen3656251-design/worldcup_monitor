import React from 'react';
import type { HotCard as HotCardType } from '../types';
import { HotCard } from './HotCard';

interface CardFeedProps {
  cards: HotCardType[];
  onCardClick?: (card: HotCardType) => void;
  loading?: boolean;
}

export const CardFeed: React.FC<CardFeedProps> = ({ cards, onCardClick, loading = false }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-pulse"
          >
            <div className="p-4">
              <div className="flex gap-2 mb-3">
                <div className="h-5 w-16 bg-gray-200 rounded-full" />
                <div className="h-5 w-12 bg-gray-200 rounded-full" />
              </div>
              <div className="h-6 bg-gray-200 rounded mb-2 w-3/4" />
              <div className="h-4 bg-gray-200 rounded mb-1 w-full" />
              <div className="h-4 bg-gray-200 rounded mb-3 w-2/3" />
              <div className="flex justify-between">
                <div className="h-3 w-20 bg-gray-200 rounded" />
                <div className="h-3 w-16 bg-gray-200 rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-6xl mb-4">⚽</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无热点内容</h3>
        <p className="text-gray-500">系统正在抓取最新的世界杯相关内容，请稍后再来查看</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {cards.map((card, index) => (
        <HotCard
          key={card.id}
          card={card}
          onClick={onCardClick}
          size={index < 3 ? 'large' : 'small'}
        />
      ))}
    </div>
  );
};

export default CardFeed;
