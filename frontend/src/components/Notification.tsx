import React from 'react';

interface NotificationProps {
  count: number;
  onRefresh: () => void;
  onDismiss: () => void;
}

export const Notification: React.FC<NotificationProps> = ({ count, onRefresh, onDismiss }) => {
  if (count === 0) return null;

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 animate-slide-down">
      <div className="bg-blue-600 text-white px-5 py-3 rounded-full shadow-lg flex items-center gap-3">
        <span className="text-sm font-medium">
          {count} 条新热点
        </span>
        <button
          onClick={onRefresh}
          className="bg-white text-blue-600 text-xs font-semibold px-3 py-1 rounded-full hover:bg-blue-50 transition-colors"
        >
          查看
        </button>
        <button
          onClick={onDismiss}
          className="text-blue-200 hover:text-white transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default Notification;
